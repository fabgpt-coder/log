---
date: 2026-04-27T22:27:51+02:00
repo: fabriziosalmi/gitoma-bench-quality
pr: 1
pr_url: https://github.com/fabriziosalmi/gitoma-bench-quality/pull/1
branch: lms-minimac2-gemma4-222751
model: gemma-4-e4b-it-mlx
endpoint: 100.107.164.29:1234/v1 (LM Studio minimac2, JIT model-load ON)
subtasks_done: 8/12
wall_min: 8
guards_fired: [G2, G8, G10, G15, input_validation]
self_review: 5 findings (2 major, 3 minor)
verdict: ★ parallel-B clean — first PR on bench-quality
---

# Run summary

Second leg of the 2-host parallel bench — gemma on minimac2 LM Studio against bench-quality. Bench-quality is the "config-jungle stress" repo built around G15 sibling-config; this run is also its **very first PR (#1)**.

## Stability

Survived the same workload that crashed minimac1 (see paired entry `2026-04-27-2227a`). Differential = JIT Model Loading enabled in Server API.

## Guards fired

- **G15 sibling-config** — `T001-S02` failed: "Sibling-config reconciliation failed after 2 attempt(s). 2 conflict(s) detected." This is the live-fire confirmation we'd been waiting for since G15 shipped: it WORKS in production, not just in unit tests. Bench-quality vindicated.
- **G2 sensitive-path** — `T004-S01/T004-S02` refused workflow edits.
- **G10 schema** — `T004-S02` config schema check failed after 2 attempts.
- **input_validation** — `T001-S01 .eslintrc.json` patch content was malformed; gitoma rejected at the read-validate boundary.

## Parallelism finding

Wall time for this leg: ~8 min. Wall time for the other leg (minimac1 → bench-blast PR #5): ~8 min. **Total wall in parallel = ~8 min vs ~16 min sequential = ~2× speedup**, no clustering needed, just host-level concurrency over LAN.

## Verdict

The new operational baseline is locked in:
- **gemma-4-e4b-it-mlx** as the worker model
- **2 minimac LM Studio independent endpoints** for parallel runs
- **Just-in-Time Model Loading ON** on every host
- **exo dropped** (Pipeline + 19GB-on-32GB evicted; Tensor on TCP/IP unusable)
