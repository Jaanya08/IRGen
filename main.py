"""Command-line driver for IRGen: source code -> tokens -> AST -> TAC."""

from irgen.lexer import tokenize
from irgen.parser import Parser
from irgen.ir_generator import IRGenerator


def main():
    code = input("Enter source code: ")

    try:
        # 1. Lexical analysis
        tokens = tokenize(code)
        print("\nTOKENS:")
        for token in tokens:
            print(token)

        # 2. Syntax analysis -> AST
        ast = Parser(tokens).parse()

        # 3. Intermediate code generation
        generator = IRGenerator()
        generator.generate(ast)

        print("\nTHREE-ADDRESS CODE:")
        for instruction in generator.get_ir():
            print(instruction)

    except SyntaxError as error:
        print(f"\nError: {error}")


if __name__ == "__main__":
    main()