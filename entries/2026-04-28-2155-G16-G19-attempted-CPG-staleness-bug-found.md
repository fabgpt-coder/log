---
date: 2026-04-28T21:55:00+02:00
type: live-fire-attempt + bug-discovery
context: Path D family closure attempt for G16 + G19 (G18 already done in earlier entry)
references:
  - https://github.com/fabriziosalmi/gitoma-bench-triggers
  - entries/2026-04-28-2130-meta-plan-from-file-shipped-G18-live-fired.md
verdict: G16 ✅ fires (technical false-positive but matches design intent); G19 ❌ blocked by CPG-staleness bug
---

# G16 + G19 closure attempt — what we learned

After shipping `--plan-from-file` and live-firing G18, the natural next step was to close the orphan-symbol critic family by writing curated `tasks.json` files for G16 (dead-code-introduction) and G19 (echo-chamber).

## G16 — fires ✅

Hand-curated plan: `loose_ends/api.py` adds a `serialize_event(parsed)` function that the prompt explicitly forbids the worker from calling anywhere.

Run output:
```
✗ T001-S01 failed: G16 dead-code check failed after 2 attempt(s).
  1 new symbol(s) dead.
```

Outcome matches design — but see "CPG staleness bug" below for an honest explanation of WHY it fires.

## G19 — blocked ❌

Hand-curated plan: `feature_x/__init__.py` (previously empty) gets two new functions, `public_a` and `public_b`, where `public_b` body explicitly contains the call `public_a(payload)`. The prompt provided literal Python code verbatim. Re-attempted with two models (gemma-4-e4b-it-mlx and qwen/qwen3-8b) and an ASCII-only constraint after a first emoji/Unicode syntax error.

Final-attempt output:
```
✗ T001-S01 failed: G16 dead-code check failed after 2 attempt(s).
  2 new symbol(s) dead.
```

**G16 fired on BOTH new symbols, including `public_b` which by design CALLS `public_a`.** That's the smoking gun for the bug below.

## The CPG-staleness bug

`gitoma/worker/orphan_check.py` G16 + G19 both query `cpg_index.callers_of(sym.id)` for the new symbol. But `self._cpg_index` is built ONCE before PHASE 2 (in `gitoma/cli/commands/run.py` line ~445) and **never rebuilt after a worker patch lands**. So:

- Patch creates new public symbol `X` in file F
- Worker writes patch to disk
- G16/G19 run: `cpg_index.get_symbol("X")` returns `[]` because the index was built before X existed
- `candidates = []` → `total_callers = 0` (loop over empty)
- G16 fires unconditionally for any new public symbol ever added by `--plan-from-file` (or any subtask) in a file it wasn't already aware of
- G19 cannot fire for self-calling-clique scenarios because the new symbols are never in cpg_index

**Verified empirically**: pre-pasted the exact body of `public_b` containing `result = public_a(payload)` into the CPG indexer manually — `index_text_to_storage` correctly extracts `public_a kind=call` as a ref. So the indexer works; the problem is purely that the WORKER's persistent `_cpg_index` is stale.

## Implications

1. **G18 design is robust** — it uses per-file before/after analysis, no dependency on `cpg_index`. Verified live earlier (`bc18a95`).

2. **G16 fires correctly when the symbol is genuinely dead** — but the firing is for the wrong reason (stale index, not confirmed-no-callers). It would ALSO fire as a false-positive if the patch added a caller in another file. The G16 result on bench-triggers is operationally a true positive but mechanistically a false positive.

3. **G19 cannot fire on patches that introduce both the callee AND its caller in the same patch** — which is the canonical echo-chamber failure mode. This is a real limitation discovered today.

## Backlog item — gitoma fix

`gitoma/worker/worker.py` should rebuild (or incrementally update) `self._cpg_index` after each successful patch apply, before the guards run. Estimated 50-100 LOC change in `worker.py`. Affects:

- G16 — would correctly fire only when no callers exist anywhere AFTER the patch
- G19 — would actually be able to detect echo-chamber patterns
- Ψ-full Φ — caller count would reflect post-patch reality
- Skeletal v1 — signature view would be current

Until this fix lands:
- G18 is fully usable
- G16 is usable but can false-positive (still useful — likely catches more real bugs than it misses)
- G19 is structurally non-fireable on add-the-clique scenarios

## Why the discovery

This bug was invisible to gitoma's metric-driven planner because that planner never landed on the trigger files in the first place. **Only the `--plan-from-file` feature (shipped today) made the bug surface.** The feature paid for itself within 30 minutes of its first use by exposing a structural critic-stack bug that was hiding behind the planner's blindness.

This is exactly why deterministic plan injection matters for testing: a black-box planner hides a thousand bugs behind its own task selection.
