# Provider API Reference Snapshot (B4.2)

Date: 2026-03-01
Purpose: lock a minimal mapping baseline before runtime hardening.

## OpenAI (Chat Completions compatible)

- Endpoint: `POST /v1/chat/completions`
- Auth: `Authorization: Bearer $OPENAI_API_KEY`
- Request core:
  - `model`
  - `messages[]` (role/content)
  - optional: `temperature`, `top_p`, `max_tokens`, `stop`, `stream`
- Response core mapping target:
  - output text from first assistant choice
  - finish reason
  - usage token fields
- Notes:
  - New projects are guided toward Responses API, but Chat Completions compatibility is required for gateway providers.

Reference:
- https://platform.openai.com/docs/api-reference/chat/create-chat-completion

## Anthropic (Messages)

- Endpoint: `POST /v1/messages`
- Auth/header:
  - `x-api-key: $ANTHROPIC_API_KEY`
  - `anthropic-version: 2023-06-01`
  - `content-type: application/json`
- Request core:
  - `model`
  - `max_tokens`
  - `messages[]`
- Response core mapping target:
  - text content blocks
  - `stop_reason`
  - usage (`input_tokens`, `output_tokens`)

Reference:
- https://docs.anthropic.com/en/api/messages

## Gemini (GenerateContent)

- Endpoint shape: `POST /v1beta/models/{model}:generateContent`
- Auth/header:
  - `x-goog-api-key: $GEMINI_API_KEY`
  - `Content-Type: application/json`
- Request core:
  - `contents[]` with `parts[]`
- Response core mapping target:
  - text candidates/parts
  - finish reason equivalent
  - usage metadata if available

Reference:
- https://ai.google.dev/api

## Unified Contract Mapping (Current Project)

- Inbound contract: `ConversationRequest`
  - provider/model/messages/timeout/base_url/api_key_env/fallback_provider
- Outbound contract: `ConversationResponse`
  - provider/model/output_text/latency_ms/finish_reason/usage/error
- Error normalization goals:
  - classify into `provider_unavailable | unsupported_provider | transport_error | auth_error | rate_limited | timeout`
  - encode retryability for fallback decisions

## Fallback Baseline

- Default provider: `local_default`
- Fallback chain: `primary -> fallback_provider` (when configured and allowed)
- `raw.fallback_trace` keeps error history for observability.
