<?php

declare(strict_types=1);

namespace WebhookReceiver;

/**
 * Atomic Redis Idempotency Lock using a single state key (`SET ... NX EX`)
 * and Lua `EVAL` state guards to eliminate check-then-act (TOCTOU) races.
 *
 * State transitions on key `webhook:idempotency:{eventId}`:
 *   (absent) --[SET NX EX ttl]--> "in_progress:{ownerToken}"
 *   "in_progress:{ownerToken}" --[Lua SET EX retention]--> "completed"
 *   "in_progress:{ownerToken}" --[Lua DEL if value == "in_progress:{ownerToken}"]--> (absent)
 */
final class RedisIdempotencyLock implements IdempotencyLockInterface
{
    private const LUA_MARK_COMPLETED = <<<'LUA'
        local cur = redis.call('GET', KEYS[1])
        if cur == 'completed' then
            return 1
        end
        if cur == ARGV[1] or not cur then
            redis.call('SET', KEYS[1], 'completed', 'EX', tonumber(ARGV[2]))
            return 1
        end
        return 0
    LUA;

    private const LUA_RELEASE_OWNED = <<<'LUA'
        if redis.call('GET', KEYS[1]) == ARGV[1] then
            return redis.call('DEL', KEYS[1])
        end
        return 0
    LUA;

    private mixed $redis;
    /** @var array<string, string> */
    private array $ownerTokens = [];

    /**
     * @param mixed $redis \Redis or Predis\Client instance (or compatible test double)
     */
    public function __construct(mixed $redis)
    {
        $this->redis = $redis;
    }

    private function key(string $eventId): string
    {
        return "webhook:idempotency:{$eventId}";
    }

    public function acquire(string $eventId, int $ttlSeconds = 60): bool
    {
        $key = $this->key($eventId);
        $token = 'in_progress:' . bin2hex(random_bytes(8));

        // Single atomic Redis command: succeeds ONLY if key does not exist
        // (neither in-progress nor completed). Eliminates TOCTOU race.
        $acquired = (bool)$this->redis->set($key, $token, ['nx', 'ex' => $ttlSeconds]);
        if ($acquired) {
            $this->ownerTokens[$eventId] = $token;
        }
        return $acquired;
    }

    public function markCompleted(string $eventId, int $retentionSeconds = 86400): void
    {
        $key = $this->key($eventId);
        $token = $this->ownerTokens[$eventId] ?? '';

        if (method_exists($this->redis, 'eval')) {
            $this->redis->eval(self::LUA_MARK_COMPLETED, [$key, $token, (string)$retentionSeconds], 1);
        } else {
            // Single atomic overwrite preserves continuity without any gap window
            $this->redis->set($key, 'completed', ['ex' => $retentionSeconds]);
        }
        unset($this->ownerTokens[$eventId]);
    }

    public function release(string $eventId): void
    {
        $key = $this->key($eventId);
        $token = $this->ownerTokens[$eventId] ?? '';

        if (method_exists($this->redis, 'eval')) {
            // Only delete if we still own the in-progress lock; NEVER delete 'completed'!
            $this->redis->eval(self::LUA_RELEASE_OWNED, [$key, $token], 1);
        } elseif ($token !== '' && $this->redis->get($key) === $token) {
            $this->redis->del($key);
        }
        unset($this->ownerTokens[$eventId]);
    }

    public function isCompleted(string $eventId): bool
    {
        return $this->redis->get($this->key($eventId)) === 'completed';
    }
}
