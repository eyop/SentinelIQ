"""Compatibility wrapper for the root NVD ingestion module."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from nvd_loader import fetch_recent_cves

__all__ = ["fetch_recent_cves"]
