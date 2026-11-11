#!/usr/bin/env python3
"""Install the pinned Tuya Local fork snapshot that includes the Lectron profile."""

import argparse
import hashlib
import io
import json
from pathlib import Path
import shutil
import tarfile
import tempfile
from datetime import UTC, datetime
from urllib.request import Request, urlopen

FORK = "dbriscoe511/tuya-local"
FORK_TAG = "lectron-vbox-pro-2026.11.11"
FORK_URL = f"https://github.com/{FORK}/archive/refs/tags/{FORK_TAG}.tar.gz"
FORK_SHA256 = "0c3be4892b216ab59c3b0f37a47ffffafb57e45ebcc218566b9b8ff8d07144e9"
PROFILE_NAME = "lectron_vboxpro_evcharger.yaml"


def download() -> bytes:
    request = Request(FORK_URL, headers={"User-Agent": "lectron-tuya-local-installer"})
    with urlopen(request, timeout=60) as response:
        archive = response.read()
    if hashlib.sha256(archive).hexdigest() != FORK_SHA256:
        raise RuntimeError("Archive checksum mismatch; nothing was installed.")
    return archive


def install(config_dir: Path, replace: bool = False, archive: bytes | None = None) -> Path:
    config_dir = config_dir.resolve(strict=True)
    integration = config_dir / "custom_components" / "tuya_local"
    if integration.exists() and not replace:
        raise RuntimeError(
            "Tuya Local is already installed. Rerun with --replace to back it up "
            "and install the fork snapshot."
        )
    archive = download() if archive is None else archive
    with tempfile.TemporaryDirectory() as temp:
        folder = Path(temp)
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as bundle:
            bundle.extractall(folder, filter="data")
        candidates = list(folder.glob("*/custom_components/tuya_local"))
        if len(candidates) != 1:
            raise RuntimeError("Unexpected archive layout; nothing was installed.")
        source = candidates[0]
        manifest = json.loads((source / "manifest.json").read_text())
        if manifest.get("domain") != "tuya_local":
            raise RuntimeError("Unexpected integration domain; nothing was installed.")
        if not (source / "devices" / PROFILE_NAME).is_file():
            raise RuntimeError("Archive lacks the Lectron profile; nothing was installed.")
        integration.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".lectron-install-", dir=integration.parent) as stage:
            staged = Path(stage) / "tuya_local"
            shutil.copytree(source, staged)
            if integration.exists():
                # Outside custom_components so HA never loads the backup.
                stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
                backup = config_dir / "tuya_local-backups" / stamp
                backup.parent.mkdir(exist_ok=True)
                integration.rename(backup)
                print(f"Previous Tuya Local moved to {backup}")
            staged.rename(integration)
    print(f"Installed Tuya Local {manifest.get('version', 'unknown')} from {FORK}@{FORK_TAG}")
    return integration / "devices" / PROFILE_NAME


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-dir", type=Path, required=True)
    parser.add_argument("--replace", action="store_true", help="back up and replace an existing Tuya Local")
    args = parser.parse_args()
    print(install(args.config_dir, args.replace))
    print("Restart Home Assistant, then add the charger through Tuya Local.")
