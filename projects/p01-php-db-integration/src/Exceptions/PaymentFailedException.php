<?php

declare(strict_types=1);

namespace App\Exceptions;

final class PaymentFailedException extends DomainException
{
    public function __construct(string $reason, int $customerId, float $amount)
    {
        parent::__construct(
            sprintf("Payment failed for customer %d (amount: $%.2f): %s", $customerId, $amount, $reason)
        );
    }
}
