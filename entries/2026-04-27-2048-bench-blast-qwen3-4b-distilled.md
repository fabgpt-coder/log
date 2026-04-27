---
date: 2026-04-27T20:48:55+02:00
repo: fabriziosalmi/gitoma-bench-blast
pr: null
branch: lmstudio-qwen3-4b-distilled-204855
model: qwen3-4b-qwen3.6-plus-reasoning-distilled
endpoint: localhost:1234/v1 (LM Studio locale, macbook)
subtasks_done: 0
wall_min: 6.25
guards_fired: []
self_review: n/a
verdict: ❌ unusable — reasoning-distilled trap
---

# Run summary

User predicted "saltera tutto" before launching. Confirmed: the model timed out in PHASE 2 planning. No PR opened.

## Failure mode

```
LLM planning failed: APITimeoutError: Request timed out.
```

KV poller during the run showed `status=generating` for the entire 6-minute window — the model NEVER stopped. Wasn't an OOM, wasn't a network issue, wasn't a malformed JSON response. The model was still trying to "finish thinking" when gitoma's HTTP client gave up.

## Why

The "reasoning-distilled" suffix in the model name is the smoking gun. CoT was baked into the weights via fine-tuning. Prompt-side toggles (`/no_think` via `LM_STUDIO_DISABLE_THINKING=true`) are HINTS the model can ignore — and this one does.

Planner prompt (~6-8 K tokens) + thousands of forced-internal reasoning tokens > `max_tokens=4096` budget → never closes the JSON → httpx 5-min timeout.

## Lesson learned

**Skip any model whose name contains `reasoning-distilled` / `r1` / `cot` / `thinking-distilled`** for gitoma workload. Architecture pattern "JSON pulito al primo colpo" is incompatible with bake-in CoT.

## Pinned

This learning has been added to `~/.claude/projects/.../memory/project_bench_2026-04-27_models_4way.md` so future sessions skip these models by name.
