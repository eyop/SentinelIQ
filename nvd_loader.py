"""Backward-compat shim.

The canonical NVD loader now lives at `ingestion/nvd_loader.py`.
This module re-exports `fetch_recent_cves` so existing references
such as `from nvd_loader import fetch_recent_cves` continue to work.
"""

from ingestion.nvd_loader import fetch_recent_cves

__all__ = ["fetch_recent_cves"]
