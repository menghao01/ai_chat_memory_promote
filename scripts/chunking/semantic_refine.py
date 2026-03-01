import re
from typing import List, Set


TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]{1,4}")


def _tokenize(text: str) -> Set[str]:
    return {m.group(0).lower() for m in TOKEN_RE.finditer(text or "")}


def _similarity(left: Set[str], right: Set[str]) -> float:
    if not left or not right:
        return 0.0
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)


def _join(units: List[str]) -> str:
    return "\n\n".join(u.strip() for u in units if u and u.strip()).strip()


def _split_units(text: str) -> List[str]:
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    if len(paragraphs) > 1:
        return paragraphs

    sentences = [s.strip() for s in re.split(r"(?<=[。！？.!?])\s+", text) if s.strip()]
    if len(sentences) > 1:
        return sentences

    return [text.strip()] if text and text.strip() else []


def _hard_split(text: str, step: int) -> List[str]:
    safe_step = max(1, step)
    parts: List[str] = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + safe_step, text_len)
        if end < text_len:
            space_boundary = text.rfind(" ", start, end)
            newline_boundary = text.rfind("\n", start, end)
            boundary = max(space_boundary, newline_boundary)
            if boundary > start + int(safe_step * 0.5):
                end = boundary

        piece = text[start:end].strip()
        if piece:
            parts.append(piece)
        start = end
        while start < text_len and text[start].isspace():
            start += 1

    return parts


def _refine_chunk(
    chunk: str,
    min_chars: int,
    target_chars: int,
    max_chars: int,
    similarity_threshold: float,
) -> List[str]:
    units = _split_units(chunk)
    if not units:
        return []

    out: List[str] = []
    current_units: List[str] = []
    current_tokens: Set[str] = set()
    current_len = 0

    for unit in units:
        unit = unit.strip()
        if not unit:
            continue

        if len(unit) > max_chars:
            if current_units:
                out.append(_join(current_units))
                current_units = []
                current_tokens = set()
                current_len = 0
            out.extend(_hard_split(unit, target_chars))
            continue

        unit_tokens = _tokenize(unit)
        projected_len = current_len + (2 if current_units else 0) + len(unit)

        if current_units and projected_len > max_chars:
            out.append(_join(current_units))
            current_units = [unit]
            current_tokens = set(unit_tokens)
            current_len = len(unit)
            continue

        if current_units and current_len >= min_chars and projected_len >= target_chars:
            sim = _similarity(current_tokens, unit_tokens)
            if sim < similarity_threshold:
                out.append(_join(current_units))
                current_units = [unit]
                current_tokens = set(unit_tokens)
                current_len = len(unit)
                continue

        current_units.append(unit)
        current_tokens = current_tokens | unit_tokens
        current_len = projected_len

    if current_units:
        out.append(_join(current_units))

    return [c for c in out if c]


def apply_semantic_refine(
    chunks: List[str],
    enabled: bool = True,
    only_if_over_max: bool = True,
    min_chars: int = 120,
    target_chars: int = 500,
    max_chars: int = 1400,
    similarity_threshold: float = 0.72,
) -> List[str]:
    """
    Refine chunk boundaries with lightweight lexical similarity.

    Intended to run before size normalization:
    - Keeps non-oversized chunks untouched when only_if_over_max=True
    - Splits oversized chunks on likely topic shifts
    """
    if not enabled:
        return [c for c in chunks if c and c.strip()]

    refined: List[str] = []
    for chunk in chunks:
        text = (chunk or "").strip()
        if not text:
            continue
        if only_if_over_max and len(text) <= max_chars:
            refined.append(text)
            continue
        refined.extend(
            _refine_chunk(
                text,
                min_chars=min_chars,
                target_chars=target_chars,
                max_chars=max_chars,
                similarity_threshold=similarity_threshold,
            )
        )
    return [c for c in refined if c]
