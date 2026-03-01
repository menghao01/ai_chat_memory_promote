from copy import deepcopy
from typing import Any, Dict, List, Tuple


def _normalized_for_dedup(text: str) -> str:
    return " ".join((text or "").split()).strip().lower()


def _source_ref(metadata: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "filename": metadata.get("filename"),
        "filepath": metadata.get("filepath"),
        "chunk_id": metadata.get("chunk_id"),
    }


def deduplicate_exact_chunks(
    chunks: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Collapse exact duplicate chunk content after whitespace/case normalization.

    Keeps the first chunk as canonical and records all source references under:
    - metadata.source_count
    - metadata.sources
    """
    before = len(chunks)
    if before == 0:
        return [], {"before": 0, "after": 0, "removed": 0, "dedup_ratio": 0.0}

    deduped: List[Dict[str, Any]] = []
    seen: Dict[str, Dict[str, Any]] = {}

    for chunk in chunks:
        content = chunk.get("content", "")
        if not isinstance(content, str):
            continue

        key = _normalized_for_dedup(content)
        metadata = chunk.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}

        if not key:
            copied = deepcopy(chunk)
            copied_meta = copied.setdefault("metadata", {})
            copied_meta.setdefault("source_count", 1)
            copied_meta.setdefault("sources", [_source_ref(metadata)])
            deduped.append(copied)
            continue

        if key not in seen:
            copied = deepcopy(chunk)
            copied_meta = copied.setdefault("metadata", {})
            copied_meta["source_count"] = 1
            copied_meta["sources"] = [_source_ref(metadata)]
            deduped.append(copied)
            seen[key] = copied
            continue

        canonical = seen[key]
        canonical_meta = canonical.setdefault("metadata", {})
        canonical_meta["source_count"] = int(canonical_meta.get("source_count", 1)) + 1
        sources = canonical_meta.setdefault("sources", [])
        sources.append(_source_ref(metadata))

    after = len(deduped)
    removed = before - after
    return deduped, {
        "before": before,
        "after": after,
        "removed": removed,
        "dedup_ratio": (removed / before) if before else 0.0,
    }
