<?php

declare(strict_types=1);

namespace WebhookReceiver;

final readonly class SignatureVerifier
{
    public function __construct(
        private string $secretKey,
        private int $toleranceSeconds = 300 // 5-minute replay tolerance window
    ) {
        if (empty($this->secretKey)) {
            throw new \InvalidArgumentException("Webhook secret key cannot be empty.");
        }
    }

    /**
     * Timing-safe verification of HMAC-SHA256 signature and replay defense.
     *
     * @param string $rawPayload Raw HTTP request body
     * @param string $signatureHeader Header value (e.g., 'sha256=abcdef...')
     * @param int $timestamp Unix timestamp of webhook dispatch
     * @return bool True if valid, false otherwise
     */
    public function verify(string $rawPayload, string $signatureHeader, int $timestamp): bool
    {
        // 1. Replay defense check
        $now = time();
        if (abs($now - $timestamp) > $this->toleranceSeconds) {
            return false;
        }

        // 2. Normalize signature header (support 'sha256=...' prefix or raw hex)
        $providedHex = str_starts_with($signatureHeader, 'sha256=')
            ? substr($signatureHeader, 7)
            : $signatureHeader;

        // 3. Compute expected HMAC: sha256(timestamp . '.' . rawPayload, secret)
        $signedData = $timestamp . '.' . $rawPayload;
        $expectedHex = hash_hmac('sha256', $signedData, $this->secretKey);

        // 4. Timing-attack-resistant constant-time comparison
        return hash_equals($expectedHex, $providedHex);
    }

    /**
     * Helper to compute signature header for test generation or client sending.
     */
    public function computeSignature(string $rawPayload, int $timestamp): string
    {
        $signedData = $timestamp . '.' . $rawPayload;
        return 'sha256=' . hash_hmac('sha256', $signedData, $this->secretKey);
    }
}
