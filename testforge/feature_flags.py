"""
testforge/feature_flags.py

Formal Feature Flags and Capability Toggles for TestForge (Handout Criterion 1.1).
Enables modular ablation, isolated benchmarking, and behavioral verification across:
  1. ref_exec        : Clean reference execution consensus & differential oracle filtering
  2. reflection      : Multi-iteration iterative reflection & defect repair loop
  3. self_consistency: Multi-candidate generation sampling with consensus assertion extraction
  4. tot             : Tree-of-Thought multi-branch hypothesis exploration for resilient mutants
  5. react           : ReAct Thought-Action-Observation interactive tool deliberation loop
  6. rag             : Retrieval-Augmented Generation from AST patterns and knowledge base
  7. memory          : Cross-job mutant memory reuse and persistent SQLite/LanceDB recall
  8. critic          : CrewAI multi-agent adversarial critic review and directive generation
  9. equivalence     : Bytecode disassembly & heuristic equivalent mutant detection/suppression
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class FeatureFlags(BaseModel):
    """
    Typed, validated configuration of all 9 modular TestForge capabilities.
    Each flag controls an independent stage or reasoning strategy in the hardening pipeline.
    """
    ref_exec: bool = Field(
        default=True,
        description="Reference execution: run candidates against clean target to verify oracle validity."
    )
    reflection: bool = Field(
        default=True,
        description="Reflection loop: iterative repair of surviving mutants and coverage gaps."
    )
    self_consistency: bool = Field(
        default=True,
        description="Self-consistency: sample multiple test candidates and extract consensus assertions."
    )
    tot: bool = Field(
        default=True,
        description="Tree of Thoughts: branch into multiple hypotheses (boundary, invariant, control flow) during repair."
    )
    react: bool = Field(
        default=True,
        description="ReAct reasoning: interactive Thought -> Action -> Observation deliberation loop."
    )
    rag: bool = Field(
        default=True,
        description="Agentic RAG: retrieve relevant AST patterns, prior test fixtures, and mutant profiles."
    )
    memory: bool = Field(
        default=True,
        description="Cross-job memory: persist and recall killed mutant patterns across sessions."
    )
    critic: bool = Field(
        default=True,
        description="Adversarial Critic: multi-agent review of test quality, mutation score, and directives."
    )
    equivalence: bool = Field(
        default=True,
        description="Equivalence analysis: detect and suppress unkillable/equivalent mutants in adjusted score."
    )

    @classmethod
    def all_enabled(cls) -> "FeatureFlags":
        """Default production configuration with all 9 capabilities active."""
        return cls()

    @classmethod
    def zero_shot(cls) -> "FeatureFlags":
        """Pure single-pass zero-shot baseline: all 9 advanced capabilities disabled."""
        return cls(
            ref_exec=False,
            reflection=False,
            self_consistency=False,
            tot=False,
            react=False,
            rag=False,
            memory=False,
            critic=False,
            equivalence=False,
        )

    @classmethod
    def from_env(cls) -> "FeatureFlags":
        """
        Derives feature flags from environment variables (e.g. `TESTFORGE_FLAG_REFLECTION=0`).
        Supports '0', 'false', 'no', 'off' (case-insensitive) for disabling.
        """
        def _parse_env_bool(var_name: str, default: bool) -> bool:
            val = os.environ.get(var_name)
            if val is None:
                return default
            return val.strip().lower() not in ("0", "false", "no", "off")

        return cls(
            ref_exec=_parse_env_bool("TESTFORGE_FLAG_REF_EXEC", True),
            reflection=_parse_env_bool("TESTFORGE_FLAG_REFLECTION", True),
            self_consistency=_parse_env_bool("TESTFORGE_FLAG_SELF_CONSISTENCY", True),
            tot=_parse_env_bool("TESTFORGE_FLAG_TOT", True),
            react=_parse_env_bool("TESTFORGE_FLAG_REACT", True),
            rag=_parse_env_bool("TESTFORGE_FLAG_RAG", True),
            memory=_parse_env_bool("TESTFORGE_FLAG_MEMORY", True),
            critic=_parse_env_bool("TESTFORGE_FLAG_CRITIC", True),
            equivalence=_parse_env_bool("TESTFORGE_FLAG_EQUIVALENCE", True),
        )

    def to_ablation_dict(self) -> Dict[str, bool]:
        """Returns standard dictionary representation of flags for ablation telemetry."""
        return {
            "ref_exec": self.ref_exec,
            "reflection": self.reflection,
            "self_consistency": self.self_consistency,
            "tot": self.tot,
            "react": self.react,
            "rag": self.rag,
            "memory": self.memory,
            "critic": self.critic,
            "equivalence": self.equivalence,
        }

    def clone_with(self, **kwargs: bool) -> "FeatureFlags":
        """Creates a copy with specific flags overridden."""
        data = self.model_dump()
        data.update(kwargs)
        return FeatureFlags.model_validate(data)
