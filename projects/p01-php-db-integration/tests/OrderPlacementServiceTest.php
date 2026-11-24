<?php

declare(strict_types=1);

namespace App\Tests;

use App\Database\ConnectionInterface;
use App\Database\DatabaseConnectionFactory;
use App\Database\IsolationLevel;
use App\Database\MockTransactionalConnection;
use App\Database\PdoConnection;
use App\Database\PreparedStatementInterface;
use App\Domain\Money;
use App\Domain\OrderStatus;
use App\Exceptions\InsufficientStockException;
use App\Exceptions\PaymentFailedException;
use App\Repository\OrderRepository;
use App\Repository\ProductRepository;
use App\Service\OrderPlacementService;

final class DriverSpyPdo extends \PDO
{
    /** @var list<string> */
    public array $log = [];

    public function __construct(private string $driverName) {}

    public function getAttribute(int $attribute): mixed
    {
        if ($attribute === \PDO::ATTR_DRIVER_NAME) {
            return $this->driverName;
        }
        return null;
    }

    public function beginTransaction(): bool
    {
        $this->log[] = 'BEGIN';
        return true;
    }

    public function exec(string $statement): int|false
    {
        $this->log[] = $statement;
        return 0;
    }
}

final class FfiSqliteConnection implements ConnectionInterface
{
    private \FFI $ffi;
    private \FFI\CData $db;
    private bool $inTx = false;
    private int $lastId = 0;

    public function __construct()
    {
        $this->ffi = \FFI::cdef(<<<'CDEF'
            typedef struct sqlite3 sqlite3;
            typedef struct sqlite3_stmt sqlite3_stmt;
            int sqlite3_open(const char *filename, sqlite3 **ppDb);
            int sqlite3_close(sqlite3 *db);
            int sqlite3_exec(sqlite3 *db, const char *sql, void *cb, void *arg, char **errmsg);
            void sqlite3_free(void *ptr);
            const char *sqlite3_errmsg(sqlite3 *db);
            long long sqlite3_last_insert_rowid(sqlite3 *db);
            int sqlite3_changes(sqlite3 *db);
            int sqlite3_prepare_v2(sqlite3 *db, const char *zSql, int nByte, sqlite3_stmt **ppStmt, const char **pzTail);
            int sqlite3_step(sqlite3_stmt *pStmt);
            int sqlite3_reset(sqlite3_stmt *pStmt);
            int sqlite3_clear_bindings(sqlite3_stmt *pStmt);
            int sqlite3_finalize(sqlite3_stmt *pStmt);
            int sqlite3_bind_parameter_index(sqlite3_stmt *pStmt, const char *zName);
            int sqlite3_bind_int64(sqlite3_stmt *pStmt, int idx, long long val);
            int sqlite3_bind_double(sqlite3_stmt *pStmt, int idx, double val);
            int sqlite3_bind_text(sqlite3_stmt *pStmt, int idx, const char *val, int nBytes, void (*destructor)(void*));
            int sqlite3_column_count(sqlite3_stmt *pStmt);
            const char *sqlite3_column_name(sqlite3_stmt *pStmt, int N);
            int sqlite3_column_type(sqlite3_stmt *pStmt, int iCol);
            long long sqlite3_column_int64(sqlite3_stmt *pStmt, int iCol);
            double sqlite3_column_double(sqlite3_stmt *pStmt, int iCol);
            const unsigned char *sqlite3_column_text(sqlite3_stmt *pStmt, int iCol);
        CDEF, 'libsqlite3.so.0');

        $ppDb = $this->ffi->new('sqlite3*');
        if ($this->ffi->sqlite3_open(':memory:', \FFI::addr($ppDb)) !== 0) {
            throw new \RuntimeException('Unable to open SQLite :memory:');
        }
        $this->db = $ppDb;
    }

    public function __destruct()
    {
        if (isset($this->db)) {
            $this->ffi->sqlite3_close($this->db);
        }
    }

    public function beginTransaction(?IsolationLevel $level = null): bool
    {
        $this->exec('BEGIN IMMEDIATE');
        $this->inTx = true;
        return true;
    }

    public function commit(): bool
    {
        $this->exec('COMMIT');
        $this->inTx = false;
        return true;
    }

    public function rollBack(): bool
    {
        $this->exec('ROLLBACK');
        $this->inTx = false;
        return true;
    }

    public function inTransaction(): bool
    {
        return $this->inTx;
    }

    public function exec(string $sql): int
    {
        $err = $this->ffi->new('char*');
        $rc = $this->ffi->sqlite3_exec($this->db, $sql, null, null, \FFI::addr($err));
        if ($rc !== 0) {
            $msg = \FFI::isNull($err) ? $this->ffi->sqlite3_errmsg($this->db) : \FFI::string($err);
            if (!\FFI::isNull($err)) {
                $this->ffi->sqlite3_free($err);
            }
            throw new \RuntimeException("SQLite error: {$msg}");
        }
        return (int)$this->ffi->sqlite3_changes($this->db);
    }

    public function lastInsertId(?string $name = null): string|int
    {
        return (int)$this->ffi->sqlite3_last_insert_rowid($this->db);
    }

    public function prepare(string $sql): PreparedStatementInterface
    {
        $ppStmt = $this->ffi->new('sqlite3_stmt*');
        if ($this->ffi->sqlite3_prepare_v2($this->db, $sql, strlen($sql), \FFI::addr($ppStmt), null) !== 0) {
            throw new \RuntimeException("Prepare failed: " . $this->ffi->sqlite3_errmsg($this->db));
        }

        return new class ($this->ffi, $this->db, $ppStmt) implements PreparedStatementInterface {
            private array $rows = [];
            private int $cursor = 0;
            private int $affected = 0;

            public function __construct(
                private \FFI $ffi,
                private \FFI\CData $db,
                private \FFI\CData $stmt
            ) {}

            public function __destruct()
            {
                $this->ffi->sqlite3_finalize($this->stmt);
            }

            public function execute(?array $params = null): bool
            {
                $this->ffi->sqlite3_reset($this->stmt);
                $this->ffi->sqlite3_clear_bindings($this->stmt);
                $this->rows = [];
                $this->cursor = 0;

                foreach ($params ?? [] as $key => $val) {
                    $name = str_starts_with((string)$key, ':') ? (string)$key : ':' . $key;
                    $idx = $this->ffi->sqlite3_bind_parameter_index($this->stmt, $name);
                    if ($idx <= 0) {
                        throw new \RuntimeException("Unknown param {$name}");
                    }
                    if (is_int($val)) {
                        $this->ffi->sqlite3_bind_int64($this->stmt, $idx, $val);
                    } elseif (is_float($val)) {
                        $this->ffi->sqlite3_bind_double($this->stmt, $idx, $val);
                    } else {
                        $str = (string)$val;
                        $transient = \FFI::cast('void(*)(void*)', -1);
                        $this->ffi->sqlite3_bind_text($this->stmt, $idx, $str, strlen($str), $transient);
                    }
                }

                $colCount = $this->ffi->sqlite3_column_count($this->stmt);
                while (true) {
                    $rc = $this->ffi->sqlite3_step($this->stmt);
                    if ($rc === 100) {
                        $row = [];
                        for ($c = 0; $c < $colCount; $c++) {
                            $col = $this->ffi->sqlite3_column_name($this->stmt, $c);
                            $type = $this->ffi->sqlite3_column_type($this->stmt, $c);
                            if ($type === 1) {
                                $row[$col] = (int)$this->ffi->sqlite3_column_int64($this->stmt, $c);
                            } elseif ($type === 2) {
                                $row[$col] = (float)$this->ffi->sqlite3_column_double($this->stmt, $c);
                            } elseif ($type === 5) {
                                $row[$col] = null;
                            } else {
                                $txt = $this->ffi->sqlite3_column_text($this->stmt, $c);
                                $row[$col] = \FFI::isNull($txt) ? '' : \FFI::string(\FFI::cast('char*', $txt));
                            }
                        }
                        $this->rows[] = $row;
                    } elseif ($rc === 101) {
                        break;
                    } else {
                        throw new \RuntimeException("SQLite step error: " . $this->ffi->sqlite3_errmsg($this->db));
                    }
                }
                $this->affected = (int)$this->ffi->sqlite3_changes($this->db);
                return true;
            }

            public function fetch(): array|false
            {
                return $this->rows[$this->cursor++] ?? false;
            }

            public function fetchAll(): array
            {
                return $this->rows;
            }

            public function rowCount(): int
            {
                return $this->affected;
            }
        };
    }
}

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

    public function testPdoConnectionDriverAwareIsolationOrdering(): void
    {
        // PostgreSQL MUST run BEGIN before SET TRANSACTION ISOLATION LEVEL
        $pgSpy = new DriverSpyPdo('pgsql');
        $pgConn = new PdoConnection($pgSpy);
        $pgConn->beginTransaction(IsolationLevel::SERIALIZABLE);
        assert($pgSpy->log === [
            'BEGIN',
            'SET TRANSACTION ISOLATION LEVEL SERIALIZABLE',
        ], "PostgreSQL must execute BEGIN before SET TRANSACTION ISOLATION LEVEL");

        // MySQL runs SET TRANSACTION ISOLATION LEVEL before BEGIN
        $mysqlSpy = new DriverSpyPdo('mysql');
        $mysqlConn = new PdoConnection($mysqlSpy);
        $mysqlConn->beginTransaction(IsolationLevel::REPEATABLE_READ);
        assert($mysqlSpy->log === [
            'SET TRANSACTION ISOLATION LEVEL REPEATABLE READ',
            'BEGIN',
        ], "MySQL must execute SET TRANSACTION ISOLATION LEVEL before BEGIN");

        // SQLite must skip unsupported SET TRANSACTION ISOLATION LEVEL
        $sqliteSpy = new DriverSpyPdo('sqlite');
        $sqliteConn = new PdoConnection($sqliteSpy);
        $sqliteConn->beginTransaction(IsolationLevel::SERIALIZABLE);
        assert($sqliteSpy->log === ['BEGIN'], "SQLite must omit SET TRANSACTION ISOLATION LEVEL");
    }

    public function testMoneyIntegerCentsArithmetic(): void
    {
        $a = Money::fromFloat(0.10);
        $b = Money::fromFloat(0.20);
        $sum = $a->add($b);
        assert($sum->cents === 30, "0.10 + 0.20 in integer cents must be exact 30 cents");
        assert($sum->multiply(3)->cents === 90);
        assert($sum->format() === 'USD 0.30');
    }

    public function testRealSqliteIntegrationOrderAndRollback(): void
    {
        $conn = in_array('sqlite', \PDO::getAvailableDrivers(), true)
            ? DatabaseConnectionFactory::create('sqlite::memory:')
            : new FfiSqliteConnection();

        $conn->exec('CREATE TABLE products (id INTEGER PRIMARY KEY, sku TEXT NOT NULL, name TEXT NOT NULL, price REAL NOT NULL, stock_quantity INTEGER NOT NULL CHECK (stock_quantity >= 0))');
        $conn->exec('CREATE TABLE orders (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER NOT NULL, status TEXT NOT NULL, total_amount REAL NOT NULL, created_at TEXT NOT NULL)');
        $conn->exec('CREATE TABLE order_items (id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER NOT NULL, product_id INTEGER NOT NULL, sku TEXT NOT NULL, quantity INTEGER NOT NULL, unit_price REAL NOT NULL)');

        $seed = $conn->prepare('INSERT INTO products (id, sku, name, price, stock_quantity) VALUES (:id, :sku, :name, :price, :stock)');
        $seed->execute(['id' => 1, 'sku' => 'LAPTOP-PRO', 'name' => 'Pro Laptop', 'price' => 1299.99, 'stock' => 5]);
        $seed->execute(['id' => 2, 'sku' => 'USB-C-CABLE', 'name' => 'USB-C Cable', 'price' => 19.99, 'stock' => 10]);

        $productRepo = new ProductRepository($conn, supportsForUpdate: false);
        $orderRepo = new OrderRepository($conn);
        $service = new OrderPlacementService($conn, $productRepo, $orderRepo);

        // 1. Committed order persists rows and decrements stock
        $order = $service->placeOrder(7, [['productId' => 1, 'quantity' => 2]], 2600.00);
        assert($order->id === 1);
        $loaded = $orderRepo->findById(1);
        assert($loaded !== null && $loaded->customerId === 7);
        assert($productRepo->findByIdForUpdate(1)?->stockQuantity === 3);

        // 2. Payment failure rolls back stock decrement inside real SQLite engine
        $rolledBack = false;
        try {
            $service->placeOrder(8, [['productId' => 2, 'quantity' => 4]], 10.00);
        } catch (PaymentFailedException) {
            $rolledBack = true;
        }
        assert($rolledBack === true);
        assert($productRepo->findByIdForUpdate(2)?->stockQuantity === 10, "SQLite ROLLBACK must restore stock to 10");
        assert($orderRepo->findById(2) === null, "Rolled-back order must not exist in orders table");
    }
}
