# Agent-Friendly Codebase Hardening Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 提升代码库的 Agent 友好度，降低上下文压缩后误判和错误传播风险，并建立可持续验证闭环。  

**Architecture:** 以“自包含依赖 + 合约测试 + 文档单一事实源 + CI 强制验证”为主线，先修复高风险耦合点（`.claude` 外部路径依赖），再补齐测试与文档，再统一工程规范。此计划保持现有功能行为不变，优先做结构性硬化。  

**Tech Stack:** Python 3.13, unittest, GitHub Actions, ChromaDB, sentence-transformers, YAML config

---

## Context Snapshot (Compression Recovery)

- 日期：2026-03-02
- 当前工作流阶段：`Wave 5-2` 已收口，进入下一阶段（provider 实网/SDK 适配前的工程硬化）
- 主工作区：`D:/ai_memory_chat` (`main`)
- 功能 worktree：`D:/ai_memory_chat/.worktrees/provider-sdk` (`feat/provider-sdk-adaptation`)
- 最近回归基线：`python -m unittest discover -s tests -p "test_*.py" -v` => `34 passed`
- 已知结构风险：
  - `scripts/chunk_and_index.py` 与 `scripts/incremental_update.py` 依赖 `.claude/skills/.../scripts` 注入路径
  - `chunk_chat_memo/chunk_topic_notes` 及 `incremental_update` 核心路径测试不足
  - 根目录缺少 README，部分文档与现状不一致

## Scope

- In scope:
  - Agent 友好性改造（可维护性、可测试性、可恢复性）
  - 文档与代码一致性修复
  - CI 与最小工程规范落地
- Out of scope:
  - 新 provider 实网集成实现
  - 新 chunk 算法策略扩展

### Task 1: 去除外部路径耦合（P0）

**Files:**
- Create: `scripts/core/chunk_schema.py`
- Create: `scripts/core/vector_indexer.py`
- Modify: `scripts/chunk_and_index.py`
- Modify: `scripts/incremental_update.py`
- Test: `tests/chunking/test_runtime_imports.py`

**Step 1: Write the failing test**
- 新增测试断言：
  - 不依赖 `sys.path.insert(.../.claude/...)` 仍可导入并执行 `chunk_markdown_document`
  - `incremental_update.get_chunk_id` 与 `chunk_note_file` 导入路径稳定

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/chunking/test_runtime_imports.py -v`  
Expected: FAIL（当前代码仍有 `.claude` 路径注入）

**Step 3: Write minimal implementation**
- 将 `chunk_schema`/`vector_indexer` 迁入仓库内 `scripts/core/`
- 移除 `sys.path.insert` 与外部导入
- 统一改为 `scripts.*` 包内导入

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests/chunking/test_runtime_imports.py -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/chunk_and_index.py scripts/incremental_update.py scripts/core/chunk_schema.py scripts/core/vector_indexer.py tests/chunking/test_runtime_imports.py
git commit -m "refactor: remove external .claude path coupling for core chunking runtime"
```

### Task 2: 补齐 chunking 未覆盖核心路径测试（P0）

**Files:**
- Test: `tests/chunking/test_chunk_note_file_paths.py`
- Modify: `scripts/chunk_and_index.py` (仅在必要时做可测性微调)

**Step 1: Write the failing test**
- 覆盖：
  - `chat-memo` 路由分支
  - `#topic` 路由分支
  - 默认 markdown 路由分支
  - 错误输入容错分支

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/chunking/test_chunk_note_file_paths.py -v`  
Expected: 至少 1 个断言失败（暴露分支缺口或可测性问题）

**Step 3: Write minimal implementation**
- 仅做最小可测性修改（不改变既有行为）

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests/chunking/test_chunk_note_file_paths.py -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add tests/chunking/test_chunk_note_file_paths.py scripts/chunk_and_index.py
git commit -m "test: cover chunk routing paths for chat memo topic and markdown"
```

### Task 3: 补齐 incremental_update 关键路径测试（P0）

**Files:**
- Test: `tests/chunking/test_incremental_update_core.py`
- Modify: `scripts/incremental_update.py` (仅在必要时拆分函数以便测试)

**Step 1: Write the failing test**
- 覆盖：
  - `get_existing_ids` 空库/异常容错
  - `index_chunks_incremental` 对已存在 ID 的跳过逻辑
  - `get_chunk_id` 稳定性（已实现规则回归锁定）

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/chunking/test_incremental_update_core.py -v`  
Expected: FAIL

**Step 3: Write minimal implementation**
- 抽离副作用，保持行为一致
- 对 DB/Embedding 通过 mock 注入测试

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests/chunking/test_incremental_update_core.py -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add tests/chunking/test_incremental_update_core.py scripts/incremental_update.py
git commit -m "test: add incremental update core-path coverage with mocked dependencies"
```

### Task 4: 文档单一事实源与过时内容修复（P0）

**Files:**
- Create: `README.md`
- Create: `docs/CURRENT_STATUS.md`
- Modify: `scripts/README.md`
- Modify: `scripts/check_model.py`
- Modify: `docs/plans/2026-03-01-context-compression-handoff.md` (加“历史快照”说明)

**Step 1: Write the failing test**
- 新增文档一致性检查脚本（最小版），验证：
  - `README.md` 存在
  - `check_model.py` 不引用不存在脚本

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/docs/test_docs_consistency.py -v`  
Expected: FAIL

**Step 3: Write minimal implementation**
- 新增根 README（入口、架构、验证命令）
- 新增 `docs/CURRENT_STATUS.md`（当前阶段、分支、测试基线）
- 修复 `scripts/README.md` 的过时叙述
- 修复 `check_model.py` 中不存在脚本提示

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests/docs/test_docs_consistency.py -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add README.md docs/CURRENT_STATUS.md scripts/README.md scripts/check_model.py tests/docs/test_docs_consistency.py docs/plans/2026-03-01-context-compression-handoff.md
git commit -m "docs: establish current source-of-truth docs and fix stale references"
```

### Task 5: 建立 CI 最小质量门（P0）

**Files:**
- Create: `.github/workflows/unittest.yml`

**Step 1: Write the failing test**
- 本地不需要先写测试；此任务以 CI 配置为主

**Step 2: Run local sanity**

Run: `python -m unittest discover -s tests -p "test_*.py" -v`  
Expected: PASS（作为 CI 基线）

**Step 3: Write minimal implementation**
- 在 GitHub Actions 中执行同一命令
- 触发条件：push + pull_request（`main`/`feat/*`）

**Step 4: Validate workflow syntax**

Run: `git diff -- .github/workflows/unittest.yml`  
Expected: YAML 结构正确、命令清晰

**Step 5: Commit**

```bash
git add .github/workflows/unittest.yml
git commit -m "ci: add unittest workflow as baseline quality gate"
```

### Task 6: 工程规范统一（P1）

**Files:**
- Create: `pyproject.toml`
- Create: `mypy.ini` (可选，若规则写入 pyproject 可省略)
- Modify: import style in `scripts/*.py`

**Step 1: Write the failing test**
- 增加 lint/type 最小检查命令并记录预期失败点

**Step 2: Run checks to verify failures**

Run: `python -m unittest discover -s tests -p "test_*.py" -v`  
Expected: PASS（行为不回归）  
Run: `ruff check scripts tests`  
Expected: 初次可能 FAIL

**Step 3: Write minimal implementation**
- 统一导入风格与命名
- 增加最小 lint 规则（先不追求严格满分）

**Step 4: Run checks to verify pass**

Run: `ruff check scripts tests`  
Expected: PASS

**Step 5: Commit**

```bash
git add pyproject.toml scripts tests
git commit -m "chore: introduce baseline lint rules and normalize import patterns"
```

## Parallelization Plan

- 串行关卡（必须先做）：
  - Task 1（去耦合）
- 可并行：
  - Task 2（chunk 分支测试）
  - Task 3（incremental_update 测试）
  - Task 4（文档修复）
- 最后串行收口：
  - Task 5（CI）
  - Task 6（规范统一，可延后）

## Definition of Done

- 不再依赖 `.claude` 外部路径注入运行核心脚本
- `chunk_note_file` 三条主要路由均有测试覆盖
- `incremental_update` 核心路径有可重复的 mock 测试
- 根 README + `docs/CURRENT_STATUS.md` 成为上下文恢复入口
- CI 自动执行 `unittest discover` 并通过

## Verification Commands

```bash
python -m unittest discover -s tests -p "test_*.py" -v
python -m unittest tests/chunking/test_chunk_note_file_paths.py -v
python -m unittest tests/chunking/test_incremental_update_core.py -v
```

## Risks and Rollback

- 风险：去除外部依赖后，历史脚本运行入口可能变化
- 缓解：保留兼容导入层（短期），并在 README 写清迁移方式
- 回滚：按任务提交粒度逐个回滚，不做大颗粒混合提交

