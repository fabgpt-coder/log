---
date: 2026-04-27T21:09:05+02:00
repo: fabriziosalmi/gitoma-bench-blast
pr: 4
pr_url: https://github.com/fabriziosalmi/gitoma-bench-blast/pull/4
branch: exo-gemma4-e4b-210905
model: mlx-community/gemma-4-e4b-it-4bit
endpoint: exo single-node minimac1 (Pipeline strategy, ~5GB on 16GB)
subtasks_done: 7/7
wall_min: 7
guards_fired: []
self_review: 4 findings (1 major, 3 minor)
verdict: ★ 100% completion — best of round
---

# Run summary

Single-node exo (just minimac1) with the small gemma-4-e4b. **3 of 3 tasks done, 7 of 7 subtasks done, zero failures, zero guard activations, 7-minute wall.** Self-review posted 4 findings (1 major + 3 minor) — the PHASE 5 critic also ran cleanly.

## Why this beat everything

- 5 GB model footprint vs 16 GB node = ~30 % single-node RAM pressure → no eviction risk
- Single-node = no inter-node sync overhead (cf. PR #2 19GB on 2× 16GB which evicted; cf. tensor-sharded gemma which timed out for sync overhead)
- gemma-4-e4b's planner output is JSON-clean on first attempt + Layer-B README-banish fired correctly + worker generated valid patches throughout

## Plan generated

```
P1 T001 — Improve Code Quality and Robustness
  T001-S01 Implement Ruff for linting          ✅ commit 165a98e
  T001-S02 Integrate mypy                       ✅ commit cd79d0b
  T001-S03 Add docstrings to public symbols     ✅ commit 074ddf9
P2 T002 — Enhance Test Coverage and Rigor
  T002-S01 Add coverage configuration           ✅ commit eca1476
  T002-S02 Expand test suite                    ✅ commit 27f4fb1
P4 T004 — Establish Project Governance Files
  T004-S01 Add CONTRIBUTING.md                  ✅ commit 85ec7fd
  T004-S02 Add CHANGELOG.md                     ✅ commit 2284c11
```

## Surprise finding

A 5GB model that ships an end-to-end clean PR with valid planner JSON, working Layer-B post-processing, and a self-review that surfaced real bugs is **a serious "small worker" candidate for gitoma**. Pinned for cross-bench validation across more rungs before promoting it past qwen3-8b as the default.
