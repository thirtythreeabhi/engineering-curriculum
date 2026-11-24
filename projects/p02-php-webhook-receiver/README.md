# Project 02: Production Webhook Receiver (PHP 8.3)

Production-ready PHP 8.3 webhook ingestion service implementing cryptographic HMAC-SHA256 signature verification, replay attack mitigation, distributed Redis idempotency locking, and an exponential backoff retry worker with Dead Letter Queue (DLQ) support.

## Security Architecture

1. **Timing-Safe HMAC-SHA256 Verification (`hash_equals`)**:
   - Compares computed SHA-256 HMAC against the `X-Hub-Signature-256` header using `hash_equals()` to prevent string comparison timing side-channel attacks.
   - Signs both the timestamp and the raw payload (`timestamp . '.' . rawPayload`) to prevent payload tampering.

2. **Replay Attack Defense (Tolerance Window)**:
   - Validates that `|currentTime - timestamp| <= 300` seconds (5 minutes). Rejects old requests and requests claiming to originate from the future.

3. **Atomic Redis Idempotency Lock**:
   - Uses `SET lock_key in_progress NX EX 60` to guarantee that concurrent duplicates delivered by webhooks are safely serialized without double execution.
   - Marks successful completions with a persistent retention TTL (`SET completed_key 1 EX 86400`).

4. **Exponential Backoff Retry Worker**:
   - `delay = min(maxDelay, baseDelay * (2 ^ (attempt - 1))) + jitter`
   - Incorporates full jitter to prevent retry thundering herds.
   - Routes permanently failing events to a Dead Letter Queue (DLQ) after maximum retry attempts are exhausted.

## Directory Structure

```
p02-php-webhook-receiver/
├── composer.json
├── README.md
├── src/
│   ├── IdempotencyLockInterface.php
│   ├── InMemoryIdempotencyLock.php
│   ├── RedisIdempotencyLock.php
│   ├── RetryWorker.php
│   ├── SignatureVerifier.php
│   ├── WebhookEvent.php
│   ├── WebhookReceiver.php
│   └── WebhookResponse.php
└── tests/
    ├── run_tests.php
    └── WebhookReceiverTest.php
```

## Running Tests

Run the test suite:

```bash
php tests/run_tests.php
```

Or with PHPUnit:
```bash
phpunit tests/
```
