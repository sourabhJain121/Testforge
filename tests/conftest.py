import os
import sys
import tempfile
import pytest

# Ensure repository root is on sys.path for test discovery
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Global test temp directory for knowledge base / vector store
_TEST_KB_DIR = None


def pytest_configure(config):
    """
    Early configuration hook running before test imports and collections.
    Isolates RAG vector store and persistent caches to a scratch directory.
    """
    global _TEST_KB_DIR
    if "TESTFORGE_KB_DIR" not in os.environ:
        _TEST_KB_DIR = tempfile.mkdtemp(prefix="testforge_test_kb_")
        os.environ["TESTFORGE_KB_DIR"] = _TEST_KB_DIR


@pytest.fixture(scope="session", autouse=True)
def isolate_test_environment(tmp_path_factory):
    """
    Session-scoped autouse fixture that isolates disk side effects
    such as RAG vector store and temporary artifacts away from tracked repo paths.
    """
    kb_dir = tmp_path_factory.mktemp("kb_artifacts")
    os.environ["TESTFORGE_KB_DIR"] = str(kb_dir)

    yield
