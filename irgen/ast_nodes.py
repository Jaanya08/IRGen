"""
Abstract Syntax Tree (AST) node definitions for IRGen.

This module defines the node classes used to construct the Abstract Syntax Tree
during parsing. Each class represents a distinct construct in the source grammar:
- Number: Represents integer numeric literals.
- Identifier: Represents variable names.
- BinaryExpression: Represents binary operations (+, -, *, /).
- Assignment: Represents variable assignment statements.
"""


class ASTNode:
    """Base class for all AST nodes."""
    pass


class Number(ASTNode):
    """
    AST node representing an integer literal.

    Attributes:
        value (str or int): The numeric value or literal string representation.
    """

    def __init__(self, value):
        """
        Initialize a Number node.

        Args:
            value (str or int): The literal numeric value.
        """
        self.value = value

    def __repr__(self):
        return f"Number({self.value})"

    def __eq__(self, other):
        return isinstance(other, Number) and self.value == other.value


class Identifier(ASTNode):
    """
    AST node representing a variable identifier.

    Attributes:
        name (str): The name of the variable identifier.
    """

    def __init__(self, name):
        """
        Initialize an Identifier node.

        Args:
            name (str): The identifier name.
        """
        self.name = name

    def __repr__(self):
        return f"Identifier('{self.name}')"

    def __eq__(self, other):
        return isinstance(other, Identifier) and self.name == other.name


class BinaryExpression(ASTNode):
    """
    AST node representing a binary operation (+, -, *, /).

    Attributes:
        left (ASTNode): The left-hand side operand expression.
        operator (str): The binary operator symbol (e.g., '+', '-', '*', '/').
        right (ASTNode): The right-hand side operand expression.
    """

    def __init__(self, left, operator, right):
        """
        Initialize a BinaryExpression node.

        Args:
            left (ASTNode): Left operand.
            operator (str): Operator string.
            right (ASTNode): Right operand.
        """
        self.left = left
        self.operator = operator
        self.right = right

    def __repr__(self):
        return f"BinaryExpression({self.left}, '{self.operator}', {self.right})"

    def __eq__(self, other):
        return (
            isinstance(other, BinaryExpression)
            and self.left == other.left
            and self.operator == other.operator
            and self.right == other.right
        )


class Assignment(ASTNode):
    """
    AST node representing an assignment statement (e.g., x = expression;).

    Attributes:
        name (str): Target variable name being assigned to.
        expression (ASTNode): Expression evaluated to produce the value.
    """

    def __init__(self, name, expression):
        """
        Initialize an Assignment node.

        Args:
            name (str): Target variable name.
            expression (ASTNode): Evaluated expression node.
        """
        self.name = name
        self.expression = expression

    def __repr__(self):
        return f"Assignment('{self.name}', {self.expression})"

    def __eq__(self, other):
        return (
            isinstance(other, Assignment)
            and self.name == other.name
            and self.expression == other.expression
        )
