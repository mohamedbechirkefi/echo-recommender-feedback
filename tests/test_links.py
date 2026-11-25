# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""Every relative link in the tracked Markdown files resolves (M6, scripts/check_links.py)."""

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_links.py"
spec = importlib.util.spec_from_file_location("check_links", SCRIPT)
check_links = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_links)


def test_slug_rules():
    assert check_links.slug("5.1 EXP-002: the primary contrast") == "51-exp-002-the-primary-contrast"
    assert check_links.slug("Quick start and reproduction") == "quick-start-and-reproduction"


def test_detects_broken_link(tmp_path):
    md = tmp_path / "a.md"
    md.write_text("# Title\n[ok](a.md#title) [bad](missing.md) [anchor](a.md#nope) `[code](x.md)`\n", encoding="utf-8")
    found = [m.group(1) for m in check_links.LINK.finditer(check_links.strip_code(md.read_text()))]
    assert found == ["a.md#title", "missing.md", "a.md#nope"]
    assert "title" in check_links.anchors(md)


def test_repository_links_resolve():
    n, broken = check_links.check()
    assert n > 0
    assert broken == []


def test_inline_code_paths_exist():
    n, missing = check_links.check_code_paths()
    assert n > 0
    assert missing == []
