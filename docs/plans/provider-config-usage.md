# Provider Config Usage

This project keeps `local_default` as the default provider. Third-party providers are optional and can use fallback.

## 1) Local default only

```yaml
provider:
  primary: local_default
  fallback:
  model:
  timeout_ms: 60000
  base_url:
  api_key_env:
```

## 2) OpenAI primary with local fallback

```yaml
provider:
  primary: openai
  fallback: local_default
  model: gpt-4.1-mini
  timeout_ms: 60000
  base_url:
  api_key_env: OPENAI_API_KEY
```

Behavior:
- If OpenAI returns retryable or provider-unavailable errors, request falls back to `local_default`.
- Non-retryable policy errors (for example `invalid_request`) do not fallback.

## 3) OpenAI-compatible with custom base_url

```yaml
provider:
  primary: openai_compatible
  fallback: local_default
  model: qwen2.5:latest
  timeout_ms: 60000
  base_url: http://127.0.0.1:11434/v1
  api_key_env: OLLAMA_API_KEY
```

Behavior:
- Request-level `endpoint.base_url` overrides provider default `base_url`.
- Aliases like `openrouter|ollama|vllm|litellm` are normalized to `openai_compatible` provider contract.

## Optional fallback policy for unsupported provider names

By default, `unsupported_provider` does not fallback to avoid hiding config errors.
To allow fallback for unknown provider names, pass request metadata:

```python
ConversationRequest(
    provider="unknown_provider",
    fallback_provider="local_default",
    metadata={"allow_unsupported_fallback": True},
    messages=[{"role": "user", "content": "hello"}],
)
```
