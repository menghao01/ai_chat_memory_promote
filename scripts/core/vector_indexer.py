"""
Vector database utilities for indexing chunks.
"""

import os
from pathlib import Path
from typing import Dict, List

import chromadb
from sentence_transformers import SentenceTransformer


def get_local_model_path():
    """Get local model path from cache, avoiding network calls."""
    cache_base = Path.home() / ".cache" / "huggingface" / "hub"
    model_dir = cache_base / "models--BAAI--bge-m3" / "snapshots"
    snapshots = list(model_dir.iterdir())
    if snapshots:
        return str(snapshots[0])
    return "BAAI/bge-m3"


class VectorIndexer:
    """Handle vector database indexing operations."""

    def __init__(self, db_path: str = "./vector_db", model_name: str = "BAAI/bge-m3"):
        self.db_path = db_path
        self.model_name = model_name
        self.model = None
        self.client = None
        self.collection = None

    def initialize_db(self):
        """Initialize or recreate vector database."""
        model_path = get_local_model_path()
        print("Loading embedding model from local cache...")
        print(f"  Model path: {model_path}")
        self.model = SentenceTransformer(model_path)

        print(f"Initializing vector database at: {self.db_path}")
        self.client = chromadb.PersistentClient(path=self.db_path)

        try:
            self.client.delete_collection("notes")
            print("   Deleted existing collection")
        except Exception:
            pass

        self.collection = self.client.create_collection(
            name="notes",
            metadata={"hnsw:space": "cosine"},
        )
        print("   Created new collection")

    def index_chunks(self, chunks: List[Dict]) -> None:
        """Index chunks into vector database."""
        if not self.collection:
            raise RuntimeError("Database not initialized. Call initialize_db() first")

        print(f"Indexing {len(chunks)} chunks...")

        for i, chunk in enumerate(chunks):
            try:
                if "content" not in chunk or "metadata" not in chunk:
                    print(f"  WARNING: Skipping chunk {i}: missing content or metadata")
                    continue

                embedding = self.model.encode(chunk["content"]).tolist()
                metadata = {}
                for key, value in chunk["metadata"].items():
                    metadata[key] = str(value) if value is not None else ""

                self.collection.add(
                    ids=[f"chunk_{i}"],
                    embeddings=[embedding],
                    documents=[chunk["content"]],
                    metadatas=[metadata],
                )

                if (i + 1) % 10 == 0:
                    print(f"  Indexed {i + 1}/{len(chunks)} chunks")
            except Exception as e:
                print(f"  ERROR: Failed to index chunk {i}: {e}")

        print(f"\nSUCCESS: Successfully indexed {len(chunks)} chunks")
        print(f"   Database location: {os.path.abspath(self.db_path)}")


def index_chunks_to_db(chunks: List[Dict], db_path: str = "./vector_db") -> None:
    """Convenience function to index chunks."""
    indexer = VectorIndexer(db_path=db_path)
    indexer.initialize_db()
    indexer.index_chunks(chunks)

