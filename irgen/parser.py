"""
Recursive descent parser for IRGen (Phase 1 + Phase 2).

This module converts a sequence of tokens into an Abstract Syntax Tree (AST).

Phase 1 grammar rules (unchanged):
  assignment -> ID '=' expression ';'
  expression -> term (('+' | '-') term)*
  term       -> factor (('*' | '/') factor)*
  factor     -> NUMBER | ID | '(' expression ')'

Phase 2 grammar rules added:
  program    -> statement*
  statement  -> assignment | if_stmt | while_stmt
  block      -> '{' statement* '}'
  if_stmt    -> 'if' '(' condition ')' block ('else' block)?
  while_stmt -> 'while' '(' condition ')' block
  condition  -> expression (RELOP expression)?
"""

from irgen.ast_nodes import (
    Assignment, BinaryExpression, Block, For, Identifier, If,
    Number, Program, While,
)
from irgen.tac import is_temp


class Parser:
    """
    Recursive descent parser for the IRGen language.

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

    # ------------------------------------------------------------------
    # Low-level helpers
    # ------------------------------------------------------------------

    def peek(self):
        """
        Return the current token without consuming it.

        Returns:
            tuple or None: Current token (TYPE, value), or None at EOF.
        """
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consume(self, expected_type=None, expected_value=None):
        """
        Consume and return the current token, validating its type/value.

        Args:
            expected_type (str, optional): Required token type.
            expected_value (str, optional): Required literal value.

        Returns:
            tuple: The consumed token (TYPE, value).

        Raises:
            SyntaxError: If the stream is exhausted or the token does not match.
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
            raise SyntaxError(
                f"Expected token type '{expected_type}', got '{tok_type}' ('{tok_val}')"
            )
        if expected_value is not None and tok_val != expected_value:
            raise SyntaxError(f"Expected '{expected_value}', got '{tok_val}'")

        self.pos += 1
        return token

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def parse(self):
        """
        Parse the complete token stream and return the root AST node.

        In Phase 2 this always returns a Program node containing one or more
        statements.  Phase 1 single-assignment inputs are wrapped the same way.

        Returns:
            Program: Root AST node for the program.

        Raises:
            SyntaxError: If any tokens remain after the last valid statement.
        """
        return self.program()

    # ------------------------------------------------------------------
    # Phase 2: top-level rules
    # ------------------------------------------------------------------

    def program(self):
        """
        Parse a sequence of statements until the token stream is exhausted.
        Grammar: program -> statement*

        Returns:
            Program: AST node whose statements list contains all parsed statements.
        """
        statements = []
        while self.peek() is not None:
            statements.append(self.statement())
        return Program(statements)

    def statement(self):
        """
        Dispatch to the appropriate statement parser based on the next token.
        Grammar: statement -> assignment | if_stmt | while_stmt

        Returns:
            ASTNode: The parsed statement node (Assignment, If, or While).

        Raises:
            SyntaxError: If the next token does not begin a valid statement.
        """
        token = self.peek()
        if token is None:
            raise SyntaxError("Unexpected end of input, expected a statement")

        tok_type, tok_val = token

        if tok_type == 'KEYWORD' and tok_val == 'if':
            return self.if_stmt()
        elif tok_type == 'KEYWORD' and tok_val == 'while':
            return self.while_stmt()
        elif tok_type == 'KEYWORD' and tok_val == 'for':
            return self.for_stmt()
        elif tok_type == 'KEYWORD' and tok_val == 'else':
            # 'else' can only follow an if-body; encountering it here is an error
            raise SyntaxError("'else' without a preceding 'if'")
        elif tok_type == 'ID':
            return self.assignment()
        else:
            raise SyntaxError(
                f"Unexpected token '{tok_val}', expected a statement"
            )

    def block(self):
        """
        Parse a block of zero or more statements enclosed in braces.
        Grammar: block -> '{' statement* '}'

        Returns:
            Block: AST node containing the parsed statements.

        Raises:
            SyntaxError: If the opening '{' or closing '}' is missing.
        """
        self.consume('LBRACE', '{')
        statements = []
        while True:
            token = self.peek()
            if token is None:
                raise SyntaxError("Unexpected end of input, expected '}'")
            if token[0] == 'RBRACE':
                break
            statements.append(self.statement())
        self.consume('RBRACE', '}')
        return Block(statements)

    def if_stmt(self):
        """
        Parse an if or if-else statement.
        Grammar: if_stmt -> 'if' '(' condition ')' block ('else' block)?

        Returns:
            If: AST node for the conditional statement.

        Raises:
            SyntaxError: If '(' or ')' around condition is missing, or if the
                         then-block or else-block is absent / malformed.
        """
        self.consume('KEYWORD', 'if')
        self.consume('LPAREN', '(')
        cond = self.condition()
        self.consume('RPAREN', ')')

        # Verify that a block follows immediately
        if self.peek() is None or self.peek()[0] != 'LBRACE':
            raise SyntaxError("Expected '{' after 'if (condition)'")
        then_block = self.block()

        # Optional else
        else_block = None
        token = self.peek()
        if token is not None and token[0] == 'KEYWORD' and token[1] == 'else':
            self.consume('KEYWORD', 'else')
            if self.peek() is None or self.peek()[0] != 'LBRACE':
                raise SyntaxError("Expected '{' after 'else'")
            else_block = self.block()

        return If(cond, then_block, else_block)

    def while_stmt(self):
        """
        Parse a while loop statement.
        Grammar: while_stmt -> 'while' '(' condition ')' block

        Returns:
            While: AST node for the loop.

        Raises:
            SyntaxError: If '(' or ')' around condition is missing, or if the
                         loop body block is absent / malformed.
        """
        self.consume('KEYWORD', 'while')
        self.consume('LPAREN', '(')
        cond = self.condition()
        self.consume('RPAREN', ')')

        if self.peek() is None or self.peek()[0] != 'LBRACE':
            raise SyntaxError("Expected '{' after 'while (condition)'")
        body = self.block()

        return While(cond, body)

    def for_stmt(self):
        """
        Parse a for loop statement.
        Grammar: for_stmt -> 'for' '(' (assignment_expr)? ';' condition? ';' (assignment_expr)? ')' block

        Returns:
            For: AST node for the loop.

        Raises:
            SyntaxError: If '(' or ')' around loop header is missing, or if the
                         semicolons are missing, or if the loop body block is absent.
        """
        self.consume('KEYWORD', 'for')
        self.consume('LPAREN', '(')

        # 1. Initialization (optional)
        init = None
        if self.peek() is not None and self.peek()[0] != 'SEMICOLON':
            init = self.assignment_expr()
        self.consume('SEMICOLON', ';')

        # 2. Condition (optional)
        condition = None
        if self.peek() is not None and self.peek()[0] != 'SEMICOLON':
            condition = self.condition()
        self.consume('SEMICOLON', ';')

        # 3. Update (optional)
        update = None
        if self.peek() is not None and self.peek()[0] != 'RPAREN':
            update = self.assignment_expr()
            if self.peek() is not None and self.peek()[0] == 'SEMICOLON':
                self.consume('SEMICOLON', ';')
        self.consume('RPAREN', ')')

        # 4. Body block
        if self.peek() is None or self.peek()[0] != 'LBRACE':
            raise SyntaxError("Expected '{' after 'for (...)')")
        body = self.block()

        return For(init, condition, update, body)

    def condition(self):
        """
        Parse a condition (an expression optionally followed by a RELOP and another expression).
        Grammar: condition -> expression (RELOP expression)?

        A lone expression (no RELOP) is returned as-is; a comparison is
        wrapped in a BinaryExpression whose operator is the relational operator.

        Returns:
            ASTNode: Expression or BinaryExpression node representing the condition.
        """
        left = self.expression()
        token = self.peek()
        if token is not None and token[0] == 'RELOP':
            op_token = self.consume('RELOP')
            right = self.expression()
            return BinaryExpression(left, op_token[1], right)
        return left

    # ------------------------------------------------------------------
    # Phase 1: expression rules (unchanged)
    # ------------------------------------------------------------------

    def assignment_expr(self):
        """
        Parse an assignment without a trailing semicolon (e.g. for loop init/update).
        Grammar: assignment_expr -> ID '=' expression

        Returns:
            Assignment: AST node for the assignment.
        """
        id_token = self.consume('ID')
        name = id_token[1]
        if is_temp(name):
            raise SyntaxError(f"'{name}' is reserved for compiler temporaries")
        self.consume('ASSIGN', '=')
        expr_node = self.expression()
        return Assignment(name, expr_node)

    def assignment(self):
        """
        Parse an assignment statement.
        Grammar: assignment -> ID '=' expression ';'

        Returns:
            Assignment: AST node for the assignment.

        Raises:
            SyntaxError: If the ID, '=', expression, or ';' is missing.
        """
        assign_node = self.assignment_expr()
        self.consume('SEMICOLON', ';')
        return assign_node

    def expression(self):
        """
        Parse an addition/subtraction expression (left-associative).
        Grammar: expression -> term (('+' | '-') term)*

        Returns:
            ASTNode: Expression subtree node.
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
        Parse a multiplication/division term (left-associative).
        Grammar: term -> factor (('*' | '/') factor)*

        Returns:
            ASTNode: Term subtree node.
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
        Parse a primary factor: a number, identifier, or parenthesised expression.
        Grammar: factor -> NUMBER | ID | '(' expression ')'

        Returns:
            ASTNode: Leaf or grouped expression node.

        Raises:
            SyntaxError: If an unexpected token is found, or a '(' has no matching ')'.
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
            if is_temp(tok_val):
                raise SyntaxError(f"'{tok_val}' is reserved for compiler temporaries")
            return Identifier(tok_val)
        elif tok_type == 'LPAREN':
            self.consume('LPAREN', '(')
            expr_node = self.expression()
            self.consume('RPAREN', ')')
            return expr_node
        else:
            raise SyntaxError(f"Unexpected token in expression: '{tok_val}'")
