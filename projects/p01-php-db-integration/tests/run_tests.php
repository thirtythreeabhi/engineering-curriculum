<?php

declare(strict_types=1);

// Register PSR-4 style autoloader for standalone execution without composer dump-autoload
spl_autoload_register(function (string $class) {
    $prefix = 'App\\';
    $baseDir = dirname(__DIR__) . '/src/';

    if (str_starts_with($class, 'App\\Tests\\')) {
        $testPrefix = 'App\\Tests\\';
        $relativeClass = substr($class, strlen($testPrefix));
        $file = dirname(__DIR__) . '/tests/' . str_replace('\\', '/', $relativeClass) . '.php';
        if (file_exists($file)) {
            require_once $file;
        }
        return;
    }

    if (str_starts_with($class, $prefix)) {
        $relativeClass = substr($class, strlen($prefix));
        $file = $baseDir . str_replace('\\', '/', $relativeClass) . '.php';
        if (file_exists($file)) {
            require_once $file;
        }
    }
});

echo "========================================================\n";
echo " Running Tests: p01-php-db-integration (PHP 8.3+ PDO)  \n";
echo "========================================================\n";

$testClass = new App\Tests\OrderPlacementServiceTest();
$methods = get_class_methods($testClass);
$passed = 0;
$failed = 0;

foreach ($methods as $method) {
    if (str_starts_with($method, 'test')) {
        echo " -> Executing {$method}... ";
        try {
            $testClass->$method();
            echo "[PASS]\n";
            $passed++;
        } catch (\Throwable $e) {
            echo "[FAIL]\n";
            echo "    Error: " . $e->getMessage() . "\n";
            echo "    Location: " . $e->getFile() . ":" . $e->getLine() . "\n";
            $failed++;
        }
    }
}

echo "--------------------------------------------------------\n";
echo "Results: {$passed} passed, {$failed} failed.\n";
echo "========================================================\n";

exit($failed > 0 ? 1 : 0);
