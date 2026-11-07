"""
testforge/scripts/run_critic_service.py

Stage 2.3: Standalone Out-of-Process A2A Mutation Critic Service.
Runs MutationQualityCriticAgent in a separate OS process, exposing an HTTP / JSON-RPC endpoint.
Includes PID in startup log and heartbeat response for cross-process provenance verification.
"""

import argparse
import json
import logging
import os
import sys
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

sys.path.insert(0, os.path.abspath("."))

from testforge.crew_critic import MutationQualityCriticAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [PID:%(process)d] %(message)s")
logger = logging.getLogger("testforge.a2a_critic_worker")

app = FastAPI(title="TestForge Standalone A2A Critic Service")
critic = MutationQualityCriticAgent(use_live_llm=False)


@app.get("/healthz")
def healthz():
    return {
        "status": "HEALTHY",
        "service": "testforge-a2a-critic-worker",
        "pid": os.getpid(),
    }


@app.post("/a2a/critic/diagnose")
async def diagnose(request: Request):
    payload = await request.json()
    logger.info("Received cross-process A2A critique request from PID: %s", payload.get("caller_pid", "unknown"))

    mutants = payload.get("surviving_mutants", [])
    target_source = payload.get("target_source", "")
    existing_tests = payload.get("existing_tests", "")

    # Execute Critic analysis in this process
    surviving_diffs = [
        m.get("unified_diff", m.get("description", "")) if isinstance(m, dict) else getattr(m, "unified_diff", str(m))
        for m in mutants
    ]
    directive = critic.diagnose_mutants(
        target_source_code=target_source,
        surviving_diffs=surviving_diffs,
        surviving_mutants=mutants,
        iteration=payload.get("iteration", 1)
    )

    return {
        "status": "SUCCESS",
        "critic_pid": os.getpid(),
        "directive": directive.model_dump() if hasattr(directive, "model_dump") else directive,
    }


def main():
    parser = argparse.ArgumentParser(description="TestForge Standalone A2A Critic Service")
    parser.add_argument("--port", type=int, default=8011, help="Port to bind")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind")
    args = parser.parse_args()

    logger.info("Starting standalone out-of-process A2A Critic Service on %s:%d with PID: %d",
                args.host, args.port, os.getpid())
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
