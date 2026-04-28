---
date: 2026-04-28T20:28:05+02:00
repo: fabriziosalmi/gitoma-bench-generation
branch_base: start-tests-first
pr: 5
pr_url: https://github.com/fabriziosalmi/gitoma-bench-generation/pull/5
branch: generation-start-tests-first-20260428-200527
model: gemma-4-e4b-it-mlx
endpoint: 100.98.112.23:1234/v1 (LM Studio minimac1)
plan_tasks: 5
plan_subtasks: 7
subtasks_done: 6/7
wall_min: 5.55
guards_fired: [G2 sensitive-path]
self_review: 5 findings (1 major, 4 minor)
verdict: ❌ TDD attack vector backfired — worker DELETED whitespace from failing tests instead of implementing the missing symbols
---

# Run summary

Leg 5 (final). Starting state: pyproject.toml + `src/wordcount/__init__.py` (empty package) + `tests/test_count.py` containing 6 unit tests that import `wordcount.core.count_text` and `wordcount.cli.main`. **Both symbols don't exist** — tests fail at collection. Hypothesis: failing tests with explicit symbol names might be the strongest possible signal short of explicit task injection.

## Plan generated

```
P1 T001 — Fix failing unit tests (Test Results)
  T001-S01 Analyze failure in tests/test_count.py and correct the underlying code
P2 T002 — CI/CD Pipeline (CI/CD Pipeline)
  T002-S01 Create CI workflow
P3 T004 — Code Quality
  T004-S01 Ruff
  T004-S02 mypy
P4 T005 — Test Suite maturity
  T005-S01 Configure coverage in pyproject
P4 T006 — Project governance
  T006-S01 CONTRIBUTING.md
  T006-S02 CHANGELOG.md
```

## What got committed

```
CHANGELOG.md         +7
CONTRIBUTING.md      +51
pyproject.toml       +10/-1
tests/test_count.py  +2/-8   ← THE KEY DIFF
```

## The test_count.py diff — pure cosmetic vandalism

The "T001-S01 Analyze the failure in tests/test_count.py and correct the underlying code" task was completed by **removing 6 blank lines** from the test file. That's the entire change. The failing imports `from wordcount.core import count_text` and `from wordcount.cli import main as cli_main` are STILL THERE; the symbols still don't exist; the tests still fail at collection.

```diff
 from wordcount.core import count_text
 from wordcount.cli import main as cli_main

-
 def test_count_text_counts_words() -> None:
     ...
-
 def test_count_text_handles_empty() -> None:
     ...
```

## Verdict

**This is the most damning failure of the bench**. The TDD setup is the textbook scenario for "AI knows what to implement because the tests tell it" — and gitoma's worker interpreted "fix failing tests" as a code-style cleanup. Six tests, named precisely after the symbols they need, IGNORED.

The planner saw `Test Results: fail` and emitted a generic "fix failing tests" task. The worker saw the task with file_hint=test_count.py and made cosmetic changes to that file. The pipeline never connected "tests reference wordcount.core" → "create wordcount/core.py with count_text".

**Plan→worker handoff has a fundamental disconnect when the work needed is OUTSIDE the file_hint**. The planner says "fix this test"; the worker only modifies that one file. Implementing the actual missing module would require touching `src/wordcount/core.py` — which wasn't in the plan's file_hints.
