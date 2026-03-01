# Hybrid Flexible Chunking & Provider Adapter Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a flexible markdown-first chunking pipeline and optional third-party conversation provider adapters without breaking the current local-default workflow.

**Architecture:** Keep existing scripts as entrypoints, add a contract layer (`ConversationRequest/Response`, `ChunkRequest/ChunkResult`), then implement markdown structural chunking + size normalization + quality gate on the indexing side and provider adapters on the chat side. Use compatibility shims so existing `Chunk` schema still works.

**Tech Stack:** Python 3, pytest, ChromaDB, sentence-transformers, optional provider SDKs/HTTP clients, existing scripts under `scripts/` and `.claude/skills/ai-partner-chat/scripts/`.

---

## Preconditions

- Use `@test-driven-development` for each behavior change.
- Use `@systematic-debugging` for any failing/unstable test.
- Use `@verification-before-completion` before claiming done.

### Task 1: Baseline Metrics Harness

**Files:**
- Create: `D:\ai_memory_chat\scripts\evaluate_chunk_quality.py`
- Create: `D:\ai_memory_chat\tests\chunking\test_evaluate_chunk_quality.py`
- Output artifact: `D:\ai_memory_chat\docs\plans\baseline-2026-03-01.json`

**Step 1: Write the failing test**

```python
def test_quality_report_contains_required_fields(tmp_path):
    from scripts.evaluate_chunk_quality import summarize_chunks
    report = summarize_chunks([{"content": "a" * 200, "metadata": {"chunk_id": 0}}], 120, 1400)
    assert "total_chunks" in report
    assert "small_chunks" in report
    assert "large_chunks" in report
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/chunking/test_evaluate_chunk_quality.py -v`  
Expected: FAIL with import or missing function error.

**Step 3: Write minimal implementation**

- Implement `summarize_chunks()` and `main()` in `scripts/evaluate_chunk_quality.py`.
- Ensure output includes `total_chunks/small_chunks/large_chunks/avg_chars/dup_ratio_proxy`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/chunking/test_evaluate_chunk_quality.py -v`  
Expected: PASS.

**Step 5: Commit**

```bash
git add scripts/evaluate_chunk_quality.py tests/chunking/test_evaluate_chunk_quality.py
git commit -m "test: add chunk quality baseline harness"
```

### Task 2: Markdown Block Parser (A1)

**Files:**
- Create: `D:\ai_memory_chat\scripts\chunking\markdown_blocks.py`
- Create: `D:\ai_memory_chat\tests\chunking\test_markdown_blocks.py`
- Modify: `D:\ai_memory_chat\scripts\chunk_and_index.py`

**Step 1: Write the failing test**

```python
def test_detect_heading_without_space():
    from scripts.chunking.markdown_blocks import parse_blocks
    blocks = parse_blocks("##关于孤独\n内容")
    assert blocks[0]["type"] == "heading"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/chunking/test_markdown_blocks.py::test_detect_heading_without_space -v`  
Expected: FAIL.

**Step 3: Write minimal implementation**

- Add `parse_blocks(text)` that emits block records: `heading/list/code/paragraph/dialogue`.
- Support both `## 标题` and `##标题`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/chunking/test_markdown_blocks.py -v`  
Expected: PASS.

**Step 5: Commit**

```bash
git add scripts/chunking/markdown_blocks.py tests/chunking/test_markdown_blocks.py scripts/chunk_and_index.py
git commit -m "feat: add markdown block parser with no-space heading support"
```

### Task 3: Structural Split + Size Normalize (A2/A3)

**Files:**
- Create: `D:\ai_memory_chat\scripts\chunking\splitters.py`
- Create: `D:\ai_memory_chat\tests\chunking\test_splitters.py`
- Modify: `D:\ai_memory_chat\scripts\chunk_and_index.py`
- Modify: `D:\ai_memory_chat\.claude\skills\ai-partner-chat\scripts\chunk_schema.py`

**Step 1: Write the failing test**

```python
def test_size_window_enforced():
    from scripts.chunking.splitters import normalize_size
    chunks = normalize_size(["x" * 20, "y" * 2500], min_chars=120, target_chars=500, max_chars=1400)
    assert all(80 <= len(c) <= 1500 for c in chunks)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/chunking/test_splitters.py::test_size_window_enforced -v`  
Expected: FAIL.

**Step 3: Write minimal implementation**

- Implement `structural_split(blocks)` and `normalize_size(chunks, min_chars, target_chars, max_chars)`.
- Keep `Chunk` output compatible with existing `validate_chunk()`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/chunking/test_splitters.py -v`  
Expected: PASS.

**Step 5: Commit**

```bash
git add scripts/chunking/splitters.py tests/chunking/test_splitters.py scripts/chunk_and_index.py .claude/skills/ai-partner-chat/scripts/chunk_schema.py
git commit -m "feat: add structural split and size normalization"
```

### Task 4: Semantic Refine Toggle (A4)

**Files:**
- Create: `D:\ai_memory_chat\scripts\chunking\semantic_refine.py`
- Create: `D:\ai_memory_chat\tests\chunking\test_semantic_refine.py`
- Modify: `D:\ai_memory_chat\scripts\chunk_and_index.py`

**Step 1: Write the failing test**

```python
def test_semantic_refine_only_applies_to_oversized_chunks():
    from scripts.chunking.semantic_refine import refine_chunks
    result = refine_chunks(["a" * 200, "b" * 2200], max_chars=1400, enabled=True)
    assert len(result) >= 2
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/chunking/test_semantic_refine.py -v`  
Expected: FAIL.

**Step 3: Write minimal implementation**

- Add `refine_chunks(..., enabled=True, only_if_over_max=True)` with deterministic splitting fallback.
- Keep this step optional via config flag.

**Step 4: Run test to verify it passes**

Run: `pytest tests/chunking/test_semantic_refine.py -v`  
Expected: PASS.

**Step 5: Commit**

```bash
git add scripts/chunking/semantic_refine.py tests/chunking/test_semantic_refine.py scripts/chunk_and_index.py
git commit -m "feat: add optional semantic refine for oversized chunks"
```

### Task 5: Quality Gate + Incremental ID Safety (A5 + hardening)

**Files:**
- Create: `D:\ai_memory_chat\scripts\chunking\quality_gate.py`
- Create: `D:\ai_memory_chat\tests\chunking\test_quality_gate.py`
- Modify: `D:\ai_memory_chat\scripts\incremental_update.py`

**Step 1: Write the failing test**

```python
def test_chunk_id_changes_when_late_content_changes():
    from scripts.incremental_update import get_chunk_id
    c1 = {"content": "A" * 150 + "x", "metadata": {"filename": "a.md", "chunk_id": 1}}
    c2 = {"content": "A" * 150 + "y", "metadata": {"filename": "a.md", "chunk_id": 1}}
    assert get_chunk_id(c1) != get_chunk_id(c2)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/chunking/test_quality_gate.py::test_chunk_id_changes_when_late_content_changes -v`  
Expected: FAIL (current 100-char hash strategy).

**Step 3: Write minimal implementation**

- Update `get_chunk_id()` to hash full normalized content (or stable longer window + length).
- Add `quality_gate.evaluate(report, thresholds)` and integration hook before index write.

**Step 4: Run test to verify it passes**

Run: `pytest tests/chunking/test_quality_gate.py -v`  
Expected: PASS.

**Step 5: Commit**

```bash
git add scripts/chunking/quality_gate.py scripts/incremental_update.py tests/chunking/test_quality_gate.py
git commit -m "fix: improve chunk id stability and add quality gate"
```

### Task 6: Conversation Contract & Provider Interface (B1)

**Files:**
- Create: `D:\ai_memory_chat\scripts\providers\contracts.py`
- Create: `D:\ai_memory_chat\scripts\providers\base.py`
- Create: `D:\ai_memory_chat\tests\providers\test_contracts.py`

**Step 1: Write the failing test**

```python
def test_conversation_response_has_required_fields():
    from scripts.providers.contracts import ConversationResponse
    data = ConversationResponse(provider="local_default", model="x", output_text="ok", latency_ms=10)
    assert data.provider == "local_default"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/providers/test_contracts.py -v`  
Expected: FAIL (module missing).

**Step 3: Write minimal implementation**

- Define dataclasses/pydantic-like typed models for:
  - `ConversationRequest/Response`
  - `ProviderError`
  - `ChunkRequest/ChunkResult`
- Define provider protocol/base class with `chat(request) -> response`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/providers/test_contracts.py -v`  
Expected: PASS.

**Step 5: Commit**

```bash
git add scripts/providers/contracts.py scripts/providers/base.py tests/providers/test_contracts.py
git commit -m "feat: add unified contracts and provider interface"
```

### Task 7: Native Providers + OpenAI-Compatible Adapter (B2/B3)

**Files:**
- Create: `D:\ai_memory_chat\scripts\providers\openai_adapter.py`
- Create: `D:\ai_memory_chat\scripts\providers\anthropic_adapter.py`
- Create: `D:\ai_memory_chat\scripts\providers\gemini_adapter.py`
- Create: `D:\ai_memory_chat\scripts\providers\openai_compatible_adapter.py`
- Create: `D:\ai_memory_chat\scripts\providers\registry.py`
- Create: `D:\ai_memory_chat\tests\providers\test_adapters_smoke.py`

**Step 1: Write the failing test**

```python
def test_registry_returns_adapter_for_provider():
    from scripts.providers.registry import get_provider
    p = get_provider("openai_compatible")
    assert p is not None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/providers/test_adapters_smoke.py -v`  
Expected: FAIL.

**Step 3: Write minimal implementation**

- Implement registry + adapter stubs with shared contract mapping.
- Add retry/timeout normalization in base layer.
- Keep external calls mockable in tests.

**Step 4: Run test to verify it passes**

Run: `pytest tests/providers/test_adapters_smoke.py -v`  
Expected: PASS (mock mode).

**Step 5: Commit**

```bash
git add scripts/providers/*.py tests/providers/test_adapters_smoke.py
git commit -m "feat: add provider adapters and registry"
```

### Task 8: Config, Fallback, and Integration Entry Point (B4)

**Files:**
- Create: `D:\ai_memory_chat\config\provider.example.yaml`
- Create: `D:\ai_memory_chat\scripts\providers\settings.py`
- Create: `D:\ai_memory_chat\tests\providers\test_fallback.py`
- Modify: `D:\ai_memory_chat\scripts\chunk_and_index.py` (if chunk pipeline config reused)
- Create: `D:\ai_memory_chat\scripts\chat_entry.py`

**Step 1: Write the failing test**

```python
def test_fallback_to_local_default_on_provider_failure():
    from scripts.providers.settings import resolve_provider_chain
    chain = resolve_provider_chain(primary="openai", fallback="local_default")
    assert chain == ["openai", "local_default"]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/providers/test_fallback.py -v`  
Expected: FAIL.

**Step 3: Write minimal implementation**

- Add settings loader (env + yaml).
- Default behavior: `provider=local_default`.
- On retryable third-party failure, fallback to local default with explicit error trace.

**Step 4: Run test to verify it passes**

Run: `pytest tests/providers/test_fallback.py -v`  
Expected: PASS.

**Step 5: Commit**

```bash
git add config/provider.example.yaml scripts/providers/settings.py scripts/chat_entry.py tests/providers/test_fallback.py
git commit -m "feat: add provider config and fallback behavior"
```

### Task 9: End-to-End Verification and Docs Sync

**Files:**
- Modify: `D:\ai_memory_chat\plan.md`
- Modify: `D:\ai_memory_chat\docs\plans\2026-03-01-hybrid-flex-chunking-provider-plan.md`
- Create: `D:\ai_memory_chat\docs\plans\verification-2026-03-01.md`

**Step 1: Run chunking verification**

Run: `python scripts/evaluate_chunk_quality.py --notes-dir notes --out docs/plans/verification-2026-03-01.md`  
Expected: report generated with small/large chunk ratios and gate status.

**Step 2: Run provider smoke verification**

Run: `pytest tests/providers -v`  
Expected: PASS in mock mode.

**Step 3: Run chunking tests**

Run: `pytest tests/chunking -v`  
Expected: PASS.

**Step 4: Document results**

- Update `plan.md` with pass/fail and deltas versus baseline.
- Record any unresolved risks (SDK auth, external rate limit, embedding drift).

**Step 5: Commit**

```bash
git add plan.md docs/plans/2026-03-01-hybrid-flex-chunking-provider-plan.md docs/plans/verification-2026-03-01.md
git commit -m "docs: record verification results for hybrid rollout"
```

## Notes for Subagent Dispatch

- Parallel lane 1: Task 2-5 (chunking pipeline).
- Parallel lane 2: Task 6-8 (provider abstraction and adapters).
- Serial checkpoints:
  - After Task 1 (baseline ready)
  - After Task 5 and Task 8 (integration checkpoint)
  - After Task 9 (final verification)
