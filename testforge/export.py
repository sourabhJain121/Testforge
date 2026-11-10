"""
export.py - Enterprise CI/CD Report Exporters (JUnit XML & OASIS SARIF v2.1.0).

Authors: Sourabh & Shreshth
System: Autonomous Multi-Agent Hardening Engine
"""

import time
import xml.etree.ElementTree as ET
from typing import Any, Dict


def generate_junit_xml(job_id: str, job_record: Dict[str, Any]) -> str:
    """Generates standard JUnit XML test report for a completed or evaluated job."""
    duration = float(job_record.get("duration", 0.0) or 0.1)
    final_state = job_record.get("final_state") or {}
    baseline_run = final_state.get("baseline_run") or job_record.get("baseline_run") or {}
    test_results = final_state.get("test_results") or job_record.get("test_results") or []

    tests_count = baseline_run.get("tests_executed") or final_state.get("baseline_tests_executed") or len(test_results) or 1
    passed_count = baseline_run.get("tests_passed") or final_state.get("baseline_tests_passed") or 0
    failed_count = baseline_run.get("tests_failed") or final_state.get("baseline_tests_failed") or 0
    errors_count = 1 if final_state.get("baseline_execution_error") else 0

    root = ET.Element("testsuites", {
        "name": f"TestForge Hardening - {job_id}",
        "id": job_id,
        "time": f"{duration:.3f}",
    })

    # Unit Tests Suite
    unit_suite = ET.SubElement(root, "testsuite", {
        "name": "unit_tests",
        "tests": str(tests_count),
        "failures": str(failed_count),
        "errors": str(errors_count),
        "skipped": "0",
        "time": f"{duration:.3f}",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(job_record.get("start_time", time.time()))),
    })

    if test_results:
        for t in test_results:
            t_name = t.get("name") or t.get("test_id", "test_case")
            t_time = f"{float(t.get('duration', 0.01)):.3f}"
            tc = ET.SubElement(unit_suite, "testcase", {
                "classname": job_record.get("target_file_path", "test_target.py"),
                "name": t_name,
                "time": t_time,
            })
            if t.get("status") in ("FAILED", "FAIL"):
                fail = ET.SubElement(tc, "failure", {
                    "message": t.get("error_message", "Assertion failed"),
                    "type": "AssertionError",
                })
                fail.text = t.get("traceback", t.get("error_message", ""))
            elif t.get("status") in ("ERROR", "TIMEOUT"):
                err = ET.SubElement(tc, "error", {
                    "message": t.get("error_message", "Execution error"),
                    "type": "RuntimeError",
                })
                err.text = t.get("traceback", "")
    else:
        tc = ET.SubElement(unit_suite, "testcase", {
            "classname": job_record.get("target_file_path", "test_target.py"),
            "name": "baseline_validation_suite",
            "time": f"{duration:.3f}",
        })
        if failed_count > 0:
            fail = ET.SubElement(tc, "failure", {
                "message": f"{failed_count} baseline test(s) failed assertions.",
                "type": "AssertionError",
            })
            fail.text = final_state.get("baseline_execution_error", "Assertion failure during test execution")
        elif errors_count > 0:
            err = ET.SubElement(tc, "error", {
                "message": final_state.get("baseline_execution_error", "Execution error"),
                "type": "RuntimeError",
            })
            err.text = final_state.get("baseline_execution_error", "")

    # Mutation Evaluations Suite
    mutants = final_state.get("mutants") or job_record.get("mutants") or []
    if mutants:
        survived_mutants = [m for m in mutants if m.get("status") == "SURVIVED"]
        error_mutants = [m for m in mutants if m.get("status") == "ERROR"]

        mut_suite = ET.SubElement(root, "testsuite", {
            "name": "mutation_evaluations",
            "tests": str(len(mutants)),
            "failures": str(len(survived_mutants)),
            "errors": str(len(error_mutants)),
            "skipped": str(sum(1 for m in mutants if m.get("status") == "EQUIVALENT")),
            "time": f"{duration:.3f}",
        })

        for m in mutants:
            m_id = m.get("mutant_id", "MUT")
            m_type = m.get("mutation_type", "MUTATION")
            l_no = m.get("line_number", 0)
            tc = ET.SubElement(mut_suite, "testcase", {
                "classname": f"mutants.{m_type}",
                "name": f"{m_id}_line_{l_no}",
                "time": f"{float(m.get('execution_time_ms', 10.0)) / 1000.0:.3f}",
            })
            if m.get("status") == "SURVIVED":
                fail = ET.SubElement(tc, "failure", {
                    "message": f"Mutant {m_id} survived at line {l_no} without being detected.",
                    "type": "SurvivingMutant",
                })
                fail.text = m.get("diff", m.get("unified_diff", "Mutant survived."))
            elif m.get("status") == "ERROR":
                err = ET.SubElement(tc, "error", {
                    "message": f"Mutant {m_id} encountered execution or syntax error.",
                    "type": "MutantExecutionError",
                })
                err.text = m.get("stderr", "Subprocess execution error.")
            elif m.get("status") == "EQUIVALENT":
                ET.SubElement(tc, "skipped", {
                    "message": "Equivalent mutant confirmed by AST equivalence analyzer."
                })

    # Summary count reconciliation
    total_tests = sum(int(s.attrib.get("tests", 0)) for s in root.findall("testsuite"))
    total_fails = sum(int(s.attrib.get("failures", 0)) for s in root.findall("testsuite"))
    total_errs = sum(int(s.attrib.get("errors", 0)) for s in root.findall("testsuite"))
    root.attrib["tests"] = str(total_tests)
    root.attrib["failures"] = str(total_fails)
    root.attrib["errors"] = str(total_errs)

    return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")


def generate_sarif_report(job_id: str, job_record: Dict[str, Any]) -> Dict[str, Any]:
    """Generates an OASIS standard SARIF v2.1.0 JSON report mapping unkilled mutants and security alerts."""
    final_state = job_record.get("final_state") or {}
    target_file = job_record.get("target_file_path") or final_state.get("target_module_path") or "target.py"
    mutants = final_state.get("mutants") or job_record.get("mutants") or []

    results = []

    for m in mutants:
        if m.get("status") == "SURVIVED":
            m_id = m.get("mutant_id", "MUT")
            m_type = m.get("mutation_type", "MUTATION")
            l_no = int(m.get("line_number", 1))
            diff_text = m.get("diff", m.get("unified_diff", ""))
            results.append({
                "ruleId": "MUTATION_SURVIVED",
                "level": "warning",
                "message": {
                    "text": f"Mutant [{m_id}] ({m_type}) survived at line {l_no}. Candidate test suite lacks assertions to detect this code alteration."
                },
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": target_file
                            },
                            "region": {
                                "startLine": max(1, l_no),
                                "startColumn": 1
                            }
                        }
                    }
                ],
                "properties": {
                    "mutant_id": m_id,
                    "operator": m_type,
                    "diff": diff_text,
                    "equivalence_status": m.get("equivalence_status", "UNKNOWN")
                }
            })

    sec_space = final_state.get("security_space") or {}
    findings = sec_space.get("findings") or []
    for f in findings:
        results.append({
            "ruleId": "SECURITY_GUARDRAIL_ALERT",
            "level": "error",
            "message": {
                "text": f.get("description", "Security guardrail violation detected")
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": target_file
                        },
                        "region": {
                            "startLine": int(f.get("line_number", 1)),
                            "startColumn": 1
                        }
                    }
                }
            ],
            "properties": {
                "risk_level": f.get("risk_level", "HIGH"),
                "category": f.get("category", "SECURITY_ALERT")
            }
        })

    return {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "TestForge",
                        "version": "2.0.0",
                        "informationUri": "https://github.com/sourabh/TestForge",
                        "rules": [
                            {
                                "id": "MUTATION_SURVIVED",
                                "name": "SurvivingMutantWarning",
                                "shortDescription": {
                                    "text": "Mutant survived candidate test suite without being detected"
                                },
                                "fullDescription": {
                                    "text": "An artificial syntactic fault was injected into the target source code but survived test execution, indicating a deficiency in assertion strength or behavioral test coverage."
                                },
                                "defaultConfiguration": {
                                    "level": "warning"
                                }
                            },
                            {
                                "id": "SECURITY_GUARDRAIL_ALERT",
                                "name": "SecurityGuardrailViolation",
                                "shortDescription": {
                                    "text": "Prohibited or dangerous primitive detected by security guardrails"
                                },
                                "fullDescription": {
                                    "text": "Security guardrails identified a prohibited operation such as unauthorized network access, OS manipulation, or credential exposure."
                                },
                                "defaultConfiguration": {
                                    "level": "error"
                                }
                            }
                        ]
                    }
                },
                "artifacts": [
                    {
                        "location": {
                            "uri": target_file
                        }
                    }
                ],
                "results": results
            }
        ]
    }

