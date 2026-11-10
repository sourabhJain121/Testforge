"""
blast_analyzer.py - Static Blast Radius & Dependency Impact Analysis Engine.

Author: Sourabh & Shreshth
System: Autonomous Multi-Agent Hardening Engine

Features:
  - ASTCallGraphVisitor: Parses Python AST to construct an adjacency graph
    of callers and callees (including nested functions, method invocations,
    and module-level calls).
  - BlastRadiusAnalyzer:
      * Upstream Callers: Recursively traverses caller chains targeting a function.
      * Downstream Callees: Recursively extracts all sub-routines invoked.
      * Impact Ratio & Risk Categorization: LOW (<20%), MEDIUM (20%-50%), HIGH (>50%).
      * Tree Representation: Formats an indented/ASCII dependency call tree for UI/CLI.
"""

from __future__ import annotations

import ast
from typing import Any, Dict, Optional, Set


class ASTCallGraphVisitor(ast.NodeVisitor):
    """
    AST visitor that traverses function definitions, methods, and call sites
    to construct an adjacency map of caller -> set of callees.
    """
    def __init__(self):
        self.call_graph: Dict[str, Set[str]] = {}
        self.all_functions: Set[str] = set()
        self.current_function: Optional[str] = None

    def visit_FunctionDef(self, node: ast.FunctionDef):
        prev = self.current_function
        self.current_function = node.name
        self.all_functions.add(node.name)
        if node.name not in self.call_graph:
            self.call_graph[node.name] = set()
        self.generic_visit(node)
        self.current_function = prev

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        prev = self.current_function
        self.current_function = node.name
        self.all_functions.add(node.name)
        if node.name not in self.call_graph:
            self.call_graph[node.name] = set()
        self.generic_visit(node)
        self.current_function = prev

    def visit_Call(self, node: ast.Call):
        callee_name = None
        if isinstance(node.func, ast.Name):
            callee_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            callee_name = node.func.attr

        caller = self.current_function or "<module>"
        if caller not in self.call_graph:
            self.call_graph[caller] = set()
        if callee_name:
            self.call_graph[caller].add(callee_name)
        self.generic_visit(node)


class BlastRadiusAnalyzer:
    """
    Computes blast radius, upstream caller propagation, downstream dependencies,
    and risk profiles for Python source modules.
    """

    @classmethod
    def build_call_graph(cls, source_code: str) -> Dict[str, Set[str]]:
        """
        Parses source code into an AST and builds a full caller -> callees adjacency dictionary.
        """
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return {}

        visitor = ASTCallGraphVisitor()
        visitor.visit(tree)
        return visitor.call_graph

    @classmethod
    def analyze_impact(cls, target_function: str, source_code: str) -> Dict[str, Any]:
        """
        Analyzes the blast radius of modifying `target_function`.
        Returns impacted upstream/downstream functions, impact ratio, risk category,
        and an ASCII tree representation.
        """
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            return {
                "target_function": target_function,
                "error": f"SyntaxError in source code: {e}",
                "upstream_callers": [],
                "downstream_callees": [],
                "affected_functions": [],
                "total_functions": 0,
                "impacted_ratio": 0.0,
                "risk_category": "LOW",
                "call_graph": {},
                "tree_representation": "Error parsing source code."
            }

        visitor = ASTCallGraphVisitor()
        visitor.visit(tree)
        call_graph = visitor.call_graph
        all_funcs = visitor.all_functions

        # Default to first function if not specified
        if not target_function and all_funcs:
            target_function = sorted(list(all_funcs))[0]

        # 1. Downstream Callees: sub-routines invoked by target_function (recursive)
        direct_callees = set(call_graph.get(target_function, set()))
        downstream: Set[str] = set()
        queue = list(direct_callees)
        visited: Set[str] = set()
        while queue:
            curr = queue.pop(0)
            if curr in visited:
                continue
            visited.add(curr)
            if curr != target_function:
                downstream.add(curr)
            for nxt in call_graph.get(curr, set()):
                if nxt not in visited:
                    queue.append(nxt)

        # 2. Upstream Callers: recursively identifies all parent functions calling target_function
        reverse_graph: Dict[str, Set[str]] = {}
        for caller, callees in call_graph.items():
            for callee in callees:
                if callee not in reverse_graph:
                    reverse_graph[callee] = set()
                reverse_graph[callee].add(caller)

        upstream: Set[str] = set()
        queue = list(reverse_graph.get(target_function, set()))
        visited = set()
        while queue:
            curr = queue.pop(0)
            if curr in visited:
                continue
            visited.add(curr)
            if curr != "<module>" and curr != target_function:
                upstream.add(curr)
            for parent in reverse_graph.get(curr, set()):
                if parent not in visited:
                    queue.append(parent)

        # Total functions defined in module
        total_functions = max(1, len(all_funcs))

        # Affected functions: target + upstream callers + downstream callees (restricted to defined functions for ratio)
        affected_all = {target_function} | upstream | downstream
        affected_defined = [f for f in affected_all if f in all_funcs]
        if not affected_defined:
            affected_defined = [target_function]

        impacted_ratio = len(affected_defined) / total_functions

        # Risk Category
        if impacted_ratio < 0.20:
            risk_category = "LOW"
        elif impacted_ratio <= 0.50:
            risk_category = "MEDIUM"
        else:
            risk_category = "HIGH"

        # Tree Representation: ASCII / indented call tree string
        lines = [f"📌 {target_function or '(None)'} [Target Function]"]
        if downstream:
            lines.append("  ├── [Downstream Sub-routines]")
            for idx, c in enumerate(sorted(downstream)):
                is_last = (idx == len(downstream) - 1)
                prefix = "  │    └── " if is_last else "  │    ├── "
                sub_callees = call_graph.get(c, set())
                sub_info = f" (invokes: {', '.join(sorted(sub_callees))})" if sub_callees else ""
                lines.append(f"{prefix}{c}{sub_info}")
        else:
            lines.append("  ├── [Downstream Sub-routines]: None (Leaf Function)")

        if upstream:
            lines.append("  └── [Upstream Callers]")
            for idx, u in enumerate(sorted(upstream)):
                is_last = (idx == len(upstream) - 1)
                prefix = "       └── " if is_last else "       ├── "
                lines.append(f"{prefix}{u}")
        else:
            lines.append("  └── [Upstream Callers]: None (Root / Entry Point)")

        tree_str = "\n".join(lines)

        return {
            "target_function": target_function,
            "upstream_callers": sorted(list(upstream)),
            "downstream_callees": sorted(list(downstream)),
            "direct_callees": sorted(list(direct_callees)),
            "affected_functions": sorted(list(affected_all)),
            "total_functions": total_functions,
            "all_functions": sorted(list(all_funcs)),
            "impacted_ratio": round(impacted_ratio, 3),
            "impacted_pct": round(impacted_ratio * 100.0, 1),
            "risk_category": risk_category,
            "call_graph": {k: sorted(list(v)) for k, v in call_graph.items()},
            "tree_representation": tree_str
        }
