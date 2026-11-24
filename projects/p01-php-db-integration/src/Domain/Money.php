<?php

declare(strict_types=1);

namespace App\Domain;

/**
 * Immutable integer-cents Money value object.
 *
 * Production financial systems store monetary amounts as exact integer minor units
 * (e.g., cents: $19.99 -> 1999) rather than IEEE-754 binary floating-point numbers,
 * avoiding rounding drift such as `0.1 + 0.2 !== 0.3`.
 */
final readonly class Money
{
    public function __construct(
        public int $cents,
        public string $currency = 'USD'
    ) {
        if ($this->cents < 0) {
            throw new \InvalidArgumentException("Money amount cannot be negative: {$this->cents} cents");
        }
    }

    public static function fromFloat(float $amount, string $currency = 'USD'): self
    {
        return new self((int)round($amount * 100), $currency);
    }

    public function add(self $other): self
    {
        if ($this->currency !== $other->currency) {
            throw new \InvalidArgumentException("Currency mismatch: {$this->currency} vs {$other->currency}");
        }
        return new self($this->cents + $other->cents, $this->currency);
    }

    public function multiply(int $quantity): self
    {
        if ($quantity < 0) {
            throw new \InvalidArgumentException("Quantity cannot be negative: {$quantity}");
        }
        return new self($this->cents * $quantity, $this->currency);
    }

    public function toFloat(): float
    {
        return $this->cents / 100.0;
    }

    public function format(): string
    {
        return sprintf('%s %.2f', $this->currency, $this->cents / 100.0);
    }
}
