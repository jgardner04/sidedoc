"""Sync module for matching blocks and updating documents."""

from typing import Optional
from sidedoc.models import Block


def match_blocks(
    old_blocks: list[Block], new_blocks: list[Block]
) -> dict[str, Block]:
    """Match old blocks to new blocks using hashes and positions.

    Matching strategy:
    1. First pass: Match by content hash (unchanged blocks)
    2. Second pass: Match by type and position (edited blocks)

    Args:
        old_blocks: List of blocks from previous version (structure.json)
        new_blocks: List of blocks from edited content.md

    Returns:
        Dictionary mapping old block IDs to their corresponding new blocks.
        Unmatched old blocks indicate deletions.
        Unmatched new blocks indicate additions.
    """
    matches: dict[str, Block] = {}
    used_new_blocks: set[int] = set()

    # First pass: Match by content hash (unchanged blocks)
    for old_block in old_blocks:
        for i, new_block in enumerate(new_blocks):
            if i in used_new_blocks:
                continue
            if old_block.content_hash == new_block.content_hash:
                matches[old_block.id] = new_block
                used_new_blocks.add(i)
                break

    # Second pass: Match by type and exact position (edited blocks)
    # This handles blocks that were edited but are at the exact same position
    # We only match if the positions are identical to avoid false matches
    remaining_old = [b for b in old_blocks if b.id not in matches]
    remaining_new_indices = [
        i for i in range(len(new_blocks)) if i not in used_new_blocks
    ]

    for old_block in remaining_old:
        old_idx = old_blocks.index(old_block)

        # Only match if there's a new block at the exact same position with same type
        if old_idx in remaining_new_indices:
            new_block = new_blocks[old_idx]
            if old_block.type == new_block.type:
                matches[old_block.id] = new_block
                used_new_blocks.add(old_idx)
                remaining_new_indices.remove(old_idx)

    return matches
