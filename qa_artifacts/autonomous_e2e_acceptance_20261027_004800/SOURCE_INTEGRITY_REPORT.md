# TestForge — Source Integrity Report

**Audit Session:** `autonomous_e2e_acceptance_20261027_004800`  
**Date:** 2026-10-27 01:14:00 IST  
**Environment:** macOS Apple Silicon (arm64), Python 3.13  

---

## 1. Objective and Scope

This audit verifies that:
1. Target source files submitted for autonomous test hardening are validated for cryptographic integrity (SHA-256) and AST syntax prior to ingestion.
2. No modification, mutation, or corruption occurs to the original source repository files.
3. All mutation injection, execution, and test evaluation take place strictly in ephemeral, isolated sandboxes (`/var/folders/.../T/testforge_box_*`).
4. Ephemeral artifacts and temporary sandboxes are cleanly torn down upon pipeline termination.

---

## 2. Ingested Target Hash Verification

| File Path | Recorded Baseline SHA-256 | Ingested Job Hash | Pre-Execution AST Syntax | Post-Run Working Tree Status | Integrity Outcome |
|---|---|---|---|---|:---:|
| `samples/discount.py` | `48cef70bdefd0000649e0ebaa5f277086a87aec15e1b61d70aec9eb1bb4fcb7c` | Matching | VALID AST | Unmodified (`git diff` clean) | **PASSED** |
| `samples/banking.py` | `3c205c05e69affb4a301d8c60f5d237a9b5faced5ac430b5d2d5fb02b5eba75a` | Matching | VALID AST | Unmodified (`git diff` clean) | **PASSED** |
| `samples/inventory_pricing.py` | `e6360fcbc75a8a3cc5b3451583ce24b7b041952b1db7369a1b958fcba90b7499` | Matching | VALID AST | Unmodified (`git diff` clean) | **PASSED** |
| `samples/state_machine.py` | `d30d78b108641e95ecf1fe077746c4289d5cd0c2ddde86f113019ea0198966d4` | Matching | VALID AST | Unmodified (`git diff` clean) | **PASSED** |
| `samples/rate_limiter.py` | `8577855aaaee2b552462b17fa3dc4ebfa9f8d33c5eefd2743ef6e8a54c70253f` | Matching | VALID AST | Unmodified (`git diff` clean) | **PASSED** |

---

## 3. Sandbox Isolation & Mutator Safety

1. **Subprocess Sandboxing:** During each mutation run, `testforge/sandbox.py` creates a temporary directory via `tempfile.TemporaryDirectory()`. The target code and candidate test suite are copied into this sandboxed box.
2. **Deterministic Mutation:** The mutator operates exclusively on the AST in-memory representation (`ast.NodeTransformer`). Mutated source code is emitted only into the isolated sandbox root.
3. **AST Pre-Execution Validation:** In `testforge/security.py`, `SecurityGuardrail.validate_code()` parses the code using `ast.parse()` and traverses all nodes to ensure no prohibited calls (`os.system`, `subprocess`, `eval`, `exec`, arbitrary file operations outside the permitted root) are present.
4. **Clean Reference Guarantee (pass@1):** In Pass 0, the candidate test suite is executed against the unmutated clean reference target. If any test fails against the clean reference (false positive), the test is quarantined immediately, preventing false mutant kills.

---

## 4. Working Tree Non-Destruction Audit

A `git status --porcelain` check confirms that zero tracked target source files in `samples/` have been altered, staged, or touched by the hardening pipeline runs.
