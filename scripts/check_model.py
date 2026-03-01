"""
检查 BAAI/bge-m3 模型缓存是否完整
"""
import os
from pathlib import Path

# HuggingFace 缓存路径
cache_base = Path.home() / ".cache" / "huggingface" / "hub"
model_dir = cache_base / "models--BAAI--bge-m3"

# 必需的文件列表
required_files = [
    "config.json",
    "config_sentence_transformers.json",
    "modules.json",
    "pytorch_model.bin",
    "sentence_bert_config.json",
    "sentencepiece.bpe.model",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "1_Pooling/config.json"
]

print(f"Check model path: {model_dir}")
print("=" * 60)

if not model_dir.exists():
    print("[X] Model directory does not exist!")
    print("\nNeed to download model. Please run:")
    print("  python scripts/download_model.py")
    exit(1)

# 查找 snapshot 目录
snapshots_dir = model_dir / "snapshots"
if not snapshots_dir.exists():
    print("[X] snapshots directory does not exist!")
    exit(1)

# 获取最新的 snapshot
snapshots = list(snapshots_dir.iterdir())
if not snapshots:
    print("[X] No snapshot found!")
    exit(1)

latest_snapshot = snapshots[0]
print(f"Snapshot: {latest_snapshot.name}")

# 检查必需文件
missing_files = []
total_size = 0
for file in required_files:
    file_path = latest_snapshot / file
    if file_path.exists():
        size = file_path.stat().st_size / (1024 * 1024)  # MB
        total_size += size
        print(f"[OK] {file:40s} ({size:8.1f} MB)")
    else:
        print(f"[--] {file:40s} [MISSING]")
        missing_files.append(file)

print("=" * 60)
print(f"Total size: {total_size:.1f} MB")

if missing_files:
    print(f"\n[X] Model incomplete, missing {len(missing_files)} files!")
    print("\nNeed to re-download. Please run:")
    print("  python scripts/download_model.py")
else:
    print("\n[OK] Model is complete!")
    print(f"Model path: {latest_snapshot}")
    print("\nNext step: modify scripts to use local model")
