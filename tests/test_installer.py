"""Installer replaces Tuya Local only on request and keeps the old copy outside custom_components."""
import io
import json
import sys
import tarfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import install_tuya_local as installer  # noqa: E402


def archive(with_profile=True):
    buffer = io.BytesIO()
    files = {"tuya-local-x/custom_components/tuya_local/manifest.json": json.dumps({"domain": "tuya_local", "version": "9"})}
    if with_profile:
        files[f"tuya-local-x/custom_components/tuya_local/devices/{installer.PROFILE_NAME}"] = "name: test\n"
    with tarfile.open(fileobj=buffer, mode="w:gz") as bundle:
        for name, text in files.items():
            data = text.encode()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            bundle.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def test_fresh_install(tmp_path):
    profile = installer.install(tmp_path, archive=archive())
    assert profile.is_file()


def test_existing_install_requires_replace_then_backs_up(tmp_path):
    old = tmp_path / "custom_components" / "tuya_local"
    old.mkdir(parents=True)
    (old / "marker").write_text("old")
    with pytest.raises(RuntimeError, match="--replace"):
        installer.install(tmp_path, archive=archive())
    assert (old / "marker").exists()
    installer.install(tmp_path, replace=True, archive=archive())
    assert not (old / "marker").exists()
    backups = list((tmp_path / "tuya_local-backups").iterdir())
    assert len(backups) == 1 and (backups[0] / "marker").read_text() == "old"
    assert [p.name for p in (tmp_path / "custom_components").iterdir()] == ["tuya_local"]


def test_archive_without_profile_changes_nothing(tmp_path):
    with pytest.raises(RuntimeError, match="Lectron profile"):
        installer.install(tmp_path, archive=archive(with_profile=False))
    assert not (tmp_path / "custom_components" / "tuya_local").exists()


def test_checksum_mismatch_installs_nothing(tmp_path, monkeypatch):
    class Response(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(installer, "urlopen", lambda *a, **k: Response(b"tampered"))
    with pytest.raises(RuntimeError, match="checksum"):
        installer.install(tmp_path)
    assert not (tmp_path / "custom_components").exists()
