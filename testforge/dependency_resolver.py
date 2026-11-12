"""
testforge/dependency_resolver.py - Multi-File AST Local Dependency & Companion Resolver.

Analyzes primary Python targets for local sibling/relative imports, resolves companion
modules across workspace search roots without pulling standard library or third-party packages,
and extracts compact AST symbol definitions to enable isolated, multi-file zero-egress hardening.
"""

from __future__ import annotations

import ast
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Python standard library module index (Python 3.10+)
STDLIB_MODULE_NAMES: frozenset[str] = getattr(sys, "stdlib_module_names", frozenset([
    "abc", "argparse", "array", "ast", "asyncio", "base64", "binascii", "builtins",
    "cmath", "collections", "concurrent", "contextlib", "copy", "csv", "ctypes",
    "dataclasses", "datetime", "decimal", "difflib", "dis", "enum", "errno",
    "faulthandler", "fcntl", "fnmatch", "fractions", "functools", "gc", "glob",
    "gzip", "hashlib", "heapq", "hmac", "html", "http", "importlib", "inspect",
    "io", "itertools", "json", "keyword", "linecache", "locale", "logging", "math",
    "mimetypes", "mmap", "multiprocessing", "numbers", "operator", "os", "pathlib",
    "pickle", "pkgutil", "platform", "posix", "pprint", "pstats", "py_compile",
    "queue", "quopri", "random", "re", "reprlib", "resource", "sched", "secrets",
    "select", "selectors", "shelve", "shlex", "shutil", "signal", "site", "socket",
    "sqlite3", "ssl", "stat", "statistics", "string", "struct", "subprocess",
    "sys", "sysconfig", "tarfile", "tempfile", "textwrap", "threading", "time",
    "timeit", "tokenize", "trace", "traceback", "types", "typing", "unicodedata",
    "unittest", "urllib", "uuid", "warnings", "weakref", "xml", "zipfile", "zipimport", "zlib"
]))


@dataclass
class DependencyBundle:
    """Encapsulates resolved companion modules, extracted AST symbols, and dependency graph edges."""
    primary_filename: str
    companion_files: Dict[str, str] = field(default_factory=dict)
    resolved_symbols: List[str] = field(default_factory=list)
    dependency_edges: List[Tuple[str, str]] = field(default_factory=list)
    symbol_signatures: Dict[str, str] = field(default_factory=dict)

    def format_prompt_context(self) -> str:
        """
        Formats a clean, high-density reference block of companion signatures
        for injection into LLM and AST test synthesis prompts.
        """
        if not self.companion_files:
            return ""

        chunks: List[str] = [
            "# --- Multi-File Companion Dependency Signatures ---",
            "# Companion modules materialized inside sandbox environment for import resolution:",
        ]
        for rel_name in sorted(self.companion_files.keys()):
            chunks.append(f"# • {rel_name}")

        if self.symbol_signatures:
            chunks.append("\n# Resolved Companion Types & Callables:")
            for sym, sig in sorted(self.symbol_signatures.items()):
                chunks.append(sig)

        return "\n".join(chunks)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_filename": self.primary_filename,
            "companion_count": len(self.companion_files),
            "companion_files": list(self.companion_files.keys()),
            "resolved_symbols": list(self.resolved_symbols),
            "dependency_edges": [list(e) for e in self.dependency_edges],
            "symbol_signatures_count": len(self.symbol_signatures),
        }


class MultiFileDependencyResolver:
    """
    Parses Python AST imports to detect local relative/sibling dependencies,
    ignores stdlib & installed site-packages, resolves companion files up to depth 3,
    and extracts compact type signatures.
    """

    def __init__(self, search_roots: Optional[List[str]] = None, max_depth: int = 3):
        self.search_roots = search_roots or []
        self.max_depth = max_depth

    def extract_compact_symbols(self, source_code: str, module_path: str = "") -> Tuple[List[str], Dict[str, str]]:
        """Public convenience method to extract compact symbol signatures from any Python code string."""
        try:
            tree = ast.parse(source_code)
            return self._extract_ast_signatures(tree, module_path, wanted_symbols=None)
        except Exception:
            return [], {}

    def resolve_local_dependencies(
        self,
        target_path: str,
        source_code: str,
        search_roots: Optional[List[str]] = None,
        max_depth: Optional[int] = None
    ) -> DependencyBundle:
        """
        Main entry point: resolves local sibling imports from source_code.
        """
        if max_depth is None:
            max_depth = self.max_depth
        primary_name = os.path.basename(target_path) if target_path else "target.py"
        bundle = DependencyBundle(primary_filename=primary_name)

        if not source_code or not source_code.strip():
            return bundle

        # Establish search roots: target parent dir, user roots, current working dir
        all_roots: List[str] = []
        if target_path:
            parent_dir = os.path.dirname(os.path.abspath(target_path))
            if parent_dir and os.path.isdir(parent_dir):
                all_roots.append(parent_dir)

        if search_roots:
            for r in search_roots:
                abs_r = os.path.abspath(r)
                if abs_r not in all_roots and os.path.isdir(abs_r):
                    all_roots.append(abs_r)

        for r in self.search_roots:
            abs_r = os.path.abspath(r)
            if abs_r not in all_roots and os.path.isdir(abs_r):
                all_roots.append(abs_r)

        cwd = os.getcwd()
        if cwd not in all_roots:
            all_roots.append(cwd)

        visited_paths: Set[str] = set()
        if target_path:
            visited_paths.add(os.path.abspath(target_path))

        self._resolve_module_imports(
            source_code=source_code,
            current_file_path=os.path.abspath(target_path) if target_path else os.path.join(cwd, "target.py"),
            current_rel_name=primary_name,
            all_roots=all_roots,
            bundle=bundle,
            visited_paths=visited_paths,
            depth=0,
            max_depth=max_depth
        )

        return bundle

    def _resolve_module_imports(
        self,
        source_code: str,
        current_file_path: str,
        current_rel_name: str,
        all_roots: List[str],
        bundle: DependencyBundle,
        visited_paths: Set[str],
        depth: int,
        max_depth: int
    ) -> None:
        if depth >= max_depth:
            return

        try:
            tree = ast.parse(source_code)
        except Exception:
            return

        curr_dir = os.path.dirname(current_file_path)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod_name = alias.name
                    top_pkg = mod_name.split(".")[0]
                    if top_pkg in STDLIB_MODULE_NAMES:
                        continue

                    match = self._find_module_file(mod_name, curr_dir, all_roots)
                    if match:
                        abs_path, rel_name = match
                        if abs_path not in visited_paths:
                            visited_paths.add(abs_path)
                            self._ingest_companion_file(
                                abs_path, rel_name, current_rel_name, None,
                                all_roots, bundle, visited_paths, depth, max_depth
                            )

            elif isinstance(node, ast.ImportFrom):
                wanted_symbols: Set[str] = {alias.name for alias in node.names if alias.name != "*"}

                if node.level and node.level > 0:
                    # Relative import e.g. from .models import User or from ..common import Config
                    base_dir = curr_dir
                    for _ in range(node.level - 1):
                        base_dir = os.path.dirname(base_dir)

                    target_mod = node.module or ""
                    match = self._find_module_file(target_mod, base_dir, [base_dir])
                    if not match and not target_mod:
                        # from . import models
                        for alias in node.names:
                            m_match = self._find_module_file(alias.name, base_dir, [base_dir])
                            if m_match:
                                abs_path, rel_name = m_match
                                if abs_path not in visited_paths:
                                    visited_paths.add(abs_path)
                                    self._ingest_companion_file(
                                        abs_path, rel_name, current_rel_name, None,
                                        all_roots, bundle, visited_paths, depth, max_depth
                                    )
                        continue

                    if match:
                        abs_path, rel_name = match
                        if abs_path not in visited_paths:
                            visited_paths.add(abs_path)
                            self._ingest_companion_file(
                                abs_path, rel_name, current_rel_name, wanted_symbols,
                                all_roots, bundle, visited_paths, depth, max_depth
                            )
                else:
                    # Absolute import e.g. from models import User or from helpers.pricing import rate
                    mod_name = node.module or ""
                    top_pkg = mod_name.split(".")[0]
                    if top_pkg in STDLIB_MODULE_NAMES:
                        continue

                    match = self._find_module_file(mod_name, curr_dir, all_roots)
                    if not match:
                        # Could be from package import module e.g. from helpers import pricing
                        for alias in node.names:
                            comb = f"{mod_name}.{alias.name}" if mod_name else alias.name
                            m_match = self._find_module_file(comb, curr_dir, all_roots)
                            if m_match:
                                abs_path, rel_name = m_match
                                if abs_path not in visited_paths:
                                    visited_paths.add(abs_path)
                                    self._ingest_companion_file(
                                        abs_path, rel_name, current_rel_name, None,
                                        all_roots, bundle, visited_paths, depth, max_depth
                                    )
                        continue

                    if match:
                        abs_path, rel_name = match
                        if abs_path not in visited_paths:
                            visited_paths.add(abs_path)
                            self._ingest_companion_file(
                                abs_path, rel_name, current_rel_name, wanted_symbols,
                                all_roots, bundle, visited_paths, depth, max_depth
                            )

    def _find_module_file(self, mod_name: str, local_dir: str, search_roots: List[str]) -> Optional[Tuple[str, str]]:
        """
        Locates a module file (.py) given a module dotted name.
        Returns (absolute_file_path, relative_module_filename).
        """
        if not mod_name:
            return None

        rel_as_path = mod_name.replace(".", os.sep)
        candidate_rel_files = [
            f"{rel_as_path}.py",
            os.path.join(rel_as_path, "__init__.py"),
        ]

        # 1. Check local directory first
        for c in candidate_rel_files:
            cand_abs = os.path.normpath(os.path.join(local_dir, c))
            if os.path.isfile(cand_abs):
                return cand_abs, os.path.basename(cand_abs) if os.sep not in c else c

        # 2. Check search roots
        for root in search_roots:
            for c in candidate_rel_files:
                cand_abs = os.path.normpath(os.path.join(root, c))
                if os.path.isfile(cand_abs):
                    rel_name = os.path.relpath(cand_abs, root)
                    return cand_abs, rel_name

        return None

    def _ingest_companion_file(
        self,
        abs_path: str,
        rel_name: str,
        parent_rel_name: str,
        wanted_symbols: Optional[Set[str]],
        all_roots: List[str],
        bundle: DependencyBundle,
        visited_paths: Set[str],
        depth: int,
        max_depth: int
    ) -> None:
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                comp_source = f.read()
        except Exception:
            return

        bundle.companion_files[rel_name] = comp_source
        edge = (parent_rel_name, rel_name)
        if edge not in bundle.dependency_edges:
            bundle.dependency_edges.append(edge)

        # Extract symbols from AST
        try:
            comp_tree = ast.parse(comp_source)
            syms, sigs = self._extract_ast_signatures(comp_tree, rel_name, wanted_symbols)
            for s in syms:
                if s not in bundle.resolved_symbols:
                    bundle.resolved_symbols.append(s)
            bundle.symbol_signatures.update(sigs)
        except Exception:
            comp_tree = None

        # Transitive recursion
        self._resolve_module_imports(
            source_code=comp_source,
            current_file_path=abs_path,
            current_rel_name=rel_name,
            all_roots=all_roots,
            bundle=bundle,
            visited_paths=visited_paths,
            depth=depth + 1,
            max_depth=max_depth
        )

    def _extract_ast_signatures(
        self,
        tree: ast.AST,
        module_name: str,
        wanted_symbols: Optional[Set[str]] = None
    ) -> Tuple[List[str], Dict[str, str]]:
        found_symbols: List[str] = []
        signatures: Dict[str, str] = {}

        for node in getattr(tree, "body", []):
            if isinstance(node, ast.ClassDef):
                if wanted_symbols is None or node.name in wanted_symbols:
                    if not node.name.startswith("_") or (wanted_symbols and node.name in wanted_symbols):
                        found_symbols.append(node.name)
                        base_names = [ast.unparse(b) for b in node.bases]
                        bases_str = f"({', '.join(base_names)})" if base_names else ""
                        lines = [f"class {node.name}{bases_str}:"]

                        doc = ast.get_docstring(node)
                        if doc:
                            lines.append(f'    """{doc.splitlines()[0]}"""')

                        fields_and_methods: List[str] = []
                        for sub in node.body:
                            if isinstance(sub, ast.AnnAssign):
                                tgt = ast.unparse(sub.target)
                                ann = ast.unparse(sub.annotation)
                                val = f" = {ast.unparse(sub.value)}" if sub.value else ""
                                fields_and_methods.append(f"    {tgt}: {ann}{val}")
                            elif isinstance(sub, ast.Assign):
                                for t in sub.targets:
                                    t_name = ast.unparse(t)
                                    if not t_name.startswith("_"):
                                        fields_and_methods.append(f"    {t_name} = {ast.unparse(sub.value)}")
                            elif isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                if sub.name == "__init__" or not sub.name.startswith("_"):
                                    args_str = ast.unparse(sub.args)
                                    ret = f" -> {ast.unparse(sub.returns)}" if sub.returns else ""
                                    fields_and_methods.append(f"    def {sub.name}({args_str}){ret}: ...")

                        if fields_and_methods:
                            lines.extend(fields_and_methods[:15])
                        elif not doc:
                            lines.append("    pass")

                        signatures[node.name] = "\n".join(lines)

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if wanted_symbols is None or node.name in wanted_symbols:
                    if not node.name.startswith("_") or (wanted_symbols and node.name in wanted_symbols):
                        found_symbols.append(node.name)
                        args_str = ast.unparse(node.args)
                        ret = f" -> {ast.unparse(node.returns)}" if node.returns else ""
                        doc = ast.get_docstring(node)
                        doc_str = f'    """{doc.splitlines()[0]}"""\n' if doc else ""
                        signatures[node.name] = f"def {node.name}({args_str}){ret}:\n{doc_str}    ..."

            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    t_name = ast.unparse(t)
                    if wanted_symbols is None or t_name in wanted_symbols:
                        if not t_name.startswith("_"):
                            found_symbols.append(t_name)
                            signatures[t_name] = f"{t_name} = {ast.unparse(node.value)}"

            elif isinstance(node, ast.AnnAssign):
                t_name = ast.unparse(node.target)
                if wanted_symbols is None or t_name in wanted_symbols:
                    if not t_name.startswith("_"):
                        found_symbols.append(t_name)
                        val = f" = {ast.unparse(node.value)}" if node.value else ""
                        signatures[t_name] = f"{t_name}: {ast.unparse(node.annotation)}{val}"

        return found_symbols, signatures


def resolve_dependencies_for_file(filepath: str, search_roots: Optional[List[str]] = None) -> DependencyBundle:
    """Convenience helper to read and resolve dependencies from a file path."""
    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()
    resolver = MultiFileDependencyResolver(search_roots=search_roots)
    return resolver.resolve_local_dependencies(filepath, code)
