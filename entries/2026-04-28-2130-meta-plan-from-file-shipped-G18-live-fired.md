---
date: 2026-04-28T21:30:48+02:00
type: feature-shipped
gitoma_commit: bc18a95
context: gitoma --plan-from-file feature
verdict: ★★★ Path D structural blocker SOLVED — first ever live G18 firing in a real gitoma run
---

# `--plan-from-file` shipped — G18 live-fired

## What shipped

`gitoma run --plan-from-file path/to/tasks.json` skips PHASE 2 (the LLM planner call) entirely and loads the plan directly from a JSON file matching the existing `TaskPlan.from_dict` schema. Worker, critic stack, PR creation, and self-review all run unchanged. Provenance stamped via `plan.llm_model = "plan-from-file:<filename>"`.

Files: `gitoma/planner/plan_loader.py` (new) + `gitoma/cli/commands/run.py` (CLI option + branch + `_repo_fp = None` default fix). 14 new unit tests in `tests/test_plan_loader.py`. CHANGELOG entry under `[Unreleased]`.

## Why this exists (recap)

The 2026-04-28 5-way generation bench proved the LLM planner is metric-driven and effectively blind to README intent, spec files, and failing tests. For workloads where the operator already knows the tasks (regression tests for individual critics, deterministic verticals, demos, true generation work), routing through the LLM planner adds noise without value.

## The 1-shot live-fire validation

Wrote a hand-curated `tasks.json`:

```json
{
  "tasks": [{
    "id": "T001",
    "title": "Consolidate the four duplicated process_* wrappers",
    "priority": 1,
    "metric": "Code Quality",
    "description": "Inline shared_validator into each callsite ... then DELETE the wrapper functions process_a/b/c/d entirely. Keep shared_validator defined for now.",
    "subtasks": [{
      "id": "T001-S01",
      "title": "Delete process_a/b/c/d wrappers, keep shared_validator",
      "description": "Edit core_helpers.py: remove process_a/b/c/d. Keep shared_validator. After your patch, shared_validator will have ZERO callers in core_helpers.py (this is intentional and is what the G18 critic should detect).",
      "file_hints": ["core_helpers.py"],
      "action": "modify"
    }]
  }]
}
```

Ran:

```bash
GITOMA_G18_ABANDONED=on gitoma run \
  https://github.com/fabriziosalmi/gitoma-bench-triggers \
  --plan-from-file /tmp/bench-triggers-tasks-g18.json \
  --branch triggers-G18-pff-213048 --yes --reset --no-ci-watch
```

## The result

```
Loading hand-curated plan from /tmp/bench-triggers-tasks-g18.json (skipping LLM call)
✓ Loaded 1 task(s) / 1 subtask(s) from /tmp/bench-triggers-tasks-g18.json
...
▶ T001 Consolidate the four duplicated process_* wrappers
  ◌ T001-S01 Delete process_a/b/c/d wrappers, keep shared_validator (gemma-4-e4b-it-mlx generating…)
  ✗ T001-S01 failed: G18 abandoned-helper check failed after 2 attempt(s). 1 symbol(s) abandoned.
```

**The first ever live G18 firing in a real `gitoma run`.** Days of metric-driven planner runs (bench-blast, bench-quality, bench-ladder, bench-triggers v1, bench-generation 5-branch) never landed on a trigger file because the planner chose Ruff/CONTRIBUTING/CHANGELOG/SECURITY/CI boilerplate every time. With `--plan-from-file` the operator pins the task and the worker actually produces the patch shape that exercises the critic.

## What this unlocks

1. **Path D — DONE for G18**. Same pattern works for G16 (write a tasks.json that adds a public function with no callers) and G19 (add self-calling clique in a new file). Will write 2 more curated `tasks.json` files in the bench-triggers repo to land all three guards.

2. **Reproducible benches**. Same plan → same execution shape → comparable runs across model swaps, env tweaks, gitoma commits. The scientific instrument we lacked.

3. **Demos / showcases**. Operator-authored canonical plans for talks, blog posts, regression videos.

4. **True generation work**. The 2026-04-28 finding ("gitoma is a polish agent, not a generation agent") was true given the LLM planner's blindness. With `--plan-from-file`, the operator can write the tree by hand and gitoma still gets all the critic+PR scaffolding for free. This re-positions gitoma from "polish agent" to "polish agent OR plan-executor agent depending on input".

## Bug fixed in passing

Initial impl hit `UnboundLocalError: _repo_fp` in PHASE 3 because the variable was set inside the LLM PHASE 2 block. Initialized to `None` at PHASE 2 entry so the bypass branch doesn't trip downstream. Caught by the very first end-to-end test — which is exactly the value of running E2E immediately rather than trusting unit tests alone.
