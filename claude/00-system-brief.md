# FPL Automation: System Brief

**Read this first in any new session.** It is the orientation doc for a cold start (scheduled tasks fire fresh sessions with no memory of prior work).

Owner: Rhys. Season: 2026/27. Goal: maximise total points.

---

## 1. The core constraint

The Claude cloud container has a locked egress allowlist. `fantasy.premierleague.com` is **blocked** (CONNECT tunnel 403). Reachable: `raw.githubusercontent.com`, `pypi.org`, `npmjs`. Not reachable: FPL API, fbref, football-data.org.

`WebFetch` *can* reach the FPL API but passes the response through a small summarising model, so it is lossy. Usable for tiny endpoints, useless for the 567-player bootstrap payload.

**Therefore:** all data flows through a GitHub repo that Rhys owns, where a GitHub Action pulls the FPL API and commits reduced JSON. The container reads that via `raw.githubusercontent.com`. `raw.githubusercontent.com` also returns `access-control-allow-origin: *`, so the browser artifact can fetch the same files client-side and stay genuinely live.

```
FPL API  ──GitHub Action (hourly / 10-min on match days)──▶  rhys/fpl-mirror  ──┬──▶ container (raw.githubusercontent) ──▶ model, optimiser, weekly rec
                                                                                └──▶ HTML artifact (CORS *) ──▶ live tracker in Cowork sidebar
```

## 2. Repo contract

Repo: `<rhys>/fpl-mirror` (public — required for unauthenticated raw reads and open CORS).

| Path | Contents | Refresh |
|---|---|---|
| `data/players.json` | 567 players, 60 whitelisted fields incl. xG/xA/xGC per 90, DefCon per 90, CBIT, recoveries, tackles, price, ownership, status, news | hourly |
| `data/teams.json` | 20 teams, strength ratings | hourly |
| `data/events.json` | 38 gameweeks, deadlines, chip windows, average scores | hourly |
| `data/fixtures.json` | 380 fixtures, kickoff times, FDR both sides, live scores | hourly |
| `data/live.json` | in-play per-player points for the current GW | 10 min on match days |
| `data/entry.json`, `entry_history.json`, `entry_transfers.json`, `picks.json` | Rhys's team, rank history, transfer log, current picks | hourly |
| `data/leagues.json` | mini-league standings | hourly |
| `data/element_summaries.json` | match-by-match history, top ~280 players | daily 04:20 UTC |
| `snapshots/prices-YYYY-MM-DD.json` | daily price/ownership/net-transfer series | daily |
| `data/meta.json` | fetch timestamp, current + next GW, next deadline | every run |

Base URL: `https://raw.githubusercontent.com/<user>/fpl-mirror/main/`

**Always check `meta.json.fetched_at` before trusting the data.** If it is more than 3 hours old the Action has failed or been throttled; say so rather than producing a recommendation on stale prices.

## 3. Project docs (state store)

| Doc | Purpose |
|---|---|
| `00-system-brief.md` | this file |
| `01-rules-2026-27.md` | scoring, DefCon thresholds, BPS changes, chip rules, key dates |
| `02-strategy.md` | risk posture, model spec, chip roadmap, standing constraints |
| `03-gw1-recommendation.md` | founding GW1 analysis. Permanent, never overwritten |
| `04-squad-state.md` | current 15, purchase prices, bank, free transfers, chips used |
| `05-data-contract.md` | repo URL, entry ID, league IDs, field definitions |
| `06-gw-log.md` | per-GW: recommendation made, action taken, points scored, model error |
| `07-current-recommendation.md` | rolling weekly rec, replaced every gameweek |

Corrected 19 Aug 2026: the numbering above previously listed `03` as squad-state and `04` as the gw-log, which did not match the files on disk. `04` and `06` are the memory. The FPL API does not expose a saved squad before a deadline (`/my-team/` needs a login cookie), so pre-deadline squad state lives in `03` and is reconciled against `picks.json` once the deadline passes.

## 4. Expected points model

Per player, per gameweek, built from FPL-native stats. No external xG provider is reachable, so everything derives from the API's own `expected_*` fields (Opta-sourced).

1. **Minutes** — p(start) from `starts_per_90`, recent minutes trend, `status`, `chance_of_playing_next_round`, `news`. Produces xMins, then appearance points (1 under 60, 2 at 60+).
2. **Attacking returns** — `expected_goals_per_90` and `expected_assists_per_90`, scaled by xMins, adjusted for opponent defensive strength (fixture FDR + opponent `expected_goals_conceded_per_90`) and home/away. Converted at position rates: goal GK 10 / DEF 6 / MID 5 / FWD 4, assist 3.
3. **Clean sheets** — Poisson on opponent expected goals for a 0. Pays GK/DEF 4, MID 1.
4. **Goals conceded** — expected −1 per 2 conceded, GK/DEF only.
5. **Saves** — `saves_per_90` scaled by opponent shot volume, 1 per 3.
6. **DefCon** — p(hitting 10 CBIT for DEF, 12 CBIRT for MID/FWD) modelled per match, not from the season average. Averages badly understate the value of a high-variance high-volume tackler. Uses `element_summaries.json` per-match counts.
7. **Bonus** — expected BPS → historical BPS-rank-to-bonus mapping. **Flagged proxy:** the BPS weights changed for 2026/27, so any mapping trained on 2025/26 is wrong until ~GW6 of live data. Under-weight bonus early. Model bonus and DefCon as **separate** terms: the 2026/27 rebalance cut CBI from 1 BPS per 2 actions to 1 per 3 specifically to reduce the overlap, so assuming they co-occur now double-counts.
8. **Cards** — yellow rate × −1.
9. **Season-phase correction**. **Added 19 Aug 2026.** Rates are season averages, but the solver optimises an 8 GW horizon at the very start of the season. Some players score at materially different per-90 rates in GW1-6 than across GW7-38, and the effect is stable across seasons. A shrunk per-player multiplier corrects the attacking component only. See `02-strategy.md`. League median multiplier is 0.98, so this is a redistribution, not a global inflation.

**Cold-start caveat, GW1–4:** there is zero 2026/27 match data. The model runs on 2025/26 priors pulled from the `vaastav/Fantasy-Premier-League` historical repo, blended with this season's prices, ownership and fixtures. That is a proxy for current form, not a measurement of it. It must be labelled as such in any commentary and the confidence band widened accordingly.

## 5. Optimiser

MILP via PuLP. Objective: maximise decayed expected points of the starting XI across a rolling horizon (default 5 GWs, decay ~0.84 per GW ahead).

Constraints: £100.0m budget with 50% sell-on fee on profit; 15 players (2/5/5/3); legal XI (min 1 GK, 3 DEF, 2 MID, 1 FWD); max 3 per club; bench ordered by p(minutes); transfer cost −4 per move beyond banked free transfers; free transfers roll to a max of 5; max 20 transfers in a single GW.

Solved as: hold (0 transfers), 1 FT, 2 moves, 3 moves. Reports net gain over the horizon for each, so a −4 is only recommended when the horizon gain clears the hit with margin.

**Risk posture: max expected points, ownership ignored.** No template weighting, no differential bonus. This is deliberate and matches the stated goal of maximising points rather than protecting rank. Consequence to keep visible: overall rank will be noisier than the score, and a strong points week can still lose ground if the field owns a haul the model faded.

## 6. Weekly cycle

Gameweek deadlines move (Friday, Saturday, Tuesday), so nothing is hard-coded to a weekday. A daily scheduled task reads `meta.json.next_deadline`, and only produces the full recommendation once inside the T-48h window.

**T-48h deliverable:** transfers (with hit maths), captain and vice, starting XI, bench order, chip call, price-change risk on anything being bought or sold, and the two- to three-week forward plan.

**T-3h final sweep: now required, not optional.** T-48h precedes most managerial press conferences. For a Saturday deadline the T-48h call lands Thursday, before Friday pressers. Minutes are the model's worst-performing component and every worst over-prediction in backtesting was a minutes error, so the sweep is the single highest-value fix available. The T-48h output is explicitly **provisional on late news** and must be labelled that way.

The sweep is manual. Predicted lineups and injury feeds are not on the container allowlist, so it runs via `WebFetch` or by Rhys directly. Cross-reference at least two of: Ben Dinnery / Premier Injuries, Fantasy Football Scout predicted lineups, the official FPL status flags in `players.json`. The sweep can override the optimiser; it does not need to re-solve.

## 7.5 Mirror model code can drift from the docs

Checked 19 Aug 2026 and both were stale:

- `model/features.py` in the mirror is the **pre-fix** minutes model. The `MOVER_BLEND` patch is **not committed**, despite `06-gw-log.md` recording it as commit `eabbd98`. Any scheduled run reproduces the original defect.
- `model/squad_ids.json` holds **Revision 1**, not the locked squad.

Verify both against the docs at the start of any session that will re-solve. The docs are the memory; the repo is not.

## 7. Execution

Rhys makes all changes manually in the official FPL app. Nothing here writes to the FPL account. The tool recommends; he executes.
