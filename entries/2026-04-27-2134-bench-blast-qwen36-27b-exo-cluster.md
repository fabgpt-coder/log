---
date: 2026-04-27T21:34:39+02:00
repo: fabriziosalmi/gitoma-bench-blast
pr: null
branch: exo-qwen36-27b-213439
model: mlx-community/Qwen3.6-27B-4bit
endpoint: exo 2-node minimac cluster (Pipeline)
subtasks_done: 0
wall_min: 1
guards_fired: []
self_review: n/a
verdict: ❌ exo cluster planner empty response
---

# Run summary

Hypothesis check: 27B-4bit (~14 GB) on 32 GB pooled cluster (≈ 44 % footprint) should respect the "≤ 60 %" rule of thumb. Reality: failed in PHASE 2 with `JSONDecodeError: Expecting value: line 1 column 1` on the first planner call.

## Failure mode

```
LLM planning failed: Unexpected LLM error (JSONDecodeError):
Expecting value: line 1 column 1 (char 0)
```

Same fingerprint as the Qwen3.6-35B exo failure (PR #2). The model returned an empty response under the planner-shape prompt.

## Diagnosis

Even at 44 % cluster footprint, the planner-shape prompt + KV cache distribution across nodes was enough to push exo to drop the response. **The "≤ 60 % footprint" rule from the gemma-single-node win does NOT generalize to multi-node Pipeline mode** — KV cache lives on a single primary node and is the actual bottleneck, not aggregate weights distribution.

## Lesson

Multi-node exo Pipeline mode is risky for any model whose KV cache could plausibly grow past one node's RAM. The bottleneck shifts from weight distribution (works fine) to KV concentration (works poorly).
