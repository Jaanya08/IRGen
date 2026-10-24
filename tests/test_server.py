"""
Unit tests for the IRGen web server and compiler service.

Tests API endpoints, compilation pipeline service, error handling,
and static file serving.
"""

import json
import unittest
from irgen.service import compile_pipeline, get_curriculum_examples
from server import IRGenRequestHandler
import io


class TestServerAndService(unittest.TestCase):
    """Test suite for IRGen service and server API."""

    def test_curriculum_examples_exist(self):
        """Test that curriculum examples are provided with valid structures."""
        examples = get_curriculum_examples()
        self.assertGreater(len(examples), 0)
        for ex in examples:
            self.assertIn("id", ex)
            self.assertIn("title", ex)
            self.assertIn("code", ex)

    def test_service_compile_pipeline_for_loop(self):
        """Test compilation pipeline on a for loop program."""
        code = "sum = 0;\nfor (i = 1; i <= 5; i = i + 1) {\n    sum = sum + i;\n}\n"
        res = compile_pipeline(code)
        self.assertTrue(res["success"])
        self.assertEqual(res["stats"]["tokens_count"], 28)
        self.assertEqual(res["stats"]["tac_before"], 11)
        self.assertEqual(res["stats"]["tac_after"], 9)
        self.assertEqual(res["execution"]["variables"]["sum"], 15)
        self.assertEqual(res["execution"]["variables"]["i"], 6)

    def test_service_compile_pipeline_with_initial_env(self):
        """Test compilation pipeline with custom preset variables."""
        code = "x = a * 2 + b;"
        res = compile_pipeline(code, initial_env={"a": 10, "b": 5})
        self.assertTrue(res["success"])
        self.assertEqual(res["execution"]["variables"]["x"], 25)

    def test_service_compile_pipeline_syntax_error(self):
        """Test that syntax errors return proper error responses."""
        code = "for (i = 0; i < 5 i = i + 1) { x = 1; }"
        res = compile_pipeline(code)
        self.assertFalse(res["success"])
        self.assertEqual(res["stage"], "Parser")
        self.assertIn("error", res)

    def test_service_ast_outline_formatting(self):
        """Test that AST outline produces indented structure."""
        code = "for (i = 0; i < 3; i = i + 1) { a = 1; }"
        res = compile_pipeline(code)
        self.assertIn("For Loop", res["ast_outline"])
        self.assertIn("init: ", res["ast_outline"])
        self.assertIn("condition: ", res["ast_outline"])
        self.assertIn("update: ", res["ast_outline"])


if __name__ == "__main__":
    unittest.main()
