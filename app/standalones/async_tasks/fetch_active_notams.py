import os
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Any, Dict, List

import requests
import requests_cache  # Added: pip install requests-cache
from dotenv import load_dotenv

from ..notams.helpers.notam_store import insert_notam

load_dotenv()
logger = logging.getLogger(__name__)

IVAO_NOTAM_URL = "https://api.ivao.aero/v2/notams/all?mapType=regionMap&now=true"
IVAO_API_KEY = os.getenv("IVAO_API_KEY", "xxx")

# Initialize a cached session
session = requests_cache.CachedSession(
    'notam_cache',
    backend='sqlite',
    expire_after=timedelta(hours=72),
    stale_if_error=True,
)

def iso_to_ddmmyyyy_hhmm(iso_str: Optional[str]) -> Optional[str]:
    """
    Convert an ISO8601 timestamp (e.g. ending with 'Z') to 'DD/MM/YYYY HHMM'.
    Returns None on invalid or empty input.
    """
    if not iso_str:
        return None
    try:
        if iso_str.endswith("Z"):
            dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(iso_str)
        dt_utc = dt.astimezone(timezone.utc)
        return dt_utc.strftime("%d/%m/%Y %H%M")
    except Exception:
        return None

def _extract_location_and_class(notam: Dict[str, Any]) -> tuple[Optional[str], str]:
    """
    Try to pull a location ICAO and a 'class' label. Defaults to International unless marked military.
    """
    klass = "International"
    location: Optional[str] = None

    airports = notam.get("airports")
    if isinstance(airports, dict):
        location = airports.get("icao")
        if airports.get("military", False):
            klass = "Military"
    elif isinstance(airports, list) and airports:
        first = airports[0]
        if isinstance(first, dict):
            location = first.get("icao")
            if first.get("military", False):
                klass = "Military"

    if not location:
        center = notam.get("center")
        if isinstance(center, dict):
            location = center.get("icao") or center.get("id")
            if center.get("military", False):
                klass = "Military"

    return location, klass

def fetch_active_notams() -> int:
    """
    Fetch active IVAO NOTAMs (using cache if available) and upsert into local sqlite.
    Returns number of NOTAMs inserted/updated.
    """
    headers = {"apiKey": IVAO_API_KEY, "accept": "application/json"}

    try:
        # Use the cached session instead of requests.get
        resp = session.get(IVAO_NOTAM_URL, headers=headers, timeout=30)

        if getattr(resp, "from_cache", False):
            logger.info("IVAO NOTAMs loaded from local cache.")
        else:
            logger.info("IVAO NOTAMs fetched from API (cache refreshed).")

        resp.raise_for_status()
        data: List[Dict[str, Any]] = resp.json()
    except Exception as e:
        logger.error(f"Failed to fetch IVAO NOTAMs: {e}")
        return 0

    inserted = 0
    for item in data:
        try:
            location, klass = _extract_location_and_class(item)

            start_time_str = iso_to_ddmmyyyy_hhmm(item.get("startTime"))
            end_time_str = iso_to_ddmmyyyy_hhmm(item.get("endTime"))

            notam_lta_number = str(item.get("name")) if item.get("name") is not None else None
            description = item.get("description")

            if not all([location, notam_lta_number, start_time_str, end_time_str]):
                continue

            uploaded_at = (
                datetime.now(timezone.utc)
                .isoformat(timespec="milliseconds")
                .replace("+00:00", "Z")
            )

            insert_notam(
                location=location,
                notam_lta_number=notam_lta_number,
                klass=klass,
                issue_date_utc=start_time_str,
                effective_date_utc=start_time_str,
                expiration_date_utc=end_time_str,
                notam_condition_subject_title=description or "",
                raw_text=description or "",
                uploaded_at=uploaded_at,
                data_source="IVAO",
                ivao_active=1,
            )
            inserted += 1
        except Exception as e:
            continue

    logger.info(f"IVAO NOTAMs processed: {inserted}")
    return inserted

async def periodic_fetch_ivao_notams(interval_seconds: int = 24 * 60 * 60):
    """
    Periodically fetch IVAO NOTAMs on an interval (default: 24h).
    """
    logger.info("Starting periodic IVAO NOTAM fetcher...")
    while True:
        try:
            fetch_active_notams()
        except Exception as e:
            logger.error(f"IVAO NOTAM periodic fetch failed: {e}")
        await asyncio.sleep(interval_seconds)