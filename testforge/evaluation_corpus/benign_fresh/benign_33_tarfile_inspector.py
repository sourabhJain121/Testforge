import tarfile
from typing import List

def inspect_tar_contents(tar_path: str) -> List[str]:
    with tarfile.open(tar_path, 'r') as tar:
        return [member.name for member in tar.getmembers() if not member.isdir()]
