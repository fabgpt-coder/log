---
date: 2026-04-27T21:40:47+02:00
repo: fabriziosalmi/gitoma-bench-blast
pr: null
branch: exo-gemma4-e4b-TENSOR-214047
model: mlx-community/gemma-4-e4b-it-4bit
endpoint: exo 2-node minimac (TENSOR sharding via TCP/IP)
subtasks_done: 0
wall_min: 6.1
guards_fired: []
self_review: n/a
verdict: ❌ TENSOR sharding TCP/IP — dead on arrival
---

# Run summary

Same gemma-4-e4b that won single-node (PR #4 100%), now in **Tensor sharding** mode across both minimacs via TCP/IP. PHASE 2 planner timed out at 6 minutes.

## Why the same model passed single-node + failed tensor-sharded

- **Pipeline sharding** (split LAYERS): each forward pass = ONE TCP sync between nodes. Manageable overhead.
- **Tensor sharding** (split TENSORS): each LAYER = N TCP syncs (per matmul). On TCP/IP gigabit, throughput collapses by orders of magnitude.

Even gemma-4-e4b's tiny 5GB footprint can't help when every attention head needs cross-node sync. On a planner-shape prompt of 6-8K tokens, the model never finishes processing before the HTTP client gives up.

## Mitigation that would help

`Interconnect: RDMA (Fast)` instead of `TCP/IP` in the exo dashboard — but that requires Thunderbolt direct connection between the nodes (or RoCE). Not the case here.

## Lesson

**Tensor sharding mode on TCP/IP exo = unusable for gitoma workload, regardless of model size.** Stick to Pipeline mode (or just don't shard at all and run single-node).
