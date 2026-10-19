"""
Unit tests for IRGen optimizer (Phase 3).

Tests cover:
  1. Exact TAC from the five Expected-results rows in AGENTS.md.
  2. Extra exact cases (CSE invalidation, if/else constant folding).
  3. Loop safety: variable operand not replaced by literal.
  4. Idempotence: running optimize twice gives the same result.
  5. Log shape and empty-log case.
  6. Semantic equivalence: original TAC and optimized TAC yield identical
     user-variable values for a range of starting environments.
  7. Random bonus: 50 seeded straight-line programs checked for equivalence.
"""

import random
import unittest

from irgen.interpreter import run_tac
from irgen.ir_generator import IRGenerator
from irgen.lexer import tokenize
from irgen.optimizer import optimize
from irgen.parser import Parser
from irgen.tac import is_temp


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


def _user_vars(env):
    """
    Filter *env* to keep only user variables (non-temporaries).

    Args:
        env (dict): Variable name -> integer value mapping.

    Returns:
        dict: Subset of *env* whose keys satisfy ``not is_temp(k)``.
    """
    return {k: v for k, v in env.items() if not is_temp(k)}


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class TestOptimizerExpectedResults(unittest.TestCase):
    """Test the five exact Expected-results rows from the AGENTS.md table."""

    def test_case1_constant_fold_and_propagate(self):
        """
        'x = 2 * 3 + a;' must optimize to exactly ['x = 6 + a'].

        2*3 folds to 6, propagation + copy-fusion collapses the rest.
        """
        tac = _compile("x = 2 * 3 + a;")
        opt, _ = optimize(tac)
        self.assertEqual(opt, ["x = 6 + a"])

    def test_case2_algebraic_simplification(self):
        """
        'x = a * 1 + 0;' must optimize to exactly ['x = a'].

        a*1 simplifies to a, a+0 simplifies to a, copy-fusion finishes.
        """
        tac = _compile("x = a * 1 + 0;")
        opt, _ = optimize(tac)
        self.assertEqual(opt, ["x = a"])

    def test_case3_constant_propagation(self):
        """
        'a = 5; b = a * 2;' must optimize to exactly ['a = 5', 'b = 10'].

        a=5 propagated into a*2, fold to 10, copy-fusion merges.
        """
        tac = _compile("a = 5; b = a * 2;")
        opt, _ = optimize(tac)
        self.assertEqual(opt, ["a = 5", "b = 10"])

    def test_case4_common_subexpression_elimination(self):
        """
        'x = a * b; y = a * b;' must optimize to
        ['t1 = a * b', 'x = t1', 'y = t1'].

        CSE keeps the first computation and replaces the second with a copy.
        """
        tac = _compile("x = a * b; y = a * b;")
        opt, _ = optimize(tac)
        self.assertEqual(opt, ["t1 = a * b", "x = t1", "y = t1"])

    def test_case5_loop_with_constant_inside(self):
        """
        'while (a < b) { x = 2 * 3; a = a + 1; }' must optimize to the
        loop body with 2*3 folded to 6 and the temp for a+1 fused away.

        Expected:
          L1:
          t1 = a < b
          ifFalse t1 goto L2
          x = 6
          a = a + 1
          goto L1
          L2:
        """
        tac = _compile("while (a < b) { x = 2 * 3; a = a + 1; }")
        opt, _ = optimize(tac)
        expected = [
            "L1:",
            "t1 = a < b",
            "ifFalse t1 goto L2",
            "x = 6",
            "a = a + 1",
            "goto L1",
            "L2:",
        ]
        self.assertEqual(opt, expected)


class TestOptimizerExtraCases(unittest.TestCase):
    """Extra exact-TAC cases beyond the AGENTS.md table."""

    def test_cse_invalidated_by_assignment(self):
        """
        'x = a * b; a = 3; y = a * b;' — the second a*b is NOT the same
        subexpression as the first because 'a' was reassigned.

        Expected: ['x = a * b', 'a = 3', 'y = 3 * b']

        CSE keeps x = a * b, then a = 3 invalidates the table entry.
        Propagation substitutes a -> 3 in the last expression; no CSE reuse.
        """
        tac = _compile("x = a * b; a = 3; y = a * b;")
        opt, _ = optimize(tac)
        self.assertEqual(opt, ["x = a * b", "a = 3", "y = 3 * b"])

    def test_constant_fold_in_both_branches(self):
        """
        'if (a > b) { x = 2 * 3; } else { x = 4 * 5; }' —
        both branches contain constant expressions that fold independently.

        Expected TAC contains exactly 'x = 6' in the then-branch and
        'x = 20' in the else-branch, with all labels and jumps preserved.
        """
        tac = _compile("if (a > b) { x = 2 * 3; } else { x = 4 * 5; }")
        opt, _ = optimize(tac)
        # Labels and jumps must be present
        self.assertIn("ifFalse t1 goto L1", opt)
        self.assertIn("goto L2", opt)
        self.assertIn("L1:", opt)
        self.assertIn("L2:", opt)
        # Folded constants in each branch
        self.assertIn("x = 6", opt)
        self.assertIn("x = 20", opt)
        # Verify the t1 condition was kept
        self.assertIn("t1 = a > b", opt)


class TestOptimizerLoopSafety(unittest.TestCase):
    """Optimizer must not incorrectly constant-fold across loop back edges."""

    def test_loop_condition_uses_variable_not_literal(self):
        """
        'a = 0; while (a < 3) { a = a + 1; }' — even though a starts at 0,
        the optimizer must NOT replace 'a' with '0' inside the loop body.

        The optimized TAC must contain a binary instruction between the L1
        label and the ifFalse instruction where at least one operand is 'a'
        (not a literal 3 on both sides), confirming a is still a variable.
        """
        tac = _compile("a = 0; while (a < 3) { a = a + 1; }")
        opt, _ = optimize(tac)

        # Find the L1 label position and the ifFalse position
        l1_idx = opt.index("L1:")
        iffalse_idx = next(
            i for i, line in enumerate(opt) if line.startswith("ifFalse")
        )

        # Collect binary instructions between L1: and the ifFalse
        between = opt[l1_idx + 1: iffalse_idx]
        binary_lines = [line for line in between if "=" in line and "ifFalse" not in line]
        self.assertTrue(
            any("a" in line for line in binary_lines),
            msg=f"Expected variable 'a' in binary instruction between L1 and ifFalse; got: {binary_lines}",
        )


class TestOptimizerIdempotence(unittest.TestCase):
    """Running optimize twice must yield the same result as running it once."""

    PROGRAMS = [
        "x = a + b * c;",
        "x = 2 * 3 + a;",
        "x = a * 1 + 0;",
        "a = 5; b = a * 2;",
        "x = a * b; y = a * b;",
        "x = a * b; a = 3; y = a * b;",
        "if (a > b) { x = 2 * 3; } else { x = 4 * 5; }",
        "while (a < b) { a = a + 1; }",
        "while (a < b) { x = 2 * 3; a = a + 1; }",
        "a = 0; while (a < 3) { a = a + 1; }",
    ]

    def test_idempotence(self):
        """
        For every test program, optimize(optimize(tac)[0])[0] == optimize(tac)[0].

        A fully optimized program should not change on a second pass.
        """
        for src in self.PROGRAMS:
            with self.subTest(src=src):
                tac = _compile(src)
                once, _ = optimize(tac)
                twice, _ = optimize(once)
                self.assertEqual(
                    once,
                    twice,
                    msg=f"Second pass changed the TAC for: {src!r}",
                )


class TestOptimizerLogShape(unittest.TestCase):
    """Each log entry must have the right shape; no-op programs have empty logs."""

    def test_log_entry_keys_and_before_ne_after(self):
        """
        For 'x = 2 * 3 + a;' (which is optimizable), every log entry must
        have exactly the keys 'pass', 'before', 'after', and before != after.
        """
        tac = _compile("x = 2 * 3 + a;")
        _, log = optimize(tac)
        self.assertGreater(len(log), 0, msg="Expected at least one log entry")
        for entry in log:
            with self.subTest(entry=entry):
                self.assertIn("pass", entry)
                self.assertIn("before", entry)
                self.assertIn("after", entry)
                self.assertNotEqual(
                    entry["before"],
                    entry["after"],
                    msg="Log entry recorded when before == after",
                )

    def test_no_log_for_unoptimizable_program(self):
        """
        'x = a + b;' compiles to ['t1 = a + b', 'x = t1'] then copy-fusion
        gives ['x = a + b'].  After that second call, there is nothing more
        to do, so the second optimize() call returns an empty log.
        """
        tac = _compile("x = a + b;")
        once, _ = optimize(tac)
        _, log2 = optimize(once)
        self.assertEqual(log2, [], msg="Already-optimized program should log nothing")

    def test_if_else_with_only_variables_empty_log(self):
        """
        'if (a > b) { x = a; } else { x = b; }' contains no constants to
        fold or simplify, so the log should be empty (or only copy_fusion
        entries at most — but actually copy_fusion cannot fire here either).
        """
        tac = _compile("if (a > b) { x = a; } else { x = b; }")
        _, log = optimize(tac)
        self.assertEqual(log, [])


class TestOptimizerSemanticEquivalence(unittest.TestCase):
    """
    Optimized TAC must produce the same user-variable values as the original.

    For each (program, env) pair the test runs both the original and the
    optimized TAC through the interpreter and compares every user variable
    (those for which is_temp() is False).
    """

    # Programs and environments to test.
    # Each entry: (source_code, [env1, env2, ...])
    CASES = [
        (
            "x = a + b * c;",
            [
                {"a": 1, "b": 2, "c": 3},
                {"a": 0, "b": 0, "c": 0},
                {"a": -1, "b": -2, "c": -3},
                {"a": 100, "b": 0, "c": 99},
            ],
        ),
        (
            "x = 2 * 3 + a;",
            [
                {"a": 0},
                {"a": 5},
                {"a": -7},
                {"a": 1000},
            ],
        ),
        (
            "x = a * 1 + 0;",
            [
                {"a": 0},
                {"a": 4},
                {"a": -4},
                {"a": 999},
            ],
        ),
        (
            "x = (a - 0) * 1 + b * 0;",
            [
                {"a": 0, "b": 0},
                {"a": 5, "b": 10},
                {"a": -3, "b": 7},
                {"a": 1, "b": -1},
            ],
        ),
        (
            "x = a * b; y = a * b;",
            [
                {"a": 3, "b": 4},
                {"a": 0, "b": 100},
                {"a": -2, "b": -5},
                {"a": 1, "b": 1},
            ],
        ),
        (
            "x = a * b; a = 3; y = a * b;",
            [
                {"a": 2, "b": 4},
                {"a": 0, "b": 0},
                {"a": -1, "b": -1},
                {"a": 10, "b": 2},
            ],
        ),
        (
            "a = 5; b = a * 2; c = b - a;",
            [
                {},
                {"extra": 0},
                {"a": 99},   # a gets overwritten; prior value doesn't matter
                {"b": 99},   # b gets overwritten
            ],
        ),
        (
            "if (a > b) { x = 2 * 3; } else { x = 4 * 5; }",
            [
                {"a": 10, "b": 5},
                {"a": 1, "b": 5},
                {"a": 0, "b": 0},
                {"a": -1, "b": -2},
            ],
        ),
        (
            "while (a < b) { a = a + 1; }",
            [
                {"a": 0, "b": 3},
                {"a": -2, "b": 3},
                {"a": 0, "b": 0},   # loop never executes
                {"a": 3, "b": 3},   # loop never executes
            ],
        ),
        (
            "a = 0; while (a < 5) { a = a + 1; s = s + a; }",
            [
                {"s": 0},
                {"s": 10},
                {"s": -5},
                {"s": 100},
            ],
        ),
        (
            "while (a < b) { if (a > 2) { x = a; } a = a + 1; }",
            [
                {"a": 0, "b": 5, "x": 0},
                {"a": 3, "b": 6, "x": 0},
                {"a": 0, "b": 0, "x": 99},   # loop never executes
                {"a": -1, "b": 2, "x": 0},
            ],
        ),
        (
            "while (a < b) { x = 2 * 3; a = a + 1; }",
            [
                {"a": 0, "b": 3, "x": 0},
                {"a": 0, "b": 0, "x": 0},   # loop never executes
                {"a": -3, "b": 0, "x": 0},
                {"a": 1, "b": 4, "x": 99},
            ],
        ),
    ]

    def test_semantic_equivalence(self):
        """
        For every (program, env) pair, the user variables produced by the
        original TAC and the optimized TAC must be identical.
        """
        for src, envs in self.CASES:
            tac = _compile(src)
            opt, _ = optimize(tac)
            for env in envs:
                with self.subTest(src=src, env=env):
                    orig_out = _user_vars(run_tac(tac, env))
                    opt_out = _user_vars(run_tac(opt, env))
                    self.assertEqual(
                        orig_out,
                        opt_out,
                        msg=(
                            f"Semantic mismatch for {src!r} with env={env}.\n"
                            f"  original : {orig_out}\n"
                            f"  optimized: {opt_out}"
                        ),
                    )


class TestOptimizerRandomEquivalence(unittest.TestCase):
    """
    Bonus: 50 seeded random straight-line programs each verified for semantic
    equivalence between original and optimized TAC.
    """

    VARS = ["a", "b", "c"]
    OPS = ["+", "-", "*"]
    LITERALS = [0, 1, 2, 3, 5, 10]

    def _random_operand(self, rng):
        """
        Return a random operand: either a variable name or an integer literal.

        Args:
            rng (random.Random): Random generator instance.

        Returns:
            str: Variable name like 'a' or integer string like '3'.
        """
        if rng.random() < 0.5:
            return rng.choice(self.VARS)
        return str(rng.choice(self.LITERALS))

    def _random_program(self, rng, n_stmts=3):
        """
        Build a random straight-line assignment program with *n_stmts* statements.

        Each statement is ``var = operand op operand;`` over VARS + LITERALS.

        Args:
            rng (random.Random): Random generator instance.
            n_stmts (int): Number of assignment statements.

        Returns:
            str: Source program string.
        """
        stmts = []
        for _ in range(n_stmts):
            dst = rng.choice(self.VARS)
            left = self._random_operand(rng)
            op = rng.choice(self.OPS)
            right = self._random_operand(rng)
            stmts.append(f"{dst} = {left} {op} {right};")
        return " ".join(stmts)

    def test_random_straight_line_equivalence(self):
        """
        Build 50 seeded random straight-line programs and assert that
        running both original and optimized TAC yields the same user-variable
        values in every case.

        Uses a fixed seed (42) for reproducibility.  Division is intentionally
        excluded because division by zero would raise without complicating the
        test runner.
        """
        rng = random.Random(42)
        # Fixed starting environments covering zeros and negatives
        envs = [
            {"a": 0, "b": 0, "c": 0},
            {"a": 1, "b": 2, "c": 3},
            {"a": -1, "b": -2, "c": -3},
            {"a": 10, "b": 5, "c": 0},
        ]

        for trial in range(50):
            src = self._random_program(rng, n_stmts=rng.randint(2, 4))
            with self.subTest(trial=trial, src=src):
                try:
                    tac = _compile(src)
                except SyntaxError:
                    # Skip the rare case where random generation hits a reserved name
                    continue
                opt, _ = optimize(tac)
                for env in envs:
                    orig_out = _user_vars(run_tac(tac, env))
                    opt_out = _user_vars(run_tac(opt, env))
                    self.assertEqual(
                        orig_out,
                        opt_out,
                        msg=(
                            f"Trial {trial}: mismatch for {src!r} env={env}.\n"
                            f"  original : {orig_out}\n"
                            f"  optimized: {opt_out}"
                        ),
                    )


if __name__ == "__main__":
    unittest.main()
