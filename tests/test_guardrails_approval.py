"""
tests/test_guardrails_approval.py

Unit and API integration tests for Output Guardrails and Human Approval Gate (Sub-Task 3.3):
- Static AST inspection blocking forbidden network & process execution in generated tests.
- Human approval gate lifecycle (PENDING -> APPROVED/REJECTED -> EXECUTE).
- FastAPI endpoints for approval requests.
"""

import os
import pytest
from starlette.testclient import TestClient

from server import app
from testforge.approval_gate import ApprovalGateManager
from testforge.security import SecurityGuardrail


class TestOutputGuardrailsAST:
    """Verifies that generated test code containing dangerous network/process imports is blocked."""

    def test_blocks_network_module_imports(self):
        guardrail = SecurityGuardrail()

        # Network imports must be blocked
        network_samples = [
            "import socket\ndef test_leak(): s = socket.socket()",
            "import requests\ndef test_exfil(): requests.get('https://evil.corp')",
            "from urllib.request import urlopen\ndef test_net(): urlopen('http://1.2.3.4')",
            "import httpx\ndef test_net(): httpx.get('https://test.corp')",
            "import aiohttp\ndef test_net(): pass",
        ]

        for code in network_samples:
            res = guardrail.inspect_code_ast(code, enforce_policy=True)
            assert not res.allowed, f"Expected network code to be blocked: {code}"
            assert any(v.rule_id == "SEC_AST_NETWORK_IMPORT" for v in res.violations)

    def test_blocks_process_and_command_execution(self):
        guardrail = SecurityGuardrail()

        evil_samples = [
            "import os\ndef test_cmd(): os.system('rm -rf /')",
            "import subprocess\ndef test_proc(): subprocess.run(['ls', '-la'])",
            "import pty\ndef test_shell(): pty.spawn('/bin/sh')",
            "def test_eval(): eval('__import__(\"os\").system(\"whoami\")')",
        ]

        for code in evil_samples:
            res = guardrail.inspect_code_ast(code, enforce_policy=True)
            assert not res.allowed, f"Expected dangerous primitive to be blocked: {code}"

    def test_allows_benign_unit_tests(self):
        guardrail = SecurityGuardrail()

        benign_code = (
            "import pytest\n"
            "from target import calculate_discount\n\n"
            "def test_nominal():\n"
            "    assert calculate_discount(100.0, 1, False) == 100.0\n\n"
            "def test_boundary():\n"
            "    assert calculate_discount(0.0, 1, False) == 0.0\n"
        )
        res = guardrail.inspect_code_ast(benign_code, enforce_policy=True)
        assert res.allowed is True
        assert len(res.violations) == 0


class TestHumanApprovalGateCore:
    """Verifies human-in-the-loop approval gate logic and write confinement."""

    def setup_method(self):
        ApprovalGateManager.get_instance().clear()

    def test_approval_lifecycle_and_write_protection(self, tmp_path):
        mgr = ApprovalGateManager.get_instance()
        target_file = tmp_path / "hardened_output.py"
        content = "def test_example(): assert True\n"

        # 1. Create request (starts in PENDING)
        req = mgr.create_request(
            job_id="job_test_01",
            action_type="REPO_WRITE",
            target_path=str(target_file),
            proposed_content=content,
        )
        assert req.status == "PENDING"
        assert not os.path.exists(target_file)

        # 2. Attempt write while PENDING -> Must be BLOCKED
        with pytest.raises(PermissionError, match="Human approval is required"):
            mgr.execute_approved_write(req.request_id)
        assert not os.path.exists(target_file)

        # 3. Approve request
        approved_req = mgr.approve_request(req.request_id, reviewer="lead_qa", comments="Verified AST safety.")
        assert approved_req.status == "APPROVED"
        assert approved_req.reviewer == "lead_qa"

        # 4. Execute approved write -> Must succeed
        result = mgr.execute_approved_write(req.request_id)
        assert result["status"] == "COMPLETED"
        assert os.path.exists(target_file)
        assert target_file.read_text(encoding="utf-8") == content

    def test_rejection_blocks_execution(self, tmp_path):
        mgr = ApprovalGateManager.get_instance()
        target_file = tmp_path / "rejected_output.py"

        req = mgr.create_request(
            job_id="job_reject_01",
            action_type="REPO_WRITE",
            target_path=str(target_file),
            proposed_content="broken code",
        )

        mgr.reject_request(req.request_id, reviewer="sec_auditor", reason="Contains bad assertions.")
        assert req.status == "REJECTED"

        with pytest.raises(PermissionError, match="status is 'REJECTED'"):
            mgr.execute_approved_write(req.request_id)
        assert not os.path.exists(target_file)


class TestHumanApprovalGateAPI:
    """Tests FastAPI endpoints for listing, creating, approving, and rejecting requests."""

    def setup_method(self):
        ApprovalGateManager.get_instance().clear()

    def test_api_approval_flow(self, tmp_path):
        client = TestClient(app)
        target_path = str(tmp_path / "api_test_suite.py")

        # 1. Create approval request
        res = client.post("/api/approval/create", json={
            "job_id": "job_api_01",
            "action_type": "REPO_WRITE",
            "target_path": target_path,
            "proposed_content": "def test_api(): pass\n",
            "diff_preview": "Add test_api",
        })
        assert res.status_code == 200
        req_id = res.json()["request_id"]
        assert res.json()["status"] == "PENDING"

        # 2. List requests
        list_res = client.get("/api/approval/requests")
        assert list_res.status_code == 200
        assert any(r["request_id"] == req_id for r in list_res.json()["requests"])

        # 3. Try to execute without approval -> 403 Forbidden
        exec_fail = client.post(f"/api/approval/requests/{req_id}/execute")
        assert exec_fail.status_code == 403

        # 4. Approve request via API
        appr_res = client.post(f"/api/approval/requests/{req_id}/approve", json={
            "reviewer": "qa_lead_api",
            "comments": "Signed off via dashboard",
        })
        assert appr_res.status_code == 200
        assert appr_res.json()["status"] == "APPROVED"

        # 5. Execute approved request
        exec_ok = client.post(f"/api/approval/requests/{req_id}/execute")
        assert exec_ok.status_code == 200
        assert exec_ok.json()["status"] == "COMPLETED"
        assert os.path.exists(target_path)
