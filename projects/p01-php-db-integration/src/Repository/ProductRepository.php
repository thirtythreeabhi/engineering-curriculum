<?php

declare(strict_types=1);

namespace App\Repository;

use App\Database\ConnectionInterface;
use App\Domain\Product;

final class ProductRepository implements ProductRepositoryInterface
{
    public function __construct(
        private ConnectionInterface $connection,
        private bool $supportsForUpdate = true
    ) {}

    public function findByIdForUpdate(int $id): ?Product
    {
        $sql = $this->supportsForUpdate
            ? "SELECT id, sku, name, price, stock_quantity FROM products WHERE id = :id FOR UPDATE"
            : "SELECT id, sku, name, price, stock_quantity FROM products WHERE id = :id";
        $stmt = $this->connection->prepare($sql);
        $stmt->execute(['id' => $id]);
        $row = $stmt->fetch();

        if ($row === false || $row === null) {
            return null;
        }

        return new Product(
            (int)$row['id'],
            (string)$row['sku'],
            (string)$row['name'],
            (float)$row['price'],
            (int)$row['stock_quantity']
        );
    }

    public function updateStock(int $id, int $newStock): void
    {
        $stmt = $this->connection->prepare(
            "UPDATE products SET stock_quantity = :stock WHERE id = :id"
        );
        $stmt->execute([
            'stock' => $newStock,
            'id' => $id,
        ]);
    }
}
