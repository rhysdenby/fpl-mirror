"""Compare the live saved squad against model/squad_ids.json.

Publishes a verdict only. The raw /my-team/ payload never touches disk:
the mirror is public and the saved squad is competitively sensitive
before a deadline.

DIAGNOSTIC BUILD: temporarily logs response body preview and cookie
length (not content) to debug a 403 that looks like a clean DRF auth
rejection rather than a bot-block page. Revert once auth is confirmed
working.
"""
import json, os, pathlib, sys
from datetime import datetime, timezone
import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "squad_check.json"
ENTRY = os.environ["FPL_ENTRY_ID"]
COOKIE = os.environ["FPL_COOKIE"]
VERBOSITY = os.environ.get("SQUAD_CHECK_VERBOSITY", "counts")

NOW = datetime.now(timezone.utc).isoformat(timespec="seconds")


def emit(**kw):
    payload = {"checked_at": NOW, "entry_id": int(ENTRY), **kw}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2))
    return payload


def fetch():
    print(f"DIAG: cookie length = {len(COOKIE)} chars")
    print(f"DIAG: cookie starts with = {COOKIE[:20]!r}")
    print(f"DIAG: contains 'pl_profile' = {'pl_profile' in COOKIE}")
    print(f"DIAG: contains 'sessionid' = {'sessionid' in COOKIE}")
    print(f"DIAG: contains 'datadome' = {'datadome' in COOKIE}")

    r = requests.get(
        f"https://fantasy.premierleague.com/api/my-team/{ENTRY}/",
        headers={
            "Cookie": COOKIE,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/plain, */*",
            "Referer": f"https://fantasy.premierleague.com/entry/{ENTRY}/event/1",
            "Accept-Language": "en-GB,en;q=0.9",
        },
        timeout=30,
    )
    ctype = r.headers.get("content-type", "")
    print(f"DIAG: status={r.status_code} content-type={ctype!r}")
    print(f"DIAG: body preview = {r.text[:500]!r}")

    if r.status_code in (401, 403) or "application/json" not in ctype:
        raise PermissionError(f"auth failed: status={r.status_code} content-type={ctype!r} body_preview={r.text[:300]!r}")
    return r.json()


def main():
    try:
        mt = fetch()
    except PermissionError as e:
        emit(auth_ok=False, error=str(e), match=None)
        sys.exit(1)
    except Exception as e:
        emit(auth_ok=False, error=f"{type(e).__name__}: {e}", match=None)
        sys.exit(1)

    intended = {p["id"] for p in json.load(open(ROOT / "model" / "squad_ids.json"))}
    live_picks = mt["picks"]
    live = {p["element"] for p in live_picks}

    missing, extra = intended - live, live - intended
    tr = mt.get("transfers") or {}

    print("RAW chips:", json.dumps(mt.get("chips", []), indent=2))
    armed = [c["name"] for c in mt.get("chips", [])
             if c.get("status_for_entry") == "active"]

    cap = next((p["element"] for p in live_picks if p.get("is_captain")), None)
    intended_cap = next((p["id"] for p in json.load(open(ROOT / "model" / "squad_ids.json"))
                         if p.get("c")), None)

    verdict = dict(
        auth_ok=True,
        match=not (missing or extra),
        n_mismatched=len(missing | extra),
        captain_match=(cap == intended_cap) if intended_cap else None,
        bank=tr.get("bank"),
        squad_value=tr.get("value"),
        free_transfers=tr.get("limit"),
        transfers_made=tr.get("made"),
        chip_armed=armed or None,
    )
    if VERBOSITY == "full":
        verdict["missing"] = sorted(missing)
        verdict["extra"] = sorted(extra)
    else:
        pos = {p["id"]: p["pos"] for p in json.load(open(ROOT / "model" / "squad_ids.json"))}
        verdict["mismatched_positions"] = sorted({pos[i] for i in missing if i in pos})

    emit(**verdict)


if __name__ == "__main__":
    main()
