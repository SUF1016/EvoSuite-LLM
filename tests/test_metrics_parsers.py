import tempfile
import unittest
from pathlib import Path

from mglet.coverage import parse_jacoco_xml
from mglet.pitest import mutation_type_guidance, parse_mutations_xml
from mglet.static_metrics import compute_static_metrics


class MetricsParserTests(unittest.TestCase):
    def test_parse_pit_mutations(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mutations.xml"
            path.write_text(
                """<mutations>
<mutation detected="true" status="KILLED">
  <sourceFile>DiscountCalculator.java</sourceFile>
  <mutatedClass>edu.course.demo.DiscountCalculator</mutatedClass>
  <mutatedMethod>freeShipping</mutatedMethod>
  <methodDescription>()Z</methodDescription>
  <lineNumber>51</lineNumber>
  <mutator>org.pitest.mutationtest.engine.gregor.mutators.ConditionalsBoundaryMutator</mutator>
  <description>changed conditional boundary</description>
  <killingTest>edu.course.demo.DiscountCalculatorTest</killingTest>
</mutation>
<mutation detected="false" status="SURVIVED">
  <sourceFile>DiscountCalculator.java</sourceFile>
  <mutatedClass>edu.course.demo.DiscountCalculator</mutatedClass>
  <mutatedMethod>discountPercent</mutatedMethod>
  <lineNumber>22</lineNumber>
  <mutator>org.pitest.mutationtest.engine.gregor.mutators.MathMutator</mutator>
  <description>Replaced integer addition with subtraction</description>
</mutation>
</mutations>""",
                encoding="utf-8",
            )
            report = parse_mutations_xml(path)
            self.assertEqual(2, report.total)
            self.assertEqual(1, report.killed)
            self.assertEqual(1, report.survived)
            self.assertAlmostEqual(0.5, report.mutation_score)
            self.assertEqual(1, len(report.survived_mutations))
            guidance = mutation_type_guidance(report, target_class="edu.course.demo.DiscountCalculator")
            self.assertIn("numeric-formula", guidance)
            self.assertIn("Assert exact BigDecimal amounts", guidance)

    def test_parse_jacoco_counters(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "jacoco.xml"
            path.write_text(
                """<report name="demo">
<counter type="LINE" missed="2" covered="8"/>
<counter type="BRANCH" missed="3" covered="1"/>
</report>""",
                encoding="utf-8",
            )
            report = parse_jacoco_xml(path)
            self.assertAlmostEqual(0.8, report.counters["LINE"].ratio)
            self.assertAlmostEqual(0.25, report.counters["BRANCH"].ratio)

    def test_static_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            test_dir = root / "src" / "test" / "java" / "edu" / "course" / "demo"
            test_dir.mkdir(parents=True)
            (test_dir / "DiscountCalculatorTest.java").write_text(
                """package edu.course.demo;
import org.junit.Test;
import static org.junit.Assert.assertEquals;
public class DiscountCalculatorTest {
  @Test public void vipCustomerGetsFreeShipping() {
    assertEquals(true, true);
  }
  @Test public void test0() {
    System.out.println("debug");
  }
}
""",
                encoding="utf-8",
            )
            metrics = compute_static_metrics(root)
            self.assertEqual(1, metrics.test_files)
            self.assertEqual(2, metrics.test_methods)
            self.assertEqual(1, metrics.assertions)
            self.assertGreater(metrics.assertion_strength_score, 0)
            self.assertEqual(1, metrics.generated_style_names)
            self.assertEqual(1, metrics.smell_count)


if __name__ == "__main__":
    unittest.main()
