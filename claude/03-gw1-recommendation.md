# GW1 Squad Recommendation, 2026/27

> **Revision 4, 19 Aug 2026: the no-Haaland call is overturned.** A season-phase defect was found in the model. Everything below is preserved as written and remains the correct reasoning *given the model as it stood*. The addendum at the foot of this document explains what changed. Do not read the Revision 3 conclusion as current.

Deadline **Fri 21 Aug 17:30 UTC / Sat 22 Aug 05:30 NZST**. Mirror data fetched 18 Aug 03:51 UTC.

**Revision 3, 18 Aug.** Two deliberate squads, one with Haaland and one without, built under the corrected minutes model with the same rules applied to both. Revision 2's analysis of the no-Haaland call stands and is retained below. Revision 1's squad is superseded.

## Headline

| | No Haaland | With Haaland | Diff |
|---|---|---|---|
| GW1 XI xP incl. captain | **54.65** | 53.02 | −1.63 |
| 8GW, no transfers | **423.3** | 419.6 | −3.7 |
| 38GW, no transfers | **1995.5** | 1974.7 | −20.7 |
| Solver objective (8GW, decay 0.90) | **309.93** | 307.37 | −2.56 |

Haaland costs about **1% of season output**. That is inside the model's own error. Calibration runs 7% hot, so treat the absolute totals as directional and only the gap as meaningful, and the gap is small.

## Why these squads differ from the raw solver output

Forcing Haaland in and letting the solver rebuild produced junk: three Bournemouth players and Diop at £4.0m on the bench. That is an artifact of a flat 0.09 bench weight and mechanical xP maximisation, not a squad anyone would field.

Both squads below are built from a pool restricted to players with **p(start) ≥ 0.70**, plus at most two genuine cheap enablers. Same restriction on both sides, so the comparison is fair. Minimum p(start) in either squad is 0.67.

## Squad 1: No Haaland — £100.0m, 3-5-2

### Starting XI

| Player | Pos | Club | £ | Own% | p(start) | GW1 xP | 8GW xP |
|---|---|---|---|---|---|---|---|
| Kelleher | GK | BRE | 5.0 | 5.8 | 0.97 | 3.69 | 26.1 |
| Gabriel (V) | DEF | ARS | 8.0 | 28.6 | 0.90 | 5.10 | 35.9 |
| Virgil | DEF | LIV | 6.5 | 17.8 | 0.97 | 3.50 | 30.0 |
| Tarkowski | DEF | EVE | 6.0 | 9.5 | 0.97 | 3.75 | 29.3 |
| **B.Fernandes (C)** | MID | MUN | 12.0 | 48.7 | 0.97 | 6.19 | 47.9 |
| Rice | MID | ARS | 7.5 | 20.2 | 0.92 | 4.64 | 34.6 |
| Mbeumo | MID | MUN | 8.0 | 30.1 | 0.91 | 4.61 | 35.7 |
| Bruno G. | MID | ARS | 7.0 | 9.1 | 0.79 | 4.60 | 33.3 |
| Anderson | MID | MCI | 6.5 | 9.7 | 0.84 | 4.36 | 33.3 |
| Thiago | FWD | BRE | 8.0 | 17.5 | 0.97 | 4.48 | 35.4 |
| Calvert-Lewin | FWD | LEE | 6.0 | 26.9 | 0.81 | 3.55 | 28.1 |

### Bench

1. Thiaw (DEF, NEW, £5.0m) — 27.9 over 8
2. Sessegnon (DEF, FUL, £4.5m) — 25.2
3. McBurnie (FWD, HUL, £5.5m) — 21.9
4. Petrović (GK, BOU, £4.5m) — 23.4

Clubs: ARS 3, BRE 2, MUN 2, rest singles. **No enabler.** All 15 are real starters, which is the practical advantage of not carrying a £15.5m striker.

## Squad 2: With Haaland — £100.0m, 3-4-3

### Starting XI

| Player | Pos | Club | £ | Own% | p(start) | GW1 xP | 8GW xP |
|---|---|---|---|---|---|---|---|
| Verbruggen | GK | BHA | 4.5 | 18.8 | 0.97 | 3.43 | 24.9 |
| Tarkowski | DEF | EVE | 6.0 | 9.5 | 0.97 | 3.75 | 29.3 |
| Thiaw | DEF | NEW | 5.0 | 1.9 | 0.87 | 3.29 | 27.9 |
| Sessegnon | DEF | FUL | 4.5 | 0.4 | 0.67 | 2.93 | 25.2 |
| B.Fernandes (V) | MID | MUN | 12.0 | 48.7 | 0.97 | 6.19 | 47.9 |
| Anderson | MID | MCI | 6.5 | 9.7 | 0.84 | 4.36 | 33.3 |
| Ndiaye | MID | EVE | 6.0 | 15.6 | 0.96 | 3.92 | 30.6 |
| Groß | MID | BHA | 5.5 | 11.9 | 0.95 | 3.74 | 28.8 |
| **Haaland (C)** | FWD | MCI | 15.5 | 70.9 | 0.89 | 6.69 | 47.0 |
| Thiago | FWD | BRE | 8.0 | 17.5 | 0.97 | 4.48 | 35.4 |
| Calvert-Lewin | FWD | LEE | 6.0 | 26.9 | 0.81 | 3.55 | 28.1 |

### Bench

1. Tavernier (MID, BOU, £6.0m) — 30.6 over 8
2. Truffert (DEF, BOU, £5.5m) — 25.9
3. Mitchell (DEF, CRY, £4.5m) — 22.7
4. Petrović (GK, BOU, £4.5m) — 23.4

Clubs: BOU 3, BHA 2, EVE 2, MCI 2, rest singles.

## What you actually give up

Only 8 of 15 players are common to both. The £15.5m is not funded by one downgrade, it is funded across the whole spine.

**Lost by taking Haaland:** Gabriel (35.9), Mbeumo (35.7), Rice (34.6), Bruno G. (33.3), Virgil (30.0), Kelleher (26.1).
**Gained:** Haaland (47.0), Tavernier (30.6), Ndiaye (30.6), Groß (28.8), Truffert (25.9), Mitchell (22.7), Verbruggen (24.9).

Haaland at 47.0 over 8 GWs is the highest single projection in the game. He does not cover the six mid-tier assets he displaces, but he comes close, and the residual is 3.7 points over 8 weeks.

## Honest weaknesses on both sides

- **The no-Haaland squad now has three Arsenal players.** That is the same variance concentration criticised in Revision 2 for the Man City stack, and the objective function still cannot see it. Gabriel, Rice and Bruno G. share every fixture. It is a smaller correlated block than three City attackers, since Gabriel's returns are mostly clean sheets rather than goals, but it is not nothing.
- **The Haaland squad leans on three Bournemouth players** and a much weaker midfield. Its floor is lower than the totals suggest: if Haaland blanks, there is little else generating.
- **The Haaland squad has the better captain and the better ceiling.** He is the highest-xP player in the game, and Triple Captain at home to a promoted side (GW3 Coventry, GW7 Ipswich, GW16 Hull) becomes available. Squad 1 forfeits that chip plan entirely.
- **Both are cold-start builds.** Zero 2026/27 match data. Every rate is 2025/26.
- **70.9% own Haaland.** Under the stated max-EV-ignore-rank posture that is irrelevant. It is not irrelevant to how the season feels, and Squad 1 will lose rank badly in any week he hauls.

## The call

The model prefers Squad 1 by roughly 1% of season output, which is inside its own error bars. It cannot resolve this and should not pretend to. Squad 1 is the higher expected-points build and has no dead bench slot. Squad 2 is the more robust build, has the better captain and preserves the Triple Captain plan.

Either is defensible. Do not let the number decide it, the number is not that precise.

---

# Appendix: the analysis behind the no-Haaland call (Revision 2)

## The minutes defect

`features.py` applies a transfer adjustment scaling `g_90` and `a_90` by the ratio of new-club to old-club attacking strength. It does **not** touch `p_start`. A player who moves club inherits his old club's start rate unchanged.

| Player | Club | p(start), shipped model |
|---|---|---|
| Semenyo | MCI (new) | 0.970 |
| Anderson | MCI (new) | 0.970 |
| Dubravka | TOT (new) | 0.970 |
| Senesi | TOT (new) | 0.970 |
| Guéhi | MCI (new) | 0.921 |
| **Haaland** | **MCI (established)** | **0.895** |

Three brand-new Man City signings rated more likely to start than Haaland, and a £4.0m keeper rated nailed. Fifty players in the pool moved this window and all are mispriced the same way. Revision 1 held six of them, carrying 42% of squad 8GW xP.

**Fix:** for movers, blend the inherited start rate with the price-rank pecking-order prior at the new club. `MOVER_BLEND = 0.50`. Patch in `out/features_minutes_fix.patch`, needs committing to `model/features.py` in the mirror. `MOVER_BLEND = 1.0` reproduces the shipped model exactly.

## Haaland sensitivity, 13 specifications

Forcing Haaland in loses in every one. The sign never flips.

| Specification | Free | Haaland forced | Delta |
|---|---|---|---|
| h=8, decay 0.90 (shipped) | 317.82 | 315.65 | −2.17 |
| h=8, no decay | 445.74 | 443.24 | −2.50 |
| h=12, decay 0.90 | 399.17 | 396.59 | −2.58 |
| h=16, decay 0.95 | 621.63 | 618.57 | −3.06 |
| h=20, no decay | 1107.77 | 1098.20 | −9.57 |
| h=38, no decay | 2102.42 | 2083.18 | −19.24 |
| transfer uplift halved | 316.41 | 314.40 | −2.01 |
| transfer uplift off entirely | 315.30 | 314.00 | −1.30 |
| movers p(start) −20% | 309.27 | 307.98 | −1.29 |
| corrected minutes, h=8 | 310.66 | 309.33 | −1.33 |
| corrected minutes, h=12 | 390.31 | 388.53 | −1.78 |
| corrected minutes, h=20 undecayed | 1084.81 | 1076.12 | −8.69 |

## Errors corrected from Revision 1

- **The cap claim was false.** Revision 1 said adding Haaland forces two City players out. It forces out one: `solve(locked=[411])` keeps Guéhi and Anderson and swaps only Semenyo. The second departure was budget, not the three-per-club cap.
- **The denominator was unexplained.** "Roughly 318" is the solver's decayed objective, 317.82, including captain, bench weights and the bank term. The XI's raw 8GW xP is 378.2.
- **The horizon argument cut the other way.** Extending the horizon makes the no-Haaland case stronger, not weaker: −2.17 at 8 GWs becomes −19.24 across an undecayed season, because budget efficiency compounds.
- **Captaincy was already priced.** The MILP selects and doubles the optimal captain every gameweek. The armband premium is roughly half a point per week and sits inside the objective.

## Hindsight test on 2025/26

Fed the optimiser last season's **actual** points at last season's GW1 prices, so no projection error at all.

**Haaland is in the hindsight-optimal squad.** 239 points, top of the league. On last season's facts, owning him was correct.

What changed is not him:

| | 25/26 | 26/27 | |
|---|---|---|---|
| Haaland | £14.0m | £15.5m | +11% |
| B.Fernandes | £9.0m | £12.0m | +33% |
| Gabriel | £6.0m | £8.0m | +33% |
| Guéhi | £4.5m | £6.0m | +33% |
| Thiago | £6.0m | £8.0m | +33% |

That hindsight-optimal squad cost £99.5m last season. The same 15 players cost **£117.0m** today, £17m over the cap. The cheap enablers that funded Haaland inflated three times faster than he did.

Supporting numbers on his 2025/26: points per million **17.1**, the worst of the top 12 scorers (every other was 23 to 40, Guéhi returned 39.8). Sixteen blanks against thirteen hauls. 155 points in GW1-19, 84 in GW20-38. 34 starts of 38.

The model projects him at 46.98 over 8 GWs, roughly 223 across a season against his actual 239. **It is not fading him.** It has him as the highest-scoring player in the game and declines to pay the price by a margin of about 1%.

## Model validation

Walk-forward on 2025/26: rates fitted on GW1-19 only, used to predict GW20-38.

| Measure | Result |
|---|---|
| Per-match Spearman | 0.610 |
| Per-match MAE vs predict-the-mean | 21.2% better |
| Season-total Spearman (GW20-38, 780 players) | 0.825 |
| by position | FWD 0.874, MID 0.853, DEF 0.814, GK 0.740 |
| Top 30 by predicted xP | 73.9 actual pts vs 44.1 for the eligible pool |
| Calibration | predicted 1.20 pts/match vs actual 1.12 |

Worst over-predictions were all minutes errors: Cullen, Paquetá, Kudus, Gvardiol, de Ligt, Vicario, Grealish, Haaland. Worst under-predictions were players who won a starting spot mid-season. The model prices football well and prices team sheets badly.

## Caveats

- **Cold start.** Zero 2026/27 match data. GW6 wildcard is the first honest review point.
- **BPS haircut.** Bonus discounted to 75%, tilted by position. Centre-backs down 20%, keepers up 15%.
- **`MOVER_BLEND = 0.50` is chosen, not measured.** Squad stable across 0.40 to 0.70. Stops mattering once real minutes data exists around GW4.
- **No correlation penalty in the objective.** Open gap, applies to the ARS 3 block in Squad 1.
- **T-48h cadence misses Friday pressers.** This ran Tuesday. Rotation news before Friday 17:30 UTC is in none of these numbers, and minutes are the model's weak point.


---

# Revision 4 addendum, 19 Aug 2026: the call reverses

## What was wrong

Every rate in the model is a **season average**, but the solver optimises an **8 gameweek horizon starting at GW1**. That is only sound if scoring rates are stationary across the season. Haaland's are not, and the deviation is one of the largest in the league.

Measured per-90, so minutes and injuries are controlled for, points per 90 in GW1-6 against GW7-38:

| Season | GW1-6 pts/90 | GW7-38 pts/90 | Ratio |
|---|---|---|---|
| 22/23 | 12.54 | 8.07 | 1.55 |
| 23/24 | 8.68 | 7.38 | 1.18 |
| 24/25 | 10.85 | 4.75 | 2.28 |
| 25/26 | 11.09 | 6.50 | 1.71 |

Mean 1.68, **94th percentile** across 431 qualifying players, above the league median in all four seasons. League median is 0.976, so this is a redistribution, not an inflation. Raw GW1-6 point totals: 67, 51, 65, 62. Mean 61.2. Worst of four seasons 51.

Revision 3 projected him at 46.98 over **eight** gameweeks. His four-season mean over **six** is 61.2. The model was not fading him on football, it was applying his April rate to his August fixtures.

## The corrected comparison

Applied as a shrunk, league-wide, per-player multiplier on attacking returns only, at full strength GW1-6 tapering to zero by GW9.

| Specification | Squad 1 8GW XI+C | Haaland build 8GW XI+C | Winner |
|---|---|---|---|
| Shipped model (no correction) | 423.3 | 412.5 | Squad 1 by 10.8 |
| Tight correction, attacking returns only | 412.6 | **440.4** | Haaland by 27.8 |
| Full correction, all components | 405.8 | **449.2** | Haaland by 43.4 |

**Breakeven is λ = 0.10.** Applying only a tenth of the correction is enough to put Haaland in the free solve. To keep Squad 1 you have to believe the season-phase effect is essentially zero.

The sign is stable across shrinkage K in 1 to 4 and clip ceilings of 1.35 and 1.50. Haaland appears in the **free** solve, unforced, in all eight specifications tested. This is the mirror image of Revision 3, where forcing him in lost across all 13 specifications.

## What Revision 3 got right

The price-inflation analysis, the hindsight test, the 13-specification sweep and the `MOVER_BLEND` fix were all correct and are unaffected. Revision 3 was not sloppy; it was rigorous about the wrong quantity. The defect it missed was upstream of the optimiser, in the assumption that a season-average rate is the right input to an eight-week horizon.

## Caveats

- n = 4. Strong signal, small sample.
- City rebuilt heavily this window. The attacking pattern that generated those four seasons may not survive.
- The correction is a decomposition of the same seasons that produce the rates, not a clean out-of-sample test.
- It is a cold-start device. Retire it once 2026/27 match data exists, around GW4 to GW6.
