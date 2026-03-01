# Scripts

This folder contains core scripts for managing the vector database.

## Core Scripts (Keep These)

### chunk_and_index.py
**Purpose:** Full database rebuild
**Usage:** `python chunk_and_index.py`
**When to use:** First-time setup or when chunking strategies change
**Warning:** Deletes existing database and rebuilds from scratch

### incremental_update.py
**Purpose:** Incremental updates (preserves existing data)
**Usage:** `python incremental_update.py`
**When to use:** Daily - when adding new notes to the database
**Note:** This is the primary script for regular use

### check_model.py
**Purpose:** Verify model integrity
**Usage:** `python check_model.py`
**When to use:** Only when troubleshooting model issues

## Guidelines

**Keep it clean:**
- ✅ Only keep the 3 core scripts listed above
- ❌ Delete temporary/debug scripts immediately after use
- ❌ Do not commit one-time verification scripts

**Why?**
A clean scripts folder prevents confusion about which scripts to use for regular maintenance.
