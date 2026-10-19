"""
Interpreter for Three-Address Code (TAC).

This module simulates the execution of Three-Address Code instructions.
It supports variables, integer arithmetic, relational comparisons,
conditional jumps, and unconditional jumps.
"""

from irgen.tac import parse_tac


def _eval_operand(operand, env):
    """
    Evaluate an operand string to an integer value.

    An operand is evaluated as an integer literal if possible;
    otherwise, it is treated as a variable name and looked up in the environment.

    Args:
        operand (str): Number literal string or variable name.
        env (dict): Current variable environment mapping names to integer values.

    Returns:
        int: The evaluated integer value.

    Raises:
        NameError: If operand is a variable name that is not present in env.
    """
    try:
        return int(operand)
    except ValueError:
        if operand not in env:
            raise NameError(f"Variable '{operand}' is not defined")
        return env[operand]


def run_tac(lines, env=None, max_steps=10000):
    """
    Execute Three-Address Code (TAC) and return the final variable environment.

    Args:
        lines (list of str or str): Lines of Three-Address Code instructions.
        env (dict, optional): Initial variable environment. Defaults to None.
        max_steps (int, optional): Maximum execution steps before aborting. Defaults to 10000.

    Returns:
        dict: Final variable environment mapping variable and temporary names to integer values.

    Raises:
        NameError: If an undefined variable is accessed.
        ZeroDivisionError: If division by zero is attempted.
        RuntimeError: If execution exceeds max_steps.
    """
    instructions = parse_tac(lines)

    # Build label to instruction index mapping
    label_map = {}
    for idx, instr in enumerate(instructions):
        if instr.kind == "label":
            label_map[instr.label] = idx

    # Work with an independent copy of the starting environment
    env_copy = dict(env) if env is not None else {}

    pc = 0
    step_count = 0
    total_instrs = len(instructions)

    while pc < total_instrs:
        step_count += 1
        if step_count > max_steps:
            raise RuntimeError("Step limit exceeded")

        instr = instructions[pc]

        if instr.kind == "label":
            pc += 1

        elif instr.kind == "goto":
            if instr.target not in label_map:
                raise KeyError(f"Undefined target label '{instr.target}'")
            pc = label_map[instr.target]

        elif instr.kind == "ifFalse":
            cond_val = _eval_operand(instr.cond, env_copy)
            if cond_val == 0:
                if instr.target not in label_map:
                    raise KeyError(f"Undefined target label '{instr.target}'")
                pc = label_map[instr.target]
            else:
                pc += 1

        elif instr.kind == "copy":
            val = _eval_operand(instr.src, env_copy)
            env_copy[instr.dst] = val
            pc += 1

        elif instr.kind == "binary":
            left_val = _eval_operand(instr.left, env_copy)
            right_val = _eval_operand(instr.right, env_copy)
            op = instr.op

            if op == "+":
                result = left_val + right_val
            elif op == "-":
                result = left_val - right_val
            elif op == "*":
                result = left_val * right_val
            elif op == "/":
                if right_val == 0:
                    raise ZeroDivisionError("division by zero")
                result = left_val // right_val
            elif op == "<":
                result = 1 if left_val < right_val else 0
            elif op == ">":
                result = 1 if left_val > right_val else 0
            elif op == "<=":
                result = 1 if left_val <= right_val else 0
            elif op == ">=":
                result = 1 if left_val >= right_val else 0
            elif op == "==":
                result = 1 if left_val == right_val else 0
            elif op == "!=":
                result = 1 if left_val != right_val else 0
            else:
                raise ValueError(f"Unsupported binary operator: '{op}'")

            env_copy[instr.dst] = result
            pc += 1

        else:
            raise ValueError(f"Unknown instruction kind: '{instr.kind}'")

    return env_copy
