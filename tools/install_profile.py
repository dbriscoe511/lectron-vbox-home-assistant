#!/usr/bin/env python3
"""Install a profile; optionally bootstrap a pinned, unmodified Tuya Local release."""

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

import yaml

UPSTREAM_VERSION = "2026.10.0"
UPSTREAM_URL = (
    "https://api.github.com/repos/make-all/tuya-local/tarball/" + UPSTREAM_VERSION
)
UPSTREAM_SHA256 = "8f8318c24e06f404696dfd932d816b75e045c9d3174827d6b95d5aaea543ef19"
PROFILE_NAME = "lectron_vbox_pro.yaml"
ROOT = Path(__file__).resolve().parents[1]


def install(config_dir: Path, bootstrap: bool = False) -> Path:
    source = ROOT / "devices" / PROFILE_NAME
    profile = yaml.safe_load(source.read_text())
    if not isinstance(profile, dict) or not profile.get("entities"):
        raise RuntimeError("Local profile is missing or invalid; nothing was installed.")
    config_dir = config_dir.resolve(strict=True)
    integration = config_dir / "custom_components" / "tuya_local"
    if not integration.exists():
        if not bootstrap:
            raise RuntimeError("Install Tuya Local first, or explicitly use --bootstrap.")
        request = Request(UPSTREAM_URL, headers={"User-Agent": "lectron-profile-installer"})
        with urlopen(request, timeout=60) as response:
            archive = response.read()
        if hashlib.sha256(archive).hexdigest() != UPSTREAM_SHA256:
            raise RuntimeError("Upstream checksum mismatch; nothing was installed.")
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as bundle:
                bundle.extractall(folder, filter="data")
            candidates = list(folder.glob("*/custom_components/tuya_local"))
            if len(candidates) != 1:
                raise RuntimeError("Unexpected upstream archive layout.")
            manifest = json.loads((candidates[0] / "manifest.json").read_text())
            if manifest.get("domain") != "tuya_local":
                raise RuntimeError("Unexpected upstream integration domain.")
            integration.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix=".lectron-install-", dir=integration.parent) as stage:
                staged_integration = Path(stage) / "tuya_local"
                shutil.copytree(candidates[0], staged_integration)
                staged_integration.rename(integration)
    manifest = json.loads((integration / "manifest.json").read_text())
    if manifest.get("domain") != "tuya_local":
        raise RuntimeError("Unexpected integration domain; installation aborted.")
    destination = integration / "devices" / PROFILE_NAME
    if destination.exists() and destination.read_bytes() != source.read_bytes():
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        shutil.copy2(destination, destination.with_suffix(f".yaml.{stamp}.bak"))
    staged = destination.with_suffix(".yaml.new")
    shutil.copyfile(source, staged)
    staged.replace(destination)
    version = manifest.get("version", "unknown")
    print(f"Installed transport version: {version} (tested: {UPSTREAM_VERSION})")
    if version != UPSTREAM_VERSION:
        print("Existing transport was preserved; validate this profile against that version.")
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-dir", type=Path, required=True)
    parser.add_argument("--bootstrap", action="store_true")
    args = parser.parse_args()
    print(install(args.config_dir, args.bootstrap))
    print("Restart Home Assistant for a new integration, then add Tuya Local manually.")

