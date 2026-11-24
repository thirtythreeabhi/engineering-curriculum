<?php

declare(strict_types=1);

/**
 * Exercise 1.2: PHP PDO Transaction Boundaries, Prepared Statements, and Integer Cents
 *
 * Problem:
 * In a banking transfer, moving money from Account A to Account B must be atomic.
 * If crediting Account B fails, deducting Account A must be rolled back. Furthermore:
 * - Monetary balances MUST be stored as exact integer minor units (cents), never floats.
 * - Queries MUST use genuine prepared statements with bound parameters (no SQL injection).
 * - Database constraints (CHECK (balance_cents >= 0)) act as the final solvency guard.
 *
 * Driver note:
 * Uses native PDO('sqlite::memory:') when pdo_sqlite is installed. In minimal CLI
 * environments where pdo.so is present without pdo_sqlite.so, falls back transparently
 * to libsqlite3.so.0 via PHP FFI so real SQLite SQL, BEGIN IMMEDIATE, prepared parameter
 * binding, and CHECK constraint rollbacks still execute against the real SQLite C engine.
 */

interface SqliteStatementInterface
{
    public function execute(array $params = []): bool;

    public function fetchAssoc(): array|false;
}

interface SqliteDatabaseInterface
{
    public function exec(string $sql): void;

    public function prepare(string $sql): SqliteStatementInterface;

    public function driverLabel(): string;
}

final class NativePdoSqliteDriver implements SqliteDatabaseInterface
{
    private \PDO $pdo;

    public function __construct()
    {
        $this->pdo = new \PDO('sqlite::memory:', null, null, [
            \PDO::ATTR_ERRMODE => \PDO::ERRMODE_EXCEPTION,
            \PDO::ATTR_EMULATE_PREPARES => false,
            \PDO::ATTR_DEFAULT_FETCH_MODE => \PDO::FETCH_ASSOC,
        ]);
    }

    public function exec(string $sql): void
    {
        $this->pdo->exec($sql);
    }

    public function prepare(string $sql): SqliteStatementInterface
    {
        $stmt = $this->pdo->prepare($sql);
        return new class ($stmt) implements SqliteStatementInterface {
            public function __construct(private \PDOStatement $stmt) {}

            public function execute(array $params = []): bool
            {
                return $this->stmt->execute($params);
            }

            public function fetchAssoc(): array|false
            {
                return $this->stmt->fetch(\PDO::FETCH_ASSOC);
            }
        };
    }

    public function driverLabel(): string
    {
        return 'PDO(sqlite::memory:)';
    }
}

final class FfiSqlite3Driver implements SqliteDatabaseInterface
{
    private \FFI $ffi;
    private \FFI\CData $db;

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
            int sqlite3_prepare_v2(sqlite3 *db, const char *zSql, int nByte, sqlite3_stmt **ppStmt, const char **pzTail);
            int sqlite3_step(sqlite3_stmt *pStmt);
            int sqlite3_reset(sqlite3_stmt *pStmt);
            int sqlite3_clear_bindings(sqlite3_stmt *pStmt);
            int sqlite3_finalize(sqlite3_stmt *pStmt);
            int sqlite3_bind_parameter_index(sqlite3_stmt *pStmt, const char *zName);
            int sqlite3_bind_int64(sqlite3_stmt *pStmt, int idx, long long val);
            int sqlite3_bind_text(sqlite3_stmt *pStmt, int idx, const char *val, int nBytes, void (*destructor)(void*));
            int sqlite3_column_count(sqlite3_stmt *pStmt);
            const char *sqlite3_column_name(sqlite3_stmt *pStmt, int N);
            int sqlite3_column_type(sqlite3_stmt *pStmt, int iCol);
            long long sqlite3_column_int64(sqlite3_stmt *pStmt, int iCol);
            const unsigned char *sqlite3_column_text(sqlite3_stmt *pStmt, int iCol);
        CDEF, 'libsqlite3.so.0');

        $ppDb = $this->ffi->new('sqlite3*');
        $rc = $this->ffi->sqlite3_open(':memory:', \FFI::addr($ppDb));
        if ($rc !== 0) {
            throw new \PDOException('Failed to open SQLite :memory: via FFI');
        }
        $this->db = $ppDb;
    }

    public function __destruct()
    {
        if (isset($this->db)) {
            $this->ffi->sqlite3_close($this->db);
        }
    }

    public function exec(string $sql): void
    {
        $errPtr = $this->ffi->new('char*');
        $rc = $this->ffi->sqlite3_exec($this->db, $sql, null, null, \FFI::addr($errPtr));
        if ($rc !== 0) {
            $msg = \FFI::isNull($errPtr) ? $this->ffi->sqlite3_errmsg($this->db) : \FFI::string($errPtr);
            if (!\FFI::isNull($errPtr)) {
                $this->ffi->sqlite3_free($errPtr);
            }
            throw new \PDOException("SQLite error ({$rc}): {$msg}");
        }
    }

    public function prepare(string $sql): SqliteStatementInterface
    {
        $ppStmt = $this->ffi->new('sqlite3_stmt*');
        $rc = $this->ffi->sqlite3_prepare_v2($this->db, $sql, strlen($sql), \FFI::addr($ppStmt), null);
        if ($rc !== 0) {
            $msg = $this->ffi->sqlite3_errmsg($this->db);
            throw new \PDOException("SQLite prepare failed ({$rc}): {$msg}");
        }
        return new class ($this->ffi, $this->db, $ppStmt) implements SqliteStatementInterface {
            private array $rows = [];
            private int $cursor = 0;

            public function __construct(
                private \FFI $ffi,
                private \FFI\CData $db,
                private \FFI\CData $stmt
            ) {}

            public function __destruct()
            {
                $this->ffi->sqlite3_finalize($this->stmt);
            }

            public function execute(array $params = []): bool
            {
                $this->ffi->sqlite3_reset($this->stmt);
                $this->ffi->sqlite3_clear_bindings($this->stmt);
                $this->rows = [];
                $this->cursor = 0;

                foreach ($params as $name => $value) {
                    $paramName = str_starts_with((string)$name, ':') ? (string)$name : ':' . $name;
                    $idx = $this->ffi->sqlite3_bind_parameter_index($this->stmt, $paramName);
                    if ($idx <= 0) {
                        throw new \PDOException("Unknown bound parameter: {$paramName}");
                    }
                    if (is_int($value)) {
                        $this->ffi->sqlite3_bind_int64($this->stmt, $idx, $value);
                    } else {
                        $str = (string)$value;
                        // SQLITE_TRANSIENT = (void*)-1 -> represented via FFI cast
                        $transient = \FFI::cast('void(*)(void*)', -1);
                        $this->ffi->sqlite3_bind_text($this->stmt, $idx, $str, strlen($str), $transient);
                    }
                }

                $colCount = $this->ffi->sqlite3_column_count($this->stmt);
                while (true) {
                    $rc = $this->ffi->sqlite3_step($this->stmt);
                    if ($rc === 100) { // SQLITE_ROW
                        $row = [];
                        for ($c = 0; $c < $colCount; $c++) {
                            $colName = $this->ffi->sqlite3_column_name($this->stmt, $c);
                            $colType = $this->ffi->sqlite3_column_type($this->stmt, $c);
                            if ($colType === 1) { // SQLITE_INTEGER
                                $row[$colName] = (int)$this->ffi->sqlite3_column_int64($this->stmt, $c);
                            } elseif ($colType === 5) { // SQLITE_NULL
                                $row[$colName] = null;
                            } else {
                                $txt = $this->ffi->sqlite3_column_text($this->stmt, $c);
                                $row[$colName] = \FFI::isNull($txt) ? '' : \FFI::string(\FFI::cast('char*', $txt));
                            }
                        }
                        $this->rows[] = $row;
                    } elseif ($rc === 101) { // SQLITE_DONE
                        break;
                    } else {
                        $msg = $this->ffi->sqlite3_errmsg($this->db);
                        throw new \PDOException("SQLite step error ({$rc}): {$msg}");
                    }
                }
                return true;
            }

            public function fetchAssoc(): array|false
            {
                if (!isset($this->rows[$this->cursor])) {
                    return false;
                }
                return $this->rows[$this->cursor++];
            }
        };
    }

    public function driverLabel(): string
    {
        return 'FFI(libsqlite3.so.0::memory:)';
    }
}

final class SqliteBankTransferService
{
    private SqliteDatabaseInterface $db;

    public function __construct(?SqliteDatabaseInterface $db = null)
    {
        if ($db !== null) {
            $this->db = $db;
        } elseif (in_array('sqlite', \PDO::getAvailableDrivers(), true)) {
            $this->db = new NativePdoSqliteDriver();
        } elseif (extension_loaded('ffi')) {
            $this->db = new FfiSqlite3Driver();
        } else {
            throw new \RuntimeException('Neither pdo_sqlite nor PHP FFI (libsqlite3) is available.');
        }

        $this->db->exec(
            'CREATE TABLE accounts (
                account_id TEXT PRIMARY KEY,
                balance_cents INTEGER NOT NULL CHECK (balance_cents >= 0)
            )'
        );

        $seed = $this->db->prepare(
            'INSERT INTO accounts (account_id, balance_cents) VALUES (:id, :balance_cents)'
        );
        $seed->execute([':id' => 'ACC-01', ':balance_cents' => 50000]); // $500.00
        $seed->execute([':id' => 'ACC-02', ':balance_cents' => 15000]); // $150.00
    }

    public function driverLabel(): string
    {
        return $this->db->driverLabel();
    }

    public function getBalanceCents(string $accountId): int
    {
        $stmt = $this->db->prepare('SELECT balance_cents FROM accounts WHERE account_id = :id');
        $stmt->execute([':id' => $accountId]);
        $row = $stmt->fetchAssoc();
        if ($row === false) {
            throw new \RuntimeException("Account not found: {$accountId}");
        }
        return (int)$row['balance_cents'];
    }

    public function transfer(
        string $from,
        string $to,
        int $amountCents,
        bool $simulateFailure = false,
        bool $bypassAppBalanceCheck = false
    ): void {
        if ($amountCents <= 0) {
            throw new \InvalidArgumentException('Transfer amount in cents must be positive.');
        }

        // BEGIN IMMEDIATE acquires SQLite's RESERVED write lock up front,
        // preventing concurrent writers from interleaving between read and update.
        $this->db->exec('BEGIN IMMEDIATE');
        try {
            $select = $this->db->prepare('SELECT balance_cents FROM accounts WHERE account_id = :id');
            $select->execute([':id' => $from]);
            $row = $select->fetchAssoc();
            if ($row === false) {
                throw new \RuntimeException("Source account not found: {$from}");
            }

            if (!$bypassAppBalanceCheck && (int)$row['balance_cents'] < $amountCents) {
                throw new \RuntimeException("Insufficient funds in {$from}");
            }

            // Prepared statement with named parameter prevents SQL injection;
            // CHECK (balance_cents >= 0) enforces solvency inside the DB engine.
            $debit = $this->db->prepare(
                'UPDATE accounts SET balance_cents = balance_cents - :amount WHERE account_id = :id'
            );
            $debit->execute([':amount' => $amountCents, ':id' => $from]);

            if ($simulateFailure) {
                throw new \RuntimeException('Simulated network crash during destination credit!');
            }

            $credit = $this->db->prepare(
                'UPDATE accounts SET balance_cents = balance_cents + :amount WHERE account_id = :id'
            );
            $credit->execute([':amount' => $amountCents, ':id' => $to]);

            $this->db->exec('COMMIT');
        } catch (\Throwable $e) {
            $this->db->exec('ROLLBACK');
            throw $e;
        }
    }
}

// Self-verifying test block
echo "==> Running Exercise 1.2: SQLite PDO Prepared Transactions & Atomic Transfers...\n";
$bank = new SqliteBankTransferService();
echo "Using database engine: {$bank->driverLabel()}\n";

// Test 1: Successful transfer of $100.00 (10,000 cents)
$bank->transfer('ACC-01', 'ACC-02', 10000);
assert($bank->getBalanceCents('ACC-01') === 40000, 'ACC-01 must be 40000 cents ($400.00)');
assert($bank->getBalanceCents('ACC-02') === 25000, 'ACC-02 must be 25000 cents ($250.00)');

// Test 2: Failure after debit triggers atomic ROLLBACK
$caughtFailure = false;
try {
    $bank->transfer('ACC-01', 'ACC-02', 5000, simulateFailure: true);
} catch (\RuntimeException $e) {
    $caughtFailure = true;
}
assert($caughtFailure === true);
assert($bank->getBalanceCents('ACC-01') === 40000, 'ACC-01 must remain 40000 cents after rollback');
assert($bank->getBalanceCents('ACC-02') === 25000, 'ACC-02 must remain 25000 cents after rollback');

// Test 3: Database-level CHECK (balance_cents >= 0) rejects overdraft even if app check bypassed
$caughtConstraint = false;
try {
    $bank->transfer('ACC-01', 'ACC-02', 999999, bypassAppBalanceCheck: true);
} catch (\PDOException $e) {
    $caughtConstraint = str_contains($e->getMessage(), 'CHECK constraint failed');
}
assert($caughtConstraint === true, 'SQLite CHECK (balance_cents >= 0) must reject overdraft!');
assert($bank->getBalanceCents('ACC-01') === 40000, 'ACC-01 must stay intact after constraint rollback');
assert($bank->getBalanceCents('ACC-02') === 25000, 'ACC-02 must stay intact after constraint rollback');

// Test 4: SQL Injection attempt via prepared parameter fails safely as unknown account
$caughtInjection = false;
try {
    $bank->transfer("ACC-01' OR '1'='1", 'ACC-02', 1000);
} catch (\RuntimeException $e) {
    $caughtInjection = str_contains($e->getMessage(), 'Source account not found');
}
assert($caughtInjection === true, 'Prepared statements must treat SQLi payload as literal string!');

echo "[PASS] Exercise 1.2 successfully verified.\n";
