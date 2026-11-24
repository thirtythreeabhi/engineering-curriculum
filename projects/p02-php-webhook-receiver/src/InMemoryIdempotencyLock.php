<?php

declare(strict_types=1);

namespace WebhookReceiver;

final class InMemoryIdempotencyLock implements IdempotencyLockInterface
{
    /** @var array<string, int> */
    private array $locks = [];

    /** @var array<string, int> */
    private array $completed = [];

    public function acquire(string $eventId, int $ttlSeconds = 60): bool
    {
        $now = time();

        // Check if completed
        if (isset($this->completed[$eventId]) && $this->completed[$eventId] > $now) {
            return false;
        }

        // Check if locked
        if (isset($this->locks[$eventId]) && $this->locks[$eventId] > $now) {
            return false;
        }

        $this->locks[$eventId] = $now + $ttlSeconds;
        return true;
    }

    public function markCompleted(string $eventId, int $retentionSeconds = 86400): void
    {
        unset($this->locks[$eventId]);
        $this->completed[$eventId] = time() + $retentionSeconds;
    }

    public function release(string $eventId): void
    {
        unset($this->locks[$eventId]);
    }

    public function isCompleted(string $eventId): bool
    {
        return isset($this->completed[$eventId]) && $this->completed[$eventId] > time();
    }
}
