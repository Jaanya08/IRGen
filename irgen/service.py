"""
Compiler service module for IRGen.

Provides a unified interface for the complete compilation pipeline:
Lexical analysis -> AST parsing -> TAC generation -> Optimization -> Code generation -> VM simulation.
Used by the web student portal and CLI JSON export.
"""

from irgen.lexer import tokenize
from irgen.parser import Parser
from irgen.ir_generator import IRGenerator
from irgen.optimizer import optimize
from irgen.codegen import generate_asm
from irgen.interpreter import run_tac
from irgen.ast_nodes import (
    ASTNode, Assignment, BinaryExpression, Block, For, Identifier, If,
    Number, Program, While,
)


def format_ast_outline(node, indent=0, prefix=""):
    """
    Format an AST node into a human-readable indented tree outline.

    Args:
        node (ASTNode): The AST node to format.
        indent (int): Current indentation depth.
        prefix (str): Node role prefix (e.g. 'init: ').

    Returns:
        str: Indented multi-line tree outline.
    """
    pad = "  " * indent
    if node is None:
        return f"{pad}{prefix}(none)\n"

    if isinstance(node, Program):
        out = f"{pad}Program ({len(node.statements)} statements)\n"
        for s in node.statements:
            out += format_ast_outline(s, indent + 1)
        return out

    elif isinstance(node, Block):
        out = f"{pad}{prefix}Block ({len(node.statements)} statements)\n"
        for s in node.statements:
            out += format_ast_outline(s, indent + 1)
        return out

    elif isinstance(node, Assignment):
        out = f"{pad}{prefix}Assign: {node.name} =\n"
        out += format_ast_outline(node.expression, indent + 1)
        return out

    elif isinstance(node, BinaryExpression):
        out = f"{pad}{prefix}BinaryExpr ({node.operator})\n"
        out += format_ast_outline(node.left, indent + 1, "left: ")
        out += format_ast_outline(node.right, indent + 1, "right: ")
        return out

    elif isinstance(node, Number):
        return f"{pad}{prefix}Number ({node.value})\n"

    elif isinstance(node, Identifier):
        return f"{pad}{prefix}Identifier ({node.name})\n"

    elif isinstance(node, If):
        out = f"{pad}{prefix}If\n"
        out += format_ast_outline(node.condition, indent + 1, "condition: ")
        out += format_ast_outline(node.then_block, indent + 1, "then: ")
        if node.else_block is not None:
            out += format_ast_outline(node.else_block, indent + 1, "else: ")
        return out

    elif isinstance(node, While):
        out = f"{pad}{prefix}While\n"
        out += format_ast_outline(node.condition, indent + 1, "condition: ")
        out += format_ast_outline(node.body, indent + 1, "body: ")
        return out

    elif isinstance(node, For):
        out = f"{pad}{prefix}For Loop\n"
        out += format_ast_outline(node.init, indent + 1, "init: ")
        out += format_ast_outline(node.condition, indent + 1, "condition: ")
        out += format_ast_outline(node.update, indent + 1, "update: ")
        out += format_ast_outline(node.body, indent + 1, "body: ")
        return out

    return f"{pad}{prefix}{type(node).__name__}\n"


def compile_pipeline(source_code, initial_env=None):
    """
    Execute the entire IRGen pipeline on source code.

    Args:
        source_code (str): Source code string in IRGen syntax.
        initial_env (dict, optional): Initial variable environment for simulation.

    Returns:
        dict: Full compilation artifacts or error details.
    """
    if initial_env is None:
        initial_env = {}

    result = {
        "success": False,
        "source": source_code,
    }

    # 1. Lexical Analysis
    try:
        tokens = tokenize(source_code)
    except SyntaxError as e:
        result["stage"] = "Lexer"
        result["error"] = str(e)
        return result

    result["tokens"] = [
        {"index": idx + 1, "type": t[0], "value": t[1]}
        for idx, t in enumerate(tokens)
    ]

    # 2. Syntax Analysis (AST)
    try:
        parser = Parser(tokens)
        ast = parser.parse()
    except SyntaxError as e:
        result["stage"] = "Parser"
        result["error"] = str(e)
        return result

    result["ast"] = ast.to_dict()
    result["ast_outline"] = format_ast_outline(ast)

    # 3. Intermediate Representation Generation (TAC)
    try:
        ir_gen = IRGenerator()
        ir_gen.generate(ast)
        tac = ir_gen.get_ir()
    except Exception as e:
        result["stage"] = "IR Generator"
        result["error"] = str(e)
        return result

    result["tac"] = tac

    # 4. Optimization Passes
    try:
        optimized_tac, opt_log = optimize(tac)
    except Exception as e:
        result["stage"] = "Optimizer"
        result["error"] = str(e)
        return result

    result["optimized_tac"] = optimized_tac
    result["optimization_log"] = opt_log

    # 5. Target Machine Assembly Code Generation
    try:
        asm = generate_asm(optimized_tac)
        raw_asm = generate_asm(tac)
    except Exception as e:
        result["stage"] = "CodeGen"
        result["error"] = str(e)
        return result

    result["assembly"] = asm
    result["raw_assembly"] = raw_asm

    # 6. Statistics
    before_count = len(tac)
    after_count = len(optimized_tac)
    removed_count = before_count - after_count
    reduction = round((removed_count / before_count * 100), 1) if before_count > 0 else 0.0

    result["stats"] = {
        "tokens_count": len(tokens),
        "tac_before": before_count,
        "tac_after": after_count,
        "removed": removed_count,
        "reduction_percent": reduction,
        "assembly_lines": len(asm),
        "raw_assembly_lines": len(raw_asm),
        "passes_fired": len(opt_log),
    }

    # 7. Virtual Machine Simulation / Execution
    exec_info = {"attempted": True}
    try:
        env_raw = run_tac(tac, env=initial_env)
        # Filter user variables (exclude internal compiler temps for cleaner student view)
        user_vars = {k: v for k, v in env_raw.items() if not k.startswith("t") or not k[1:].isdigit()}
        all_vars = env_raw
        exec_info["success"] = True
        exec_info["variables"] = user_vars
        exec_info["all_variables"] = all_vars
    except Exception as e:
        exec_info["success"] = False
        exec_info["error"] = str(e)
        exec_info["error_type"] = type(e).__name__

    try:
        env_opt = run_tac(optimized_tac, env=initial_env)
        exec_info["optimized_variables"] = {
            k: v for k, v in env_opt.items() if not k.startswith("t") or not k[1:].isdigit()
        }
    except Exception:
        pass

    result["execution"] = exec_info
    result["success"] = True
    return result


def get_curriculum_examples():
    """
    Return curated educational examples for the student learning portal.

    Returns:
        list of dict: Educational examples with title, description, code, and default variables.
    """
    return [
        {
            "id": "for_loop_sum",
            "category": "Loops & Iteration",
            "title": "For Loop: Summation 1 to 5",
            "description": "Demonstrates the newly added for loop with initialization, condition check, accumulator body, and update step.",
            "code": "sum = 0;\nfor (i = 1; i <= 5; i = i + 1) {\n    sum = sum + i;\n}\n",
            "initial_env": {},
        },
        {
            "id": "for_loop_nested",
            "category": "Loops & Iteration",
            "title": "Nested For Loops: 2D Grid Counter",
            "description": "Demonstrates label stacking and nested loop scopes with inner and outer loops.",
            "code": "total = 0;\nfor (row = 1; row <= 3; row = row + 1) {\n    for (col = 1; col <= 2; col = col + 1) {\n        total = total + 1;\n    }\n}\n",
            "initial_env": {},
        },
        {
            "id": "while_loop",
            "category": "Loops & Iteration",
            "title": "While Loop: Decrement Counter",
            "description": "Demonstrates conditional repetition using a while loop with relational test.",
            "code": "n = 5;\ncount = 0;\nwhile (n > 0) {\n    count = count + n;\n    n = n - 1;\n}\n",
            "initial_env": {},
        },
        {
            "id": "if_else_max",
            "category": "Conditionals",
            "title": "If-Else: Maximum of Two Numbers",
            "description": "Demonstrates conditional branching with conditional jumps (ifFalse) and unconditional jumps (goto).",
            "code": "a = 42;\nb = 17;\nif (a > b) {\n    max = a;\n} else {\n    max = b;\n}\n",
            "initial_env": {},
        },
        {
            "id": "optimizations_demo",
            "category": "Optimizer Showcase",
            "title": "Optimizer Showcase: Constant Folding & Dead Code",
            "description": "Demonstrates Constant Folding (2*3 -> 6), Algebraic Simplification (b*1 -> b), Copy Fusion, and Dead Temp Elimination.",
            "code": "a = 10;\nx = 2 * 3 + a;\ny = 2 * 3 + a;\nsimplified = b * 1 + 0;\n",
            "initial_env": {"b": 5},
        },
        {
            "id": "arithmetic_precedence",
            "category": "Expressions",
            "title": "Arithmetic: Operator Precedence",
            "description": "Demonstrates precedence parsing (* and / bind tighter than + and -) and temporary variable allocation.",
            "code": "result = a + b * c - (d + 2) / 3;\n",
            "initial_env": {"a": 10, "b": 3, "c": 4, "d": 7},
        },
        {
            "id": "basic_assignment",
            "category": "Expressions",
            "title": "Basic Assignment: Three-Address Code",
            "description": "Introductory example showing a single expression decomposed into atomic 3-address instructions.",
            "code": "x = a * b + c;\n",
            "initial_env": {"a": 2, "b": 3, "c": 4},
        },
    ]
