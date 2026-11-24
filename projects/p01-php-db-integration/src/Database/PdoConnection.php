<?php

declare(strict_types=1);

namespace App\Database;

final class PdoPreparedStatement implements PreparedStatementInterface
{
    public function __construct(private \PDOStatement $statement) {}

    public function execute(?array $params = null): bool
    {
        return $this->statement->execute($params);
    }

    public function fetch(): array|false
    {
        return $this->statement->fetch(\PDO::FETCH_ASSOC);
    }

    public function fetchAll(): array
    {
        return $this->statement->fetchAll(\PDO::FETCH_ASSOC);
    }

    public function rowCount(): int
    {
        return $this->statement->rowCount();
    }
}

final class PdoConnection implements ConnectionInterface
{
    public function __construct(private \PDO $pdo) {}

    public function beginTransaction(?IsolationLevel $level = null): bool
    {
        if ($level !== null) {
            $this->pdo->exec("SET TRANSACTION ISOLATION LEVEL {$level->value}");
        }
        return $this->pdo->beginTransaction();
    }

    public function commit(): bool
    {
        return $this->pdo->commit();
    }

    public function rollBack(): bool
    {
        return $this->pdo->rollBack();
    }

    public function inTransaction(): bool
    {
        return $this->pdo->inTransaction();
    }

    public function prepare(string $sql): PreparedStatementInterface
    {
        $stmt = $this->pdo->prepare($sql);
        if ($stmt === false) {
            throw new \RuntimeException("Failed to prepare statement: {$sql}");
        }
        return new PdoPreparedStatement($stmt);
    }

    public function exec(string $sql): int
    {
        $res = $this->pdo->exec($sql);
        if ($res === false) {
            throw new \RuntimeException("Failed to execute SQL: {$sql}");
        }
        return $res;
    }

    public function lastInsertId(?string $name = null): string|int
    {
        return $this->pdo->lastInsertId($name);
    }

    public function getUnderlyingPdo(): \PDO
    {
        return $this->pdo;
    }
}
