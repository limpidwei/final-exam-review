#!/usr/bin/env python3
"""
Chunk manager for context window segmentation of large files.

Usage:
    python chunk_manager.py --input large_file.md --max-tokens 8000
    python chunk_manager.py --merge chunk_*.json --output merged.md
    python chunk_manager.py --estimate file.md         # Estimate token count

Splits large files at natural chapter/section boundaries while preserving
200-character overlap between chunks for continuity.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Optional

def estimate_tokens(text: str) -> int:
    """
    Rough token estimation.
    Chinese: ~1.5 tokens per character
    English: ~1.3 tokens per word
    Mixed: heuristic
    """
    chinese_chars = len(re.findall(r'[一-鿿㐀-䶿]', text))
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    other = len(text) - chinese_chars - english_words

    return int(chinese_chars * 1.5 + english_words * 1.3 + other * 0.5)

def find_chapter_boundaries(text: str) -> List[int]:
    """
    Find natural split points: H1/H2 headings, horizontal rules, or double newlines at page-like intervals.
    Returns list of character offsets.
    """
    boundaries = []

    # H1 headings: # Title
    for m in re.finditer(r'^#\s+.+$', text, re.MULTILINE):
        boundaries.append(m.start())

    # H2 headings: ## Title
    for m in re.finditer(r'^##\s+.+$', text, re.MULTILINE):
        boundaries.append(m.start())

    # Chapter markers: 第X章, Chapter X, CHAPTER X
    for m in re.finditer(r'(?:第[一二三四五六七八九十\d]+[章节]|Chapter\s+\d+|CHAPTER\s+\d+)', text):
        boundaries.append(m.start())

    # Horizontal rules: --- or *** or ===
    for m in re.finditer(r'^[-*=_]{3,}\s*$', text, re.MULTILINE):
        boundaries.append(m.start())

    # Sort and deduplicate
    boundaries = sorted(set(boundaries))

    # Filter: boundaries must be at least 500 chars apart
    filtered = []
    for b in boundaries:
        if not filtered or b - filtered[-1] >= 500:
            filtered.append(b)
    return filtered

def chunk_text(text: str, max_tokens: int = 8000, overlap: int = 200) -> List[Dict]:
    """
    Split text into chunks respecting chapter boundaries.
    Each chunk ≤ max_tokens, with overlap chars between chunks.
    """
    boundaries = find_chapter_boundaries(text)
    chunks = []
    pos = 0
    chunk_idx = 0

    # Target: 70% of max_tokens to leave room
    target_tokens = int(max_tokens * 0.7)
    target_chars = int(target_tokens / 1.5)  # rough char estimate for Chinese

    while pos < len(text):
        chunk_idx += 1

        # Find the furthest boundary within target_chars from pos
        end = min(pos + target_chars, len(text))
        chunk_end = end

        # Try to find a natural boundary near the target end
        nearby_boundaries = [b for b in boundaries if pos < b <= end]
        if nearby_boundaries:
            # Use the last boundary before the target end
            chunk_end = nearby_boundaries[-1]
        elif end < len(text):
            # No boundary found; try to break at a paragraph (double newline)
            search_region = text[pos + target_chars // 2:end]
            para_break = search_region.rfind('\n\n')
            if para_break > 0:
                chunk_end = pos + target_chars // 2 + para_break

        chunk_text_slice = text[pos:chunk_end]
        chunk_tokens = estimate_tokens(chunk_text_slice)

        chunks.append({
            "chunk_index": chunk_idx,
            "start_pos": pos,
            "end_pos": chunk_end,
            "char_count": len(chunk_text_slice),
            "token_estimate": chunk_tokens,
            "text": chunk_text_slice,
        })

        # Next position: overlap from previous chunk end
        if chunk_end >= len(text):
            break

        # Move back by overlap, but not past the previous chunk's start
        next_pos = max(chunk_end - overlap, pos + 1)
        # Also ensure we don't get stuck
        if next_pos <= pos:
            next_pos = pos + target_chars // 2
        pos = next_pos

    return chunks

def merge_chunks(chunk_dir: str, output_path: Optional[str] = None) -> str:
    """
    Merge processed chunk results back into a single document.
    Reads chunk_*.json files from chunk_dir, removes overlap regions.
    """
    chunk_files = sorted(Path(chunk_dir).glob("chunk_*.json"))
    if not chunk_files:
        raise FileNotFoundError(f"No chunk_*.json files found in {chunk_dir}")

    merged_parts = []
    for cf in chunk_files:
        with open(cf, "r", encoding="utf-8") as f:
            data = json.load(f)
        merged_parts.append(data.get("text", data.get("content", "")))

    full_text = "\n\n".join(merged_parts)

    # Remove duplicate overlap lines
    lines = full_text.split("\n")
    deduped = []
    seen = set()
    for line in lines:
        stripped = line.strip()
        if stripped and stripped in seen:
            continue
        if stripped:
            seen.add(stripped)
        deduped.append(line)

    result = "\n".join(deduped)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result)

    return result

def main():
    parser = argparse.ArgumentParser(description="Chunk manager for large files")
    subparsers = parser.add_subparsers(dest="command")

    # Chunk command
    chunk_parser = subparsers.add_parser("chunk", help="Split a file into chunks")
    chunk_parser.add_argument("--input", "-i", required=True, help="Input file")
    chunk_parser.add_argument("--max-tokens", type=int, default=8000, help="Max tokens per chunk")
    chunk_parser.add_argument("--overlap", type=int, default=200, help="Overlap characters between chunks")
    chunk_parser.add_argument("--output-dir", "-o", required=True, help="Output directory for chunks")

    # Merge command
    merge_parser = subparsers.add_parser("merge", help="Merge chunks back")
    merge_parser.add_argument("--input-dir", "-i", required=True, help="Directory with chunk_*.json files")
    merge_parser.add_argument("--output", "-o", required=True, help="Output merged file")

    # Estimate command
    est_parser = subparsers.add_parser("estimate", help="Estimate token count")
    est_parser.add_argument("--input", "-i", required=True, help="Input file")

    args = parser.parse_args()

    if args.command == "chunk":
        with open(args.input, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()

        chunks = chunk_text(text, max_tokens=args.max_tokens, overlap=args.overlap)

        os.makedirs(args.output_dir, exist_ok=True)
        for chunk in chunks:
            chunk_file = os.path.join(args.output_dir, f"chunk_{chunk['chunk_index']:04d}.json")
            with open(chunk_file, "w", encoding="utf-8") as f:
                json.dump(chunk, f, indent=2, ensure_ascii=False)

        print(f"Split into {len(chunks)} chunks → {args.output_dir}", file=sys.stderr)
        # Output summary
        summary = {
            "file": args.input,
            "total_chars": len(text),
            "total_tokens": estimate_tokens(text),
            "chunks": len(chunks),
            "max_tokens_per_chunk": args.max_tokens,
            "chunk_details": [{"index": c["chunk_index"], "chars": c["char_count"],
                                "tokens": c["token_estimate"]} for c in chunks],
        }
        print(json.dumps(summary, indent=2, ensure_ascii=False))

    elif args.command == "merge":
        result = merge_chunks(args.input_dir, args.output)
        print(f"Merged → {args.output} ({len(result)} chars)", file=sys.stderr)

    elif args.command == "estimate":
        with open(args.input, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        tokens = estimate_tokens(text)
        result = {
            "file": args.input,
            "chars": len(text),
            "estimated_tokens": tokens,
            "would_need_chunking": tokens > 8000,
            "suggested_chunks": max(1, tokens // 6000 + 1) if tokens > 8000 else 1,
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
