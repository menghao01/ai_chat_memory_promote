# Lane A Agent Brief - Markdown Chunking Foundation

## Scope

- Focus tasks: `A1` first (`Markdown 结构解析器`)
- Files primarily under:
  - `scripts/chunking/`
  - `scripts/chunk_and_index.py`
  - `tests/chunking/`

## Current Problem

- Existing markdown split relies on `^##\\s+` and misses headings like `##关于孤独`.
- Chunk size constraints exist in schema constants but are not enforced in main flow.

## Goal (This Wave)

- Implement `parse_blocks(text)` to emit normalized blocks:
  - `heading`
  - `list`
  - `code`
  - `paragraph`
  - `dialogue` (heuristic)
- Ensure heading detection supports both:
  - `## 标题`
  - `##标题`

## Constraints

- Preserve existing `Chunk` compatibility (`content + metadata`).
- No vector DB schema change in this wave.
- Keep behavior deterministic (no network/model dependency in parser tests).

## Acceptance

- Add tests under `tests/chunking/test_markdown_blocks.py`.
- Must include a failing test for no-space heading before implementation.
- All chunking tests pass.

## Non-Goals

- Do not implement semantic refine in this wave.
- Do not modify provider integration code in this lane.
