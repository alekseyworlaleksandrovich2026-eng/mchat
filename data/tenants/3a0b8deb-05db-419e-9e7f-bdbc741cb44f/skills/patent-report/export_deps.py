"""Warm optional export dependencies for patent-report."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


def _run_pip_install(package: str) -> bool:
    import shutil

    cmds: list[list[str]] = []
    uv = shutil.which("uv")
    if uv:
        cmds.append([uv, "pip", "install", package, "-q"])
    cmds.append([sys.executable, "-m", "pip", "install", package, "-q"])
    for cmd in cmds:
        try:
            proc = subprocess.run(cmd, timeout=180, capture_output=True, text=True)
            if proc.returncode == 0:
                importlib.invalidate_caches()
                return True
        except (OSError, subprocess.TimeoutExpired):
            pass
    return False


def _ensure(package: str, import_name: str) -> None:
    try:
        __import__(import_name)
        return
    except ImportError:
        pass
    if _run_pip_install(package):
        __import__(import_name)


def warm_export_dependencies() -> None:
    _ensure("matplotlib", "matplotlib")
    _ensure("openpyxl", "openpyxl")
    _ensure("python-docx", "docx")
    _ensure("python-pptx", "pptx")
