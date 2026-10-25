"""
mutator.py - Deterministic AST-based Mutation Testing Engine.

Author: Shreshth (Module 2) & Sourabh
Course: CSE3101 - Agentic AI
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
"""

from __future__ import annotations
import ast
import difflib
from typing import List, Dict, Type, Optional, Set
from testforge.state import MutantRecord
from testforge.equivalence import (
    EquivalentMutantAnalyzer,
    EquivalenceClassification
)


class MutationTransformer(ast.NodeTransformer):
    """
    AST transformer that mutates exactly one targeted mutation site per pass.
    When target_node_id == 0, acts as an accurate mutation site inspector.
    Supports restricting mutations to specific line numbers via target_lines.
    Tracks exact original and mutated expressions for full provenance.
    """
    def __init__(self, target_node_id: int, target_lines: Optional[List[int]] = None):
        self.target_node_id = target_node_id
        self.target_lines: Optional[Set[int]] = set(target_lines) if target_lines else None
        self.current_node_id = 0
        self.applied = False
        self.mutant_type: str = ""
        self.line_number: int = 1
        self.original_expr: Optional[str] = None
        self.mutated_expr: Optional[str] = None
        self._in_compare = False
        self._in_docstring = False

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
        if self.target_lines is not None and getattr(node, "lineno", None) not in self.target_lines:
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
                self.current_node_id += 1
                if self.current_node_id == self.target_node_id and not self.applied:
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
                self.current_node_id += 1
                if self.current_node_id == self.target_node_id and not self.applied:
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
            self.current_node_id += 1
            if self.current_node_id == self.target_node_id and not self.applied:
                new_left = ast.Constant(value=val + delta)
                new_node = ast.Compare(left=new_left, ops=node.ops, comparators=node.comparators)
                ast.copy_location(new_node, node)
                self._mark_applied(node, "OFF_BY_ONE", orig_node=node, mutated_node=new_node)
                return new_node
            # Site n - 1
            self.current_node_id += 1
            if self.current_node_id == self.target_node_id and not self.applied:
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
                self.current_node_id += 1
                if self.current_node_id == self.target_node_id and not self.applied:
                    new_comps = list(node.comparators)
                    new_comps[j] = ast.Constant(value=val + delta)
                    new_node = ast.Compare(left=node.left, ops=node.ops, comparators=new_comps)
                    ast.copy_location(new_node, node)
                    self._mark_applied(node, "OFF_BY_ONE", orig_node=node, mutated_node=new_node)
                    return new_node
                # Site n - 1
                self.current_node_id += 1
                if self.current_node_id == self.target_node_id and not self.applied:
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
        if self.target_lines is not None and getattr(node, "lineno", None) not in self.target_lines:
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
            self.current_node_id += 1
            if self.current_node_id == self.target_node_id and not self.applied:
                new_node = ast.BinOp(left=node.left, op=arith_map[op_cls](), right=node.right)
                ast.copy_location(new_node, node)
                self._mark_applied(node, "ARITH_OP", orig_node=node, mutated_node=new_node)
                return new_node
        return self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> ast.AST:
        if self.target_lines is not None and getattr(node, "lineno", None) not in self.target_lines:
            return self.generic_visit(node)
        # Logical Connective Swaps (LOGICAL_CONN: and <-> or)
        if isinstance(node.op, ast.And):
            self.current_node_id += 1
            if self.current_node_id == self.target_node_id and not self.applied:
                new_node = ast.BoolOp(op=ast.Or(), values=node.values)
                ast.copy_location(new_node, node)
                self._mark_applied(node, "LOGICAL_CONN", orig_node=node, mutated_node=new_node)
                return new_node
        elif isinstance(node.op, ast.Or):
            self.current_node_id += 1
            if self.current_node_id == self.target_node_id and not self.applied:
                new_node = ast.BoolOp(op=ast.And(), values=node.values)
                ast.copy_location(new_node, node)
                self._mark_applied(node, "LOGICAL_CONN", orig_node=node, mutated_node=new_node)
                return new_node
        return self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> ast.AST:
        if self.target_lines is not None and getattr(node, "lineno", None) not in self.target_lines:
            return self.generic_visit(node)
        # Math Function & Precision Flips (MATH_FUNC)
        if isinstance(node.func, ast.Name):
            # round(x, 2) -> round(x, 1)
            if node.func.id == "round" and len(node.args) >= 2:
                prec_arg = node.args[1]
                if isinstance(prec_arg, ast.Constant) and isinstance(prec_arg.value, int) and prec_arg.value > 0:
                    self.current_node_id += 1
                    if self.current_node_id == self.target_node_id and not self.applied:
                        new_args = list(node.args)
                        new_args[1] = ast.Constant(value=prec_arg.value - 1)
                        new_node = ast.Call(func=node.func, args=new_args, keywords=node.keywords)
                        ast.copy_location(new_node, node)
                        self._mark_applied(node, "MATH_FUNC", orig_node=node, mutated_node=new_node)
                        return new_node
            # abs(x) -> x
            elif node.func.id == "abs" and len(node.args) == 1:
                self.current_node_id += 1
                if self.current_node_id == self.target_node_id and not self.applied:
                    new_node = node.args[0]
                    ast.copy_location(new_node, node)
                    self._mark_applied(node, "MATH_FUNC", orig_node=node, mutated_node=new_node)
                    return new_node
        return self.generic_visit(node)

    def visit_If(self, node: ast.If) -> ast.AST:
        if self.target_lines is not None and getattr(node, "lineno", None) not in self.target_lines:
            return self.generic_visit(node)
        self.current_node_id += 1
        if self.current_node_id == self.target_node_id and not self.applied:
            new_test = ast.UnaryOp(op=ast.Not(), operand=node.test)
            new_node = ast.If(test=new_test, body=node.body, orelse=node.orelse)
            ast.copy_location(new_node, node)
            self._mark_applied(node, "COND_INV", orig_node=node, mutated_node=new_node)
            return new_node
        return self.generic_visit(node)

    def visit_Return(self, node: ast.Return) -> ast.AST:
        if self.target_lines is not None and getattr(node, "lineno", None) not in self.target_lines:
            return self.generic_visit(node)
        self.current_node_id += 1
        if self.current_node_id == self.target_node_id and not self.applied:
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

    def visit_Expr(self, node: ast.Expr) -> ast.AST:
        # Detect and preserve module/function docstrings
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            self._in_docstring = True
            try:
                return self.generic_visit(node)
            finally:
                self._in_docstring = False
        return self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        # Constant / literal mutations (CONST_VAL)
        if self._in_compare or self._in_docstring:
            return self.generic_visit(node)
        if self.target_lines is not None and getattr(node, "lineno", None) not in self.target_lines:
            return self.generic_visit(node)

        val = node.value
        # Booleans
        if isinstance(val, bool):
            self.current_node_id += 1
            if self.current_node_id == self.target_node_id and not self.applied:
                new_node = ast.Constant(value=not val)
                ast.copy_location(new_node, node)
                self._mark_applied(node, "CONST_VAL", orig_node=node, mutated_node=new_node)
                return new_node
        # Integers (excluding booleans)
        elif isinstance(val, int):
            self.current_node_id += 1
            if self.current_node_id == self.target_node_id and not self.applied:
                new_val = 1 if val == 0 else (0 if val == 1 else -val)
                new_node = ast.Constant(value=new_val)
                ast.copy_location(new_node, node)
                self._mark_applied(node, "CONST_VAL", orig_node=node, mutated_node=new_node)
                return new_node
        # Strings (non-empty)
        elif isinstance(val, str) and len(val) > 0:
            self.current_node_id += 1
            if self.current_node_id == self.target_node_id and not self.applied:
                new_node = ast.Constant(value="")
                ast.copy_location(new_node, node)
                self._mark_applied(node, "CONST_VAL", orig_node=node, mutated_node=new_node)
                return new_node

        return self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> ast.AST:
        # Exception handler mutations (EXCEPT_HANDLER)
        if self.target_lines is not None and getattr(node, "lineno", None) not in self.target_lines:
            return self.generic_visit(node)

        exc_swap = {
            "ValueError": "TypeError",
            "TypeError": "ValueError",
            "KeyError": "IndexError",
            "IndexError": "KeyError",
            "ZeroDivisionError": "ValueError",
        }
        if isinstance(node.type, ast.Name) and node.type.id in exc_swap:
            self.current_node_id += 1
            if self.current_node_id == self.target_node_id and not self.applied:
                new_type = ast.Name(id=exc_swap[node.type.id], ctx=ast.Load())
                ast.copy_location(new_type, node.type)
                new_node = ast.ExceptHandler(type=new_type, name=node.name, body=node.body)
                ast.copy_location(new_node, node)
                self._mark_applied(node, "EXCEPT_HANDLER", orig_node=node, mutated_node=new_node)
                return new_node

        return self.generic_visit(node)


class ASTMutator:
    """
    High-level orchestrator for discovering mutation sites and generating
    deterministic, syntax-validated AST mutants with provenance and equivalence analysis.
    """

    @staticmethod
    def inspect_mutation_points(source_code: str, target_lines: Optional[List[int]] = None) -> int:
        """
        Walks AST using MutationTransformer in inspection mode (target_node_id=0)
        to count the exact number of mutation sites deterministically.
        If target_lines is provided, only counts sites on those lines.
        """
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return 0
        inspector = MutationTransformer(target_node_id=0, target_lines=target_lines)
        inspector.visit(tree)
        return inspector.current_node_id

    @classmethod
    def mutate(cls, source_code: str, target_lines: Optional[List[int]] = None) -> List[MutantRecord]:
        """
        Generates deterministic AST mutants. If target_lines is provided and non-empty,
        only mutates AST nodes residing on those lines.
        Never modifies original source files in place.
        Validates output syntax with ast.parse and attaches provenance.
        """
        try:
            ast.parse(source_code)
        except SyntaxError:
            return []

        num_targets = cls.inspect_mutation_points(source_code, target_lines=target_lines)
        mutants: List[MutantRecord] = []
        original_lines = source_code.splitlines(keepends=True)

        for target_id in range(1, num_targets + 1):
            tree = ast.parse(source_code)
            transformer = MutationTransformer(target_node_id=target_id, target_lines=target_lines)
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
                    mutated_code = source_code
                    is_valid_syntax = False
                    initial_status = "INVALID"

                mutated_lines = mutated_code.splitlines(keepends=True)
                diff_lines = list(difflib.unified_diff(
                    original_lines,
                    mutated_lines,
                    fromfile="target.py (original)",
                    tofile=f"target.py (mutant_{target_id})",
                    lineterm=""
                ))
                diff = "\n".join(diff_lines)

                line_no = 1
                for line in diff_lines:
                    if line.startswith("@@"):
                        parts = line.split("+")
                        if len(parts) > 1:
                            try:
                                line_no = int(parts[1].split(",")[0].split(" ")[0])
                            except ValueError:
                                line_no = 1
                        break

                resolved_line = transformer.line_number if transformer.line_number > 0 else line_no

                record = MutantRecord(
                    mutant_id=f"MUT_{transformer.mutant_type}_{target_id:03d}",
                    mutation_type=transformer.mutant_type,
                    line_number=resolved_line,
                    original_code_snippet=source_code,
                    mutated_code_snippet=mutated_code,
                    unified_diff=diff,
                    status=initial_status,
                    is_valid_syntax=is_valid_syntax,
                    original_expression=transformer.original_expr,
                    mutated_expression=transformer.mutated_expr,
                    is_executed=False,
                )

                # Early static equivalence check (e.g. dead code, algebraic identity)
                eq_result = EquivalentMutantAnalyzer.analyze_mutant(record, original_source=source_code)
                if eq_result.status == EquivalenceClassification.EQUIVALENT:
                    record.status = "EQUIVALENT"
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

        return mutants

    @classmethod
    def generate_mutants(cls, source_code: str, target_lines: Optional[List[int]] = None) -> List[MutantRecord]:
        """
        Alias for mutate() to preserve backward compatibility.
        """
        return cls.mutate(source_code, target_lines=target_lines)
