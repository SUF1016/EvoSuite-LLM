import unittest
from pathlib import Path

from mglet.patching import extract_java_files


class PatchingTests(unittest.TestCase):
    def test_extracts_java_block_with_path(self):
        response = """```java
// path: src/test/java/edu/course/demo/DiscountCalculatorLLMEnhancedTest.java
package edu.course.demo;

public class DiscountCalculatorLLMEnhancedTest {
}
```"""
        files = extract_java_files(response)
        self.assertEqual(1, len(files))
        self.assertEqual(
            Path("src/test/java/edu/course/demo/DiscountCalculatorLLMEnhancedTest.java"),
            Path(str(files[0].relative_path).replace("\\", "/")),
        )
        self.assertIn("package edu.course.demo;", files[0].content)

    def test_no_change_returns_empty_list(self):
        self.assertEqual([], extract_java_files("NO_CHANGE"))


if __name__ == "__main__":
    unittest.main()
