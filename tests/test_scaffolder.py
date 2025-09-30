# tests/test_scaffolder.py
import tempfile
from pathlib import Path
from labcraft.scaffolder import init_project

def test_init_creates_dirs(tmp_path):
    ok = init_project(tmp_path / "mylab")
    assert ok is True
    base = tmp_path / "mylab"
    assert (base / "notes").exists()
    assert (base / "scripts").exists()
    assert (base / "labcraft.json").exists()
