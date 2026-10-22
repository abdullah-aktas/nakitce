import json

from data import starter_data

_STORAGE_KEY = "nakitce_records_v1"
_SYNC_CONFIG_KEY = "nakitce_sync_config_v1"
_SYNC_META_KEY = "nakitce_sync_meta_v1"
_EVIDENCE_KEY = "nakitce_local_evidence_v1"
_WORKSPACE_KEY = "nakitce_workspace_v1"

_LEGACY_KEYS = {
    _STORAGE_KEY: "ustakasa_records_v1",
    _SYNC_CONFIG_KEY: "ustakasa_sync_config_v1",
    _SYNC_META_KEY: "ustakasa_sync_meta_v1",
    _EVIDENCE_KEY: "ustakasa_local_evidence_v1",
    _WORKSPACE_KEY: "ustakasa_workspace_v1",
}


async def _load_json(preferences, key, default):
    raw = await preferences.get(key)
    if not raw:
        legacy = _LEGACY_KEYS.get(key)
        if legacy:
            raw = await preferences.get(legacy)
    if not raw:
        return default
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return default


async def load_records(preferences):
    records = await _load_json(preferences, _STORAGE_KEY, None)
    if records is None:
        records = starter_data()
        await save_records(preferences, records)
    return records


async def save_records(preferences, records):
    await preferences.set(_STORAGE_KEY, json.dumps(records, ensure_ascii=False))


async def load_sync_config(preferences):
    return await _load_json(preferences, _SYNC_CONFIG_KEY, {})


async def save_sync_config(preferences, config):
    await preferences.set(_SYNC_CONFIG_KEY, json.dumps(config, ensure_ascii=False))


async def load_sync_meta(preferences):
    return await _load_json(preferences, _SYNC_META_KEY, {})


async def save_sync_meta(preferences, meta):
    await preferences.set(_SYNC_META_KEY, json.dumps(meta, ensure_ascii=False))


async def load_evidence(preferences):
    return await _load_json(preferences, _EVIDENCE_KEY, {})


async def save_evidence(preferences, evidence):
    await preferences.set(_EVIDENCE_KEY, json.dumps(evidence, ensure_ascii=False))


async def load_workspace(preferences):
    workspace = await _load_json(preferences, _WORKSPACE_KEY, None)
    if workspace is None:
        return {"profile": {}, "mode": "simple", "reminders": []}
    workspace.setdefault("profile", {})
    workspace.setdefault("mode", "simple")
    workspace.setdefault("reminders", [])
    # Local membership field is display-only leftover; never grants Premium.
    workspace.pop("membership", None)
    return workspace


async def save_workspace(preferences, workspace):
    payload = dict(workspace)
    payload.pop("membership", None)
    payload.pop("_server_membership_status", None)
    await preferences.set(_WORKSPACE_KEY, json.dumps(payload, ensure_ascii=False))
