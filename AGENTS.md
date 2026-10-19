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

## Phase 2 — control flow (build this now)

Phase 1 behaviour and all 7 existing tests must keep passing.

### New syntax
- Relational operators: `<  >  <=  >=  ==  !=`
- `if (cond) { ... }` and `if (cond) { ... } else { ... }`
- `while (cond) { ... }`
- Blocks use `{ }` and hold zero or more statements. A program is a list of statements.
- Keywords `if`, `else`, `while` must not be lexed as identifiers.
- `=` is assignment, `==` is comparison. Lex two-character operators first.

### New tokens
`RELOP`, `KEYWORD` (if, else, while), `LBRACE`, `RBRACE`.

### Updated grammar
```
program    -> statement*
statement  -> assignment | if_stmt | while_stmt
block      -> '{' statement* '}'
if_stmt    -> 'if' '(' condition ')' block ('else' block)?
while_stmt -> 'while' '(' condition ')' block
condition  -> expression (RELOP expression)?
assignment -> ID '=' expression ';'
(expression, term, factor unchanged)
```

### New AST nodes
`Program(statements)`, `Block(statements)`, `If(condition, then_block, else_block)`,
`While(condition, body)`. A comparison reuses `BinaryExpression`.

### IR rules
- `new_label()` returns `L1`, `L2`, ... (separate counter from temps).
- Jump instructions: `ifFalse tN goto Lx`, `goto Lx`, and label lines `Lx:`.

### Expected TAC

`if (a > b) { x = a; } else { x = b; }`
```
t1 = a > b
ifFalse t1 goto L1
x = a
goto L2
L1:
x = b
L2:
```

`if (a > b) { x = a; }`
```
t1 = a > b
ifFalse t1 goto L1
x = a
L1:
```

`while (a < b) { a = a + 1; }`
```
L1:
t1 = a < b
ifFalse t1 goto L2
t2 = a + 1
a = t2
goto L1
L2:
```

### CLI
`main.py` accepts an optional file path (`python main.py examples/loop.txt`). With no argument, it reads multiple lines from the terminal until an empty line.

## Phase 3 — optimization, codegen, export (build this now)

Phases 1 and 2 must keep working. All 19 existing tests must keep passing.
Python 3 standard library only.

### New files (add to structure)
```
irgen/tac.py          # parse TAC strings into Instruction objects and format them back
irgen/interpreter.py  # run TAC to verify behaviour
irgen/optimizer.py    # optimization passes
irgen/codegen.py      # TAC -> assembly for an imaginary register machine
tests/test_optimizer.py, tests/test_codegen.py, tests/test_interpreter.py
```

### tac.py
Instruction kinds: label (`L1:`), goto (`goto L1`), ifFalse (`ifFalse t1 goto L1`),
copy (`x = y`), binary (`t1 = a + b`, ops: + - * / < > <= >= == !=).
`parse_tac(lines)` returns a list of Instruction; `format_tac(instrs)` returns strings.
parse then format must give back the original lines. A name is a temp if it matches `t\d+`.

### interpreter.py
`run_tac(lines, env=None, max_steps=10000)` executes TAC and returns the final
variable dictionary. Relational ops give 1 or 0. `/` is integer (floor) division.
Division by zero raises ZeroDivisionError. Exceeding max_steps raises RuntimeError.
Unset variables are an error (NameError) unless provided in env.

### optimizer.py
`optimize(lines)` returns `(optimized_lines, log)` where log is a list of
`{"pass": name, "before": [...], "after": [...]}` recorded only when a pass changed something.
Run all passes repeatedly until nothing changes (max 20 rounds). Passes:
1. Constant folding: `t1 = 2 * 3` -> `t1 = 6`; relational ops fold to 1 or 0.
   Never fold division by zero (leave it unchanged).
2. Algebraic simplification: `x*1`, `1*x`, `x+0`, `0+x`, `x-0`, `x/1` -> copy of x; `x*0`, `0*x` -> 0.
3. Constant and copy propagation inside a basic block. A basic block ends at
   any label, goto or ifFalse. Forget all known values at every label and after
   every jump. Forget a variable's known value when it is reassigned. Never
   propagate across a label (loops would break).
4. Common subexpression elimination inside a basic block: if the same
   `a op b` is computed again and neither a nor b was reassigned in between,
   replace the second computation with a copy of the first result.
5. Copy fusion: `tN = expr` immediately followed by `x = tN`, where tN is used
   nowhere else, becomes `x = expr`.
6. Dead temp elimination: delete `tN = ...` when tN is never read anywhere.
   Never delete assignments to user variables (non-temps).
Labels, gotos and ifFalse are never removed.

### Expected results
| Source | Optimized TAC |
|---|---|
| `x = 2 * 3 + a;` | `x = 6 + a` |
| `x = a * 1 + 0;` | `x = a` |
| `a = 5; b = a * 2;` | `a = 5` / `b = 10` |
| `x = a * b; y = a * b;` | `t1 = a * b` / `x = t1` / `y = t1` |
| `while (a < b) { x = 2 * 3; a = a + 1; }` | `L1:` / `t1 = a < b` / `ifFalse t1 goto L2` / `x = 6` / `t3 = a + 1` / `a = t3` / `goto L1` / `L2:` (the loop condition and `a` must NOT be folded) |

(Temp numbers in results are whatever remains after removal; do not renumber.)

### codegen.py
`generate_asm(lines)` returns assembly lines. Variables live in memory; R1 and R2
are scratch registers. Immediates are written `#6`.
```
t1 = b * c      ->  LOAD R1, b / LOAD R2, c / MUL R1, R2 / STORE t1, R1
x = t1          ->  LOAD R1, t1 / STORE x, R1
x = 6           ->  LOAD R1, #6 / STORE x, R1
t1 = a < b      ->  LOAD R1, a / LOAD R2, b / CMPLT R1, R2 / STORE t1, R1
ifFalse t1 goto L1  ->  LOAD R1, t1 / JZ R1, L1
goto L2         ->  JMP L2
L1:             ->  L1:
```
Opcodes: ADD SUB MUL DIV, CMPLT CMPGT CMPLE CMPGE CMPEQ CMPNE (leave 1 or 0 in R1).

### Export and CLI
Add `to_dict()` to every AST node (`{"node": "BinaryExpression", ...}` with children nested).
`main.py` flags: `--optimize`, `--asm`, `--json`, `--stats`. Examples:
`python main.py examples/loop.txt --optimize --asm --stats`
`--stats` prints instruction counts before and after optimization.
`--json` prints one JSON object with keys: tokens, ast, tac, optimized_tac,
optimization_log, assembly, stats. On error print `{"error": "<message>"}`.
Without flags, behave exactly as before.
