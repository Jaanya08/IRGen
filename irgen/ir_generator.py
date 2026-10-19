"""
Intermediate Representation (IR) Generator for IRGen.

This module converts an Abstract Syntax Tree (AST) into Three-Address Code (TAC).
TAC instructions are formatted as machine-independent 3-address assignment strings.

Phase 2 additions:
- new_label(): allocates labels L1, L2, ... from a counter separate from temps.
- generate() handles Block, If, and While in addition to the Phase 1 nodes.

TAC patterns emitted:
  If/else:  ifFalse tN goto Lelse / goto Lend / Lelse: / Lend:
  If only:  ifFalse tN goto Lend / Lend:
  While:    Lstart: / ifFalse tN goto Lend / goto Lstart / Lend:
"""

from irgen.ast_nodes import (
    Assignment, BinaryExpression, Block, Identifier, If,
    Number, Program, While,
)


class IRGenerator:
    """
    IRGenerator traverses an AST and emits Three-Address Code (TAC) instructions.

    Attributes:
        temp_count (int): Counter for unique temporary names; first result is 't1'.
        label_count (int): Counter for unique label names; first result is 'L1'.
        instructions (list of str): Accumulated TAC instruction strings.
    """

    def __init__(self):
        """Initialize with separate temp and label counters, and an empty instruction list."""
        self.temp_count = 0
        self.label_count = 0
        self.instructions = []

    # ------------------------------------------------------------------
    # Counter helpers
    # ------------------------------------------------------------------

    def new_temp(self):
        """
        Allocate the next unique temporary variable name.

        Returns:
            str: Name of the form 't1', 't2', etc.
        """
        self.temp_count += 1
        return f"t{self.temp_count}"

    def new_label(self):
        """
        Allocate the next unique label name.

        The label counter is independent of the temp counter so that adding
        more arithmetic sub-expressions inside a control-flow construct does
        not change the label numbering.

        Returns:
            str: Name of the form 'L1', 'L2', etc.
        """
        self.label_count += 1
        return f"L{self.label_count}"

    # ------------------------------------------------------------------
    # Instruction emitters
    # ------------------------------------------------------------------

    def _emit(self, instruction):
        """
        Append a single TAC instruction string to the instruction list.

        Args:
            instruction (str): The TAC instruction to emit.
        """
        self.instructions.append(instruction)

    def _emit_label(self, label):
        """
        Emit a label definition line of the form 'Lx:'.

        Args:
            label (str): Label name, e.g. 'L1'.
        """
        self._emit(f"{label}:")

    def _emit_goto(self, label):
        """
        Emit an unconditional jump instruction: 'goto Lx'.

        Args:
            label (str): Target label name.
        """
        self._emit(f"goto {label}")

    def _emit_if_false(self, temp, label):
        """
        Emit a conditional jump instruction: 'ifFalse tN goto Lx'.

        Args:
            temp (str): Temporary variable holding the condition result.
            label (str): Target label name jumped to when condition is false.
        """
        self._emit(f"ifFalse {temp} goto {label}")

    # ------------------------------------------------------------------
    # Main recursive generator
    # ------------------------------------------------------------------

    def generate(self, node):
        """
        Recursively walk an AST node and emit the corresponding TAC instructions.

        Args:
            node (ASTNode): Root or sub-tree AST node to generate IR for.

        Returns:
            str or None: Operand string for expression nodes (temp name, variable
                         name, or numeric literal); None for statement nodes whose
                         result is not used as an operand.

        Raises:
            TypeError: If an unrecognised AST node type is encountered.
        """
        if isinstance(node, Program):
            # Generate code for each top-level statement in order.
            for stmt in node.statements:
                self.generate(stmt)
            return None

        elif isinstance(node, Block):
            # Generate code for each statement inside a { ... } block.
            for stmt in node.statements:
                self.generate(stmt)
            return None

        elif isinstance(node, Number):
            # A numeric literal produces no instruction; its value is the operand.
            return str(node.value)

        elif isinstance(node, Identifier):
            # A variable name produces no instruction; the name is the operand.
            return str(node.name)

        elif isinstance(node, BinaryExpression):
            # Generate left then right, then emit: tN = left op right.
            left_op = self.generate(node.left)
            right_op = self.generate(node.right)
            temp = self.new_temp()
            self._emit(f"{temp} = {left_op} {node.operator} {right_op}")
            return temp

        elif isinstance(node, Assignment):
            # Generate the RHS expression, then emit: name = result.
            expr_result = self.generate(node.expression)
            self._emit(f"{node.name} = {expr_result}")
            return node.name

        elif isinstance(node, If):
            return self._generate_if(node)

        elif isinstance(node, While):
            return self._generate_while(node)

        else:
            raise TypeError(f"Unknown AST node type: {type(node).__name__}")

    # ------------------------------------------------------------------
    # Control-flow helpers (keep generate() readable)
    # ------------------------------------------------------------------

    def _generate_if(self, node):
        """
        Emit TAC for an If node.

        With else-block:
            <condition>
            ifFalse tN goto Lelse
            <then block>
            goto Lend
            Lelse:
            <else block>
            Lend:

        Without else-block:
            <condition>
            ifFalse tN goto Lend
            <then block>
            Lend:

        Labels are allocated before any nested code is generated so that
        inner constructs receive higher label numbers, keeping numbering
        deterministic.

        Args:
            node (If): The If AST node to generate IR for.

        Returns:
            None
        """
        if node.else_block is not None:
            # Allocate both labels up front.
            l_else = self.new_label()
            l_end = self.new_label()

            cond_temp = self.generate(node.condition)
            self._emit_if_false(cond_temp, l_else)
            self.generate(node.then_block)
            self._emit_goto(l_end)
            self._emit_label(l_else)
            self.generate(node.else_block)
            self._emit_label(l_end)
        else:
            # Only one label needed.
            l_end = self.new_label()

            cond_temp = self.generate(node.condition)
            self._emit_if_false(cond_temp, l_end)
            self.generate(node.then_block)
            self._emit_label(l_end)

        return None

    def _generate_while(self, node):
        """
        Emit TAC for a While node.

        Pattern:
            Lstart:
            <condition>
            ifFalse tN goto Lend
            <body>
            goto Lstart
            Lend:

        Both labels are allocated before any nested code so inner constructs
        receive strictly higher label numbers.

        Args:
            node (While): The While AST node to generate IR for.

        Returns:
            None
        """
        l_start = self.new_label()
        l_end = self.new_label()

        self._emit_label(l_start)
        cond_temp = self.generate(node.condition)
        self._emit_if_false(cond_temp, l_end)
        self.generate(node.body)
        self._emit_goto(l_start)
        self._emit_label(l_end)

        return None

    # ------------------------------------------------------------------
    # Public accessor
    # ------------------------------------------------------------------

    def get_ir(self):
        """
        Return the accumulated list of TAC instruction strings.

        Returns:
            list of str: TAC instruction strings in emission order.
        """
        return self.instructions
