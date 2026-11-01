"""Test against the actual maintained Tuya Local parser, not a reimplementation."""
import os
from pathlib import Path
import sys

source = os.environ.get("TUYA_LOCAL_SOURCE")
if not source:
    raise RuntimeError("Set TUYA_LOCAL_SOURCE to the Tuya Local checkout/config directory.")
if not (Path(source) / "custom_components" / "tuya_local").is_dir():
    raise RuntimeError("TUYA_LOCAL_SOURCE must contain custom_components/tuya_local.")
sys.path.insert(0, source)

