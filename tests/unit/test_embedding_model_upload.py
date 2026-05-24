import zipfile
from pathlib import Path

import pytest

from app.services.embedding_model_service import (
    _resolve_model_root,
    _validate_model_dir,
)


def test_validate_model_dir_requires_marker(tmp_path):
    (tmp_path / "readme.txt").write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="未识别"):
        _validate_model_dir(tmp_path)

    (tmp_path / "config.json").write_text("{}", encoding="utf-8")
    _validate_model_dir(tmp_path)


def test_resolve_model_root_single_folder(tmp_path):
    inner = tmp_path / "my-model"
    inner.mkdir()
    (inner / "config.json").write_text("{}", encoding="utf-8")
    assert _resolve_model_root(tmp_path) == inner


def test_safe_zip_layout(tmp_path):
    zpath = tmp_path / "m.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        zf.writestr("model/config.json", "{}")
    extract = tmp_path / "out"
    extract.mkdir()
    from app.services.embedding_model_service import _safe_extract_zip

    _safe_extract_zip(zpath, extract)
    assert (extract / "model" / "config.json").is_file()
