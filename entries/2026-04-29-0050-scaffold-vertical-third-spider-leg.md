---
date: 2026-04-29T00:50:00+02:00
type: feature-shipped
gitoma_commits: [83690cc, 3a8e160]
context: gitoma scaffold deterministic vertical (occam-trees integration)
verdict: ★★★ from-zero generation gap closed via third spider leg
---

# `gitoma scaffold` — third deterministic vertical

The from-zero generation gap that yesterday's 5-way bench
exposed (gitoma's LLM planner is metric-blind to user intent)
is now closed via a deterministic upstream tool, not by trying
to make the LLM smarter.

## Pattern (now well-grooved)

`gitoma scaffold <repo> --stack <id> --level <1-10>`:

1. Pre-flight — occam-trees HTTP service reachable + healthy
2. Validate `(stack, level)` early with helpful "did you mean"
   when stack id unknown
3. Resolve canonical file tree via `/v1/resolve` (1000 scaffolds:
   100 stacks × 10 complexity archetypes)
4. Clone target repo
5. Diff: missing files only — additive, never overwrites
6. If 0 missing → "nothing to do" + suggest `gitoma run` polish
7. If `--dry-run` → preview list + exit
8. Otherwise: branch + write stubs + commit + push + PR

Each missing file gets a tiny TODO body matching either its
semantic role (`manifest` → `{}`, `framework-config` → `// TODO`,
`root-layout` → `// TODO` …) OR — when role is unknown — its
extension (.py / .js / .ts / .go / .rs / .rb / .php / .css /
.html / .md / .yml / .toml / .json / .sh). Goal is shape
preservation; the polish-agent fills content afterwards.

## Live-fire validation (0:50)

Two repos created on the fly + scaffolded clean:

| Repo | Stack × Level | Files added | PR |
|------|---------------|-------------|----|
| `gitoma-bench-scaffold-mern` | MERN × L4 (Full-Stack Monolith) | 22 | [#1](https://github.com/fabriziosalmi/gitoma-bench-scaffold-mern/pull/1) |
| `gitoma-bench-scaffold-django` | Django + React × L5 (Multi-tier) | 23 | [#1](https://github.com/fabriziosalmi/gitoma-bench-scaffold-django/pull/1) |

Plus idempotency check: re-running scaffold on the now-merged
django repo correctly says:

```
╭── Nothing to do ──╮
│ ✓ The repo already has all 23 canonical files for Django + React × L5
│ Nothing to scaffold. The polish-agent (`gitoma run`) is the right next step.
╰──────────────────╯
```

So the vertical handles the full lifecycle:
- empty repo → full scaffold
- partial repo → only missing pieces (additive)
- complete repo → silent acknowledgement + handoff to polish-agent

## The bug that wasn't

Initial commit (`83690cc`) had a typo: used `pr.html_url` (the
GitHub API field name, muscle memory from `gh` CLI) instead of
`pr.url` (gitoma's PRInfo dataclass attribute). The PR was
opened correctly — push + create_pr ran cleanly — but the
post-creation console panel crashed. Caught by the very first
live smoke test, fixed in `3a8e160`. Net cost: ~2 minutes,
including the fix commit.

This is exactly what end-to-end live-fire is for. Unit tests
won't catch attribute typos in display-only code paths.

## Three legs in two days

The spider web architecture (per pinned project memory) is now
visibly real:

| Leg | Wraps | Pattern |
|-----|-------|---------|
| `gitoma gitignore` | occam-gitignore-core (Python lib) | direct import |
| Layer0 client + PHASE 1.5/8 | layer0 (Rust gRPC) | thin gRPC wrapper |
| `gitoma scaffold` | occam-trees (Python FastAPI) | thin httpx wrapper |

Same shape every time:
- `gitoma/integrations/<leg>.py` — silent-fail-open client
- (CLI verticals) `gitoma/cli/commands/<leg>.py` mirrors `gitignore.py`
- env-var opt-in (`OCCAM_*_URL`, `LAYER0_GRPC_URL`)
- 5s timeout, no retries
- gitoma proceeds unchanged when leg unavailable
- ~20 unit tests per leg

Adding the next leg (semgrep? license-checker? reuse-tool?)
is now mechanical.

## What this enables next

- **From-zero workflow**: `gitoma scaffold X` → `gitoma run X`
  is now the canonical pattern. Operator picks the
  `(stack, level)`, gitoma builds the shell, polish-agent fills
  it. Closes the bench-generation finding from yesterday.
- **Bench corpus auto-build**: future bench-* repos can start
  from `occam-trees resolve` instead of hand-curated. Scales
  bench creation by 10×.
- **Stack-shape context for the LLM planner** (PHASE 1.7 idea):
  pre-PHASE-2, infer `(stack, level)` from RepoBrief, fetch
  canonical tree, inject into planner prompt as ground truth.
  Reduces "Add CONTRIBUTING.md" boilerplate when CONTRIBUTING.md
  is already canonical-or-irrelevant. Backlog.

## State of the bot at the end of this evening

In ~7 hours of evening (2026-04-28 night → 2026-04-29 0:50am):
- 6 commits: `bc18a95`, `e95f658`, `abf1cff`, `6655038`,
  `ca6562c`, `83690cc`+`3a8e160`
- 3 features shipped: `--plan-from-file`, PHASE 7 diary,
  Layer0 wire-in (1.5+8), `gitoma scaffold`
- 1 bug fixed (CPG-staleness) — orphan-symbol family closed
- 3 spider legs now active in `gitoma/integrations/`
- 4 PRs auto-opened by gitoma during testing
- Suite at 1735/1735

The bot you wake up to tomorrow can now:
1. Read its own past per repo (Layer0)
2. Write its own future per run (Layer0 + diary)
3. Generate a project shell from zero (scaffold)
4. Polish that shell into real code (`gitoma run`)
5. Generate a deterministic .gitignore (gitignore vertical)
6. Be told exactly what tasks to do (--plan-from-file)
7. Narrate everything it did (PHASE 7 diary)

It's not the same agent it was yesterday morning.
