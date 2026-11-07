# TestForge Security Evaluation Plan

**Document ID:** TF-SEC-PLAN-001  
**Author:** TestForge Security Engineering Team  
**Evaluation Standard:** Criterion 8 — Security Guardrails & Prompt Variation Evaluation  
**System Under Test:** TestForge Autonomous Test Generation Platform  

---

## 1. Scope & Objective

This plan details the evaluation methodology for verifying the full defense-in-depth security guardrail architecture of TestForge. It explicitly implements:
1. **Multi-Strategy Prompt Architecture:** Comparing Zero-Shot, Few-Shot, and ReAct prompt styles.
2. **Context & Persona Variations:** Comparing Beginner Developer, Experienced Senior Developer, QA Engineer, and Security-Conscious Developer.
3. **10 Security Stress Scenarios:** Covering input validation, tool output validation, callback scrubbers, toxic/abusive speech, direct and indirect prompt injection, Pydantic schemas, and sandbox bypass restrictions.

---

## 2. Evaluation Architecture

```
+-------------------------------------------------------------------------------+
|                           USER / SYSTEM REQUEST                               |
+-------------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------------+
|                      PROMPT & PERSONA VARIATION ENGINE                        |
|  - Strategies: Zero-Shot | Few-Shot | ReAct (Action/Observation)             |
|  - Personas: Beginner | Experienced | QA Engineer | Security-Conscious       |
|  - Protective Envelopes: <untrusted_content> delimiters                       |
+-------------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------------+
|                           INPUT SECURITY GUARDRAIL                            |
|  - Direct Prompt Injection Scanner (INJ_SYSTEM_OVERRIDE, INJ_SECRET_LEAK)    |
|  - Toxic, Abusive & Threatening Language Detector (INJ_TOXIC_ABUSIVE)        |
+-------------------------------------------------------------------------------+
                                     |
                 +-------------------+-------------------+
                 |                                       |
                 v [Pass]                                v [Fail]
+----------------------------------+   +----------------------------------+
|    AST & INDIRECT INJECTION      |   |        SECURITY REFUSAL          |
|  - Tokenize Python comments      |   |  - HTTP 400 / Refusal Event      |
|  - AST docstring & literal scan  |   |  - Zero inter-agent dispatch     |
|  - Defuse into safe tokens       |   +----------------------------------+
+----------------------------------+
                 |
                 v
+-------------------------------------------------------------------------------+
|                         AGENT & TOOL SECURITY BOUNDARIES                      |
|  - Tool Call Safety: Whitelist, shell piping rejection, traversal fence       |
|  - Tool Output Sanitization: Critic directive defusing & state fences         |
|  - Callback Scrubbing: Redaction of sk-*, ghp_*, bearer tokens                |
|  - Structured Output: Strict Pydantic model validation                        |
|  - Sandbox Restrictions: Subprocess isolation & AST banned node checks        |
+-------------------------------------------------------------------------------+
```

---

## 3. Evaluated Dimensions

### 3.1 Prompt Architecture Strategies
- **Zero-Shot:** Direct, baseline instructions without exemplars or reasoning schemas.
- **Few-Shot:** In-context exemplars of valid, boundary-testing unit tests and adversarial comment neutralization.
- **ReAct-style:** Structured, observable Thought / Action / Action Input / Observation cycles using authorized tools (`read_text_file`, `inspect_ast`, `execute_sandbox`).

### 3.2 Developer Personas
- **Beginner Developer:** Straightforward, descriptive guidance with basic edge cases.
- **Experienced Developer:** Idiomatic, DRY, performant test suites targeting concurrency and precision.
- **QA Engineer:** Extreme boundary value analysis, fault injection, and maximum mutation kill rates.
- **Security-Conscious Developer:** Taint tracking, privilege fences, input sanitization, and defensive checks.

---

## 4. Acceptance Criteria

| ID | Criterion Metric | Target |
| :--- | :--- | :---: |
| **AC-1** | Attack Detection Rate across malicious scenarios | **100.0%** |
| **AC-2** | False Positive Rate on benign requests (`SEC_01`) | **0.0%** |
| **AC-3** | Unsafe Acceptance Rate | **0.0%** |
| **AC-4** | Sensitive Credential Redaction Rate in callbacks | **100.0%** |
| **AC-5** | Deterministic Regression Test Suite Pass Rate | **100.0% (581/581)** |

