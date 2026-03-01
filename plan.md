Hybrid（推荐）

- 做法：

  - 内部定义统一协议：ConversationRequest/Response、ChunkRequest/ChunkResult

  - 第一层原生适配器：OpenAI / Anthropic / Gemini

  - 第二层兼容适配器：OpenAI-compatible（LiteLLM/OpenRouter/Ollama/vLLM 等）

  - 默认 provider=local_default（保持你在 Claude Code/Codex 的默认工作方式）

  - 可选开启第三方 provider

- 优点：兼顾灵活性和上限；未来加 provider 基本只加 adapter。

- 风险：初期设计工作量比 gateway-only 大一点。

- 适合：你现在这个“灵活优先 + 可扩展 + 可选第三方”的目标。

## 自动分块（配合方案 3 的推荐形态）

- Parser：Markdown AST/结构识别（标题、列表、代码块、对话段）

- Structural Split：先按语义边界粗分（而不是文件格式名）

- Semantic Refine：对超大块做 embedding/相似度细分

- Size Normalize：强约束 chunk 尺寸窗口（避免过小/过大）

- Quality Gate：每批次统计分块质量（长度分布、重复率、召回代理指标）

这个设计参考了现成能力，而不是从零拍脑袋写规则。

## 你可以直接拍板的推荐

我建议你选 方案 3（Hybrid）。
它最符合你说的：不被单一格式脚本绑死，同时支持可选第三方 API/model，并且可拆成并行子任务给子 agent 做。

---

## 当前进度（2026-03-01）

- 已完成：评估现有自动分块机制，结论是“可用但不够稳健”，不建议直接保留原样。
- 已完成：确认总体方向采用方案 3（Hybrid）。
- 已完成：确认必须优先支持 `notes` 中已有文件类型，重点是 `.md`。
- 已确认原则：先看可复用的开源实现/API 规范，再动手写代码。

## 我们现在所在阶段

- 阶段：从“方向确定”进入“可执行拆解”。
- 目标：把方案 3 拆成可并行的小任务，并定义每个任务的输入/输出、验收标准、风险控制。

## 下一步（正在进行）

- 子任务 A：自动分块升级设计（Markdown 结构识别 + 语义细分 + 尺寸归一 + 质量门禁）。
- 子任务 B：第三方模型接入架构设计（统一接口 + 原生 provider + OpenAI-compatible provider）。
- 子任务 C：并行执行策略设计（哪些任务可子 agent 并行，哪些必须串行）。
- 产出：先形成一版任务表和执行顺序，再进入实现/改造。

## 下一节：可执行拆解 v1（并行友好）

### 0) 串行前置（必须先做）

- T0.1 基线冻结：记录当前 `chunk_and_index.py` 的分块统计和检索基线（用于回归对比）。
- T0.2 参考对齐：确定可复用规范与实现（OpenAI/Anthropic/Gemini 官方 API，LlamaIndex/Unstructured 方案边界）。
- 验收：形成 `baseline` 指标表（chunk 数量分布、过小/过大比例、重复率代理指标）。

### 1) 可并行任务组 A（分块能力）

- A1 Markdown 结构解析器
  - 输入：`notes/*.md`
  - 输出：标准化 Block 序列（heading/list/code/paragraph/dialogue）
  - 验收：覆盖当前 notes 中样本，`##无空格` 标题可识别。

- A2 结构化粗分策略（Structural Split）
  - 输入：Block 序列
  - 输出：按语义边界形成初始 chunk
  - 验收：跨标题错误拼接显著下降。

- A3 尺寸归一（Size Normalize）
  - 输入：初始 chunk
  - 输出：满足窗口约束的 chunk（最小/目标/最大）
  - 验收：`<min` 与 `>max` 比例降到阈值内（阈值在实施前锁定）。

- A4 语义细分（Semantic Refine，可开关）
  - 输入：超大 chunk
  - 输出：语义相似度驱动的二次拆分结果
  - 验收：对超长段落样本可稳定拆分，且不破坏上下文连贯性。

- A5 质量门禁（Quality Gate）
  - 输入：最终 chunks
  - 输出：批次质量报告 JSON + 失败阈值告警
  - 验收：每次索引前可自动出报告并可阻断明显劣化。

### 2) 可并行任务组 B（对话模型接入）

- B1 统一接口层
  - 定义：`ConversationRequest/Response`、Provider 抽象、错误模型、重试与超时策略。
  - 验收：本地默认 provider 与第三方 provider 共用同一调用入口。

- B2 原生 Provider 适配器
  - 目标：OpenAI / Anthropic / Gemini（最小可用子集：文本对话）。
  - 验收：三者都能通过同一 smoke 测试契约。

- B3 OpenAI-compatible 适配器
  - 目标：LiteLLM / OpenRouter / Ollama / vLLM（通过 base_url + key + model 配置接入）。
  - 验收：至少 1 个兼容网关实测跑通。

- B4 配置与回退
  - 默认：`provider=local_default`
  - 可选：切换到第三方 provider，失败时可回退默认。
  - 验收：配置错误可读报错，回退行为可预测。

### 3) 并行执行建议（子 agent）

- 可并行：
  - 组 A 与组 B 可同时推进（文件和模块边界独立）。
  - A1/A2 与 B1 可先并行；A3/A4 依赖 A2；B2/B3 依赖 B1。
- 必须串行：
  - 统一验收、集成联调、回归评估、文档更新。

### 4) Definition of Done（本阶段）

- `.md`（notes 现有样本）分块稳定通过质量门禁。
- 检索准确率代理指标相对基线无回退，且极端 chunk 比例下降。
- 默认本地模式不受影响；第三方 provider 为“可选增强”。
- 关键流程有最小测试与可复现命令。

## 下一步产物：接口契约草案 v1（字段级）

### ConversationRequest（统一对话请求）

- `provider: str`  
  - 取值：`local_default | openai | anthropic | gemini | openai_compatible`
- `model: str | None`
- `messages: list[Message]`  
  - `Message = {role: system|user|assistant|tool, content: str, name?: str, tool_call_id?: str}`
- `stream: bool = false`
- `temperature: float | None`
- `top_p: float | None`
- `max_tokens: int | None`
- `stop: list[str] | None`
- `timeout_ms: int = 60000`
- `retry: {max_attempts: int = 2, backoff_ms: int = 400}`
- `auth: {api_key_env?: str}`  
  - `local_default` 默认不要求外部 key
- `endpoint: {base_url?: str}`  
  - 给 `openai_compatible` 使用
- `fallback_provider: str | None`
- `metadata: {session_id?: str, trace_id?: str, tags?: list[str]}`

### ConversationResponse（统一对话响应）

- `provider: str`
- `model: str`
- `output_text: str`
- `finish_reason: str | None`
- `usage: {input_tokens?: int, output_tokens?: int, total_tokens?: int}`
- `latency_ms: int`
- `raw: dict`（原始 provider 响应，便于排障）
- `error: ProviderError | None`

### ProviderError（统一错误模型）

- `type: str`（`auth_error | rate_limit | timeout | invalid_request | provider_unavailable | unknown`）
- `message: str`
- `provider: str`
- `status_code: int | None`
- `retryable: bool`
- `raw: dict | None`

### ChunkRequest（统一分块请求）

- `source: {path: str, filename: str, filetype: str = "md"}`
- `content: str`（优先直接传内容，避免二次 IO）
- `parser: {mode: "markdown_ast", detect_dialogue: bool = true}`
- `split_policy:`
  - `structural_first: bool = true`
  - `size: {min_chars: int = 120, target_chars: int = 500, max_chars: int = 1400}`
  - `overlap_chars: int = 60`
- `semantic_refine:`
  - `enabled: bool = true`
  - `only_if_over_max: bool = true`
  - `similarity_threshold: float = 0.72`
- `metadata_seed: {date?: str, tags?: list[str]}`

### ChunkResult（统一分块结果）

- `chunks: list[ChunkRecord]`
- `stats:`
  - `total_chunks: int`
  - `small_chunks: int`
  - `large_chunks: int`
  - `avg_chars: float`
  - `dup_ratio_proxy: float`
- `quality_gate: {passed: bool, failed_rules: list[str]}`
- `warnings: list[str]`

### ChunkRecord（兼容现有 Chunk schema）

- `content: str`
- `metadata:`
  - `filename: str`
  - `filepath: str`
  - `chunk_id: int`
  - `chunk_type: str`
  - `title?: str`
  - `date?: str`
  - `sub_chunk_id?: int`
  - `tags?: list[str]`
  - `char_start?: int`
  - `char_end?: int`

---

## 并行开发执行记录（Wave 1，2026-03-01）

### 已启动的并行任务

- Lane A（分块基础）：A1 `Markdown 结构解析器`
- Lane B（Provider 基础）：B1 `统一接口层（契约与基类）`

### 已完成产物

- Agent 上下文包：
  - `docs/plans/agent-brief-lane-a-chunking.md`
  - `docs/plans/agent-brief-lane-b-providers.md`
- A 线代码：
  - `scripts/chunking/markdown_blocks.py`
  - `scripts/chunking/__init__.py`
  - `scripts/chunk_and_index.py`（修复 `##无空格` 标题分割）
- B 线代码：
  - `scripts/providers/contracts.py`
  - `scripts/providers/base.py`
  - `scripts/providers/__init__.py`
- 测试：
  - `tests/chunking/test_markdown_blocks.py`
  - `tests/providers/test_contracts.py`
  - `tests/__init__.py`
  - `tests/chunking/__init__.py`
  - `tests/providers/__init__.py`

### 验证结果

- 受限环境说明：无法联网安装 `pytest`，改用内置 `unittest` 执行红绿测试循环。
- 通过命令：
  - `python -m unittest tests/chunking/test_markdown_blocks.py`
  - `python -m unittest tests/providers/test_contracts.py`
  - `python -m unittest discover -s tests -p "test_*.py" -v`
- 结果：`5 passed`

### Wave 2 执行结果（已完成）

- Lane A：A2 + A3（结构化粗分 + 尺寸归一）
  - 新增：`scripts/chunking/splitters.py`
  - 改造：`scripts/chunk_and_index.py` 已接入 `parse_blocks -> structural_split -> normalize_size`
  - 测试：`tests/chunking/test_splitters.py` 通过
- Lane B：B2（原生 provider 适配器骨架）
  - 新增：
    - `scripts/providers/openai_adapter.py`
    - `scripts/providers/anthropic_adapter.py`
    - `scripts/providers/gemini_adapter.py`
    - `scripts/providers/registry.py`
  - 测试：`tests/providers/test_native_adapters.py` 通过

### Wave 2 验证结果

- 命令：
  - `python -m unittest tests/chunking/test_splitters.py -v`
  - `python -m unittest tests/providers/test_native_adapters.py -v`
  - `python -m unittest discover -s tests -p "test_*.py" -v`
- 结果：`9 passed`
- 采样验证：`chunk_note_file(notes/25.12.06.md)` 返回 `1` 个 `section` chunk（已支持 `##无空格` 标题）

### 下一波并行建议（Wave 3）

- Lane A：A4（Semantic Refine 可开关）
- Lane B：B3（OpenAI-compatible 适配器）
- 串行关卡：A5（Quality Gate）+ 增量更新哈希修复 + 基线对比报告

---

## 压缩上下文恢复锚点（2026-03-01）

- 关键交接文件：
  - `docs/plans/2026-03-01-context-compression-handoff.md`
- 压缩后建议第一条动作：
  - 按交接文件第 7 节“恢复顺序”加载上下文，再进入 Wave 3。


### Wave 3 执行结果（已完成）
- Lane A：A4（Semantic Refine，可开关）
  - 新增：`scripts/chunking/semantic_refine.py`
  - 改造：`scripts/chunk_and_index.py` 已接入 `structural_split -> apply_semantic_refine -> normalize_size`
  - 测试：`tests/chunking/test_semantic_refine.py` 通过
- Lane B：B3（OpenAI-compatible 适配器）
  - 新增：`scripts/providers/openai_compatible_adapter.py`
  - 改造：`scripts/providers/registry.py` 新增兼容映射
    - `openai_compatible | openai-compatible | litellm | openrouter | ollama | vllm`
  - 测试：`tests/providers/test_openai_compatible.py` 通过

### Wave 3 验证结果
- 定向测试：
  - `python -m unittest tests/chunking/test_semantic_refine.py -v`
  - `python -m unittest tests/providers/test_openai_compatible.py -v`
- 全量回归：
  - `python -m unittest discover -s tests -p "test_*.py" -v`
- 结果：`16 passed`

---

### Wave 4 串行关卡结果（2026-03-01）
- A5（Quality Gate）已落地：
  - 新增：`scripts/chunking/quality_gate.py`
  - 能输出统计：`total_chunks/small_chunks/large_chunks/avg_chars/dup_ratio_proxy`
  - 能评估门禁：`evaluate(stats, thresholds)`，返回 `passed + failed_rules`
  - 主流程接入：`scripts/chunk_and_index.py` 在索引前执行质量门禁，失败时阻断索引
- `incremental_update.py#get_chunk_id` 稳定性修复已完成：
  - 从“前100字符哈希”改为“全内容归一化 + SHA256 + 长度”组合
  - 解决尾部内容变化不触发 ID 变化的问题
- 运行级冒烟问题已修复（无 chromadb 也可跑纯分块）：
  - `scripts/chunk_and_index.py` 的 `VectorIndexer` 改为 `main()` 内惰性导入
  - `scripts/incremental_update.py` 的 `chromadb/sentence_transformers` 改为函数内惰性导入

### Wave 4 验证结果
- 新增测试：
  - `tests/chunking/test_quality_gate.py`
- 定向测试：
  - `python -m unittest tests/chunking/test_quality_gate.py -v` => `3 passed`
- 全量回归：
  - `python -m unittest discover -s tests -p "test_*.py" -v` => `19 passed`
- 运行级冒烟：
  - `chunk_note_file(notes/25.12.06.md)` => `1` 个 `section` chunk

### Wave 4-2 基线对比报告（2026-03-01）
- 产物：
  - `docs/plans/baseline-2026-03-01.json`
  - `docs/plans/baseline-2026-03-01.md`
- 样本范围：`notes/*.md` 共 `15` 个文件。
- 对比口径：
  - `coarse`：`parse_blocks -> structural_split`（历史基线代理）
  - `size_only`：`parse_blocks -> structural_split -> normalize_size`
  - `current`：`parse_blocks -> structural_split -> semantic_refine -> normalize_size`
- 汇总指标（small/large/extreme/dup）：
  - `coarse`：`total=29`，`small_ratio=0.310`，`large_ratio=0.310`，`extreme_ratio=0.621`，`dup_ratio_proxy=0.000`，`avg_chars=4168.31`
  - `size_only`：`total=110`，`small_ratio=0.000`，`large_ratio=0.000`，`extreme_ratio=0.000`，`dup_ratio_proxy=0.164`，`avg_chars=1097.66`
  - `current`：`total=265`，`small_ratio=0.000`，`large_ratio=0.000`，`extreme_ratio=0.000`，`dup_ratio_proxy=0.196`，`avg_chars=454.44`
- 关键变化：
  - `current vs coarse`：`extreme_ratio -0.621`，`avg_chars -3713.87`，`total_chunks +236`
  - `current vs size_only`：`extreme_ratio +0.000`，`dup_ratio_proxy +0.033`，`avg_chars -643.22`，`total_chunks +155`
- 结论：
  - 目标“极端块比例下降”已满足（当前为 `0.000`）。
  - `dup_ratio_proxy` 有上升但仍低于门禁阈值 `0.40`，后续可作为优化项持续跟踪。

### Wave 4-3 重复率代理优化（2026-03-01）
- 代码改动：
  - 新增：`scripts/chunking/deduplicate.py`
    - `deduplicate_exact_chunks(chunks)`：按“内容归一化（压缩空白 + 小写）”做全局精确去重
    - 保留首条为 canonical，并在 metadata 聚合 `source_count/sources`
  - 改造：`scripts/chunk_and_index.py`
    - 在索引前增加去重步骤，打印 `Dedup Summary`
- 新增测试：
  - `tests/chunking/test_deduplicate.py`
    - 验证重复折叠与来源聚合
    - 验证不同内容不误删
- 验证报告：
  - `docs/plans/verification-2026-03-01.json`
  - `docs/plans/verification-2026-03-01.md`
- 核心指标（真实链路：`chunk_note_file`）：
  - 去重前：`total=156`，`small_ratio=0.218`，`large_ratio=0.186`，`dup_ratio_proxy=0.212`，`avg_chars=754.74`
  - 去重后：`total=123`，`small_ratio=0.211`，`large_ratio=0.163`，`dup_ratio_proxy=0.000`，`avg_chars=686.58`
  - 变化：`total -33`，`dup_ratio_proxy -0.212`，`small_ratio -0.007`，`large_ratio -0.023`

### Wave 4-4 近重复（非完全重复）保守评估（2026-03-01）
- 评估范围与前置：
  - 范围：`notes/*.md` 共 `15` 个文件。
  - 前置：先运行当前默认链路中的精确去重（`deduplicate_exact_chunks`），得到 `123` 个 chunk 作为近重复评估输入。
- 产物：
  - `docs/plans/near-duplicate-assessment-2026-03-01.json`
  - `docs/plans/near-duplicate-assessment-2026-03-01.md`
- 评估口径（保守约束）：
  - 仅同 `chunk_type` 比较
  - 两侧 `length >= min_chars`
  - `length_ratio >= len_ratio_min`
  - 前缀相似度（前 120 归一化字符）`>= prefix_threshold`
  - 全文归一化相似度（`difflib.SequenceMatcher`）`>= sim_threshold`
- 敏感性结论（离线模拟，不启用）：
  - `strict_recommended`：`sim>=0.97`，`len_ratio>=0.92`，`prefix>=0.93`，`min_chars>=180`
    - `pairs=1`，`would_remove=1`（`0.81%`），门禁仍通过
  - `balanced_candidate`：`sim>=0.96`，`len_ratio>=0.90`，`prefix>=0.92`，`min_chars>=180`
    - `pairs=2`，`would_remove=2`（`1.63%`），门禁仍通过
  - `wider_candidate`：`sim>=0.95`，`len_ratio>=0.88`，`prefix>=0.90`，`min_chars>=160`
    - `pairs=2`，`would_remove=2`（`1.63%`），门禁仍通过
- 推荐：
  - 仅将 `strict_recommended` 作为未来可选实验候选，保持默认关闭（`offline_assessment_only`）。

### Wave 5-1 B4 配置与回退（2026-03-01）
- 代码改动：
  - 新增：`scripts/providers/settings.py`
    - `load_provider_settings(config_path, env)`：支持 YAML + 环境变量加载，默认 `provider=local_default`
    - `resolve_provider_chain(primary, fallback)`：确定主备 provider 链路
    - `build_request_from_settings(...)`：将配置映射到统一 `ConversationRequest`
  - 新增：`scripts/chat_entry.py`
    - `chat_with_fallback(request, provider_kwargs_map)`：主 provider 失败后按策略回退
    - 失败轨迹落盘到响应 `raw.fallback_trace`
  - 新增：`scripts/providers/local_default_adapter.py`
    - 提供 `local_default` 适配入口（可注入 transport；无 transport 时保持 host delegated 语义）
  - 改造：`scripts/providers/registry.py`
    - 新增 `local_default | local | default` 映射
  - 新增配置样例：`config/provider.example.yaml`
- 新增测试：
  - `tests/providers/test_fallback.py`
    - 验证 `resolve_provider_chain`
    - 验证主 provider 异常时回退 `local_default`
    - 验证环境变量覆盖 YAML 配置
- 验证结果：
  - `python -m unittest tests/providers/test_fallback.py -v` => `3 passed`
  - `python -m unittest discover -s tests/providers -p "test_*.py" -v` => `12 passed`
  - `python -m unittest discover -s tests -p "test_*.py" -v` => `24 passed`
- 判定：
  - B4 最小闭环已完成：默认本地模式保留、第三方 provider 可选、失败回退路径可预测。

### Wave 5-2 计划与批次 1（2026-03-01）
- 新计划文档：
  - `docs/plans/2026-03-01-provider-runtime-hardening-plan.md`
- 串行/并行拆分：
  - 串行：Task 1（参考对齐） -> Task 2（settings 合同加固） -> Task 4（fallback 分层） -> Task 6（全量回归与交接）
  - 可并行：Task 3A（native transport）与 Task 3B（openai-compatible）；Task 5（配置文档）可在 Task 2 后并行
- Batch 1 已完成（Task 1 + Task 2 + Task 3A）：
  - Task 1 产物：
    - `docs/plans/2026-03-01-provider-api-reference.md`
  - Task 2 产物：
    - 新增测试：`tests/providers/test_settings_contract.py`
    - 改造：`scripts/providers/settings.py`
      - timeout 护栏：`MIN_TIMEOUT_MS=1000`，`MAX_TIMEOUT_MS=300000`
      - 非法超时值回退默认 `60000`
  - Task 3A 产物：
    - 新增：`scripts/providers/transport.py`
      - `execute_transport(...)` + `normalize_transport_exception(...)`
      - 超时异常归一化为 `ProviderError(type=\"timeout\", retryable=True)`
    - 新增测试：`tests/providers/test_transport_native.py`
    - 改造：
      - `scripts/providers/openai_adapter.py`
      - `scripts/providers/anthropic_adapter.py`
      - `scripts/providers/gemini_adapter.py`
      - 统一捕获 transport 异常并返回结构化错误响应
- Batch 1 验证：
  - `python -m unittest tests/providers/test_settings_contract.py -v` => `3 passed`
  - `python -m unittest tests/providers/test_transport_native.py -v` => `2 passed`
  - `python -m unittest discover -s tests/providers -p "test_*.py" -v` => `17 passed`

### Wave 5-2 Batch 2 (2026-03-01)
- Completed: Task 3B (openai-compatible transport/alias hardening)
  - Added: `tests/providers/test_transport_compatible.py`
  - Updated: `scripts/providers/openai_compatible_adapter.py`
  - Behavior: alias request provider is normalized to `openai_compatible`; transport exceptions are normalized via `execute_transport(...)`.
- Completed: Task 4 (fallback policy stratification)
  - Updated: `tests/providers/test_fallback.py`
  - Updated: `scripts/chat_entry.py`
  - Behavior: retryable errors fallback; non-retryable policy errors do not fallback; `unsupported_provider` fallback requires `metadata.allow_unsupported_fallback=true`.
- Completed: Task 5 (config/docs examples)
  - Updated: `config/provider.example.yaml`
  - Added: `docs/plans/provider-config-usage.md`
- Batch 2 verification:
  - `python -m unittest tests/providers/test_transport_compatible.py -v` => `3 passed`
  - `python -m unittest tests/providers/test_fallback.py -v` => `5 passed`
  - `python -m unittest discover -s tests/providers -p "test_*.py" -v` => `22 passed`
  - `python -m unittest discover -s tests -p "test_*.py" -v` => `34 passed`
- Workflow stage:
  - `executing-plans` Batch 2 completed, currently at Report/Checkpoint.
  - Next serial gate: Task 6 (full verification snapshot + handoff final update).

### Wave 5-2 Task 6 Finalization (2026-03-01)
- Task 6 completed: full verification and handoff checkpoint updated.
- Fresh verification evidence:
  - `python -m unittest discover -s tests/providers -p "test_*.py" -v` => `22 passed`
  - `python -m unittest discover -s tests -p "test_*.py" -v` => `34 passed`
- Workflow status:
  - `executing-plans` implementation tasks are complete (Task 1-6 done).
  - Entered final-node check via `finishing-a-development-branch`.
- Environment note:
  - `git rev-parse --is-inside-work-tree` failed (`not a git repository`), so branch integration options (merge/PR/discard) are not executable in this workspace root.
  - Work output remains in-place under current workspace for manual VCS integration if needed.
