"""
adk_agents/testforge_repair/agent.py

Native Google ADK agent definition for TestForge Reflection Repair.
Compatible with `adk web adk_agents` and `adk run testforge_repair`.
"""

from google.adk.agents.llm_agent import LlmAgent

root_agent = LlmAgent(
    name="testforge_repair",
    description="Iteratively patches surviving AST mutants based on adversarial critic directives.",
    instruction=(
        "You are TestForge Reflection Repair Agent. Your role is to examine surviving mutant diffs "
        "and critic directives to synthesize targeted assertion patches that kill stubborn survivors."
    ),
)

