# Scripts

This directory contains runtime scripts for chunking, indexing, and provider access.

## Main Entry Scripts

- `chunk_and_index.py`
  - Full rebuild indexing flow.
  - Use when chunking strategy changes or rebuilding from scratch.

- `incremental_update.py`
  - Incremental indexing flow that preserves existing vectors.
  - Use for daily note updates.

- `check_model.py`
  - Local embedding model cache validation utility.
  - Use for troubleshooting model cache issues.

## Subdirectories

- `core/`: shared core runtime modules (`chunk_schema`, `vector_indexer`)
- `chunking/`: chunk quality and splitting utilities
- `providers/`: provider abstraction and transport layers

## Verification

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

