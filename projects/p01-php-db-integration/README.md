# Project 01: Modern PHP 8.3 E-Commerce Order Service with Pure PDO Transactions

Production-grade PHP 8.3 implementation of an e-commerce order processing pipeline utilizing pure PDO, explicit database transactions, pessimistic row locking (`SELECT ... FOR UPDATE`), transaction isolation levels (`SERIALIZABLE`), prepared statements, and domain exceptions.

## Key Architectural Highlights

1. **Explicit Isolation Levels & Atomic Transactions**:
   - Every order placement begins with an explicit transaction isolation level (`SET TRANSACTION ISOLATION LEVEL SERIALIZABLE`) to eliminate phantom reads, dirty reads, and non-repeatable reads.
   - Atomic rollback in catch blocks ensures zero partial state updates on failure.

2. **Pessimistic Locking (`SELECT ... FOR UPDATE`)**:
   - Product inventory is locked at the row level during stock verification to prevent race conditions and inventory overselling under high concurrency.

3. **Strict Domain Model & Typed Exceptions**:
   - Pure PHP 8.3 typed properties, readonly classes, and backed enums (`OrderStatus`).
   - Domain-specific exceptions (`InsufficientStockException`, `PaymentFailedException`, `OrderNotFoundException`) ensure business errors are cleanly separated from low-level infrastructure failures.

4. **Production PDO Hardening**:
   - `PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION`: guarantees all database anomalies trigger exceptions.
   - `PDO::ATTR_EMULATE_PREPARES => false`: uses genuine engine-level prepared statements to protect against SQL injection.
   - `PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC`: avoids duplicated numerical indices in memory.

## Directory Structure

```
p01-php-db-integration/
├── composer.json
├── README.md
├── src/
│   ├── Database/
│   │   ├── ConnectionInterface.php
│   │   ├── DatabaseConnectionFactory.php
│   │   ├── IsolationLevel.php
│   │   ├── MockTransactionalConnection.php
│   │   ├── PdoConnection.php
│   │   └── PreparedStatementInterface.php
│   ├── Domain/
│   │   ├── Order.php
│   │   ├── OrderItem.php
│   │   ├── OrderStatus.php
│   │   └── Product.php
│   ├── Exceptions/
│   │   ├── DomainException.php
│   │   ├── InsufficientStockException.php
│   │   ├── OrderNotFoundException.php
│   │   ├── PaymentFailedException.php
│   │   └── TransactionException.php
│   ├── Repository/
│   │   ├── OrderRepository.php
│   │   ├── OrderRepositoryInterface.php
│   │   ├── ProductRepository.php
│   │   └── ProductRepositoryInterface.php
│   └── Service/
│       └── OrderPlacementService.php
└── tests/
    ├── OrderPlacementServiceTest.php
    └── run_tests.php
```

## Running the Tests

Execute the test suite using standard PHP CLI:

```bash
php tests/run_tests.php
```

Or with PHPUnit (if installed):
```bash
phpunit tests/
```

## Production Deployment & Database Configuration

To connect to a live PostgreSQL or MySQL database in production:

```php
use App\Database\DatabaseConnectionFactory;

$connection = DatabaseConnectionFactory::create(
    dsn: 'pgsql:host=localhost;port=5432;dbname=ecommerce;sslmode=require',
    username: 'app_user',
    password: 'secure_password'
);
```
