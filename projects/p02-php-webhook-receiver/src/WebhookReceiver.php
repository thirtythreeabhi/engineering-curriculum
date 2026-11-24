<?php

declare(strict_types=1);

namespace WebhookReceiver;

final class WebhookReceiver
{
    public function __construct(
        private SignatureVerifier $verifier,
        private IdempotencyLockInterface $idempotencyLock,
        /** @var callable(WebhookEvent): void */
        private $handler
    ) {}

    /**
     * Process an incoming webhook HTTP request.
     *
     * @param string $rawBody Raw input body
     * @param array<string, string> $headers Normalized request headers
     * @return WebhookResponse
     */
    public function handleRequest(string $rawBody, array $headers): WebhookResponse
    {
        $signatureHeader = $headers['x-hub-signature-256'] ?? $headers['x-signature'] ?? null;
        $timestampHeader = $headers['x-timestamp'] ?? null;
        $eventId = $headers['x-event-id'] ?? null;

        if ($signatureHeader === null || $timestampHeader === null || $eventId === null) {
            return new WebhookResponse(400, "Missing required security headers (Signature, Timestamp, Event-ID)");
        }

        $timestamp = (int)$timestampHeader;

        // 1. Signature verification & replay defense
        if (!$this->verifier->verify($rawBody, $signatureHeader, $timestamp)) {
            return new WebhookResponse(401, "Invalid webhook signature or expired timestamp");
        }

        // 2. Check if already permanently processed
        if ($this->idempotencyLock->isCompleted($eventId)) {
            return new WebhookResponse(200, "Event already processed (idempotent duplicate)");
        }

        // 3. Acquire atomic idempotency lock
        if (!$this->idempotencyLock->acquire($eventId, ttlSeconds: 60)) {
            return new WebhookResponse(409, "Event is currently being processed by another worker");
        }

        // 4. Parse payload
        $data = json_decode($rawBody, true);
        if (!is_array($data)) {
            $this->idempotencyLock->release($eventId);
            return new WebhookResponse(400, "Malformed JSON payload");
        }

        $eventType = (string)($data['event'] ?? $data['type'] ?? 'unknown');
        $event = new WebhookEvent($eventId, $timestamp, $eventType, $data, $rawBody);

        // 5. Execute handler
        try {
            ($this->handler)($event);
            $this->idempotencyLock->markCompleted($eventId);
            return new WebhookResponse(200, "Webhook processed successfully");
        } catch (\Throwable $e) {
            // Release lock to allow retry worker to pick it up later
            $this->idempotencyLock->release($eventId);
            return new WebhookResponse(500, "Processing failed: " . $e->getMessage());
        }
    }
}
