# Provider Runtime Hardening (B4.2) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make third-party provider access production-ready with clear config, deterministic fallback, and transport/error normalization while keeping `local_default` as safe default.

**Architecture:** Keep existing adapter registry and contracts, add a lightweight transport normalization layer, strengthen settings validation, and harden fallback behavior in `chat_entry`. Use mock transport for deterministic tests and keep external network calls optional.

**Tech Stack:** Python 3, `unittest`, existing `scripts/providers/*`, YAML settings.

---

## Serial/Parallel Execution Strategy

- Must be serial:
  - Task 1 (reference baseline) -> Task 2 (settings contract) -> Task 4 (fallback behavior)
  - Final full regression and handoff docs update
- Can run in parallel (agent-friendly):
  - Task 3A native transport mapping (OpenAI/Anthropic/Gemini)
  - Task 3B OpenAI-compatible mapping and alias behavior
  - Task 5 docs/examples updates after Task 2 contract is stable

### Task 1: Reference Alignment Snapshot (Serial)

**Files:**
- Create: `D:\ai_memory_chat\docs\plans\2026-03-01-provider-api-reference.md`

**Step 1: Write minimal acceptance checklist**
- Define required fields to verify:
  - request fields mapping
  - auth/header location
  - base_url handling
  - error class mapping

**Step 2: Create reference snapshot doc**
- Record canonical mapping target for:
  - OpenAI Chat Completions-compatible
  - Anthropic Messages
  - Gemini GenerateContent

**Step 3: Verification**
Run: `rg -n "OpenAI|Anthropic|Gemini|fallback|base_url|api key" docs/plans/2026-03-01-provider-api-reference.md`
Expected: all key sections present.

### Task 2: Settings Contract Hardening (Serial)

**Files:**
- Modify: `D:\ai_memory_chat\scripts\providers\settings.py`
- Create: `D:\ai_memory_chat\tests\providers\test_settings_contract.py`

**Step 1: Write failing tests**
- invalid timeout fallback to default
- provider alias normalization
- empty provider fallback to `local_default`

**Step 2: Run tests to verify RED**
Run: `python -m unittest tests/providers/test_settings_contract.py -v`
Expected: FAIL.

**Step 3: Minimal implementation**
- Add stricter provider normalization and timeout guardrails.
- Keep backward compatibility with existing env names.

**Step 4: Run tests to verify GREEN**
Run: `python -m unittest tests/providers/test_settings_contract.py -v`
Expected: PASS.

### Task 3A: Native Provider Transport Normalization (Parallel Lane A)

**Files:**
- Create: `D:\ai_memory_chat\scripts\providers\transport.py`
- Create: `D:\ai_memory_chat\tests\providers\test_transport_native.py`
- Modify: `D:\ai_memory_chat\scripts\providers\openai_adapter.py`
- Modify: `D:\ai_memory_chat\scripts\providers\anthropic_adapter.py`
- Modify: `D:\ai_memory_chat\scripts\providers\gemini_adapter.py`

**Step 1: Write failing tests**
- each adapter forwards normalized payload and retains response contract.

**Step 2: Verify RED**
Run: `python -m unittest tests/providers/test_transport_native.py -v`
Expected: FAIL.

**Step 3: Minimal implementation**
- Add shared helpers to normalize transport errors and payload shape.

**Step 4: Verify GREEN**
Run: `python -m unittest tests/providers/test_transport_native.py -v`
Expected: PASS.

### Task 3B: OpenAI-Compatible Transport/Alias Hardening (Parallel Lane B)

**Files:**
- Modify: `D:\ai_memory_chat\scripts\providers\openai_compatible_adapter.py`
- Create: `D:\ai_memory_chat\tests\providers\test_transport_compatible.py`

**Step 1: Write failing tests**
- base_url precedence (request > provider default)
- alias routes preserve provider contract

**Step 2: Verify RED**
Run: `python -m unittest tests/providers/test_transport_compatible.py -v`
Expected: FAIL.

**Step 3: Minimal implementation + verify GREEN**
Run: `python -m unittest tests/providers/test_transport_compatible.py -v`
Expected: PASS.

### Task 4: Fallback Policy Stratification (Serial)

**Files:**
- Modify: `D:\ai_memory_chat\scripts\chat_entry.py`
- Modify: `D:\ai_memory_chat\tests\providers\test_fallback.py`

**Step 1: Write failing tests**
- retryable error falls back
- non-retryable policy error does not fallback
- unsupported provider falls back only if configured and allowed

**Step 2: Verify RED**
Run: `python -m unittest tests/providers/test_fallback.py -v`
Expected: FAIL.

**Step 3: Minimal implementation + verify GREEN**
Run: `python -m unittest tests/providers/test_fallback.py -v`
Expected: PASS.

### Task 5: Config/Usage Docs & Examples (Parallel after Task 2)

**Files:**
- Modify: `D:\ai_memory_chat\config\provider.example.yaml`
- Create: `D:\ai_memory_chat\docs\plans\provider-config-usage.md`

**Step 1: Add minimal examples**
- local default only
- openai primary + local fallback
- openai_compatible with custom `base_url`

**Step 2: Verification**
Run: `rg -n "local_default|fallback|openai_compatible|base_url" config/provider.example.yaml docs/plans/provider-config-usage.md`
Expected: all snippets present.

### Task 6: Full Verification + Handoff Update (Serial Final)

**Files:**
- Modify: `D:\ai_memory_chat\plan.md`
- Modify: `D:\ai_memory_chat\docs\plans\2026-03-01-context-compression-handoff.md`

**Step 1: Run provider regression**
Run: `python -m unittest discover -s tests/providers -p "test_*.py" -v`
Expected: PASS.

**Step 2: Run full regression**
Run: `python -m unittest discover -s tests -p "test_*.py" -v`
Expected: PASS.

**Step 3: Update progress and workflow stage**
- Record Wave 5-2 results, risks, and next checkpoint.
