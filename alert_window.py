# alert_window.py
import json
from datetime import datetime, timezone
from dateutil import parser

SEEN_FILE = "seen_alerts.json"

def _load_seen() -> set[str]:
    try:
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()

def _save_seen(seen: set[str]) -> None:
    try:
        with open(SEEN_FILE, "w", encoding="utf-8") as f:
            json.dump(list(seen), f)
    except Exception:
        pass

def minutes_until(iso_ts: str | None) -> float | None:
    if not iso_ts:
        return None
    try:
        dt = parser.isoparse(iso_ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return (dt - datetime.now(timezone.utc)).total_seconds() / 60.0
    except Exception:
        return None

def pick_eta(arrival: dict) -> str | None:
    """Prefer estimated arrival; fallback to scheduled (ISO-8601 strings)."""
    return arrival.get("estimated") or arrival.get("scheduled")

def make_alert_key(flight: dict, eta_iso: str | None) -> str:
    f = flight.get("flight") or {}
    fnum = (f.get("iata") or f.get("number") or "UNKNOWN").upper()
    day_key = (eta_iso or "")[:10]  # YYYY-MM-DD
    return f"{fnum}@{day_key}"

def should_alert_window(flight: dict, dst_iata: str, min_min: int, max_min: int) -> tuple[bool, str | None, float | None]:
    """
    True if:
      - destination matches dst_iata
      - ETA minutes in [min_min, max_min]
      - not alerted before today
    Returns (ok, eta_iso, minutes)
    """
    arrival = flight.get("arrival") or {}
    dst = (arrival.get("iata") or arrival.get("airport") or "").upper()
    if dst != dst_iata.upper():
        return (False, None, None)

    eta_iso = pick_eta(arrival)
    mins = minutes_until(eta_iso)
    if mins is None:
        return (False, eta_iso, None)
    if mins < min_min or mins > max_min:
        return (False, eta_iso, mins)

    key = make_alert_key(flight, eta_iso)
    seen = _load_seen()
    if key in seen:
        return (False, eta_iso, mins)
    seen.add(key)
    _save_seen(seen)
    return (True, eta_iso, mins)