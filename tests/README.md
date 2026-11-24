<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# tests

pytest and hypothesis suite (M2): cosine and normalisation edge cases (`test_vectors.py`); choice, update rules, policies, candidate exclusion and Gini with hand-computed golden values and property tests (`test_components.py`); determinism, the zero-drift negative control, exclusion from the per-step log, common random numbers and a differential test against the loop-based reference `reference_sim.py` (`test_simulation.py`); result schema, run guards, runner integration, stop rule, statistics and report (`test_schema_runner.py`). Run with `PYTHONPATH=src uv run --frozen python -m echo.cli test`.
