# IRGen — Intermediate Code Generator

A small compiler front-end in **Python 3 (standard library only)**. It converts statements in a tiny custom language into **Three-Address Code (TAC)**, a machine-independent intermediate representation.

This is a student project (Compiler Design). Keep code simple, readable and well-commented. Do not over-engineer.

## Rules for the agent

1. Work on **one component at a time** and stop for review. Do not build ahead.
2. **Stay inside the current scope** (Phase 1 below). Do not add control flow, optimization or code generation unless asked.
3. No external dependencies. Tests must run with `python -m unittest` (or plain `python tests/test_cases.py`).
4. Do not change the folder structure or file names without asking.
5. Raise clear errors (`SyntaxError` with a useful message) for bad input instead of failing silently.
6. After each change, run the tests and show the output.

## Pipeline

```
Source -> Lexer -> Tokens -> Parser -> AST -> IR Generator -> TAC
```

## Folder structure

```
IRGen/
├── AGENTS.md
├── README.md
├── main.py                 # CLI: reads input, prints tokens and TAC
├── irgen/
│   ├── __init__.py
│   ├── lexer.py            # tokenize(code) -> list of (TYPE, value)
│   ├── ast_nodes.py        # Number, Identifier, BinaryExpression, Assignment
│   ├── parser.py           # Parser(tokens).parse() -> AST
│   ├── ir_generator.py     # IRGenerator: generate(node), get_ir()
│   ├── optimizer.py        # (Phase 3, empty for now)
│   └── codegen.py          # (Phase 3, empty for now)
├── tests/
│   ├── test_cases.py
│   └── test_control_flow.py   # (Phase 2)
├── examples/
├── docs/
└── visualizer/             # (future)
```

Run from the project root: `python main.py`. Imports look like `from irgen.lexer import tokenize`.

## Phase 1 — current scope (build this)

Supported language:
- Identifiers: `[A-Za-z_][A-Za-z0-9_]*`
- Integer numbers: `10`, `25`
- Operators: `+  -  *  /`
- Assignment `=`, parentheses `( )`, statement end `;`
- One assignment statement per input line

### Tokens

`NUMBER`, `ID`, `OP` (`+ - * /`), `ASSIGN`, `LPAREN`, `RPAREN`, `SEMICOLON`.
Whitespace is skipped. Any other character raises `SyntaxError("Unexpected character: ...")`.
`tokenize()` must **return** the token list. Note the parenthesis regexes must be escaped: `\(` and `\)`.

### Grammar (recursive descent, one method per rule)

```
assignment -> ID '=' expression ';'
expression -> term (('+' | '-') term)*
term       -> factor (('*' | '/') factor)*
factor     -> NUMBER | ID | '(' expression ')'
```

`*` and `/` bind tighter than `+` and `-`. Operators of equal precedence are left-associative.

### AST nodes

| Node | Fields |
|---|---|
| `Number` | `value` |
| `Identifier` | `name` |
| `BinaryExpression` | `left`, `operator`, `right` |
| `Assignment` | `name`, `expression` |

### IR generator

- `new_temp()` returns `t1`, `t2`, ... (counter starts at 0, first temp is `t1`).
- `generate(node)` is a recursive tree walk:
  - `Number` returns its value; `Identifier` returns its name (no instruction emitted).
  - `BinaryExpression` generates left, then right, makes a new temp and appends `tN = left op right`.
  - `Assignment` generates the expression and appends `name = <result>`.
- `get_ir()` returns the list of instruction strings.

### TAC format

One instruction per line, e.g. `t1 = b * c`. Max three operands per instruction.

## Test cases (must all pass)

| Input | Expected TAC |
|---|---|
| `x = a + b;` | `t1 = a + b` / `x = t1` |
| `x = a * b + c;` | `t1 = a * b` / `t2 = t1 + c` / `x = t2` |
| `x = (a + b) * c;` | `t1 = a + b` / `t2 = t1 * c` / `x = t2` |
| `result = a + b * c - d;` | `t1 = b * c` / `t2 = a + t1` / `t3 = t2 - d` / `result = t3` |

Also test error cases: unexpected character (`x = a $ b;`), missing semicolon, unbalanced parenthesis.

Expected CLI output for `x = a + b * c;`:

```
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

## Phase 2 — control flow (do NOT build yet)

Relational operators `< > <= >= == !=`, `if / else`, `while`, labels (`L1:`), `goto`, `if tN goto L1`. Needs `new_label()`.

Target output for `if (a > b) x = a; else x = b;`:

```
t1 = a > b
if t1 goto L1
goto L2
L1:
x = a
goto L3
L2:
x = b
L3:
```

## Phase 3 — future (do NOT build yet)

Optimization (constant folding, dead-code elimination), IR visualization, target code generation.
