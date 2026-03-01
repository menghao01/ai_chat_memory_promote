# Lane B Agent Brief - Provider Contracts Foundation

## Scope

- Focus tasks: `B1` first (统一接口层)
- Files primarily under:
  - `scripts/providers/`
  - `tests/providers/`

## Goal (This Wave)

- Define typed contracts:
  - `ConversationRequest`
  - `ConversationResponse`
  - `ProviderError`
  - `ChunkRequest`
  - `ChunkResult`
- Define provider abstraction:
  - `BaseProvider.chat(request) -> ConversationResponse`

## Constraints

- Keep default mode compatible with `provider=local_default`.
- Keep adapters out-of-scope for this wave (only contract + base abstraction).
- Contracts should be easy to map to OpenAI / Anthropic / Gemini / OpenAI-compatible.

## Acceptance

- Add tests under `tests/providers/test_contracts.py`.
- Start with failing tests, then implement minimal passing models.
- Ensure serialization helper exists for future API mapping.

## Non-Goals

- Do not call external APIs in this wave.
- Do not implement provider registry or fallback logic in this wave.
