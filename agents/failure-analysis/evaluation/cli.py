"""CLI entrypoint for offline evaluation runs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.pipeline_orchestrator import EvaluationOrchestrator


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="AI Evaluation, Validation & Model Training Framework"
    )
    parser.add_argument("--config", default=None, help="Path to evaluation.yaml")
    parser.add_argument("--discover-only", action="store_true")
    parser.add_argument("--dataset-id", default=None)
    parser.add_argument(
        "--modules",
        default=None,
        help="Comma-separated FA-FR modules, e.g. FA-FR-001,FA-FR-002",
    )
    parser.add_argument("--max-logs", type=int, default=None)
    parser.add_argument("--output", default=None, help="Write JSON report to path")
    args = parser.parse_args(argv)

    orch = EvaluationOrchestrator(config_path=args.config)
    if args.discover_only:
        result = orch.discover()
    else:
        modules = (
            [m.strip() for m in args.modules.split(",") if m.strip()]
            if args.modules
            else None
        )
        result = orch.run(
            dataset_id=args.dataset_id,
            modules=modules,
            max_logs=args.max_logs,
        )

    text = json.dumps(result, indent=2, default=str)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
