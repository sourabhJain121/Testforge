"""
run_demo.py - TestForge End-to-End Multi-Target Benchmark Suite.

Course: CSE3101 - Agentic AI
Authors: Sourabh & Shreshth
"""

import os
import sys
import argparse
from testforge.orchestrator import TestForgeOrchestrator
from testforge.logger import TraceLogger

AVAILABLE_TARGETS = {
    "banking": ("samples/banking.py", "Banking Transaction Boundary Rules"),
    "discount": ("samples/discount.py", "Volume & VIP Tiered Discount Rules"),
    "inventory": ("samples/inventory_pricing.py", "Tiered Inventory & Bulk Pricing Engine"),
    "ratelimit": ("samples/rate_limiter.py", "Token Bucket Rate Limiter with Decay"),
    "statemachine": ("samples/state_machine.py", "Order Finite State Machine with RBAC")
}

def main():
    parser = argparse.ArgumentParser(description="TestForge Multi-Target Benchmark Runner")
    parser.add_argument(
        "--target", "-t",
        choices=list(AVAILABLE_TARGETS.keys()),
        default="banking",
        help="Select target benchmark program"
    )
    parser.add_argument("--max-iter", "-i", type=int, default=3, help="Max reflection iterations")
    parser.add_argument("--target-score", "-score", type=float, default=85.0, help="Target mutation score")
    parser.add_argument("--model", "-m", default="gemini-3.6-flash", help="Foundation model name")
    parser.add_argument("--engine-mode", "-e", choices=["auto", "cloud", "openrouter", "local"], default="auto", help="Engine execution mode")
    args = parser.parse_args()

    rel_path, desc = AVAILABLE_TARGETS[args.target]
    full_path = os.path.join(os.path.dirname(__file__), rel_path)

    print("==========================================================")
    print(f"  BENCHMARK TARGET: {args.target.upper()} - {desc}")
    print(f"  Source Path: {rel_path}")
    print(f"  Engine Mode: {args.engine_mode}")
    print("==========================================================\n")

    with open(full_path, "r", encoding="utf-8") as f:
        code = f.read()

    orchestrator = TestForgeOrchestrator(
        target_source_code=code,
        initial_test_code=None,  # Generates initial tests autonomously
        max_iterations=args.max_iter,
        target_mutation_score=args.target_score,
        model_name=args.model,
        target_file_path=full_path,
        engine_mode=args.engine_mode
    )

    final_state = orchestrator.run()

    print("\n==========================================================")
    print("                    FINAL BENCHMARK AUDIT                 ")
    print("==========================================================")
    for m in final_state.history:
        print(f"Iteration {m.iteration}: Total: {m.total_mutants} | Killed: {m.killed_mutants} | Survived: {m.survived_mutants} | Score: {m.mutation_score}% | Duration: {m.duration_seconds}s")

    print(f"\nFinal Test Hardening Status: {'ACHIEVED' if final_state.terminated else 'IN_PROGRESS'}")
    print(f"Reason: {final_state.termination_reason}")
    print("Trace log saved to: testforge_trace.jsonl")

    logger = TraceLogger()
    traces = logger.read_traces()
    inference_events = [t for t in traces if t.get("event_type") == "LLM_INFERENCE_TELEMETRY"]
    print(f"Telemetry Audit: Recorded {len(traces)} total events ({len(inference_events)} LLM calls with real token/latency logs).")

if __name__ == "__main__":
    main()
