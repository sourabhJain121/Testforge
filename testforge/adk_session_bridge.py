"""
testforge/adk_session_bridge.py

Blackboard-to-ADK Session State Bridge for TestForge (Handout Feature F4).
Bridges Blackboard multi-partition states into Google ADK's SessionService / Session.state
using standardized scoped prefixes:
  - 'app:'  -> Global application / target space invariants (target path, source SHA, scores)
  - 'user:' -> User configuration limits (iteration caps, target mutation score threshold)
  - 'temp:' -> Ephemeral critique directives and working test generation artifacts
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.sessions.session import Session

from testforge.blackboard import Blackboard

logger = logging.getLogger("testforge.adk_session_bridge")


class ADKBlackboardSessionBridge:
    """
    Bidirectional bridge synchronizing Blackboard partition spaces with
    Google ADK's InMemorySessionService using scoped prefixes ('app:', 'user:', 'temp:').
    """
    __test__ = False

    def __init__(
        self,
        blackboard: Optional[Blackboard] = None,
        session_service: Optional[InMemorySessionService] = None,
        app_name: str = "testforge",
        user_id: str = "default_user",
    ):
        self.blackboard = blackboard or Blackboard()
        self.session_service = session_service or InMemorySessionService()
        self.app_name = app_name
        self.user_id = user_id

    def get_or_create_session(self, session_id: str = "default_session") -> Session:
        """Retrieves an existing ADK session or initializes a new one in the session service."""
        try:
            session = self.session_service.get_session_sync(
                app_name=self.app_name,
                user_id=self.user_id,
                session_id=session_id,
            )
            if session is not None:
                return session
        except Exception:
            pass

        return self.session_service.create_session_sync(
            app_name=self.app_name,
            user_id=self.user_id,
            session_id=session_id,
        )

    def _get_internal_session(self, session_id: str = "default_session") -> Session:
        """Retrieves the underlying persistent Session instance from the session service."""
        self.get_or_create_session(session_id)
        if (
            hasattr(self.session_service, "sessions")
            and self.app_name in self.session_service.sessions
            and self.user_id in self.session_service.sessions[self.app_name]
            and session_id in self.session_service.sessions[self.app_name][self.user_id]
        ):
            return self.session_service.sessions[self.app_name][self.user_id][session_id]
        return self.get_or_create_session(session_id)

    def sync_blackboard_to_session(self, session_id: str = "default_session") -> Session:
        """
        Extracts partition states from Blackboard and synchronizes them into
        the ADK Session.state dictionary using scoped prefixes:
          - 'app:target_path'
          - 'app:sha256_hash'
          - 'app:mutation_score'
          - 'app:branch_coverage'
          - 'user:config_iterations'
          - 'user:target_score'
          - 'temp:latest_critique_directives'
        """
        internal_session = self._get_internal_session(session_id=session_id)

        target_space = self.blackboard.get_target_space()
        metrics_space = self.blackboard.get_metrics_space()
        critic_space = self.blackboard.get_critic_space()

        score = (
            getattr(metrics_space, "final_mutation_score", None)
            or getattr(metrics_space, "raw_mutation_score", None)
            or getattr(metrics_space, "adjusted_mutation_score", None)
            or getattr(critic_space, "mutation_score", None)
            or 0.0
        )

        # Scoped 'app:' mappings
        internal_session.state["app:target_path"] = target_space.target_file_path or target_space.target_module_path
        internal_session.state["app:sha256_hash"] = target_space.source_sha
        internal_session.state["app:mutation_score"] = float(score)
        internal_session.state["app:branch_coverage"] = float(metrics_space.branch_coverage or 0.0)

        # Scoped 'user:' mappings
        internal_session.state["user:config_iterations"] = int(metrics_space.max_iterations)
        internal_session.state["user:target_score"] = float(metrics_space.target_mutation_score)

        # Scoped 'temp:' mappings
        latest_dir = critic_space.latest_directive or (critic_space.critic_directives[-1] if critic_space.critic_directives else "")
        internal_session.state["temp:latest_critique_directives"] = latest_dir

        logger.info(
            f"ADKBlackboardSessionBridge: Synchronized Blackboard to session '{session_id}' "
            f"({len(internal_session.state)} scoped keys populated)."
        )
        return self.get_or_create_session(session_id=session_id)

    def sync_session_to_blackboard(self, session_id: str = "default_session") -> None:
        """
        Propagates updated scoped keys from ADK Session.state back into Blackboard partitions.
        """
        internal_session = self._get_internal_session(session_id=session_id)
        state = internal_session.state

        # Update MetricsSpace from scoped keys
        if "app:mutation_score" in state:
            score_val = float(state["app:mutation_score"])
            self.blackboard.update_metrics_space(
                final_mutation_score=score_val,
                raw_mutation_score=score_val,
            )

        if "app:branch_coverage" in state:
            self.blackboard.update_metrics_space(branch_coverage=float(state["app:branch_coverage"]))

        if "user:config_iterations" in state:
            self.blackboard.update_metrics_space(max_iterations=int(state["user:config_iterations"]))

        if "user:target_score" in state:
            self.blackboard.update_metrics_space(target_mutation_score=float(state["user:target_score"]))

        # Update CriticSpace from scoped keys
        if "temp:latest_critique_directives" in state and state["temp:latest_critique_directives"]:
            latest = str(state["temp:latest_critique_directives"])
            existing_dirs = self.blackboard.get_critic_space().critic_directives
            if latest not in existing_dirs:
                self.blackboard.update_critic_space(
                    latest_directive=latest,
                    critic_directives=existing_dirs + [latest],
                )

        logger.info(f"ADKBlackboardSessionBridge: Synchronized session '{session_id}' back to Blackboard.")

    def get_scoped(self, key: str, session_id: str = "default_session") -> Any:
        """Retrieves a scoped key ('app:*', 'user:*', 'temp:*') from the session."""
        internal_session = self._get_internal_session(session_id=session_id)
        return internal_session.state.get(key)

    def set_scoped(self, key: str, value: Any, session_id: str = "default_session") -> None:
        """Sets a scoped key in the ADK session state."""
        internal_session = self._get_internal_session(session_id=session_id)
        internal_session.state[key] = value
        logger.debug(f"ADKBlackboardSessionBridge: Set scoped key '{key}' in session '{session_id}'.")
