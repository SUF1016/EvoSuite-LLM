from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CommandResult:
    args: list[str]
    cwd: Path
    returncode: int
    stdout: str
    stderr: str
    elapsed_seconds: float

    @property
    def output(self) -> str:
        return "\n".join(part for part in [self.stdout, self.stderr] if part)

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "args": self.args,
            "cwd": str(self.cwd),
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "elapsed_seconds": self.elapsed_seconds,
        }


@dataclass
class Mutation:
    status: str
    detected: bool
    mutator: str
    source_file: str
    mutated_class: str
    mutated_method: str
    line_number: int | None
    description: str
    killing_test: str = ""

    def to_prompt_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "mutator": self.mutator,
            "class": self.mutated_class,
            "method": self.mutated_method,
            "source_file": self.source_file,
            "line": self.line_number,
            "description": self.description,
        }


@dataclass
class PitReport:
    path: Path | None
    total: int = 0
    detected: int = 0
    killed: int = 0
    survived: int = 0
    no_coverage: int = 0
    timed_out: int = 0
    non_viable: int = 0
    run_error: int = 0
    mutations: list[Mutation] = field(default_factory=list)

    @property
    def mutation_score(self) -> float:
        if self.total == 0:
            return 0.0
        return self.detected / self.total

    @property
    def survived_mutations(self) -> list[Mutation]:
        return [
            m
            for m in self.mutations
            if m.status.upper() in {"SURVIVED", "NO_COVERAGE"} or not m.detected
        ]

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path) if self.path else None,
            "total": self.total,
            "detected": self.detected,
            "killed": self.killed,
            "survived": self.survived,
            "no_coverage": self.no_coverage,
            "timed_out": self.timed_out,
            "non_viable": self.non_viable,
            "run_error": self.run_error,
            "mutation_score": round(self.mutation_score, 4),
            "survived_mutations": [
                m.to_prompt_dict() for m in self.survived_mutations[:50]
            ],
        }


@dataclass
class CoverageCounter:
    missed: int = 0
    covered: int = 0

    @property
    def total(self) -> int:
        return self.missed + self.covered

    @property
    def ratio(self) -> float:
        if self.total == 0:
            return 0.0
        return self.covered / self.total

    def to_dict(self) -> dict[str, Any]:
        return {
            "missed": self.missed,
            "covered": self.covered,
            "total": self.total,
            "ratio": round(self.ratio, 4),
        }


@dataclass
class CoverageReport:
    path: Path | None
    counters: dict[str, CoverageCounter] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path) if self.path else None,
            "counters": {k: v.to_dict() for k, v in self.counters.items()},
        }


@dataclass
class StaticTestMetrics:
    test_files: int = 0
    test_methods: int = 0
    assertions: int = 0
    assertion_strength: float = 0.0
    strong_assertions: int = 0
    weak_assertions: int = 0
    semantic_assertions: int = 0
    generated_style_names: int = 0
    average_test_name_length: float = 0.0
    smell_count: int = 0
    smell_examples: list[str] = field(default_factory=list)

    @property
    def assertions_per_test(self) -> float:
        if self.test_methods == 0:
            return 0.0
        return self.assertions / self.test_methods

    @property
    def assertion_strength_per_test(self) -> float:
        if self.test_methods == 0:
            return 0.0
        return self.assertion_strength / self.test_methods

    @property
    def assertion_strength_score(self) -> float:
        if self.test_methods == 0:
            return 0.0
        semantic_bonus = min(self.semantic_assertions * 1.5, 15)
        weak_penalty = min(self.weak_assertions * 0.75, 10)
        return max(
            0.0,
            min(100.0, self.assertion_strength_per_test * 12 + semantic_bonus - weak_penalty),
        )

    @property
    def readability_score(self) -> float:
        if self.test_methods == 0:
            return 0.0
        generated_penalty = (self.generated_style_names / self.test_methods) * 35
        smell_penalty = min(self.smell_count * 3, 25)
        length_bonus = min(self.average_test_name_length, 35) / 35 * 15
        return max(0.0, min(100.0, 70 + length_bonus - generated_penalty - smell_penalty))

    def to_dict(self) -> dict[str, Any]:
        return {
            "test_files": self.test_files,
            "test_methods": self.test_methods,
            "assertions": self.assertions,
            "assertions_per_test": round(self.assertions_per_test, 3),
            "assertion_strength": round(self.assertion_strength, 2),
            "assertion_strength_per_test": round(self.assertion_strength_per_test, 3),
            "assertion_strength_score": round(self.assertion_strength_score, 2),
            "strong_assertions": self.strong_assertions,
            "weak_assertions": self.weak_assertions,
            "semantic_assertions": self.semantic_assertions,
            "generated_style_names": self.generated_style_names,
            "average_test_name_length": round(self.average_test_name_length, 2),
            "smell_count": self.smell_count,
            "smell_examples": self.smell_examples[:20],
            "readability_score": round(self.readability_score, 2),
        }


@dataclass
class Evaluation:
    label: str
    maven_test_ok: bool
    flaky_failures: int
    coverage: CoverageReport
    pit: PitReport
    static_metrics: StaticTestMetrics
    commands: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "maven_test_ok": self.maven_test_ok,
            "flaky_failures": self.flaky_failures,
            "coverage": self.coverage.to_dict(),
            "pit": self.pit.to_dict(),
            "static_metrics": self.static_metrics.to_dict(),
            "commands": self.commands,
        }
