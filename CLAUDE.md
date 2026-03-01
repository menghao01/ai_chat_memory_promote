# Claude Code Guidelines for ai-memory-chat

## Note File Naming Convention

Chat memo files use this format: `chat-memo_{number}_{YYYYMMDD}{HHMMSS}.md`

Example: `chat-memo_1_20260201095705.md`
- `chat-memo_1` - Memo series/identifier
- `20260201` - Date (YYYYMMDD format)
- `095705` - Timestamp (HHMMSS)

**Important:** Notes MUST have `.md` extension to be indexed. `.txt` files are ignored.

## Quick Command Reference

### Update Vector Database (Daily Use)
```bash
./venv/Scripts/python "scripts/incremental_update.py"
```

### Full Database Rebuild (First-time / Format Changes)
```bash
./venv/Scripts/python "scripts/chunk_and_index.py"
```

### Check Model Integrity
```bash
./venv/Scripts/python "scripts/check_model.py"
```

---

## Common Errors & Solutions

### ❌ ModuleNotFoundError: No module named 'chromadb'
**Cause:** Using system Python instead of virtual environment

**Solution:** Always use venv Python:
```bash
# Wrong
python scripts/incremental_update.py

# Correct
./venv/Scripts/python "scripts/incremental_update.py"
```

### ❌ Path syntax errors on Windows
**Cause:** Using backslashes or wrong path format in Bash

**Solution:** Use forward slashes and quote paths:
```bash
# Wrong
python scripts\incremental_update.py
python "scripts\incremental_update.py"

# Correct
./venv/Scripts/python "scripts/incremental_update.py"
```

### ❌ cd command fails
**Cause:** Using Windows-specific cd syntax in bash shell

**Solution:** Run scripts directly from project root (no cd needed):
```bash
# Wrong (Windows cmd syntax)
cd /d D:\ai_memory_chat

# Correct (already in project root)
./venv/Scripts/python "scripts/incremental_update.py"
```

---

## Critical Rules

1. **Always use venv Python** - Dependencies (chromadb, sentence-transformers) are only installed in venv
2. **Use forward slashes** - Bash tool expects Unix-style paths even on Windows
3. **Quote paths** - Prevents parsing issues
4. **Run from project root** - Working directory is already set correctly, no cd needed

---

## Script Selection Guide

| Script | Use When | Effect |
|--------|----------|--------|
| `incremental_update.py` | Adding new notes | Preserves existing data |
| `chunk_and_index.py` | First-time setup / format changes | Deletes and rebuilds |
| `check_model.py` | Troubleshooting model issues | Verifies model only |
