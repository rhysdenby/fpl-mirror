# Gameweek Log

**Append-only.** One entry per gameweek: what was recommended, what was actually done, what it scored, and where the model was wrong. This is how the tool learns whether it is any good. Do not rewrite history here, add to it.

The rolling weekly recommendation lives at `claude/07-current-recommendation.md` and is replaced every gameweek. This log is the durable record. `claude/03-gw1-recommendation.md` is kept permanently as the founding analysis and is not overwritten.

**Entry format:** recommendation made, action taken, points scored, rank movement, model error and what caused it.

---

## GW1 — deadline Fri 21 Aug 2026 17:30 UTC / Sat 22 Aug 05:30 NZST

**Status:** recommended, awaiting deadline. No result yet.

**Recommendation.** Initial squad build, no transfers applicable. Squad 1 locked, £100.0m, £0.0m bank, 3-5-2.

XI: Kelleher | Gabriel (V), Virgil, Tarkowski | B.Fernandes (C), Rice, Mbeumo, Bruno G., Anderson | Thiago, Calvert-Lewin
Bench: Thiaw, Sessegnon, McBurnie, Petrović

Projected 54.65 GW1 including the captain, 423.3 over 8 GWs, 1995.5 ghost-ship over 38.

**Chip call:** none. Bench Boost is unusually live for GW1/GW2 because the squad carries no enabler and the whole bench is playable, but held pending real minutes data.

**Decisions worth remembering.**

*No Haaland.* Challenged twice by Rhys, re-tested across 13 specifications (horizon 8 to 38, decay 0.90 to 1.00, transfer uplift halved and off, minutes haircuts, corrected model). The sign never flipped. Margin is roughly 1% of season output, which is inside model error, so this was a coin flip resolved on the point estimate, not a conviction call. A hindsight test on 2025/26 actual points confirms Haaland *was* correct to own last season at £14.0m. What changed is price inflation around him: the hindsight-optimal 2025/26 squad cost £99.5m then and £117.0m now, because budget enablers inflated ~33% against his 11%.

*Model defect found and fixed.* The transfer adjustment scaled attacking rates but left `p_start` untouched, so movers inherited their old club's start rate. Pre-fix it rated three new Man City signings as more likely to start than Haaland. Fixed via `MOVER_BLEND = 0.50` in `model/features.py`, recorded as commit `eabbd98`. This reshaped 4 of 15 squad slots, all movers. **Correction, 19 Aug: the commit record is wrong. The patch is NOT in the mirror.** `model/features.py` fetched 19 Aug is still the pre-fix version. The fix exists only in session code. Do not treat a logged commit hash as proof again without verifying the file.

*Captaincy.* Fernandes over Gabriel. Fernandes leads on mean in all 8 gameweeks and, more importantly for the stated max-points posture, on the tail: P(≥20 captained) 34.3% vs 20.0% on 2025/26 per-start outcomes. Gabriel's higher 2025/26 per-start mean (6.90 vs 6.71) was earned under the old BPS, which specifically penalised centre-backs in the 2026/27 rebalance, so it is the least transferable number in the squad.

**Open risks carried into GW1.**

- `MOVER_BLEND = 0.50` is chosen, not measured. First real evidence arrives GW1-3.
- Bruno G. and Anderson are the only movers left in the squad and are the most likely to be repriced once team-sheet data exists.
- Virgil, Rice and McBurnie appear in only 3-4 of 7 runs across the parameter sweep. Low conviction.
- Bank is £0.0m, no flexibility without selling.
- Triple Captain plan was built around Haaland at home to a promoted side and is now unexecutable. Needs re-solving.

**To record after the deadline:** actual points, rank, which projections missed and whether the miss was minutes or football.


---

## GW1 pre-deadline revision, 19 Aug 2026

**Status:** recommendation revised two days before the deadline and accepted. Squad was not yet entered, so the change cost nothing.

**Trigger.** A deep strategy review across published 2026/27 sources, then a re-solve against the live mirror (`meta.json` fetched 18 Aug 23:29 UTC).

**Model defect found: season-phase bias.** All rates are season averages; the solver optimises an 8 gameweek horizon starting at GW1. Measured on four seasons of per-match data on a per-90 basis, Haaland scores at the 94th percentile for early-season front-loading, above the league median in all four seasons, mean ratio 1.68. GW1-6 point totals of 67, 51, 65, 62. The model was applying his April rate to his August fixtures.

Corrected with a shrunk, league-wide, per-player multiplier on attacking returns only. League median multiplier 0.976, so it redistributes rather than inflates.

**The GW1 call reverses.**

| Specification | Squad 1 | Haaland build |
|---|---|---|
| Shipped model | **423.3** | 412.5 |
| Tight correction | 412.6 | **440.4** |
| Full correction | 405.8 | **449.2** |

Breakeven λ = 0.10. Haaland enters the **free** solve unforced in all 8 sensitivity specifications, the mirror image of the 13 specifications in which forcing him in previously lost.

**Squad, 3-4-3, £100.0m. Locked by Rhys 19 Aug.** Kelleher | Gabriel, Virgil, Thiaw | Semenyo (V), Anderson, Groß, Ndiaye | Haaland (C), Thiago, Calvert-Lewin. Bench Mitchell, Truffert, Gomez, Petrović. Seven of fifteen change from Squad 1.

**Secondary benefit not in the 440.4:** the Triple Captain plan (GW3 Coventry, GW7 Ipswich, GW16 Hull) becomes executable again.

**Other corrections made to the docs this session.**

- The governing hindsight finding was misattributed to 2025/26. It is **2019/20**, Sertalp Cay's study, winner Joshua Bull on 2,557. The ghost ship **did** use a chip (Bench Boost GW1, De Bruyne captained all 38, 502 points from him alone). "Hold by default" does not follow from the ghost ship; it follows from prediction noise.
- Correlation argument reframed: correlation is **irrelevant** to expected total points by linearity of expectation. The earlier "variance-seeking" justification overreached.
- BPS rebalance quantified: Gabriel 30 bonus to 20, no centre-back gained more than one. Gabriel stress-tested and survives to a further 50% bonus haircut, so no manual adjustment needed.
- T-3h pre-deadline sweep upgraded from optional to mandatory.
- Mirror found stale: `features.py` unpatched, `squad_ids.json` on Revision 1.

**To record after the deadline:** actual points, rank, whether the season-phase correction helped or hurt, and whether the miss was minutes or football.
