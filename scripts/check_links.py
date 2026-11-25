# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""Check every relative link in the repository's tracked Markdown files (M6).

A relative link ``[text](target)`` or ``![alt](target)`` must resolve to an existing
file or directory, relative to the linking file; a ``#anchor`` must match a heading
of the target Markdown file (GitHub slug rules: lower case, punctuation removed,
spaces to hyphens). External links (``http:``, ``https:``, ``mailto:``) are not
fetched. Links inside fenced code blocks and inline code are ignored as links.

Second check: an inline-code path such as `research/protocol.md` (a token with a
"/" and a file extension, no spaces, no placeholder such as EXP-00N or <...>) must
exist relative to the repository root or to the linking file. Paths under
git-ignored or generated folders (results/raw, data/raw, data/processed, dist,
node_modules, .venv) are skipped, and so are the append-only records and frozen
protocols (APPEND_ONLY): they are historical, cite paths relative to a results folder
or to the shared labs folder, and are never edited in place.

Usage:
    .venv/bin/python scripts/check_links.py        # prints each broken link, exit 1 if any
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

REPO = Path(__file__).resolve().parents[1]
LINK = re.compile(r"!?\[(?:[^\]\[]|\[[^\]]*\])*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
EXTERNAL = ("http://", "https://", "mailto:", "data:")
CODE_PATH = re.compile(r"`([\w.\-]+(?:/[\w.\-]+)+\.(?:md|py|json|jsonl|csv|svg|toml|lock|txt|ts|tsx|mjs|png|pdf|log|tex|cff))`")
IGNORED_PREFIXES = ("results/raw/", "data/raw/", "data/processed/", "dist/", "demo/dist/", "node_modules/", ".venv/")
APPEND_ONLY = re.compile(r"^(progress\.md|research/decision_log\.md|research/protocol\.md|research/experiments/EXP-\d{3}/protocol\.md)$")


def tracked_markdown() -> list[Path]:
    out = subprocess.run(["git", "ls-files", "*.md"], cwd=REPO, capture_output=True, text=True, check=True).stdout
    return [REPO / p for p in out.splitlines() if "node_modules/" not in p]


def strip_code(text: str) -> str:
    text = re.sub(r"^(```|~~~).*?^\1", "", text, flags=re.S | re.M)
    return re.sub(r"`[^`\n]*`", "", text)


def slug(heading: str) -> str:
    h = re.sub(r"[`*_]|<[^>]+>", "", heading.strip().lower())
    h = re.sub(r"[^\w\- ]", "", h)
    return h.replace(" ", "-")


def anchors(md: Path) -> set[str]:
    seen: dict[str, int] = {}
    out = set()
    for line in strip_code(md.read_text(encoding="utf-8")).splitlines():
        m = re.match(r"^#{1,6}\s+(.*?)\s*#*\s*$", line)
        if m:
            s = slug(m.group(1))
            n = seen.get(s, 0)
            out.add(s if n == 0 else f"{s}-{n}")
            seen[s] = n + 1
    return out


def check() -> tuple[int, list[str]]:
    broken: list[str] = []
    n = 0
    for md in tracked_markdown():
        for m in LINK.finditer(strip_code(md.read_text(encoding="utf-8"))):
            target = m.group(1)
            if target.startswith(EXTERNAL):
                continue
            n += 1
            path, _, frag = target.partition("#")
            dest = (md.parent / unquote(path)).resolve() if path else md
            where = f"{md.relative_to(REPO)}: {target}"
            if not dest.exists():
                broken.append(f"{where} (missing file)")
            elif frag and dest.suffix == ".md" and frag.lower() not in anchors(dest):
                broken.append(f"{where} (missing anchor)")
    return n, broken


def check_code_paths() -> tuple[int, list[str]]:
    broken: list[str] = []
    n = 0
    for md in tracked_markdown():
        if APPEND_ONLY.match(str(md.relative_to(REPO))):
            continue
        text = re.sub(r"^(```|~~~).*?^\1", "", md.read_text(encoding="utf-8"), flags=re.S | re.M)
        for m in CODE_PATH.finditer(text):
            target = m.group(1)
            if target.startswith(IGNORED_PREFIXES) or re.search(r"EXP-00N|NNN", target):
                continue
            n += 1
            if not ((REPO / target).exists() or (md.parent / target).exists()):
                broken.append(f"{md.relative_to(REPO)}: `{target}` (missing path)")
    return n, broken


def main() -> int:
    n, broken = check()
    k, missing = check_code_paths()
    for b in broken + missing:
        print("BROKEN", b)
    print(f"{n} relative links checked, {len(broken)} broken; {k} inline-code paths checked, {len(missing)} missing")
    return 1 if broken or missing else 0


if __name__ == "__main__":
    sys.exit(main())
