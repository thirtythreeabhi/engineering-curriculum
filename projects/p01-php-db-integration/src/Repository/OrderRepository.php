<?php

declare(strict_types=1);

namespace App\Repository;

use App\Database\ConnectionInterface;
use App\Domain\Order;
use App\Domain\OrderItem;
use App\Domain\OrderStatus;

final class OrderRepository implements OrderRepositoryInterface
{
    public function __construct(private ConnectionInterface $connection) {}

    public function save(Order $order): int
    {
        $stmt = $this->connection->prepare(
            "INSERT INTO orders (customer_id, status, total_amount, created_at)
             VALUES (:customer_id, :status, :total_amount, :created_at)"
        );
        $stmt->execute([
            'customer_id' => $order->customerId,
            'status' => $order->getStatus()->value,
            'total_amount' => $order->totalAmount,
            'created_at' => $order->createdAt->format('Y-m-d H:i:s'),
        ]);

        $orderId = (int)$this->connection->lastInsertId('orders_id_seq');

        $itemStmt = $this->connection->prepare(
            "INSERT INTO order_items (order_id, product_id, sku, quantity, unit_price)
             VALUES (:order_id, :product_id, :sku, :quantity, :unit_price)"
        );

        foreach ($order->getItems() as $item) {
            $itemStmt->execute([
                'order_id' => $orderId,
                'product_id' => $item->productId,
                'sku' => $item->sku,
                'quantity' => $item->quantity,
                'unit_price' => $item->unitPrice,
            ]);
        }

        return $orderId;
    }

    public function findById(int $id): ?Order
    {
        $stmt = $this->connection->prepare(
            "SELECT id, customer_id, status, total_amount, created_at FROM orders WHERE id = :id"
        );
        $stmt->execute(['id' => $id]);
        $row = $stmt->fetch();

        if ($row === false || $row === null) {
            return null;
        }

        $itemsStmt = $this->connection->prepare(
            "SELECT product_id, sku, quantity, unit_price FROM order_items WHERE order_id = :order_id"
        );
        $itemsStmt->execute(['order_id' => $id]);
        $itemRows = $itemsStmt->fetchAll();

        $items = [];
        foreach ($itemRows as $iRow) {
            $items[] = new OrderItem(
                (int)$iRow['product_id'],
                (string)$iRow['sku'],
                (int)$iRow['quantity'],
                (float)$iRow['unit_price']
            );
        }

        return new Order(
            (int)$row['id'],
            (int)$row['customer_id'],
            OrderStatus::from((string)$row['status']),
            $items,
            (float)$row['total_amount'],
            new \DateTimeImmutable((string)$row['created_at'])
        );
    }
}
