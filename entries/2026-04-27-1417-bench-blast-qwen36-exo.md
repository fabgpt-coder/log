---
date: 2026-04-27T14:17:00+02:00
repo: fabriziosalmi/gitoma-bench-blast
pr: 2
pr_url: https://github.com/fabriziosalmi/gitoma-bench-blast/pull/2
branch: exo-qwen36-35b-a3b-4bit-1418
model: mlx-community/Qwen3.6-35B-A3B-4bit
endpoint: exo cluster (2-node minimac, Pipeline strategy)
subtasks_done: 5/12
wall_min: 17
guards_fired: [G2]
self_review: skipped (model 404)
verdict: partial — exo eviction mid-run
---

# Run summary

First cross-model bench post-exo install. Plan generation was solid (7 task / 14 subtask, valid JSON first try). Execution shipped 5 commits before exo started returning empty/404 responses on the planner-shape prompts.

## Failure mode

Mid-run, the model started returning `JSONDecodeError: Expecting value: line 1 column 1` on multi-file subtasks (T002-S02 docs API, T005-S02 expand tests, T006-S01 CI coverage step). Final subtask + PHASE 5 self-review hit explicit `404 No instance found for model` — exo had silently swapped the model out under memory pressure.

## Root cause

19 GB model on 2 × 16 GB nodes (≈ 120 % of single-node RAM). MLX Pipeline distributes weights but the KV cache balloons on a single primary node under planner-shape prompts (~6-8K tokens). Sized way above the safe envelope.

## Outcome

- 5 commits landed (T001-S01 ruff, T002-S01 docstrings core, T004-S01 .env in .gitignore, T004-S02 SECURITY.md, T005-S01 coverage in pyproject)
- G2 build-manifest guard fired correctly on a pyproject.toml edit not in `file_hint`
- PR #2 opened despite degraded run; review later
