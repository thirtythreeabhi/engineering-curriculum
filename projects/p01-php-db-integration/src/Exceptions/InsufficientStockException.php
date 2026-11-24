<?php

declare(strict_types=1);

namespace App\Exceptions;

final class InsufficientStockException extends DomainException
{
    public function __construct(int $productId, int $requested, int $available)
    {
        parent::__construct(
            sprintf("Insufficient stock for product ID %d: requested %d, but only %d available.", $productId, $requested, $available)
        );
    }
}
