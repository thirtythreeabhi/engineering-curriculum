<?php

declare(strict_types=1);

spl_autoload_register(function (string $class) {
    $prefix = 'WebhookReceiver\\';
    $baseDir = dirname(__DIR__) . '/src/';

    if (str_starts_with($class, 'WebhookReceiver\\Tests\\')) {
        $testPrefix = 'WebhookReceiver\\Tests\\';
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
echo " Running Tests: p02-php-webhook-receiver                \n";
echo "========================================================\n";

$testClass = new WebhookReceiver\Tests\WebhookReceiverTest();
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
