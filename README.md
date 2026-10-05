# IRGen: A Lightweight Intermediate Code Generation System Using Three-Address Code

## Overview
IRGen is a lightweight compiler front-end built in Python using standard library modules only. It converts statements in a small custom assignment language into machine-independent Three-Address Code (TAC). The system is designed to demonstrate key compiler concepts including lexical analysis, parsing, Abstract Syntax Tree (AST) construction, and intermediate representation generation.

## Pipeline
```
Source -> Lexer -> Tokens -> Parser -> AST -> IR Generator -> TAC
```

## Supported Features (Phase 1)
- **Integer numbers**: Decimal integer literals (e.g., `10`, `25`).
- **Identifiers**: Variable names matching `[A-Za-z_][A-Za-z0-9_]*`.
- **Operators**: Arithmetic binary operators (`+`, `-`, `*`, `/`).
- **Assignment**: Single variable assignment using `=`.
- **Parentheses**: Explicit expression grouping using `(` and `)`.
- **Statement Terminator**: Semicolon (`;`) ending each assignment statement.

## Project Structure
```
IRGen/
├── .gitignore
├── AGENTS.md
├── README.md
├── main.py
├── docs/
├── examples/
├── irgen/
│   ├── __init__.py
│   ├── ast_nodes.py
│   ├── codegen.py
│   ├── ir_generator.py
│   ├── lexer.py
│   ├── optimizer.py
│   └── parser.py
├── tests/
│   ├── test_cases.py
│   └── test_control_flow.py
└── visualizer/
```

## How to Run
Run the main script from the project root and enter a source code statement when prompted:

```bash
python main.py
```

## Example
Running `python main.py` with input `x = a + b * c;`:

```text
Enter source code: x = a + b * c;

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

## Running Tests
Run all unit tests using Python's standard `unittest` framework:

```bash
python -m unittest discover tests
```

## Current Status
Phase 1 is complete. This includes tokenization, recursive descent parsing, AST construction, and TAC generation for arithmetic expressions and assignment statements.

## Planned Features (NOT Yet Implemented)
The following features are planned for future phases and are currently **NOT** implemented:
- Relational operators (`<`, `>`, `<=`, `>=`, `==`, `!=`)
- Control flow statements (`if` / `else` conditional branches)
- Iteration loops (`while` loops)
- Jump instructions and label management (`goto`, `L1:`, `if tN goto L1`)
- IR optimization (constant folding, dead-code elimination)
