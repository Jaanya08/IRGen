"""
Abstract Syntax Tree (AST) node definitions for IRGen.

This module defines the node classes used to construct the Abstract Syntax Tree
during parsing. Each class represents a distinct construct in the source grammar:
- Number: Represents integer numeric literals.
- Identifier: Represents variable names.
- BinaryExpression: Represents binary operations (+, -, *, /) and comparisons.
- Assignment: Represents variable assignment statements.
- Program: Represents a sequence of statements.
- Block: Represents a block of statements enclosed in braces { ... }.
- If: Represents an if / if-else conditional branch.
- While: Represents a while loop statement.
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
        """Return developer-friendly string representation of Number."""
        return f"Number({self.value})"

    def __eq__(self, other):
        """Check equality with another Number node."""
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
        """Return developer-friendly string representation of Identifier."""
        return f"Identifier('{self.name}')"

    def __eq__(self, other):
        """Check equality with another Identifier node."""
        return isinstance(other, Identifier) and self.name == other.name


class BinaryExpression(ASTNode):
    """
    AST node representing a binary operation (+, -, *, /) or relational comparison.

    Attributes:
        left (ASTNode): The left-hand side operand expression.
        operator (str): The operator symbol (e.g., '+', '-', '*', '/', '<', '>=', '==').
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
        """Return developer-friendly string representation of BinaryExpression."""
        return f"BinaryExpression({self.left}, '{self.operator}', {self.right})"

    def __eq__(self, other):
        """Check equality with another BinaryExpression node."""
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
        """Return developer-friendly string representation of Assignment."""
        return f"Assignment('{self.name}', {self.expression})"

    def __eq__(self, other):
        """Check equality with another Assignment node."""
        return (
            isinstance(other, Assignment)
            and self.name == other.name
            and self.expression == other.expression
        )


class Program(ASTNode):
    """
    AST node representing a top-level program with a list of statements.

    Attributes:
        statements (list of ASTNode): List of statement nodes in the program.
    """

    def __init__(self, statements):
        """
        Initialize a Program node.

        Args:
            statements (list of ASTNode): Sequence of statements.
        """
        self.statements = statements

    def __repr__(self):
        """Return developer-friendly string representation of Program."""
        return f"Program({self.statements})"

    def __eq__(self, other):
        """Check equality with another Program node."""
        return isinstance(other, Program) and self.statements == other.statements


class Block(ASTNode):
    """
    AST node representing a block of statements enclosed in braces { ... }.

    Attributes:
        statements (list of ASTNode): List of statement nodes within the block.
    """

    def __init__(self, statements):
        """
        Initialize a Block node.

        Args:
            statements (list of ASTNode): Sequence of statements in the block.
        """
        self.statements = statements

    def __repr__(self):
        """Return developer-friendly string representation of Block."""
        return f"Block({self.statements})"

    def __eq__(self, other):
        """Check equality with another Block node."""
        return isinstance(other, Block) and self.statements == other.statements


class If(ASTNode):
    """
    AST node representing an if or if-else conditional statement.

    Attributes:
        condition (ASTNode): Condition expression evaluating to a boolean value.
        then_block (Block): Block of statements to execute if condition is true.
        else_block (Block or None): Block of statements to execute if condition is false, or None.
    """

    def __init__(self, condition, then_block, else_block=None):
        """
        Initialize an If node.

        Args:
            condition (ASTNode): The conditional test expression.
            then_block (Block): The then-branch block.
            else_block (Block, optional): The else-branch block. Defaults to None.
        """
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block

    def __repr__(self):
        """Return developer-friendly string representation of If."""
        return f"If({self.condition}, {self.then_block}, {self.else_block})"

    def __eq__(self, other):
        """Check equality with another If node."""
        return (
            isinstance(other, If)
            and self.condition == other.condition
            and self.then_block == other.then_block
            and self.else_block == other.else_block
        )


class While(ASTNode):
    """
    AST node representing a while loop statement.

    Attributes:
        condition (ASTNode): Loop condition expression.
        body (Block): Block of statements to execute iteratively.
    """

    def __init__(self, condition, body):
        """
        Initialize a While node.

        Args:
            condition (ASTNode): The loop condition expression.
            body (Block): The loop body block.
        """
        self.condition = condition
        self.body = body

    def __repr__(self):
        """Return developer-friendly string representation of While."""
        return f"While({self.condition}, {self.body})"

    def __eq__(self, other):
        """Check equality with another While node."""
        return (
            isinstance(other, While)
            and self.condition == other.condition
            and self.body == other.body
        )
