# AI Chat Memory Promote

Agent-friendly note chunking and retrieval project focused on markdown-based notes and provider extensibility.

## Repository Layout

- `notes/`: source notes (chat memo, topic notes, markdown)
- `scripts/`: chunking, indexing, provider runtime scripts
- `scripts/core/`: shared runtime modules (chunk schema, vector indexer)
- `tests/`: unit tests for chunking and provider contracts
- `docs/`: plans, handoff notes, and current status snapshots

## Quick Start

Run baseline tests:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

Run key chunking tests:

```bash
python -m unittest tests/chunking/test_chunk_note_file_paths.py -v
python -m unittest tests/chunking/test_incremental_update_core.py -v
```

## Notes

- `scripts/chunk_and_index.py` rebuilds the vector index.
- `scripts/incremental_update.py` performs incremental indexing.
- Core runtime no longer depends on external `.claude` path injection.

