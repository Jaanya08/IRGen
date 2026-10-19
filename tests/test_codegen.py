"""
Unit tests for IRGen code generator (Phase 3).

Tests cover:
  1. Exact 10-line assembly for 'x = a + b * c;'.
  2. Exact 15-line assembly for 'while (a < b) { a = a + 1; }' (unoptimized).
  3. Integer literals (positive and negative) are formatted as immediates (#N).
  4. All six relational operators map to the correct CMP opcode.
  5. An unknown operator raises ValueError.
"""

import unittest

from irgen.codegen import generate_asm
from irgen.ir_generator import IRGenerator
from irgen.lexer import tokenize
from irgen.parser import Parser
from irgen.tac import Instruction


# ---------------------------------------------------------------------------
# Shared pipeline helper
# ---------------------------------------------------------------------------

def _compile(code):
    """
    Run the full front-end pipeline on *code* and return the TAC lines.

    Args:
        code (str): Source program string.

    Returns:
        list of str: TAC instruction strings from IRGenerator.
    """
    tokens = tokenize(code)
    ast = Parser(tokens).parse()
    gen = IRGenerator()
    gen.generate(ast)
    return gen.get_ir()


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class TestCodegenExactAssembly(unittest.TestCase):
    """Verify exact assembly output for specific programs."""

    def test_assignment_with_nested_multiply(self):
        """
        'x = a + b * c;' must generate exactly 10 assembly lines:
          LOAD R1, b
          LOAD R2, c
          MUL R1, R2
          STORE t1, R1
          LOAD R1, a
          LOAD R2, t1
          ADD R1, R2
          STORE t2, R1
          LOAD R1, t2
          STORE x, R1
        """
        tac = _compile("x = a + b * c;")
        asm = generate_asm(tac)
        expected = [
            "LOAD R1, b",
            "LOAD R2, c",
            "MUL R1, R2",
            "STORE t1, R1",
            "LOAD R1, a",
            "LOAD R2, t1",
            "ADD R1, R2",
            "STORE t2, R1",
            "LOAD R1, t2",
            "STORE x, R1",
        ]
        self.assertEqual(asm, expected)

    def test_while_loop_unoptimized(self):
        """
        'while (a < b) { a = a + 1; }' (unoptimized TAC) must generate
        exactly 15 assembly lines:
          L1:
          LOAD R1, a
          LOAD R2, b
          CMPLT R1, R2
          STORE t1, R1
          LOAD R1, t1
          JZ R1, L2
          LOAD R1, a
          LOAD R2, #1
          ADD R1, R2
          STORE t2, R1
          LOAD R1, t2
          STORE a, R1
          JMP L1
          L2:
        """
        tac = _compile("while (a < b) { a = a + 1; }")
        asm = generate_asm(tac)
        expected = [
            "L1:",
            "LOAD R1, a",
            "LOAD R2, b",
            "CMPLT R1, R2",
            "STORE t1, R1",
            "LOAD R1, t1",
            "JZ R1, L2",
            "LOAD R1, a",
            "LOAD R2, #1",
            "ADD R1, R2",
            "STORE t2, R1",
            "LOAD R1, t2",
            "STORE a, R1",
            "JMP L1",
            "L2:",
        ]
        self.assertEqual(asm, expected)


class TestCodegenLiterals(unittest.TestCase):
    """Integer literals must be emitted as immediate operands prefixed with #."""

    def test_positive_literal_copy(self):
        """
        'x = 6' (a copy instruction with a literal source) must emit:
          LOAD R1, #6
          STORE x, R1
        The '#' prefix signals an immediate value to the machine.
        """
        asm = generate_asm(["x = 6"])
        self.assertEqual(asm, ["LOAD R1, #6", "STORE x, R1"])

    def test_negative_literal_as_left_operand(self):
        """
        't1 = -3 + a' must emit LOAD R1, #-3 (negative immediate) as the
        first instruction, confirming that _format_operand handles negative
        integer strings correctly.
        """
        asm = generate_asm(["t1 = -3 + a"])
        self.assertEqual(asm[0], "LOAD R1, #-3")

    def test_zero_literal(self):
        """
        'x = 0' must emit LOAD R1, #0 — zero is an integer literal too.
        """
        asm = generate_asm(["x = 0"])
        self.assertEqual(asm, ["LOAD R1, #0", "STORE x, R1"])

    def test_variable_is_not_immediate(self):
        """
        'x = a' must emit LOAD R1, a (no '#' prefix) because 'a' is a
        memory variable, not an integer literal.
        """
        asm = generate_asm(["x = a"])
        self.assertEqual(asm, ["LOAD R1, a", "STORE x, R1"])


class TestCodegenRelationalOpcodes(unittest.TestCase):
    """Each relational TAC operator must map to exactly the right CMP opcode."""

    def _asm_for_binary(self, op):
        """
        Return the assembly lines for a binary instruction 't1 = a OP b'.

        Args:
            op (str): Relational operator string.

        Returns:
            list of str: Assembly instruction strings.
        """
        instr = Instruction(kind="binary", dst="t1", left="a", op=op, right="b")
        return generate_asm([instr])

    def test_lt_maps_to_cmplt(self):
        """'<' must produce the CMPLT opcode."""
        asm = self._asm_for_binary("<")
        self.assertIn("CMPLT R1, R2", asm)

    def test_gt_maps_to_cmpgt(self):
        """'>' must produce the CMPGT opcode."""
        asm = self._asm_for_binary(">")
        self.assertIn("CMPGT R1, R2", asm)

    def test_le_maps_to_cmple(self):
        """'<=' must produce the CMPLE opcode."""
        asm = self._asm_for_binary("<=")
        self.assertIn("CMPLE R1, R2", asm)

    def test_ge_maps_to_cmpge(self):
        """'>=' must produce the CMPGE opcode."""
        asm = self._asm_for_binary(">=")
        self.assertIn("CMPGE R1, R2", asm)

    def test_eq_maps_to_cmpeq(self):
        """'==' must produce the CMPEQ opcode."""
        asm = self._asm_for_binary("==")
        self.assertIn("CMPEQ R1, R2", asm)

    def test_ne_maps_to_cmpne(self):
        """'!=' must produce the CMPNE opcode."""
        asm = self._asm_for_binary("!=")
        self.assertIn("CMPNE R1, R2", asm)

    def test_add_maps_to_add(self):
        """'+' must produce the ADD opcode."""
        asm = self._asm_for_binary("+")
        self.assertIn("ADD R1, R2", asm)

    def test_sub_maps_to_sub(self):
        """'-' must produce the SUB opcode."""
        asm = self._asm_for_binary("-")
        self.assertIn("SUB R1, R2", asm)

    def test_mul_maps_to_mul(self):
        """'*' must produce the MUL opcode."""
        asm = self._asm_for_binary("*")
        self.assertIn("MUL R1, R2", asm)

    def test_div_maps_to_div(self):
        """'/' must produce the DIV opcode."""
        asm = self._asm_for_binary("/")
        self.assertIn("DIV R1, R2", asm)


class TestCodegenControlFlow(unittest.TestCase):
    """goto, ifFalse, and label instructions map to the right assembly forms."""

    def test_goto_becomes_jmp(self):
        """'goto L2' must emit exactly 'JMP L2'."""
        asm = generate_asm(["goto L2"])
        self.assertEqual(asm, ["JMP L2"])

    def test_iffalse_becomes_jz(self):
        """
        'ifFalse t1 goto L1' must emit:
          LOAD R1, t1
          JZ R1, L1
        """
        asm = generate_asm(["ifFalse t1 goto L1"])
        self.assertEqual(asm, ["LOAD R1, t1", "JZ R1, L1"])

    def test_label_is_preserved(self):
        """'L1:' must be emitted unchanged as a label line."""
        asm = generate_asm(["L1:"])
        self.assertEqual(asm, ["L1:"])


class TestCodegenErrors(unittest.TestCase):
    """Unknown operators must raise ValueError."""

    def test_unknown_operator_raises(self):
        """
        A binary Instruction with operator '%' (not in OPCODE_MAP) must raise
        ValueError rather than silently producing wrong assembly.
        """
        instr = Instruction(kind="binary", dst="t1", left="a", op="%", right="b")
        with self.assertRaises(ValueError):
            generate_asm([instr])

    def test_unknown_kind_raises(self):
        """
        An Instruction with an unrecognized kind must raise ValueError.
        This guards against future instruction-kind additions being overlooked.
        """
        instr = Instruction(kind="unknown_kind")
        with self.assertRaises(ValueError):
            generate_asm([instr])


if __name__ == "__main__":
    unittest.main()
