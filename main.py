"""Command-line driver for IRGen: source code -> tokens -> AST -> TAC."""

import os
import sys
from irgen.lexer import tokenize
from irgen.parser import Parser
from irgen.ir_generator import IRGenerator


def read_source():
    """
    Read source code from a file argument or interactively from terminal input.

    Returns:
        str: Source code to be processed by IRGen.
    """
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if not os.path.exists(file_path):
            print(f"Error: File not found: '{file_path}'")
            sys.exit(1)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except OSError as error:
            print(f"Error: Could not read file '{file_path}': {error}")
            sys.exit(1)
    else:
        print("Enter source code (empty line to finish):")
        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            if line == "":
                break
            lines.append(line)
        return "\n".join(lines)


def main():
    """
    Run the IRGen pipeline on input source code and print tokens and TAC instructions.
    """
    code = read_source()

    try:
        # 1. Lexical analysis
        tokens = tokenize(code)

        # 2. Syntax analysis -> AST
        ast = Parser(tokens).parse()

        # 3. Intermediate code generation
        generator = IRGenerator()
        generator.generate(ast)

        # 4. Print results
        print("TOKENS:")
        for token in tokens:
            print(token)
        print()
        print("THREE-ADDRESS CODE:")
        for instruction in generator.get_ir():
            print(instruction)

    except SyntaxError as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()