import tempfile
from pathlib import Path

def write_temporary_scratch_data(content: str) -> str:
    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.txt') as tf:
        tf.write(content)
        return tf.name
