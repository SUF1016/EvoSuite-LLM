from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config, resolve_config_path, resolve_project_dir
from .evaluator import evaluate_project
from .pipeline import CoursePipeline
from .reports import render_summary_markdown, write_json


def redact_config(config: dict) -> dict:
    redacted = json.loads(json.dumps(config, ensure_ascii=False))
    llm = redacted.get("llm", {})
    if llm.get("api_key"):
        llm["api_key"] = f"<redacted:{len(llm['api_key'])}>"
    return redacted


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mglet",
        description="Mutation-guided LLM enhancement for EvoSuite-generated Java unit tests.",
    )
    parser.add_argument("--config", default="configs/course-project.json", help="Path to JSON config.")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run EvoSuite, LLM enhancement, validation, PIT and JaCoCo.")
    run.add_argument("--target", action="append", default=[], help="Fully qualified target class.")
    run.add_argument("--skip-evosuite", action="store_true", help="Use existing tests as the seed suite.")

    evaluate = sub.add_parser("evaluate", help="Evaluate an existing Maven project test suite.")
    evaluate.add_argument("--label", default="manual", help="Label used in output files.")

    prompt = sub.add_parser("print-config", help="Print the resolved configuration.")
    prompt.add_argument("--pretty", action="store_true")

    report = sub.add_parser("render-report", help="Render summary markdown from a results.json file.")
    report.add_argument("results_json")
    report.add_argument("--output", default="")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_config(args.config)
    project_dir = resolve_project_dir(config, args.config)
    output_dir = resolve_config_path(config["output_dir"], args.config)
    if config.get("evosuite", {}).get("jar"):
        config["evosuite"]["jar"] = str(resolve_config_path(config["evosuite"]["jar"], args.config))
    if config.get("maven", {}).get("executable") not in {None, "mvn"}:
        config["maven"]["executable"] = str(resolve_config_path(config["maven"]["executable"], args.config))

    if args.command == "print-config":
        text = json.dumps(redact_config(config), ensure_ascii=False, indent=2 if args.pretty else None)
        print(text)
        return 0

    if args.command == "evaluate":
        run_dir = output_dir / "manual-evaluation"
        evaluation = evaluate_project(project_dir, config, run_dir, args.label)
        data = {"project_dir": str(project_dir), "targets": config.get("targets", []), "evaluations": [evaluation.to_dict()]}
        write_json(run_dir / "results.json", data)
        (run_dir / "summary.md").write_text(render_summary_markdown(data), encoding="utf-8")
        print(run_dir / "summary.md")
        return 0

    if args.command == "render-report":
        data = json.loads(Path(args.results_json).read_text(encoding="utf-8"))
        markdown = render_summary_markdown(data)
        if args.output:
            Path(args.output).write_text(markdown, encoding="utf-8")
        else:
            print(markdown)
        return 0

    if args.command == "run":
        targets = args.target or list(config.get("targets", []))
        pipeline = CoursePipeline(config, project_dir, output_dir)
        results = pipeline.run(targets=targets, skip_evosuite=args.skip_evosuite)
        print(Path(config["output_dir"]).resolve() / results["run_id"] / "summary.md")
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
