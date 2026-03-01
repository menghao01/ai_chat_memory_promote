import re
from typing import Dict, List


def _join_with_blank_line(parts: List[str]) -> str:
    return "\n\n".join([p.strip() for p in parts if p and p.strip()]).strip()


def structural_split(blocks: List[Dict[str, str]]) -> List[str]:
    """
    Build coarse chunks by structural boundaries.

    Current rule: heading blocks (level <= 2) start a new chunk.
    """
    chunks: List[str] = []
    current: List[str] = []

    for block in blocks:
        btype = block.get("type", "")
        text = (block.get("text") or "").strip()
        if not text:
            continue

        if btype == "heading":
            level = int(block.get("level", "2"))
            heading_line = f"{'#' * level} {text}".strip()
            if level <= 2 and current:
                chunks.append(_join_with_blank_line(current))
                current = [heading_line]
            else:
                current.append(heading_line)
            continue

        current.append(text)

    if current:
        chunks.append(_join_with_blank_line(current))

    return [c for c in chunks if c]


def _split_oversized(text: str, target_chars: int, max_chars: int) -> List[str]:
    """Split oversized chunk by paragraph/sentence boundaries, then hard split."""
    if len(text) <= max_chars:
        return [text]

    units = [u.strip() for u in re.split(r"\n{2,}", text) if u.strip()]
    if len(units) <= 1:
        units = [u.strip() for u in re.split(r"(?<=[。！？.!?])\s+", text) if u.strip()]
    if len(units) <= 1:
        units = [text]

    out: List[str] = []
    buf: List[str] = []
    buf_len = 0

    for unit in units:
        if len(unit) > max_chars:
            if buf:
                out.append(_join_with_blank_line(buf))
                buf = []
                buf_len = 0
            start = 0
            while start < len(unit):
                out.append(unit[start : start + target_chars].strip())
                start += target_chars
            continue

        projected = buf_len + (2 if buf else 0) + len(unit)
        if projected > max_chars and buf:
            out.append(_join_with_blank_line(buf))
            buf = [unit]
            buf_len = len(unit)
        else:
            buf.append(unit)
            buf_len = projected

    if buf:
        out.append(_join_with_blank_line(buf))

    return [o for o in out if o]


def _hard_split(text: str, step: int) -> List[str]:
    return [text[i : i + step].strip() for i in range(0, len(text), step) if text[i : i + step].strip()]


def normalize_size(
    chunks: List[str],
    min_chars: int = 120,
    target_chars: int = 500,
    max_chars: int = 1400,
) -> List[str]:
    """
    Normalize chunk sizes into an expected window.
    """
    expanded: List[str] = []
    for chunk in chunks:
        chunk = (chunk or "").strip()
        if not chunk:
            continue
        expanded.extend(_split_oversized(chunk, target_chars=target_chars, max_chars=max_chars))

    normalized: List[str] = []
    pending_small: str = ""

    for chunk in expanded:
        if len(chunk) < min_chars:
            pending_small = f"{pending_small}\n\n{chunk}".strip() if pending_small else chunk
            continue

        if pending_small:
            merged = f"{pending_small}\n\n{chunk}"
            if len(merged) <= max_chars:
                chunk = merged
                pending_small = ""
            else:
                normalized.extend(_hard_split(pending_small, target_chars))
                pending_small = ""

        normalized.append(chunk)

    if pending_small:
        if normalized and len(normalized[-1]) + 2 + len(pending_small) <= max_chars:
            normalized[-1] = f"{normalized[-1]}\n\n{pending_small}".strip()
        else:
            normalized.extend(_hard_split(pending_small, target_chars))

    # Final pass: avoid ultra-small tail chunks when possible.
    final_chunks: List[str] = []
    for chunk in normalized:
        if final_chunks and len(chunk) < 80 and len(final_chunks[-1]) + 2 + len(chunk) <= max_chars:
            final_chunks[-1] = f"{final_chunks[-1]}\n\n{chunk}".strip()
        else:
            final_chunks.append(chunk)

    return [c for c in final_chunks if c]
