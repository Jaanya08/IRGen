"""
Recursive descent parser for IRGen.

This module converts a sequence of tokens into an Abstract Syntax Tree (AST).
Grammar rules implemented:
- assignment -> ID '=' expression ';'
- expression -> term (('+' | '-') term)*
- term       -> factor (('*' | '/') factor)*
- factor     -> NUMBER | ID | '(' expression ')'
"""

from irgen.ast_nodes import Assignment, BinaryExpression, Identifier, Number


class Parser:
    """
    Recursive descent parser for statement syntax analysis.

    Attributes:
        tokens (list): List of (TYPE, value) tuples returned by the lexer.
        pos (int): Current index in the token list.
    """

    def __init__(self, tokens):
        """
        Initialize the Parser with a list of tokens.

        Args:
            tokens (list): Token list from tokenize().
        """
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        """
        Look at the current token without consuming it.

        Returns:
            tuple or None: Current token (TYPE, value) or None if at EOF.
        """
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consume(self, expected_type=None, expected_value=None):
        """
        Consume and return the current token. Validate constraints if given.

        Args:
            expected_type (str, optional): Expected token type (e.g., 'ID', 'SEMICOLON').
            expected_value (str, optional): Expected literal string value (e.g., '=', '(').

        Returns:
            tuple: Consumed token (TYPE, value).

        Raises:
            SyntaxError: If input ends unexpectedly or token fails expectation match.
        """
        token = self.peek()
        if token is None:
            msg = "Unexpected end of input"
            if expected_value:
                msg += f", expected '{expected_value}'"
            elif expected_type:
                msg += f", expected token of type {expected_type}"
            raise SyntaxError(msg)

        tok_type, tok_val = token
        if expected_type is not None and tok_type != expected_type:
            raise SyntaxError(f"Expected token type '{expected_type}', got '{tok_type}' ('{tok_val}')")

        if expected_value is not None and tok_val != expected_value:
            raise SyntaxError(f"Expected '{expected_value}', got '{tok_val}'")

        self.pos += 1
        return token

    def parse(self):
        """
        Parse the complete token stream into an AST root node.

        Returns:
            Assignment: Root AST node for the assignment statement.

        Raises:
            SyntaxError: If extra unparsed tokens remain after the statement.
        """
        node = self.assignment()
        if self.pos < len(self.tokens):
            extra_type, extra_val = self.tokens[self.pos]
            raise SyntaxError(f"Unexpected token after statement: '{extra_val}'")
        return node

    def assignment(self):
        """
        Parse an assignment statement.
        Grammar: assignment -> ID '=' expression ';'

        Returns:
            Assignment: AST node representing the assignment.

        Raises:
            SyntaxError: If ID, '=', or ';' is missing.
        """
        id_token = self.consume('ID')
        self.consume('ASSIGN', '=')
        expr_node = self.expression()
        self.consume('SEMICOLON', ';')
        return Assignment(id_token[1], expr_node)

    def expression(self):
        """
        Parse an expression handling addition and subtraction (left-associative).
        Grammar: expression -> term (('+' | '-') term)*

        Returns:
            ASTNode: AST node representing the expression.
        """
        node = self.term()
        while True:
            token = self.peek()
            if token and token[0] == 'OP' and token[1] in ('+', '-'):
                op_token = self.consume('OP')
                right_node = self.term()
                node = BinaryExpression(node, op_token[1], right_node)
            else:
                break
        return node

    def term(self):
        """
        Parse a term handling multiplication and division (left-associative).
        Grammar: term -> factor (('*' | '/') factor)*

        Returns:
            ASTNode: AST node representing the term.
        """
        node = self.factor()
        while True:
            token = self.peek()
            if token and token[0] == 'OP' and token[1] in ('*', '/'):
                op_token = self.consume('OP')
                right_node = self.factor()
                node = BinaryExpression(node, op_token[1], right_node)
            else:
                break
        return node

    def factor(self):
        """
        Parse a factor (number, identifier, or parenthesized expression).
        Grammar: factor -> NUMBER | ID | '(' expression ')'

        Returns:
            ASTNode: AST node representing the factor.

        Raises:
            SyntaxError: If an unexpected token or unbalanced parenthesis is found.
        """
        token = self.peek()
        if token is None:
            raise SyntaxError("Unexpected end of input, expected expression factor")

        tok_type, tok_val = token

        if tok_type == 'NUMBER':
            self.consume('NUMBER')
            return Number(tok_val)
        elif tok_type == 'ID':
            self.consume('ID')
            return Identifier(tok_val)
        elif tok_type == 'LPAREN':
            self.consume('LPAREN', '(')
            expr_node = self.expression()
            self.consume('RPAREN', ')')
            return expr_node
        else:
            raise SyntaxError(f"Unexpected token in expression: '{tok_val}'")
