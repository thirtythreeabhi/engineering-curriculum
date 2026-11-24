<?php

declare(strict_types=1);

namespace App\Service;

use App\Database\ConnectionInterface;
use App\Database\IsolationLevel;
use App\Domain\Order;
use App\Domain\OrderItem;
use App\Domain\OrderStatus;
use App\Exceptions\DomainException;
use App\Exceptions\InsufficientStockException;
use App\Exceptions\PaymentFailedException;
use App\Exceptions\TransactionException;
use App\Repository\OrderRepositoryInterface;
use App\Repository\ProductRepositoryInterface;

final class OrderPlacementService
{
    public function __construct(
        private ConnectionInterface $connection,
        private ProductRepositoryInterface $productRepository,
        private OrderRepositoryInterface $orderRepository
    ) {}

    /**
     * Atomically validates stock, decrements inventory, creates order, and processes payment.
     *
     * @param int $customerId
     * @param array<int, array{productId: int, quantity: int}> $itemsInput
     * @param float $paymentAmount
     * @return Order
     *
     * @throws InsufficientStockException
     * @throws PaymentFailedException
     * @throws TransactionException
     */
    public function placeOrder(int $customerId, array $itemsInput, float $paymentAmount): Order
    {
        if (empty($itemsInput)) {
            throw new DomainException("Cannot place an empty order.");
        }

        // Begin transaction with SERIALIZABLE isolation to prevent write skew and phantom reads
        $this->connection->beginTransaction(IsolationLevel::SERIALIZABLE);

        try {
            $orderItems = [];
            $totalAmount = 0.0;

            foreach ($itemsInput as $input) {
                $productId = (int)$input['productId'];
                $quantity = (int)$input['quantity'];

                // Pessimistic locking: SELECT ... FOR UPDATE
                $product = $this->productRepository->findByIdForUpdate($productId);

                if ($product === null) {
                    throw new DomainException("Product with ID {$productId} not found.");
                }

                if ($product->stockQuantity < $quantity) {
                    throw new InsufficientStockException($productId, $quantity, $product->stockQuantity);
                }

                // Deduct stock atomically
                $newStock = $product->stockQuantity - $quantity;
                $this->productRepository->updateStock($productId, $newStock);

                $item = new OrderItem(
                    productId: $product->id,
                    sku: $product->sku,
                    quantity: $quantity,
                    unitPrice: $product->price
                );

                $orderItems[] = $item;
                $totalAmount += $item->getSubtotal();
            }

            $totalAmount = round($totalAmount, 2);

            // Verify payment
            if ($paymentAmount < $totalAmount) {
                throw new PaymentFailedException(
                    sprintf("Insufficient funds: needed $%.2f, received $%.2f", $totalAmount, $paymentAmount),
                    $customerId,
                    $paymentAmount
                );
            }

            $order = new Order(
                id: null,
                customerId: $customerId,
                status: OrderStatus::CONFIRMED,
                items: $orderItems,
                totalAmount: $totalAmount
            );

            $orderId = $this->orderRepository->save($order);

            $this->connection->commit();

            return new Order(
                id: $orderId,
                customerId: $customerId,
                status: OrderStatus::CONFIRMED,
                items: $orderItems,
                totalAmount: $totalAmount
            );
        } catch (\Throwable $e) {
            if ($this->connection->inTransaction()) {
                $this->connection->rollBack();
            }
            if ($e instanceof DomainException) {
                throw $e;
            }
            throw new TransactionException("Order transaction failed: " . $e->getMessage(), $e);
        }
    }
}
