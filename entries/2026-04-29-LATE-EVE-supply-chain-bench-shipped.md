---
date: 2026-04-29T23:15:00+02:00
type: feature-shipped + bench-finding + bug-fix
gitoma_commits: [016a510]
context: ship the bench-supply-chain corpus to E2E-validate G21/G22 + the trivy/semgrep planner-prompt blocks; live-fire on it; surface and fix the semgrep-metrics-off silent-bail bug along the way
verdict: ★★★ all PHASE blocks proven on real adversarial content; gemma actually used the trivy data to upgrade vuln deps; semgrep wire-up bug found + fixed
---

# bench-supply-chain corpus + semgrep bug fix + live-fire validation

The morning's PHASE 1.6 (semgrep) and 1.8 (trivy) shipped with the
silent-fail-open contract — meant to "no-op cleanly when the
substrate has nothing to surface." Today's evening bench found
that interpretation was a coverup: the substrate had PLENTY to
surface on the right corpus, we just hadn't built one. So we did.

Plus, building the corpus surfaced a real bug in PHASE 1.6 that had
been silently degrading every gitoma run since the leg shipped.

## The corpus

A new bench repo with intentional badness across every signal type
PHASE 1.6/1.8 consumes:

- Vulnerable Python deps (`pyproject.toml` + `requirements.txt`
  pinning known-CVE versions of requests / urllib3 / pyyaml /
  pillow / django)
- Vulnerable npm deps (`package.json` pinning lodash / minimist /
  tar / axios at known-CVE versions)
- Credential-shaped fixture file (`config/credentials.env` —
  AWS keys, GitHub PATs, OpenAI keys, RSA private key blocks,
  all randomly generated to match scanner regex patterns
  without colliding with real services' allowlisted EXAMPLE
  values)
- Hardcoded credentials in source (`src/db_connect.py` — DB
  password + AWS access key in module-level constants)
- Dockerfile with 4 misconfigs (`:latest` tag, no `--no-install-
  recommends`, runs as root, ADD instead of COPY)
- K8s deployment with 8 misconfigs (privileged: true,
  runAsUser: 0, no resource limits, hardcoded password env)

Pre-scan totals on the local clone: trivy 98 findings (81 vulns +
5 secrets + 12 misconfigs), semgrep 12 findings. Substantial
enough to E2E-validate the wire-up.

## Bonus: silent-bail bug found in PHASE 1.6

While verifying semgrep would actually surface findings, ran the
local scan that gitoma's PHASE 1.6 wrapper would issue:

```bash
semgrep scan --config auto --quiet --metrics off ...
```

semgrep stderr response: `Cannot create auto config when metrics
are off. Please allow metrics or run with a specific config.`

i.e., `--config auto` (which fetches the language-appropriate
ruleset from semgrep.dev) REQUIRES `--metrics on`. The wrapper
hard-coded `--metrics off` for the privacy posture (no telemetry
to a third party per gitoma run), so every semgrep invocation
since the leg shipped (this morning, commit `e5e34c4`) had been
silently bailing. The "0 findings on every clean repo" we observed
earlier was the symptom — we had been attributing it to "the bench
corpus is clean", but actually semgrep wasn't running at all.

Two-part fix:

1. Default config changed from `auto` to `p/default` — a static
   ruleset that works fine with metrics off. 12 findings on the
   bench-supply-chain corpus on first scan vs 0 with `auto +
   metrics-off`.
2. Cmd builder adapts: when config IS `auto` (operator opted in
   explicitly via `SEMGREP_CONFIG=auto`), the cmd uses `--metrics
   on` so semgrep can do the registry lookup. For any other
   config, keep `--metrics off`.

Two regression tests added covering both paths. Suite
1998 → 2000.

## Live-fire on the corpus

Ran gitoma against the new corpus on minimac1 (gemma-4-e4b-it-mlx)
with the full opt-in stack: G21 + G22 + G23 enabled, all PHASE
blocks active.

PHASE block firings (all three first time on real adversarial
content):

| Phase | Result |
|---|---|
| 1.5 Layer0 | empty namespace on first run; populated to 7 memories on PHASE 8 |
| 1.6 Semgrep | **12 findings (9 ERROR), G21 baseline = 9** |
| 1.7 Stack-shape | matched Django + React L2, 12 canonical paths missing |
| 1.8 Trivy | **180 findings (163 vuln + 5 secret + 12 misconfig), G22 baseline = 112** |

Critic stack live-fires (8 distinct critic types):
- G2 syntax_check, G7 ast_diff, G8 test_regression × 4, G10 schema,
  G15 sibling-config (via critic_panel), G20 config_syntax × 1,
  G23 config_keys × 1
- README-banish dropped 1 subtask
- critic_panel ran 9 reviews, 23 findings total

G21 + G22 specifically did NOT fire — but this is the CORRECT
outcome. Both critics are regression GATES: they fire when a
patch INTRODUCES new findings vs the baseline. In this run the
worker's patches REDUCED the baseline (legitimate dep upgrades),
so the gate stayed quiet. The wire-up is proven (baselines
populate correctly, threading to WorkerAgent works); a forced-
regression test would require an adversarial plan-from-file
("downgrade to vulnerable version") — deferred.

## Output quality — best worker run of the session

The PR opened (#1 on the new repo) shows gemma actively using the
PHASE 1.8 trivy block to make security-driven changes:

- `urllib3==1.24.1` → `urllib3>=1.24.2` (security upgrade with
  conservative version range)
- `pyyaml==5.3` → `pyyaml>=5.3.1` (security upgrade)
- `django==2.2.0` → `django>=2.2.8` (security upgrade)
- `config/credentials.env` reduced -25/+3 lines (most fixture
  secrets removed)
- Plus governance docs (CHANGELOG, CONTRIBUTING)

3 of 5 vulnerable deps actually got bumped — using the bump-target
versions trivy surfaced in the PHASE 1.8 prompt block. This is
exactly the workflow PHASE 1.8 was designed to enable. The
remaining 2 (requests, pillow) the LLM didn't tackle — could be
context budget or attention prioritization.

Cosmetic noise in the diff: `pythonpath = ["."]` →
`pythonpath = ["." ]` (added a space inside the list literal).
Harmless but suggests the worker is occasionally re-emitting
unchanged regions with whitespace drift. Worth noting for a
future tightening.

## Operational note: fabgpt-coder repo permissions

When creating the corpus repo via `gh repo create
fabriziosalmi/...`, the bot account `fabgpt-coder` doesn't
automatically inherit collab access. PHASE 4 (push branch + open
PR) failed with HTTP 403 on the first attempt. Fixed by:
1. `gh api -X PUT .../collaborators/fabgpt-coder -f permission=push`
2. Bot accepted the invite via its own token.

Worth bundling into a one-shot script for future bench-repo
creation; tonight handled manually.

## Stats

3 commits this evening (post-G23):
- `8bf82d2` G13 bulk-shrinkage hardening
- `016a510` semgrep --metrics-off silent-bail fix
- (corpus is its own repo, not a gitoma commit)

Suite: 1998 → **2000** verde. G-stack: 23 critics + Layer-A/B
post-processors + Ψ-lite. PHASE blocks: 1 / 1.5 / 1.6 / 1.7 / 1.8
/ 7 / 8 — all live-fired in production at least once.

Net session day total (2026-04-28 EVE → 2026-04-29 LATE-EVE):
17+ commits, 23 critics, 5 spider legs, 8 PHASE-side hooks, 4 PRs
opened on the bench corpus tonight (the 22 from yesterday all
closed in PR triage), Layer0 namespaces populated for 3 bench
repos.

The bench corpus is now diverse enough to exercise every critic
in the stack:

- bench-blast — BLAST RADIUS / Ψ-Φ / G18+G19 orphan-symbol family
- bench-quality — G15 sibling-config + G10 schema validators
- bench-triggers — orphan trio (G16+G18+G19)
- bench-generation — from-zero generation (5 starting states)
- **bench-supply-chain — G21 + G22 + PHASE 1.6/1.8** (NEW)

Each bench targets a distinct part of the stack. Future bench
adds (Ψ-full, runtime-aware context, formal verification) will
extend this matrix.

Closing observation: the bench-driven methodology continues to
pay off. Today's most valuable finding wasn't a planned feature
— it was the semgrep `--metrics off` silent-bail bug that had
been degrading PHASE 1.6 for 12 hours without anyone noticing,
discovered ONLY because we built a corpus rich enough to expose
the failure mode. Ship → bench → discover → fix.
