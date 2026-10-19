"""
Assembly code generator for IRGen.

Translates Three-Address Code (TAC) into assembly instructions for an imaginary
register machine featuring memory variables and two scratch registers, R1 and R2.
"""

from irgen.tac import Instruction, parse_tac

# Mapping of TAC binary and relational operators to assembly opcodes
OPCODE_MAP = {
    "+": "ADD",
    "-": "SUB",
    "*": "MUL",
    "/": "DIV",
    "<": "CMPLT",
    ">": "CMPGT",
    "<=": "CMPLE",
    ">=": "CMPGE",
    "==": "CMPEQ",
    "!=": "CMPNE",
}


def _format_operand(val):
    """
    Format a TAC operand for assembly.

    Integer literals (including negative integers) are formatted as immediates
    with a '#' prefix (e.g., '#6', '#-3'). Any other operand represents a
    variable located in memory and is returned as-is.

    Args:
        val (str): The TAC operand string.

    Returns:
        str: Formatted assembly operand string.
    """
    try:
        int(val)
        return f"#{val}"
    except (ValueError, TypeError):
        return str(val)


def generate_asm(lines):
    """
    Translate Three-Address Code (TAC) into assembly for an imaginary register machine.

    Target machine architecture:
    - Variables live in memory.
    - Two scratch registers: R1 and R2.
    - Immediates are prefixed with '#' (e.g. #6, #-3).
    - Opcodes:
        Arithmetic: ADD, SUB, MUL, DIV
        Comparison: CMPLT, CMPGT, CMPLE, CMPGE, CMPEQ, CMPNE (sets R1 to 1 or 0)
        Control flow: JZ (jump if zero), JMP (unconditional jump)
        Data movement: LOAD, STORE

    Instruction mapping:
        t1 = b * c          ->  LOAD R1, b
                                LOAD R2, c
                                MUL R1, R2
                                STORE t1, R1

        x = t1              ->  LOAD R1, t1
                                STORE x, R1

        x = 6               ->  LOAD R1, #6
                                STORE x, R1

        t1 = a < b          ->  LOAD R1, a
                                LOAD R2, b
                                CMPLT R1, R2
                                STORE t1, R1

        ifFalse t1 goto L1  ->  LOAD R1, t1
                                JZ R1, L1

        goto L2             ->  JMP L2

        L1:                 ->  L1:

    Args:
        lines (list of str or str or list of Instruction): TAC input lines or objects.

    Returns:
        list of str: List of assembly instruction strings.

    Raises:
        ValueError: If an unknown operator or instruction kind is encountered.
    """
    if isinstance(lines, list) and lines and isinstance(lines[0], Instruction):
        instrs = lines
    else:
        instrs = parse_tac(lines)

    asm = []
    for instr in instrs:
        if instr.kind == "binary":
            if instr.op not in OPCODE_MAP:
                raise ValueError(f"Unknown operator: '{instr.op}'")
            opcode = OPCODE_MAP[instr.op]
            asm.append(f"LOAD R1, {_format_operand(instr.left)}")
            asm.append(f"LOAD R2, {_format_operand(instr.right)}")
            asm.append(f"{opcode} R1, R2")
            asm.append(f"STORE {instr.dst}, R1")
        elif instr.kind == "copy":
            asm.append(f"LOAD R1, {_format_operand(instr.src)}")
            asm.append(f"STORE {instr.dst}, R1")
        elif instr.kind == "ifFalse":
            asm.append(f"LOAD R1, {_format_operand(instr.cond)}")
            asm.append(f"JZ R1, {instr.target}")
        elif instr.kind == "goto":
            asm.append(f"JMP {instr.target}")
        elif instr.kind == "label":
            asm.append(f"{instr.label}:")
        else:
            raise ValueError(f"Unknown instruction kind: '{instr.kind}'")

    return asm
