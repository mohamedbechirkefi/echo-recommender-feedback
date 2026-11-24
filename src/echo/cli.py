# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""Command-line interface: smoke, run, report, test.

Run from the repository root:

    PYTHONPATH=src uv run --frozen python -m echo.cli smoke
    PYTHONPATH=src uv run --frozen python -m echo.cli run --config experiments/EXP-002/config.json
    PYTHONPATH=src uv run --frozen python -m echo.cli report results/exploratory/EXP-001
    PYTHONPATH=src uv run --frozen python -m echo.cli test

Exit codes: 0 success, 1 failed checks or runs, 2 refused by a guard.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from .manifest import REPO_ROOT
from .runner import RefusedError, StopRuleError, default_out_dir, load_experiment, run_experiment


def _progress(i: int, n: int, run_id: str, status: str, secs: float) -> None:
    print(f"[{i}/{n}] {run_id} {status} {secs:.2f}s", flush=True)


def cmd_run(args: argparse.Namespace) -> int:
    try:
        summaries = run_experiment(Path(args.config), Path(args.out) if args.out else None,
                                   trace_memory=args.trace_memory, progress=_progress)
    except RefusedError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    except StopRuleError as exc:
        print(f"STOPPED: {exc}", file=sys.stderr)
        return 1
    failed = sum(1 for s in summaries if s["result"]["status"] != "ok")
    print(f"done: {len(summaries)} runs, {failed} failed")
    return 1 if failed else 0


def cmd_smoke(args: argparse.Namespace) -> int:
    from .smoke import run_checks

    config = Path(args.config)
    exp = load_experiment(config)
    if exp["label"] != "exploratory":
        print("REFUSED: smoke only runs exploratory configs", file=sys.stderr)
        return 2
    out = Path(args.out) if args.out else default_out_dir(exp)
    try:
        summaries = run_experiment(config, out, record={"smoke"}, trace_memory=args.trace_memory, progress=_progress)
    except (RefusedError, StopRuleError) as exc:
        print(f"REFUSED or STOPPED: {exc}", file=sys.stderr)
        return 2
    checks = run_checks(summaries, out, exp["experiment_id"], exp["label"])
    for k in sorted(c for c in checks if c.startswith("V")):
        print(f"{k}: {'PASS' if checks[k]['pass'] else 'FAIL'}")
    print("ALL CHECKS PASS" if checks["all_pass"] else "SOME CHECKS FAILED")
    return 0 if checks["all_pass"] else 1


def cmd_report(args: argparse.Namespace) -> int:
    from .report import generate

    summary = generate(Path(args.results_dir), pdf=not args.no_pdf)
    print(json.dumps({k: summary[k] for k in ("experiment_id", "label", "n_runs", "n_failed", "checks_all_pass", "pdf")}, indent=1))
    return 0


def cmd_test(args: argparse.Namespace) -> int:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.call([sys.executable, "-m", "pytest", *args.pytest_args], cwd=REPO_ROOT, env=env)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="echo", description="ECHO recommender-feedback simulation (simulation only).")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("smoke", help="run the exploratory EXP-001 matrix and checks V1 to V6")
    s.add_argument("--config", default=str(REPO_ROOT / "experiments" / "EXP-001" / "config.json"))
    s.add_argument("--out", default=None)
    s.add_argument("--trace-memory", action="store_true")
    s.set_defaults(func=cmd_smoke)
    r = sub.add_parser("run", help="run an experiment config (confirmatory configs need a frozen protocol)")
    r.add_argument("--config", required=True)
    r.add_argument("--out", default=None)
    r.add_argument("--trace-memory", action="store_true")
    r.set_defaults(func=cmd_run)
    rp = sub.add_parser("report", help="build tables, figures and PDF from a results directory")
    rp.add_argument("results_dir")
    rp.add_argument("--no-pdf", action="store_true")
    rp.set_defaults(func=cmd_report)
    t = sub.add_parser("test", help="run the test suite")
    t.add_argument("pytest_args", nargs=argparse.REMAINDER)
    t.set_defaults(func=cmd_test)
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv[:1] == ["test"]:  # pass every remaining argument to pytest unchanged
        return cmd_test(argparse.Namespace(pytest_args=argv[1:]))
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
