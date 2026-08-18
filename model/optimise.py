"""Initial squad optimiser (GW1). MILP over an 8 gameweek horizon.

Objective: decayed expected points of the starting XI plus captain, with a small
weight on bench cover and money left in the bank.
"""

import pathlib

import pandas as pd
import pulp

ROOT = pathlib.Path(__file__).resolve().parent.parent

BUDGET = 100.0
SQUAD = {"GK": 2, "DEF": 5, "MID": 5, "FWD": 3}
XI_MIN = {"GK": 1, "DEF": 3, "MID": 2, "FWD": 1}
XI_MAX = {"GK": 1, "DEF": 5, "MID": 5, "FWD": 3}

DECAY = 0.90
VCAP_WEIGHT = 0.10
ITB_VALUE = 0.08          # points per £0.1m left in the bank
BENCH_WEIGHT = {"GK": 0.03, "DEF": 0.09, "MID": 0.09, "FWD": 0.09}
MAX_PER_CLUB = 3


def solve(xp, horizon=8, banned=(), locked=(), budget=BUDGET, msg=False):
    xp = xp[xp["gw"] <= xp["gw"].min() + horizon - 1].copy()
    gws = sorted(xp["gw"].unique())

    # Players who cannot return inside the horizon are dead weight in a 15-man
    # squad, so exclude anyone flagged unavailable with no expected return.
    meta = xp.groupby("id").agg(
        name=("name", "first"), pos=("pos", "first"), team=("team", "first"),
        price=("price", "first"), sel=("sel", "first"), status=("status", "first"),
        news=("news", "first"), total=("xp", "sum")).reset_index()
    ids = [i for i in meta["id"] if i not in banned]
    m = meta.set_index("id")

    pts = {(r.id, r.gw): r.xp for r in xp.itertuples()}
    for i in ids:
        for gw in gws:
            pts.setdefault((i, gw), 0.0)

    prob = pulp.LpProblem("fpl_initial_squad", pulp.LpMaximize)
    squad = pulp.LpVariable.dicts("s", ids, cat="Binary")
    line = pulp.LpVariable.dicts("l", (ids, gws), cat="Binary")
    cap = pulp.LpVariable.dicts("c", (ids, gws), cat="Binary")
    vc = pulp.LpVariable.dicts("v", (ids, gws), cat="Binary")

    spend = pulp.lpSum(m.loc[i, "price"] * squad[i] for i in ids)

    obj = []
    for gw in gws:
        d = DECAY ** (gw - gws[0])
        for i in ids:
            x = pts[(i, gw)]
            w = BENCH_WEIGHT[m.loc[i, "pos"]]
            obj.append(d * x * line[i][gw])
            obj.append(d * x * cap[i][gw])
            obj.append(d * VCAP_WEIGHT * x * vc[i][gw])
            obj.append(d * w * x * (squad[i] - line[i][gw]))
    prob += pulp.lpSum(obj) + ITB_VALUE * 10 * (budget - spend)

    prob += pulp.lpSum(squad[i] for i in ids) == 15
    for pos, n in SQUAD.items():
        prob += pulp.lpSum(squad[i] for i in ids if m.loc[i, "pos"] == pos) == n
    prob += spend <= budget
    for t in m["team"].unique():
        prob += pulp.lpSum(squad[i] for i in ids if m.loc[i, "team"] == t) <= MAX_PER_CLUB
    for i in locked:
        prob += squad[i] == 1

    for gw in gws:
        prob += pulp.lpSum(line[i][gw] for i in ids) == 11
        for pos in SQUAD:
            n = pulp.lpSum(line[i][gw] for i in ids if m.loc[i, "pos"] == pos)
            prob += n >= XI_MIN[pos]
            prob += n <= XI_MAX[pos]
        prob += pulp.lpSum(cap[i][gw] for i in ids) == 1
        prob += pulp.lpSum(vc[i][gw] for i in ids) == 1
        for i in ids:
            prob += line[i][gw] <= squad[i]
            prob += cap[i][gw] <= line[i][gw]
            prob += vc[i][gw] <= line[i][gw]
            prob += cap[i][gw] + vc[i][gw] <= 1

    prob.solve(pulp.PULP_CBC_CMD(msg=msg, timeLimit=300))
    status = pulp.LpStatus[prob.status]

    picked = [i for i in ids if squad[i].value() > 0.5]
    out = m.loc[picked].reset_index()
    out["gw1_xp"] = [pts[(i, gws[0])] for i in picked]
    out["horizon_xp"] = [sum(pts[(i, g)] for g in gws) for i in picked]
    out["xi_gw1"] = [line[i][gws[0]].value() > 0.5 for i in picked]
    out["cap_gw1"] = [cap[i][gws[0]].value() > 0.5 for i in picked]
    out["vc_gw1"] = [vc[i][gws[0]].value() > 0.5 for i in picked]

    plan = []
    for gw in gws:
        xi = [i for i in picked if line[i][gw].value() > 0.5]
        c = [i for i in picked if cap[i][gw].value() > 0.5][0]
        plan.append({"gw": gw, "captain": m.loc[c, "name"],
                     "xi_xp": round(sum(pts[(i, gw)] for i in xi), 2),
                     "cap_xp": round(pts[(c, gw)], 2)})

    return {"status": status, "squad": out, "plan": pd.DataFrame(plan),
            "spend": round(float(spend.value()), 1),
            "objective": round(pulp.value(prob.objective), 2)}


def show(res):
    s = res["squad"].copy()
    order = {"GK": 0, "DEF": 1, "MID": 2, "FWD": 3}
    s["o"] = s["pos"].map(order)
    s = s.sort_values(["xi_gw1", "o", "gw1_xp"], ascending=[False, True, False])
    s["role"] = ""
    s.loc[s["cap_gw1"], "role"] = "(C)"
    s.loc[s["vc_gw1"], "role"] = "(V)"
    print(f"status={res['status']}  spend=£{res['spend']}m  bank=£{round(100 - res['spend'], 1)}m")
    print("\nSTARTING XI")
    print(s[s["xi_gw1"]][["name", "pos", "price", "sel", "gw1_xp", "horizon_xp", "role"]]
          .round(2).to_string(index=False))
    print("\nBENCH")
    print(s[~s["xi_gw1"]][["name", "pos", "price", "sel", "gw1_xp", "horizon_xp"]]
          .round(2).to_string(index=False))
    print("\nHORIZON PLAN")
    print(res["plan"].to_string(index=False))


if __name__ == "__main__":
    xp = pd.read_parquet(ROOT / "out" / "xp.parquet")
    res = solve(xp)
    show(res)
    res["squad"].to_csv(ROOT / "out" / "gw1_squad.csv", index=False)
