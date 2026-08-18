"""Build the per-player, per-gameweek expected points table for 2026/27.

Cold start: there is no 2026/27 match data yet, so every rate is estimated from
2025/26 per-match history (vaastav mirror) joined onto current prices, positions
and availability from the live FPL mirror.
"""

import json
import math
import pathlib

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
D = ROOT / "data"

POS = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}
GOAL_PTS = {"GK": 10, "DEF": 6, "MID": 5, "FWD": 4}
CS_PTS = {"GK": 4, "DEF": 4, "MID": 1, "FWD": 0}
DEFCON_THRESHOLD = {"GK": 999, "DEF": 10, "MID": 12, "FWD": 12}

# BPS was rebalanced for 2026/27. Any bonus estimate from 2025/26 is misspecified.
# Haircut it, and tilt by position group in the direction the rebalance points:
# stationary centre-backs lose (CBI cut from 1-per-2 to 1-per-3), keepers and
# attacking players gain (new save categories, tackled-penalty removed).
BONUS_CONFIDENCE = 0.75
BONUS_POS_TILT = {"GK": 1.15, "DEF": 0.80, "MID": 1.05, "FWD": 1.05}


def load():
    players = pd.DataFrame(json.load(open(D / "players.json")))
    teams = pd.DataFrame(json.load(open(D / "teams.json")))
    fixtures = pd.DataFrame(json.load(open(D / "fixtures.json")))
    hist = pd.read_csv(D / "merged_gw_2526.csv")
    old = pd.read_csv(D / "hist_players_2526.csv")
    return players, teams, fixtures, hist, old


def per_match_history(hist, old, players):
    """Attach the stable player `code` to 2025/26 match rows so they join to 2026/27."""
    id2code = dict(zip(old["id"], old["code"]))
    hist = hist.copy()
    hist["code"] = hist["element"].map(id2code)
    hist = hist.dropna(subset=["code"])
    hist["code"] = hist["code"].astype(int)
    valid = set(players["code"])
    return hist[hist["code"].isin(valid)]


def player_rates(hist, players):
    """Per-90 rates and minutes profile from 2025/26."""
    g = hist.groupby("code")
    played = hist[hist["minutes"] > 0]
    gp = played.groupby("code")

    # A raw starts/38 rate punishes anyone who had an injury spell, which is the
    # wrong signal for a player who is fit now. Drop gameweeks that fall inside a
    # run of 3+ consecutive blanks (almost always injury or suspension) and
    # measure the start rate over the gameweeks he was actually available.
    def fit_start_rate(d):
        d = d.sort_values("GW")
        zero = (d["minutes"] == 0).to_numpy()
        blocked = np.zeros(len(d), dtype=bool)
        i = 0
        while i < len(zero):
            if zero[i]:
                j = i
                while j < len(zero) and zero[j]:
                    j += 1
                if j - i >= 3:
                    blocked[i:j] = True
                i = j
            else:
                i += 1
        avail = d[~blocked]
        if len(avail) < 5:
            return np.nan
        return avail["starts"].mean()

    fit_rate = hist.groupby("code")[["GW", "minutes", "starts"]].apply(fit_start_rate)
    fit_rate.name = "fit_start_rate"

    rates = pd.DataFrame({
        "apps": g.size(),
        "starts_25": g["starts"].sum(),
        "mins_25": g["minutes"].sum(),
        "mins_when_started": played[played["starts"] == 1].groupby("code")["minutes"].mean(),
        "start_rate": g["starts"].mean(),
        "xg": g["expected_goals"].sum(),
        "xa": g["expected_assists"].sum(),
        "xgc": g["expected_goals_conceded"].sum(),
        "goals": g["goals_scored"].sum(),
        "assists": g["assists"].sum(),
        "saves": g["saves"].sum(),
        "bonus": g["bonus"].sum(),
        "yellows": g["yellow_cards"].sum(),
        "reds": g["red_cards"].sum(),
        "pens_missed": g["penalties_missed"].sum(),
        "pens_saved": g["penalties_saved"].sum(),
    })
    m90 = rates["mins_25"].clip(lower=1) / 90.0
    for c in ["xg", "xa", "saves", "bonus", "yellows", "reds"]:
        rates[c + "_90"] = rates[c] / m90
    # Blend raw xG/xA with actual output. Pure xG under-rates elite finishers and
    # over-rates volume shooters; 75/25 toward xG is the usual compromise.
    rates["g_90"] = 0.75 * rates["xg_90"] + 0.25 * (rates["goals"] / m90)
    rates["a_90"] = 0.75 * rates["xa_90"] + 0.25 * (rates["assists"] / m90)

    # DefCon is a threshold, not a rate. Use the empirical per-match hit rate
    # conditional on starting, which is what actually matters.
    starts_only = hist[hist["starts"] == 1]
    dc = starts_only.groupby("code").apply(
        lambda d: pd.Series({
            "dc_starts": len(d),
            "dc_mean": d["defensive_contribution"].mean(),
            "dc_hit_def": (d["defensive_contribution"] >= 10).mean(),
            "dc_hit_mid": (d["defensive_contribution"] >= 12).mean(),
        }), include_groups=False)
    rates = rates.join(dc).join(fit_rate)
    # Which club he played for in 2025/26, so a transfer can be adjusted for.
    rates = rates.join(hist.groupby("code")["team"].agg(lambda s: s.mode().iloc[0]).rename("old_team"))
    return rates


def team_strength(teams, hist):
    """Team attack (xG for) and defence (xG against) per match, home and away.

    The API's granular strength_attack_* / strength_defence_* fields are all zero
    pre-season, so they are useless here. Derive real numbers from 2025/26 match
    data instead: team xG is the sum of player expected_goals in a fixture, team
    xGC is the (team-level, replicated) expected_goals_conceded.

    Promoted sides have no PL history, so they fall back to a promoted-team prior.
    Everything is shrunk toward the league mean because squads turn over.
    """
    g = hist.groupby(["team", "fixture", "was_home"]).agg(
        xg=("expected_goals", "sum"), xgc=("expected_goals_conceded", "max"))
    g = g.reset_index()
    obs = g.groupby(["team", "was_home"]).agg(xg=("xg", "mean"), xgc=("xgc", "mean")).unstack()
    obs.columns = [f"{a}_{'home' if b else 'away'}" for a, b in obs.columns]

    ts = teams.set_index("id")[["name", "short_name", "strength_overall_home", "strength_overall_away"]].copy()
    ts = ts.join(obs, on="name")

    # Promoted-side prior, roughly what a newly promoted team has averaged.
    PROMOTED = {"xg_home": 1.05, "xg_away": 0.85, "xgc_home": 1.60, "xgc_away": 1.90}
    ts["promoted"] = ts["xg_home"].isna()
    for c, v in PROMOTED.items():
        ts[c] = ts[c].fillna(v)

    # Shrink 30% toward the league mean: a summer of transfers moves teams around.
    SHRINK = 0.30
    for c in PROMOTED:
        ts[c] = (1 - SHRINK) * ts[c] + SHRINK * ts[c].mean()

    for c in PROMOTED:
        ts[c + "_rel"] = ts[c] / ts[c].mean()
    return ts


# Movers keep their OLD club's start rate under the shipped model, which is wrong
# in a predictable direction: a player nailed at a mid-table side is not nailed at
# a top side. Blend the inherited rate with the price-rank pecking-order prior at
# the NEW club. MOVER_BLEND = weight on the inherited rate (1.0 reproduces shipped).
MOVER_BLEND = 0.50


def build(horizon_start=1, horizon=8, mover_blend=None):
    mover_blend = MOVER_BLEND if mover_blend is None else mover_blend
    players, teams, fixtures, hist, old = load()
    hist = per_match_history(hist, old, players)
    rates = player_rates(hist, players)
    ts = team_strength(teams, hist)

    p = players.copy()
    p["pos"] = p["element_type"].map(POS)
    p["price"] = p["now_cost"] / 10.0
    p = p.join(rates, on="code", rsuffix="_h25")

    # Availability
    p["avail"] = 1.0
    p.loc[p["status"].isin(["i", "s", "u", "n"]), "avail"] = 0.0
    cop = pd.to_numeric(p["chance_of_playing_next_round"], errors="coerce")
    p.loc[cop.notna(), "avail"] = cop[cop.notna()] / 100.0
    p.loc[p["status"] == "d", "avail"] = p.loc[p["status"] == "d", "avail"].fillna(0.5).clip(upper=0.75)

    # Minutes model. Anyone with no 2025/26 PL history (new signings, promoted
    # club players) gets a price-informed prior rather than being zeroed out.
    price_rank = p.groupby("team")["price"].rank(pct=True)
    prior_start = (0.15 + 0.75 * price_rank).clip(0.05, 0.90)
    # Weight the availability-adjusted rate most, keep some pull from the raw
    # rate so a chronically injured player is not treated as nailed.
    base = 0.75 * p["fit_start_rate"] + 0.25 * p["start_rate"]
    base = base.fillna(p["fit_start_rate"]).fillna(p["start_rate"]).fillna(prior_start)
    p["p_start"] = base.clip(0, 0.97) * p["avail"]
    p["_prior_start"] = prior_start
    p["_base_start"] = base
    p["mins_if_start"] = p["mins_when_started"].fillna(78.0).clip(45, 90)
    # Small cameo probability for non-starters.
    p["p_cameo"] = ((1 - p["p_start"]) * 0.30 * p["avail"]).clip(0, 0.5)
    p["xmins"] = p["p_start"] * p["mins_if_start"] + p["p_cameo"] * 22

    # Rate fallbacks for players with no history.
    pos_median = p.groupby("pos")[["g_90", "a_90", "saves_90", "bonus_90", "yellows_90"]].transform("median")
    for c in ["g_90", "a_90", "saves_90", "bonus_90", "yellows_90"]:
        p[c] = p[c].fillna(pos_median[c] * 0.6)
    p["dc_hit"] = np.where(p["pos"] == "DEF", p["dc_hit_def"], p["dc_hit_mid"])
    dc_pos_median = p.groupby("pos")["dc_hit"].transform("median")
    p["dc_hit"] = p["dc_hit"].fillna(dc_pos_median * 0.6).fillna(0.0)
    p.loc[p["pos"] == "GK", "dc_hit"] = 0.0

    # Transfer adjustment. A player's 2025/26 attacking rate was produced by his
    # old team's chance creation. Moving clubs changes that, and roughly a fifth
    # of the player pool moves each summer. Scale by the ratio of new team to old
    # team attacking strength, clipped so one transfer cannot dominate the model.
    team_xg = ((ts["xg_home"] + ts["xg_away"]) / 2)
    xg_by_name = dict(zip(ts["name"], team_xg))
    league_xg = team_xg.mean()
    new_xg = p["team"].map(dict(zip(ts.index, team_xg)))
    old_xg = p["old_team"].map(xg_by_name)
    p["club_move_mult"] = (new_xg / old_xg).fillna(1.0).clip(0.70, 1.50)
    p["moved"] = p["old_team"].notna() & (p["old_team"] != p["team"].map(dict(zip(ts.index, ts["name"]))))
    p.loc[~p["moved"].fillna(False), "club_move_mult"] = 1.0

    # Minutes adjustment for movers. The attacking adjustment above already accepts
    # that a transfer changes a player's context; leaving p(start) untouched is
    # inconsistent, and biased upward for anyone moving to a stronger squad.
    mv = p["moved"].fillna(False)
    blended = mover_blend * p["_base_start"] + (1 - mover_blend) * p["_prior_start"]
    p.loc[mv, "p_start"] = blended[mv].clip(0, 0.97) * p.loc[mv, "avail"]
    p["p_cameo"] = ((1 - p["p_start"]) * 0.30 * p["avail"]).clip(0, 0.5)
    p["xmins"] = p["p_start"] * p["mins_if_start"] + p["p_cameo"] * 22
    for c in ["g_90", "a_90"]:
        p[c] = p[c] * p["club_move_mult"]

    fx = fixtures[fixtures["event"].between(horizon_start, horizon_start + horizon - 1)].copy()
    by_team = {t: fx[(fx["team_h"] == t) | (fx["team_a"] == t)] for t in teams["id"]}

    rows = []
    for _, pl in p.iterrows():
        tid = pl["team"]
        for _, f in by_team[tid].iterrows():
            home = f["team_h"] == tid
            opp = f["team_a"] if home else f["team_h"]
            fdr = f["team_h_difficulty"] if home else f["team_a_difficulty"]
            ha = "home" if home else "away"
            opp_ha = "away" if home else "home"

            # Attacking multiplier. The player's own g_90/a_90 already embeds his
            # team's attacking output averaged across all opponents, so adjusting
            # by our own attack strength again would double-count. Only the
            # fixture-specific parts apply: opponent defence and venue.
            opp_def = ts.loc[opp, f"xgc_{opp_ha}_rel"]
            att_mult = float(opp_def) * (1.08 if home else 0.94)

            # Expected goals conceded by our player's team in this fixture.
            own_def = ts.loc[tid, f"xgc_{ha}"]
            opp_att = ts.loc[opp, f"xg_{opp_ha}_rel"]
            xgc = float(own_def * opp_att)

            m90 = pl["xmins"] / 90.0
            pos = pl["pos"]
            p_play = min(1.0, pl["p_start"] + pl["p_cameo"])
            p_60 = pl["p_start"] * (0.90 if pl["mins_if_start"] > 70 else 0.55)

            xp_apps = p_60 * 2 + (p_play - p_60) * 1
            xp_goals = pl["g_90"] * m90 * att_mult * GOAL_PTS[pos]
            xp_assists = pl["a_90"] * m90 * att_mult * 3
            p_cs = math.exp(-xgc) * p_60  # clean sheet only pays if 60+ minutes
            xp_cs = p_cs * CS_PTS[pos]
            xp_conc = -(xgc * m90 / 2.0) if pos in ("GK", "DEF") else 0.0
            xp_saves = (pl["saves_90"] * m90 / 3.0) if pos == "GK" else 0.0
            xp_defcon = pl["dc_hit"] * pl["p_start"] * 2.0
            xp_bonus = pl["bonus_90"] * m90 * BONUS_CONFIDENCE * BONUS_POS_TILT[pos]
            xp_cards = -pl["yellows_90"] * m90

            rows.append({
                "code": pl["code"], "id": pl["id"], "name": pl["web_name"], "pos": pos,
                "team": tid, "price": pl["price"], "sel": float(pl["selected_by_percent"]),
                "gw": int(f["event"]), "opp": opp, "home": home, "fdr": fdr,
                "xmins": pl["xmins"], "p_start": pl["p_start"],
                "xp": xp_apps + xp_goals + xp_assists + xp_cs + xp_conc + xp_saves
                      + xp_defcon + xp_bonus + xp_cards,
                "xp_att": xp_goals + xp_assists, "xp_cs": xp_cs, "xp_defcon": xp_defcon,
                "xp_bonus": xp_bonus, "xp_apps": xp_apps,
                "status": pl["status"], "news": pl["news"] or "",
            })

    df = pd.DataFrame(rows)
    df["xp"] = df["xp"].clip(lower=0)
    return df, p


if __name__ == "__main__":
    df, p = build()
    df.to_parquet(ROOT / "out" / "xp.parquet")
    print(f"{len(df):,} player-gameweek rows, GW{df.gw.min()}-{df.gw.max()}")
    gw1 = df[df.gw == 1].nlargest(20, "xp")
    print(gw1[["name", "pos", "price", "sel", "opp", "home", "xmins", "xp",
               "xp_att", "xp_cs", "xp_defcon", "xp_bonus"]].round(2).to_string(index=False))
