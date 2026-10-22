"""Premium decisions based only on server-verified membership.

SharedPreferences may hold a short UI cache of the last server response.
That cache must never invent or extend a trial from the device clock.
"""

from datetime import datetime, timezone

BASIC_LIMITS = {
    "monthly_transactions": 30,
    "customers": 10,
    "products": 20,
    "reminders": 3,
}

# Offline UI grace: show last verified Premium for at most this many hours
# after the last successful server check. Does not start or extend trial.
CACHE_MAX_AGE_HOURS = 48


def _parse_iso(value):
    if not value or not isinstance(value, str):
        return None
    try:
        cleaned = value.replace("Z", "+00:00")
        return datetime.fromisoformat(cleaned)
    except ValueError:
        return None


def _as_status(payload):
    return payload if isinstance(payload, dict) else None


def premium_access(server_status, *, allow_cache=False):
    """Return true only for an entitlement issued by the membership API.

    allow_cache=True may accept a previously verified payload stamped with
    server_verified + cached_at. Device-local trial counters are never used.
    """
    status = _as_status(server_status)
    if not status or status.get("server_verified") is not True:
        return False
    if status.get("premium_active") is not True:
        return False
    if status.get("from_cache") is True:
        if not allow_cache:
            return False
        cached_at = _parse_iso(status.get("cached_at"))
        if cached_at is None:
            return False
        now = datetime.now(timezone.utc)
        if cached_at.tzinfo is None:
            cached_at = cached_at.replace(tzinfo=timezone.utc)
        age_hours = (now - cached_at).total_seconds() / 3600
        if age_hours < 0 or age_hours > CACHE_MAX_AGE_HOURS:
            return False
        # Honor server-provided end time when present; do not recompute trial.
        ends_at = _parse_iso(status.get("premium_ends_at") or status.get("trial_ends_at"))
        if ends_at is not None:
            if ends_at.tzinfo is None:
                ends_at = ends_at.replace(tzinfo=timezone.utc)
            if now > ends_at:
                return False
    return True


def current_plan(server_status):
    if not isinstance(server_status, dict) or server_status.get("server_verified") is not True:
        return "unknown"
    return server_status.get("plan", "basic")


def trial_days_left(server_status):
    if not isinstance(server_status, dict) or server_status.get("server_verified") is not True:
        return 0
    try:
        return max(0, int(server_status.get("trial_days_left", 0)))
    except (TypeError, ValueError):
        return 0


def membership_summary(server_status):
    if not isinstance(server_status, dict) or server_status.get("server_verified") is not True:
        return "Sunucu üyeliği doğrulanmadı"
    if server_status.get("from_cache"):
        prefix = "Önbellek · "
    else:
        prefix = ""
    if server_status.get("premium_active"):
        days = trial_days_left(server_status)
        if server_status.get("plan") == "trial":
            return f"{prefix}Premium denemesi · {days} gün kaldı"
        return f"{prefix}Premium üyelik etkin"
    return f"{prefix}Temel üyelik"


def stamp_cache(server_status):
    """Attach cache metadata for SharedPreferences UI-only storage."""
    if not isinstance(server_status, dict) or server_status.get("server_verified") is not True:
        return None
    cached = dict(server_status)
    cached["from_cache"] = False
    cached["cached_at"] = datetime.now(timezone.utc).isoformat()
    return cached


def as_cached_status(stored):
    """Mark a stored payload as cache so live-only checks can reject it."""
    if not isinstance(stored, dict) or stored.get("server_verified") is not True:
        return None
    status = dict(stored)
    status["from_cache"] = True
    return status
