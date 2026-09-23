"""2026/27 team strength blend for features.team_strength().

The problem this solves. `features.team_strength()` derives team xG and xGC
entirely from 2025/26. Early in a new season that makes every improved or
degraded defence invisible.

The naive fix (blend in raw 2026/27 xGC) is worse than it looks, because after
a few matches a team's raw defensive record is dominated by who they happened to
play. So this module does two things:

1. OPPONENT-ADJUST. Fit multiplicative attack and defence ratings by iterative
   proportional fitting, so a team is credited for what it did relative to the
   opposition it faced rather than in absolute terms.
2. SHRINK BY SAMPLE SIZE. beta = n / (n + K), n = matches played, K = prior
   strength in pseudo-matches. Rises on its own; no weekly tuning.

Home/away split is taken from the 2025/26 shape rather than re-estimated.

Committed 24 Sep 2026 from the project copy (claude/team_blend.py). Callers must
recompute the *_rel columns afterwards; features.add_relative() does that.
"""

import numpy as np
import pandas as pd

BLEND_K = 6.0        # pseudo-matches of 2025/26 prior. beta = n/(n+K)
ADJUST_ITERS = 12    # iterative proportional fitting passes
RATING_CLIP = (0.55, 1.80)
MIN_MATCHES = 3      # below this, no blend at all


def _team_totals(players, fixtures, teams):
    """Season-to-date xG for / xGC against per team, plus each team's opponent list."""
    tid = list(teams["id"])
    xg = {t: 0.0 for t in tid}
    xgc = {t: 0.0 for t in tid}
    for p in players.itertuples():
        xg[p.team] = xg.get(p.team, 0.0) + float(p.expected_goals)
        if p.element_type in (1, 2):
            # team-level figure, replicated across defenders, so take the max
            xgc[p.team] = max(xgc.get(p.team, 0.0), float(p.expected_goals_conceded))
    opps = {t: [] for t in tid}
    for f in fixtures.itertuples():
        if not getattr(f, "finished", False):
            continue
        opps[f.team_h].append((f.team_a, True))
        opps[f.team_a].append((f.team_h, False))
    return xg, xgc, opps


def fit_ratings(players, fixtures, teams):
    """Opponent-adjusted multiplicative attack / defence ratings, mean 1.0."""
    xg, xgc, opps = _team_totals(players, fixtures, teams)
    tid = [t for t in opps if len(opps[t]) >= MIN_MATCHES]
    if not tid:
        return None
    n = {t: len(opps[t]) for t in tid}
    lg_xg = np.mean([xg[t] / n[t] for t in tid])          # league mean xG per match
    # Guard the replicated-xGC convention: if it ever breaks, defence ratings go to zero.
    assert sum(xgc[t] for t in tid) > 0, "team xGC is zero: API convention may have changed"

    att = {t: 1.0 for t in tid}
    dfc = {t: 1.0 for t in tid}
    for _ in range(ADJUST_ITERS):
        for t in tid:
            exp = sum(lg_xg * dfc.get(o, 1.0) for o, _ in opps[t] if o in dfc)
            if exp > 0:
                att[t] = np.clip(xg[t] / exp, *RATING_CLIP)
        m = np.mean(list(att.values()))
        att = {t: v / m for t, v in att.items()}
        for t in tid:
            exp = sum(lg_xg * att.get(o, 1.0) for o, _ in opps[t] if o in att)
            if exp > 0:
                dfc[t] = np.clip(xgc[t] / exp, *RATING_CLIP)
        m = np.mean(list(dfc.values()))
        dfc = {t: v / m for t, v in dfc.items()}

    return {"att": att, "dfc": dfc, "n": n, "lg_xg": lg_xg,
            "raw_xg": {t: xg[t] / n[t] for t in tid},
            "raw_xgc": {t: xgc[t] / n[t] for t in tid}}


def blend(ts, players, fixtures, teams, k=BLEND_K):
    """Blend opponent-adjusted 2026/27 ratings into a 2025/26 `team_strength` frame."""
    r = fit_ratings(players, fixtures, teams)
    if r is None:
        return ts
    ts = ts.copy()
    sn = dict(zip(teams["id"], teams["short_name"]))
    lg = r["lg_xg"]
    for tid, nm in r["n"].items():
        rows = ts.index[ts["short_name"] == sn[tid]]
        if not len(rows):
            continue
        beta = nm / (nm + k)
        cur_xg = lg * r["att"][tid]
        cur_xgc = lg * r["dfc"][tid]
        for row in rows:
            base_xg = (ts.loc[row, "xg_home"] + ts.loc[row, "xg_away"]) / 2
            base_xgc = (ts.loc[row, "xgc_home"] + ts.loc[row, "xgc_away"]) / 2
            for col, base, cur in [("xg_home", base_xg, cur_xg), ("xg_away", base_xg, cur_xg),
                                   ("xgc_home", base_xgc, cur_xgc), ("xgc_away", base_xgc, cur_xgc)]:
                shape = ts.loc[row, col] / base if base > 0 else 1.0
                ts.loc[row, col] = ((1 - beta) * ts.loc[row, col]) + (beta * cur * shape)
    return ts
