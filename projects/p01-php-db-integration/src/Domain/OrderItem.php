<?php

declare(strict_types=1);

namespace App\Domain;

final readonly class OrderItem
{
    public function __construct(
        public int $productId,
        public string $sku,
        public int $quantity,
        public float $unitPrice
    ) {
        if ($this->quantity <= 0) {
            throw new \InvalidArgumentException("Order item quantity must be positive, got: {$this->quantity}");
        }
        if ($this->unitPrice < 0.0) {
            throw new \InvalidArgumentException("Unit price cannot be negative, got: {$this->unitPrice}");
        }
    }

    public function getSubtotal(): float
    {
        return round($this->unitPrice * $this->quantity, 2);
    }
}
