"""Walk-forward validation of the expected points model on 2025/26.

Fit every rate on GW1-19 only, then predict GW20-38 and compare with what
actually happened. Strictly out of sample: nothing from the second half of the
season touches the estimates.
"""

import math
import pathlib

import numpy as np
import pandas as pd
from scipy import stats

ROOT = pathlib.Path(__file__).resolve().parent.parent

GOAL_PTS = {"GK": 10, "DEF": 6, "MID": 5, "FWD": 4}
CS_PTS = {"GK": 4, "DEF": 4, "MID": 1, "FWD": 0}
SPLIT = 19
BONUS_CONF = 1.0  # no BPS haircut here: 2025/26 rules applied all season


def main():
    h = pd.read_csv(ROOT / "data" / "merged_gw_2526.csv")
    h["pos"] = h["position"]
    train = h[h["GW"] <= SPLIT]
    test = h[h["GW"] > SPLIT].copy()

    # Team strength from the first half only.
    tg = train.groupby(["team", "fixture", "was_home"]).agg(
        xg=("expected_goals", "sum"), xgc=("expected_goals_conceded", "max")).reset_index()
    ts = tg.groupby(["team", "was_home"]).agg(xg=("xg", "mean"), xgc=("xgc", "mean")).unstack()
    ts.columns = [f"{a}_{'home' if b else 'away'}" for a, b in ts.columns]
    for c in list(ts.columns):
        ts[c] = 0.7 * ts[c] + 0.3 * ts[c].mean()
        ts[c + "_rel"] = ts[c] / ts[c].mean()
    id2team = train.groupby("element")["team"].agg(lambda s: s.mode().iloc[0])
    tname = dict(zip(train["opponent_team"], train["team"]))  # not reliable; rebuilt below

    # opponent_team is a team id; map ids to names using the team/fixture pairs.
    pair = train[["team", "fixture", "was_home"]].drop_duplicates()
    fx = pair.merge(pair, on="fixture", suffixes=("", "_o"))
    fx = fx[fx["team"] != fx["team_o"]]
    opp_ids = train[["element", "fixture", "opponent_team"]].drop_duplicates()
    lookup = train[["fixture", "team", "opponent_team"]].drop_duplicates()
    id_to_name = {}
    for _, r in lookup.iterrows():
        row = fx[(fx["fixture"] == r["fixture"]) & (fx["team"] == r["team"])]
        if len(row):
            id_to_name[r["opponent_team"]] = row.iloc[0]["team_o"]

    g = train.groupby("element")
    played = train[train["minutes"] > 0]
    m90 = train.groupby("element")["minutes"].sum().clip(lower=1) / 90

    r = pd.DataFrame({
        "pos": g["pos"].first(),
        "start_rate": g["starts"].mean(),
        "mins_if_start": train[train["starts"] == 1].groupby("element")["minutes"].mean(),
        "g_90": (0.75 * g["expected_goals"].sum() + 0.25 * g["goals_scored"].sum()) / m90,
        "a_90": (0.75 * g["expected_assists"].sum() + 0.25 * g["assists"].sum()) / m90,
        "saves_90": g["saves"].sum() / m90,
        "bonus_90": g["bonus"].sum() / m90,
        "yellows_90": g["yellow_cards"].sum() / m90,
    })
    starts = train[train["starts"] == 1].groupby("element")["defensive_contribution"]
    r["dc_hit_def"] = starts.apply(lambda s: (s >= 10).mean())
    r["dc_hit_mid"] = starts.apply(lambda s: (s >= 12).mean())
    r["dc_hit"] = np.where(r["pos"] == "DEF", r["dc_hit_def"], r["dc_hit_mid"])
    r.loc[r["pos"] == "GK", "dc_hit"] = 0.0
    r["mins_if_start"] = r["mins_if_start"].fillna(78).clip(45, 90)
    r = r.fillna(0.0)

    test = test[test["element"].isin(r.index)].copy()
    test["opp_name"] = test["opponent_team"].map(id_to_name)
    test = test.dropna(subset=["opp_name"])
    test = test[test["opp_name"].isin(ts.index) & test["team"].isin(ts.index)]

    preds = []
    for row in test.itertuples():
        pl = r.loc[row.element]
        pos = pl["pos"]
        ha, oha = ("home", "away") if row.was_home else ("away", "home")
        att = ts.loc[row.opp_name, f"xgc_{oha}_rel"] * (1.08 if row.was_home else 0.94)
        xgc = ts.loc[row.team, f"xgc_{ha}"] * ts.loc[row.opp_name, f"xg_{oha}_rel"]

        p_start = pl["start_rate"]
        p_cameo = (1 - p_start) * 0.30
        xmins = p_start * pl["mins_if_start"] + p_cameo * 22
        mm = xmins / 90
        p_play = min(1.0, p_start + p_cameo)
        p_60 = p_start * (0.90 if pl["mins_if_start"] > 70 else 0.55)

        xp = (p_60 * 2 + (p_play - p_60)
              + pl["g_90"] * mm * att * GOAL_PTS[pos]
              + pl["a_90"] * mm * att * 3
              + math.exp(-xgc) * p_60 * CS_PTS[pos]
              + (-(xgc * mm / 2) if pos in ("GK", "DEF") else 0)
              + (pl["saves_90"] * mm / 3 if pos == "GK" else 0)
              + pl["dc_hit"] * p_start * 2
              + pl["bonus_90"] * mm * BONUS_CONF
              - pl["yellows_90"] * mm)
        preds.append(max(xp, 0.0))

    test["pred"] = preds
    print(f"out-of-sample rows: {len(test):,} (GW{SPLIT+1}-38)\n")

    sp = stats.spearmanr(test["pred"], test["total_points"])
    pe = stats.pearsonr(test["pred"], test["total_points"])
    print(f"per-match  spearman {sp.statistic:.3f}   pearson {pe.statistic:.3f}")
    print(f"calibration: mean predicted {test['pred'].mean():.2f} vs actual {test['total_points'].mean():.2f}")
    mae = (test["pred"] - test["total_points"]).abs().mean()
    naive = (test["total_points"].mean() - test["total_points"]).abs().mean()
    print(f"MAE {mae:.2f} vs predict-the-mean {naive:.2f}  ({100*(1-mae/naive):.1f}% better)\n")

    agg = test.groupby("element").agg(pred=("pred", "sum"), actual=("total_points", "sum"),
                                      name=("name", "first"), pos=("pos", "first"))
    sp2 = stats.spearmanr(agg["pred"], agg["actual"])
    print(f"season-total (GW20-38) spearman {sp2.statistic:.3f} over {len(agg)} players")
    for pos in ["GK", "DEF", "MID", "FWD"]:
        a = agg[agg["pos"] == pos]
        print(f"  {pos}: spearman {stats.spearmanr(a['pred'], a['actual']).statistic:.3f}  n={len(a)}")

    top = agg.nlargest(30, "pred")
    print(f"\ntop-30 by predicted: mean actual {top['actual'].mean():.1f} pts "
          f"vs squad-eligible mean {agg[agg['pred'] > 20]['actual'].mean():.1f}")
    print(f"\nbiggest misses (predicted high, scored low):")
    agg["err"] = agg["pred"] - agg["actual"]
    print(agg.nlargest(8, "err")[["name", "pos", "pred", "actual"]].round(1).to_string())
    print(f"\nbiggest misses (predicted low, scored high):")
    print(agg.nsmallest(8, "err")[["name", "pos", "pred", "actual"]].round(1).to_string())


if __name__ == "__main__":
    main()
