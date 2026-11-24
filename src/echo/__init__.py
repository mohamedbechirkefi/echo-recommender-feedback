# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""ECHO: seeded simulation of music recommendation feedback.

All outputs are simulation results. They hold only within the model
assumptions of research/protocol.md and are not evidence about people.

Module layout (master prompt section 4: separate concerns):

- ``config``: typed, validated simulation configuration and its hash.
- ``vectors``: normalisation, cosine similarity and angles (pure functions).
- ``catalogue``: synthetic catalogue and listener generation (ingestion).
- ``policies``, ``choice``, ``preferences``: model components.
- ``simulate``: the session loop.
- ``metrics``: outcome metrics.
- ``schema``: versioned JSON result schema (validated at export and import).
- ``manifest``: per-run reproducibility manifest.
- ``runner``: experiment matrix expansion, freeze guard and serialization.
- ``stats``: seed-level uncertainty.
- ``report``: tables, figures and PDF from result files.
- ``smoke``: EXP-001 verification checks V1 to V6.
- ``cli``: command-line entry point.
"""

__version__ = "0.1.0"
