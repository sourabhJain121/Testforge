"""
adk_agents/testforge_planner/agent.py

Native Google ADK agent definition for TestForge Planner.
Compatible with `adk web adk_agents` and `adk run testforge_planner`.
"""

from google.adk.agents.llm_agent import LlmAgent

root_agent = LlmAgent(
    name="testforge_planner",
    description="Analyzes cyclomatic complexity, AST branching, and allocates test scenarios.",
    instruction=(
        "You are TestForge Planner. Your role is to inspect target code structure, "
        "measure branch complexity, and formulate a targeted test plan with boundary scenarios."
    ),
)

