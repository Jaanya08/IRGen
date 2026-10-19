"""
Three-Address Code (TAC) representation and parsing utilities.

This module provides data structures and helper functions to parse, represent,
and format Three-Address Code (TAC) instructions.

Supported instruction kinds:
- 'label': Target label declaration (e.g., 'L1:')
- 'goto': Unconditional jump (e.g., 'goto L1')
- 'ifFalse': Conditional jump on false condition (e.g., 'ifFalse t1 goto L1')
- 'copy': Value assignment or copy (e.g., 'x = y', 'x = 6')
- 'binary': Binary operation assignment (e.g., 't1 = a + b')
"""

import re

# Set of recognized binary operators in TAC
BINARY_OPS = {'+', '-', '*', '/', '<', '>', '<=', '>=', '==', '!='}


def is_temp(name):
    r"""
    Check if a given variable name is a compiler temporary variable.

    A name is considered a temporary if it matches the pattern 't' followed
    by one or more digits (e.g., 't1', 't2').

    Args:
        name (str): The name to test.

    Returns:
        bool: True if name matches r'^t\d+$', False otherwise.
    """
    return bool(re.fullmatch(r"t\d+", str(name)))


class Instruction:
    """
    Represents a single Three-Address Code (TAC) instruction.

    Attributes:
        kind (str): Kind of instruction ('label', 'goto', 'ifFalse', 'copy', 'binary').
        label (str or None): Label name for 'label' instructions.
        target (str or None): Target label for 'goto' and 'ifFalse' instructions.
        cond (str or None): Condition temporary for 'ifFalse' instructions.
        dst (str or None): Destination variable for 'copy' and 'binary' instructions.
        src (str or None): Source operand for 'copy' instructions.
        left (str or None): Left operand for 'binary' instructions.
        op (str or None): Operator symbol for 'binary' instructions.
        right (str or None): Right operand for 'binary' instructions.
    """

    def __init__(
        self,
        kind,
        label=None,
        target=None,
        cond=None,
        dst=None,
        src=None,
        left=None,
        op=None,
        right=None,
    ):
        """
        Initialize an Instruction instance.

        Args:
            kind (str): Instruction kind ('label', 'goto', 'ifFalse', 'copy', 'binary').
            label (str, optional): Label identifier for label instructions.
            target (str, optional): Target label name for jumps.
            cond (str, optional): Condition operand for ifFalse jumps.
            dst (str, optional): Destination variable name for assignments.
            src (str, optional): Source operand for copy assignments.
            left (str, optional): Left operand for binary operations.
            op (str, optional): Operator for binary operations.
            right (str, optional): Right operand for binary operations.
        """
        self.kind = kind
        self.label = label
        self.target = target
        self.cond = cond
        self.dst = dst
        self.src = src
        self.left = left
        self.op = op
        self.right = right

    def format(self):
        """
        Format the instruction back into its canonical TAC string representation.

        Returns:
            str: Canonical single-line TAC string.

        Raises:
            ValueError: If the instruction kind is unknown.
        """
        if self.kind == "label":
            return f"{self.label}:"
        elif self.kind == "goto":
            return f"goto {self.target}"
        elif self.kind == "ifFalse":
            return f"ifFalse {self.cond} goto {self.target}"
        elif self.kind == "copy":
            return f"{self.dst} = {self.src}"
        elif self.kind == "binary":
            return f"{self.dst} = {self.left} {self.op} {self.right}"
        else:
            raise ValueError(f"Unknown instruction kind: '{self.kind}'")

    def __str__(self):
        """Return the formatted TAC string."""
        return self.format()

    def __repr__(self):
        """Return a detailed developer-friendly representation of the Instruction."""
        parts = [f"kind='{self.kind}'"]
        for attr in ("label", "target", "cond", "dst", "src", "left", "op", "right"):
            val = getattr(self, attr)
            if val is not None:
                parts.append(f"{attr}='{val}'")
        return f"Instruction({', '.join(parts)})"

    def __eq__(self, other):
        """Check equality with another Instruction instance."""
        if not isinstance(other, Instruction):
            return False
        return (
            self.kind == other.kind
            and self.label == other.label
            and self.target == other.target
            and self.cond == other.cond
            and self.dst == other.dst
            and self.src == other.src
            and self.left == other.left
            and self.op == other.op
            and self.right == other.right
        )


def parse_instruction(line):
    """
    Parse a single line of TAC into an Instruction object.

    Args:
        line (str): A single TAC instruction string.

    Returns:
        Instruction: The parsed Instruction object.

    Raises:
        ValueError: If line cannot be parsed as a valid TAC instruction.
    """
    text = line.strip()
    if not text:
        raise ValueError("Cannot parse empty line as TAC instruction")

    # 1. Label: 'Lx:'
    if text.endswith(":"):
        label_name = text[:-1].strip()
        if not label_name:
            raise ValueError(f"Invalid label syntax: '{line}'")
        return Instruction(kind="label", label=label_name)

    # 2. Goto: 'goto Lx'
    if text.startswith("goto "):
        target = text[5:].strip()
        if not target:
            raise ValueError(f"Missing target in goto instruction: '{line}'")
        return Instruction(kind="goto", target=target)

    # 3. ifFalse: 'ifFalse tN goto Lx'
    if text.startswith("ifFalse "):
        match = re.match(r"^ifFalse\s+(\S+)\s+goto\s+(\S+)$", text)
        if not match:
            raise ValueError(f"Invalid ifFalse instruction syntax: '{line}'")
        cond, target = match.groups()
        return Instruction(kind="ifFalse", cond=cond, target=target)

    # 4. Assignment: 'dst = ...'
    if "=" in text:
        parts = text.split("=", 1)
        dst = parts[0].strip()
        rhs = parts[1].strip()
        if not dst:
            raise ValueError(f"Missing destination variable in assignment: '{line}'")

        rhs_parts = rhs.split()
        if len(rhs_parts) == 3 and rhs_parts[1] in BINARY_OPS:
            left, op, right = rhs_parts
            return Instruction(
                kind="binary", dst=dst, left=left, op=op, right=right
            )
        elif len(rhs_parts) == 1:
            return Instruction(kind="copy", dst=dst, src=rhs_parts[0])
        else:
            raise ValueError(f"Invalid RHS in TAC assignment: '{line}'")

    raise ValueError(f"Unrecognized TAC instruction: '{line}'")


def parse_tac(lines):
    """
    Parse a list of TAC instruction strings (or multi-line string) into Instruction objects.

    Args:
        lines (list of str or str): Lines of Three-Address Code strings.

    Returns:
        list of Instruction: List of parsed Instruction objects.
    """
    if isinstance(lines, str):
        lines = lines.splitlines()

    instructions = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        instructions.append(parse_instruction(stripped))
    return instructions


def format_tac(instrs):
    """
    Format a list of Instruction objects back into a list of TAC string lines.

    Args:
        instrs (list of Instruction): List of Instruction objects.

    Returns:
        list of str: List of formatted TAC instruction strings.
    """
    return [instr.format() for instr in instrs]
