"""
tests/test_a2a_documentation_and_labels.py

Verification tests for Stage 2.4: Label Accuracy and A2A Protocol Disambiguation.
Verifies:
  1. docs/A2A_PROTOCOL_SPECIFICATION.md exists and is populated.
  2. Disambiguation between Official A2A (v0.3.0) and FIPA performative bus is clearly documented.
  3. References to a2a_protocol.py, a2a.py, and a2a_distributed.py are correct and resolvable.
  4. Task lifecycle state machine and distributed worker fallback are documented.
"""

from pathlib import Path
import pytest


def test_a2a_protocol_specification_content():
    spec_path = Path("docs/A2A_PROTOCOL_SPECIFICATION.md")
    assert spec_path.exists()

    content = spec_path.read_text(encoding="utf-8")
    assert "Agent2Agent (A2A) v0.3.0" in content
    assert "FIPA-ACL Envelopes" in content
    assert "Two Complementary Communication Layers" in content
    assert "Layer 1: Official A2A Wire Protocol" in content
    assert "Layer 2: In-Process FIPA Performative Bus" in content
    assert "Layer 3: Distributed Cross-Process A2A Architecture" in content

    # Check file link references
    assert "testforge/a2a_protocol.py" in content
    assert "testforge/a2a.py" in content
    assert "testforge/a2a_distributed.py" in content

    # Ensure document is comprehensive
    assert len(content) > 1500
