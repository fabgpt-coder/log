---
date: 2026-04-29T11:00:00+02:00
type: bench-finding
gitoma_commits: [89f7bf3]
context: live-fire validation of the 6 features shipped this morning — surfaced a REAL gap and fixed it
verdict: ★★★ honest bench, real gap, real fix — methodology > shipping streak
---

# Live-fire bench → RepoBrief framework extraction

After shipping 6 features in 4h ("shipping streak") I needed honest
validation that they actually fire on real input — not just on
mocked unit tests. Per the user's bench-ladder methodology
(`feedback_user_internalised_qa_methodology.md`): "never claim
victory without immutable measurement".

## Setup

Cost ~5 min:
- `brew install semgrep trivy` → semgrep 1.157.0, trivy 0.70.0
- A local harness script (~130 lines) that imports the spider-leg
  clients, runs each scan against a target repo, computes the
  G21+G22 baselines, prints a structured summary

Three target repos picked for stack diversity. Naming them
generically here (the repo names + their specific findings stay
private, since some are operator-internal or client work):
- **Repo A** — Python (gitoma itself, sanity check)
- **Repo B** — Rust (HTTP service built on hyper directly)
- **Repo C** — Python+JavaScript (multimedia tool, mixed deps)

## Results — first run (before fix)

| Repo | PHASE 1.6 | PHASE 1.7 | PHASE 1.8 |
|---|---|---|---|
| A (Python) | ✓ 0 findings (0.4s) | ✗ SKIP | ✓ findings (slow first run) |
| B (Rust) | ✓ 0 findings (0.3s) | ✗ SKIP | ✓ findings (15s) |
| C (Py+JS) | ✓ 0 findings (0.4s) | ✗ SKIP | ✓ 0 findings (10s) |

**Trivy caught real issues** on Repo B (multiple categories: an
outdated lib with a known CVE, a couple of TLS test fixture files
trivy classified as private-key leaks, and a dozen Dockerfile
misconfigs). On Repo A trivy flagged a couple of credential-shaped
strings in operator-config files — both legitimate operator-side
secrets, but the detection itself proves G22 would catch a real
hardcoded-token regression in production patches.

PHASE 1.6 semgrep was clean across all 3 — well-maintained
codebases. Reasonable but doesn't tell us much about the feature's
value on adversarial input. Worth a future adversarial bench
(`b2v`-style intentionally-broken repo).

## The gap that mattered

**PHASE 1.7 SKIPPED on 3/3 real repos.**

Root cause: `RepoBrief.stack` was emitting language-only signals:
- Repo A → `['Python']` (1 component)
- Repo B → `['Rust']` (1 component)
- Repo C → `['Python', 'JavaScript']` (2 components, but no
  catalog stack has BOTH as components — they're either Python+web
  framework or JS+web framework, not "raw Python + raw JS")

The PHASE 1.7 stack inference threshold is 2 matches against
occam-trees catalog stacks (which key on framework names like
"FastAPI", "React", "Tokio"). Single-language signals can't reach
the threshold. The feature was DOA in production.

This is the kind of gap that synthetic unit tests don't catch — the
feature works perfectly on mocked input that happens to have the
right shape. The bench-ladder discipline forces honest discovery.

## The fix (~80 LOC)

Extended each manifest extractor in
`gitoma/context/repo_brief.py` to walk the dependency list and
append canonical framework tags:

```python
_PY_FRAMEWORKS = {
    "fastapi": "FastAPI", "django": "Django", "flask": "Flask",
    "langchain": "LangChain", "pytorch": "PyTorch",
    "tensorflow": "TensorFlow", "numpy": "NumPy", ...  # 22 total
}
_RUST_FRAMEWORKS = {
    "tokio": "Tokio", "actix": "Actix", "rocket": "Rocket",
    "hyper": "Hyper", "axum": "Axum", "tauri": "Tauri", ...  # 13
}
_JS_FRAMEWORKS = {
    "react": "React", "vue": "Vue.js", "next": "Next.js",
    "express": "Express.js", "tailwindcss": "Tailwind CSS", ...  # 22
}
```

Two normalisation tricks worth flagging:
- **PEP-508 dep strings**: `fastapi[all] (>=0.100,<1.0)` strips
  extras + version specifier + env marker → `fastapi`
- **JS @scope/pkg deps**: `@nestjs/core` tries BOTH the scope AND
  the package name (NestJS lookup is keyed on `nestjs`, but
  `@types/react` is keyed on `react`). Cheap to try both.

## Results — re-run (after fix)

| Repo | New stack signals | PHASE 1.7 |
|---|---|---|
| A | language + web framework | ✓ matches an appropriate catalog stack (2/4 components) |
| C | language + numerics lib + secondary language | ⚠️ matches a numerics-shaped catalog stack (math correct, semantically a stretch) |
| B | language + 4 raw HTTP/runtime libs | ✗ STILL SKIP |

**2/3 firing** vs 0/3 before. Net unblock.

## What Repo B teaches us

Repo B has 5 stack components after the fix but PHASE 1.7 still
skips because the occam-trees catalog has NO stack matching the
combination of raw HTTP/runtime libraries this repo uses without an
associated web-framework component.

Repo B is "raw" infrastructure (uses HTTP libs directly, no
framework wrapper). The catalog assumes you're building app-shaped
projects, not infrastructure. This is an UPSTREAM occam-trees
catalog gap, not gitoma's problem to solve.

Backlog item for occam-trees: add stacks for raw-library
infrastructure shapes (no framework wrapper). Tracking it as
occam-trees evolution, not blocking gitoma.

## What Repo C teaches us

Repo C is a multimedia tool that uses a numerics lib + Python +
some JS for the web UI. PHASE 1.7 inference matched it as a
numerics+web stack because both share the language + numerics
component. The match math is correct (2 components in common), but
semantically the matched stack isn't the right shape.

This false-positive risk is real but acceptable for v1:
- The matched scaffold's missing-paths delta is shown as
  "additive-only hints" — the planner SHOULD evaluate them against
  the report metrics before emitting subtasks
- Worst case: planner sees "you're missing some web-framework
  scaffolding" and ignores it because the repo's metrics don't
  reference that framework

A future tightening: weight match by RANK (popular stacks get a
bonus only if user's signals strongly agree). Defer until we see
this false-positive cause real problems in a live LLM run.

## Methodology — what this bench proved

The pattern of "ship → bench → discover real gap → fix it" closes
the loop on the morning's shipping streak. Without this validation,
PHASE 1.7 would have shipped to production with a 0% firing rate —
a feature that exists but never runs. The bench cost ~30 min total
(install + harness + 3 runs + fix + re-validate + commit) — cheap
relative to the value of catching the gap before any user noticed.

This is exactly what the user's bench-ladder discipline guards
against: shipping that LOOKS like it works (1930 unit tests pass!)
but DOESN'T actually fire (0/3 on real input).

## Stats

14 commits this session (2026-04-28 evening → 2026-04-29 AM7):

| # | Commit | Cosa |
|---|--------|------|
| 1-13 | (the 13 from earlier diary entries) | … |
| 14 | **`89f7bf3`** | **bench-driven RepoBrief framework extraction** |

Suite: 1930 → **1938** verde (+8 framework-extraction tests).

Trivy as the 5th leg paid off immediately — the new critic surface
is now validated on real input. Specific findings + repo identities
intentionally redacted from this entry; details stay in the
operator's local trace JSONL.
