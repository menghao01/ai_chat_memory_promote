from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Literal, Optional


MessageRole = Literal["system", "user", "assistant", "tool"]


@dataclass
class Message:
    role: MessageRole
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None


@dataclass
class RetryPolicy:
    max_attempts: int = 2
    backoff_ms: int = 400


@dataclass
class AuthConfig:
    api_key_env: Optional[str] = None


@dataclass
class EndpointConfig:
    base_url: Optional[str] = None


@dataclass
class ConversationRequest:
    provider: str
    messages: List[Dict[str, Any]]
    model: Optional[str] = None
    stream: bool = False
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    stop: Optional[List[str]] = None
    timeout_ms: int = 60000
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    auth: AuthConfig = field(default_factory=AuthConfig)
    endpoint: EndpointConfig = field(default_factory=EndpointConfig)
    fallback_provider: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderError:
    type: str
    message: str
    provider: str
    status_code: Optional[int] = None
    retryable: bool = False
    raw: Optional[Dict[str, Any]] = None


@dataclass
class ConversationResponse:
    provider: str
    model: str
    output_text: str
    latency_ms: int
    finish_reason: Optional[str] = None
    usage: Dict[str, int] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict)
    error: Optional[ProviderError] = None


@dataclass
class ChunkRequest:
    source: Dict[str, str]
    content: str
    parser: Dict[str, Any] = field(default_factory=lambda: {"mode": "markdown_ast", "detect_dialogue": True})
    split_policy: Dict[str, Any] = field(
        default_factory=lambda: {
            "structural_first": True,
            "size": {"min_chars": 120, "target_chars": 500, "max_chars": 1400},
            "overlap_chars": 60,
        }
    )
    semantic_refine: Dict[str, Any] = field(
        default_factory=lambda: {
            "enabled": True,
            "only_if_over_max": True,
            "similarity_threshold": 0.72,
        }
    )
    metadata_seed: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChunkResult:
    chunks: List[Dict[str, Any]]
    stats: Dict[str, Any]
    quality_gate: Dict[str, Any]
    warnings: List[str] = field(default_factory=list)


def to_dict(value: Any) -> Dict[str, Any]:
    """Serialize dataclass contracts to dict for adapter transport."""
    return asdict(value)
