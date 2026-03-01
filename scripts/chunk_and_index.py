"""
Chunk and index notes for AI Partner Chat skill.

This script implements a HYBRID chunking approach:
1. Known formats (chat-memo, topic-notes, markdown) use pre-written strategies
2. Unknown formats fall back to standard markdown chunking
3. Future: AI dynamic analysis for truly unknown formats

Supported formats:
- Chat Memo: AI conversation exports (DeepSeek, Claude, ChatGPT)
- Topic Notes: #topic style notes
- Standard Markdown: Documents with ## headers
"""

import sys
from pathlib import Path
from typing import List, Dict
import re

# Import provided utilities
sys.path.insert(0, str(Path(__file__).parent.parent / ".claude/skills/ai-partner-chat/scripts"))

from chunk_schema import Chunk, validate_chunk

try:
    from scripts.chunking.deduplicate import deduplicate_exact_chunks
    from scripts.chunking.markdown_blocks import parse_blocks
    from scripts.chunking.quality_gate import evaluate as evaluate_quality_gate
    from scripts.chunking.quality_gate import summarize_chunks
    from scripts.chunking.semantic_refine import apply_semantic_refine
    from scripts.chunking.splitters import structural_split, normalize_size
except ImportError:
    # Script-mode fallback when running from ./scripts directory.
    from chunking.deduplicate import deduplicate_exact_chunks
    from chunking.markdown_blocks import parse_blocks
    from chunking.quality_gate import evaluate as evaluate_quality_gate
    from chunking.quality_gate import summarize_chunks
    from chunking.semantic_refine import apply_semantic_refine
    from chunking.splitters import structural_split, normalize_size


def extract_date_from_filename(filename: str) -> str | None:
    """Extract date from filename like 'chat-memo_1_20260105202854.md' or '25.12.02.md'."""
    # Try chat-memo pattern: YYYYMMDD
    chat_memo_match = re.search(r'(\d{8})', filename)
    if chat_memo_match:
        date_str = chat_memo_match.group(1)
        if len(date_str) == 8:
            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

    # Try YY.MM.DD pattern
    dot_match = re.match(r'(\d{2})\.(\d{2})\.(\d{2})', filename)
    if dot_match:
        yy, mm, dd = dot_match.groups()
        # Assume 20XX for years < 50, otherwise 19XX
        century = "20" if int(yy) < 50 else "19"
        return f"{century}{yy}-{mm}-{dd}"

    # Try daily-log pattern: daily-log-YYYY-MM-DD
    daily_log_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    if daily_log_match:
        return daily_log_match.group(1)

    return None


def chunk_chat_memo(filepath: str, content: str, filename: str, filepath_str: str) -> List[Chunk]:
    """
    Chunk chat-memo format files.
    Format: Contains Title, URL, Platform, Created, Messages, then User/AI dialogue.
    """
    chunks = []
    date = extract_date_from_filename(filename)

    # Split by the separator line
    sections = re.split(r'=+', content)

    for section_idx, section in enumerate(sections):
        if not section.strip():
            continue

        # Extract title from the section
        title_match = re.search(r'Title:\s*(.+?)(?:\n|$)', section)
        title = title_match.group(1).strip() if title_match else f"Conversation {section_idx + 1}"

        # Split into message pairs (User + AI)
        messages = re.split(r'User:\s*\[\d{4}-\d{2}-\d{2}[\s:\d]+\]', section)

        for msg_idx, message in enumerate(messages):
            if not message.strip() or message.strip() == '\n':
                continue

            # Split AI response
            ai_parts = re.split(r'AI:\s*\[\d{4}-\d{2}-\d{2}[\s:\d]+\]', message)

            # Get user message
            user_msg = ai_parts[0].strip()
            if user_msg:
                chunks.append({
                    'content': f"[User问] {user_msg}",
                    'metadata': {
                        'filename': filename,
                        'filepath': filepath_str,
                        'chunk_id': len(chunks),
                        'chunk_type': 'user_message',
                        'date': date,
                        'title': title
                    }
                })

            # Get AI response if exists
            if len(ai_parts) > 1 and ai_parts[1].strip():
                ai_msg = ai_parts[1].strip()
                chunks.append({
                    'content': f"[AI答] {ai_msg}",
                    'metadata': {
                        'filename': filename,
                        'filepath': filepath_str,
                        'chunk_id': len(chunks),
                        'chunk_type': 'ai_response',
                        'date': date,
                        'title': title
                    }
                })

    return chunks


def chunk_markdown_document(
    filepath: str,
    content: str,
    filename: str,
    filepath_str: str,
    semantic_refine_enabled: bool = True,
) -> List[Chunk]:
    """
    Chunk standard markdown documents with headers.
    Use structural split and size normalization to improve retrieval quality.
    """
    chunks: List[Chunk] = []
    blocks = parse_blocks(content)
    coarse_chunks = structural_split(blocks)
    refined_chunks = apply_semantic_refine(
        coarse_chunks,
        enabled=semantic_refine_enabled,
        only_if_over_max=True,
        min_chars=120,
        target_chars=500,
        max_chars=1400,
        similarity_threshold=0.72,
    )
    final_chunks = normalize_size(
        refined_chunks,
        min_chars=120,
        target_chars=500,
        max_chars=1400,
    )

    for text in final_chunks:
        first_line = text.splitlines()[0].strip() if text.splitlines() else ""
        title_match = re.match(r'^##+\s*(.+)$', first_line)
        metadata = {
            'filename': filename,
            'filepath': filepath_str,
            'chunk_id': len(chunks),
            'chunk_type': 'section' if title_match else 'paragraph',
        }
        if title_match:
            metadata['title'] = title_match.group(1).strip()

        chunks.append({
            'content': text,
            'metadata': metadata
        })

    return chunks


def chunk_topic_notes(filepath: str, content: str, filename: str, filepath_str: str) -> List[Chunk]:
    """
    Chunk notes with # topic markers (like 25.12.02.md).
    Each # starts a new topic.
    """
    chunks = []

    # Split by # at the start of a line (but not ##)
    topics = re.split(r'^#(?!\s)', content, flags=re.MULTILINE)

    for topic_idx, topic in enumerate(topics):
        topic = topic.strip()
        if not topic:
            continue

        # Extract the first line as title
        lines = topic.split('\n', 1)
        title = lines[0].strip() if lines else f"Topic {topic_idx + 1}"
        topic_content = lines[1] if len(lines) > 1 else ""

        full_content = f"#{title}\n{topic_content}" if topic_content else f"#{title}"

        chunks.append({
            'content': full_content,
            'metadata': {
                'filename': filename,
                'filepath': filepath_str,
                'chunk_id': len(chunks),
                'chunk_type': 'topic',
                'title': title
            }
        })

    return chunks


def chunk_note_file(filepath: str) -> List[Chunk]:
    """
    Analyze file format and generate appropriate chunks.

    HYBRID APPROACH:
    1. Detect format by checking content patterns
    2. Apply pre-written strategy for known formats
    3. Fall back to markdown chunking for unknown formats
    4. Future: AI dynamic analysis for complex unknown formats

    Each chunk must conform to chunk_schema.Chunk format:
    {
        'content': 'text',
        'metadata': {
            'filename': 'file.md',
            'filepath': '/path/to/file',
            'chunk_id': 0,
            'chunk_type': 'your_label'
        }
    }
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        filename = Path(filepath).name
        filepath_str = str(Path(filepath).absolute())

        # Detect format by checking content patterns
        is_chat_memo = (
            'Chat Memo' in content[:200] or
            'Total Conversations:' in content[:500] or
            re.search(r'Platform:\s*(DeepSeek|ChatGPT|Claude)', content[:500])
        )

        is_topic_notes = re.search(r'^#[^\s#]', content, flags=re.MULTILINE) is not None

        # Choose chunking strategy (HYBRID APPROACH)
        if is_chat_memo:
            # Known format: AI conversation exports
            chunks = chunk_chat_memo(filepath, content, filename, filepath_str)
        elif is_topic_notes:
            # Known format: #topic style notes
            chunks = chunk_topic_notes(filepath, content, filename, filepath_str)
        else:
            # Unknown format: Use default markdown chunking
            # Future enhancement: Call AI for dynamic analysis
            chunks = chunk_markdown_document(filepath, content, filename, filepath_str)

        # Validate chunks
        valid_chunks = []
        for chunk in chunks:
            if validate_chunk(chunk):
                valid_chunks.append(chunk)
            else:
                print(f"  WARNING: Invalid chunk in {filename}, skipping")

        return valid_chunks

    except Exception as e:
        print(f"  ERROR processing {filepath}: {e}")
        return []


def main():
    """Main function to initialize vector database."""
    print("Initializing AI Partner Chat vector database...")
    from vector_indexer import VectorIndexer

    # Initialize vector database
    indexer = VectorIndexer(db_path="./vector_db")
    indexer.initialize_db()

    # Process all note files
    all_chunks = []
    notes_dir = Path("./notes")

    if not notes_dir.exists():
        print(f"ERROR: Notes directory not found: {notes_dir}")
        return

    note_files = list(notes_dir.glob("**/*.md")) + list(notes_dir.glob("**/*.txt"))

    if not note_files:
        print("INFO: No note files found in ./notes/ directory")
        return

    print(f"Found {len(note_files)} note files")

    for note_file in note_files:
        if note_file.is_file():
            print(f"  Processing: {note_file.name}")
            chunks = chunk_note_file(str(note_file))
            print(f"    Generated {len(chunks)} chunks")
            all_chunks.extend(chunks)

    if not all_chunks:
        print("ERROR: No valid chunks generated")
        return

    all_chunks, dedup_stats = deduplicate_exact_chunks(all_chunks)
    if dedup_stats["removed"] > 0:
        print(
            "\nDedup Summary:"
            f" before={dedup_stats['before']}, after={dedup_stats['after']},"
            f" removed={dedup_stats['removed']},"
            f" ratio={dedup_stats['dedup_ratio']:.3f}"
        )

    stats = summarize_chunks(all_chunks, min_chars=120, max_chars=1400)
    gate = evaluate_quality_gate(stats)
    print("\nChunk Quality Report:")
    print(
        f"  total={stats['total_chunks']}, small={stats['small_chunks']}, "
        f"large={stats['large_chunks']}, avg={stats['avg_chars']:.1f}, "
        f"dup_ratio={stats['dup_ratio_proxy']:.3f}"
    )
    if not gate["passed"]:
        print(f"ERROR: Quality gate failed: {', '.join(gate['failed_rules'])}")
        return

    print(f"\nTotal chunks to index: {len(all_chunks)}")

    # Index chunks
    indexer.index_chunks(all_chunks)

    print("\nSUCCESS: Vector database initialization complete!")
    print(f"   Database location: {Path('./vector_db').absolute()}")
    print(f"   Total chunks indexed: {len(all_chunks)}")


if __name__ == "__main__":
    main()
