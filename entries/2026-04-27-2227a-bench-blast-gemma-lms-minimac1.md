---
date: 2026-04-27T22:27:51+02:00
repo: fabriziosalmi/gitoma-bench-blast
pr: 5
pr_url: https://github.com/fabriziosalmi/gitoma-bench-blast/pull/5
branch: lms-minimac1-gemma4-222751
model: gemma-4-e4b-it-mlx
endpoint: 100.98.112.23:1234/v1 (LM Studio minimac1, post-exo dropped)
subtasks_done: 4/7
wall_min: 8
guards_fired: [G2, G8, sibling_config_indirect]
self_review: 4 findings (2 major, 2 minor)
verdict: parallel-A clean (PR opened), but channel error after run
---

# Run summary

First leg of a 2-host parallel bench — gemma on minimac1 LM Studio targeting bench-blast, while a sibling run hit minimac2 against bench-quality. exo had been uninstalled earlier; this is the new baseline topology.

## Stability incident — Channel Error mid-run

LM Studio on minimac1 emitted `Channel Error` at 22:35:59 with a `Fatal Python error: Segmentation fault` during prompt processing at 0.0% progress. No Python frame in the traceback → native (MLX/torch) crash.

Loaded extension modules at crash time: `torch._C`, `torch._dynamo.*`, `sentencepiece`, etc. → MLX runtime + torch tokenizer co-resident, accumulated state across many back-to-back calls finally tipped a Metal-side allocator.

**Differential vs the parallel run on minimac2 (which survived)**: minimac2 had **"Just-in-Time Model Loading" ENABLED** in the LM Studio Server API settings; minimac1 had it OFF. JIT off → state persists across requests → segfault after N calls. JIT on → reset per request → fresh state.

## Outcome

PR #5 opened with 4/7 subtasks despite the crash (LM Studio auto-restarts after channel error; gitoma's revert+retry handled the gap).

## Fix going forward

**Mandatory: enable "Just-in-Time Model Loading" on every LM Studio host running gitoma workload.** Pinned in topology memory.
