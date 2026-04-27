---
date: 2026-04-27T20:31:04+02:00
repo: fabriziosalmi/gitoma-bench-blast
pr: 3
pr_url: https://github.com/fabriziosalmi/gitoma-bench-blast/pull/3
branch: lmstudio-qwen3-8b-203104
model: qwen/qwen3-8b
endpoint: localhost:1234/v1 (LM Studio locale, macbook)
subtasks_done: 8/12
wall_min: 10.5
guards_fired: [G2]
self_review: clean
verdict: clean — proven worker baseline
---

# Run summary

qwen3-8b LM Studio local. Direct A/B vs PR #2 (Qwen3.6 exo). 8 of 12 subtasks done in 10:30 wall; the 4 failures were all G2 sensitive-path refusals on `.github/workflows/bench-validate.yml` — the guard worked correctly.

## KV cache behaviour

LM Studio's `lms ps --json` polled every 30s during the run. `status` cycled cleanly `idle → processingPrompt → generating → idle` per subtask. `queued=0` quasi sempre (singolo picco a 1 e gestito istantaneamente). No stress, no eviction, no hang. Opposite of exo behaviour from PR #2.

## Self-review

PHASE 5 ran clean. No findings flagged.

## Verdict

qwen3-8b on LM Studio remains the proven worker baseline. More reliable than the bigger model on exo, AND faster wall (10:30 vs 17 min), AND more subtasks completed (67 % vs 42 %).
