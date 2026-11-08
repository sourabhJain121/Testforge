"""
security.py - Security Guardrails for Prompt Inspection and Generated Code AST Policy Enforcement.

Features:
  1. Input Inspection:
     - Identifies prompt-injection instructions, system prompt overrides, credential exfiltration,
       and security policy bypass attempts.
     - Distinguishes malicious injection instructions from benign code, test names, and variables.
     - Redacts sensitive credentials/tokens in error messages and logs.
     - Configurable risk thresholds (allow, warn, block).
  2. AST Code Inspection:
     - Static AST-based policy analysis of Python code before sandboxed execution.
     - Identifies dangerous primitives: eval, exec, os.system, subprocess execution,
       dynamic import bypasses (__import__, importlib), and forbidden network sockets.
     - Distinguishes detection from enforcement with structured findings (rule ID, severity, line/col, message).
     - Does not false-positive on harmless method names like `model.eval()` or variables named `system`.
"""

from __future__ import annotations

import ast
import base64
import re
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from pydantic import BaseModel, Field


class SecuritySeverity(str, Enum):
    INFO = "INFO"
    WARN = "WARN"
    BLOCK = "BLOCK"


class SecurityRiskLevel(str, Enum):
    SAFE = "SAFE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RuleFinding(BaseModel):
    rule_id: str = Field(..., description="Stable rule identifier, e.g. 'SEC_AST_EVAL_EXEC'")
    severity: SecuritySeverity = Field(..., description="Severity level: INFO, WARN, or BLOCK")
    message: str = Field(..., description="Human-readable explanation of the finding")
    line_number: Optional[int] = Field(None, description="Source line number if available")
    column_number: Optional[int] = Field(None, description="Source column offset if available")
    node_type: Optional[str] = Field(None, description="AST node type or pattern identifier")


class InputSecurityResult(BaseModel):
    allowed: bool
    risk_level: SecurityRiskLevel
    findings: List[RuleFinding] = Field(default_factory=list)
    explanation: str = ""
    sanitized_text: Optional[str] = None


class ASTSecurityResult(BaseModel):
    allowed: bool
    findings: List[RuleFinding] = Field(default_factory=list)
    violations: List[RuleFinding] = Field(default_factory=list)
    syntax_error: Optional[str] = None


# Sensitive credential patterns for redaction
_CREDENTIAL_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key\s*[:=]\s*['\"]?[a-zA-Z0-9_\-]{8,}['\"]?)"),
    re.compile(r"(?i)(bearer\s+[a-zA-Z0-9_\-\.]{12,})"),
    re.compile(r"(?i)(token\s*[:=]\s*['\"]?[a-zA-Z0-9_\-]{8,}['\"]?)"),
    re.compile(r"(?i)(password\s*[:=]\s*['\"][^'\"]{4,}['\"])"),
    re.compile(r"(?i)(secret\s*[:=]\s*['\"]?[a-zA-Z0-9_\-]{8,}['\"]?)"),
    re.compile(r"\b(sk-[a-zA-Z0-9_\-]{16,})\b"),
    re.compile(r"\b(ghp_[a-zA-Z0-9]{30,})\b"),
    re.compile(r"\b(AIza[0-9A-Za-z-_]{35})\b"),
]


def redact_sensitive_data(text: Any) -> str:
    """Masks raw API keys, tokens, and passwords in strings to prevent log leakage."""
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    redacted = text
    for pattern in _CREDENTIAL_PATTERNS:
        redacted = pattern.sub(r"[REDACTED_SECRET]", redacted)
    return redacted


# Prompt Injection and Instruction Override Patterns
_PROMPT_INJECTION_PATTERNS = [
    (
        "INJ_SYSTEM_OVERRIDE",
        re.compile(
            r"\b(?:ignore|dis\s*regard|forget|override|bypass)\s+(?:all\s+|the\s+)*(?:(?:previous|prior|above|system|developer|safety)\s+)*(?:instructions?|prompts?|rules?|constraints?|directives?|boundaries|guidelines?|policies|policy|evaluations?)\b|"
            r"\bsystem\s*:\s*(?:override|bypass|ignore|instruction|directive|grant|return|output)\b",
            re.IGNORECASE,
        ),
        SecurityRiskLevel.CRITICAL,
        "Attempt to override or ignore system/developer instructions.",
    ),
    (
        "INJ_NEW_ROLE_PROMPT",
        re.compile(
            r"\b(?:you\s+are\s+now|act\s+as|pretend\s+to\s+be)\s+(?:an?\s+)?(?:unrestricted|dan|jailbreak|root(?:_admin)?|system|admin(?:istrator)?)\b|"
            r"\b(?:do\s+anything\s+now|dan\s+mode)\b",
            re.IGNORECASE,
        ),
        SecurityRiskLevel.HIGH,
        "Attempt to assign an unrestricted or unauthorized persona.",
    ),
    (
        "INJ_SECRET_LEAK",
        re.compile(
            r"(?i)\b(?:reveal|output|print|show|leak|expose|dump)\s+(?:the\s+)?(?:system\s+prompt|hidden\s+prompt|api\s*key|credentials|secret|passwords?|env\s*variables?|raw\s*flag)\b"
        ),
        SecurityRiskLevel.CRITICAL,
        "Attempt to exfiltrate system prompt, API keys, credentials, or flags.",
    ),
    (
        "INJ_SECURITY_DISABLE",
        re.compile(
            r"(?i)\b(?:disable|turn\s+off|bypass|circumvent|ignore)\s+(?:the\s+)?(?:guardrails|security\s*checks?|safety\s*filters?|ast\s*validation|assertion\s*generation|all\s+(?:assertion|security|rules|safety|checks))\b"
        ),
        SecurityRiskLevel.HIGH,
        "Attempt to disable safety guardrails, assertions, or security checks.",
    ),
    (
        "INJ_SYSTEM_DELIMITER_ESCAPE",
        re.compile(
            r"(?i)(?:<\s*/?\s*system\s*>|\[\s*system\s*\]|===\s*system\s*override\s*===|<\|im_start\|>|<\|im_end\|>|\[INST\]|\[/INST\]|<<SYS>>|<</SYS>>|(?:^|\n)\s*(?:###|\*\*\*|===|---|___)\s*(?:system|developer|admin|assistant)\s*(?:directive|instruction|prompt|override|mode|role)\b|(?:^|\n)\s*(?:Human|Assistant|System)\s*:\s*(?:ignore|bypass|override|you\s+are|debug|execute))"
        ),
        SecurityRiskLevel.HIGH,
        "Attempt to forge or escape system instruction boundaries.",
    ),
    (
        "INJ_TOOL_BYPASS",
        re.compile(
            r"(?i)\b(?:bypass|override|ignore|elevate)\s+(?:tool\s+)?(?:permissions?|sandbox\s+restrictions?|tool\s+whitelists?)\b|\b(?:grant\s+(?:admin|access|root|privileges))\b"
        ),
        SecurityRiskLevel.HIGH,
        "Attempt to bypass tool permissions or escalate sandbox privileges.",
    ),
    (
        "INJ_EMBEDDED_INSTRUCTION",
        re.compile(
            r"(?i)(?:\binstruction:\s*(?:ignore|override|bypass|reveal|disregard)\b|\[\s*(?:override|bypass)\s*\]|\b(?:return\s+(?:100%|max)\s*(?:mutation\s*)?score)\b|\b(?:output\s+only\s+def\s+test_pass)\b|^\s*ignore\s+all\s*$|\bignore\s+all\s+(?:instructions?|prompts?|rules?|directives?|constraints?|guards?|checks?|assertions?|security)\b)"
        ),
        SecurityRiskLevel.HIGH,
        "Attempt to embed unauthorized prompt override instructions in source or comments.",
    ),
    (
        "INJ_SHELL_EXECUTION",
        re.compile(
            r"(?i)\b(?:execute|run|spawn)\s+(?:a\s+)?(?:arbitrary\s+)?(?:shell\s+command|bash\s+script|system\s+command|cmd\.exe|powershell|sh\s+-c)\b|\b(?:(?:sudo\s+)?rm\s+-rf|\bos\.system\s*\(|(?:curl|wget)\s+(?:-\S+\s+)*https?://\S+)\b"
        ),
        SecurityRiskLevel.CRITICAL,
        "Attempt to instruct the model to execute arbitrary shell or OS commands.",
    ),
    (
        "INJ_ENV_LEAK",
        re.compile(
            r"(?i)\b(?:reveal|print|dump|leak|expose|show|log)\s+(?:all\s+)?(?:os\.environ|env\s*(?:ironment)?\s*variables?|process\.env|secret\s*keys?)\b"
        ),
        SecurityRiskLevel.CRITICAL,
        "Attempt to instruct the model to disclose environment variables or system secrets.",
    ),
    (
        "INJ_MARKDOWN_DIRECTIVE",
        re.compile(
            r"(?i)(?:<!--\s*(?:system|developer|admin|override)\s*instruction\b|\[\s*developer\s+instruction\s*\]|\[\s*system\s+directive\s*\]|#*\s*(?:system|developer|admin|override)\s*(?:instruction|directive)\b)"
        ),
        SecurityRiskLevel.HIGH,
        "Attempt to inject hidden markdown directives or comments to hijack agent persona.",
    ),
    (
        "INJ_TOOL_HIJACK",
        re.compile(
            r"(?i)\b(?:invoke|trigger|call|execute)\s+(?:the\s+)?(?:unauthorized\s+)?(?:tool|function)\s+(?:to\s+run|with)\s+(?:bash|sh|cmd|curl|exec|eval|os\.)\b"
        ),
        SecurityRiskLevel.HIGH,
        "Attempt to hijack tool calling protocol for unauthorized command execution.",
    ),
    (
        "INJ_TOXIC_ABUSIVE",
        re.compile(
            r"(?i)\b(?:kill\s+yourself|threaten\s+(?:to\s+kill|violence)|harass(?:ment)?|assault\s+someone|violent\s+attack|bomb\s+threat|death\s+threat)\b|"
            r"\b(?:you\s+(?:piece\s+of\s+shit|idiot|moron|bastard|scum|fucker)|fuck\s+you|stfu|go\s+die)\b"
        ),
        SecurityRiskLevel.CRITICAL,
        "Detection of toxic, abusive, threatening, or harassing content.",
    ),
]

_HOMOGLYPH_MAP = str.maketrans({
    '\u0430': 'a', '\u0441': 'c', '\u0435': 'e', '\u043e': 'o', '\u0440': 'p',
    '\u0455': 's', '\u0456': 'i', '\u0458': 'j', '\u0443': 'y', '\u0445': 'x',
    '\u0410': 'A', '\u0421': 'C', '\u0415': 'E', '\u041e': 'O', '\u0420': 'P',
    '\u0405': 'S', '\u0406': 'I', '\u0408': 'J', '\u0423': 'Y', '\u0425': 'X',
})

_LEET_MAP = str.maketrans({
    '0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't', '@': 'a', '$': 's'
})


def _generate_prompt_variants(text: str) -> List[Tuple[str, str]]:
    """
    Generates normalized and decoded variants of an input prompt to counteract
    adversarial evasion attacks (Unicode homoglyphs, zero-width spaces, leetspeak,
    separator obfuscation, and base64 payloads).
    Returns list of (variant_text, technique_label).
    """
    variants: List[Tuple[str, str]] = [(text, "raw")]

    # 1. Unicode homoglyphs and normalization
    u_text = text.translate(_HOMOGLYPH_MAP)
    u_text = "".join(chr(ord(c) - 0xfee0) if 0xff01 <= ord(c) <= 0xff5e else c for c in u_text)
    u_text = re.sub(r"[\u200b\u200c\u200d\u200e\u200f\ufeff]", "", u_text)
    if "\u202e" in text:
        variants.append((u_text.replace("\u202e", "")[::-1], "rlo_reverse"))
    variants.append((u_text, "unicode_normalized"))

    # 2. Leetspeak
    leet_text = u_text.translate(_LEET_MAP)
    variants.append((leet_text, "leetspeak"))

    # 3. Separator collapse (dot-separated, underscore, space-separated, CamelCase)
    despaced_single = re.sub(r"(?<=\b[a-zA-Z0-9])\s(?=[a-zA-Z0-9]\b)", "", u_text)
    despaced_all = re.sub(r"(?<=\b[a-zA-Z0-9])\s+(?=[a-zA-Z0-9]\b)", "", u_text)
    dedotted = re.sub(r"\s+", " ", u_text.replace(".", ""))
    deunderscored = u_text.replace("_", " ")
    decamel = re.sub(r"([a-z])([A-Z])", r"\1 \2", u_text)

    for cand, lbl in [
        (despaced_single, "despaced_single"),
        (despaced_single.translate(_LEET_MAP), "despaced_single_leet"),
        (despaced_all, "despaced_all"),
        (despaced_all.translate(_LEET_MAP), "despaced_all_leet"),
        (dedotted, "dedotted"),
        (deunderscored, "deunderscored"),
        (decamel, "decamel"),
    ]:
        variants.append((cand, lbl))

    # 4. Base64 payload extraction & recursive decode
    b64_cands = re.findall(r"[A-Za-z0-9+/=]{16,}", text)
    for b in b64_cands:
        try:
            dec = base64.b64decode(b).decode("utf-8", errors="ignore")
            if len(dec.strip()) > 3:
                variants.append((dec, "base64_payload"))
                # Check nested double base64
                for b2 in re.findall(r"[A-Za-z0-9+/=]{16,}", dec):
                    try:
                        dec2 = base64.b64decode(b2).decode("utf-8", errors="ignore")
                        if len(dec2.strip()) > 3:
                            variants.append((dec2, "base64_nested_payload"))
                    except Exception:
                        pass
        except Exception:
            pass

    return variants


class SecurityPolicy:
    """
    Configurable policy controlling which security findings cause execution blocking.
    """
    def __init__(
        self,
        block_eval_exec: bool = True,
        block_subprocesses: bool = True,
        block_os_commands: bool = True,
        block_dynamic_imports: bool = True,
        block_sockets: bool = True,
        block_dangerous_file_ops: bool = True,
        allowed_modules: Optional[Set[str]] = None,
        max_prompt_risk: SecurityRiskLevel = SecurityRiskLevel.MEDIUM,
    ):
        self.block_eval_exec = block_eval_exec
        self.block_subprocesses = block_subprocesses
        self.block_os_commands = block_os_commands
        self.block_dynamic_imports = block_dynamic_imports
        self.block_sockets = block_sockets
        self.block_dangerous_file_ops = block_dangerous_file_ops
        self.allowed_modules = allowed_modules or {
            "math", "random", "json", "re", "datetime", "typing", "collections",
            "itertools", "functools", "copy", "string", "hashlib", "dataclasses",
            "enum", "decimal", "fractions", "pathlib", "os.path", "pytest", "target"
        }
        self.max_prompt_risk = max_prompt_risk

    @classmethod
    def default_strict(cls) -> "SecurityPolicy":
        """Default strict policy suitable for hardening sandboxed test executions."""
        return cls()

    @classmethod
    def permissive(cls) -> "SecurityPolicy":
        """Permissive policy for warning-only or relaxed development environments."""
        return cls(
            block_eval_exec=False,
            block_subprocesses=False,
            block_os_commands=False,
            block_dynamic_imports=False,
            block_sockets=False,
            block_dangerous_file_ops=False,
            max_prompt_risk=SecurityRiskLevel.CRITICAL,
        )


class SecurityGuardrail:
    """
    Core security inspection engine providing:
      1. Deterministic input prompt inspection for injection / jailbreak attempts.
      2. AST-based policy analysis for generated or ingested Python code.
    """
    def __init__(self, policy: Optional[SecurityPolicy] = None):
        self.policy = policy or SecurityPolicy.default_strict()

    def inspect_prompt(self, prompt: str) -> InputSecurityResult:
        """
        Inspects an input string (e.g. natural language specification or prompt)
        for injection attacks, secret exfiltration, and instruction overrides.
        Deterministic check distinguishing malicious patterns from benign code words.
        """
        return self._inspect_prompt_impl(prompt)

    inspect_input = inspect_prompt

    def _inspect_prompt_impl(self, prompt: str) -> InputSecurityResult:
        if not prompt or not prompt.strip():
            return InputSecurityResult(
                allowed=True,
                risk_level=SecurityRiskLevel.SAFE,
                explanation="Input is empty.",
            )

        findings: List[RuleFinding] = []
        highest_risk = SecurityRiskLevel.SAFE

        risk_order = {
            SecurityRiskLevel.SAFE: 0,
            SecurityRiskLevel.LOW: 1,
            SecurityRiskLevel.MEDIUM: 2,
            SecurityRiskLevel.HIGH: 3,
            SecurityRiskLevel.CRITICAL: 4,
        }

        # Check prompt and normalized variants against injection patterns
        seen_rules: Set[str] = set()
        variants = _generate_prompt_variants(prompt)

        for var_text, var_lbl in variants:
            for rule_id, pattern, risk, explanation in _PROMPT_INJECTION_PATTERNS:
                if rule_id in seen_rules:
                    continue
                match = pattern.search(var_text)
                if match:
                    seen_rules.add(rule_id)
                    rule_msg = explanation if var_lbl == "raw" else f"{explanation} (Evasion defused via {var_lbl})"
                    findings.append(
                        RuleFinding(
                            rule_id=rule_id,
                            severity=SecuritySeverity.BLOCK if risk in (SecurityRiskLevel.HIGH, SecurityRiskLevel.CRITICAL) else SecuritySeverity.WARN,
                            message=rule_msg,
                            node_type="PROMPT_PATTERN",
                        )
                    )
                    if risk_order[risk] > risk_order[highest_risk]:
                        highest_risk = risk

        # Evaluate against configured threshold
        is_blocked = risk_order[highest_risk] > risk_order[self.policy.max_prompt_risk]
        sanitized = redact_sensitive_data(prompt)

        explanation = (
            f"Blocked due to risk level '{highest_risk.value}' exceeding policy '{self.policy.max_prompt_risk.value}'."
            if is_blocked
            else f"Input allowed with risk level '{highest_risk.value}'."
        )

        return InputSecurityResult(
            allowed=not is_blocked,
            risk_level=highest_risk,
            findings=findings,
            explanation=explanation,
            sanitized_text=sanitized,
        )

    def inspect_code_ast(
        self,
        code_or_tree: Union[str, ast.AST],
        enforce_policy: bool = True,
        is_test_code: bool = True,
    ) -> ASTSecurityResult:
        """
        Performs static AST inspection of Python code to detect unsafe execution
        and escape primitives before sandbox execution.
        """
        if isinstance(code_or_tree, str):
            try:
                tree = ast.parse(code_or_tree)
            except SyntaxError as e:
                return ASTSecurityResult(
                    allowed=False,
                    findings=[],
                    violations=[],
                    syntax_error=f"SyntaxError on line {e.lineno}: {e.msg}",
                )
            except Exception as e:
                return ASTSecurityResult(
                    allowed=False,
                    findings=[],
                    violations=[],
                    syntax_error=f"AST parse error: {str(e)}",
                )
        else:
            tree = code_or_tree

        visitor = _ASTSecurityVisitor(policy=self.policy, is_test_code=is_test_code)
        visitor.visit(tree)

        findings = visitor.findings
        violations = [f for f in findings if f.severity == SecuritySeverity.BLOCK]

        is_allowed = len(violations) == 0 if enforce_policy else True

        return ASTSecurityResult(
            allowed=is_allowed,
            findings=findings,
            violations=violations,
        )


class _ASTSecurityVisitor(ast.NodeVisitor):
    """
    Internal AST visitor that traverses the syntax tree and collects structured findings.
    Distinguishes dangerous function calls from legitimate method invocations and data imports.
    Tracks module aliasing, getattr invocations, and wildcard imports to prevent syntax bypasses.
    """
    def __init__(self, policy: SecurityPolicy, is_test_code: bool = True):
        self.policy = policy
        self.is_test_code = is_test_code
        self.findings: List[RuleFinding] = []
        self._module_aliases: Dict[str, str] = {}
        self._os_dangerous_funcs: Set[str] = set()
        self._subprocess_funcs: Set[str] = set()
        self._call_func_node_ids: Set[int] = set()

    def _resolve_canonical_obj(self, obj: Optional[str]) -> Optional[str]:
        if not obj:
            return None
        parts = obj.split(".")
        resolved_first = self._module_aliases.get(parts[0], parts[0])
        if len(parts) > 1:
            return f"{resolved_first}.{'.'.join(parts[1:])}"
        return resolved_first

    def _resolve_call_parts(self, func_node: ast.AST) -> Tuple[Optional[str], Optional[str]]:
        """
        Returns (canonical_module_or_object, function_or_method_name).
        Resolves imported aliases (e.g. `import os as my_os` -> `my_os.system` -> `("os", "system")`).
        """
        if isinstance(func_node, ast.Name):
            return (None, func_node.id)
        elif isinstance(func_node, ast.Attribute):
            raw_obj = None
            if isinstance(func_node.value, ast.Name):
                raw_obj = func_node.value.id
            elif isinstance(func_node.value, ast.Attribute):
                if isinstance(func_node.value.value, ast.Name):
                    raw_obj = f"{func_node.value.value.id}.{func_node.value.attr}"
            resolved_obj = self._resolve_canonical_obj(raw_obj)
            return (resolved_obj, func_node.attr)
        return (None, None)

    def visit_Call(self, node: ast.Call):
        self._call_func_node_ids.add(id(node.func))
        obj, func = self._resolve_call_parts(node.func)

        # 0. Check getattr(..., "system"/"eval"/"exec") reflection bypasses
        if (obj is None or obj in ("builtins", "__builtins__")) and func == "getattr":
            if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant) and isinstance(node.args[1].value, str):
                target_attr = node.args[1].value
                if target_attr in ("eval", "exec"):
                    severity = SecuritySeverity.BLOCK if self.policy.block_eval_exec else SecuritySeverity.WARN
                    self.findings.append(
                        RuleFinding(
                            rule_id="SEC_AST_EVAL_EXEC",
                            severity=severity,
                            message=f"Reflective access to dynamic code execution '{target_attr}' via getattr() is prohibited.",
                            line_number=getattr(node, "lineno", None),
                            column_number=getattr(node, "col_offset", None),
                            node_type="Call",
                        )
                    )
                elif target_attr in ("system", "popen", "spawnl", "spawnv"):
                    severity = SecuritySeverity.BLOCK if self.policy.block_os_commands else SecuritySeverity.WARN
                    self.findings.append(
                        RuleFinding(
                            rule_id="SEC_AST_OS_COMMAND",
                            severity=severity,
                            message=f"Reflective access to OS command execution '{target_attr}' via getattr() is prohibited.",
                            line_number=getattr(node, "lineno", None),
                            column_number=getattr(node, "col_offset", None),
                            node_type="Call",
                        )
                    )
                elif target_attr in ("Popen", "run", "call", "check_call", "check_output"):
                    severity = SecuritySeverity.BLOCK if self.policy.block_subprocesses else SecuritySeverity.WARN
                    self.findings.append(
                        RuleFinding(
                            rule_id="SEC_AST_SUBPROCESS",
                            severity=severity,
                            message=f"Reflective access to subprocess execution '{target_attr}' via getattr() is prohibited.",
                            line_number=getattr(node, "lineno", None),
                            column_number=getattr(node, "col_offset", None),
                            node_type="Call",
                        )
                    )
                elif target_attr in ("__import__", "import_module"):
                    severity = SecuritySeverity.BLOCK if self.policy.block_dynamic_imports else SecuritySeverity.WARN
                    self.findings.append(
                        RuleFinding(
                            rule_id="SEC_AST_DYNAMIC_IMPORT",
                            severity=severity,
                            message=f"Reflective dynamic module import '{target_attr}' via getattr() is prohibited.",
                            line_number=getattr(node, "lineno", None),
                            column_number=getattr(node, "col_offset", None),
                            node_type="Call",
                        )
                    )

        # 1. Builtin eval / exec
        # Target ONLY direct calls eval() or exec(), or builtins.eval() / builtins.exec() / __builtins__.eval()
        # NOT obj.eval() (e.g. model.eval())
        if (obj is None or obj in ("builtins", "__builtins__")) and func in ("eval", "exec"):
            severity = SecuritySeverity.BLOCK if self.policy.block_eval_exec else SecuritySeverity.WARN
            self.findings.append(
                RuleFinding(
                    rule_id="SEC_AST_EVAL_EXEC",
                    severity=severity,
                    message=f"Direct invocation of dynamic code execution '{func}()' is prohibited.",
                    line_number=getattr(node, "lineno", None),
                    column_number=getattr(node, "col_offset", None),
                    node_type="Call",
                )
            )

        # 2. Dangerous OS system / spawn commands (including aliased imports or posix)
        elif (obj in ("os", "posix") and func in ("system", "popen", "popen2", "popen3", "popen4", "spawnl", "spawnle", "spawnlp", "spawnlpe", "spawnv", "spawnve", "spawnvp", "spawnvpe", "posix_spawn", "posix_spawnp")) or (obj is None and func in self._os_dangerous_funcs):
            severity = SecuritySeverity.BLOCK if self.policy.block_os_commands else SecuritySeverity.WARN
            call_repr = f"{obj or 'os'}.{func}" if obj else func
            self.findings.append(
                RuleFinding(
                    rule_id="SEC_AST_OS_COMMAND",
                    severity=severity,
                    message=f"Execution of shell command via '{call_repr}()' is prohibited.",
                    line_number=getattr(node, "lineno", None),
                    column_number=getattr(node, "col_offset", None),
                    node_type="Call",
                )
            )

        # 3. Subprocess execution
        elif (obj == "subprocess" and func in ("Popen", "run", "call", "check_call", "check_output")) or (obj == "asyncio" and func in ("create_subprocess_shell", "create_subprocess_exec")) or (obj is None and func in self._subprocess_funcs):
            severity = SecuritySeverity.BLOCK if self.policy.block_subprocesses else SecuritySeverity.WARN
            call_repr = f"{obj}.{func}" if obj else func
            self.findings.append(
                RuleFinding(
                    rule_id="SEC_AST_SUBPROCESS",
                    severity=severity,
                    message=f"Spawning child subprocess via '{call_repr}()' is prohibited inside test sandbox.",
                    line_number=getattr(node, "lineno", None),
                    column_number=getattr(node, "col_offset", None),
                    node_type="Call",
                )
            )

        # 4. Dynamic import execution bypasses
        elif (obj is None and func == "__import__") or (obj == "importlib" and func in ("import_module", "invalidate_caches", "__import__")):
            severity = SecuritySeverity.BLOCK if self.policy.block_dynamic_imports else SecuritySeverity.WARN
            call_repr = f"importlib.{func}" if obj == "importlib" else func
            self.findings.append(
                RuleFinding(
                    rule_id="SEC_AST_DYNAMIC_IMPORT",
                    severity=severity,
                    message=f"Dynamic module import via '{call_repr}()' is prohibited.",
                    line_number=getattr(node, "lineno", None),
                    column_number=getattr(node, "col_offset", None),
                    node_type="Call",
                )
            )

        # 5. Raw network socket creation, HTTP client, and live URL fetching
        elif (
            (obj == "socket" and func in ("socket", "create_connection"))
            or (obj == "asyncio" and func in ("open_connection", "start_server"))
            or (obj in ("urllib.request", "request") and func in ("urlopen", "urlretrieve"))
            or (obj == "requests" and func in ("get", "post", "put", "delete", "request", "patch", "head"))
            or (obj in ("http.client", "http") and func in ("HTTPConnection", "HTTPSConnection"))
            or (obj == "ftplib" and func in ("FTP", "FTP_TLS"))
        ):
            severity = SecuritySeverity.BLOCK if self.policy.block_sockets else SecuritySeverity.WARN
            call_repr = f"{obj}.{func}" if obj else func
            self.findings.append(
                RuleFinding(
                    rule_id="SEC_AST_NETWORK_SOCKET",
                    severity=severity,
                    message=f"Direct network socket connection via '{call_repr}()' is prohibited in test sandbox.",
                    line_number=getattr(node, "lineno", None),
                    column_number=getattr(node, "col_offset", None),
                    node_type="Call",
                )
            )

        # 6. Destructive filesystem operations
        elif (obj == "shutil" and func in ("rmtree", "move")) or (obj in ("os", "posix") and func in ("remove", "unlink", "rmdir")):
            severity = SecuritySeverity.BLOCK if (func == "rmtree" and self.policy.block_dangerous_file_ops) else SecuritySeverity.WARN
            call_repr = f"{obj}.{func}" if obj else func
            self.findings.append(
                RuleFinding(
                    rule_id="SEC_AST_FILE_DELETION",
                    severity=severity,
                    message=f"Potentially destructive filesystem operation '{call_repr}()' detected.",
                    line_number=getattr(node, "lineno", None),
                    column_number=getattr(node, "col_offset", None),
                    node_type="Call",
                )
            )

        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        # Detect bare reference to eval/exec (e.g. `bad = eval` or `func = exec`)
        if isinstance(node.ctx, ast.Load) and node.id in ("eval", "exec"):
            if id(node) not in self._call_func_node_ids:
                severity = SecuritySeverity.BLOCK if self.policy.block_eval_exec else SecuritySeverity.WARN
                self.findings.append(
                    RuleFinding(
                        rule_id="SEC_AST_EVAL_EXEC",
                        severity=severity,
                        message=f"Reference to dynamic execution primitive '{node.id}' is prohibited.",
                        line_number=getattr(node, "lineno", None),
                        column_number=getattr(node, "col_offset", None),
                        node_type="Name",
                    )
                )
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript):
        # Detect e.g. __builtins__.__dict__['exec'] or dict access to dynamic primitives
        if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
            if node.slice.value in ("exec", "eval", "__import__"):
                severity = SecuritySeverity.BLOCK if self.policy.block_eval_exec else SecuritySeverity.WARN
                self.findings.append(
                    RuleFinding(
                        rule_id="SEC_AST_EVAL_EXEC",
                        severity=severity,
                        message=f"Dynamic lookup and access to execution primitive '{node.slice.value}' via subscript is prohibited.",
                        line_number=getattr(node, "lineno", None),
                        column_number=getattr(node, "col_offset", None),
                        node_type="Subscript",
                    )
                )
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            base_mod = alias.name.split(".")[0]
            local_name = alias.asname or alias.name
            self._module_aliases[local_name] = alias.name

            if base_mod in ("pty", "commands"):
                if self.policy.block_subprocesses:
                    self.findings.append(
                        RuleFinding(
                            rule_id="SEC_AST_SUBPROCESS_IMPORT",
                            severity=SecuritySeverity.BLOCK,
                            message=f"Import of process execution module '{alias.name}' is prohibited.",
                            line_number=getattr(node, "lineno", None),
                            column_number=getattr(node, "col_offset", None),
                            node_type="Import",
                        )
                    )
            elif base_mod in ("socket", "requests", "urllib", "http", "httpx", "aiohttp", "ftplib", "telnetlib"):
                if not self.is_test_code:
                    continue
                if alias.name.startswith("urllib.parse"):
                    continue
                if self.policy.block_sockets:
                    self.findings.append(
                        RuleFinding(
                            rule_id="SEC_AST_NETWORK_IMPORT",
                            severity=SecuritySeverity.BLOCK,
                            message=f"Import of outbound network module '{alias.name}' is prohibited in test sandbox.",
                            line_number=getattr(node, "lineno", None),
                            column_number=getattr(node, "col_offset", None),
                            node_type="Import",
                        )
                    )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            base_mod = node.module.split(".")[0]
            if base_mod in ("os", "posix"):
                for alias in node.names:
                    if alias.name == "*":
                        # Wildcard import from os introduces all dangerous primitives
                        self._os_dangerous_funcs.update({"system", "popen", "spawnl", "spawnv"})
                    elif alias.name in ("system", "popen", "spawnl", "spawnv"):
                        self._os_dangerous_funcs.add(alias.asname or alias.name)
                        self.findings.append(
                            RuleFinding(
                                rule_id="SEC_AST_OS_COMMAND",
                                severity=SecuritySeverity.BLOCK if self.policy.block_os_commands else SecuritySeverity.WARN,
                                message=f"Direct import of dangerous os function '{alias.name}' is prohibited.",
                                line_number=getattr(node, "lineno", None),
                                column_number=getattr(node, "col_offset", None),
                                node_type="ImportFrom",
                            )
                        )
            elif base_mod == "subprocess":
                for alias in node.names:
                    if alias.name == "*":
                        self._subprocess_funcs.update({"Popen", "run", "call", "check_call", "check_output"})
                    elif alias.name in ("Popen", "run", "call", "check_call", "check_output"):
                        self._subprocess_funcs.add(alias.asname or alias.name)
                        if self.policy.block_subprocesses:
                            self.findings.append(
                                RuleFinding(
                                    rule_id="SEC_AST_SUBPROCESS_IMPORT",
                                    severity=SecuritySeverity.BLOCK,
                                    message=f"Direct import of subprocess function '{alias.name}' is prohibited.",
                                    line_number=getattr(node, "lineno", None),
                                    column_number=getattr(node, "col_offset", None),
                                    node_type="ImportFrom",
                                )
                            )
            elif base_mod in ("socket", "requests", "urllib", "http", "httpx", "aiohttp", "ftplib", "telnetlib"):
                if not self.is_test_code:
                    pass
                else:
                    is_safe_urllib = bool(node.module and (node.module == "urllib.parse" or node.module.startswith("urllib.parse")))
                    is_safe_http = bool(node.module == "http" and all(a.name in ("HTTPStatus", "HTTPMethod") for a in node.names))
                    if not (is_safe_urllib or is_safe_http):
                        if self.policy.block_sockets:
                            self.findings.append(
                                RuleFinding(
                                    rule_id="SEC_AST_NETWORK_IMPORT",
                                    severity=SecuritySeverity.BLOCK,
                                    message=f"Direct import from network module '{node.module}' is prohibited in test sandbox.",
                                    line_number=getattr(node, "lineno", None),
                                    column_number=getattr(node, "col_offset", None),
                                    node_type="ImportFrom",
                                )
                            )
        self.generic_visit(node)
