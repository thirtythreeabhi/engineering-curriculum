<?php

declare(strict_types=1);

namespace App\Exceptions;

final class TransactionException extends \RuntimeException
{
    public function __construct(string $message, ?\Throwable $previous = null)
    {
        parent::__construct($message, 0, $previous);
    }
}
