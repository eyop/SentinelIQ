# scheduler.py  (replace the existing file)
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import get_settings

logging.basicConfig(level="INFO", format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)
settings = get_settings()


def ingest_job() -> None:
    """Full ingestion run — called by the scheduler every N hours."""
    from ingestion.mitre_loader import fetch_attack_techniques
    from ingestion.normaliser import cve_to_document, technique_to_document
    from ingestion.nvd_loader import fetch_recent_cves
    from rag.chunker import chunk_documents
    from rag.vectorstore import upsert_documents

    start = time.time()
    logger.info("=== Ingestion job starting at %s ===", datetime.now(tz=timezone.utc).isoformat())

    cves = fetch_recent_cves()
    techniques = fetch_attack_techniques()

    cve_docs = [cve_to_document(c) for c in cves]
    tech_docs = [technique_to_document(t) for t in techniques]
    chunked = chunk_documents(cve_docs + tech_docs)
    upsert_documents(chunked)

    elapsed = round(time.time() - start, 1)
    logger.info("=== Done: %d CVEs, %d techniques, %d chunks in %ss ===",
                len(cves), len(techniques), len(chunked), elapsed)


def on_job_executed(event):
    logger.info("Job '%s' completed successfully", event.job_id)


def on_job_error(event):
    logger.error("Job '%s' FAILED: %s", event.job_id, event.exception)
    # TODO: send a Slack/email alert here


if __name__ == "__main__":
    scheduler = BlockingScheduler(timezone="UTC")

    scheduler.add_listener(on_job_executed, EVENT_JOB_EXECUTED)
    scheduler.add_listener(on_job_error, EVENT_JOB_ERROR)

    scheduler.add_job(
        ingest_job,
        trigger=IntervalTrigger(hours=settings.ingest_interval_hours),
        id="cve_ingest",
        name="CVE + ATT&CK ingestion",
        replace_existing=True,
        max_instances=1,          # prevents overlapping runs
        misfire_grace_time=3600,  # if it misses its window by <1hr, still run it
        next_run_time=datetime.now(tz=timezone.utc),  # run immediately on startup
    )

    logger.info("Scheduler started — running every %dh", settings.ingest_interval_hours)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped cleanly")