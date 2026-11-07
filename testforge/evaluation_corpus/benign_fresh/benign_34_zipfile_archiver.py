import zipfile
from pathlib import Path
from typing import List

def create_text_zip(zip_destination: Path, file_paths: List[Path]) -> None:
    with zipfile.ZipFile(zip_destination, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for fp in file_paths:
            if fp.is_file():
                zf.write(fp, arcname=fp.name)
