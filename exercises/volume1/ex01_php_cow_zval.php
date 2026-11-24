<?php

declare(strict_types=1);

/**
 * Exercise 1.1: PHP Zend Engine Memory Semantics, Copy-on-Write (CoW),
 *               Reference Semantics (&$var / is_ref), and Cycle GC
 *
 * Problem:
 * Modern PHP manages memory via zvals and reference counting. When a variable is
 * copied by value, PHP avoids duplicating memory by incrementing refcount and
 * deferring buffer duplication until mutation (Copy-on-Write). Conversely, explicit
 * references (&$var) wrap the zval in a zend_reference (IS_REFERENCE) so mutations
 * propagate without separation, and circular object graphs require PHP's synchronous
 * cycle collector (gc_collect_cycles) because refcounts never drop to zero on unset.
 *
 * Implement a memory analyzer that:
 * 1. Measures memory before allocation, after copy, and after in-place mutation.
 * 2. Demonstrates that assignment by value does NOT double memory consumption until modified.
 * 3. Demonstrates reference semantics (&$var) and cycle collection behavior via gc_collect_cycles().
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
            'original_first' => $original[0],
            'copy_first' => $copy[0],
            'cow_effective' => ($copiedMemoryDelta < ($allocatedMemory * 0.1)),
        ];
    }

    public static function demonstrateReferenceAndCycleGc(): array
    {
        // Part A: Reference semantics (&$var -> IS_REFERENCE / zend_reference)
        $source = [10, 20, 30];
        $ref = &$source;       // Both $source and $ref point to the same zend_reference
        $cowCopy = $source;    // Assigning by value from a reference copies the underlying array via CoW

        $ref[0] = 999;         // Mutates shared target in-place without separating $source and $ref
        $sourceAfterRefMutation = $source[0];
        $cowCopyAfterRefMutation = $cowCopy[0];

        unset($ref);           // Breaks reference binding (refcount on zend_reference drops)

        // Part B: Cyclic references & synchronous cycle GC
        gc_enable();
        gc_collect_cycles();
        $rootsBefore = gc_status()['roots'];

        $nodeA = new \stdClass();
        $nodeB = new \stdClass();
        $nodeA->peer = $nodeB;
        $nodeB->peer = $nodeA;

        // Dropping external handles leaves each object with refcount=1 due to the cycle.
        // PHP places these possible roots in the GC root buffer rather than freeing immediately.
        unset($nodeA, $nodeB);
        $rootsWithCycle = gc_status()['roots'];

        // Running gc_collect_cycles() detects and frees unreachable cycles.
        $collectedZvals = gc_collect_cycles();
        $rootsAfterGc = gc_status()['roots'];

        return [
            'source_after_ref_mutation' => $sourceAfterRefMutation,
            'cow_copy_after_ref_mutation' => $cowCopyAfterRefMutation,
            'roots_before' => $rootsBefore,
            'roots_with_cycle' => $rootsWithCycle,
            'collected_zvals' => $collectedZvals,
            'roots_after_gc' => $rootsAfterGc,
        ];
    }
}

// Self-verifying test block
echo "==> Running Exercise 1.1: PHP Copy-on-Write, Reference & Cycle GC Semantics...\n";
$metrics = MemoryAnalyzer::demonstrateCopyOnWrite();

echo "Allocated buffer size: " . number_format($metrics['allocated_bytes']) . " bytes\n";
echo "Copy-by-value delta:   " . number_format($metrics['copied_delta_bytes']) . " bytes\n";
echo "Post-mutation delta:   " . number_format($metrics['mutated_delta_bytes']) . " bytes\n";

assert($metrics['cow_effective'] === true, "CoW must avoid duplicating buffer until mutation!");
assert($metrics['mutated_delta_bytes'] > 0, "Mutating copy must trigger memory separation!");
assert($metrics['original_first'] === 1 && $metrics['copy_first'] === 999999, "Original must remain untouched on CoW write!");

$refGc = MemoryAnalyzer::demonstrateReferenceAndCycleGc();
echo "Reference semantics:   source[0]={$refGc['source_after_ref_mutation']}, cowCopy[0]={$refGc['cow_copy_after_ref_mutation']}\n";
echo "Cycle GC roots:        with_cycle={$refGc['roots_with_cycle']}, collected={$refGc['collected_zvals']}, after_gc={$refGc['roots_after_gc']}\n";

assert($refGc['source_after_ref_mutation'] === 999, "&\$var mutation must propagate to original variable!");
assert($refGc['cow_copy_after_ref_mutation'] === 10, "Value copy must stay isolated from reference mutation!");
assert($refGc['roots_with_cycle'] >= 2, "Unsetting cyclic objects must buffer potential cycle roots!");
assert($refGc['collected_zvals'] >= 2, "gc_collect_cycles() must reclaim cyclic objects!");
assert($refGc['roots_after_gc'] === 0, "GC root buffer must be empty after collection!");

echo "[PASS] Exercise 1.1 successfully verified.\n";
