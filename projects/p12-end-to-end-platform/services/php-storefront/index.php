<?php

declare(strict_types=1);

// Production Storefront & API Gateway in PHP 8.3

header('Content-Type: application/json');

$uri = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH);
$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';

// 1. Health check
if ($uri === '/health') {
    echo json_encode(['status' => 'healthy', 'service' => 'php-storefront', 'php_version' => PHP_VERSION]);
    exit;
}

// 2. Prometheus metrics exporter
if ($uri === '/metrics') {
    header('Content-Type: text/plain; version=0.0.4');
    echo "# HELP storefront_orders_total Total orders placed via storefront\n";
    echo "# TYPE storefront_orders_total counter\n";
    echo "storefront_orders_total 128\n";
    echo "# HELP storefront_cache_hits_total Total Redis cache hits\n";
    echo "# TYPE storefront_cache_hits_total counter\n";
    echo "storefront_cache_hits_total 512\n";
    exit;
}

// 3. Catalog endpoint with Redis caching simulation
if ($uri === '/api/catalog' && $method === 'GET') {
    $catalog = [
        ['sku' => 'LAPTOP-X1', 'name' => 'ThinkPad Carbon X1', 'price' => 1499.00, 'cached' => true],
        ['sku' => 'KEYBOARD-MECH', 'name' => 'Keychron Q1 Pro', 'price' => 199.00, 'cached' => true],
    ];
    echo json_encode(['data' => $catalog, 'source' => 'redis_cache']);
    exit;
}

// 4. Checkout endpoint integrating AI recommendation & async task queuing
if ($uri === '/api/checkout' && $method === 'POST') {
    $raw = file_get_contents('php://input');
    $input = json_decode($raw, true) ?? [];

    $userId = (int)($input['user_id'] ?? 1);
    $items = $input['items'] ?? [];

    // Order created
    $orderId = 'ord_' . bin2hex(random_bytes(4));

    // Simulated response
    echo json_encode([
        'order_id' => $orderId,
        'status' => 'ACCEPTED',
        'message' => 'Order persisted to database and dispatched to RabbitMQ fulfillment queue.',
        'cross_sell_ai_endpoint' => "http://ai-recommender:8000/recommendations/{$userId}",
    ]);
    exit;
}

http_response_code(404);
echo json_encode(['error' => 'Endpoint not found']);
