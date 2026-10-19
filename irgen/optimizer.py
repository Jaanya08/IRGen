"""
TAC optimizer for IRGen.

This module implements optimization passes over Three-Address Code (TAC)
instructions, with a fixpoint driver that runs all passes repeatedly until
nothing changes (max 20 rounds).

Passes:
  1. Constant folding
  2. Algebraic simplification
  3. Constant and copy propagation (basic-block scoped)
  4. Common subexpression elimination (basic-block scoped)
  5. Copy fusion
  6. Dead temp elimination
"""

from irgen.tac import Instruction, parse_tac, format_tac, is_temp

_MAX_ROUNDS = 20


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _is_int(s):
    """
    Return True when *s* is a string representation of an integer literal,
    including negative values (e.g. '0', '42', '-3').

    Args:
        s (str): The string to test.

    Returns:
        bool: True if s is an integer literal, False otherwise.
    """
    try:
        int(s)
        return True
    except (ValueError, TypeError):
        return False


def _apply_op(op, left_val, right_val):
    """
    Evaluate a binary TAC operation on two integer values.

    Args:
        op (str): Operator string ('+', '-', '*', '/', '<', '>', '<=', '>=', '==', '!=').
        left_val (int): Left operand value.
        right_val (int): Right operand value.

    Returns:
        int: Result of the operation (relational ops yield 1 or 0).
    """
    if op == '+':
        return left_val + right_val
    elif op == '-':
        return left_val - right_val
    elif op == '*':
        return left_val * right_val
    elif op == '/':
        return left_val // right_val
    elif op == '<':
        return 1 if left_val < right_val else 0
    elif op == '>':
        return 1 if left_val > right_val else 0
    elif op == '<=':
        return 1 if left_val <= right_val else 0
    elif op == '>=':
        return 1 if left_val >= right_val else 0
    elif op == '==':
        return 1 if left_val == right_val else 0
    elif op == '!=':
        return 1 if left_val != right_val else 0
    else:
        raise ValueError(f"Unknown operator: '{op}'")


def _instrs_equal(a, b):
    """
    Compare two instruction lists for equality by their formatted TAC strings.

    Args:
        a (list of Instruction): First instruction list.
        b (list of Instruction): Second instruction list.

    Returns:
        bool: True if both lists produce identical formatted strings.
    """
    return format_tac(a) == format_tac(b)


# ---------------------------------------------------------------------------
# Pass 1: Constant folding
# ---------------------------------------------------------------------------

def _pass_constant_folding(instructions):
    """
    Fold binary instructions whose both operands are integer literals.

    For example: ``t1 = 2 * 3`` becomes ``t1 = 6``.
    Relational operators fold to 1 or 0.
    Division by zero is left unchanged.
    Labels, gotos, ifFalse, and copy instructions are not touched.

    Args:
        instructions (list of Instruction): Input instruction list.

    Returns:
        list of Instruction: New list with folded instructions.
    """
    result = []
    for instr in instructions:
        if (
            instr.kind == 'binary'
            and _is_int(instr.left)
            and _is_int(instr.right)
        ):
            lv = int(instr.left)
            rv = int(instr.right)
            # Never fold division by zero
            if instr.op == '/' and rv == 0:
                result.append(instr)
                continue
            folded = _apply_op(instr.op, lv, rv)
            result.append(Instruction(kind='copy', dst=instr.dst, src=str(folded)))
        else:
            result.append(instr)
    return result


# ---------------------------------------------------------------------------
# Pass 2: Algebraic simplification
# ---------------------------------------------------------------------------

def _pass_algebraic_simplification(instructions):
    """
    Simplify arithmetic identities without needing concrete values.

    Identities handled:
      ``x * 1``, ``1 * x``, ``x + 0``, ``0 + x``, ``x - 0``, ``x / 1``
      all collapse to a copy of x.
      ``x * 0``, ``0 * x`` collapse to a copy of literal 0.

    Labels, gotos, ifFalse, and non-matching binary instructions are unchanged.

    Args:
        instructions (list of Instruction): Input instruction list.

    Returns:
        list of Instruction: New list with simplified instructions.
    """
    result = []
    for instr in instructions:
        if instr.kind != 'binary':
            result.append(instr)
            continue

        left, op, right = instr.left, instr.op, instr.right
        dst = instr.dst
        simplified = None

        if op == '*':
            if right == '1':
                simplified = Instruction(kind='copy', dst=dst, src=left)
            elif left == '1':
                simplified = Instruction(kind='copy', dst=dst, src=right)
            elif left == '0' or right == '0':
                simplified = Instruction(kind='copy', dst=dst, src='0')
        elif op == '+':
            if right == '0':
                simplified = Instruction(kind='copy', dst=dst, src=left)
            elif left == '0':
                simplified = Instruction(kind='copy', dst=dst, src=right)
        elif op == '-':
            if right == '0':
                simplified = Instruction(kind='copy', dst=dst, src=left)
        elif op == '/':
            if right == '1':
                simplified = Instruction(kind='copy', dst=dst, src=left)

        result.append(simplified if simplified is not None else instr)
    return result


# ---------------------------------------------------------------------------
# Pass 3: Constant and copy propagation
# ---------------------------------------------------------------------------

def _pass_propagation(instructions):
    """
    Propagate constants and copy equivalences within each basic block.

    A basic block ends at (and restarts after) any label, goto, or ifFalse
    instruction — knowledge is completely reset at those boundaries.

    Within a block:
    - When a variable gets a known value (from a copy or binary whose result is
      a literal), record it in the ``known`` map.
    - Substitute recorded values into the *operands* of subsequent copy and
      binary instructions.
    - When a variable is reassigned, drop its own entry AND any entry in
      ``known`` whose value (copy source) equals that variable name.
    - The condition operand of an ``ifFalse`` instruction is NOT rewritten.
    - Labels, gotos, and ifFalse instructions themselves are never removed.

    Args:
        instructions (list of Instruction): Input instruction list.

    Returns:
        list of Instruction: New list with propagated constants/copies.
    """
    result = []
    # known maps variable_name -> value_string (int literal or variable name)
    known = {}

    def lookup(name):
        """Return the known substitution for *name*, or *name* itself if unknown."""
        return known.get(name, name)

    def invalidate(name):
        """Remove all knowledge about *name* and any copy that depended on it."""
        known.pop(name, None)
        # Also remove any entry x -> name (x was a copy of name, now stale)
        for k in list(known):
            if known[k] == name:
                del known[k]

    def reset_all():
        """Forget everything — called at every block boundary."""
        known.clear()

    for instr in instructions:
        if instr.kind == 'label':
            # Block boundary: reset then emit label unchanged
            reset_all()
            result.append(instr)

        elif instr.kind == 'goto':
            # Block boundary after the jump
            result.append(instr)
            reset_all()

        elif instr.kind == 'ifFalse':
            # Do NOT rewrite the condition operand; reset after
            result.append(instr)
            reset_all()

        elif instr.kind == 'copy':
            # Substitute the source with its known value first
            new_src = lookup(instr.src)
            new_instr = Instruction(kind='copy', dst=instr.dst, src=new_src)
            result.append(new_instr)
            # Invalidate old knowledge about dst, then record new value
            invalidate(instr.dst)
            known[instr.dst] = new_src

        elif instr.kind == 'binary':
            # Substitute both operands
            new_left = lookup(instr.left)
            new_right = lookup(instr.right)
            new_instr = Instruction(
                kind='binary',
                dst=instr.dst,
                left=new_left,
                op=instr.op,
                right=new_right,
            )
            result.append(new_instr)
            # Invalidate old knowledge about dst
            invalidate(instr.dst)
            # If after substitution both sides are literals, record the
            # computed value so later passes can fold it.
            if _is_int(new_left) and _is_int(new_right):
                if not (instr.op == '/' and int(new_right) == 0):
                    val = _apply_op(instr.op, int(new_left), int(new_right))
                    known[instr.dst] = str(val)
        else:
            result.append(instr)

    return result


# ---------------------------------------------------------------------------
# Pass 4: Common subexpression elimination (CSE)
# ---------------------------------------------------------------------------

# Operators treated as commutative for CSE key matching.
_COMMUTATIVE_OPS = frozenset({'+', '*', '==', '!='})


def _cse_key(left, op, right):
    """
    Build a canonical lookup key for a binary expression.

    For commutative operators (+, *, ==, !=) the operands are sorted
    lexicographically so that ``a + b`` and ``b + a`` share the same key.
    Non-commutative operators (-, /, <, >, <=, >=) keep the original order.

    Args:
        left (str): Left operand name or literal.
        op (str): Binary operator string.
        right (str): Right operand name or literal.

    Returns:
        tuple: Three-element key suitable for use as a dict key.
    """
    if op in _COMMUTATIVE_OPS and left > right:
        return (right, op, left)
    return (left, op, right)


def _pass_cse(instructions):
    """
    Eliminate common subexpressions within each basic block.

    A table maps canonical expression keys to the temporary variable that
    already holds the result.  When the same expression is encountered again
    in the same block, the binary instruction is replaced by a copy from the
    existing holder.

    Invalidation rules:
    - When any variable is assigned (copy or binary destination), remove all
      table entries whose *operands* include that variable and all entries
      whose *holder* is that variable.
    - The entire table is reset at every label, goto, and ifFalse.

    Only +, *, ==, != are treated as commutative for key matching.

    Args:
        instructions (list of Instruction): Input instruction list.

    Returns:
        list of Instruction: New list with duplicate expressions replaced by copies.
    """
    result = []
    # table: canonical_key -> holder_variable_name
    table = {}

    def _invalidate(var):
        """Remove table entries whose holder or operands reference *var*."""
        to_remove = [
            key for key, holder in table.items()
            if holder == var or var in (key[0], key[2])
        ]
        for k in to_remove:
            del table[k]

    def _reset():
        """Clear the entire CSE table at a basic-block boundary."""
        table.clear()

    for instr in instructions:
        if instr.kind in ('label', 'goto', 'ifFalse'):
            _reset()
            result.append(instr)

        elif instr.kind == 'binary':
            key = _cse_key(instr.left, instr.op, instr.right)
            if key in table:
                # Reuse existing result: replace with copy from holder
                holder = table[key]
                _invalidate(instr.dst)
                result.append(Instruction(kind='copy', dst=instr.dst, src=holder))
            else:
                # New expression: record it, then emit
                _invalidate(instr.dst)
                table[key] = instr.dst
                result.append(instr)

        elif instr.kind == 'copy':
            _invalidate(instr.dst)
            result.append(instr)

        else:
            result.append(instr)

    return result


# ---------------------------------------------------------------------------
# Pass 5: Copy fusion
# ---------------------------------------------------------------------------

def _count_reads(instructions):
    """
    Count how many times each name is *read* (used as a source operand) across
    the entire instruction list.

    Reads are counted from:
    - ``src`` of copy instructions
    - ``left`` and ``right`` of binary instructions
    - ``cond`` of ifFalse instructions

    Destination fields are NOT counted as reads.

    Args:
        instructions (list of Instruction): Full instruction list.

    Returns:
        dict: Mapping name -> read count (int).
    """
    counts = {}
    for instr in instructions:
        if instr.kind == 'copy':
            counts[instr.src] = counts.get(instr.src, 0) + 1
        elif instr.kind == 'binary':
            counts[instr.left] = counts.get(instr.left, 0) + 1
            counts[instr.right] = counts.get(instr.right, 0) + 1
        elif instr.kind == 'ifFalse':
            counts[instr.cond] = counts.get(instr.cond, 0) + 1
    return counts


def _pass_copy_fusion(instructions):
    """
    Fuse adjacent pairs ``tN = <expr>`` / ``x = tN`` into ``x = <expr>``.

    A fusion is valid only when *tN* is read exactly once in the entire
    program (i.e., only by the immediately following copy).  This is checked
    with a global read-count computed before any mutations.

    The fused instruction inherits the destination of the second instruction
    (``x``) and the source expression of the first (either a copy src or a
    binary left/op/right).

    Args:
        instructions (list of Instruction): Input instruction list.

    Returns:
        list of Instruction: New list with eligible adjacent pairs merged.
    """
    read_counts = _count_reads(instructions)
    result = []
    i = 0
    while i < len(instructions):
        instr = instructions[i]
        # Check fusion conditions
        if (
            instr.kind in ('copy', 'binary')
            and is_temp(instr.dst)
            and i + 1 < len(instructions)
        ):
            nxt = instructions[i + 1]
            if (
                nxt.kind == 'copy'
                and nxt.src == instr.dst
                and read_counts.get(instr.dst, 0) == 1
            ):
                # Build fused instruction with nxt.dst as destination
                if instr.kind == 'copy':
                    fused = Instruction(kind='copy', dst=nxt.dst, src=instr.src)
                else:  # binary
                    fused = Instruction(
                        kind='binary',
                        dst=nxt.dst,
                        left=instr.left,
                        op=instr.op,
                        right=instr.right,
                    )
                result.append(fused)
                i += 2
                continue
        result.append(instr)
        i += 1
    return result


# ---------------------------------------------------------------------------
# Pass 6: Dead temp elimination
# ---------------------------------------------------------------------------

def _pass_dead_temp_elimination(instructions):
    """
    Delete compiler temporary assignments whose value is never read.

    An instruction ``tN = ...`` (copy or binary) is removed when *tN* does
    not appear as a source operand anywhere in the program.

    Safety rules:
    - Assignments to *user* variables (non-temporaries) are never removed.
    - Labels, gotos, and ifFalse instructions are never removed.

    Args:
        instructions (list of Instruction): Input instruction list.

    Returns:
        list of Instruction: New list with dead temporary assignments removed.
    """
    read_vars = set()
    for instr in instructions:
        if instr.kind == 'copy':
            read_vars.add(instr.src)
        elif instr.kind == 'binary':
            read_vars.add(instr.left)
            read_vars.add(instr.right)
        elif instr.kind == 'ifFalse':
            read_vars.add(instr.cond)

    result = []
    for instr in instructions:
        if (
            instr.kind in ('copy', 'binary')
            and is_temp(instr.dst)
            and instr.dst not in read_vars
        ):
            # Dead temp: skip (do not emit)
            continue
        result.append(instr)
    return result


# ---------------------------------------------------------------------------
# Fixpoint driver
# ---------------------------------------------------------------------------

_PASSES = [
    ('constant_folding', _pass_constant_folding),
    ('algebraic_simplification', _pass_algebraic_simplification),
    ('propagation', _pass_propagation),
    ('cse', _pass_cse),
    ('copy_fusion', _pass_copy_fusion),
    ('dead_temp_elimination', _pass_dead_temp_elimination),
]


def optimize(lines):
    """
    Apply all six optimization passes in a fixpoint loop and return the result.

    Passes are applied in order (constant folding, algebraic simplification,
    propagation, CSE, copy fusion, dead-temp elimination). The loop repeats
    until a full round produces no change, or until ``_MAX_ROUNDS`` rounds
    have been completed.

    A log entry ``{"pass": name, "before": [...], "after": [...]}`` is
    appended only when a pass actually changes the instruction list.
    ``before`` and ``after`` are lists of formatted TAC strings.

    Args:
        lines (list of str or str): Input TAC instruction strings.

    Returns:
        tuple:
            - list of str: Optimized TAC instruction strings.
            - list of dict: Log of passes that produced changes.
    """
    instructions = parse_tac(lines)
    log = []

    for _ in range(_MAX_ROUNDS):
        changed_this_round = False

        for pass_name, pass_fn in _PASSES:
            before = instructions
            after = pass_fn(before)

            if not _instrs_equal(before, after):
                log.append({
                    'pass': pass_name,
                    'before': format_tac(before),
                    'after': format_tac(after),
                })
                instructions = after
                changed_this_round = True

        if not changed_this_round:
            break

    return format_tac(instructions), log
