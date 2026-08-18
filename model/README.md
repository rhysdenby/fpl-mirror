# Model code

Lives in the mirror repo on purpose. The Claude cloud container is ephemeral, so a
scheduled session starts with an empty filesystem. Keeping the model here means any
fresh session can fetch it from raw.githubusercontent and reproduce the analysis.

**Because sessions fetch from `raw.githubusercontent.com`, an uncommitted change here
does nothing. Commit and push or the next scheduled run uses the old model.**

| File | Purpose |
|---|---|
| `features.py` | builds the per-player, per-gameweek expected points table |
| `optimise.py` | MILP squad optimiser (initial squad / wildcard mode) |
| `weekly.py` | weekly transfer optimiser: compares hold / 1 / 2 / 3 moves net of hits |
| `backtest.py` | walk-forward validation on 2025/26, fit GW1-19, test GW20-38 |
| `squad_ids.json` | the GW1 squad, as element ids |

## Inputs

`features.py` expects these in a `data/` directory beside it:

- `players.json`, `teams.json`, `fixtures.json` — from this repo's `data/`
- `merged_gw_2526.csv` — `vaastav/Fantasy-Premier-League/data/2025-26/gws/merged_gw.csv`
- `hist_players_2526.csv` — `vaastav/Fantasy-Premier-League/data/2025-26/players_raw.csv`

## Change log

### 18 Aug 2026 — mover minutes fix (`MOVER_BLEND`)

**The defect.** The transfer adjustment scaled `g_90` and `a_90` by the ratio of
new-club to old-club attacking strength, but left `p_start` untouched. A player who
changed clubs therefore inherited his old club's start rate unchanged. The bias is
one-directional and large: anyone moving to a stronger squad was rated as nailed as
he was at his previous club.

Pre-fix `p_start`, GW1 2026/27:

| Player | Club | p(start) |
|---|---|---|
| Semenyo | MCI (new) | 0.970 |
| Anderson | MCI (new) | 0.970 |
| Dubravka | TOT (new) | 0.970 |
| Senesi | TOT (new) | 0.970 |
| Guéhi | MCI (new) | 0.921 |
| **Haaland** | **MCI (established)** | **0.895** |

Three new Man City signings rated more likely to start than Haaland, and a £4.0m
keeper rated nailed. Fifty players in the 590-player pool moved this window and every
one was mispriced the same way. The GW1 squad this produced held six movers carrying
42% of its 8-gameweek xP.

**The fix.** For movers only, blend the inherited start rate with the price-rank
pecking-order prior at the new club:

```
p_start = MOVER_BLEND * inherited_rate + (1 - MOVER_BLEND) * price_rank_prior
```

`MOVER_BLEND = 0.50`. Setting it to `1.0` reproduces the pre-fix behaviour exactly,
so the change is auditable and reversible.

**Effect.** Four of fifteen GW1 squad slots changed, all of them movers. Guéhi,
Bruno G., Senesi and Dubravka out. The three-player Man City block that the pre-fix
model produced only appears at `MOVER_BLEND >= 0.85`, i.e. it existed solely because
the model assumed a transfer does not affect minutes.

**`MOVER_BLEND = 0.50` is a chosen number, not a measured one.** The squad is stable
across 0.40 to 0.70. Real 2026/27 minutes data replaces it, so revisit at GW4 and
again before the GW6 wildcard.

**`backtest.py` does not and cannot validate this fix.** It fits on 2025/26 GW1-19 and
tests on GW20-38 of the same season, where nobody changes club. The validation numbers
below are unaffected by the change and also provide no evidence for it. The only real
test is out-of-sample minutes from GW1-3 of 2026/27.

## Validation, run 18 Aug 2026

Fitted on 2025/26 GW1-19, tested on GW20-38, nothing from the test half used in fitting.

- per-match Spearman 0.610, MAE 21.2% better than predicting the mean
- season-total Spearman 0.825 across 780 players (FWD 0.874, MID 0.853, DEF 0.814, GK 0.740)
- top 30 by predicted xP averaged 73.9 actual points vs 44.1 for the eligible pool
- calibration: predicted 1.20 pts/match vs actual 1.12, so the model runs ~7% hot

Every large over-prediction was a minutes failure, not a football failure. That is the
whole error budget, and the `MOVER_BLEND` fix above addresses one specific instance of
it. Re-run `backtest.py` whenever the model changes and keep those numbers honest.

## Known issues

- **`weekly.py --squad` defaults to `ROOT/out/squad_ids.json`, which does not exist in
  this repo.** The tracked squad lives at `model/squad_ids.json`. Either pass `--squad`
  explicitly or change the default, otherwise a scheduled run has no squad to plan from.
- **`optimise.py` uses a flat 0.09 bench weight** for outfield bench slots instead of the
  ordered 0.21 / 0.06 / 0.002. It will happily park a non-playing £4.0m body on the bench.
  Restrict the candidate pool by `p_start` when building initial squads.
- **No correlation penalty in the objective.** Deliberate: the stated risk posture is
  maximum total points with club concentration ignored. Do not add one without changing
  the posture in `02-strategy.md` first.
