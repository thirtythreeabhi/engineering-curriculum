<?php

declare(strict_types=1);

namespace WebhookReceiver\Tests;

use WebhookReceiver\InMemoryIdempotencyLock;
use WebhookReceiver\RedisIdempotencyLock;
use WebhookReceiver\RetryWorker;
use WebhookReceiver\SignatureVerifier;
use WebhookReceiver\WebhookEvent;
use WebhookReceiver\WebhookReceiver;

final class FakeAtomicRedis
{
    /** @var array<string, array{val: string, exp: int}> */
    public array $store = [];
    public int $now = 1000;

    private function purgeExpired(string $key): void
    {
        if (isset($this->store[$key]) && $this->store[$key]['exp'] <= $this->now) {
            unset($this->store[$key]);
        }
    }

    public function get(string $key): string|false
    {
        $this->purgeExpired($key);
        return $this->store[$key]['val'] ?? false;
    }

    public function set(string $key, string $value, array $options = []): bool
    {
        $this->purgeExpired($key);
        $nx = in_array('nx', $options, true);
        if ($nx && isset($this->store[$key])) {
            return false;
        }
        $ttl = (int)($options['ex'] ?? 60);
        $this->store[$key] = ['val' => $value, 'exp' => $this->now + $ttl];
        return true;
    }

    public function del(string $key): int
    {
        if (isset($this->store[$key])) {
            unset($this->store[$key]);
            return 1;
        }
        return 0;
    }

    public function eval(string $script, array $args = [], int $numKeys = 0): mixed
    {
        $key = (string)$args[0];
        $this->purgeExpired($key);

        if (str_contains($script, "'completed'")) {
            $token = (string)$args[1];
            $retention = (int)$args[2];
            $cur = $this->store[$key]['val'] ?? null;
            if ($cur === 'completed') {
                return 1;
            }
            if ($cur === $token || $cur === null) {
                $this->store[$key] = ['val' => 'completed', 'exp' => $this->now + $retention];
                return 1;
            }
            return 0;
        }

        // Release-if-owned Lua script
        $token = (string)$args[1];
        if (($this->store[$key]['val'] ?? null) === $token) {
            unset($this->store[$key]);
            return 1;
        }
        return 0;
    }
}

final class WebhookReceiverTest
{
    private string $secret = 'whsec_99a8b7c6d5e4f3a2b1c0';
    private SignatureVerifier $verifier;
    private InMemoryIdempotencyLock $lock;
    private array $handledEvents = [];
    private WebhookReceiver $receiver;

    public function setUp(): void
    {
        $this->verifier = new SignatureVerifier($this->secret, toleranceSeconds: 300);
        $this->lock = new InMemoryIdempotencyLock();
        $this->handledEvents = [];

        $this->receiver = new WebhookReceiver(
            $this->verifier,
            $this->lock,
            function (WebhookEvent $event) {
                $this->handledEvents[] = $event;
            }
        );
    }

    public function testValidWebhookAccepted(): void
    {
        $this->setUp();

        $timestamp = time();
        $payload = json_encode(['event' => 'payment.succeeded', 'amount' => 4999, 'currency' => 'usd']);
        $sig = $this->verifier->computeSignature($payload, $timestamp);

        $headers = [
            'x-hub-signature-256' => $sig,
            'x-timestamp' => (string)$timestamp,
            'x-event-id' => 'evt_1001',
        ];

        $response = $this->receiver->handleRequest($payload, $headers);

        assert($response->statusCode === 200, "Valid webhook should return 200 OK, got: {$response->statusCode}");
        assert(count($this->handledEvents) === 1, "Handler should have been executed once");
        assert($this->lock->isCompleted('evt_1001'), "Event should be marked completed in idempotency store");
    }

    public function testForgedSignatureRejected(): void
    {
        $this->setUp();

        $timestamp = time();
        $payload = json_encode(['event' => 'order.created', 'id' => 123]);
        $forgedSig = 'sha256=' . hash('sha256', 'bogus-hash-value');

        $headers = [
            'x-hub-signature-256' => $forgedSig,
            'x-timestamp' => (string)$timestamp,
            'x-event-id' => 'evt_1002',
        ];

        $response = $this->receiver->handleRequest($payload, $headers);

        assert($response->statusCode === 401, "Forged signature must return 401 Unauthorized, got: {$response->statusCode}");
        assert(count($this->handledEvents) === 0, "Handler must NOT be executed for forged signature");
    }

    public function testExpiredTimestampRejected(): void
    {
        $this->setUp();

        $timestamp = time() - 360; // 6 minutes ago (exceeds 5-minute tolerance)
        $payload = json_encode(['event' => 'user.updated']);
        $sig = $this->verifier->computeSignature($payload, $timestamp);

        $headers = [
            'x-hub-signature-256' => $sig,
            'x-timestamp' => (string)$timestamp,
            'x-event-id' => 'evt_1003',
        ];

        $response = $this->receiver->handleRequest($payload, $headers);

        assert($response->statusCode === 401, "Expired timestamp must be rejected to prevent replay attacks");
        assert(count($this->handledEvents) === 0, "Handler must not run for replayed message");
    }

    public function testIdempotentDeduplication(): void
    {
        $this->setUp();

        $timestamp = time();
        $payload = json_encode(['event' => 'invoice.paid', 'id' => 'inv_555']);
        $sig = $this->verifier->computeSignature($payload, $timestamp);

        $headers = [
            'x-hub-signature-256' => $sig,
            'x-timestamp' => (string)$timestamp,
            'x-event-id' => 'evt_duplicate_test',
        ];

        // First delivery
        $res1 = $this->receiver->handleRequest($payload, $headers);
        assert($res1->statusCode === 200, "First delivery must succeed");
        assert(count($this->handledEvents) === 1, "Handler ran once");

        // Second delivery (duplicate delivery from provider)
        $res2 = $this->receiver->handleRequest($payload, $headers);
        assert($res2->statusCode === 200, "Second duplicate delivery must return 200 idempotent OK");
        assert(count($this->handledEvents) === 1, "Handler MUST NOT run again for duplicate event");
    }

    public function testRetryWorkerExponentialBackoffAndDlq(): void
    {
        $worker = new RetryWorker(maxRetries: 3, baseDelayMs: 100, maxDelayMs: 1000, jitterMs: 20);
        $event = new WebhookEvent('evt_dlq', time(), 'test.event', [], '{}');

        // Attempt 1 failure -> scheduled
        $r1 = $worker->handleFailure($event, 1, 'Network timeout');
        assert($r1['status'] === 'scheduled');
        assert($r1['nextAttempt'] === 2);
        assert($r1['delayMs'] >= 200 && $r1['delayMs'] <= 250);

        // Attempt 2 failure -> scheduled
        $r2 = $worker->handleFailure($event, 2, '503 Service Unavailable');
        assert($r2['status'] === 'scheduled');
        assert($r2['nextAttempt'] === 3);

        // Attempt 3 failure -> maxRetries reached -> routed to DLQ!
        $r3 = $worker->handleFailure($event, 3, 'Fatal database error');
        assert($r3['status'] === 'dlq', "Must route to DLQ once maxRetries exhausted");
        assert(count($worker->deadLetterQueue) === 1, "DLQ should contain 1 failed message");
        assert($worker->deadLetterQueue[0]['event']->eventId === 'evt_dlq');
    }

    public function testRedisIdempotencyLockConcurrencyAndReplaySafety(): void
    {
        $redis = new FakeAtomicRedis();
        $workerA = new RedisIdempotencyLock($redis);
        $workerB = new RedisIdempotencyLock($redis);

        // 1. Concurrent acquisition: only Worker A acquires
        assert($workerA->acquire('evt_race_1', ttlSeconds: 60) === true);
        assert($workerB->acquire('evt_race_1', ttlSeconds: 60) === false, "Concurrent Worker B must be denied");

        // 2. Worker A marks completed atomically (no gap window between lock and completed)
        $workerA->markCompleted('evt_race_1', retentionSeconds: 3600);
        assert($workerA->isCompleted('evt_race_1') === true);

        // 3. Stale Worker B calling release() MUST NOT delete 'completed' state
        $workerB->release('evt_race_1');
        assert($workerA->isCompleted('evt_race_1') === true, "Non-owner release must not erase completed marker");

        // 4. Subsequent replay attempt cannot re-acquire lock
        assert($workerB->acquire('evt_race_1', ttlSeconds: 60) === false, "Replay after completion must be rejected");

        // 5. Failed Worker A releases its own in-progress lock so retry Worker B succeeds
        assert($workerA->acquire('evt_retry_2', ttlSeconds: 60) === true);
        $workerA->release('evt_retry_2');
        assert($workerB->acquire('evt_retry_2', ttlSeconds: 60) === true, "Retry after owned release must succeed");

        // 6. End-to-end WebhookReceiver concurrent in-flight 409 & replay 200
        $handled = 0;
        $receiver = new WebhookReceiver($this->verifier, new RedisIdempotencyLock($redis), function () use (&$handled) {
            $handled++;
        });
        $ts = time();
        $body = json_encode(['event' => 'charge.captured']);
        $headers = [
            'x-hub-signature-256' => $this->verifier->computeSignature($body, $ts),
            'x-timestamp' => (string)$ts,
            'x-event-id' => 'evt_e2e_redis',
        ];
        // Pre-lock in-flight -> receiver returns 409 Conflict
        $contender = new RedisIdempotencyLock($redis);
        assert($contender->acquire('evt_e2e_redis', 60) === true);
        $conflict = $receiver->handleRequest($body, $headers);
        assert($conflict->statusCode === 409, "Concurrent in-flight delivery must return 409 Conflict");
        assert($handled === 0);

        // Release contender, process once, then replay -> 200 idempotent OK with handler run once
        $contender->release('evt_e2e_redis');
        $ok = $receiver->handleRequest($body, $headers);
        assert($ok->statusCode === 200 && $handled === 1);
        $replay = $receiver->handleRequest($body, $headers);
        assert($replay->statusCode === 200 && $handled === 1, "Replay must not re-run handler");
    }
}
