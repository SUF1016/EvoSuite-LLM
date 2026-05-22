from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _ratio(data: dict[str, Any], counter: str) -> float:
    return float(data.get("coverage", {}).get("counters", {}).get(counter, {}).get("ratio", 0.0))


def render_summary_markdown(results: dict[str, Any]) -> str:
    evaluations = results.get("evaluations", [])
    lines = [
        "# MGLET Experiment Summary",
        "",
        f"- Project: `{results.get('project_dir', '')}`",
        f"- Targets: `{', '.join(results.get('targets', []))}`",
        f"- Iterations: `{results.get('iterations', 0)}`",
        "",
        "| Label | Test OK | Line Cov. | Branch Cov. | Mutation Score | Assertions | Assert Strength | Readability | Flaky Failures |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for evaluation in evaluations:
        static = evaluation.get("static_metrics", {})
        pit = evaluation.get("pit", {})
        lines.append(
            "| {label} | {ok} | {line:.2%} | {branch:.2%} | {mutation:.2%} | "
            "{assertions} | {strength:.1f} | {readability:.1f} | {flaky} |".format(
                label=evaluation.get("label", ""),
                ok="yes" if evaluation.get("maven_test_ok") else "no",
                line=_ratio(evaluation, "LINE"),
                branch=_ratio(evaluation, "BRANCH"),
                mutation=float(pit.get("mutation_score", 0.0)),
                assertions=static.get("assertions", 0),
                strength=float(static.get("assertion_strength_score", 0.0)),
                readability=float(static.get("readability_score", 0.0)),
                flaky=evaluation.get("flaky_failures", 0),
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `evosuite-baseline` is the generated suite before LLM enhancement.",
            "- `llm-iteration-N` is the suite after the N-th mutation-guided prompt and validation loop.",
            "- Mutation score is the primary outcome because EvoSuite is already coverage-oriented.",
        ]
    )
    return "\n".join(lines) + "\n"
