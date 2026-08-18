"""Weekly transfer optimiser: decide what to do with an existing squad.

Solved as a small set of forced-transfer-count problems (hold, 1, 2, 3) rather
than one free-form model, so the output is a comparison Rhys can audit rather
than a single opaque answer.

Simplification worth knowing: transfers are applied once, before the first
gameweek of the horizon, and the resulting squad is held for the whole horizon.
Future transfers are not modelled. That makes the optimiser slightly conservative
about moves whose value depends on a follow-up move, which is the safer bias.
"""

import argparse
import json
import pathlib

import pandas as pd
import pulp

from optimise import (BUDGET, SQUAD, XI_MIN, XI_MAX, DECAY, VCAP_WEIGHT,
                      ITB_VALUE, BENCH_WEIGHT, MAX_PER_CLUB)

ROOT = pathlib.Path(__file__).resolve().parent.parent

HIT_COST = 4.0
# What a banked free transfer is worth in points. This is the hurdle every move
# must clear before it is worth making at all, and it is deliberately high: a
# static squad held all season would have finished rank 386 last year, so
# transfer churn is a small residual, not the main event.
FT_VALUE = {0: 0.0, 1: 1.5, 2: 2.0, 3: 1.6, 4: 1.3, 5: 1.1}


def sell_value(buy_price, now_price):
    """FPL takes 50% of any profit, rounded down to the nearest £0.1m."""
    if now_price <= buy_price:
        return now_price
    profit = round((now_price - buy_price) * 10)
    return buy_price + (profit // 2) / 10


def solve_transfers(xp, current, bank, n_transfers, free_transfers,
                    horizon=8, banned=(), locked=(), msg=False):
    """current: {id: buy_price}. Returns the best squad making exactly n_transfers."""
    xp = xp[xp["gw"] <= xp["gw"].min() + horizon - 1].copy()
    gws = sorted(xp["gw"].unique())
    meta = xp.groupby("id").agg(
        name=("name", "first"), pos=("pos", "first"), team=("team", "first"),
        price=("price", "first"), sel=("sel", "first"), status=("status", "first"),
        news=("news", "first")).reset_index()
    m = meta.set_index("id")
    ids = [i for i in meta["id"] if i not in banned or i in current]

    pts = {(r.id, r.gw): r.xp for r in xp.itertuples()}
    for i in ids:
        for gw in gws:
            pts.setdefault((i, gw), 0.0)

    held = {i for i in current if i in m.index}
    sell = {i: sell_value(current[i], float(m.loc[i, "price"])) for i in held}

    prob = pulp.LpProblem("fpl_weekly", pulp.LpMaximize)
    squad = pulp.LpVariable.dicts("s", ids, cat="Binary")
    line = pulp.LpVariable.dicts("l", (ids, gws), cat="Binary")
    cap = pulp.LpVariable.dicts("c", (ids, gws), cat="Binary")
    vc = pulp.LpVariable.dicts("v", (ids, gws), cat="Binary")

    # Money: proceeds from anyone sold plus the bank must cover anyone bought.
    proceeds = pulp.lpSum(sell[i] * (1 - squad[i]) for i in held)
    outlay = pulp.lpSum(m.loc[i, "price"] * squad[i] for i in ids if i not in held)
    prob += outlay <= proceeds + bank

    obj = []
    for gw in gws:
        d = DECAY ** (gw - gws[0])
        for i in ids:
            x = pts[(i, gw)]
            w = BENCH_WEIGHT[m.loc[i, "pos"]]
            obj += [d * x * line[i][gw], d * x * cap[i][gw],
                    d * VCAP_WEIGHT * x * vc[i][gw],
                    d * w * x * (squad[i] - line[i][gw])]
    leftover = proceeds + bank - outlay
    hits = max(0, n_transfers - free_transfers) * HIT_COST
    kept_ft = FT_VALUE.get(min(free_transfers - n_transfers, 5), 0.0) if n_transfers < free_transfers else 0.0
    prob += pulp.lpSum(obj) + ITB_VALUE * 10 * leftover - hits + kept_ft

    prob += pulp.lpSum(squad[i] for i in ids) == 15
    for pos, n in SQUAD.items():
        prob += pulp.lpSum(squad[i] for i in ids if m.loc[i, "pos"] == pos) == n
    for t in m["team"].unique():
        prob += pulp.lpSum(squad[i] for i in ids if m.loc[i, "team"] == t) <= MAX_PER_CLUB
    prob += pulp.lpSum(1 - squad[i] for i in held) == n_transfers
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
    if pulp.LpStatus[prob.status] != "Optimal":
        return None

    picked = [i for i in ids if squad[i].value() > 0.5]
    out_ids = [i for i in held if squad[i].value() < 0.5]
    in_ids = [i for i in picked if i not in held]
    g0 = gws[0]
    return {
        "n": n_transfers,
        "objective": round(pulp.value(prob.objective), 2),
        "hits": hits,
        "out": [(m.loc[i, "name"], sell[i]) for i in out_ids],
        "in": [(m.loc[i, "name"], float(m.loc[i, "price"])) for i in in_ids],
        "bank_after": round(float(leftover.value()), 1),
        "captain": m.loc[[i for i in picked if cap[i][g0].value() > 0.5][0], "name"],
        "vice": m.loc[[i for i in picked if vc[i][g0].value() > 0.5][0], "name"],
        "xi": [m.loc[i, "name"] for i in picked if line[i][g0].value() > 0.5],
        "bench": [m.loc[i, "name"] for i in picked if line[i][g0].value() < 0.5],
        "squad_ids": picked,
    }


def report(xp, current, bank, free_transfers, horizon=8, max_transfers=3, **kw):
    rows = []
    for n in range(0, max_transfers + 1):
        r = solve_transfers(xp, current, bank, n, free_transfers, horizon=horizon, **kw)
        if r:
            rows.append(r)
    if not rows:
        return None, []
    base = rows[0]["objective"]
    for r in rows:
        r["gain_vs_hold"] = round(r["objective"] - base, 2)
    best = max(rows, key=lambda r: r["objective"])
    return best, rows


def show(best, rows):
    print(f"{'moves':>6}  {'objective':>10}  {'vs hold':>8}  {'hit':>4}  transfers")
    for r in rows:
        moves = ", ".join(f"{o[0]} → {i[0]}" for o, i in zip(r["out"], r["in"])) or "hold"
        star = " *" if r is best else "  "
        print(f"{r['n']:>6}  {r['objective']:>10.2f}  {r['gain_vs_hold']:>+8.2f}  {r['hits']:>4.0f}  {moves}{star}")
    print(f"\nRecommended: {'hold and bank the transfer' if best['n'] == 0 else str(best['n']) + ' transfer(s)'}")
    print(f"Captain {best['captain']}, vice {best['vice']}, bank after £{best['bank_after']}m")
    print("XI:", ", ".join(best["xi"]))
    print("Bench:", ", ".join(best["bench"]))
    if best["n"] > 0 and best["gain_vs_hold"] < 1.5:
        print("\nNote: the gain does not clear the 1.5 point free-transfer hurdle. Holding is defensible.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--squad", default=str(ROOT / "out" / "squad_ids.json"),
                    help="JSON list of {id, buy} for the current 15")
    ap.add_argument("--bank", type=float, default=0.0)
    ap.add_argument("--ft", type=int, default=1, help="free transfers banked")
    ap.add_argument("--horizon", type=int, default=8)
    ap.add_argument("--max-transfers", type=int, default=3)
    a = ap.parse_args()

    xp = pd.read_parquet(ROOT / "out" / "xp.parquet")
    sq = json.load(open(a.squad))
    current = {int(s["id"]): float(s.get("buy") or s.get("price")) for s in sq}
    best, rows = report(xp, current, a.bank, a.ft, horizon=a.horizon, max_transfers=a.max_transfers)
    show(best, rows)
