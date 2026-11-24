<?php

declare(strict_types=1);

namespace WebhookReceiver;

interface IdempotencyLockInterface
{
    /**
     * Attempts to acquire an atomic lock for the event ID.
     *
     * @param string $eventId Unique ID of the event
     * @param int $ttlSeconds Time-to-live for the in-progress lock
     * @return bool True if acquired, false if already held or already processed
     */
    public function acquire(string $eventId, int $ttlSeconds = 60): bool;

    /**
     * Marks the event as permanently completed.
     */
    public function markCompleted(string $eventId, int $retentionSeconds = 86400): void;

    /**
     * Releases an in-progress lock (e.g. upon transient processing failure).
     */
    public function release(string $eventId): void;

    /**
     * Checks if event has already been completed.
     */
    public function isCompleted(string $eventId): bool;
}
