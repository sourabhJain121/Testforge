"""
mutator.py - Deterministic AST-based Mutation Testing Engine.

Author: Shreshth (Module 2) & Sourabh
System: Autonomous Multi-Agent Hardening Engine
Milestone: 2 (AST-Aware Mutation & Equivalent-Mutant Analysis)

Implements 10 deterministic, syntax-aware AST mutation categories:
  1. Comparison operator inversion (COMP_OP: e.g. > to <=, == to !=)
  2. Boundary relational swaps (BOUNDARY_SWAP: e.g. < to <=, > to >=)
  3. Off-by-one constant shifts (OFF_BY_ONE: e.g. n to n + 1 or n - 1 in comparisons)
  4. Arithmetic operator swapping (ARITH_OP: e.g. + to -, * to //)
  5. Logical connective swaps (LOGICAL_CONN: e.g. and to or, or to and)
  6. Math function & precision flips (MATH_FUNC: e.g. round(x, 2) to round(x, 1), strip abs(x))
  7. Conditional inversion (COND_INV: e.g. if x -> if not x)
  8. Return value mutation (RETURN_VAL: e.g. return True -> return False, return x -> return None)
  9. Constant literal mutations (CONST_VAL: e.g. True <-> False, 0 <-> 1, str -> "")
 10. Safe Exception handling mutation (EXCEPT_HANDLER: e.g. except ValueError -> except TypeError)

Held-Out / Evaluation Operator Categories (Stage 1.5 & Sub-Task 5.6):
 11. Bitwise operator swapping (BITWISE_OP: e.g. & to |, ^ to &, << to >>)
 12. Exception class raising swap (EXCEPTION_SWAP: e.g. raise ValueError -> raise TypeError)
 13. Statement deletion (STATEMENT_DELETION: e.g. total += x -> pass, call() -> pass)
"""

from __future__ import annotations

import ast
import difflib
from typing import Dict, List, Optional, Set, Tuple, Type

from testforge.equivalence import EquivalenceClassification, EquivalentMutantAnalyzer
from testforge.state import MutantRecord


class MutationTransformer(ast.NodeTransformer):
    """
    AST transformer that mutates exactly one targeted mutation site per pass.
    When target_node_id == 0, acts as an accurate mutation site inspector.
    Supports restricting mutations to specific line numbers via target_lines.
    Tracks exact original and mutated expressions for full provenance.
    """
    def __init__(
        self,
        target_node_id: int,
        target_lines: Optional[List[int]] = None,
        include_held_out: bool = False,
        allowed_line_ranges: Optional[List[Tuple[int, int]]] = None,
    ):
        self.target_node_id = target_node_id
        self.target_lines: Optional[Set[int]] = set(target_lines) if target_lines else None
        self.allowed_line_ranges: Optional[List[Tuple[int, int]]] = allowed_line_ranges
        self.include_held_out = include_held_out
        self.current_node_id = 0
        self.sites: Dict[int, str] = {}
        self.applied = False
        self.mutant_type: str = ""
        self.line_number: int = 1
        self.original_expr: Optional[str] = None
        self.mutated_expr: Optional[str] = None
        self._in_compare = False
        self._in_docstring = False

    def _line_allowed(self, node: ast.AST) -> bool:
        lineno = getattr(node, "lineno", None)
        if lineno is not None:
            if self.target_lines is not None and lineno not in self.target_lines:
                return False
            if self.allowed_line_ranges is not None:
                if not any(start <= lineno <= end for start, end in self.allowed_line_ranges):
                    return False
        return True

    def _inc_id(self, op_name: str) -> bool:
        self.current_node_id += 1
        self.sites[self.current_node_id] = op_name
        return self.current_node_id == self.target_node_id and not self.applied

    def visit(self, node: ast.AST) -> ast.AST:
        if getattr(node, "mutatable", True) is False:
            return self.generic_visit(node)
        return super().visit(node)

    def _mark_applied(self, node: ast.AST, mutant_type: str, orig_node: Optional[ast.AST] = None, mutated_node: Optional[ast.AST] = None):
        self.applied = True
        self.mutant_type = mutant_type
        self.line_number = getattr(node, "lineno", 1)
        try:
            self.original_expr = ast.unparse(orig_node or node)
        except Exception:
            self.original_expr = None
        try:
            self.mutated_expr = ast.unparse(mutated_node) if mutated_node is not None else None
        except Exception:
            self.mutated_expr = None

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        if not self._line_allowed(node):
            return self.generic_visit(node)
        comp_map: Dict[Type[ast.AST], Type[ast.AST]] = {
            ast.Gt: ast.LtE,
            ast.Lt: ast.GtE,
            ast.GtE: ast.Lt,
            ast.LtE: ast.Gt,
            ast.Eq: ast.NotEq,
            ast.NotEq: ast.Eq,
            ast.In: ast.NotIn,
            ast.NotIn: ast.In,
            ast.Is: ast.IsNot,
            ast.IsNot: ast.Is
        }
        boundary_map: Dict[Type[ast.AST], Type[ast.AST]] = {
            ast.Gt: ast.GtE,
            ast.Lt: ast.LtE,
            ast.GtE: ast.Gt,
            ast.LtE: ast.Lt
        }

        # 1. Comparison Operator Inversion (COMP_OP)
        for i, op in enumerate(node.ops):
            op_cls = op.__class__
            if op_cls in comp_map:
                if self._inc_id("COMP_OP"):
                    new_ops = list(node.ops)
                    new_ops[i] = comp_map[op_cls]()
                    new_node = ast.Compare(left=node.left, ops=new_ops, comparators=node.comparators)
                    ast.copy_location(new_node, node)
                    self._mark_applied(node, "COMP_OP", orig_node=node, mutated_node=new_node)
                    return new_node

        # 2. Boundary Relational Swaps (BOUNDARY_SWAP: < to <=, > to >=)
        for i, op in enumerate(node.ops):
            op_cls = op.__class__
            if op_cls in boundary_map:
                if self._inc_id("BOUNDARY_SWAP"):
                    new_ops = list(node.ops)
                    new_ops[i] = boundary_map[op_cls]()
                    new_node = ast.Compare(left=node.left, ops=new_ops, comparators=node.comparators)
                    ast.copy_location(new_node, node)
                    self._mark_applied(node, "BOUNDARY_SWAP", orig_node=node, mutated_node=new_node)
                    return new_node

        # 3. Off-By-One Mutations (OFF_BY_ONE: numeric constants n -> n+1, n-1)
        # Check left operand
        if isinstance(node.left, ast.Constant) and isinstance(node.left.value, (int, float)) and not isinstance(node.left.value, bool):
            val = node.left.value
            delta = 1.0 if isinstance(val, float) else 1
            # Site n + 1
            if self._inc_id("OFF_BY_ONE"):
                new_left = ast.Constant(value=val + delta)
                new_node = ast.Compare(left=new_left, ops=node.ops, comparators=node.comparators)
                ast.copy_location(new_node, node)
                self._mark_applied(node, "OFF_BY_ONE", orig_node=node, mutated_node=new_node)
                return new_node
            # Site n - 1
            if self._inc_id("OFF_BY_ONE"):
                new_left = ast.Constant(value=val - delta)
                new_node = ast.Compare(left=new_left, ops=node.ops, comparators=node.comparators)
                ast.copy_location(new_node, node)
                self._mark_applied(node, "OFF_BY_ONE", orig_node=node, mutated_node=new_node)
                return new_node

        # Check comparators
        for j, comp in enumerate(node.comparators):
            if isinstance(comp, ast.Constant) and isinstance(comp.value, (int, float)) and not isinstance(comp.value, bool):
                val = comp.value
                delta = 1.0 if isinstance(val, float) else 1
                # Site n + 1
                if self._inc_id("OFF_BY_ONE"):
                    new_comps = list(node.comparators)
                    new_comps[j] = ast.Constant(value=val + delta)
                    new_node = ast.Compare(left=node.left, ops=node.ops, comparators=new_comps)
                    ast.copy_location(new_node, node)
                    self._mark_applied(node, "OFF_BY_ONE", orig_node=node, mutated_node=new_node)
                    return new_node
                # Site n - 1
                if self._inc_id("OFF_BY_ONE"):
                    new_comps = list(node.comparators)
                    new_comps[j] = ast.Constant(value=val - delta)
                    new_node = ast.Compare(left=node.left, ops=node.ops, comparators=new_comps)
                    ast.copy_location(new_node, node)
                    self._mark_applied(node, "OFF_BY_ONE", orig_node=node, mutated_node=new_node)
                    return new_node

        self._in_compare = True
        try:
            res = self.generic_visit(node)
        finally:
            self._in_compare = False
        return res

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        if not self._line_allowed(node):
            return self.generic_visit(node)
        arith_map: Dict[Type[ast.AST], Type[ast.AST]] = {
            ast.Add: ast.Sub,
            ast.Sub: ast.Add,
            ast.Mult: ast.FloorDiv,
            ast.Div: ast.Mult,
            ast.FloorDiv: ast.Mult,
            ast.Mod: ast.Mult,
            ast.Pow: ast.Mult
        }
        op_cls = node.op.__class__
        if op_cls in arith_map:
            if self._inc_id("ARITH_OP"):
                new_node = ast.BinOp(left=node.left, op=arith_map[op_cls](), right=node.right)
                ast.copy_location(new_node, node)
                self._mark_applied(node, "ARITH_OP", orig_node=node, mutated_node=new_node)
                return new_node

        # 11. Bitwise Operator Swapping (BITWISE_OP - Held-out evaluation operator)
        if self.include_held_out:
            bitwise_map: Dict[Type[ast.AST], Type[ast.AST]] = {
                ast.BitAnd: ast.BitOr,
                ast.BitOr: ast.BitAnd,
                ast.BitXor: ast.BitAnd,
                ast.LShift: ast.RShift,
                ast.RShift: ast.LShift,
            }
            if op_cls in bitwise_map:
                if self._inc_id("BITWISE_OP"):
                    new_node = ast.BinOp(left=node.left, op=bitwise_map[op_cls](), right=node.right)
                    ast.copy_location(new_node, node)
                    self._mark_applied(node, "BITWISE_OP", orig_node=node, mutated_node=new_node)
                    return new_node
        return self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> ast.AST:
        if not self._line_allowed(node):
            return self.generic_visit(node)
        # Logical Connective Swaps (LOGICAL_CONN: and <-> or)
        if isinstance(node.op, ast.And):
            if self._inc_id("LOGICAL_CONN"):
                new_node = ast.BoolOp(op=ast.Or(), values=node.values)
                ast.copy_location(new_node, node)
                self._mark_applied(node, "LOGICAL_CONN", orig_node=node, mutated_node=new_node)
                return new_node
        elif isinstance(node.op, ast.Or):
            if self._inc_id("LOGICAL_CONN"):
                new_node = ast.BoolOp(op=ast.And(), values=node.values)
                ast.copy_location(new_node, node)
                self._mark_applied(node, "LOGICAL_CONN", orig_node=node, mutated_node=new_node)
                return new_node
        return self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> ast.AST:
        if not self._line_allowed(node):
            return self.generic_visit(node)
        # Math Function & Precision Flips (MATH_FUNC)
        if isinstance(node.func, ast.Name):
            # round(x, 2) -> round(x, 1)
            if node.func.id == "round" and len(node.args) >= 2:
                prec_arg = node.args[1]
                if isinstance(prec_arg, ast.Constant) and isinstance(prec_arg.value, int) and prec_arg.value > 0:
                    if self._inc_id("MATH_FUNC"):
                        new_args = list(node.args)
                        new_args[1] = ast.Constant(value=prec_arg.value - 1)
                        new_node = ast.Call(func=node.func, args=new_args, keywords=node.keywords)
                        ast.copy_location(new_node, node)
                        self._mark_applied(node, "MATH_FUNC", orig_node=node, mutated_node=new_node)
                        return new_node
            # abs(x) -> x
            elif node.func.id == "abs" and len(node.args) == 1:
                if self._inc_id("MATH_FUNC"):
                    new_node = node.args[0]
                    ast.copy_location(new_node, node)
                    self._mark_applied(node, "MATH_FUNC", orig_node=node, mutated_node=new_node)
                    return new_node
        return self.generic_visit(node)

    def visit_If(self, node: ast.If) -> ast.AST:
        if not self._line_allowed(node):
            return self.generic_visit(node)
        if self._inc_id("COND_INV"):
            new_test = ast.UnaryOp(op=ast.Not(), operand=node.test)
            new_node = ast.If(test=new_test, body=node.body, orelse=node.orelse)
            ast.copy_location(new_node, node)
            self._mark_applied(node, "COND_INV", orig_node=node, mutated_node=new_node)
            return new_node
        return self.generic_visit(node)

    def visit_Return(self, node: ast.Return) -> ast.AST:
        if not self._line_allowed(node):
            return self.generic_visit(node)
        if self._inc_id("RETURN_VAL"):
            if isinstance(node.value, ast.Constant):
                if node.value.value is True:
                    new_val = ast.Constant(value=False)
                elif node.value.value is False:
                    new_val = ast.Constant(value=True)
                else:
                    new_val = ast.Constant(value=None)
            else:
                new_val = ast.Constant(value=None)
            new_node = ast.Return(value=new_val)
            ast.copy_location(new_node, node)
            self._mark_applied(node, "RETURN_VAL", orig_node=node, mutated_node=new_node)
            return new_node
        return self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> ast.AST:
        # 13. Statement Deletion Mutations (STATEMENT_DELETION - Extended operator)
        if self.include_held_out:
            if not self._line_allowed(node):
                return self.generic_visit(node)
            if self._inc_id("STATEMENT_DELETION"):
                new_node = ast.Pass()
                ast.copy_location(new_node, node)
                self._mark_applied(node, "STATEMENT_DELETION", orig_node=node, mutated_node=new_node)
                return new_node
        return self.generic_visit(node)

    def visit_Expr(self, node: ast.Expr) -> ast.AST:
        # Detect and preserve module/function docstrings
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            self._in_docstring = True
            try:
                return self.generic_visit(node)
            finally:
                self._in_docstring = False

        # Statement Deletion on standalone function/method calls (when include_held_out)
        if self.include_held_out and isinstance(node.value, ast.Call):
            if not self._line_allowed(node):
                return self.generic_visit(node)
            if self._inc_id("STATEMENT_DELETION"):
                new_node = ast.Pass()
                ast.copy_location(new_node, node)
                self._mark_applied(node, "STATEMENT_DELETION", orig_node=node, mutated_node=new_node)
                return new_node

        return self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        # Constant / literal mutations (CONST_VAL)
        if self._in_compare or self._in_docstring:
            return self.generic_visit(node)
        if not self._line_allowed(node):
            return self.generic_visit(node)

        val = node.value
        # Booleans
        if isinstance(val, bool):
            if self._inc_id("CONST_VAL"):
                new_node = ast.Constant(value=not val)
                ast.copy_location(new_node, node)
                self._mark_applied(node, "CONST_VAL", orig_node=node, mutated_node=new_node)
                return new_node
        # Integers (excluding booleans)
        elif isinstance(val, int):
            if self._inc_id("CONST_VAL"):
                new_val = 1 if val == 0 else (0 if val == 1 else -val)
                new_node = ast.Constant(value=new_val)
                ast.copy_location(new_node, node)
                self._mark_applied(node, "CONST_VAL", orig_node=node, mutated_node=new_node)
                return new_node
        # Strings (non-empty)
        elif isinstance(val, str) and len(val) > 0:
            if self._inc_id("CONST_VAL"):
                new_node = ast.Constant(value="")
                ast.copy_location(new_node, node)
                self._mark_applied(node, "CONST_VAL", orig_node=node, mutated_node=new_node)
                return new_node

        return self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> ast.AST:
        # Exception handler mutations (EXCEPT_HANDLER)
        if not self._line_allowed(node):
            return self.generic_visit(node)

        exc_swap = {
            "ValueError": "TypeError",
            "TypeError": "ValueError",
            "KeyError": "IndexError",
            "IndexError": "KeyError",
            "ZeroDivisionError": "ValueError",
        }
        if isinstance(node.type, ast.Name) and node.type.id in exc_swap:
            if self._inc_id("EXCEPT_HANDLER"):
                new_type = ast.Name(id=exc_swap[node.type.id], ctx=ast.Load())
                ast.copy_location(new_type, node.type)
                new_node = ast.ExceptHandler(type=new_type, name=node.name, body=node.body)
                ast.copy_location(new_node, node)
                self._mark_applied(node, "EXCEPT_HANDLER", orig_node=node, mutated_node=new_node)
                return new_node

        return self.generic_visit(node)

    def visit_Raise(self, node: ast.Raise) -> ast.AST:
        # 12. Exception Raising Mutations (EXCEPTION_SWAP - Held-out evaluation operator)
        if not self.include_held_out:
            return self.generic_visit(node)
        if not self._line_allowed(node):
            return self.generic_visit(node)

        exc_swap = {
            "ValueError": "TypeError",
            "TypeError": "ValueError",
            "KeyError": "IndexError",
            "IndexError": "KeyError",
            "RuntimeError": "ValueError",
            "LookupError": "KeyError",
        }

        if node.exc is not None:
            # e.g. raise ValueError("msg")
            if isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Name):
                func_name = node.exc.func.id
                if func_name in exc_swap:
                    if self._inc_id("EXCEPTION_SWAP"):
                        new_func = ast.Name(id=exc_swap[func_name], ctx=ast.Load())
                        ast.copy_location(new_func, node.exc.func)
                        new_call = ast.Call(func=new_func, args=node.exc.args, keywords=node.exc.keywords)
                        ast.copy_location(new_call, node.exc)
                        new_node = ast.Raise(exc=new_call, cause=node.cause)
                        ast.copy_location(new_node, node)
                        self._mark_applied(node, "EXCEPTION_SWAP", orig_node=node, mutated_node=new_node)
                        return new_node
            # e.g. raise ValueError
            elif isinstance(node.exc, ast.Name):
                func_name = node.exc.id
                if func_name in exc_swap:
                    if self._inc_id("EXCEPTION_SWAP"):
                        new_exc = ast.Name(id=exc_swap[func_name], ctx=ast.Load())
                        ast.copy_location(new_exc, node.exc)
                        new_node = ast.Raise(exc=new_exc, cause=node.cause)
                        ast.copy_location(new_node, node)
                        self._mark_applied(node, "EXCEPTION_SWAP", orig_node=node, mutated_node=new_node)
                        return new_node

        return self.generic_visit(node)


def _stratify_mutants(mutants: List[MutantRecord], max_limit: int = 150) -> List[MutantRecord]:
    """
    Samples up to max_limit mutants evenly stratified across all present mutation categories.
    Preserves original relative line ordering.
    """
    if len(mutants) <= max_limit:
        return mutants
    from collections import defaultdict
    by_category: Dict[str, List[MutantRecord]] = defaultdict(list)
    for m in mutants:
        by_category[m.mutation_type].append(m)

    selected: List[MutantRecord] = []
    categories = sorted(by_category.keys())
    cat_indices = {cat: 0 for cat in categories}

    while len(selected) < max_limit and any(cat_indices[c] < len(by_category[c]) for c in categories):
        for c in categories:
            idx = cat_indices[c]
            if idx < len(by_category[c]):
                selected.append(by_category[c][idx])
                cat_indices[c] += 1
                if len(selected) >= max_limit:
                    break

    # Retain natural code line order
    selected.sort(key=lambda m: (m.line_number, m.mutant_id))
    return selected


class ASTMutator:
    """
    High-level orchestrator for discovering mutation sites and generating
    deterministic, syntax-validated AST mutants with provenance and equivalence analysis.
    """
    _MUTANT_CACHE: Dict[Any, List[MutantRecord]] = {}

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the in-memory AST mutant cache."""
        cls._MUTANT_CACHE.clear()

    @classmethod
    def inspect_mutation_sites(
        cls,
        source_code: str,
        target_lines: Optional[List[int]] = None,
        include_held_out: bool = False,
        allowed_line_ranges: Optional[List[Tuple[int, int]]] = None,
    ) -> Dict[int, str]:
        """
        Inspects all mutation points and returns mapping of target_id -> mutation_type.
        """
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return {}
        from testforge.security import mark_dynamic_nodes_immutable
        mark_dynamic_nodes_immutable(tree)
        inspector = MutationTransformer(
            target_node_id=0,
            target_lines=target_lines,
            include_held_out=include_held_out,
            allowed_line_ranges=allowed_line_ranges,
        )
        inspector.visit(tree)
        return inspector.sites

    @staticmethod
    def inspect_mutation_points(
        source_code: str,
        target_lines: Optional[List[int]] = None,
        include_held_out: bool = False,
        allowed_line_ranges: Optional[List[Tuple[int, int]]] = None,
    ) -> int:
        """
        Walks AST using MutationTransformer in inspection mode (target_node_id=0)
        to count the exact number of mutation sites deterministically.
        If target_lines is provided, only counts sites on those lines.
        """
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return 0
        from testforge.security import mark_dynamic_nodes_immutable
        mark_dynamic_nodes_immutable(tree)
        inspector = MutationTransformer(
            target_node_id=0,
            target_lines=target_lines,
            include_held_out=include_held_out,
            allowed_line_ranges=allowed_line_ranges,
        )
        inspector.visit(tree)
        return inspector.current_node_id

    @classmethod
    def mutate(
        cls,
        source_code: str,
        target_lines: Optional[List[int]] = None,
        include_held_out: bool = False,
        max_mutants: Optional[int] = None,
        allowed_line_ranges: Optional[List[Tuple[int, int]]] = None,
    ) -> List[MutantRecord]:
        """
        Generates deterministic AST mutants. If target_lines is provided and non-empty,
        only mutates AST nodes residing on those lines.
        If allowed_line_ranges is provided, only mutates nodes inside those line spans.
        If file exceeds 1,000 lines or max_mutants is specified, stratifies mutants up to max_mutants (default 150).
        Never modifies original source files in place.
        Validates output syntax with ast.parse and attaches provenance.
        """
        try:
            ast.parse(source_code)
        except SyntaxError:
            return []

        is_large = len(source_code.splitlines()) > 1000
        effective_max = max_mutants if max_mutants is not None else (150 if is_large else None)

        # Check in-memory AST cache for idempotent acceleration
        cache_key = (
            hash(source_code),
            tuple(sorted(target_lines)) if target_lines else None,
            include_held_out,
            effective_max,
            tuple(sorted(allowed_line_ranges)) if allowed_line_ranges else None,
        )
        if cache_key in cls._MUTANT_CACHE:
            return [m.model_copy() for m in cls._MUTANT_CACHE[cache_key]]

        sites = cls.inspect_mutation_sites(
            source_code,
            target_lines=target_lines,
            include_held_out=include_held_out,
            allowed_line_ranges=allowed_line_ranges,
        )
        num_targets = len(sites)
        if num_targets == 0:
            return []

        if effective_max is not None and num_targets > effective_max:
            from collections import defaultdict
            by_cat: Dict[str, List[int]] = defaultdict(list)
            for tid, cat in sites.items():
                by_cat[cat].append(tid)

            selected_ids: List[int] = []
            cats = sorted(by_cat.keys())
            cat_idx = {c: 0 for c in cats}
            while len(selected_ids) < effective_max and any(cat_idx[c] < len(by_cat[c]) for c in cats):
                for c in cats:
                    idx = cat_idx[c]
                    if idx < len(by_cat[c]):
                        selected_ids.append(by_cat[c][idx])
                        cat_idx[c] += 1
                        if len(selected_ids) >= effective_max:
                            break
            target_ids = sorted(selected_ids)
        else:
            target_ids = list(range(1, num_targets + 1))

        mutants: List[MutantRecord] = []
        from testforge.security import mark_dynamic_nodes_immutable
        original_lines = source_code.splitlines(keepends=True)
        source_for_mutation = source_code

        for target_id in target_ids:
            tree = ast.parse(source_for_mutation)
            mark_dynamic_nodes_immutable(tree)
            transformer = MutationTransformer(
                target_node_id=target_id,
                target_lines=target_lines,
                include_held_out=include_held_out,
                allowed_line_ranges=allowed_line_ranges,
            )
            mutated_tree = transformer.visit(tree)
            ast.fix_missing_locations(mutated_tree)

            if transformer.applied:
                try:
                    mutated_code = ast.unparse(mutated_tree)
                    # Validate that mutated output is parseable valid Python
                    ast.parse(mutated_code)
                    is_valid_syntax = True
                    initial_status = "PENDING"
                except Exception:
                    mutated_code = source_for_mutation
                    is_valid_syntax = False
                    initial_status = "INVALID"

                resolved_line = transformer.line_number if transformer.line_number > 0 else 1
                if is_large:
                    diff = (
                        f"--- target.py (original)\n"
                        f"+++ target.py (mutant_{target_id})\n"
                        f"@@ -{resolved_line},1 +{resolved_line},1 @@\n"
                        f"-{transformer.original_expr or ''}\n"
                        f"+{transformer.mutated_expr or ''}"
                    )
                else:
                    mutated_lines = mutated_code.splitlines(keepends=True)
                    diff_lines = list(difflib.unified_diff(
                        original_lines,
                        mutated_lines,
                        fromfile="target.py (original)",
                        tofile=f"target.py (mutant_{target_id})",
                        lineterm=""
                    ))
                    diff = "\n".join(diff_lines)
                    for line in diff_lines:
                        if line.startswith("@@"):
                            parts = line.split("+")
                            if len(parts) > 1:
                                try:
                                    line_no = int(parts[1].split(",")[0].split(" ")[0])
                                    if transformer.line_number <= 0:
                                        resolved_line = line_no
                                except ValueError:
                                    pass
                            break

                record = MutantRecord(
                    mutant_id=f"MUT_{transformer.mutant_type}_{target_id:03d}",
                    mutation_type=transformer.mutant_type,
                    line_number=resolved_line,
                    original_code_snippet=source_for_mutation,
                    mutated_code_snippet=mutated_code,
                    unified_diff=diff,
                    status=initial_status,
                    is_valid_syntax=is_valid_syntax,
                    original_expression=transformer.original_expr,
                    mutated_expression=transformer.mutated_expr,
                    is_executed=False,
                )

                # Early static equivalence check (e.g. dead code, algebraic identity)
                eq_result = EquivalentMutantAnalyzer.analyze_mutant(record, original_source=source_for_mutation)
                if eq_result.status == EquivalenceClassification.EQUIVALENT:
                    record.equivalence_status = eq_result.status.value
                    record.equivalence_method = eq_result.method.value
                    record.equivalence_reason = eq_result.reason
                    record.equivalence_confidence = eq_result.confidence.value
                elif eq_result.status == EquivalenceClassification.POTENTIALLY_EQUIVALENT:
                    record.equivalence_status = eq_result.status.value
                    record.equivalence_method = eq_result.method.value
                    record.equivalence_reason = eq_result.reason
                    record.equivalence_confidence = eq_result.confidence.value

                mutants.append(record)

        cls._MUTANT_CACHE[cache_key] = [m.model_copy() for m in mutants]
        return mutants

    @classmethod
    def generate_mutants(
        cls,
        source_code: str,
        target_lines: Optional[List[int]] = None,
        max_mutants: Optional[int] = None,
        allowed_line_ranges: Optional[List[Tuple[int, int]]] = None,
    ) -> List[MutantRecord]:
        """
        Alias for mutate() to preserve backward compatibility.
        """
        return cls.mutate(
            source_code,
            target_lines=target_lines,
            max_mutants=max_mutants,
            allowed_line_ranges=allowed_line_ranges,
        )

    @classmethod
    def generate_held_out_mutants(
        cls,
        source_code: str,
        target_lines: Optional[List[int]] = None,
        allowed_line_ranges: Optional[List[Tuple[int, int]]] = None,
    ) -> List[MutantRecord]:
        """
        Generates exclusively the held-out mutation operators (BITWISE_OP, EXCEPTION_SWAP)
        for empirical generalization evaluation (Stage 1.5).
        """
        all_with_held = cls.mutate(
            source_code,
            target_lines=target_lines,
            include_held_out=True,
            allowed_line_ranges=allowed_line_ranges,
        )
        return [m for m in all_with_held if m.mutation_type in ("BITWISE_OP", "EXCEPTION_SWAP")]
