"""
Command-line driver for IRGen: source code -> tokens -> AST -> TAC -> ASM.

Supports command-line flags for optimization, assembly code generation,
instruction statistics, and JSON export.
"""

import argparse
import json
import os
import sys

from irgen.lexer import tokenize
from irgen.parser import Parser
from irgen.ir_generator import IRGenerator
from irgen.optimizer import optimize
from irgen.codegen import generate_asm


def parse_arguments():
    """
    Parse command-line arguments and flags for IRGen.

    Returns:
        argparse.Namespace: Parsed CLI options and arguments.
    """
    parser = argparse.ArgumentParser(
        description="IRGen compiler front-end CLI"
    )
    parser.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Path to source file (reads terminal input if omitted)",
    )
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="Run optimization passes and display optimized TAC",
    )
    parser.add_argument(
        "--asm",
        action="store_true",
        help="Generate and display assembly instructions for an imaginary register machine",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Display TAC instruction count statistics before and after optimization",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Export full compilation pipeline results as a single JSON object",
    )
    return parser.parse_args()


def read_source(file_path, json_mode):
    """
    Read source code from a file or from standard/interactive input.

    Args:
        file_path (str or None): Path to the source file, or None if reading from stdin.
        json_mode (bool): If True and no file is given, read stdin silently without prompts.

    Returns:
        str: Input source code string.
    """
    if file_path is not None:
        if not os.path.exists(file_path):
            error_msg = f"File not found: '{file_path}'"
            if json_mode:
                print(json.dumps({"error": error_msg}, indent=2))
            else:
                print(f"Error: {error_msg}")
            sys.exit(1)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except OSError as error:
            error_msg = f"Could not read file '{file_path}': {error}"
            if json_mode:
                print(json.dumps({"error": error_msg}, indent=2))
            else:
                print(f"Error: {error_msg}")
            sys.exit(1)
    else:
        if json_mode:
            return sys.stdin.read()
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
    Run the IRGen pipeline on input source code according to CLI flags.
    """
    args = parse_arguments()
    code = read_source(args.file, args.json)

    try:
        # 1. Lexical analysis -> Tokens
        tokens = tokenize(code)

        # 2. Syntax analysis -> AST
        ast = Parser(tokens).parse()

        # 3. Intermediate code generation -> TAC
        generator = IRGenerator()
        generator.generate(ast)
        tac = generator.get_ir()

    except SyntaxError as error:
        if args.json:
            print(json.dumps({"error": str(error)}, indent=2))
            sys.exit(1)
        else:
            print(f"Error: {error}")
            sys.exit(1)

    # 4. JSON export mode
    if args.json:
        optimized_tac, opt_log = optimize(tac)
        asm = generate_asm(optimized_tac)
        output = {
            "source": code,
            "tokens": [list(t) for t in tokens],
            "ast": ast.to_dict(),
            "tac": tac,
            "optimized_tac": optimized_tac,
            "optimization_log": opt_log,
            "assembly": asm,
            "stats": {
                "tac_before": len(tac),
                "tac_after": len(optimized_tac),
                "removed": len(tac) - len(optimized_tac),
                "assembly_lines": len(asm),
            },
        }
        print(json.dumps(output, indent=2))
        return

    # 5. Default text output mode
    print("TOKENS:")
    for token in tokens:
        print(token)
    print()
    print("THREE-ADDRESS CODE:")
    for instruction in tac:
        print(instruction)

    optimized_tac = None
    if args.optimize or args.stats:
        optimized_tac, _ = optimize(tac)

    if args.optimize:
        print()
        print("OPTIMIZED TAC:")
        for instruction in optimized_tac:
            print(instruction)

    if args.asm:
        asm_source = optimized_tac if args.optimize else tac
        asm_lines = generate_asm(asm_source)
        print()
        print("ASSEMBLY:")
        for instruction in asm_lines:
            print(instruction)

    if args.stats:
        before_count = len(tac)
        after_count = len(optimized_tac)
        removed_count = before_count - after_count
        print()
        print("STATS:")
        print(f"Instructions before: {before_count}")
        print(f"Instructions after:  {after_count}")
        print(f"Removed: {removed_count}")


if __name__ == "__main__":
    main()