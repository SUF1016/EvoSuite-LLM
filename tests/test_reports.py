import unittest

from mglet.reports import render_summary_markdown


class ReportTests(unittest.TestCase):
    def test_renders_summary_table(self):
        markdown = render_summary_markdown(
            {
                "project_dir": "demo",
                "targets": ["edu.course.demo.DiscountCalculator"],
                "iterations": 1,
                "evaluations": [
                    {
                        "label": "evosuite-baseline",
                        "maven_test_ok": True,
                        "flaky_failures": 0,
                        "coverage": {
                            "counters": {
                                "LINE": {"ratio": 0.8},
                                "BRANCH": {"ratio": 0.5},
                            }
                        },
                        "pit": {"mutation_score": 0.4},
                        "static_metrics": {"assertions": 3, "readability_score": 70.0},
                    }
                ],
            }
        )
        self.assertIn("| evosuite-baseline | yes | 80.00% | 50.00% | 40.00% | 3 |", markdown)


if __name__ == "__main__":
    unittest.main()
