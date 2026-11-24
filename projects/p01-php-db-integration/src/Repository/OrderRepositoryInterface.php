<?php

declare(strict_types=1);

namespace App\Repository;

use App\Domain\Order;

interface OrderRepositoryInterface
{
    public function save(Order $order): int;

    public function findById(int $id): ?Order;
}
