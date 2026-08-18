# Model code

Lives in the mirror repo on purpose. The Claude cloud container is ephemeral, so a
scheduled session starts with an empty filesystem. Keeping the model here means any
fresh session can fetch it from raw.githubusercontent and reproduce the analysis.

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

## Validation, run 18 Aug 2026

Fitted on 2025/26 GW1-19, tested on GW20-38, nothing from the test half used in fitting.

- per-match Spearman 0.610, MAE 21.2% better than predicting the mean
- season-total Spearman 0.825 across 780 players (FWD 0.874, MID 0.853, DEF 0.814, GK 0.740)
- top 30 by predicted xP averaged 73.9 actual points vs 44.1 for the eligible pool

Every large over-prediction was a minutes failure, not a football failure. Re-run
`backtest.py` whenever the model changes and keep those numbers honest.
