"""Compare the live saved squad against model/squad_ids.json.

Publishes a verdict only. The raw /my-team/ payload never touches disk:
the mirror is public and the saved squad is competitively sensitive
before a deadline.
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
    """Always write a verdict, including on failure. A missing file and a
    failed check must never look the same to the consumer."""
    payload = {"checked_at": NOW, "entry_id": int(ENTRY), **kw}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2))
    return payload


def fetch():
    r = requests.get(
        f"https://fantasy.premierleague.com/api/my-team/{ENTRY}/",
        headers={
            "Cookie": COOKIE,
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json",
        },
        timeout=30,
    )
    ctype = r.headers.get("content-type", "")
    # Cloudflare returns HTML with a 200. Status code alone is not enough.
    if r.status_code in (401, 403) or "application/json" not in ctype:
        raise PermissionError(f"auth failed: status={r.status_code} content-type={ctype!r}")
    return r.json()


def main():
    try:
        mt = fetch()
    except PermissionError as e:
        emit(auth_ok=False, error=str(e), match=None)
        sys.exit(1)          # fail the job so it surfaces in the Actions tab
    except Exception as e:
        emit(auth_ok=False, error=f"{type(e).__name__}: {e}", match=None)
        sys.exit(1)

    intended = {p["id"] for p in json.load(open(ROOT / "model" / "squad_ids.json"))}
    live_picks = mt["picks"]
    live = {p["element"] for p in live_picks}

    missing, extra = intended - live, live - intended
    tr = mt.get("transfers") or {}

    # Log the raw chips array while its semantics are still unconfirmed.
    # Not secret, and reading it is how the field gets pinned down.
    print("RAW chips:", json.dumps(mt.get("chips", []), indent=2))
    armed = [c["name"] for c in mt.get("chips", [])
             if c.get("status_for_entry") == "active"]

    cap = next((p["element"] for p in live_picks if p.get("is_captain")), None)
    vice = next((p["element"] for p in live_picks if p.get("is_vice_captain")), None)
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
