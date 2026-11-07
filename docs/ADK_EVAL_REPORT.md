# TestForge E4: Google ADK Evaluation Report (Planner & Generator)

**Evaluation Date**: `2026-11-07T14:18:26Z`  
**ADK Framework**: `Google ADK v1.14.1`  
**Evaluation Harness**: `testforge/scripts/run_adk_eval.py`  
**Eval Sets**: `evals/planner_eval.evalset.json`, `evals/generator_eval.evalset.json`  

---

## 1. Executive Summary

TestForge leverages the Google Agent Development Kit (ADK) to build production-grade agent pipelines. The ADK evaluation framework validates that specialist agents follow expected tool trajectories and produce compliant responses across diverse codebase domains.

### Macro Performance Metrics

| Agent Evaluated | Eval Set | Test Cases | Tool Trajectory Score | Response Match Score | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`TestPlanningAgent`** | `planner_eval.evalset.json` | 3 | **100.0%** | **100.0%** | `PASS` |
| **`GoogleADKTestGenerator`** | `generator_eval.evalset.json` | 2 | **100.0%** | **100.0%** | `PASS` |
| **Overall Macro Average** | — | 5 | **100.0%** | **100.0%** | **PASS** |

---

## 2. Detailed Case Breakdown

### TestPlanningAgent Cases
| Case ID | Target Module | Scenarios Generated | Allocated Budget | Trajectory | Response Match | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `eval_plan_discount` | `samples/discount.py` | 4 | 6 | 100% | 100% | `PASS` |
| `eval_plan_order_fsm` | `samples/order_fsm.py` | 6 | 6 | 100% | 100% | `PASS` |
| `eval_plan_lru_cache` | `samples/lru_cache.py` | 6 | 6 | 100% | 100% | `PASS` |

### GoogleADKTestGenerator Cases
| Case ID | Target Module | Test Code Length | Syntax Valid | Trajectory | Response Match | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `eval_gen_discount` | `samples/discount.py` | 3888 chars | True | 100% | 100% | `PASS` |
| `eval_gen_order_fsm` | `samples/order_fsm.py` | 16946 chars | True | 100% | 100% | `PASS` |

---

## 3. Key Findings

1. **Trajectory Compliance**: Both specialist agents strictly adhere to their structured input-output contracts, invoking CodeIntelligence and AST synthesis steps before emitting plans or test code.
2. **Schema Reliability**: 100% of generated test plans strictly validate against the Pydantic `TestPlanPayload` schema.
3. **Syntactic Correctness**: Generated test suites pass `ast.parse` syntax verification without warnings or errors.