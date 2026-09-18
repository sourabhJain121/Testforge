"""
mutator.py - Deterministic AST-based Mutation Testing Engine.

Author: Shreshth (Module 2)
Course: CSE3101 - Agentic AI

Implements 4 deterministic AST mutations:
  1. Comparison operator inversion (e.g. > to <=, == to !=)
  2. Arithmetic operator swapping (e.g. + to -, * to //)
  3. Conditional inversion (e.g. if x -> if not x)
  4. Return value mutation (e.g. return True -> return False, return x -> return None)
"""

from __future__ import annotations
import ast
import difflib
from typing import List, Dict, Type
from testforge.state import MutantRecord


class MutationTransformer(ast.NodeTransformer):
    """
    AST transformer that mutates exactly one targeted mutation site per pass.
    """
    def __init__(self, target_node_id: int):
        self.target_node_id = target_node_id
        self.current_node_id = 0
        self.applied = False
        self.mutant_type: str = ""

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
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
        new_ops = []
        modified = False
        for op in node.ops:
            op_cls = op.__class__
            if op_cls in comp_map:
                self.current_node_id += 1
                if self.current_node_id == self.target_node_id and not self.applied:
                    new_ops.append(comp_map[op_cls]())
                    self.applied = True
                    self.mutant_type = "COMP_OP"
                    modified = True
                    continue
            new_ops.append(op)
        if modified:
            new_node = ast.Compare(left=node.left, ops=new_ops, comparators=node.comparators)
            return ast.copy_location(new_node, node)
        return self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
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
                self.applied = True
                self.mutant_type = "ARITH_OP"
                new_node = ast.BinOp(left=node.left, op=arith_map[op_cls](), right=node.right)
                return ast.copy_location(new_node, node)
        return self.generic_visit(node)

    def visit_If(self, node: ast.If) -> ast.AST:
        self.current_node_id += 1
        if self.current_node_id == self.target_node_id and not self.applied:
            self.applied = True
            self.mutant_type = "COND_INV"
            new_test = ast.UnaryOp(op=ast.Not(), operand=node.test)
            new_node = ast.If(test=new_test, body=node.body, orelse=node.orelse)
            return ast.copy_location(new_node, node)
        return self.generic_visit(node)

    def visit_Return(self, node: ast.Return) -> ast.AST:
        self.current_node_id += 1
        if self.current_node_id == self.target_node_id and not self.applied:
            self.applied = True
            self.mutant_type = "RETURN_VAL"
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
            return ast.copy_location(new_node, node)
        return self.generic_visit(node)


class ASTMutator:
    """
    High-level orchestrator for discovering mutation sites and generating mutants.
    """

    @staticmethod
    def inspect_mutation_points(source_code: str) -> int:
        tree = ast.parse(source_code)
        counter = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                for op in node.ops:
                    if op.__class__ in (ast.Gt, ast.Lt, ast.GtE, ast.LtE, ast.Eq, ast.NotEq, ast.In, ast.NotIn, ast.Is, ast.IsNot):
                        counter += 1
            elif isinstance(node, ast.BinOp):
                if node.op.__class__ in (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow):
                    counter += 1
            elif isinstance(node, ast.If):
                counter += 1
            elif isinstance(node, ast.Return):
                counter += 1
        return counter

    @classmethod
    def generate_mutants(cls, source_code: str) -> List[MutantRecord]:
        num_targets = cls.inspect_mutation_points(source_code)
        mutants: List[MutantRecord] = []
        original_lines = source_code.splitlines(keepends=True)

        for target_id in range(1, num_targets + 1):
            tree = ast.parse(source_code)
            transformer = MutationTransformer(target_node_id=target_id)
            mutated_tree = transformer.visit(tree)
            ast.fix_missing_locations(mutated_tree)

            if transformer.applied:
                mutated_code = ast.unparse(mutated_tree)
                mutated_lines = mutated_code.splitlines(keepends=True)

                diff_lines = list(difflib.unified_diff(
                    original_lines,
                    mutated_lines,
                    fromfile="target.py (original)",
                    tofile=f"target.py (mutant_{target_id})",
                    lineterm=""
                ))
                diff = "\n".join(diff_lines)

                # Extract line number from unified diff chunk header (e.g. @@ -10,3 +10,3 @@)
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

                mutants.append(MutantRecord(
                    mutant_id=f"MUT_{transformer.mutant_type}_{target_id:03d}",
                    mutation_type=transformer.mutant_type,  # type: ignore
                    line_number=line_no,
                    original_code_snippet=source_code,
                    mutated_code_snippet=mutated_code,
                    unified_diff=diff
                ))

        return mutants
