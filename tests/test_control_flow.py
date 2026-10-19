"""
Unit tests for IRGen control flow (Phase 2).

Tests control-flow constructs (if, if-else, while, nesting, sequential statements),
error handling for malformed syntax, and lexer tokenization of relational operators
and keywords.
"""

import unittest
from irgen.lexer import tokenize
from irgen.parser import Parser
from irgen.ir_generator import IRGenerator


class TestControlFlow(unittest.TestCase):
    """Test suite covering Phase 2 control flow TAC generation, error cases, and lexing."""

    def generate_tac(self, code):
        """
        Run the complete pipeline on a source code string and return TAC instruction strings.

        Args:
            code (str): Source code string to process.

        Returns:
            list of str: List of emitted Three-Address Code instructions.
        """
        tokens = tokenize(code)
        parser = Parser(tokens)
        ast = parser.parse()
        irgen = IRGenerator()
        irgen.generate(ast)
        return irgen.get_ir()

    def test_if_else(self):
        """Test TAC generation for an if-else statement."""
        code = "if (a > b) { x = a; } else { x = b; }"
        expected = [
            "t1 = a > b",
            "ifFalse t1 goto L1",
            "x = a",
            "goto L2",
            "L1:",
            "x = b",
            "L2:",
        ]
        self.assertEqual(self.generate_tac(code), expected)

    def test_if_without_else(self):
        """Test TAC generation for an if statement without an else branch."""
        code = "if (a > b) { x = a; }"
        expected = [
            "t1 = a > b",
            "ifFalse t1 goto L1",
            "x = a",
            "L1:",
        ]
        self.assertEqual(self.generate_tac(code), expected)

    def test_while(self):
        """Test TAC generation for a while loop statement."""
        code = "while (a < b) { a = a + 1; }"
        expected = [
            "L1:",
            "t1 = a < b",
            "ifFalse t1 goto L2",
            "t2 = a + 1",
            "a = t2",
            "goto L1",
            "L2:",
        ]
        self.assertEqual(self.generate_tac(code), expected)

    def test_nested_if_inside_while(self):
        """Test TAC generation for an if statement nested inside a while loop."""
        code = "while (a < b) { if (a > 2) { x = a; } a = a + 1; }"
        expected = [
            "L1:",
            "t1 = a < b",
            "ifFalse t1 goto L2",
            "t2 = a > 2",
            "ifFalse t2 goto L3",
            "x = a",
            "L3:",
            "t3 = a + 1",
            "a = t3",
            "goto L1",
            "L2:",
        ]
        self.assertEqual(self.generate_tac(code), expected)

    def test_two_statements_sequence(self):
        """Test TAC generation for multiple sequential statements."""
        code = "x = a + b; y = x * 2;"
        expected = [
            "t1 = a + b",
            "x = t1",
            "t2 = x * 2",
            "y = t2",
        ]
        self.assertEqual(self.generate_tac(code), expected)

    def test_if_else_inside_while(self):
        """Test TAC generation for an if-else statement nested inside a while loop."""
        code = "while (a < b) { if (a > 2) { x = a; } else { x = b; } a = a + 1; }"
        expected = [
            "L1:",
            "t1 = a < b",
            "ifFalse t1 goto L2",
            "t2 = a > 2",
            "ifFalse t2 goto L3",
            "x = a",
            "goto L4",
            "L3:",
            "x = b",
            "L4:",
            "t3 = a + 1",
            "a = t3",
            "goto L1",
            "L2:",
        ]
        self.assertEqual(self.generate_tac(code), expected)

    def test_error_missing_rparen(self):
        """Test SyntaxError is raised when a closing parenthesis is missing in a while condition."""
        code = "while (a < b { a = a + 1; }"
        with self.assertRaises(SyntaxError):
            tokens = tokenize(code)
            Parser(tokens).parse()

    def test_error_missing_block(self):
        """Test SyntaxError is raised when an if statement body is not enclosed in a block."""
        code = "if (a > b) x = a;"
        with self.assertRaises(SyntaxError):
            tokens = tokenize(code)
            Parser(tokens).parse()

    def test_error_missing_rbrace(self):
        """Test SyntaxError is raised when a closing brace is missing from a block."""
        code = "while (a < b) { a = a + 1;"
        with self.assertRaises(SyntaxError):
            tokens = tokenize(code)
            Parser(tokens).parse()

    def test_error_stray_else(self):
        """Test SyntaxError is raised when an else keyword appears without a preceding if."""
        code = "else { x = 1; }"
        with self.assertRaises(SyntaxError):
            tokens = tokenize(code)
            Parser(tokens).parse()

    def test_lexer_relop_two_characters(self):
        """Test that two-character relational operators (>=, ==) are matched as single RELOP tokens."""
        tokens_gte = tokenize(">=")
        self.assertEqual(tokens_gte, [("RELOP", ">=")])
        tokens_eq = tokenize("==")
        self.assertEqual(tokens_eq, [("RELOP", "==")])

    def test_lexer_keywords_and_identifiers(self):
        """Test that if, else, while are lexed as KEYWORD tokens while iffy is lexed as ID."""
        tokens = tokenize("if else while iffy")
        expected = [
            ("KEYWORD", "if"),
            ("KEYWORD", "else"),
            ("KEYWORD", "while"),
            ("ID", "iffy"),
        ]
        self.assertEqual(tokens, expected)


if __name__ == "__main__":
    unittest.main()
