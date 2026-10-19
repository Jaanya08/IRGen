"""
Unit tests for the IRGen Three-Address Code (TAC) interpreter.

Tests execution of expressions, conditionals, loops, nested constructs,
and runtime error conditions (undefined variable, division by zero, step limit exceeded).
"""

import unittest
from irgen.lexer import tokenize
from irgen.parser import Parser
from irgen.ir_generator import IRGenerator
from irgen.interpreter import run_tac


class TestInterpreter(unittest.TestCase):
    """Test suite covering the execution of Three-Address Code via run_tac."""

    def compile_to_tac(self, source_code):
        """
        Compile source code to a list of TAC instruction lines using the IRGen pipeline.

        Args:
            source_code (str): Source code string to compile.

        Returns:
            list of str: List of TAC instruction lines.
        """
        tokens = tokenize(source_code)
        ast = Parser(tokens).parse()
        generator = IRGenerator()
        generator.generate(ast)
        return generator.get_ir()

    def test_arithmetic_expression(self):
        """Test TAC execution for 'x = a + b * c;' with a=2, b=3, c=4 producing x=14."""
        tac = self.compile_to_tac("x = a + b * c;")
        initial_env = {"a": 2, "b": 3, "c": 4}
        final_env = run_tac(tac, initial_env)
        self.assertEqual(final_env["x"], 14)
        # Ensure initial env was not modified
        self.assertEqual(initial_env, {"a": 2, "b": 3, "c": 4})

    def test_while_loop(self):
        """Test TAC execution for 'while (a < b) { a = a + 1; }' with a=0, b=3 producing a=3."""
        tac = self.compile_to_tac("while (a < b) { a = a + 1; }")
        final_env = run_tac(tac, {"a": 0, "b": 3})
        self.assertEqual(final_env["a"], 3)

    def test_if_else(self):
        """Test TAC execution for if-else branching with both true and false paths."""
        tac = self.compile_to_tac("if (a > b) { x = a; } else { x = b; }")
        # True branch: a=5, b=2 -> x=5
        env_true = run_tac(tac, {"a": 5, "b": 2})
        self.assertEqual(env_true["x"], 5)
        # False branch: a=1, b=2 -> x=2
        env_false = run_tac(tac, {"a": 1, "b": 2})
        self.assertEqual(env_false["x"], 2)

    def test_nested_while_if(self):
        """Test TAC execution for nested while/if with a=0, b=5 producing x=4 and a=5."""
        tac = self.compile_to_tac("while (a < b) { if (a > 2) { x = a; } a = a + 1; }")
        final_env = run_tac(tac, {"a": 0, "b": 5})
        self.assertEqual(final_env["x"], 4)
        self.assertEqual(final_env["a"], 5)

    def test_undefined_variable_raises_name_error(self):
        """Test NameError is raised when an unset variable is referenced during TAC execution."""
        tac = self.compile_to_tac("x = a + 1;")
        with self.assertRaises(NameError):
            run_tac(tac, {})

    def test_division_by_zero_raises_zero_division_error(self):
        """Test ZeroDivisionError is raised when dividing by zero in TAC execution."""
        tac = self.compile_to_tac("x = a / b;")
        with self.assertRaises(ZeroDivisionError):
            run_tac(tac, {"a": 10, "b": 0})

    def test_infinite_loop_raises_runtime_error(self):
        """Test RuntimeError('Step limit exceeded') is raised when a loop exceeds max_steps."""
        tac = self.compile_to_tac("while (1 < 2) { a = a + 1; }")
        with self.assertRaises(RuntimeError):
            run_tac(tac, {"a": 0}, max_steps=500)


if __name__ == "__main__":
    unittest.main()
