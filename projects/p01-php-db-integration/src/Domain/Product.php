<?php

declare(strict_types=1);

namespace App\Domain;

final readonly class Product
{
    public function __construct(
        public int $id,
        public string $sku,
        public string $name,
        public float $price,
        public int $stockQuantity
    ) {
        if ($this->price < 0.0) {
            throw new \InvalidArgumentException("Product price cannot be negative: {$this->price}");
        }
        if ($this->stockQuantity < 0) {
            throw new \InvalidArgumentException("Stock quantity cannot be negative: {$this->stockQuantity}");
        }
    }

    public function withUpdatedStock(int $newStock): self
    {
        return new self($this->id, $this->sku, $this->name, $this->price, $newStock);
    }
}
