# Near-Duplicate Conservative Assessment (2026-03-01)

- Mode: offline assessment only
- Default behavior changed: no (not enabled)
- Scope: 15 files, raw_chunks=156, after_exact_dedup=123

## Baseline (after exact dedup)
- total=123, small_ratio=0.211, large_ratio=0.163, dup_ratio_proxy=0.000, avg_chars=686.58, gate_passed=True

## Sensitivity
- strict_recommended: sim>=0.97, len_ratio>=0.92, prefix>=0.93, min_chars>=180 -> pairs=1, groups=1, would_remove=1, after_total=122, gate_passed=True
- balanced_candidate: sim>=0.96, len_ratio>=0.9, prefix>=0.92, min_chars>=180 -> pairs=2, groups=2, would_remove=2, after_total=121, gate_passed=True
- wider_candidate: sim>=0.95, len_ratio>=0.88, prefix>=0.9, min_chars>=160 -> pairs=2, groups=2, would_remove=2, after_total=121, gate_passed=True

## Recommendation (Conservative)
- Use `strict_recommended` for future optional trial only: sim>=0.97, len_ratio>=0.92, prefix>=0.93, min_chars>=180
- Estimated impact: remove 1 chunk(s) (0.81%), quality gate still passed
- Sample candidates (top):
  - sim=0.9921, A=chat-memo_1_20260105202854.md#1 <-> B=chat-memo_1_20260107142903.md#1

## Notes
- This report is for offline decision-making only and does not change runtime dedup behavior.
- If enabled in future, keep it as an explicit opt-in flag with telemetry on false-merge risk.
