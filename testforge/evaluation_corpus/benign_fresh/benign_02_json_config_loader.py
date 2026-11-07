import json
from pathlib import Path
from typing import Dict, Any

def load_app_settings(config_path: Path) -> Dict[str, Any]:
    if not config_path.is_file():
        return {}
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)
