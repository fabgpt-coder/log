#!/usr/bin/env python3
"""Build README.md and pages/ from entries/ frontmatter.

Source of truth: YAML frontmatter at the top of each entries/*.md file.
Output: README.md (dashboard + latest runs) and pages/PAGE_NNN.md (archive).

Run from repo root:  python3 scripts/build_readme.py
"""

from __future__ import annotations

import datetime as dt
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
ENTRIES_DIR = ROOT / "entries"
PAGES_DIR = ROOT / "pages"
README = ROOT / "README.md"

PAGE_SIZE = 25  # rows per page (README also shows PAGE_SIZE)
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)

# Verdict normalization buckets.
VERDICT_CLEAN = "clean"
VERDICT_PARTIAL = "partial"
VERDICT_FAILED = "failed"
VERDICT_MILESTONE = "milestone"
VERDICT_OTHER = "other"

VERDICT_EMOJI = {
    VERDICT_CLEAN: "✅",
    VERDICT_PARTIAL: "◐",
    VERDICT_FAILED: "❌",
    VERDICT_MILESTONE: "★",
    VERDICT_OTHER: "·",
}


@dataclass
class Entry:
    path: Path
    date: dt.datetime
    fm: dict
    body_first_line: str = ""

    # Derived
    repo: str = ""
    repo_short: str = ""
    pr: str = ""
    pr_url: str = ""
    model: str = ""
    endpoint: str = ""
    subtasks_done: str = ""
    subtasks_num: int = 0
    subtasks_den: int = 0
    guards: list = field(default_factory=list)
    verdict_raw: str = ""
    verdict_class: str = VERDICT_OTHER
    is_run: bool = False
    is_milestone: bool = False


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_entry(path: Path) -> Entry | None:
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        print(f"warn: yaml error in {path.name}: {e}", file=sys.stderr)
        return None
    if not isinstance(fm, dict):
        return None

    date = _parse_date(fm.get("date"), path.name)
    if date is None:
        return None

    body = text[m.end():].strip()
    first_heading = ""
    for line in body.splitlines():
        s = line.strip()
        if s and not s.startswith("---"):
            first_heading = s.lstrip("# ").strip()
            break

    e = Entry(path=path, date=date, fm=fm, body_first_line=first_heading)
    e.repo = str(fm.get("repo") or "").strip()
    e.repo_short = e.repo.split("/", 1)[1] if "/" in e.repo else e.repo
    pr_raw = fm.get("pr")
    e.pr = str(pr_raw) if pr_raw not in (None, "") else ""
    e.pr_url = str(fm.get("pr_url") or "").strip()
    e.model = _short_model(str(fm.get("model") or "").strip())
    e.endpoint = str(fm.get("endpoint") or "").strip()
    e.subtasks_done = str(fm.get("subtasks_done") or "").strip()
    e.subtasks_num, e.subtasks_den = _parse_subtasks(e.subtasks_done)
    e.guards = _parse_guards(fm.get("guards_fired"))
    e.verdict_raw = str(fm.get("verdict") or "").strip()
    e.verdict_class = _classify_verdict(e.verdict_raw, fm.get("type"))

    # Any entry with a `type:` field is operator-written narrative (milestone,
    # finding, summary). Run entries never set `type`.
    e.is_milestone = bool(str(fm.get("type") or "").strip())
    # A run = bot actually executed against a repo. PR is optional (failed runs
    # are the most valuable entries to surface). Milestones never count as runs.
    e.is_run = (not e.is_milestone) and bool(e.repo or e.model or e.pr_url)
    return e


def _parse_date(raw, fallback_name: str) -> dt.datetime | None:
    if isinstance(raw, dt.datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=dt.timezone.utc)
    if isinstance(raw, dt.date):
        return dt.datetime.combine(raw, dt.time(0, 0), tzinfo=dt.timezone.utc)
    if isinstance(raw, str) and raw:
        s = raw.replace("Z", "+00:00")
        try:
            d = dt.datetime.fromisoformat(s)
            return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)
        except ValueError:
            pass
    # Fallback: derive from filename "YYYY-MM-DD-HHMM-..."
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})-(\d{2})(\d{2})", fallback_name)
    if m:
        y, mo, d, h, mi = map(int, m.groups())
        return dt.datetime(y, mo, d, h, mi, tzinfo=dt.timezone.utc)
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", fallback_name)
    if m:
        y, mo, d = map(int, m.groups())
        return dt.datetime(y, mo, d, tzinfo=dt.timezone.utc)
    return None


def _short_model(s: str) -> str:
    if not s:
        return ""
    return s.split("/")[-1]


def _parse_subtasks(s: str) -> tuple[int, int]:
    m = re.match(r"\s*(\d+)\s*/\s*(\d+)", s)
    if m:
        return int(m.group(1)), int(m.group(2))
    return 0, 0


def _parse_guards(raw) -> list:
    if raw is None:
        return []
    if isinstance(raw, str):
        # "[G2]" or "G2, G3"
        stripped = raw.strip().strip("[]")
        if not stripped:
            return []
        return [x.strip() for x in stripped.split(",") if x.strip()]
    if isinstance(raw, list):
        out = []
        for x in raw:
            if isinstance(x, str) and x.strip():
                out.append(x.strip())
        return out
    return []


def _classify_verdict(raw: str, entry_type) -> str:
    if entry_type in ("meta-finding", "feature-shipped"):
        return VERDICT_MILESTONE
    if not raw:
        return VERDICT_OTHER
    low = raw.lower()
    if "★" in raw:
        return VERDICT_MILESTONE
    if low.startswith("clean") or "clean baseline" in low or "clean win" in low:
        return VERDICT_CLEAN
    if "❌" in raw or low.startswith("unusable") or low.startswith("dead"):
        return VERDICT_FAILED
    if low.startswith("partial") or "partial" in low.split("—")[0]:
        return VERDICT_PARTIAL
    if low.startswith("pr opened") or "pr opened" in low:
        return VERDICT_PARTIAL
    if "⚠" in raw:
        return VERDICT_PARTIAL
    return VERDICT_OTHER


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

def _fmt_when(d: dt.datetime) -> str:
    return d.strftime("%Y-%m-%d %H:%M")


_LEADING_DECOR = re.compile(r"^(?:[★✅◐❌·⚠️\s]+)")


def _short_verdict(e: Entry) -> str:
    cls = e.verdict_class
    emoji = VERDICT_EMOJI[cls]
    text = re.sub(r"\s+", " ", e.verdict_raw).strip()
    # Strip any leading verdict glyphs to avoid stacking with our emoji prefix.
    text = _LEADING_DECOR.sub("", text).strip()
    if not text:
        text = cls
    if len(text) > 64:
        text = text[:61].rstrip() + "…"
    text = text.replace("|", "\\|")
    return f"{emoji} {text}"


def _guards_cell(e: Entry) -> str:
    if not e.guards:
        return "—"
    if len(e.guards) == 1:
        return f"`{e.guards[0]}`"
    return f"`{e.guards[0]}` +{len(e.guards) - 1}"


def _pr_cell(e: Entry) -> str:
    if e.pr_url and e.pr:
        return f"[#{e.pr}]({e.pr_url})"
    if e.pr_url:
        return f"[link]({e.pr_url})"
    if e.pr:
        return f"#{e.pr}"
    return "—"


def _model_cell(e: Entry) -> str:
    if not e.model:
        return "—"
    m = e.model.replace("|", "\\|")
    return f"`{m}`"


def _entry_link(e: Entry, from_pages: bool) -> str:
    rel = f"../entries/{e.path.name}" if from_pages else f"entries/{e.path.name}"
    return f"[entry]({rel})"


def render_runs_table(rows: list[Entry], from_pages: bool = False) -> str:
    head = (
        "| When | Repo | PR | Model | Subs | Guards | Verdict | · |\n"
        "|---|---|---|---|---|---|---|---|\n"
    )
    lines = []
    for e in rows:
        subs = e.subtasks_done or "—"
        repo = (e.repo_short or "—").replace("|", "\\|")
        lines.append(
            f"| {_fmt_when(e.date)} | `{repo}` | {_pr_cell(e)} | {_model_cell(e)} "
            f"| {subs} | {_guards_cell(e)} | {_short_verdict(e)} | {_entry_link(e, from_pages)} |"
        )
    return head + "\n".join(lines) + ("\n" if lines else "")


def render_milestones_table(rows: list[Entry]) -> str:
    head = (
        "| When | What | Verdict | · |\n"
        "|---|---|---|---|\n"
    )
    lines = []
    for e in rows:
        what = e.body_first_line or e.path.stem
        what = re.sub(r"\s+", " ", what).strip()
        if len(what) > 80:
            what = what[:77].rstrip() + "…"
        what = what.replace("|", "\\|")
        lines.append(
            f"| {_fmt_when(e.date)} | {what} | {_short_verdict(e)} | {_entry_link(e, False)} |"
        )
    return head + "\n".join(lines) + ("\n" if lines else "")


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def compute_stats(runs: list[Entry], milestones: list[Entry]) -> dict:
    verdict_counts = Counter(e.verdict_class for e in runs)
    subs_num = sum(e.subtasks_num for e in runs)
    subs_den = sum(e.subtasks_den for e in runs)
    subs_pct = (100 * subs_num / subs_den) if subs_den else 0

    guard_counter = Counter()
    for e in runs:
        for g in e.guards:
            guard_counter[g] += 1

    model_counter = Counter(e.model for e in runs if e.model)
    repo_counter = Counter(e.repo_short for e in runs if e.repo_short)

    days_active = len({e.date.date() for e in runs})
    first = min((e.date for e in runs), default=None)
    last = max((e.date for e in runs), default=None)

    return {
        "runs_total": len(runs),
        "milestones_total": len(milestones),
        "prs_shipped": sum(1 for e in runs if e.pr_url),
        "verdicts": verdict_counts,
        "subs_num": subs_num,
        "subs_den": subs_den,
        "subs_pct": subs_pct,
        "guards": guard_counter,
        "guard_firings": sum(guard_counter.values()),
        "models": model_counter,
        "repos": repo_counter,
        "days_active": days_active,
        "first": first,
        "last": last,
    }


def render_snapshot(stats: dict) -> str:
    v = stats["verdicts"]
    order = [VERDICT_CLEAN, VERDICT_PARTIAL, VERDICT_FAILED, VERDICT_OTHER]
    parts = [f"{name} {v[name]}" for name in order if v.get(name)]
    verdict_mix = " · ".join(parts) if parts else "—"

    def top(c: Counter, n: int = 5) -> str:
        if not c:
            return "—"
        return " · ".join(f"`{k}` ({v})" for k, v in c.most_common(n))

    first = stats["first"].strftime("%Y-%m-%d") if stats["first"] else "—"
    last = stats["last"].strftime("%Y-%m-%d") if stats["last"] else "—"
    subs = f"{stats['subs_num']}/{stats['subs_den']} ({stats['subs_pct']:.0f}%)" \
        if stats["subs_den"] else "—"

    out = []
    out.append("| Metric | Value |")
    out.append("|---|---|")
    out.append(f"| Runs logged | **{stats['runs_total']}** |")
    out.append(f"| PRs opened | **{stats['prs_shipped']}** |")
    out.append(f"| Subtasks completed | {subs} |")
    out.append(f"| Distinct repos | {len(stats['repos'])} |")
    out.append(f"| Distinct models | {len(stats['models'])} |")
    out.append(f"| Guard firings | {stats['guard_firings']} |")
    out.append(f"| Milestones | {stats['milestones_total']} |")
    out.append(f"| Active days | {stats['days_active']} ({first} → {last}) |")
    out.append("")
    out.append(f"**Verdict mix** — {verdict_mix}")
    out.append("")
    out.append(f"**Top models** — {top(stats['models'])}")
    out.append("")
    out.append(f"**Top repos** — {top(stats['repos'])}")
    out.append("")
    out.append(f"**Top guards fired** — {top(stats['guards'])}")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# Page navigation
# ---------------------------------------------------------------------------

def page_filename(idx: int) -> str:
    return f"PAGE_{idx:03d}.md"


def page_nav(file_idx: int, last_idx: int) -> str:
    """Nav for archive file `PAGE_{file_idx:03d}.md`. README is page 1; archive
    pages start at 2. `last_idx` is the highest archive file number."""
    parts = []
    # Newer side
    if file_idx <= 2:
        parts.append("← [newer](../README.md)")
    else:
        parts.append(f"← [newer]({page_filename(file_idx - 1)})")
    # Older side
    if file_idx >= last_idx:
        parts.append("**older →**")
    else:
        parts.append(f"[older →]({page_filename(file_idx + 1)})")
    return " · ".join(parts)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    if not ENTRIES_DIR.exists():
        print(f"error: {ENTRIES_DIR} not found", file=sys.stderr)
        return 1

    entries: list[Entry] = []
    for path in sorted(ENTRIES_DIR.glob("*.md")):
        e = parse_entry(path)
        if e is None:
            print(f"warn: skipped {path.name} (no frontmatter)", file=sys.stderr)
            continue
        entries.append(e)

    entries.sort(key=lambda e: e.date, reverse=True)

    runs = [e for e in entries if e.is_run]
    milestones = [e for e in entries if e.is_milestone]
    stats = compute_stats(runs, milestones)

    # README: first page of runs.
    readme_rows = runs[:PAGE_SIZE]
    archive_rows = runs[PAGE_SIZE:]
    archive_pages = [
        archive_rows[i:i + PAGE_SIZE]
        for i in range(0, len(archive_rows), PAGE_SIZE)
    ]
    total_pages = 1 + len(archive_pages)  # README counts as page 1

    # Clean and regenerate pages/
    PAGES_DIR.mkdir(exist_ok=True)
    for old in PAGES_DIR.glob("PAGE_*.md"):
        old.unlink()

    # Archive pages start at file index 2 (README is page 1).
    last_idx = 1 + len(archive_pages)
    for i, page_rows in enumerate(archive_pages, start=2):
        page_path = PAGES_DIR / page_filename(i)
        nav = page_nav(i, last_idx)
        body = render_runs_table(page_rows, from_pages=True)
        content = (
            f"# fabgpt-coder log — page {i} of {total_pages}\n"
            f"\n_Archive. The freshest page is [`/README.md`](../README.md)._\n\n"
            f"{nav}\n\n{body}\n{nav}\n"
        )
        page_path.write_text(content, encoding="utf-8")

    # README
    snapshot = render_snapshot(stats)
    runs_table = render_runs_table(readme_rows, from_pages=False)
    milestones_table = render_milestones_table(milestones[:15])

    archive_links = ""
    if archive_pages:
        links = " · ".join(
            f"[{i}](pages/{page_filename(i)})"
            for i in range(2, total_pages + 1)
        )
        archive_links = (
            f"\n**Older runs** — page 1 (here) · {links}\n"
        )

    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    readme = f"""# fabgpt-coder — operations log

Public timeline of what **`fabgpt-coder`** — the [gitoma](https://github.com/fabriziosalmi/gitoma)-powered agent operated by [@fabriziosalmi](https://github.com/fabriziosalmi) — does across all repos. One entry per gitoma run, including runs that **didn't** ship a PR (those are where the learnings live).

Each entry has machine-readable frontmatter (date, repo, PR, model, endpoint, subtasks, guards, verdict) plus a short body. Append-only — entries are immutable once written.

> This file is auto-generated from `entries/` by `scripts/build_readme.py`. Do not edit by hand.

## Snapshot — {today}

{snapshot}
## Latest runs (showing {len(readme_rows)} of {stats['runs_total']})

{runs_table}{archive_links}
## Milestones (latest {min(15, len(milestones))} of {len(milestones)})

{milestones_table}
---

_Built by `scripts/build_readme.py` on {today}. Source-of-truth = `entries/*.md` frontmatter._
"""
    README.write_text(readme, encoding="utf-8")

    print(f"wrote {README.relative_to(ROOT)}")
    print(f"wrote {len(archive_pages)} archive page(s) under {PAGES_DIR.relative_to(ROOT)}/")
    print(f"  runs={stats['runs_total']} milestones={stats['milestones_total']} "
          f"prs={stats['prs_shipped']} guards={stats['guard_firings']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
