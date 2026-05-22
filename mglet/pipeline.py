from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import Any

from .evaluator import evaluate_project
from .evosuite import EvoSuiteRunner
from .java_project import class_to_test_path, ensure_maven_project, run_maven_goal
from .llm import make_llm_client
from .patching import extract_java_files, write_generated_files
from .prompting import (
    build_enhancement_messages,
    build_repair_messages,
    build_rule_extraction_messages,
    collect_related_source_context,
    heuristic_business_rules,
)
from .reports import render_summary_markdown, write_json


class CoursePipeline:
    def __init__(self, config: dict[str, Any], project_dir: Path, output_dir: Path) -> None:
        self.config = config
        self.project_dir = project_dir
        self.output_dir = output_dir
        self.llm = make_llm_client(config)

    def run(self, targets: list[str] | None = None, skip_evosuite: bool = False) -> dict[str, Any]:
        ensure_maven_project(self.project_dir)
        targets = targets or list(self.config.get("targets", []))
        if not targets:
            raise ValueError("No target classes configured. Add targets to config or pass --target.")

        run_id = time.strftime("%Y%m%d-%H%M%S")
        run_dir = self.output_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.project_dir / "pom.xml", run_dir / "pom.xml.snapshot")

        if not skip_evosuite:
            evosuite = EvoSuiteRunner(self.project_dir, self.config, run_dir)
            for target in targets:
                evosuite.generate(target)

        evaluations: list[dict[str, Any]] = []
        baseline = evaluate_project(self.project_dir, self.config, run_dir, "evosuite-baseline")
        evaluations.append(baseline.to_dict())
        current_pit = baseline.pit
        current_coverage = baseline.coverage
        business_rules = {
            target: self._extract_business_rules(target, run_dir)
            for target in targets
        }

        generated_paths: list[Path] = []
        for iteration in range(1, int(self.config.get("iterations", 1)) + 1):
            for target in targets:
                messages = build_enhancement_messages(
                    self.project_dir,
                    target,
                    current_pit,
                    current_coverage,
                    self.config.get("prompt", {}),
                    business_rules=business_rules.get(target, ""),
                )
                response = self.llm.complete(messages)
                response_path = run_dir / "llm" / f"iteration_{iteration}_{target.replace('.', '_')}.md"
                response_path.parent.mkdir(parents=True, exist_ok=True)
                response_path.write_text(response, encoding="utf-8")
                fallback = class_to_test_path(self.project_dir, target).relative_to(self.project_dir)
                files = extract_java_files(response, fallback_relative_path=fallback)
                generated_paths = write_generated_files(self.project_dir, files)

                if not generated_paths:
                    continue

                test_result = run_maven_goal(self.project_dir, self.config["maven"], "test_goal")
                if not test_result.ok:
                    generated_paths = self._repair(target, generated_paths, test_result.output, run_dir)

            evaluation = evaluate_project(
                self.project_dir,
                self.config,
                run_dir,
                f"llm-iteration-{iteration}",
            )
            evaluations.append(evaluation.to_dict())
            current_pit = evaluation.pit
            current_coverage = evaluation.coverage

        results: dict[str, Any] = {
            "run_id": run_id,
            "project_dir": str(self.project_dir),
            "targets": targets,
            "iterations": int(self.config.get("iterations", 1)),
            "generated_files": [str(p) for p in generated_paths],
            "business_rules": business_rules,
            "evaluations": evaluations,
        }
        write_json(run_dir / "results.json", results)
        (run_dir / "summary.md").write_text(render_summary_markdown(results), encoding="utf-8")
        return results

    def _extract_business_rules(self, target: str, run_dir: Path) -> str:
        messages = build_rule_extraction_messages(
            self.project_dir,
            target,
            self.config.get("prompt", {}),
        )
        response = self.llm.complete(messages)
        if response.strip() == "NO_CHANGE":
            source_context = collect_related_source_context(
                self.project_dir,
                target,
                int(self.config.get("prompt", {}).get("max_rule_source_chars", 18000)),
            )
            response = heuristic_business_rules(source_context)
        response_path = run_dir / "llm" / f"business_rules_{target.replace('.', '_')}.md"
        response_path.parent.mkdir(parents=True, exist_ok=True)
        response_path.write_text(response, encoding="utf-8")
        return response

    def _repair(
        self,
        target: str,
        generated_paths: list[Path],
        failing_output: str,
        run_dir: Path,
    ) -> list[Path]:
        repaired_paths = generated_paths
        for attempt in range(1, int(self.config.get("repair_attempts", 2)) + 1):
            messages = build_repair_messages(
                self.project_dir,
                target,
                failing_output,
                repaired_paths,
                self.config.get("prompt", {}),
            )
            response = self.llm.complete(messages)
            response_path = run_dir / "llm" / f"repair_{attempt}_{target.replace('.', '_')}.md"
            response_path.parent.mkdir(parents=True, exist_ok=True)
            response_path.write_text(response, encoding="utf-8")
            files = extract_java_files(response)
            if not files:
                break
            repaired_paths = write_generated_files(self.project_dir, files)
            test_result = run_maven_goal(self.project_dir, self.config["maven"], "test_goal")
            if test_result.ok:
                return repaired_paths
            failing_output = test_result.output
        return repaired_paths
