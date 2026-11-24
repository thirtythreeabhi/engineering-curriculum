<?php

declare(strict_types=1);

namespace App\Domain;

final class Order
{
    /**
     * @param OrderItem[] $items
     */
    public function __construct(
        public readonly ?int $id,
        public readonly int $customerId,
        private OrderStatus $status,
        private array $items,
        public readonly float $totalAmount,
        public readonly \DateTimeImmutable $createdAt = new \DateTimeImmutable()
    ) {}

    public function getStatus(): OrderStatus
    {
        return $this->status;
    }

    public function setStatus(OrderStatus $newStatus): void
    {
        $this->status = $newStatus;
    }

    /**
     * @return OrderItem[]
     */
    public function getItems(): array
    {
        return $this->items;
    }
}
