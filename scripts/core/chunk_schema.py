"""
Chunk data format specification.

This module defines the required format for document chunks.
All chunking strategies must produce chunks conforming to this schema.
"""

from typing import Optional, TypedDict


class ChunkMetadata(TypedDict, total=False):
    """Metadata for a document chunk."""

    filename: str
    filepath: str
    chunk_id: int
    chunk_type: str
    date: Optional[str]
    title: Optional[str]
    sub_chunk_id: Optional[int]
    tags: Optional[list[str]]


class Chunk(TypedDict):
    """Document chunk format."""

    content: str
    metadata: ChunkMetadata


def validate_chunk(chunk: dict) -> bool:
    """Validate whether a chunk conforms to the schema."""
    if not isinstance(chunk, dict):
        return False

    if "content" not in chunk or "metadata" not in chunk:
        return False

    if not isinstance(chunk["content"], str):
        return False

    metadata = chunk["metadata"]
    required_fields = ["filename", "filepath", "chunk_id", "chunk_type"]
    for field in required_fields:
        if field not in metadata:
            return False

    return True


MIN_CHUNK_SIZE = 50
MAX_CHUNK_SIZE = 2000
TARGET_CHUNK_SIZE = 500

