# IRGen: A Lightweight Intermediate Code Generation System Using Three-Address Code

## Overview
IRGen is a lightweight compiler front-end built in Python using standard library modules only. It converts statements and control-flow constructs in a custom programming language into machine-independent Three-Address Code (TAC). The system demonstrates core compiler concepts including lexical analysis, recursive descent parsing, Abstract Syntax Tree (AST) construction, and intermediate representation generation with control flow.

## Pipeline
```
Source -> Lexer -> Tokens -> Parser -> AST -> IR Generator -> TAC
```

## Supported Features (Phase 1 & Phase 2)
- **Integer numbers**: Decimal integer literals (e.g., `10`, `25`).
- **Identifiers**: Variable names matching `[A-Za-z_][A-Za-z0-9_]*`.
- **Arithmetic Operators**: Binary operators (`+`, `-`, `*`, `/`) with precedence (`*`, `/` over `+`, `-`) and left-associativity.
- **Relational Operators**: Comparisons (`<`, `>`, `<=`, `>=`, `==`, `!=`).
- **Assignments**: Variable assignments (`x = expr;`).
- **Blocks & Grouping**: Statement blocks enclosed in braces `{ ... }` and parenthesized sub-expressions `( ... )`.
- **Conditionals**: `if (cond) { ... }` and `if (cond) { ... } else { ... }`.
- **Loops**: `while (cond) { ... }`.
- **Sequential Statements**: Multi-statement programs and nested control-flow constructs.
- **TAC Emission**: Machine-independent instructions with separate temp (`t1`, `t2`, ...) and label (`L1`, `L2`, ...) counters, conditional jumps (`ifFalse tN goto Lx`), unconditional jumps (`goto Lx`), and label targets (`Lx:`).

## Project Structure
```
IRGen/
├── .gitignore
├── AGENTS.md
├── README.md
├── main.py
├── docs/
├── examples/
│   ├── ifelse.txt
│   └── loop.txt
├── irgen/
│   ├── __init__.py
│   ├── ast_nodes.py
│   ├── codegen.py          # (Phase 3)
│   ├── ir_generator.py
│   ├── lexer.py
│   ├── optimizer.py        # (Phase 3)
│   └── parser.py
├── tests/
│   ├── test_cases.py       # Phase 1 tests
│   └── test_control_flow.py # Phase 2 tests
└── visualizer/             # (Phase 3)
```

## How to Run

### 1. From a File
Pass a source file path as a command-line argument:

```bash
python main.py examples/loop.txt
```

or:

```bash
python main.py examples/ifelse.txt
```

### 2. Interactive Multi-line Input
Run without arguments to enter source code directly into the terminal. Finish input by pressing Enter on an empty line:

```bash
python main.py
```

## Examples

### Example 1: Arithmetic Expression
Input:
```text
x = a + b * c;
```

Output:
```text
TOKENS:
('ID', 'x')
('ASSIGN', '=')
('ID', 'a')
('OP', '+')
('ID', 'b')
('OP', '*')
('ID', 'c')
('SEMICOLON', ';')

THREE-ADDRESS CODE:
t1 = b * c
t2 = a + t1
x = t2
```

### Example 2: Control Flow (`while` loop)
Running `python main.py examples/loop.txt`:

```text
TOKENS:
('KEYWORD', 'while')
('LPAREN', '(')
('ID', 'a')
('RELOP', '<')
('ID', 'b')
('RPAREN', ')')
('LBRACE', '{')
('ID', 'a')
('ASSIGN', '=')
('ID', 'a')
('OP', '+')
('NUMBER', '1')
('SEMICOLON', ';')
('RBRACE', '}')

THREE-ADDRESS CODE:
L1:
t1 = a < b
ifFalse t1 goto L2
t2 = a + 1
a = t2
goto L1
L2:
```

### Example 3: Conditional Branch (`if-else`)
Running `python main.py examples/ifelse.txt`:

```text
TOKENS:
('KEYWORD', 'if')
('LPAREN', '(')
('ID', 'a')
('RELOP', '>')
('ID', 'b')
('RPAREN', ')')
('LBRACE', '{')
('ID', 'x')
('ASSIGN', '=')
('ID', 'a')
('SEMICOLON', ';')
('RBRACE', '}')
('KEYWORD', 'else')
('LBRACE', '{')
('ID', 'x')
('ASSIGN', '=')
('ID', 'b')
('SEMICOLON', ';')
('RBRACE', '}')

THREE-ADDRESS CODE:
t1 = a > b
ifFalse t1 goto L1
x = a
goto L2
L1:
x = b
L2:
```

## Running Tests
Run all unit tests across both phases using Python's standard `unittest` test runner:

```bash
python -m unittest discover tests -v
```

All 19 tests (7 Phase 1 + 12 Phase 2) should report `OK`.

## Current Status
- **Phase 1 (Expressions & Assignments)**: Complete.
- **Phase 2 (Control Flow & Multi-statement Programs)**: Complete.

## Planned Features (Phase 3)
The following features are planned for future development:
- IR optimization (constant folding, dead-code elimination, algebraic simplification).
- Target code generation.
- Interactive IR / AST visualizer.
