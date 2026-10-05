"""
Lexical analyzer (lexer) for IRGen.

This module converts raw source code into a list of token tuples (TYPE, value).
Supported token types:
- NUMBER: Integer numeric literals (e.g., 10, 25)
- ID: Variable identifiers ([A-Za-z_][A-Za-z0-9_]*)
- OP: Arithmetic operators (+, -, *, /)
- ASSIGN: Assignment operator (=)
- LPAREN: Left parenthesis '('
- RPAREN: Right parenthesis ')'
- SEMICOLON: Statement terminator ';'
"""

import re


def tokenize(code):
    """
    Tokenize a source code string into a list of (TYPE, value) token tuples.

    Args:
        code (str): Source code string to be tokenized.

    Returns:
        list of tuple: List of (token_type, token_value) tuples.

    Raises:
        SyntaxError: If an unexpected character is encountered.
    """
    token_patterns = [
        ('NUMBER', r'\d+'),
        ('ID', r'[A-Za-z_][A-Za-z0-9_]*'),
        ('OP', r'[+\-*/]'),
        ('ASSIGN', r'='),
        ('LPAREN', r'\('),
        ('RPAREN', r'\)'),
        ('SEMICOLON', r';'),
        ('SKIP', r'[ \t\r\n]+'),
        ('MISMATCH', r'.'),
    ]

    # Combine regular expressions with named groups
    tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_patterns)
    tokens = []

    for match in re.finditer(tok_regex, code, re.DOTALL):
        kind = match.lastgroup
        value = match.group()

        if kind == 'SKIP':
            continue
        elif kind == 'MISMATCH':
            raise SyntaxError(f"Unexpected character: '{value}'")
        else:
            tokens.append((kind, value))

    return tokens
