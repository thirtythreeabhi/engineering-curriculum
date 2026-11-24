<?php

declare(strict_types=1);

namespace App\Database;

interface PreparedStatementInterface
{
    /**
     * @param array<string|int, mixed>|null $params
     */
    public function execute(?array $params = null): bool;

    /**
     * @return array<string, mixed>|false
     */
    public function fetch(): array|false;

    /**
     * @return array<int, array<string, mixed>>
     */
    public function fetchAll(): array;

    public function rowCount(): int;
}
