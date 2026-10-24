# IRGen: A Lightweight Intermediate Code Generation System Using Three-Address Code

## Overview
IRGen is a lightweight compiler front-end and intermediate representation system built in Python using standard library modules only. It converts statements and control-flow constructs in a custom programming language into machine-independent Three-Address Code (TAC), optimizes the TAC through multiple iterative passes, executes TAC via a built-in interpreter, and generates target assembly for an imaginary register machine.

## Pipeline
```
Source -> Lexer -> Tokens -> Parser -> AST -> IR Generator -> TAC -> Optimizer -> Assembly
                                                │
                                                └──> TAC Interpreter (Execution & Testing)
```

## Features

### Front-End & Control Flow (Phases 1 & 2)
- **Integer numbers**: Decimal integer literals (e.g., `10`, `25`, negative literals `-3`).
- **Identifiers**: Variable names matching `[A-Za-z_][A-Za-z0-9_]*` (compiler temporaries `t[0-9]+` reserved).
- **Arithmetic Operators**: Binary operators (`+`, `-`, `*`, `/`) with standard precedence (`*`, `/` over `+`, `-`) and left-associativity.
- **Relational Operators**: Comparisons (`<`, `>`, `<=`, `>=`, `==`, `!=`).
- **Assignments & Blocks**: Statements terminated by `;`, blocks enclosed in `{ ... }`, parenthesized sub-expressions `( ... )`.
- **Conditionals & Loops**: `if (cond) { ... }`, `if (cond) { ... } else { ... }`, `while (cond) { ... }`, and `for (init; cond; update) { ... }`.
- **For Loop Support**: Full support for `for (init; cond; update) { ... }` with optional components, translating into clean TAC loop blocks with deterministic labels.
- **TAC Emission**: Instruction representations with dedicated temp (`t1`, `t2`, ...) and label (`L1`, `L2`, ...) counters, conditional jumps (`ifFalse tN goto Lx`), unconditional jumps (`goto Lx`), and labels (`Lx:`).

### Optimization & Code Generation (Phase 3)
- **TAC Parser & Formatter (`irgen/tac.py`)**: Structured representation of TAC instructions supporting round-trip formatting.
- **TAC Interpreter (`irgen/interpreter.py`)**: Direct execution of TAC with environment tracking, integer division, relational evaluations, and step limits.
- **6-Pass Fixpoint Optimizer (`irgen/optimizer.py`)**: Iterates passes repeatedly until reaching a fixpoint (max 20 rounds):
  1. *Constant Folding*: Pre-computes arithmetic and relational operations on constants (protects against division by zero).
  2. *Algebraic Simplification*: Simplifies identities (`x*1`, `x+0`, `x-0`, `x/1` -> `x`; `x*0` -> `0`).
  3. *Constant & Copy Propagation*: Propagates known values inside basic blocks; resets at labels/jumps.
  4. *Common Subexpression Elimination (CSE)*: Eliminates duplicate binary computations within basic blocks; handles commutative operators (`+`, `*`, `==`, `!=`).
  5. *Copy Fusion*: Merges single-use temporary definitions into destination variable assignments.
  6. *Dead Temporary Elimination*: Removes dead temporaries (`tN = ...`) not referenced elsewhere.
- **Assembly Codegen (`irgen/codegen.py`)**: Emits assembly instructions for an imaginary register machine using scratch registers `R1` and `R2`, immediate operands (`#N`), memory variables, and jump instructions.
- **AST Serialization**: `to_dict()` methods on all AST nodes for clean JSON export.

### Web Student Learning Portal (`server.py` or `python main.py --serve`)
- **Interactive Web Interface (`web/index.html`)**: Sleek educational compiler laboratory designed for students.
- **Full Compiler Pipeline Visibility**:
  - Live Token Stream Table (with category filtering & lexeme search)
  - Interactive Abstract Syntax Tree (Hierarchical Tree, Indented Outline, and JSON)
  - Three-Address Code (TAC) Viewer with line numbers
  - Optimizer Showcase with pass-by-pass Before vs After code diffs
  - Target Machine Assembly Viewer with ISA reference
  - Virtual Machine (Interpreter) live simulation showing computed variable environments and semantic equivalence proofs
- **Zero External Dependencies**: Powered by Python 3's built-in `http.server`.

## Project Structure
```
IRGen/
├── .gitignore
├── AGENTS.md
├── README.md
├── main.py                 # CLI interface (includes --serve flag)
├── server.py               # Standalone HTTP server for student portal
├── web/
│   ├── index.html          # Interactive Student Learning Portal
│   ├── style.css           # Refined non-dark, non-minimalist academic theme
│   └── app.js              # Client application & pipeline visualizations
├── docs/
├── examples/
│   ├── ifelse.txt
│   ├── loop.txt
│   └── for_loop.txt
├── irgen/
│   ├── __init__.py
│   ├── ast_nodes.py        # AST nodes with to_dict() export (Number, ID, BinOp, Assign, If, While, For)
│   ├── codegen.py          # TAC to assembly generator
│   ├── interpreter.py      # TAC runtime interpreter
│   ├── ir_generator.py     # AST to TAC generator
│   ├── lexer.py            # Tokenizer
│   ├── optimizer.py        # 6-pass optimization engine
│   ├── parser.py           # Recursive descent parser
│   ├── service.py          # Unified compilation pipeline service
│   └── tac.py              # TAC instruction parser/formatter
├── tests/
│   ├── test_cases.py       # Phase 1 expression & error tests
│   ├── test_codegen.py     # Phase 3 assembly codegen tests
│   ├── test_control_flow.py# Phase 2 control flow & block tests
│   ├── test_for_loop.py    # For loop AST, TAC, optimizer, and codegen tests
│   ├── test_interpreter.py # Phase 3 TAC interpreter tests
│   ├── test_optimizer.py   # Phase 3 optimizer & equivalence tests
│   └── test_server.py      # Web service & API tests
```

## How to Run

### Web Student Learning Portal

Launch the student portal and open it in your browser:

```bash
# Launch via main.py:
python main.py --serve

# Or launch directly with server.py:
python server.py

# Specify a custom port if desired:
python server.py 8080
```
Then visit: **`http://localhost:8000/`** (or your selected port).

### Command-Line Interface (`main.py`)

Run `main.py` by providing an optional source file path or interactively via standard input:

```bash
# Basic run (displays tokens and unoptimized TAC)
python main.py examples/loop.txt

# Run for loop example with optimization, assembly codegen, and instruction statistics
python main.py examples/for_loop.txt --optimize --asm --stats

# Output structured JSON (tokens, AST, TAC, optimized TAC, log, assembly, stats)
python main.py examples/for_loop.txt --json
```

### CLI Flags

| Flag | Description |
|---|---|
| `<file>` | Optional path to input file. If omitted, reads from stdin until an empty line. |
| `--optimize` | Runs the 6-pass optimizer and displays optimized TAC. |
| `--asm` | Generates and prints assembly for an imaginary register machine. |
| `--stats` | Displays instruction count metrics before and after optimization. |
| `--json` | Emits a single JSON object with compiler stages or error details. |
| `--serve` | Launches the interactive student web learning portal server. |
| `--port` | Port number for the student portal server (default: 8000). |

## Examples

### Example 1: Arithmetic Expression with Optimization & Assembly
Running:
```bash
python main.py --optimize --asm --stats
```
Input:
```text
x = 2 * 3 + a;
```

Output:
```text
TOKENS:
('ID', 'x')
('ASSIGN', '=')
('NUMBER', '2')
('OP', '*')
('NUMBER', '3')
('OP', '+')
('ID', 'a')
('SEMICOLON', ';')

THREE-ADDRESS CODE:
t1 = 2 * 3
t2 = t1 + a
x = t2

OPTIMIZED TAC:
x = 6 + a

ASSEMBLY:
LOAD R1, #6
LOAD R2, a
ADD R1, R2
STORE x, R1

STATS:
Instructions before: 3
Instructions after:  1
Removed: 2
```

### Example 2: Control Flow (`while` loop)
Running `python main.py examples/loop.txt --optimize --asm --stats`:

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

OPTIMIZED TAC:
L1:
t1 = a < b
ifFalse t1 goto L2
a = a + 1
goto L1
L2:

ASSEMBLY:
L1:
LOAD R1, a
LOAD R2, b
CMPLT R1, R2
STORE t1, R1
LOAD R1, t1
JZ R1, L2
LOAD R1, a
LOAD R2, #1
ADD R1, R2
STORE a, R1
JMP L1
L2:

STATS:
Instructions before: 7
Instructions after:  6
Removed: 1
```

## Running Tests

Run the full test suite with Python's standard `unittest` discovery runner:

```bash
python -m unittest discover tests -v
```

All 79 tests across all phases pass:
- **`tests/test_cases.py`** (7 tests): Lexer, parser, and basic expressions.
- **`tests/test_control_flow.py`** (13 tests): Conditionals, while loops, blocks, reserved temp validation.
- **`tests/test_for_loop.py`** (12 tests): For loop AST nodes, TAC emission, nested loops, interpreter execution, optimizer, assembly, and syntax errors.
- **`tests/test_interpreter.py`** (7 tests): TAC execution semantics, relational evaluation, step limits, errors.
- **`tests/test_optimizer.py`** (16 tests): All 6 optimization passes, fixpoint iterations, expected results, idempotence, randomized semantic equivalence.
- **`tests/test_codegen.py`** (19 tests): Assembly generation, scratch register allocation, immediates, jump conditions, comparison opcodes.
- **`tests/test_server.py`** (5 tests): Web API endpoints, compilation pipeline service, and error diagnostics.

## Current Status
- **Phase 1 (Expressions & Assignments)**: Complete.
- **Phase 2 (Control Flow & Multi-statement Programs)**: Complete.
- **Phase 3 (Optimization, Codegen, Interpreter & CLI Export)**: Complete.
- **Phase 4 (For Loops & Web Student Learning Portal)**: Complete.
