---
date: 2026-04-28T20:34:00+02:00
type: meta-finding
context: gitoma-bench-generation 5-way bench
references:
  - https://github.com/fabriziosalmi/gitoma-bench-generation/pull/1
  - https://github.com/fabriziosalmi/gitoma-bench-generation/pull/2
  - https://github.com/fabriziosalmi/gitoma-bench-generation/pull/3
  - https://github.com/fabriziosalmi/gitoma-bench-generation/pull/4
  - https://github.com/fabriziosalmi/gitoma-bench-generation/pull/5
verdict: ★ structural conclusion — gitoma is a polish agent, not a generation agent
---

# Meta-finding — gitoma cannot generate from zero

The 5-way generation bench delivered an unambiguous structural conclusion that informs every future planning decision.

## Setup recap

- 1 repo, 5 branches, **identical user intent** in shared README ("build a wordcount CLI with these specs")
- 5 different starting states: empty / skeleton / stub-with-TODOs / spec-driven / tests-first
- Same model, same endpoint, same env, same `--reset --no-ci-watch`
- 5 sequential runs against minimac1 LM Studio (gemma-4-e4b-it-mlx)
- Total wall: 28 min

## Result

| Branch | Wall | Tasks | Subtask done | Files in src/ touched | wordcount intent honored? |
|---|---|---|---|---|---|
| start-empty | 6:26 | 4 | 7/9 | 0 | no |
| start-skeleton | 5:19 | 4 | 6/10 | 0 | no |
| start-stub | 5:34 | 4 | 6/8 | 1 (cli.py) | partial — contradicts spec |
| start-spec | 5:19 | 5 | 7/10 | 0 | no |
| start-tests-first | 5:33 | 5 | 6/7 | 0 (test edited cosmetically) | no |

5 PRs opened, 5 PRs are pure boilerplate (CONTRIBUTING/CHANGELOG/SECURITY/Ruff/mypy/CI), only 1 made any attempt at the actual goal — and that attempt explicitly ignores the README spec.

## What this proves about gitoma's planner

1. **README intent is invisible to the planner.** Every branch had the same explicit "build wordcount" instruction. NONE of the 5 plans contains a task like "implement count_text" or "wire main()" or "emit JSON output".

2. **Spec files (JSON Schema, contract markdown) are invisible.** They get treated by the Documentation analyzer as "content to render with MkDocs" — not as specs to implement.

3. **Failing tests with import errors are invisible (worse: misinterpreted).** The planner sees `Test Results: fail` and generates a generic "fix tests" task; the worker interprets it as cosmetic cleanup. The semantic content of the failing tests (the names of the missing symbols) is lost.

4. **Inline TODO markers in code are the ONLY narrative surface that survives.** start-stub was the only branch where `src/` got touched — because there was a Python file with `# TODO: implement` comments. Even there, the worker contradicts the README spec because TODO is a "make it runnable" cue, not a "satisfy the contract" instruction.

5. **The plan→worker file_hint handoff is rigid.** When the actual implementation needed lives in files OUTSIDE the planner's file_hints, those files don't get created. start-tests-first proves it: the failing tests sit in `tests/test_count.py`, the implementation needs to land in `src/wordcount/core.py` and `src/wordcount/cli.py` — but file_hint pointed at the test, so the worker only touched the test.

## Implication for gitoma's positioning

**gitoma is a polish agent for existing code, not a generation agent.** It works well when:
- The repo already contains substantial code (bench-blast, bench-quality, bench-ladder all have real code)
- The "improvements" needed are scaffolding-shaped (Ruff config, CONTRIBUTING.md, SECURITY.md, …)
- The desired output IS a polished version of the input

It does NOT work when:
- The repo is empty or skeleton-only and needs from-zero generation
- The user intent is in README/spec/tests rather than in pre-existing metric failures
- The work needed crosses files in ways the planner's file_hint mechanism doesn't predict

## Action item: `--plan-from-file` is now obligatory, not optional

Path D's option E (CLI flag to load a fixed `tasks.json` instead of calling the planner LLM) is the only way to make gitoma usable for tasks that don't map to its 9 metrics. Concrete shape:

```bash
gitoma run REPO_URL --plan-from-file ./tasks.json --branch X --yes
```

`tasks.json` would match the existing `TaskPlan` dataclass schema: list of `Task` with `id`, `metric`, `priority`, list of `SubTask` with `id`, `action`, `file_hints`, `description`. PHASE 2 LLM call is skipped; everything else (worker, critic stack, PR, self-review) runs as today.

**Effort estimate**: 2-3h (TaskPlan loader + CLI option + skip-PHASE-2 branch in run.py + 1 sample tasks.json + 4-5 unit tests).

**Why this matters beyond Path D**: with `--plan-from-file`, gitoma becomes:
- A reproducible bench tool (same plan → same execution → comparable runs)
- A regression-test harness (handcrafted `tasks.json` to live-fire G16/G18/G19/Test Gen)
- A demo tool (operator-curated plans for showcasing)
- The path to true generation work (operator hand-writes the plan once gitoma can't)

This is the single highest-leverage feature gitoma could ship in a 2-3h window.
