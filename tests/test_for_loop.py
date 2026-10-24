"""
Unit tests for IRGen for loop functionality.

Covers lexing, parsing, AST serialization, TAC generation, optimization,
assembly code generation, interpreter execution, and syntax error handling
for 'for' loops.
"""

import unittest
from irgen.lexer import tokenize
from irgen.parser import Parser
from irgen.ir_generator import IRGenerator
from irgen.ast_nodes import For, Assignment, Identifier, Number, BinaryExpression, Block
from irgen.interpreter import run_tac
from irgen.optimizer import optimize
from irgen.codegen import generate_asm


class TestForLoop(unittest.TestCase):
    """Test suite for for loop construct in IRGen."""

    def generate_tac(self, code):
        """Run lexer, parser, and IR generator to produce TAC instruction lines."""
        tokens = tokenize(code)
        parser = Parser(tokens)
        ast = parser.parse()
        irgen = IRGenerator()
        irgen.generate(ast)
        return irgen.get_ir()

    def test_lexer_for_keyword(self):
        """Test that 'for' is recognized as a KEYWORD and 'formula' as an ID."""
        tokens = tokenize("for formula for_i")
        self.assertEqual(tokens, [
            ("KEYWORD", "for"),
            ("ID", "formula"),
            ("ID", "for_i"),
        ])

    def test_ast_for_node_to_dict(self):
        """Test that For AST node correctly serializes to dict."""
        code = "for (i = 0; i < 5; i = i + 1) { a = a + i; }"
        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        stmt = ast.statements[0]
        self.assertIsInstance(stmt, For)
        d = stmt.to_dict()
        self.assertEqual(d["node"], "For")
        self.assertEqual(d["init"]["node"], "Assignment")
        self.assertEqual(d["init"]["name"], "i")
        self.assertEqual(d["condition"]["node"], "BinaryExpression")
        self.assertEqual(d["condition"]["operator"], "<")
        self.assertEqual(d["update"]["node"], "Assignment")
        self.assertEqual(d["body"]["node"], "Block")
        self.assertEqual(repr(stmt), f"For({stmt.init}, {stmt.condition}, {stmt.update}, {stmt.body})")

    def test_basic_for_loop_tac(self):
        """Test standard TAC generation for a for loop."""
        code = "for (i = 0; i < 5; i = i + 1) { a = a + i; }"
        expected = [
            "i = 0",
            "L1:",
            "t1 = i < 5",
            "ifFalse t1 goto L2",
            "t2 = a + i",
            "a = t2",
            "t3 = i + 1",
            "i = t3",
            "goto L1",
            "L2:",
        ]
        self.assertEqual(self.generate_tac(code), expected)

    def test_for_loop_omitted_init(self):
        """Test TAC generation when init is omitted in for loop."""
        code = "for (; i < 5; i = i + 1) { a = a + 1; }"
        expected = [
            "L1:",
            "t1 = i < 5",
            "ifFalse t1 goto L2",
            "t2 = a + 1",
            "a = t2",
            "t3 = i + 1",
            "i = t3",
            "goto L1",
            "L2:",
        ]
        self.assertEqual(self.generate_tac(code), expected)

    def test_for_loop_omitted_update(self):
        """Test TAC generation when update is omitted in for loop."""
        code = "for (i = 0; i < 5;) { i = i + 1; }"
        expected = [
            "i = 0",
            "L1:",
            "t1 = i < 5",
            "ifFalse t1 goto L2",
            "t2 = i + 1",
            "i = t2",
            "goto L1",
            "L2:",
        ]
        self.assertEqual(self.generate_tac(code), expected)

    def test_for_loop_with_nested_if(self):
        """Test TAC generation for a for loop containing an if statement."""
        code = "for (i = 0; i < 10; i = i + 1) { if (i > 5) { sum = sum + i; } }"
        expected = [
            "i = 0",
            "L1:",
            "t1 = i < 10",
            "ifFalse t1 goto L2",
            "t2 = i > 5",
            "ifFalse t2 goto L3",
            "t3 = sum + i",
            "sum = t3",
            "L3:",
            "t4 = i + 1",
            "i = t4",
            "goto L1",
            "L2:",
        ]
        self.assertEqual(self.generate_tac(code), expected)

    def test_nested_for_loops(self):
        """Test TAC generation for nested for loops."""
        code = "for (i = 0; i < 2; i = i + 1) { for (j = 0; j < 3; j = j + 1) { count = count + 1; } }"
        expected = [
            "i = 0",
            "L1:",
            "t1 = i < 2",
            "ifFalse t1 goto L2",
            "j = 0",
            "L3:",
            "t2 = j < 3",
            "ifFalse t2 goto L4",
            "t3 = count + 1",
            "count = t3",
            "t4 = j + 1",
            "j = t4",
            "goto L3",
            "L4:",
            "t5 = i + 1",
            "i = t5",
            "goto L1",
            "L2:",
        ]
        self.assertEqual(self.generate_tac(code), expected)

    def test_interpreter_execution(self):
        """Test that the interpreter correctly computes the results of a for loop."""
        code = "sum = 0; for (i = 1; i <= 5; i = i + 1) { sum = sum + i; }"
        tac = self.generate_tac(code)
        env = run_tac(tac)
        self.assertEqual(env["sum"], 15)
        self.assertEqual(env["i"], 6)

    def test_nested_interpreter_execution(self):
        """Test interpreter execution of nested for loops."""
        code = "count = 0; for (i = 0; i < 3; i = i + 1) { for (j = 0; j < 4; j = j + 1) { count = count + 1; } }"
        tac = self.generate_tac(code)
        env = run_tac(tac)
        self.assertEqual(env["count"], 12)
        self.assertEqual(env["i"], 3)
        self.assertEqual(env["j"], 4)

    def test_optimizer_on_for_loop(self):
        """Test that optimizer runs cleanly on TAC containing a for loop."""
        code = "for (i = 0; i < 5; i = i + 1) { c = 2 * 3; sum = sum + c; }"
        tac = self.generate_tac(code)
        opt_tac, log = optimize(tac)
        # Constant folding should turn 2 * 3 into 6
        self.assertIn("c = 6", opt_tac)
        # Condition should be preserved
        self.assertTrue(any("i < 5" in line for line in opt_tac))
        # Loop execution of optimized TAC should produce identical values
        env_original = run_tac(tac, {"sum": 0})
        env_opt = run_tac(opt_tac, {"sum": 0})
        self.assertEqual(env_original["sum"], env_opt["sum"])
        self.assertEqual(env_original["sum"], 30)

    def test_codegen_on_for_loop(self):
        """Test assembly generation from for loop TAC."""
        code = "for (i = 0; i < 3; i = i + 1) { a = a + 1; }"
        tac = self.generate_tac(code)
        asm = generate_asm(tac)
        self.assertIn("L1:", asm)
        self.assertIn("L2:", asm)
        self.assertIn("JMP L1", asm)
        self.assertTrue(any("JZ" in line for line in asm))
        self.assertTrue(any("CMPLT" in line for line in asm))

    def test_syntax_errors(self):
        """Test clear SyntaxError exceptions for malformed for loop syntax."""
        # Missing opening paren
        with self.assertRaises(SyntaxError):
            tokenize_and_parse = Parser(tokenize("for i = 0; i < 5; i = i + 1) { a = 1; }")).parse()

        # Missing closing paren
        with self.assertRaises(SyntaxError):
            tokenize_and_parse = Parser(tokenize("for (i = 0; i < 5; i = i + 1 { a = 1; }")).parse()

        # Missing semicolon in loop header
        with self.assertRaises(SyntaxError):
            tokenize_and_parse = Parser(tokenize("for (i = 0 i < 5; i = i + 1) { a = 1; }")).parse()

        # Missing body block braces
        with self.assertRaises(SyntaxError):
            tokenize_and_parse = Parser(tokenize("for (i = 0; i < 5; i = i + 1) a = 1;")).parse()


if __name__ == "__main__":
    unittest.main()
