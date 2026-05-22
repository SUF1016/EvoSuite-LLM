from __future__ import annotations

import re
from pathlib import Path

from .java_project import find_test_files
from .models import StaticTestMetrics


ASSERTION_RE = re.compile(
    r"\b(assert[A-Za-z]*|Assertions\.assert[A-Za-z]*|MatcherAssert\.assertThat)\s*\("
)
ASSERT_LINE_RE = re.compile(
    r"\b(assert[A-Za-z]*|Assertions\.assert[A-Za-z]*|MatcherAssert\.assertThat|fail)\s*\("
)
TEST_METHOD_RE = re.compile(
    r"@Test(?:\s*\([^)]*\))?\s+(?:public\s+)?(?:void|[A-Za-z0-9_<>\[\]]+)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",
    re.MULTILINE,
)
GENERATED_NAME_RE = re.compile(r"^(test\d+|test[A-Fa-f0-9]{6,}|notGeneratedAnyAssertion.*)$")
SEMANTIC_RESULT_RE = re.compile(
    r"\b(getTotal|getSubtotal|getTierDiscount|getCouponDiscount|getShippingFee|getTax|"
    r"isCouponApplied|getMessages|rejectionReason|discountFor|tierDiscount|subtotal)\b"
)
MONEY_RE = re.compile(r"(BigDecimal|new\s+BigDecimal|setScale|\d+\.\d{2})")
SMELL_PATTERNS = {
    "sleep": re.compile(r"\bThread\.sleep\s*\("),
    "stdout": re.compile(r"\bSystem\.out\.print"),
    "empty_catch": re.compile(r"catch\s*\([^)]*\)\s*\{\s*\}", re.DOTALL),
    "random": re.compile(r"\bnew\s+Random\s*\("),
}


def assertion_strength_for_line(line: str) -> tuple[float, bool, bool]:
    stripped = line.strip()
    if not ASSERT_LINE_RE.search(stripped):
        return 0.0, False, False

    weak = bool(re.search(r"\b(assertNotNull|assertNull)\s*\(", stripped))
    semantic = bool(SEMANTIC_RESULT_RE.search(stripped))
    strength = 1.0

    if re.search(r"\b(assertEquals|assertArrayEquals|assertSame|assertThat)\s*\(", stripped):
        strength = 2.5
    if re.search(r"\b(assertTrue|assertFalse)\s*\(", stripped):
        strength = 1.75
    if re.search(r"\bfail\s*\(", stripped):
        strength = 1.5
    if weak:
        strength = 0.5
    if MONEY_RE.search(stripped):
        strength += 1.0
    if semantic:
        strength += 1.0
    if "getMessage()" in stripped or "contains(" in stripped:
        strength += 0.75

    return strength, strength >= 3.0, weak


def compute_static_metrics(project_dir: Path) -> StaticTestMetrics:
    metrics = StaticTestMetrics()
    lengths: list[int] = []

    for path in find_test_files(project_dir):
        metrics.test_files += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        assertions = ASSERTION_RE.findall(text)
        metrics.assertions += len(assertions)
        for line in text.splitlines():
            strength, strong, weak = assertion_strength_for_line(line)
            if strength == 0.0:
                continue
            metrics.assertion_strength += strength
            if strong:
                metrics.strong_assertions += 1
            if weak:
                metrics.weak_assertions += 1
            if SEMANTIC_RESULT_RE.search(line):
                metrics.semantic_assertions += 1
        names = TEST_METHOD_RE.findall(text)
        metrics.test_methods += len(names)
        lengths.extend(len(name) for name in names)
        metrics.generated_style_names += sum(1 for name in names if GENERATED_NAME_RE.match(name))
        for smell_name, pattern in SMELL_PATTERNS.items():
            matches = pattern.findall(text)
            metrics.smell_count += len(matches)
            if matches and len(metrics.smell_examples) < 20:
                metrics.smell_examples.append(f"{path.name}: {smell_name}")

    metrics.average_test_name_length = sum(lengths) / len(lengths) if lengths else 0.0
    return metrics
