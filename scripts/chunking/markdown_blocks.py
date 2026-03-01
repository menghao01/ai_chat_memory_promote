import re
from typing import Dict, List


Block = Dict[str, str]


HEADING_RE = re.compile(r"^(#{1,6})\s*(.+?)\s*$")
LIST_RE = re.compile(r"^\s*([-*+]|\d+\.)\s+")
DIALOGUE_RE = re.compile(r"^(User|AI|Assistant|Human)\s*:\s*", re.IGNORECASE)


def _flush_paragraph(lines: List[str], blocks: List[Block]) -> None:
    text = "\n".join(lines).strip()
    if text:
        blocks.append({"type": "paragraph", "text": text})
    lines.clear()


def parse_blocks(text: str) -> List[Block]:
    """
    Parse markdown text into coarse structural blocks.

    Block types: heading, list, code, paragraph, dialogue
    """
    blocks: List[Block] = []
    paragraph_lines: List[str] = []
    code_lines: List[str] = []
    in_code = False

    for raw_line in text.splitlines():
        line = raw_line.rstrip("\n")

        # fenced code block
        if line.strip().startswith("```"):
            if in_code:
                code_lines.append(line)
                blocks.append({"type": "code", "text": "\n".join(code_lines)})
                code_lines = []
                in_code = False
            else:
                _flush_paragraph(paragraph_lines, blocks)
                in_code = True
                code_lines.append(line)
            continue

        if in_code:
            code_lines.append(line)
            continue

        # blank line flushes paragraph context
        if not line.strip():
            _flush_paragraph(paragraph_lines, blocks)
            continue

        heading = HEADING_RE.match(line)
        if heading:
            _flush_paragraph(paragraph_lines, blocks)
            level = len(heading.group(1))
            blocks.append(
                {
                    "type": "heading",
                    "text": heading.group(2).strip(),
                    "level": str(level),
                }
            )
            continue

        if LIST_RE.match(line):
            _flush_paragraph(paragraph_lines, blocks)
            blocks.append({"type": "list", "text": line.strip()})
            continue

        if DIALOGUE_RE.match(line):
            _flush_paragraph(paragraph_lines, blocks)
            blocks.append({"type": "dialogue", "text": line.strip()})
            continue

        paragraph_lines.append(line)

    if in_code and code_lines:
        # tolerate unclosed fences as code content
        blocks.append({"type": "code", "text": "\n".join(code_lines)})

    _flush_paragraph(paragraph_lines, blocks)
    return blocks
