<?php

declare(strict_types=1);

namespace WebhookReceiver;

final readonly class WebhookEvent
{
    public function __construct(
        public string $eventId,
        public int $timestamp,
        public string $eventType,
        public array $data,
        public string $rawPayload
    ) {}
}

final readonly class WebhookResponse
{
    public function __construct(
        public int $statusCode,
        public string $message,
        public array $headers = []
    ) {}
}
