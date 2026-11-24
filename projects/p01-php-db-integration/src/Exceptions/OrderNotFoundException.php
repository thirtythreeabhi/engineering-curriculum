<?php

declare(strict_types=1);

namespace App\Exceptions;

final class OrderNotFoundException extends DomainException
{
    public function __construct(int $orderId)
    {
        parent::__construct("Order with ID {$orderId} was not found.");
    }
}
