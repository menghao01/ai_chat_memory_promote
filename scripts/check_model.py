"""
Validate local BAAI/bge-m3 model cache integrity.
"""

from pathlib import Path


REQUIRED_FILES = [
    "config.json",
    "config_sentence_transformers.json",
    "modules.json",
    "pytorch_model.bin",
    "sentence_bert_config.json",
    "sentencepiece.bpe.model",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "1_Pooling/config.json",
]


def main() -> int:
    cache_base = Path.home() / ".cache" / "huggingface" / "hub"
    model_dir = cache_base / "models--BAAI--bge-m3"

    print(f"Check model path: {model_dir}")
    print("=" * 60)

    if not model_dir.exists():
        print("[X] Model directory does not exist.")
        print("Download with your preferred method, for example:")
        print("  huggingface-cli download BAAI/bge-m3")
        return 1

    snapshots_dir = model_dir / "snapshots"
    if not snapshots_dir.exists():
        print("[X] snapshots directory does not exist.")
        return 1

    snapshots = [p for p in snapshots_dir.iterdir() if p.is_dir()]
    if not snapshots:
        print("[X] No snapshot found.")
        return 1

    latest_snapshot = snapshots[0]
    print(f"Snapshot: {latest_snapshot.name}")

    missing_files = []
    total_size_mb = 0.0
    for rel in REQUIRED_FILES:
        file_path = latest_snapshot / rel
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            total_size_mb += size_mb
            print(f"[OK] {rel:40s} ({size_mb:8.1f} MB)")
        else:
            print(f"[--] {rel:40s} [MISSING]")
            missing_files.append(rel)

    print("=" * 60)
    print(f"Total size: {total_size_mb:.1f} MB")

    if missing_files:
        print(f"[X] Model incomplete, missing {len(missing_files)} file(s).")
        print("Re-download model files with your preferred method.")
        return 1

    print("[OK] Model is complete.")
    print(f"Model path: {latest_snapshot}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

