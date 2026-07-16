import json
from pathlib import Path


def load_json(file_path: Path):
    """
    Load a JSON file and return a Python dictionary.
    """

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_text(file_path: Path, text: str):
    """
    Save cleaned transcript as a text file.
    """

    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)

def load_text(file_path: Path):
    """
    Load a text file.
    """

    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()