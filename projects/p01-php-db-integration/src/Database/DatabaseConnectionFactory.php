<?php

declare(strict_types=1);

namespace App\Database;

final class DatabaseConnectionFactory
{
    /**
     * Creates a hardened production PDO connection.
     */
    public static function create(
        string $dsn,
        ?string $username = null,
        ?string $password = null,
        array $driverOptions = []
    ): ConnectionInterface {
        $defaultOptions = [
            \PDO::ATTR_ERRMODE => \PDO::ERRMODE_EXCEPTION,
            \PDO::ATTR_EMULATE_PREPARES => false,
            \PDO::ATTR_DEFAULT_FETCH_MODE => \PDO::FETCH_ASSOC,
            \PDO::ATTR_PERSISTENT => false,
        ];

        $options = $driverOptions + $defaultOptions;
        $pdo = new \PDO($dsn, $username, $password, $options);
        return new PdoConnection($pdo);
    }
}
