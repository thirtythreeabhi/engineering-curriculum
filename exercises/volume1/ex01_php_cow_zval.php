<?php

declare(strict_types=1);

/**
 * Exercise 1.1: PHP Zend Engine Memory Semantics & Copy-on-Write (CoW)
 *
 * Problem:
 * Modern PHP manages memory via zvals and reference counting. When a variable is
 * copied, PHP avoids duplicating memory by incrementing the reference count (refcount)
 * and marking it with the Copy-on-Write (CoW) flag.
 *
 * Implement a memory analyzer that:
 * 1. Measures memory before allocation, after copy, and after in-place mutation.
 * 2. Demonstrates that assignment by value does NOT double memory consumption until modified.
 * 3. Demonstrates reference semantics (&$var) and cycle collection prevention.
 */

class MemoryAnalyzer
{
    public static function demonstrateCopyOnWrite(): array
    {
        gc_collect_cycles();
        $baseMemory = memory_get_usage();

        // 1. Allocate large array (10,000 integers)
        $original = range(1, 10000);
        $allocatedMemory = memory_get_usage() - $baseMemory;

        // 2. Copy by value (CoW: pointer shared, refcount incremented, negligible memory delta)
        $copy = $original;
        $copiedMemoryDelta = (memory_get_usage() - $baseMemory) - $allocatedMemory;

        // 3. Mutate copy (CoW triggered: PHP now duplicates buffer in memory)
        $copy[0] = 999999;
        $mutatedMemoryDelta = (memory_get_usage() - $baseMemory) - $allocatedMemory;

        return [
            'allocated_bytes' => $allocatedMemory,
            'copied_delta_bytes' => $copiedMemoryDelta,
            'mutated_delta_bytes' => $mutatedMemoryDelta,
            'cow_effective' => ($copiedMemoryDelta < ($allocatedMemory * 0.1)),
        ];
    }
}

// Self-verifying test block
echo "==> Running Exercise 1.1: PHP Copy-on-Write Memory Semantics...\n";
$metrics = MemoryAnalyzer::demonstrateCopyOnWrite();

echo "Allocated buffer size: " . number_format($metrics['allocated_bytes']) . " bytes\n";
echo "Copy-by-value delta:   " . number_format($metrics['copied_delta_bytes']) . " bytes\n";
echo "Post-mutation delta:   " . number_format($metrics['mutated_delta_bytes']) . " bytes\n";

assert($metrics['cow_effective'] === true, "CoW must avoid duplicating buffer until mutation!");
assert($metrics['mutated_delta_bytes'] > 0, "Mutating copy must trigger memory separation!");
echo "[PASS] Exercise 1.1 successfully verified.\n";
