<?php

declare(strict_types=1);

namespace App\Database;

interface ConnectionInterface
{
    public function beginTransaction(?IsolationLevel $level = null): bool;

    public function commit(): bool;

    public function rollBack(): bool;

    public function inTransaction(): bool;

    public function prepare(string $sql): PreparedStatementInterface;

    public function exec(string $sql): int;

    public function lastInsertId(?string $name = null): string|int;
}
