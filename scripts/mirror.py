#!/usr/bin/env python3
"""Mirror public Fantasy Premier League API endpoints into flat JSON.

Runs in GitHub Actions. Everything pulled here is public, no auth needed.
Writes reduced payloads to data/ and dated snapshots to snapshots/.
"""

import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

BASE = "https://fantasy.premierleague.com/api"
ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SNAPS = ROOT / "snapshots"
UA = "Mozilla/5.0 (compatible; fpl-mirror/1.0)"

# Only these element fields are kept. Trims ~1.5MB to ~250KB.
PLAYER_FIELDS = [
    "id", "code", "web_name", "first_name", "second_name", "team", "team_code",
    "element_type", "status", "news", "news_added",
    "chance_of_playing_this_round", "chance_of_playing_next_round",
    "now_cost", "cost_change_event", "cost_change_start", "selected_by_percent",
    "transfers_in_event", "transfers_out_event", "price_change_percent",
    "minutes", "starts", "starts_per_90", "total_points", "points_per_game",
    "event_points", "form", "ep_this", "ep_next", "value_form", "value_season",
    "goals_scored", "assists", "clean_sheets", "clean_sheets_per_90",
    "goals_conceded", "goals_conceded_per_90", "saves", "saves_per_90",
    "bonus", "bps", "yellow_cards", "red_cards", "own_goals",
    "penalties_saved", "penalties_missed",
    "expected_goals", "expected_goals_per_90",
    "expected_assists", "expected_assists_per_90",
    "expected_goal_involvements", "expected_goal_involvements_per_90",
    "expected_goals_conceded", "expected_goals_conceded_per_90",
    "defensive_contribution", "defensive_contribution_per_90",
    "clearances_blocks_interceptions", "recoveries", "tackles",
    "influence", "creativity", "threat", "ict_index",
    "penalties_order", "penalties_text",
    "corners_and_indirect_freekicks_order", "direct_freekicks_order",
    "dreamteam_count", "in_dreamteam",
]


def get(path, retries=4):
    url = f"{BASE}{path}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.load(r)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            if attempt == retries - 1:
                print(f"FAIL {url}: {e}", file=sys.stderr)
                return None
            time.sleep(3 * (attempt + 1))
    return None


def write(rel, payload):
    p = DATA / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True))
    print(f"wrote {rel} ({p.stat().st_size:,} bytes)")


def main():
    DATA.mkdir(exist_ok=True)
    SNAPS.mkdir(exist_ok=True)
    now = datetime.now(timezone.utc)
    cfg = json.loads((ROOT / "config.json").read_text())
    entry_id = cfg.get("entry_id")
    mode = os.environ.get("MIRROR_MODE", "full")

    boot = get("/bootstrap-static/")
    if not boot:
        sys.exit("bootstrap-static unavailable, aborting without writing")

    players = [{k: e.get(k) for k in PLAYER_FIELDS} for e in boot["elements"]]
    events = boot["events"]
    current = next((e for e in events if e.get("is_current")), None)
    nxt = next((e for e in events if e.get("is_next")), None)

    write("players.json", players)
    write("teams.json", boot["teams"])
    write("events.json", events)
    write("element_types.json", boot["element_types"])
    write("game_settings.json", boot.get("game_settings", {}))

    fixtures = get("/fixtures/")
    if fixtures:
        write("fixtures.json", fixtures)

    # Live in-play scores for the gameweek currently underway.
    live_gw = (current or nxt or {}).get("id")
    if live_gw:
        live = get(f"/event/{live_gw}/live/")
        if live:
            write("live.json", {"event": live_gw, "elements": live.get("elements", [])})

    if entry_id:
        for name, path in [
            ("entry.json", f"/entry/{entry_id}/"),
            ("entry_history.json", f"/entry/{entry_id}/history/"),
            ("entry_transfers.json", f"/entry/{entry_id}/transfers/"),
        ]:
            d = get(path)
            if d:
                write(name, d)
        # Picks only become public once the deadline has passed.
        if current:
            picks = get(f"/entry/{entry_id}/event/{current['id']}/picks/")
            if picks and "picks" in picks:
                write("picks.json", {"event": current["id"], **picks})

    standings = {}
    for lid in cfg.get("classic_league_ids", []):
        d = get(f"/leagues-classic/{lid}/standings/")
        if d:
            standings[str(lid)] = d
        time.sleep(1)
    for lid in cfg.get("h2h_league_ids", []):
        d = get(f"/leagues-h2h/{lid}/standings/")
        if d:
            standings[str(lid)] = d
        time.sleep(1)
    if standings:
        write("leagues.json", standings)

    # Per-player match-by-match history. Heavy, so daily only.
    if mode == "daily":
        pool = sorted(
            [p for p in players if (p.get("minutes") or 0) > 0 or float(p.get("selected_by_percent") or 0) > 1.0],
            key=lambda p: float(p.get("selected_by_percent") or 0),
            reverse=True,
        )[:280]
        summaries = {}
        for p in pool:
            d = get(f"/element-summary/{p['id']}/", retries=2)
            if d:
                summaries[str(p["id"])] = {
                    "history": d.get("history", []),
                    "history_past": d.get("history_past", []),
                }
            time.sleep(0.35)
        if summaries:
            write("element_summaries.json", summaries)

    stamp = now.strftime("%Y-%m-%d")
    snap = SNAPS / f"prices-{stamp}.json"
    snap.write_text(json.dumps(
        [{"id": p["id"], "now_cost": p["now_cost"],
          "selected_by_percent": p["selected_by_percent"],
          "transfers_in_event": p["transfers_in_event"],
          "transfers_out_event": p["transfers_out_event"]} for p in players],
        separators=(",", ":")))
    print(f"snapshot {snap.name}")

    write("meta.json", {
        "fetched_at": now.isoformat(),
        "mode": mode,
        "current_event": (current or {}).get("id"),
        "next_event": (nxt or {}).get("id"),
        "next_deadline": (nxt or {}).get("deadline_time"),
        "player_count": len(players),
        "entry_id": entry_id,
    })


if __name__ == "__main__":
    main()
