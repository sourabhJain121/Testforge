"""
testforge/symbolic_solver.py - Neuro-Symbolic Boundary & Path Constraint Solver.

Deterministically extracts exact boundary conditions from surviving AST mutants
(relational boundaries, off-by-one offsets, string predicates, sequence length limits,
and boolean/guard inversions) and synthesizes verified Pass@1 pytest assertions in milliseconds
without waiting on slow LLM reflection calls.
"""

from __future__ import annotations

import ast
import copy
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

logger = logging.getLogger("testforge.symbolic_solver")

BLOCKLIST_CALLABLES: Set[str] = {
    "run", "serve", "start", "main", "_cli_parse", "_cli_patch",
    "listen", "listen_and_serve", "app", "application"
}


@dataclass
class BoundaryConstraint:
    """Represents a symbolic boundary constraint extracted from a surviving AST mutant site."""
    function_name: str
    class_name: Optional[str] = None
    line_number: int = 1
    constraint_type: str = "NUMERIC_RELATIONAL"  # NUMERIC_RELATIONAL, STRING_SEQUENCE, GUARD_INVERSION, OFF_BY_ONE
    variable_name: Optional[str] = None
    operator: Optional[str] = None
    threshold_value: Any = None
    probe_values: List[Any] = field(default_factory=list)
    param_names: List[str] = field(default_factory=list)
    target_param: Optional[str] = None
    param_defaults: Dict[str, Any] = field(default_factory=dict)
    mutant_id: Optional[str] = None
    original_expr: Optional[str] = None
    mutated_expr: Optional[str] = None


class FunctionContextExtractor(ast.NodeVisitor):
    """
    Traverses the Python AST to map line numbers to enclosing function/method definitions,
    parameter signatures, type hints, and default values.
    """

    def __init__(self):
        self.current_class: Optional[str] = None
        # line_number -> (FunctionDef/AsyncFunctionDef, class_name)
        self.line_to_func: Dict[int, Tuple[Union[ast.FunctionDef, ast.AsyncFunctionDef], Optional[str]]] = {}
        self.functions: Dict[str, Tuple[Union[ast.FunctionDef, ast.AsyncFunctionDef], Optional[str]]] = {}

    def visit_ClassDef(self, node: ast.ClassDef):
        prev_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = prev_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._record_func(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._record_func(node)
        self.generic_visit(node)

    def _record_func(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]):
        start = getattr(node, "lineno", 1)
        end = getattr(node, "end_lineno", start + 50)
        for line in range(start, end + 1):
            self.line_to_func[line] = (node, self.current_class)
        self.functions[node.name] = (node, self.current_class)


class NeuroSymbolicBoundarySolver:
    """
    Pure deterministic AST and Constraint Solver that generates boundary-value analysis (BVA)
    test probes for surviving mutants and queries reference code oracle behavior.
    """

    def __init__(self):
        pass

    # --------------------------------------------------------------------------
    # 1. Constraint Extraction
    # --------------------------------------------------------------------------

    def extract_boundary_constraints(
        self,
        source_code: str,
        surviving_mutants: List[Union[Dict[str, Any], Any]]
    ) -> List[BoundaryConstraint]:
        """
        Parses source_code AST and maps surviving mutants to boundary constraints
        (relational thresholds, string checks, length limits, boolean guards).
        """
        constraints: List[BoundaryConstraint] = []
        if not source_code or not source_code.strip() or not surviving_mutants:
            return constraints

        try:
            tree = ast.parse(source_code)
        except Exception as e:
            logger.debug(f"Failed to parse source_code AST for symbolic constraints: {e}")
            return constraints

        extractor = FunctionContextExtractor()
        extractor.visit(tree)

        for mutant in surviving_mutants:
            m_dict = mutant if isinstance(mutant, dict) else mutant.__dict__
            lineno = m_dict.get("line_number") or m_dict.get("lineno") or 1
            m_type = m_dict.get("mutation_type") or m_dict.get("mutant_type") or ""
            orig_expr = m_dict.get("original_expr") or m_dict.get("original_expression") or m_dict.get("original_code_snippet") or ""
            mut_expr = m_dict.get("mutated_expr") or m_dict.get("mutated_expression") or m_dict.get("mutated_code_snippet") or ""
            mutant_id = m_dict.get("mutant_id") or ""

            func_info = extractor.line_to_func.get(lineno)
            if not func_info:
                continue

            func_node, class_name = func_info
            func_name = func_node.name

            # Skip dangerous or CLI functions
            if func_name.lower() in BLOCKLIST_CALLABLES:
                continue

            param_names, param_defaults = self._extract_parameters(func_node)
            if not param_names:
                continue

            # Attempt constraint extraction:
            # 1. Try parsing original_expr directly
            c = self._extract_from_expression(
                expr_str=orig_expr,
                func_name=func_name,
                class_name=class_name,
                lineno=lineno,
                param_names=param_names,
                param_defaults=param_defaults,
                mutant_id=mutant_id,
                orig_expr=orig_expr,
                mut_expr=mut_expr,
                m_type=m_type
            )
            if c:
                constraints.append(c)
                continue

            # 2. Try inspecting AST nodes specifically located on lineno
            c_ast = self._extract_from_ast_line(
                tree=tree,
                lineno=lineno,
                func_name=func_name,
                class_name=class_name,
                param_names=param_names,
                param_defaults=param_defaults,
                mutant_id=mutant_id,
                orig_expr=orig_expr,
                mut_expr=mut_expr,
                m_type=m_type
            )
            if c_ast:
                constraints.append(c_ast)

        return constraints

    def _extract_parameters(
        self,
        node: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> Tuple[List[str], Dict[str, Any]]:
        """Extracts parameter names and sensible type-inferred default values."""
        params: List[str] = []
        defaults: Dict[str, Any] = {}

        # Handle positional & keyword arguments (skipping 'self' and 'cls')
        all_args = [a for a in node.args.args if a.arg not in ("self", "cls")]

        # Match explicit AST default values
        default_offset = len(all_args) - len(node.args.defaults)
        for idx, arg in enumerate(all_args):
            name = arg.arg
            params.append(name)
            def_val = None
            if idx >= default_offset:
                d_node = node.args.defaults[idx - default_offset]
                try:
                    def_val = ast.literal_eval(d_node)
                except Exception:
                    def_val = None

            if def_val is None:
                def_val = self._infer_default_value(arg, name)
            defaults[name] = def_val

        return params, defaults

    def _infer_default_value(self, arg: ast.arg, param_name: str) -> Any:
        """Infers a safe default probe baseline for a parameter based on annotation or name."""
        ann = ""
        if arg.annotation:
            try:
                ann = ast.unparse(arg.annotation).lower()
            except Exception:
                pass

        if "float" in ann:
            return 10.0
        if "int" in ann:
            return 1
        if "str" in ann:
            return "test"
        if "bool" in ann:
            return True
        if "list" in ann:
            return [1, 2]
        if "dict" in ann:
            return {"key": "val"}

        # Heuristic by variable name
        p_low = param_name.lower()
        if any(k in p_low for k in ("price", "amount", "cost", "total", "balance", "weight", "rate", "pct")):
            return 10.0
        if any(k in p_low for k in ("qty", "quantity", "count", "num", "index", "idx", "limit", "max", "min")):
            return 1
        if any(k in p_low for k in ("name", "id", "str", "token", "key", "desc", "msg", "type")):
            return "test"
        if any(k in p_low for k in ("items", "list", "records", "values", "elements")):
            return [1, 2]
        if any(k in p_low for k in ("flag", "is_", "has_", "enable")):
            return True

        return 1

    def _extract_from_expression(
        self,
        expr_str: str,
        func_name: str,
        class_name: Optional[str],
        lineno: int,
        param_names: List[str],
        param_defaults: Dict[str, Any],
        mutant_id: str,
        orig_expr: str,
        mut_expr: str,
        m_type: str
    ) -> Optional[BoundaryConstraint]:
        """Tries parsing a snippet expression string to detect comparison or guard patterns."""
        if not expr_str or not expr_str.strip():
            return None

        try:
            expr_ast = ast.parse(expr_str.strip(), mode="eval")
        except Exception:
            return None

        body = getattr(expr_ast, "body", None)
        if isinstance(body, ast.Compare):
            return self._build_compare_constraint(
                comp=body,
                func_name=func_name,
                class_name=class_name,
                lineno=lineno,
                param_names=param_names,
                param_defaults=param_defaults,
                mutant_id=mutant_id,
                orig_expr=orig_expr,
                mut_expr=mut_expr,
                m_type=m_type
            )
        elif isinstance(body, ast.Call):
            return self._build_call_constraint(
                call=body,
                func_name=func_name,
                class_name=class_name,
                lineno=lineno,
                param_names=param_names,
                param_defaults=param_defaults,
                mutant_id=mutant_id,
                orig_expr=orig_expr,
                mut_expr=mut_expr,
                m_type=m_type
            )
        return None

    def _extract_from_ast_line(
        self,
        tree: ast.AST,
        lineno: int,
        func_name: str,
        class_name: Optional[str],
        param_names: List[str],
        param_defaults: Dict[str, Any],
        mutant_id: str,
        orig_expr: str,
        mut_expr: str,
        m_type: str
    ) -> Optional[BoundaryConstraint]:
        """Scans AST nodes on the given line for Compare or Call patterns."""
        target_nodes: List[ast.AST] = []
        for node in ast.walk(tree):
            if getattr(node, "lineno", None) == lineno:
                target_nodes.append(node)

        for n in target_nodes:
            if isinstance(n, ast.Compare):
                c = self._build_compare_constraint(
                    comp=n,
                    func_name=func_name,
                    class_name=class_name,
                    lineno=lineno,
                    param_names=param_names,
                    param_defaults=param_defaults,
                    mutant_id=mutant_id,
                    orig_expr=orig_expr,
                    mut_expr=mut_expr,
                    m_type=m_type
                )
                if c:
                    return c
            elif isinstance(n, ast.Call):
                c = self._build_call_constraint(
                    call=n,
                    func_name=func_name,
                    class_name=class_name,
                    lineno=lineno,
                    param_names=param_names,
                    param_defaults=param_defaults,
                    mutant_id=mutant_id,
                    orig_expr=orig_expr,
                    mut_expr=mut_expr,
                    m_type=m_type
                )
                if c:
                    return c

        return None

    def _build_compare_constraint(
        self,
        comp: ast.Compare,
        func_name: str,
        class_name: Optional[str],
        lineno: int,
        param_names: List[str],
        param_defaults: Dict[str, Any],
        mutant_id: str,
        orig_expr: str,
        mut_expr: str,
        m_type: str
    ) -> Optional[BoundaryConstraint]:
        """Constructs a BoundaryConstraint from a Compare node."""
        if not comp.ops or not comp.comparators:
            return None

        op = comp.ops[0]
        op_sym = self._op_to_symbol(op)
        left = comp.left
        right = comp.comparators[0]

        # Case A: Sequence length boundary `len(var) <= C`
        if isinstance(left, ast.Call) and isinstance(left.func, ast.Name) and left.func.id == "len" and left.args:
            var_name = self._resolve_target_var(left.args[0], param_names)
            if var_name and isinstance(right, ast.Constant) and isinstance(right.value, int):
                length = right.value
                probes = [
                    [0] * max(0, length - 1),
                    [0] * length,
                    [0] * (length + 1)
                ]
                return BoundaryConstraint(
                    function_name=func_name,
                    class_name=class_name,
                    line_number=lineno,
                    constraint_type="STRING_SEQUENCE",
                    variable_name=var_name,
                    operator=op_sym,
                    threshold_value=length,
                    probe_values=probes,
                    param_names=param_names,
                    target_param=var_name,
                    param_defaults=param_defaults,
                    mutant_id=mutant_id,
                    original_expr=orig_expr,
                    mutated_expr=mut_expr
                )

        # Case B: Numeric boundary `var < C` or `var >= C`
        var_name = self._resolve_target_var(left, param_names)
        if var_name and isinstance(right, ast.Constant) and isinstance(right.value, (int, float)) and not isinstance(right.value, bool):
            val = right.value
            probes = self._generate_numeric_probes(val)
            return BoundaryConstraint(
                function_name=func_name,
                class_name=class_name,
                line_number=lineno,
                constraint_type="NUMERIC_RELATIONAL",
                variable_name=var_name,
                operator=op_sym,
                threshold_value=val,
                probe_values=probes,
                param_names=param_names,
                target_param=var_name,
                param_defaults=param_defaults,
                mutant_id=mutant_id,
                original_expr=orig_expr,
                mutated_expr=mut_expr
            )

        # Case C: Inverted `C < var`
        var_name_r = self._resolve_target_var(right, param_names)
        if var_name_r and isinstance(left, ast.Constant) and isinstance(left.value, (int, float)) and not isinstance(left.value, bool):
            val = left.value
            probes = self._generate_numeric_probes(val)
            return BoundaryConstraint(
                function_name=func_name,
                class_name=class_name,
                line_number=lineno,
                constraint_type="NUMERIC_RELATIONAL",
                variable_name=var_name_r,
                operator=op_sym,
                threshold_value=val,
                probe_values=probes,
                param_names=param_names,
                target_param=var_name_r,
                param_defaults=param_defaults,
                mutant_id=mutant_id,
                original_expr=orig_expr,
                mutated_expr=mut_expr
            )

        # Case D: String equality / membership `var == 'S'`
        if var_name and isinstance(right, ast.Constant) and isinstance(right.value, str):
            s_val = right.value
            probes = [s_val, s_val[:-1] if len(s_val) > 1 else "", s_val + "x", ""]
            return BoundaryConstraint(
                function_name=func_name,
                class_name=class_name,
                line_number=lineno,
                constraint_type="STRING_SEQUENCE",
                variable_name=var_name,
                operator=op_sym,
                threshold_value=s_val,
                probe_values=probes,
                param_names=param_names,
                target_param=var_name,
                param_defaults=param_defaults,
                mutant_id=mutant_id,
                original_expr=orig_expr,
                mutated_expr=mut_expr
            )

        # Case E: Identity guard `var is None` / `var is not None`
        if var_name and isinstance(op, (ast.Is, ast.IsNot)) and isinstance(right, ast.Constant) and right.value is None:
            return BoundaryConstraint(
                function_name=func_name,
                class_name=class_name,
                line_number=lineno,
                constraint_type="GUARD_INVERSION",
                variable_name=var_name,
                operator=op_sym,
                threshold_value=None,
                probe_values=[None, 1, "test"],
                param_names=param_names,
                target_param=var_name,
                param_defaults=param_defaults,
                mutant_id=mutant_id,
                original_expr=orig_expr,
                mutated_expr=mut_expr
            )

        return None

    def _build_call_constraint(
        self,
        call: ast.Call,
        func_name: str,
        class_name: Optional[str],
        lineno: int,
        param_names: List[str],
        param_defaults: Dict[str, Any],
        mutant_id: str,
        orig_expr: str,
        mut_expr: str,
        m_type: str
    ) -> Optional[BoundaryConstraint]:
        """Constructs a BoundaryConstraint from string calls like startswith or endswith."""
        if isinstance(call.func, ast.Attribute) and call.args:
            attr_name = call.func.attr
            if attr_name in ("startswith", "endswith"):
                var_name = self._resolve_target_var(call.func.value, param_names)
                arg_0 = call.args[0]
                if var_name and isinstance(arg_0, ast.Constant) and isinstance(arg_0.value, str):
                    s_val = arg_0.value
                    probes = [s_val, s_val[:-1] if len(s_val) > 1 else "", s_val + "xyz", "", "other"]
                    return BoundaryConstraint(
                        function_name=func_name,
                        class_name=class_name,
                        line_number=lineno,
                        constraint_type="STRING_SEQUENCE",
                        variable_name=var_name,
                        operator=attr_name,
                        threshold_value=s_val,
                        probe_values=probes,
                        param_names=param_names,
                        target_param=var_name,
                        param_defaults=param_defaults,
                        mutant_id=mutant_id,
                        original_expr=orig_expr,
                        mutated_expr=mut_expr
                    )

        return None

    def _generate_numeric_probes(self, threshold: Union[int, float]) -> List[Union[int, float]]:
        """Generates boundary-value triplet [C - 1, C, C + 1] or float equivalent."""
        if isinstance(threshold, int) and not isinstance(threshold, bool):
            return [threshold - 1, threshold, threshold + 1]
        elif isinstance(threshold, float):
            return [round(threshold - 0.01, 4), threshold, round(threshold + 0.01, 4)]
        return [threshold]

    def _resolve_target_var(self, node: ast.AST, param_names: List[str]) -> Optional[str]:
        """Maps an AST variable node to the enclosing function's parameter name."""
        if isinstance(node, ast.Name):
            if node.id in param_names:
                return node.id
            if len(param_names) == 1:
                return param_names[0]
            # Heuristic match
            for p in param_names:
                if node.id.lower() in p.lower() or p.lower() in node.id.lower():
                    return p
            return param_names[0]
        return None

    def _op_to_symbol(self, op: ast.AST) -> str:
        mapping = {
            ast.Gt: ">", ast.Lt: "<", ast.GtE: ">=", ast.LtE: "<=",
            ast.Eq: "==", ast.NotEq: "!=", ast.In: "in", ast.NotIn: "not in",
            ast.Is: "is", ast.IsNot: "is not"
        }
        return mapping.get(type(op), "==")

    # --------------------------------------------------------------------------
    # 2. Test Synthesis & Ground-Truth Oracle Execution
    # --------------------------------------------------------------------------

    def synthesize_boundary_tests(
        self,
        source_code: str,
        surviving_mutants: List[Union[Dict[str, Any], Any]],
        target_module: str = "target",
        companion_context: str = ""
    ) -> str:
        """
        Executes reference function on generated boundary probe values to capture exact
        ground truth return values or raised exceptions, and synthesizes 100% Pass@1 tests.
        """
        constraints = self.extract_boundary_constraints(source_code, surviving_mutants)
        if not constraints:
            return ""

        # Prepare isolated reference environment
        clean_ns: Dict[str, Any] = {"__name__": "__main__"}
        try:
            exec(compile(source_code, "<clean_reference_target>", "exec"), clean_ns)
        except Exception as exc:
            logger.debug(f"Unable to execute clean reference code for oracle querying: {exc}")
            return ""

        test_functions: List[str] = []
        seen_test_keys: Set[str] = set()

        for idx, c in enumerate(constraints):
            func_name = c.function_name
            class_name = c.class_name
            target_callable = None

            if class_name:
                cls_obj = clean_ns.get(class_name)
                if not cls_obj:
                    continue
                try:
                    inst = cls_obj()
                    target_callable = getattr(inst, func_name, None)
                except Exception:
                    continue
            else:
                target_callable = clean_ns.get(func_name)

            if not callable(target_callable):
                continue

            # Query oracle ground truth for each probe value
            probe_outcomes: List[Tuple[str, Any, Any, List[Any]]] = []
            for pv in c.probe_values:
                call_args: List[Any] = []
                for p in c.param_names:
                    if p == c.target_param:
                        call_args.append(pv)
                    else:
                        call_args.append(c.param_defaults.get(p, 1))

                try:
                    ret_val = target_callable(*call_args)
                    probe_outcomes.append(("return", pv, ret_val, call_args))
                except Exception as exc:
                    probe_outcomes.append(("raise", pv, type(exc).__name__, call_args))

            if not probe_outcomes:
                continue

            # Generate deterministic test function
            test_fn_name = f"test_symbolic_boundary_{func_name}_line{c.line_number}_{idx}"
            if test_fn_name in seen_test_keys:
                continue
            seen_test_keys.add(test_fn_name)

            fn_lines: List[str] = [
                f"def {test_fn_name}():",
                f"    \"\"\"Symbolic boundary test targeting {c.constraint_type} on line {c.line_number}.\"\"\"",
                "    import pytest",
            ]
            mod_to_import = target_module if target_module and target_module != "target" else "target"
            if class_name:
                fn_lines.append(f"    from {mod_to_import} import {class_name}")
                fn_lines.append(f"    inst = {class_name}()")
                call_prefix = f"inst.{func_name}"
            else:
                fn_lines.append(f"    from {mod_to_import} import {func_name}")
                call_prefix = func_name

            for outcome, pv, expected, call_args in probe_outcomes:
                args_repr = ", ".join(repr(a) for a in call_args)
                if outcome == "return":
                    if isinstance(expected, float):
                        fn_lines.append(f"    assert pytest.approx({call_prefix}({args_repr}), rel=1e-3) == {repr(expected)}")
                    else:
                        fn_lines.append(f"    assert {call_prefix}({args_repr}) == {repr(expected)}")
                elif outcome == "raise":
                    fn_lines.append(f"    with pytest.raises({expected}):")
                    fn_lines.append(f"        {call_prefix}({args_repr})")

            test_functions.append("\n".join(fn_lines))

        if not test_functions:
            return ""

        header = (
            "# ==============================================================================\n"
            "# Neuro-Symbolic Boundary Constraint Assertions (Synthesized via BVA Oracle)\n"
            "# ==============================================================================\n\n"
        )
        return header + "\n\n\n".join(test_functions) + "\n"
