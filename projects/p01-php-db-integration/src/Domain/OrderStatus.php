<?php

declare(strict_types=1);

namespace App\Domain;

enum OrderStatus: string
{
    case PENDING = 'pending';
    case CONFIRMED = 'confirmed';
    case PROCESSING = 'processing';
    case COMPLETED = 'completed';
    case CANCELLED = 'cancelled';
    case FAILED = 'failed';

    public function isFinal(): bool
    {
        return match($this) {
            self::COMPLETED, self::CANCELLED, self::FAILED => true,
            default => false,
        };
    }
}
