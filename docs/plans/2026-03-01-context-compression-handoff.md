# Context Compression Handoff (2026-03-01)

## 1) 项目目标与约束（必须保持）

- 优先目标：`B类目标（灵活性优先）`
  - 数据分块不依赖单一固定格式脚本，能对不同结构自主分块再向量化。
  - 对话模型支持可选第三方 provider/API；默认仍为 `local_default`（不破坏本地默认工作流）。
- 必须支持：当前 `notes/` 中已有文件类型，重点 `.md`。
- 原则：先参考已有规范/实现，再扩展代码。

## 2) 当前方案（已拍板）

- 采用 `Hybrid（方案3）`：
  - 内部统一协议：`ConversationRequest/Response`、`ChunkRequest/ChunkResult`
  - 原生 provider：`openai/anthropic/gemini`
  - 兼容 provider：`openai-compatible`（下一波）

## 3) 已完成进度

### Wave 1（完成）

- A1：Markdown 结构解析基础
  - `scripts/chunking/markdown_blocks.py`
  - `scripts/chunk_and_index.py` 已支持 `##无空格` 标题分割
- B1：统一契约与 provider 基类
  - `scripts/providers/contracts.py`
  - `scripts/providers/base.py`
- 测试
  - `tests/chunking/test_markdown_blocks.py`
  - `tests/providers/test_contracts.py`

### Wave 2（完成）

- A2/A3：结构化粗分 + 尺寸归一
  - `scripts/chunking/splitters.py`
  - `scripts/chunk_and_index.py` 接入链路：`parse_blocks -> structural_split -> normalize_size`
- B2：原生 provider 适配器骨架 + registry
  - `scripts/providers/openai_adapter.py`
  - `scripts/providers/anthropic_adapter.py`
  - `scripts/providers/gemini_adapter.py`
  - `scripts/providers/registry.py`
- 测试
  - `tests/chunking/test_splitters.py`
  - `tests/providers/test_native_adapters.py`

## 4) 验证基线（最近一次）

- 命令：
  - `python -m unittest discover -s tests -p "test_*.py" -v`
- 结果：`9 passed`
- 采样：
  - `chunk_note_file(notes/25.12.06.md)` 返回 `1` 个 `section` chunk（验证 `##无空格` 生效）

## 5) 环境与风险（压缩后容易丢）

- 当前环境不可联网安装新包：`pip install pytest` 失败（socket/网络受限）。
- 因此测试框架采用内置 `unittest`（不是 pytest）。
- 当前目录不是 git 仓库（`fatal: not a git repository`），不能依赖 git 历史恢复上下文。

## 6) 下一步执行（Wave 3）

### Lane A（并行）

- A4：`Semantic Refine`（可开关）
  - 新增 `scripts/chunking/semantic_refine.py`
  - 新增 `tests/chunking/test_semantic_refine.py`

### Lane B（并行）

- B3：`OpenAI-compatible` 适配器
  - 新增 `scripts/providers/openai_compatible_adapter.py`
  - 扩展 `scripts/providers/registry.py`
  - 新增 `tests/providers/test_openai_compatible.py`

### 串行关卡

- A5：`Quality Gate`
- `incremental_update.py` 的 `get_chunk_id` 全内容哈希修复
- 基线对比报告（chunk 分布、极端块比例、重复率代理）

## 7) 压缩后恢复顺序（严格按此读）

1. `D:\ai_memory_chat\plan.md`
2. `D:\ai_memory_chat\docs\plans\2026-03-01-hybrid-flex-chunking-provider-plan.md`
3. `D:\ai_memory_chat\docs\plans\2026-03-01-context-compression-handoff.md`（本文件）
4. 分块主链路：
   - `scripts/chunk_and_index.py`
   - `scripts/chunking/markdown_blocks.py`
   - `scripts/chunking/splitters.py`
5. provider 主链路：
   - `scripts/providers/contracts.py`
   - `scripts/providers/base.py`
   - `scripts/providers/registry.py`
6. 回归测试：
   - `python -m unittest discover -s tests -p "test_*.py" -v`

## 8) 子 agent 分发上下文入口

- Lane A brief:
  - `docs/plans/agent-brief-lane-a-chunking.md`
- Lane B brief:
  - `docs/plans/agent-brief-lane-b-providers.md`

> 以上两个 brief 已做边界约束，可直接用于并行分发。

## 9) Wave 3 最新状态（2026-03-01）
- 已完成 A4：`scripts/chunking/semantic_refine.py`，并在 `scripts/chunk_and_index.py` 接入。
- 已完成 B3：`scripts/providers/openai_compatible_adapter.py`，并扩展 `scripts/providers/registry.py` 支持别名。
- 新增测试：
  - `tests/chunking/test_semantic_refine.py`
  - `tests/providers/test_openai_compatible.py`
- 最新回归：`python -m unittest discover -s tests -p "test_*.py" -v` => `16 passed`
- 下一关卡仍为串行项：A5 `Quality Gate` + `incremental_update.py#get_chunk_id` 稳定性修复 + 基线对比报告。

## 10) Wave 4 串行关卡最新状态（2026-03-01）
- 已完成 A5：`scripts/chunking/quality_gate.py`
  - 提供 `summarize_chunks()` 与 `evaluate()`，可产出质量统计与门禁判定。
  - `scripts/chunk_and_index.py` 已在索引前接入质量门禁，门禁失败时阻断索引。
- 已完成 `incremental_update.py#get_chunk_id` 稳定性修复：
  - 从前100字符哈希改为全内容归一化后哈希（SHA256）+ 内容长度。
- 已修复运行级冒烟阻塞（环境缺少 chromadb）：
  - `scripts/chunk_and_index.py` 将 `VectorIndexer` 改为 `main()` 内惰性导入。
  - `scripts/incremental_update.py` 将 `chromadb` 与 `sentence_transformers` 改为函数内惰性导入。
- 新增测试：
  - `tests/chunking/test_quality_gate.py`
- 最新回归：
  - `python -m unittest tests/chunking/test_quality_gate.py -v` => `3 passed`
  - `python -m unittest discover -s tests -p "test_*.py" -v` => `19 passed`
- 运行级冒烟：
  - `chunk_note_file(notes/25.12.06.md)` => `1` 个 `section` chunk（在无 chromadb 环境可执行）。

## 11) 基线对比报告状态（2026-03-01）
- 已生成基线报告：
  - `docs/plans/baseline-2026-03-01.json`
  - `docs/plans/baseline-2026-03-01.md`
- 样本范围：`notes/*.md`，共 `15` 个文件。
- 对比口径：
  - `coarse`：`parse_blocks -> structural_split`（历史基线代理）
  - `size_only`：`parse_blocks -> structural_split -> normalize_size`
  - `current`：`parse_blocks -> structural_split -> semantic_refine -> normalize_size`
- 核心结果：
  - `coarse`：`extreme_ratio=0.621`，`dup_ratio_proxy=0.000`，`avg_chars=4168.31`，`total=29`
  - `size_only`：`extreme_ratio=0.000`，`dup_ratio_proxy=0.164`，`avg_chars=1097.66`，`total=110`
  - `current`：`extreme_ratio=0.000`，`dup_ratio_proxy=0.196`，`avg_chars=454.44`，`total=265`
- 判定：
  - 极端块比例目标已满足（当前 `0.000`）。
  - 重复率代理较 `size_only` 上升 `+0.033`，但仍在质量门禁阈值（`<=0.40`）内。

## 12) 重复率代理优化最新状态（2026-03-01）
- 已新增索引前去重模块：
  - `scripts/chunking/deduplicate.py`
  - 能力：`deduplicate_exact_chunks(chunks)` 按归一化内容做全局精确去重，并聚合来源元数据（`source_count/sources`）。
- 主流程已接入：
  - `scripts/chunk_and_index.py` 在质量门禁前执行去重并输出 `Dedup Summary`。
- 新增测试：
  - `tests/chunking/test_deduplicate.py`（2 条）
- 全量回归：
  - `python -m unittest discover -s tests -p "test_*.py" -v` => `21 passed`
- 真实性能对比（`chunk_note_file` 全量 `notes/*.md`）：
  - 去重前：`total=156`，`small_ratio=0.218`，`large_ratio=0.186`，`dup_ratio_proxy=0.212`
  - 去重后：`total=123`，`small_ratio=0.211`，`large_ratio=0.163`，`dup_ratio_proxy=0.000`
  - 关键变化：`dup_ratio_proxy -0.212`，且极端比例未回退。

## 13) 近重复（非完全重复）保守评估状态（2026-03-01）
- 已完成离线评估（不改默认行为）：
  - `docs/plans/near-duplicate-assessment-2026-03-01.json`
  - `docs/plans/near-duplicate-assessment-2026-03-01.md`
- 评估输入：
  - 基于 `chunk_note_file(notes/*.md)` 全量结果先做精确去重后，`chunks_after_exact_dedup=123`。
- 保守规则护栏（离线）：
  - 仅同 `chunk_type` 比较
  - 两侧长度不低于 `min_chars`
  - `length_ratio` / 前缀相似度 / 全文相似度均需同时达阈值
- 敏感性结果：
  - `strict_recommended`（`sim>=0.97,len_ratio>=0.92,prefix>=0.93,min_chars>=180`）：
    - `candidate_pairs=1`，`would_remove=1`（`0.81%`）
  - `balanced_candidate`：`candidate_pairs=2`，`would_remove=2`（`1.63%`）
  - `wider_candidate`：`candidate_pairs=2`，`would_remove=2`（`1.63%`）
- 判定：
  - 建议仅保留 `strict_recommended` 作为未来可选实验口径，保持默认关闭并继续离线观察误伤风险。

## 14) B4 配置与回退最新状态（2026-03-01）
- 已完成最小可用闭环：
  - `scripts/providers/settings.py`
    - 支持 `YAML + ENV` 配置加载，默认 `provider=local_default`
    - `resolve_provider_chain(primary, fallback)` 生成主备链路
  - `scripts/chat_entry.py`
    - `chat_with_fallback(...)` 实现主 provider 失败后的回退
    - 输出 `raw.fallback_trace` 便于排障
  - `scripts/providers/local_default_adapter.py`
    - 新增 `local_default` 适配器
  - `scripts/providers/registry.py`
    - 支持 `local_default | local | default`
  - `config/provider.example.yaml`
- 新增测试：
  - `tests/providers/test_fallback.py`（3 条）
- 验证：
  - `python -m unittest tests/providers/test_fallback.py -v` => `3 passed`
  - `python -m unittest discover -s tests/providers -p "test_*.py" -v` => `12 passed`
  - `python -m unittest discover -s tests -p "test_*.py" -v` => `24 passed`
- 当前阶段判断：
  - `executing-plans` 的本批次已完成，处于 **Report/Checkpoint**，可进入下一批（建议：B4.2 实网/SDK 适配与错误分层）。

## 15) B4.2（Provider Runtime Hardening）批次 1 状态（2026-03-01）
- 新计划：
  - `docs/plans/2026-03-01-provider-runtime-hardening-plan.md`
- 串行/并行策略：
  - 串行：Task 1 -> Task 2 -> Task 4 -> Task 6
  - 可并行：Task 3A（native）与 Task 3B（compatible）；Task 5 文档任务在 Task 2 后并行
- Batch 1 已完成：
  - Task 1：参考快照
    - `docs/plans/2026-03-01-provider-api-reference.md`
  - Task 2：settings 合同加固
    - `tests/providers/test_settings_contract.py`
    - `scripts/providers/settings.py`（timeout 护栏与默认回退）
  - Task 3A：native transport 归一化
    - `scripts/providers/transport.py`
    - `tests/providers/test_transport_native.py`
    - `scripts/providers/openai_adapter.py`
    - `scripts/providers/anthropic_adapter.py`
    - `scripts/providers/gemini_adapter.py`
- 验证：
  - `python -m unittest tests/providers/test_settings_contract.py -v` => `3 passed`
  - `python -m unittest tests/providers/test_transport_native.py -v` => `2 passed`
  - `python -m unittest discover -s tests/providers -p "test_*.py" -v` => `17 passed`
- 下一批建议（Batch 2）：
  - Task 3B（openai-compatible transport/alias hardening）
  - Task 4（fallback policy 分层）
  - Task 5（配置示例与使用文档）

## 16) B4.2 (Provider Runtime Hardening) Batch 2 status (2026-03-01)
- Completed tasks:
  - Task 3B: openai-compatible transport/alias hardening
    - `tests/providers/test_transport_compatible.py`
    - `scripts/providers/openai_compatible_adapter.py`
  - Task 4: fallback policy stratification
    - `tests/providers/test_fallback.py`
    - `scripts/chat_entry.py`
  - Task 5: config and usage docs
    - `config/provider.example.yaml`
    - `docs/plans/provider-config-usage.md`
- Policy update summary:
  - Retryable errors fallback to next provider.
  - Non-retryable policy errors do not fallback.
  - `unsupported_provider` only falls back when `metadata.allow_unsupported_fallback=true`.
- Verification:
  - `python -m unittest tests/providers/test_transport_compatible.py -v` => `3 passed`
  - `python -m unittest tests/providers/test_fallback.py -v` => `5 passed`
  - `python -m unittest discover -s tests/providers -p "test_*.py" -v` => `22 passed`
  - `python -m unittest discover -s tests -p "test_*.py" -v` => `34 passed`
- Current workflow stage:
  - `executing-plans` Batch 2 is complete and at Report/Checkpoint.
  - Next step: Task 6 serial finalization (regression evidence + final handoff checkpoint).

## 17) B4.2 Final Node and Closure (2026-03-01)
- Task 6 status: completed.
- Fresh verification:
  - `python -m unittest discover -s tests/providers -p "test_*.py" -v` => `22 passed`
  - `python -m unittest discover -s tests -p "test_*.py" -v` => `34 passed`
- Workflow stage:
  - `executing-plans`: all planned tasks finished.
  - `finishing-a-development-branch`: integration step blocked by environment (`not a git repository`).
- Actionable outcome:
  - Code + tests + docs are in final checkpoint state.
  - If repository context is restored, next action is to run branch integration options there.
