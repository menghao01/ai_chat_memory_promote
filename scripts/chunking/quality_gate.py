from typing import Any, Dict, List, Optional


DEFAULT_THRESHOLDS: Dict[str, float] = {
    "small_ratio_max": 0.35,
    "large_ratio_max": 0.35,
    "dup_ratio_proxy_max": 0.40,
    "min_total_chunks": 1,
}


def _normalized_for_dup(text: str) -> str:
    return " ".join((text or "").split()).strip().lower()


def summarize_chunks(
    chunks: List[Dict[str, Any]],
    min_chars: int = 120,
    max_chars: int = 1400,
) -> Dict[str, Any]:
    """
    Build quality summary metrics for final chunk list.
    """
    contents: List[str] = []
    for chunk in chunks:
        content = chunk.get("content", "")
        if isinstance(content, str) and content.strip():
            contents.append(content)

    total = len(contents)
    if total == 0:
        return {
            "total_chunks": 0,
            "small_chunks": 0,
            "large_chunks": 0,
            "avg_chars": 0.0,
            "dup_ratio_proxy": 0.0,
        }

    lengths = [len(c) for c in contents]
    small = sum(1 for n in lengths if n < min_chars)
    large = sum(1 for n in lengths if n > max_chars)
    normalized = [_normalized_for_dup(c) for c in contents]
    unique_count = len(set(normalized))
    dup_ratio_proxy = 1.0 - (unique_count / total)

    return {
        "total_chunks": total,
        "small_chunks": small,
        "large_chunks": large,
        "avg_chars": sum(lengths) / total,
        "dup_ratio_proxy": dup_ratio_proxy,
    }


def evaluate(
    stats: Dict[str, Any],
    thresholds: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Evaluate whether chunk quality meets guardrail thresholds.
    """
    cfg = dict(DEFAULT_THRESHOLDS)
    if thresholds:
        cfg.update(thresholds)

    total = int(stats.get("total_chunks", 0) or 0)
    small = int(stats.get("small_chunks", 0) or 0)
    large = int(stats.get("large_chunks", 0) or 0)
    dup = float(stats.get("dup_ratio_proxy", 0.0) or 0.0)

    if total > 0:
        small_ratio = small / total
        large_ratio = large / total
    else:
        small_ratio = 0.0
        large_ratio = 0.0

    failed_rules: List[str] = []
    if total < int(cfg["min_total_chunks"]):
        failed_rules.append("min_total_chunks")
    if small_ratio > float(cfg["small_ratio_max"]):
        failed_rules.append("small_ratio_max")
    if large_ratio > float(cfg["large_ratio_max"]):
        failed_rules.append("large_ratio_max")
    if dup > float(cfg["dup_ratio_proxy_max"]):
        failed_rules.append("dup_ratio_proxy_max")

    return {
        "passed": len(failed_rules) == 0,
        "failed_rules": failed_rules,
        "ratios": {
            "small_ratio": small_ratio,
            "large_ratio": large_ratio,
            "dup_ratio_proxy": dup,
        },
        "thresholds": cfg,
    }
