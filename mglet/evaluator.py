from __future__ import annotations

from pathlib import Path

from .coverage import jacoco_xml_path, parse_jacoco_xml
from .java_project import run_maven_goal
from .models import Evaluation
from .pitest import latest_mutations_xml, parse_mutations_xml
from .static_metrics import compute_static_metrics


def evaluate_project(
    project_dir: Path,
    config: dict,
    output_dir: Path,
    label: str,
) -> Evaluation:
    from .command import write_command_log

    commands = []
    maven_cfg = config["maven"]

    test_result = run_maven_goal(project_dir, maven_cfg, "test_goal")
    commands.append(test_result.to_dict())
    write_command_log(test_result, output_dir / "commands", f"{label}_maven_test")

    flaky_failures = 0
    flaky_runs = int(config.get("flaky_runs", 1))
    for idx in range(max(0, flaky_runs - 1)):
        rerun = run_maven_goal(project_dir, maven_cfg, "test_goal")
        commands.append(rerun.to_dict())
        write_command_log(rerun, output_dir / "commands", f"{label}_flaky_{idx + 2}")
        if not rerun.ok:
            flaky_failures += 1

    jacoco_result = run_maven_goal(project_dir, maven_cfg, "jacoco_goal")
    commands.append(jacoco_result.to_dict())
    write_command_log(jacoco_result, output_dir / "commands", f"{label}_jacoco")
    coverage = parse_jacoco_xml(jacoco_xml_path(project_dir))

    pit_result = run_maven_goal(project_dir, maven_cfg, "pit_goal")
    commands.append(pit_result.to_dict())
    write_command_log(pit_result, output_dir / "commands", f"{label}_pit")
    pit = parse_mutations_xml(latest_mutations_xml(project_dir))

    return Evaluation(
        label=label,
        maven_test_ok=test_result.ok,
        flaky_failures=flaky_failures,
        coverage=coverage,
        pit=pit,
        static_metrics=compute_static_metrics(project_dir),
        commands=commands,
    )
