import os
import shutil
import tempfile

TEMP_DIR = "temp"


def ensure_temp_dir() -> None:
    os.makedirs(TEMP_DIR, exist_ok=True)


def cleanup_temp_dir() -> None:
    shutil.rmtree(TEMP_DIR, ignore_errors=True)


def save_upload(contents: bytes, suffix: str) -> str:
    tmp = tempfile.NamedTemporaryFile(dir=TEMP_DIR, suffix=suffix, delete=False)
    tmp.write(contents)
    tmp.close()
    return tmp.name


def remove_file(path: str) -> None:
    if os.path.exists(path):
        os.remove(path)