# -*- coding: utf-8 -*-
"""
Incremental update for vector database - preserves existing data.

This script adds new notes to the database without deleting existing ones.
"""

import hashlib
import re
from pathlib import Path
from typing import List, Dict

from scripts.core.chunk_schema import Chunk, validate_chunk


def get_local_model_path():
    """Get local model path from cache, avoiding network calls."""
    cache_base = Path.home() / ".cache" / "huggingface" / "hub"
    model_dir = cache_base / "models--BAAI--bge-m3" / "snapshots"
    if not model_dir.exists():
        return "BAAI/bge-m3"
    # Get the first snapshot
    snapshots = list(model_dir.iterdir())
    if snapshots:
        return str(snapshots[0])
    return "BAAI/bge-m3"  # Fallback to default


def _normalize_content_for_id(content: str) -> str:
    """Normalize content for stable chunk hashing across whitespace-only edits."""
    text = content if isinstance(content, str) else str(content or "")
    return re.sub(r"\s+", " ", text).strip()


def get_chunk_id(chunk: Dict) -> str:
    """
    Generate a unique, deterministic ID for each chunk.
    Based on filename + chunk_id + content hash to avoid duplicates.
    """
    filename = chunk['metadata'].get('filename', '')
    chunk_id = chunk['metadata'].get('chunk_id', 0)
    content = _normalize_content_for_id(chunk.get('content', ''))
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()

    # Create unique ID
    unique_str = f"{filename}_{chunk_id}_{len(content)}_{digest}"
    return unique_str


def get_or_create_collection(db_path: str, model_name: str):
    """
    Get existing collection or create new one (without deleting).
    """
    import chromadb

    client = chromadb.PersistentClient(path=db_path)

    # Try to get existing collection
    try:
        collection = client.get_collection("notes")
        print(f"Found existing collection with {collection.count()} items")
        return client, collection
    except:
        # Create new collection if doesn't exist
        print("Creating new collection...")
        collection = client.create_collection(
            name="notes",
            metadata={"hnsw:space": "cosine"}
        )
        return client, collection


def get_existing_ids(collection) -> set:
    """Get all existing chunk IDs from the collection."""
    try:
        # Get all data
        results = collection.get(include=['metadatas'])
        return set(results['ids'])
    except:
        return set()


def index_chunks_incremental(chunks: List[Dict], db_path: str = "./vector_db", model_name: str = "BAAI/bge-m3") -> None:
    """
    Index chunks incrementally - only add new chunks, don't delete existing ones.
    """
    from sentence_transformers import SentenceTransformer

    # Use local model path to avoid network calls
    model_path = get_local_model_path()
    print(f"Loading embedding model from local cache...")
    print(f"  Model path: {model_path}")
    model = SentenceTransformer(model_path)

    print(f"Connecting to database at: {db_path}")
    client, collection = get_or_create_collection(db_path, model_name)

    # Get existing IDs to avoid duplicates
    existing_ids = get_existing_ids(collection)
    print(f"Database currently has {len(existing_ids)} chunks")

    # Prepare new chunks
    new_chunks = []
    new_ids = []

    for chunk in chunks:
        if not validate_chunk(chunk):
            continue

        chunk_id = get_chunk_id(chunk)

        # Skip if already exists
        if chunk_id in existing_ids:
            continue

        new_chunks.append(chunk)
        new_ids.append(chunk_id)

    if not new_chunks:
        print("No new chunks to add (all already exist in database)")
        return

    print(f"Adding {len(new_chunks)} new chunks...")

    # Generate embeddings and add
    for i, (chunk, chunk_id) in enumerate(zip(new_chunks, new_ids)):
        try:
            # Generate embedding
            embedding = model.encode(chunk['content']).tolist()

            # Prepare metadata
            metadata = {}
            for key, value in chunk['metadata'].items():
                metadata[key] = str(value) if value is not None else ""

            # Add to collection
            collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                documents=[chunk['content']],
                metadatas=[metadata]
            )

            if (i + 1) % 10 == 0:
                print(f"  Added {i + 1}/{len(new_chunks)} chunks")

        except Exception as e:
            print(f"  ERROR: Failed to add chunk {chunk_id}: {e}")

    total_count = collection.count()
    print(f"\nSUCCESS: Database now has {total_count} chunks (added {len(new_chunks)} new)")


# Import chunking logic from chunk_and_index.py
def chunk_note_file(filepath: str) -> List[Dict]:
    """Import chunking logic."""
    # Import here to avoid circular dependency
    import importlib
    chunk_module = importlib.import_module("scripts.chunk_and_index")
    return chunk_module.chunk_note_file(filepath)


def main():
    """Incrementally update the database with new notes."""
    print("=== Incremental Vector Database Update ===\n")

    # Process all note files
    notes_dir = Path("./notes")
    all_chunks = []

    note_files = list(notes_dir.glob("**/*.md"))
    print(f"Found {len(note_files)} note files\n")

    for note_file in note_files:
        if not note_file.is_file():
            continue

        print(f"Processing: {note_file.name}")
        try:
            chunks = chunk_note_file(str(note_file))
            valid_chunks = [c for c in chunks if validate_chunk(c)]
            print(f"  Generated {len(valid_chunks)} chunks")
            all_chunks.extend(valid_chunks)
        except Exception as e:
            print(f"  ERROR: {e}")

    print(f"\nTotal chunks to process: {len(all_chunks)}")

    # Incrementally index (preserve existing data)
    index_chunks_incremental(all_chunks)

    print("\nDone!")


if __name__ == "__main__":
    main()
