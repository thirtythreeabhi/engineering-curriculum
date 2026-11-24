<?php

declare(strict_types=1);

namespace App\Tests;

use App\Database\IsolationLevel;
use App\Database\MockTransactionalConnection;
use App\Domain\OrderStatus;
use App\Exceptions\InsufficientStockException;
use App\Exceptions\PaymentFailedException;
use App\Repository\OrderRepository;
use App\Repository\ProductRepository;
use App\Service\OrderPlacementService;

final class OrderPlacementServiceTest
{
    private MockTransactionalConnection $db;
    private ProductRepository $productRepo;
    private OrderRepository $orderRepo;
    private OrderPlacementService $service;

    public function setUp(): void
    {
        $this->db = new MockTransactionalConnection();
        $this->productRepo = new ProductRepository($this->db);
        $this->orderRepo = new OrderRepository($this->db);
        $this->service = new OrderPlacementService($this->db, $this->productRepo, $this->orderRepo);

        // Seed products
        $this->db->tables['products'] = [
            1 => ['id' => 1, 'sku' => 'LAPTOP-PRO', 'name' => 'Pro Laptop', 'price' => 1299.99, 'stock_quantity' => 10],
            2 => ['id' => 2, 'sku' => 'USB-C-CABLE', 'name' => 'USB-C Cable', 'price' => 19.99, 'stock_quantity' => 50],
            3 => ['id' => 3, 'sku' => 'DESK-MAT', 'name' => 'Desk Mat', 'price' => 29.50, 'stock_quantity' => 2],
        ];
    }

    public function testSuccessfulOrderPlacement(): void
    {
        $this->setUp();

        $items = [
            ['productId' => 1, 'quantity' => 2], // 2 * 1299.99 = 2599.98
            ['productId' => 2, 'quantity' => 1], // 1 * 19.99 = 19.99 => total 2619.97
        ];

        $order = $this->service->placeOrder(customerId: 42, itemsInput: $items, paymentAmount: 2620.00);

        assert($order->id !== null, "Order ID should be assigned");
        assert($order->getStatus() === OrderStatus::CONFIRMED, "Order status should be confirmed");
        assert($order->totalAmount === 2619.97, "Total amount should match calculated subtotal");
        assert(count($order->getItems()) === 2, "Order should have 2 items");

        // Verify transaction semantics
        assert($this->db->beginTransactionCalls === 1, "Should call beginTransaction once");
        assert($this->db->commitCalls === 1, "Should call commit once");
        assert($this->db->rollBackCalls === 0, "Should not call rollBack on success");
        assert($this->db->currentIsolationLevel === IsolationLevel::SERIALIZABLE, "Isolation level must be SERIALIZABLE");

        // Verify stock was decremented in database
        assert($this->db->tables['products'][1]['stock_quantity'] === 8, "Stock for product 1 should decrease from 10 to 8");
        assert($this->db->tables['products'][2]['stock_quantity'] === 49, "Stock for product 2 should decrease from 50 to 49");
    }

    public function testInsufficientStockRollback(): void
    {
        $this->setUp();

        $items = [
            ['productId' => 3, 'quantity' => 5], // Only 2 in stock!
        ];

        $exceptionCaught = false;
        try {
            $this->service->placeOrder(customerId: 42, itemsInput: $items, paymentAmount: 500.00);
        } catch (InsufficientStockException $e) {
            $exceptionCaught = true;
        }

        assert($exceptionCaught, "InsufficientStockException must be thrown");
        assert($this->db->beginTransactionCalls === 1, "Should have started transaction");
        assert($this->db->rollBackCalls === 1, "Must rollback transaction on stock failure");
        assert($this->db->commitCalls === 0, "Must not commit failed order");
        // Verify stock was restored by rollback
        assert($this->db->tables['products'][3]['stock_quantity'] === 2, "Stock must remain unchanged after rollback");
    }

    public function testPaymentFailureRollback(): void
    {
        $this->setUp();

        $items = [
            ['productId' => 2, 'quantity' => 2], // 2 * 19.99 = 39.98
        ];

        $exceptionCaught = false;
        try {
            // Provide insufficient payment: 20.00 instead of 39.98
            $this->service->placeOrder(customerId: 100, itemsInput: $items, paymentAmount: 20.00);
        } catch (PaymentFailedException $e) {
            $exceptionCaught = true;
        }

        assert($exceptionCaught, "PaymentFailedException must be thrown");
        assert($this->db->beginTransactionCalls === 1, "Should begin transaction");
        assert($this->db->rollBackCalls === 1, "Must rollback transaction on payment failure");
        assert($this->db->commitCalls === 0, "Must not commit on payment failure");
        // Verify stock deduction was reverted
        assert($this->db->tables['products'][2]['stock_quantity'] === 50, "Stock must be reverted on payment failure");
    }

    public function testPessimisticLockQueryExecuted(): void
    {
        $this->setUp();

        $items = [
            ['productId' => 1, 'quantity' => 1],
        ];

        $this->service->placeOrder(customerId: 1, itemsInput: $items, paymentAmount: 1300.00);

        // Find SELECT FOR UPDATE in executed queries
        $hasForUpdate = false;
        foreach ($this->db->executedQueries as $entry) {
            if (stripos($entry['sql'], 'FOR UPDATE') !== false) {
                $hasForUpdate = true;
                break;
            }
        }

        assert($hasForUpdate, "Product lookup must execute SELECT ... FOR UPDATE query");
    }
}
