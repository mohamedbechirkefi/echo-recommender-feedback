# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""Structural check of CITATION.cff against CFF 1.2.0 (keys and value shapes; M6).

No YAML parser is installed, so the check reads the simple block layout this file
uses: top-level ``key: value`` lines, and ``- key: value`` list items under
``authors``, ``references`` and ``keywords``.
"""

import re
from pathlib import Path

CFF = Path(__file__).resolve().parents[1] / "CITATION.cff"

# CFF 1.2.0 top-level keys (https://github.com/citation-file-format/citation-file-format, schema.json).
ALLOWED = {
    "abstract", "authors", "cff-version", "commit", "contact", "date-released", "doi", "identifiers",
    "keywords", "license", "license-url", "message", "preferred-citation", "references", "repository",
    "repository-artifact", "repository-code", "title", "type", "url", "version",
}
REQUIRED = {"authors", "cff-version", "message", "title"}
PERSON_KEYS = {"family-names", "given-names", "name-particle", "name-suffix", "affiliation", "orcid",
               "alias", "website", "address", "city", "country", "email", "fax", "post-code", "region", "tel"}


def top_level() -> dict[str, str]:
    out = {}
    for line in CFF.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^([a-z][a-z\-]*):(?:\s+(.*))?$", line)
        if m:
            out[m.group(1)] = (m.group(2) or "").strip()
    return out


def block(name: str) -> list[str]:
    lines = CFF.read_text(encoding="utf-8").splitlines()
    i = lines.index(f"{name}:")
    out = []
    for line in lines[i + 1:]:
        if line and not line.startswith(" "):
            break
        out.append(line)
    return out


def test_keys_and_required():
    keys = top_level()
    assert set(keys) <= ALLOWED, set(keys) - ALLOWED
    assert REQUIRED <= set(keys)
    assert keys["cff-version"] == "1.2.0"
    assert keys["type"] in {"software", "dataset"}
    assert keys["message"].startswith('"') and keys["title"].startswith('"')


def test_release_candidate_without_release_date():
    keys = top_level()
    assert "date-released" not in keys  # removed until a release exists (owner-approvals-2026-11-25e)
    assert re.fullmatch(r'"\d+\.\d+\.\d+-rc\d+"', keys["version"])


def test_authors_and_references_shapes():
    authors = block("authors")
    assert authors and authors[0].startswith("  - ")
    for line in authors:
        key = line.strip().lstrip("- ").split(":")[0]
        assert key in PERSON_KEYS, key
    refs = "\n".join(block("references"))
    assert "type: dataset" in refs and "title:" in refs and "authors:" in refs
    assert all(line.startswith("  - ") for line in block("keywords"))
