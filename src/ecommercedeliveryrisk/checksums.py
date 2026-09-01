import hashlib
from pathlib import Path

def calculate_local_sha256(file_path: Path) -> str:
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(1024*1024), b""):
            sha256_hash.update(chunk)

    return sha256_hash.hexdigest()
