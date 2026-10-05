"""
Unit tests for IRGen (Phase 1).

Tests the complete Phase 1 pipeline (Lexer -> Parser -> AST -> IRGenerator)
against standard test cases defined in AGENTS.md and error scenarios.
"""

import unittest
from irgen.lexer import tokenize
from irgen.parser import Parser
from irgen.ir_generator import IRGenerator


class TestIRGenPhase1(unittest.TestCase):
    """Test suite covering Phase 1 expression parsing and TAC generation."""

    def generate_tac(self, code):
        """
        Helper method to run tokenization, parsing, and IR generation on input code.

        Args:
            code (str): Source code statement string.

        Returns:
            list of str: List of TAC instruction strings.
        """
        tokens = tokenize(code)
        parser = Parser(tokens)
        ast = parser.parse()
        irgen = IRGenerator()
        irgen.generate(ast)
        return irgen.get_ir()

    def test_case_1_simple_addition(self):
        """Test TAC generation for 'x = a + b;'."""
        code = "x = a + b;"
        expected = ["t1 = a + b", "x = t1"]
        self.assertEqual(self.generate_tac(code), expected)

    def test_case_2_precedence_mult_then_add(self):
        """Test TAC generation for 'x = a * b + c;'."""
        code = "x = a * b + c;"
        expected = ["t1 = a * b", "t2 = t1 + c", "x = t2"]
        self.assertEqual(self.generate_tac(code), expected)

    def test_case_3_parentheses_override(self):
        """Test TAC generation for 'x = (a + b) * c;'."""
        code = "x = (a + b) * c;"
        expected = ["t1 = a + b", "t2 = t1 * c", "x = t2"]
        self.assertEqual(self.generate_tac(code), expected)

    def test_case_4_complex_expression(self):
        """Test TAC generation for 'result = a + b * c - d;'."""
        code = "result = a + b * c - d;"
        expected = ["t1 = b * c", "t2 = a + t1", "t3 = t2 - d", "result = t3"]
        self.assertEqual(self.generate_tac(code), expected)

    def test_error_unexpected_character(self):
        """Test SyntaxError raised on unexpected input character 'x = a $ b;'."""
        code = "x = a $ b;"
        with self.assertRaises(SyntaxError):
            tokenize(code)

    def test_error_missing_semicolon(self):
        """Test SyntaxError raised when semicolon is missing 'x = a + b'."""
        code = "x = a + b"
        tokens = tokenize(code)
        parser = Parser(tokens)
        with self.assertRaises(SyntaxError):
            parser.parse()

    def test_error_unbalanced_parenthesis(self):
        """Test SyntaxError raised on unbalanced parenthesis 'x = (a + b;'."""
        code = "x = (a + b;"
        tokens = tokenize(code)
        parser = Parser(tokens)
        with self.assertRaises(SyntaxError):
            parser.parse()


if __name__ == "__main__":
    unittest.main()
