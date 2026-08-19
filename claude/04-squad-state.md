# Squad State

**Authoritative record of the squad between deadlines.** The FPL API does not expose a saved team before a deadline (`/my-team/` needs a login cookie), so this doc is the source of truth until `picks.json` appears in the mirror after each deadline. Reconcile against `picks.json` every gameweek and correct any drift here.

Last updated: 19 Aug 2026.

## Status

- Season 2026/27, entering **GW1**. Deadline Fri 21 Aug 17:30 UTC / **Sat 22 Aug 05:30 NZST**
- **LOCKED: the Revision 4 Haaland build, 3-4-3.** Rhys's call, 19 Aug 2026, after the season-phase defect was found and the no-Haaland call reversed. This supersedes Squad 1, which was locked on 18 Aug under the defective model
- **Squad NOT YET ENTERED in the official app.** This remains the one outstanding action before Fri 21 Aug 17:30 UTC
- Entry ID `5470938` — team **HaCunha Matata**. Mini-league `218656` Stank League

## Why the no-Haaland call was overturned

A season-phase defect was found on 19 Aug. The model estimates rates as season averages and applies them to an 8 gameweek horizon starting at GW1. Haaland is the most rate-front-loaded player in the league across the last four seasons, at the 94th percentile on a per-90 basis, above the league median in all four. His GW1-6 point totals were 67, 51, 65 and 62.

Full working in `03-gw1-recommendation.md` Revision 4 and `02-strategy.md`.

| Specification | Squad 1 8GW XI+C | Haaland build 8GW XI+C |
|---|---|---|
| Shipped model | **423.3** | 412.5 |
| Tight correction (attacking returns only) | 412.6 | **440.4** |
| Full correction | 405.8 | **449.2** |

Breakeven is λ = 0.10. Haaland appears in the **free**, unforced solve in all eight sensitivity specifications.

The earlier no-Haaland work was not wrong on its own terms. The price-inflation finding, the hindsight test and the 13-specification sweep all stand. They were rigorous about a quantity computed from a defective input.

## Squad (15) — £100.0m spent, £0.0m bank, 3-4-3

Built from a pool restricted to p(start) ≥ 0.70, the same discipline applied in Revision 3, so the comparison is like for like. Minimum p(start) in the squad is 0.81.

### Starting XI

| Player | Pos | Club | £ | Own% | p(start) | GW1 xP | 8GW xP |
|---|---|---|---|---|---|---|---|
| Kelleher | GK | BRE | 5.0 | 5.9 | 0.97 | 3.69 | 26.1 |
| Gabriel | DEF | ARS | 8.0 | 28.9 | 0.90 | 5.15 | 36.2 |
| Virgil | DEF | LIV | 6.5 | 18.1 | 0.97 | 3.50 | 30.0 |
| Thiaw | DEF | NEW | 5.0 | 1.9 | 0.87 | 3.29 | 27.9 |
| Semenyo (V) | MID | MCI | 8.5 | 26.5 | 0.92 | 5.45 | 38.6 |
| Anderson | MID | MCI | 6.5 | 9.4 | 0.84 | 4.28 | 32.8 |
| Groß | MID | BHA | 5.5 | 12.4 | 0.95 | 4.03 | 30.7 |
| Ndiaye | MID | EVE | 6.0 | 15.7 | 0.96 | 4.00 | 31.2 |
| **Haaland (C)** | FWD | MCI | 15.5 | 70.2 | 0.89 | 8.56 | 57.5 |
| Thiago | FWD | BRE | 8.0 | 17.7 | 0.97 | 4.57 | 36.0 |
| Calvert-Lewin | FWD | LEE | 6.0 | 27.7 | 0.81 | 3.78 | 29.7 |

### Bench

1. Mitchell (DEF, CRY, £4.5m), 23.2 over 8
2. Truffert (DEF, BOU, £5.5m), 25.9
3. Gomez (MID, BHA, £5.0m), 21.4
4. Petrović (GK, BOU, £4.5m), 23.4

Clubs: **MCI 3** (Haaland, Semenyo, Anderson), BRE 2, BHA 2, rest singles. No enabler, all 15 are real starters.

**Projections (tight specification):** GW1 XI 50.30, **58.86 with the captain doubled**. 8GW XI+C 440.4. Model calibration runs 7% hot, so treat absolute totals as directional and only the gaps as meaningful.

**Solver captains Haaland in all 8 gameweeks of the horizon.**

## Superseded: Squad 1 (locked 18 Aug, no Haaland)

Retained in full in `03-gw1-recommendation.md`. Kelleher, Gabriel, Virgil, Tarkowski, B.Fernandes (C), Rice, Mbeumo, Bruno G., Anderson, Thiago, Calvert-Lewin, with Thiaw, Sessegnon, McBurnie, Petrović benched. £100.0m, 3-5-2.

Seven of fifteen change. Out: Tarkowski, B.Fernandes, Rice, Mbeumo, Bruno G., Sessegnon, McBurnie. In: Haaland, Semenyo, Groß, Ndiaye, Mitchell, Truffert, Gomez.

## Chips and transfers

- Free transfers banked: n/a until GW2
- Chips used: none
- First set (WC, FH, TC, BB) expires **13:30 GMT Sat 2 Jan 2027**, the GW19 deadline. Second set opens GW20
- **Triple Captain is executable again if the Haaland build is adopted.** GW3 Coventry (h), GW7 Ipswich (h), GW16 Hull (h). GW3 is the primary given the season-phase evidence points at the earliest gameweeks being his strongest. GW16 has the softest raw fixture but carries pre-Christmas rotation risk and collides with any GW16 Free Hit
- This is a material secondary benefit of the Haaland build and it is not counted in the 440.4 figure. Under the max-points posture chips carry a large share of season upside, and the no-Haaland build forfeited this chip plan entirely

## Standing risks

- **The season-phase correction is new and rests on n = 4 for Haaland.** It is robust in sensitivity and neutral at the league median, but it is a cold-start device. Retire it once real 2026/27 data exists, around GW4 to GW6
- **City rebuilt heavily this window.** The attacking pattern that produced Haaland's four front-loaded seasons may not survive. Semenyo and Anderson are both new City signings and both are movers, the class of player the model has already been caught mispricing once
- **MCI 3 is a correlated block.** Flagged and accepted under the stated posture. Correlation does not affect expected total points, so this is recorded for completeness, not as an action
- **`MOVER_BLEND = 0.50` is a judgement call,** chosen not measured. Real 2026/27 minutes from GW1-3 replace it. Review hard at GW4 and again before the GW6 wildcard
- **The mirror is stale and must be fixed.** `model/features.py` does **not** contain the `MOVER_BLEND` patch, despite `06-gw-log.md` recording it as commit `eabbd98`. `model/squad_ids.json` still holds Revision 1. Any scheduled run right now reproduces the original minutes defect. **Commit both before the next scheduled run**
- **Gabriel and the BPS rebalance.** He is the single biggest loser from the bonus changes, dropping 30 bonus to 20 in the published back-test. Stress-tested: he survives in the optimal squad up to a further 50% haircut on his remaining bonus, so the current 0.80 defender tilt already prices him adequately. No action, but he is the squad's most exposed asset to a rule change
- **Bank is £0.0m,** so no flexibility for a price-driven move without selling first
- **T-48h cadence misses Friday pressers.** This build ran Wednesday. A T-3h sweep before Fri 21 Aug 17:30 UTC is now mandatory and is worth more here than anywhere else in the season

## Career baseline, for judging the season

15 seasons played. Career best 2024/25 at 2,438 points, rank 350,194, **top 3%**. Last season 2,163 points, top 10%. Median season sits around top 20-25%. Beating 2,438 is the honest target.
