from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from .models import Mutation, PitReport


RELEVANT_STATUSES = {
    "KILLED",
    "SURVIVED",
    "NO_COVERAGE",
    "TIMED_OUT",
    "MEMORY_ERROR",
    "RUN_ERROR",
}


def latest_mutations_xml(project_dir: Path) -> Path | None:
    report_root = project_dir / "target" / "pit-reports"
    if not report_root.exists():
        return None
    candidates = sorted(
        report_root.rglob("mutations.xml"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def _text(element: ET.Element, name: str) -> str:
    child = element.find(name)
    return child.text.strip() if child is not None and child.text else ""


def parse_mutations_xml(path: Path | None) -> PitReport:
    if path is None or not path.exists():
        return PitReport(path=None)

    root = ET.parse(path).getroot()
    report = PitReport(path=path)
    for mutation_el in root.findall("mutation"):
        status = (mutation_el.attrib.get("status") or "").upper()
        detected_attr = (mutation_el.attrib.get("detected") or "false").lower()
        detected = detected_attr == "true" or status in {"KILLED", "TIMED_OUT"}
        line_text = _text(mutation_el, "lineNumber")
        try:
            line_number = int(line_text) if line_text else None
        except ValueError:
            line_number = None

        mutation = Mutation(
            status=status,
            detected=detected,
            mutator=_text(mutation_el, "mutator"),
            source_file=_text(mutation_el, "sourceFile"),
            mutated_class=_text(mutation_el, "mutatedClass"),
            mutated_method=_text(mutation_el, "mutatedMethod"),
            line_number=line_number,
            description=_text(mutation_el, "description"),
            killing_test=_text(mutation_el, "killingTest"),
        )
        report.mutations.append(mutation)

        if status in RELEVANT_STATUSES:
            report.total += 1
            if detected:
                report.detected += 1
        if status == "KILLED":
            report.killed += 1
        elif status == "SURVIVED":
            report.survived += 1
        elif status == "NO_COVERAGE":
            report.no_coverage += 1
        elif status == "TIMED_OUT":
            report.timed_out += 1
        elif status in {"NON_VIABLE", "MEMORY_ERROR"}:
            report.non_viable += 1
        elif status == "RUN_ERROR":
            report.run_error += 1

    return report


def summarize_survived_mutants(report: PitReport, limit: int = 20) -> str:
    survivors = report.survived_mutations[:limit]
    if not survivors:
        return "No survived or uncovered mutants were reported."
    lines = []
    for idx, mutation in enumerate(survivors, start=1):
        location = f"{mutation.mutated_class}.{mutation.mutated_method}"
        if mutation.line_number is not None:
            location += f":{mutation.line_number}"
        lines.append(
            f"{idx}. {location} | {mutation.status} | {mutation.mutator} | "
            f"{mutation.description}"
        )
    return "\n".join(lines)


def classify_mutation(mutation: Mutation) -> str:
    mutator = mutation.mutator.lower()
    description = mutation.description.lower()
    if "conditionalsboundary" in mutator or "boundary" in description:
        return "boundary-condition"
    if "negateconditionals" in mutator or "conditional" in description:
        return "branch-polarity"
    if "mathmutator" in mutator or "math" in mutator or "addition" in description or "subtraction" in description:
        return "numeric-formula"
    if "return" in mutator or "replaced" in description and "return" in description:
        return "return-oracle"
    if "voidmethodcall" in mutator or "removed call" in description:
        return "side-effect"
    if "increments" in mutator:
        return "counter-update"
    if "constructor" in mutator:
        return "object-construction"
    return "general"


MUTATION_STRATEGIES = {
    "boundary-condition": "Generate tests exactly at, below, and above threshold values; assert monetary totals and eligibility results.",
    "branch-polarity": "Exercise both semantic branches; assert which branch should be selected and why.",
    "numeric-formula": "Assert exact BigDecimal amounts for subtotal, discount, shipping, tax, and total.",
    "return-oracle": "Assert returned booleans, strings, and result fields directly instead of only checking non-null values.",
    "side-effect": "Assert externally visible state or result messages caused by the removed call.",
    "counter-update": "Use multi-item or multi-category inputs and assert accumulated totals.",
    "object-construction": "Create representative domain objects and assert constructor validation and normalized fields.",
    "general": "Add focused semantic assertions tied to the mutated method and line.",
}


def mutation_type_guidance(report: PitReport, target_class: str | None = None, limit: int = 20) -> str:
    survivors = report.survived_mutations
    if target_class:
        target_survivors = [m for m in survivors if m.mutated_class == target_class]
        survivors = target_survivors or survivors
    survivors = survivors[:limit]
    if not survivors:
        return "No survived mutants. Prefer readability improvements and stronger semantic assertions only if clearly useful."

    grouped: dict[str, list[Mutation]] = {}
    for mutation in survivors:
        grouped.setdefault(classify_mutation(mutation), []).append(mutation)

    lines = ["Mutation-type-aware guidance:"]
    for category, mutations in grouped.items():
        lines.append(f"- {category}: {len(mutations)} mutant(s). Strategy: {MUTATION_STRATEGIES[category]}")
        for mutation in mutations[:5]:
            location = f"{mutation.mutated_class}.{mutation.mutated_method}"
            if mutation.line_number is not None:
                location += f":{mutation.line_number}"
            lines.append(f"  - {location}: {mutation.description}")
    return "\n".join(lines)
