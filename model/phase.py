"""Season-phase correction.

Every rate in `features.py` is a season average, but the solver optimises an
8 gameweek horizon starting at GW1. That is only valid if scoring rates are
stationary across a season. They are not. Some players score at materially
different per-90 rates in GW1-6 than across GW7-38, and the deviation is
stable enough across seasons to be predictable.

Method
------
For each player, in each season with enough minutes on both sides of the split:

    ratio = (GW1-6 points per 90) / (GW7-38 points per 90)

Computed per-90 so the minutes and injury confound is removed. `features.py`
already models minutes separately via `p_start` and `xmins`, so a correction
built on raw point totals would double-count them.

The per-player mean ratio is shrunk toward 1.0 and clipped, then applied to the
ATTACKING component of xP only (goals and assists). Clean sheets, saves, DefCon
and bonus are lumpy and team-driven, and the apparent phase signal in them is
mostly noise. Restricting the scope also stops the solver reaching for
front-loaded goalkeepers, which was the tell that the wider version overfitted.

League median multiplier is ~0.98, so this redistributes rather than inflates.

Cold-start device
-----------------
This exists because GW1-8 has no 2026/27 match data and the model is running on
2025/26 season averages. Once real match data exists, around GW4 to GW6, the
rates themselves become current and this correction should be retired. Set
`PHASE_ENABLED = False` or pass `enabled=False`.

See `claude/02-strategy.md` for the finding and the sensitivity analysis.
"""

import pathlib

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
D = ROOT / "data"
CACHE = D / "phase_multipliers.csv"

PHASE_ENABLED = True

# Seasons used to fit the ratio. Four is the practical maximum: earlier seasons
# predate enough of the current player pool to be worth the join.
SEASONS = ["2022-23", "2023-24", "2024-25", "2025-26"]
VAASTAV = "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data"

SPLIT_GW = 6          # GW1..SPLIT_GW is "early"
SHRINK_K = 2.0        # pseudo-observations pulling toward 1.0
CLIP = (0.75, 1.50)
MIN_EARLY_MINS = 270  # 3 full matches
MIN_LATE_MINS = 900   # 10 full matches

# Full strength for the measured window, then decay to nothing by GW9.
TAPER = {1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0, 5: 1.0, 6: 1.0, 7: 0.66, 8: 0.33}


def _season_frame(season):
    """Per-player early vs late points-per-90 for one season."""
    url = f"{VAASTAV}/{season}/gws/merged_gw.csv"
    local = D / f"merged_gw_{season}.csv"
    src = local if local.exists() else url
    d = pd.read_csv(src, low_memory=False)
    d = d[d["GW"] <= 38]

    early = (d[d["GW"] <= SPLIT_GW].groupby("name")
             .agg(e_pts=("total_points", "sum"), e_min=("minutes", "sum")))
    late = (d[d["GW"] > SPLIT_GW].groupby("name")
            .agg(l_pts=("total_points", "sum"), l_min=("minutes", "sum")))

    m = early.join(late, how="inner")
    m = m[(m["e_min"] > MIN_EARLY_MINS) & (m["l_min"] > MIN_LATE_MINS)]
    e90 = m["e_pts"] / (m["e_min"] / 90.0)
    l90 = m["l_pts"] / (m["l_min"] / 90.0)
    m["ratio"] = (e90 / l90.replace(0, np.nan))
    return m.reset_index()[["name", "ratio"]].dropna()


def build_multipliers(refresh=False):
    """Return a dict of {player code: multiplier}.

    Joins on player name within each season, then maps to the stable `code` via
    the current-season raw file, which is how players join across seasons.
    """
    if CACHE.exists() and not refresh:
        c = pd.read_csv(CACHE)
        return dict(zip(c["code"].astype(int), c["mult"]))

    frames = [_season_frame(s) for s in SEASONS]
    a = pd.concat(frames, ignore_index=True)

    g = a.groupby("name").agg(n=("ratio", "size"), raw=("ratio", "mean"))
    g["mult"] = (((g["n"] * g["raw"]) + SHRINK_K * 1.0)
                 / (g["n"] + SHRINK_K)).clip(*CLIP)

    raw_path = D / "hist_players_2526.csv"
    raw = (pd.read_csv(raw_path) if raw_path.exists()
           else pd.read_csv(f"{VAASTAV}/2025-26/players_raw.csv"))
    raw["full"] = raw["first_name"].str.strip() + " " + raw["second_name"].str.strip()
    name_to_code = dict(zip(raw["full"], raw["code"]))

    g = g.reset_index()
    g["code"] = g["name"].map(name_to_code)
    g = g.dropna(subset=["code"])
    g["code"] = g["code"].astype(int)

    CACHE.parent.mkdir(parents=True, exist_ok=True)
    g[["code", "name", "n", "raw", "mult"]].to_csv(CACHE, index=False)
    return dict(zip(g["code"], g["mult"]))


def apply_phase(df, mults=None, enabled=PHASE_ENABLED):
    """Scale the attacking component of xP by the tapered phase multiplier.

    `df` is the player-gameweek frame from `features.build()`. Requires columns
    `code`, `gw`, `xp` and `xp_att`. Adds `xp_prephase` and `phase_mult` so the
    uncorrected number stays inspectable.
    """
    df = df.copy()
    df["xp_prephase"] = df["xp"]
    if not enabled:
        df["phase_mult"] = 1.0
        return df

    if mults is None:
        mults = build_multipliers()

    df["phase_mult"] = df["code"].map(mults).fillna(1.0)
    taper = df["gw"].map(TAPER).fillna(0.0)
    eff = 1.0 + (df["phase_mult"] - 1.0) * taper
    df["xp"] = (df["xp"] - df["xp_att"] + df["xp_att"] * eff).clip(lower=0)
    return df


if __name__ == "__main__":
    m = build_multipliers(refresh=True)
    s = pd.Series(m)
    print(f"{len(s)} players with a season-phase multiplier")
    print(f"league median {s.median():.3f}  (should sit near 1.0)")
    c = pd.read_csv(CACHE).sort_values("mult", ascending=False)
    print("\nmost front-loaded (n>=3):")
    print(c[c["n"] >= 3].head(8)[["name", "n", "raw", "mult"]].round(2).to_string(index=False))
    print("\nmost back-loaded (n>=3):")
    print(c[c["n"] >= 3].tail(6)[["name", "n", "raw", "mult"]].round(2).to_string(index=False))
