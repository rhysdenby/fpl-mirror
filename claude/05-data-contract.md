# Data Contract

Everything the tool reads. Verified live 18 Aug 2026, 03:13 UTC.

## Identifiers

| Thing | Value |
|---|---|
| Mirror repo | `rhysdenby/fpl-mirror` (public) |
| Base URL | `https://raw.githubusercontent.com/rhysdenby/fpl-mirror/main/` |
| FPL entry ID | `5470938` |
| Team name | HaCunha Matata |
| Classic league | `218656` — Stank League |
| Seasons active | 15 |

## Endpoint status

| File | Status | Notes |
|---|---|---|
| `data/meta.json` | live | fetch timestamp, current/next GW, next deadline |
| `data/players.json` | live, 590 players | pre-season it still carries 2025/26 aggregates; these reset once GW1 starts |
| `data/teams.json` | live | granular `strength_attack_*` / `strength_defence_*` are all **zero** pre-season and unusable; only `strength_overall_home/away` (the FDR tier) is populated. Team strength is derived from 2025/26 match data instead |
| `data/fixtures.json` | live, 380 | kickoff times and FDR both sides |
| `data/element_summaries.json` | live, 280 players | `history` is empty until matches are played; `history_past` gives up to 5 prior seasons |
| `data/entry.json` | live | rank fields null until GW1 completes |
| `data/entry_history.json` | live | `current` empty until GW1 completes; `past` has all 15 seasons |
| `data/leagues.json` | live | Stank League standings empty until GW1 completes |
| `data/live.json` | live, empty | populates during matches |
| `data/picks.json` | **404 until the GW1 deadline passes** | expected; picks are not public before the deadline |
| `data/entry_transfers.json` | 404 | no transfers made yet |

## External sources

| Source | Use |
|---|---|
| `vaastav/Fantasy-Premier-League` `data/2025-26/gws/merged_gw.csv` | 2025/26 per-match data: minutes, starts, xG, xA, xGC, CBI, tackles, recoveries, `defensive_contribution` counts, bonus, BPS. The cold-start backbone and the source for DefCon threshold probabilities |
| same repo, `data/2025-26/players_raw.csv` | maps 2025/26 element ids to the stable `code`, which is how players join across seasons |
| same repo, `data/2022-23`, `2023-24`, `2024-25` `gws/merged_gw.csv` | **added 19 Aug 2026.** Four-season panel used to fit the season-phase correction (GW1-6 points per 90 against GW7-38 points per 90). Joined on player name within season, then to `code` via the 2025/26 raw file. All reachable and confirmed HTTP 200 |

**Not machine-reachable, requires manual or WebFetch retrieval:** predicted lineups and injury feeds (Ben Dinnery / Premier Injuries, Fantasy Football Scout predicted lineups). These feed the mandatory T-3h pre-deadline sweep and cannot be automated inside the container.

Note: the vaastav mirror of the **current** season is roughly two weeks stale (its 2026-27 snapshot predates pre-season price changes). Use it for history only, never for live data.

## Network constraints

Reachable from the Claude container: `raw.githubusercontent.com`, `api.github.com` (limited), `pypi.org`, npm.
Blocked: `fantasy.premierleague.com` (CONNECT tunnel 403), `fbref.com`, `football-data.org`.
`raw.githubusercontent.com` returns `access-control-allow-origin: *` and `cache-control: max-age=300`, which is what lets the browser artifact fetch the same files directly.

## Model code

Lives at `model/` in the mirror repo so a fresh, ephemeral session can fetch and run it:
`features.py`, `optimise.py`, `weekly.py`, `backtest.py`, `squad_ids.json`.

**Verified 19 Aug 2026: the repo is behind the docs. Two uncommitted items.**

| File | State in mirror | Required |
|---|---|---|
| `model/features.py` | **pre-fix minutes model.** No `MOVER_BLEND`. Movers still inherit their old club's start rate | commit the `MOVER_BLEND = 0.50` patch. `06-gw-log.md` records this as commit `eabbd98`; that record is wrong |
| `model/squad_ids.json` | holds **Revision 1** (Verbruggen, Guéhi, Semenyo) | replace with whichever GW1 squad is entered |

Also missing: the season-phase correction is not in the repo at all. It currently exists only as session code. It needs committing as `model/phase.py` or folded into `features.py` before any scheduled run can reproduce the GW1 recommendation.

Dependencies confirmed installable in-container: `pandas`, `numpy`, `pulp`, `pyarrow`. `pyarrow` is required for the parquet write in `features.py` and is **not** present by default.

## Career baseline

Rhys's own history, for judging whether a season is going well rather than leaning on unreliable external benchmarks.

| Season | Points | Rank | Percentile |
|---|---|---|---|
| 2024/25 | 2,438 | 350,194 | top 3% |
| 2025/26 | 2,163 | 1,333,580 | top 10% |
| 2022/23 | 2,248 | 2,116,175 | top 19% |
| 2018/19 | 2,152 | 484,910 | top 8% |

Career best is 2024/25 at top 3%. Median season sits around top 20-25%. A 2026/27 target of beating 2,438 points is the honest bar.
