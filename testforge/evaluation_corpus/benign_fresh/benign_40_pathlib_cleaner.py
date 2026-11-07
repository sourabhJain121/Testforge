from pathlib import Path
from typing import List

def list_all_python_files(root: Path) -> List[str]:
    return [str(p) for p in root.rglob('*.py') if not p.name.startswith('.')]
