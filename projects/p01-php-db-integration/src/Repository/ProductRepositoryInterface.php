<?php

declare(strict_types=1);

namespace App\Repository;

use App\Domain\Product;

interface ProductRepositoryInterface
{
    /**
     * Retrieves product and locks row with FOR UPDATE when inside transaction.
     */
    public function findByIdForUpdate(int $id): ?Product;

    public function updateStock(int $id, int $newStock): void;
}
