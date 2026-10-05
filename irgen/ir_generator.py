"""
Intermediate Representation (IR) Generator for IRGen.

This module converts an Abstract Syntax Tree (AST) into Three-Address Code (TAC).
TAC instructions are formatted as machine-independent 3-address assignment strings.
"""

from irgen.ast_nodes import Assignment, BinaryExpression, Identifier, Number


class IRGenerator:
    """
    IRGenerator traverses an AST and emits Three-Address Code (TAC) instructions.

    Attributes:
        temp_count (int): Counter for generating unique temp variable names (t1, t2, ...).
        instructions (list): Sequence of generated TAC instruction strings.
    """

    def __init__(self):
        """Initialize IRGenerator with temp counter starting at 0 and empty instruction list."""
        self.temp_count = 0
        self.instructions = []

    def new_temp(self):
        """
        Generate a new unique temporary variable name.

        Returns:
            str: Next temporary variable name starting from 't1'.
        """
        self.temp_count += 1
        return f"t{self.temp_count}"

    def generate(self, node):
        """
        Recursively walk the AST node and emit TAC instructions.

        Args:
            node (ASTNode): The root or sub-tree AST node to generate IR for.

        Returns:
            str: The operand string representing the result value of the node
                 (variable name, number literal, or temporary variable name).

        Raises:
            TypeError: If an unhandled or invalid AST node type is passed.
        """
        if isinstance(node, Number):
            return str(node.value)

        elif isinstance(node, Identifier):
            return str(node.name)

        elif isinstance(node, BinaryExpression):
            left_op = self.generate(node.left)
            right_op = self.generate(node.right)
            temp = self.new_temp()
            instruction = f"{temp} = {left_op} {node.operator} {right_op}"
            self.instructions.append(instruction)
            return temp

        elif isinstance(node, Assignment):
            expr_result = self.generate(node.expression)
            instruction = f"{node.name} = {expr_result}"
            self.instructions.append(instruction)
            return node.name

        else:
            raise TypeError(f"Unknown AST node type: {type(node).__name__}")

    def get_ir(self):
        """
        Get the list of generated Three-Address Code (TAC) instructions.

        Returns:
            list of str: TAC instruction strings.
        """
        return self.instructions
