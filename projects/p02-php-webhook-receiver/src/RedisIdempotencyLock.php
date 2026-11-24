<?php

declare(strict_types=1);

namespace WebhookReceiver;

final class RedisIdempotencyLock implements IdempotencyLockInterface
{
    private mixed $redis;

    /**
     * @param mixed $redis \Redis or Predis\Client instance
     */
    public function __construct(mixed $redis)
    {
        $this->redis = $redis;
    }

    public function acquire(string $eventId, int $ttlSeconds = 60): bool
    {
        $completedKey = "webhook:completed:{$eventId}";
        if ($this->redis->exists($completedKey)) {
            return false;
        }

        $lockKey = "webhook:lock:{$eventId}";
        // Atomic SET with NX (not exists) and EX (expire seconds)
        // Returns true if key was set, false if key already existed
        $result = $this->redis->set($lockKey, 'in_progress', ['nx', 'ex' => $ttlSeconds]);
        return (bool)$result;
    }

    public function markCompleted(string $eventId, int $retentionSeconds = 86400): void
    {
        $lockKey = "webhook:lock:{$eventId}";
        $completedKey = "webhook:completed:{$eventId}";

        $this->redis->del($lockKey);
        $this->redis->set($completedKey, '1', ['ex' => $retentionSeconds]);
    }

    public function release(string $eventId): void
    {
        $lockKey = "webhook:lock:{$eventId}";
        $this->redis->del($lockKey);
    }

    public function isCompleted(string $eventId): bool
    {
        $completedKey = "webhook:completed:{$eventId}";
        return (bool)$this->redis->exists($completedKey);
    }
}
