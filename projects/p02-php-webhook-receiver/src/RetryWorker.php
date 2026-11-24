<?php

declare(strict_types=1);

namespace WebhookReceiver;

final class RetryWorker
{
    /** @var array<int, array{event: WebhookEvent, reason: string}> */
    public array $deadLetterQueue = [];

    /** @var array<int, array{event: WebhookEvent, delayMs: int, attempt: int}> */
    public array $scheduledRetries = [];

    public function __construct(
        private int $maxRetries = 5,
        private int $baseDelayMs = 1000,
        private int $maxDelayMs = 32000,
        private int $jitterMs = 250
    ) {}

    /**
     * Calculates the exponential backoff delay with full jitter.
     * delay = min(maxDelay, baseDelay * (2 ^ (attempt - 1))) + uniform_jitter
     */
    public function calculateDelay(int $attempt): int
    {
        $exponential = $this->baseDelayMs * (2 ** max(0, $attempt - 1));
        $capped = min($this->maxDelayMs, $exponential);
        $jitter = random_int(0, $this->jitterMs);
        return $capped + $jitter;
    }

    /**
     * Processes an event failure: either schedules a delayed retry or moves to DLQ.
     */
    public function handleFailure(WebhookEvent $event, int $currentAttempt, string $reason): array
    {
        if ($currentAttempt >= $this->maxRetries) {
            $dlqRecord = [
                'event' => $event,
                'reason' => $reason,
                'failedAt' => time(),
                'totalAttempts' => $currentAttempt,
            ];
            $this->deadLetterQueue[] = $dlqRecord;
            return ['status' => 'dlq', 'attempt' => $currentAttempt, 'reason' => $reason];
        }

        $nextAttempt = $currentAttempt + 1;
        $delayMs = $this->calculateDelay($nextAttempt);
        $this->scheduledRetries[] = [
            'event' => $event,
            'delayMs' => $delayMs,
            'attempt' => $nextAttempt,
        ];

        return [
            'status' => 'scheduled',
            'nextAttempt' => $nextAttempt,
            'delayMs' => $delayMs,
        ];
    }
}
