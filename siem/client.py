"""Elasticsearch SIEM client for SentinelIQ with offline sample fallback."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from config import get_settings

logger = logging.getLogger(__name__)

SAMPLE_SECURITY_EVENTS: list[dict[str, Any]] = [
    {
        "_id": "sample-1",
        "_index": "sentineliq-demo",
        "_source": {
            "timestamp": "2026-08-10T09:12:00Z",
            "event.module": "suricata",
            "event.kind": "alert",
            "rule.name": "ET EXPLOIT Possible CVE-2024-3400 command injection attempt",
            "source.ip": "203.0.113.10",
            "destination.ip": "192.168.1.50",
            "destination.port": 443,
            "message": "Suricata alert: ET EXPLOIT Possible CVE-2024-3400 (Palo Alto PAN-OS) command injection attempt detected from 203.0.113.10 to 192.168.1.50:443.",
        },
    },
    {
        "_id": "sample-2",
        "_index": "sentineliq-demo",
        "_source": {
            "timestamp": "2026-08-10T09:18:00Z",
            "event.module": "system",
            "event.kind": "event",
            "event.category": "authentication",
            "event.outcome": "failure",
            "user.name": "admin",
            "source.ip": "198.51.100.23",
            "message": "5 failed SSH login attempts for user 'admin' from 198.51.100.23 within 60 seconds.",
        },
    },
    {
        "_id": "sample-3",
        "_index": "sentineliq-demo",
        "_source": {
            "timestamp": "2026-08-10T09:25:00Z",
            "event.module": "windows",
            "event.kind": "alert",
            "winlog.event_id": 4688,
            "process.name": "powershell.exe",
            "process.command_line": "powershell.exe -enc SQBFAFgAKABOAGUAdwAtAE8AYgBqAGUAYwB0ACAA",
            "message": "PowerShell process created with encoded command line - possible exploitation of CVE-2022-41040 / CVE-2022-41082 (ProxyShell chain).",
        },
    },
    {
        "_id": "sample-4",
        "_index": "sentineliq-demo",
        "_source": {
            "timestamp": "2026-08-10T09:31:00Z",
            "event.module": "suricata",
            "event.kind": "alert",
            "rule.name": "ET SCAN Suspicious port scan (nmap)",
            "source.ip": "203.0.113.77",
            "destination.ip": "192.168.1.0/24",
            "message": "Suspicious TCP port scan detected from 203.0.113.77 across multiple hosts on the internal network.",
        },
    },
    {
        "_id": "sample-5",
        "_index": "sentineliq-demo",
        "_source": {
            "timestamp": "2026-08-10T09:40:00Z",
            "event.module": "zeek",
            "event.kind": "alert",
            "zeek.connection.service": "rdp",
            "source.ip": "198.51.100.200",
            "destination.ip": "192.168.1.88",
            "destination.port": 3389,
            "message": "RDP brute-force pattern observed towards 192.168.1.88 from 198.51.100.200 - correlation with CVE-2019-0708 (BlueKeep) relevant.",
        },
    },
]


def _normalise_doc(doc: dict[str, Any]) -> dict[str, Any]:
    """Flatten an Elasticsearch hit into a simple event dict."""
    source = doc.get("_source") or {}
    return {
        "id": doc.get("_id"),
        "index": doc.get("_index"),
        "timestamp": source.get("timestamp") or datetime.now(timezone.utc).isoformat(),
        "event_module": source.get("event.module"),
        "event_category": source.get("event.category"),
        "event_outcome": source.get("event.outcome"),
        "rule_name": source.get("rule.name"),
        "source_ip": source.get("source.ip"),
        "destination_ip": source.get("destination.ip"),
        "destination_port": source.get("destination.port"),
        "user_name": source.get("user.name"),
        "process_name": source.get("process.name"),
        "message": source.get("message") or "",
        "raw": source,
    }


class SIEMClient:
    """Lazy Elasticsearch client wrapper with offline sample fallback."""

    def __init__(self) -> None:
        self._es: Any = None

    def _get_client(self) -> Any:
        """Build (once) and return the elasticsearch client or None."""
        if self._es is not None:
            return self._es
        settings = get_settings()
        try:
            from elasticsearch import Elasticsearch

            kwargs: dict[str, Any] = {"hosts": [settings.elastic_url]}
            if settings.elastic_username and settings.elastic_password:
                kwargs["basic_auth"] = (settings.elastic_username, settings.elastic_password)
            self._es = Elasticsearch(**kwargs)
        except Exception as exc:  # pragma: no cover - library missing
            logger.warning("Elasticsearch client unavailable: %s", exc)
            self._es = None
        return self._es

    def ping(self) -> bool:
        """Return True if Elasticsearch is reachable."""
        client = self._get_client()
        if client is None:
            return False
        try:
            return bool(client.ping())
        except Exception as exc:
            logger.warning("Elasticsearch ping failed: %s", exc)
            return False
