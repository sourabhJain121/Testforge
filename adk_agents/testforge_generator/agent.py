"""
adk_agents/testforge_generator/agent.py

Native Google ADK agent definition for TestForge Generator.
Compatible with `adk web adk_agents` and `adk run testforge_generator`.
"""

from google.adk.agents.llm_agent import LlmAgent

root_agent = LlmAgent(
    name="testforge_generator",
    description="Synthesizes mutation-verified pytest suites for Python modules.",
    instruction=(
        "You are TestForge Generator, an expert test engineer. "
        "Your task is to analyze Python source code and generate deterministic, "
        "high-coverage Pytest test functions that kill AST mutants and assert edge boundaries."
    ),
)

