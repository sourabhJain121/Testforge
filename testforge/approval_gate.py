"""
testforge/approval_gate.py

Human Approval Gate for Repository Writes, File Modifications, and GitHub PR Creation
(Handout Feature F4 & Sub-Task 3.3).

Provides a human-in-the-loop security barrier:
Before TestForge writes hardened test suites back to the repository disk or submits
a GitHub Pull Request, an ApprovalRequest is created in PENDING state.
Execution is halted until a human reviewer explicitly approves the action via API / UI.
"""

from __future__ import annotations

import logging
import os
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger("testforge.approval_gate")


@dataclass
class ApprovalRequest:
    request_id: str
    job_id: str
    action_type: str  # "REPO_WRITE", "GITHUB_PR_CREATE", "OVERWRITE_TARGET"
    target_path: str
    proposed_content: str
    diff_preview: str
    status: str  # "PENDING", "APPROVED", "REJECTED"
    created_at: float
    resolved_at: Optional[float] = None
    reviewer: Optional[str] = None
    reviewer_comments: Optional[str] = None


class ApprovalGateManager:
    """
    Manages pending human approval requests for file mutations and PR deployments.
    Guarantees no file writes or external PR dispatches occur without explicit human sign-off.
    """

    _instance: Optional[ApprovalGateManager] = None

    def __init__(self):
        self._requests: Dict[str, ApprovalRequest] = {}

    @classmethod
    def get_instance(cls) -> ApprovalGateManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def create_request(
        self,
        job_id: str,
        action_type: str,
        target_path: str,
        proposed_content: str,
        diff_preview: str = "",
    ) -> ApprovalRequest:
        req_id = f"appr_{uuid.uuid4().hex[:10]}"
        req = ApprovalRequest(
            request_id=req_id,
            job_id=job_id,
            action_type=action_type,
            target_path=target_path,
            proposed_content=proposed_content,
            diff_preview=diff_preview or f"Writing {len(proposed_content)} bytes to {target_path}",
            status="PENDING",
            created_at=time.time(),
        )
        self._requests[req_id] = req
        logger.info(f"Created Human Approval Request [{req_id}] for {action_type} on {target_path}")
        return req

    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        return self._requests.get(request_id)

    def list_requests(self, status: Optional[str] = None) -> List[ApprovalRequest]:
        if status:
            return [r for r in self._requests.values() if r.status == status]
        return list(self._requests.values())

    def approve_request(
        self,
        request_id: str,
        reviewer: str = "human_operator",
        comments: Optional[str] = None,
    ) -> ApprovalRequest:
        req = self._requests.get(request_id)
        if not req:
            raise KeyError(f"Approval request '{request_id}' not found.")
        if req.status != "PENDING":
            raise ValueError(f"Approval request '{request_id}' is already {req.status}.")

        req.status = "APPROVED"
        req.resolved_at = time.time()
        req.reviewer = reviewer
        req.reviewer_comments = comments or "Approved by operator."
        logger.info(f"Approval Request [{request_id}] APPROVED by {reviewer}.")
        return req

    def reject_request(
        self,
        request_id: str,
        reviewer: str = "human_operator",
        reason: Optional[str] = None,
    ) -> ApprovalRequest:
        req = self._requests.get(request_id)
        if not req:
            raise KeyError(f"Approval request '{request_id}' not found.")
        if req.status != "PENDING":
            raise ValueError(f"Approval request '{request_id}' is already {req.status}.")

        req.status = "REJECTED"
        req.resolved_at = time.time()
        req.reviewer = reviewer
        req.reviewer_comments = reason or "Rejected by operator."
        logger.warning(f"Approval Request [{request_id}] REJECTED by {reviewer}: {req.reviewer_comments}")
        return req

    def execute_approved_write(self, request_id: str) -> Dict[str, Any]:
        """
        Executes file write ONLY if the request status is APPROVED.
        Raises PermissionError if still PENDING or REJECTED.
        """
        req = self._requests.get(request_id)
        if not req:
            raise KeyError(f"Approval request '{request_id}' not found.")
        if req.status != "APPROVED":
            raise PermissionError(
                f"Security Guard: Operation blocked. Approval request '{request_id}' status is '{req.status}'. "
                "Human approval is required before modifying repository files."
            )

        # Proceed with file write
        abs_target = os.path.abspath(req.target_path)
        os.makedirs(os.path.dirname(abs_target), exist_ok=True)
        with open(abs_target, "w", encoding="utf-8") as f:
            f.write(req.proposed_content)

        logger.info(f"Successfully executed approved write to {abs_target} ({len(req.proposed_content)} bytes).")
        return {
            "request_id": req.request_id,
            "target_path": abs_target,
            "bytes_written": len(req.proposed_content),
            "status": "COMPLETED",
            "executed_at": time.time(),
        }

    def clear(self) -> None:
        """Clears in-memory requests (for testing isolation)."""
        self._requests.clear()

