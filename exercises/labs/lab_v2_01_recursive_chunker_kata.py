"""
Lab V2-01 (Volume 2 Ch 2 - Production RAG):
Recursive Character Chunker Debugging & Overlap Kata

Instructions:
This recursive text splitter has three classic chunking bugs:
1. It computes `new_separators = separators[i + 1:]` when a segment exceeds `chunk_size`,
   but then calls `self._split_text(piece, separators)` instead of passing `new_separators`.
2. When `new_separators` is empty (no finer separator exists), it truncates `piece[:chunk_size]`
   and silently DROPS the rest of the text instead of slicing all `chunk_size` windows!
3. `_merge_splits` ignores `self.chunk_overlap`, producing zero context overlap between
   adjacent chunks.

Your task:
1. Fix the recursive call to pass `new_separators`.
2. Replace `piece[: self.chunk_size]` with a loop slicing `piece` into full `chunk_size`
   windows (with `chunk_overlap` stride or non-empty slices) so zero characters are lost.
3. Implement `chunk_overlap` retention in `_merge_splits` so consecutive chunks share up to
   `chunk_overlap` characters of trailing context.

Run this file directly to check your fix:
    python3 exercises/labs/lab_v2_01_recursive_chunker_kata.py
"""

from typing import List


class RecursiveTextSplitter:
    def __init__(
        self,
        chunk_size: int = 45,
        chunk_overlap: int = 12,
        separators: List[str] | None = None,
    ):
        assert chunk_overlap < chunk_size, "chunk_overlap must be smaller than chunk_size"
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators if separators is not None else ["\n\n", "\n", ". ", " ", ""]

    def split_text(self, text: str) -> List[str]:
        return self._split_text(text.strip(), self.separators)

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        if len(text) <= self.chunk_size:
            return [text] if text else []

        separator = separators[-1]
        new_separators: List[str] = []
        for i, sep in enumerate(separators):
            if sep == "" or sep in text:
                separator = sep
                new_separators = separators[i + 1 :]
                break

        splits = list(text) if separator == "" else text.split(separator)

        good_splits: List[str] = []
        final_chunks: List[str] = []
        joiner = "" if separator == "" else separator

        for piece in splits:
            if len(piece) <= self.chunk_size:
                good_splits.append(piece)
            else:
                if good_splits:
                    final_chunks.extend(self._merge_splits(good_splits, joiner))
                    good_splits = []
                if not new_separators:
                    # BUG 2: Silently drops characters beyond `chunk_size`!
                    # TODO: Slice `piece` into non-overlapping/overlapping windows of `chunk_size`.
                    final_chunks.append(piece[: self.chunk_size])
                else:
                    # BUG 1: Passes `separators` instead of `new_separators`!
                    # TODO: Pass `new_separators` as the second argument.
                    final_chunks.extend(self._split_text(piece, separators))

        if good_splits:
            final_chunks.extend(self._merge_splits(good_splits, joiner))
        return final_chunks

    def _merge_splits(self, splits: List[str], joiner: str) -> List[str]:
        chunks: List[str] = []
        current: List[str] = []
        current_len = 0

        for piece in splits:
            piece_len = len(piece)
            extra = len(joiner) if current else 0
            if current and current_len + extra + piece_len > self.chunk_size:
                chunks.append(joiner.join(current))
                # BUG 3: Discards `current` completely instead of retaining `chunk_overlap`!
                # TODO: Pop from the front of `current` until remaining length <= self.chunk_overlap
                #       (and adding `piece` fits or `current` becomes empty).
                current = []
                current_len = 0
            current.append(piece)
            current_len += (len(joiner) if len(current) > 1 else 0) + piece_len

        if current:
            chunks.append(joiner.join(current))
        return chunks


if __name__ == "__main__":
    print("==> Running Lab V2-01: Recursive Chunker Kata...")

    # Test 1: Coarse-to-fine splitting + overlap
    splitter = RecursiveTextSplitter(chunk_size=45, chunk_overlap=15)
    doc = (
        "PostgreSQL MVCC uses row versions.\n\n"
        "Each transaction sees a consistent snapshot without blocking readers or writers "
        "during normal SELECT queries."
    )
    chunks = splitter.split_text(doc)
    assert len(chunks) >= 3, f"[FAIL] Expected >= 3 chunks, got {len(chunks)}"
    assert all(len(c) <= 45 for c in chunks), f"[FAIL] Chunk exceeded chunk_size=45: {chunks}"

    para_chunks = [c for c in chunks if "snapshot" in c or "consistent" in c or "readers" in c]
    assert any(
        len(set(a.split()) & set(b.split())) >= 1
        for a, b in zip(para_chunks, para_chunks[1:])
    ), "[FAIL] Adjacent chunks should share overlapping context words!"

    # Test 2: No data loss when no finer separator exists
    no_char_fallback = RecursiveTextSplitter(chunk_size=10, chunk_overlap=0, separators=[" "])
    long_token = "abcdefghij1234567890"
    sliced = no_char_fallback.split_text(long_token)
    assert "".join(sliced) == long_token, f"[FAIL] Lost characters when slicing oversized token: {sliced}"

    print("[PASS] Lab V2-01 completed!")
