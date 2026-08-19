# Strategy, Model Spec and Research Basis

## The finding that should govern everything

**Corrected 19 Aug 2026.** The previous version of this section attributed these numbers to 2025/26. They are from **2019/20**, and the study is Sertalp B. Cay's hindsight optimisation work (alpscode.com, May 2021). Getting the season wrong does not change the conclusions, but the inference drawn from it was subtly wrong and is restated below.

Cay solved 2019/20 four ways with perfect information:

| Model | Constraint | Points |
|---|---|---|
| 1 | unlimited hits | **4,984** (took 145 hits) |
| 2 | no hits | 3,945 |
| 3 | no transfers, Free Hit allowed | 3,236 |
| 4 | "ghost ship": one squad, never touched | **2,446**, rank 386 |

The actual 2019/20 winner was Joshua Bull on **2,557**. The 2025/26 winner was Erik Ibsen, a rookie, who won by 38 points.

Two corrections of detail that matter:

- The ghost ship **was not chip-free**. It played Bench Boost in GW1 and captained De Bruyne in all 38 gameweeks. De Bruyne alone supplied 502 of its 2,446 points. It is not a clean "do nothing" baseline.
- **"Hold by default" does not follow from the ghost ship.** A static squad finishing 386th shows the GW1 build is high-leverage. It says nothing about whether transfers are worth making. The transfer case is Model 1 against Model 2: with perfect information, aggressive transferring is worth roughly **1,000 points**. Transfers are enormously valuable *when you know what happens next*.

The correct inference, which is what this system actually runs on:

1. **The GW1 build is the single highest-leverage decision of the season.** It deserves more compute and more scrutiny than any subsequent week. Unchanged.
2. **Prediction quality is the binding constraint, not optimisation quality.** The MILP is trivially solvable. The 2,500-point gap between Model 1 and Model 4 is entirely a forecasting gap. Effort goes into the minutes model and the DefCon distribution before it goes into solver sophistication.
3. **Default to hold because our forecasts are noisy, not because transferring is bad.** A marginal transfer rarely clears the hurdle once prediction error is priced in. If the model ever gets materially better, the correct transfer rate goes **up**, not down. A recommendation engine that manufactures a move every week is destroying value today; that is a statement about our error bars, not a law of the game.

Supporting evidence from an actual champion: Ibsen took **zero hits** across his title-winning 2025/26 season, saying a hit never mathematically justified itself to him and he would rather field a player in a bad fixture. He still transferred frequently early, but with free transfers and largely for price reasons.

## Risk posture

**Maximise total points. Ownership, club concentration and rank are all ignored.**

Confirmed explicitly by Rhys, 18 Aug 2026: *"maximum probability of scoring the highest points possible, not worried about who, what team they play for or if we have 3 of the same club."*

Three things follow, and they are not all obvious.

**No correlation penalty. Do not add one.** Correct conclusion, but the justification was muddled and is restated here (19 Aug 2026).

The clean argument is **linearity of expectation**. If the objective is expected total points, the expected season total is just the sum of the individual expected points. Correlation between players has **literally zero effect on it**. So a concentration penalty is not merely unnecessary, it is a distortion: it would trade away mean for a quantity the objective does not contain.

The earlier "we are variance-seeking so stacking is good" framing overreached. That argument only applies to a tail objective such as P(winning), and even there the effect is small: a season total is a sum over roughly 11 starters across 38 gameweeks, so it is close to normal and squad-level correlation barely moves the tail. The honest position is that correlation is **irrelevant** to us, not that it is desirable. We neither penalise nor seek it. Keep `max_defenders_per_team` as a defensive-stacking guard only.

**Where the tail actually lives is captaincy and chips, not the 15.** A 15-man squad is a sum of many players and its total is close to normal, so squad composition moves the mean far more than it moves the tail. The decisions that genuinely change the shape of the distribution are the armband and the four chips. If the objective is maximum points rather than protected rank, chip timing deserves more analytical weight than transfer churn does.

**Expect noisy rank.** Overall rank is a relative measure and this posture optimises an absolute one. Weeks where the model fades a heavily-owned haul will cost significant rank while the points total looks fine. That is the accepted trade, not a bug to fix.

**Ownership still matters to us, but only second-order.** Added 19 Aug 2026. Ignoring ownership *as a rank instrument* is correct. Ignoring it entirely is not, because two channels feed back into absolute points:

1. **Price and team value.** Owning risers early compounds squad value, and value converts to expected points later in the season. Ibsen treated the first half as a value-building phase for exactly this reason. This is already partly captured by `itb_value`.
2. **Minutes information.** High ownership is partly a crowd signal that a player is nailed. Minutes are the model's weakest component, so where our p(start) disagrees sharply with a very high ownership figure, the crowd is often right and it is worth a manual look.

Neither channel justifies template-hugging, effective ownership maths, or differentials-for-rank. Treat all such content as inapplicable.

One nuance from the 2025/26 champion (Erik Ibsen): he captained Haaland in **22 of 38 gameweeks**, with Bruno Fernandes the only other player captained more than twice (seven times), and took his risk on non-captain starters instead. That is not template-hugging, it is EV maximisation correctly applied. Captaincy is the highest-variance single decision on the board, so the EV-optimal captain is usually the boring one; the risk budget is better spent on squad slots 2-11 where a miss costs 5 points, not 15. Ibsen framed it as securing an extra 7 or 8 points rather than chasing 20.

**Captaincy rule for this system:** captain = argmax(xP), full stop. Ownership and effective ownership do not enter. A "differential captain" is correct if and only if the differential genuinely has the higher expected points. The only legitimate tie-break is minutes certainty when two candidates sit inside model noise.

**Home/away asymmetry is a real captaincy input.** Premium attackers carry a meaningful expected-points edge at home. The model already applies a venue multiplier (1.08 home, 0.94 away) inside the attacking term, so this is priced; the point here is not to override it with narrative when the away fixture merely looks easier.

## Model parameters

Calibrated against the community reference solver (`solioanalytics/open-fpl-solver`, formerly `sertalpbilal/FPL-Optimization-Tools`).

| Parameter | Value | Meaning |
|---|---|---|
| `horizon` | 8 GWs | how far ahead the solver plans |
| `decay_base` | 0.90 | future GW xP weight, `0.9^t` |
| `ft_value` | 1.5 pts | value of holding a free transfer, i.e. the hurdle a move must clear |
| `ft_value_list` | 2→2.0, 3→1.6, 4→1.3, 5→1.1 | diminishing value as transfers stack up |
| `ft_use_penalty` | 0.2 | friction against churning for marginal gain |
| `bench_weights` | GK 0.03, B1 0.21, B2 0.06, B3 0.002 | how much bench xP counts toward the objective |
| `vcap_weight` | 0.1 | vice-captain contribution |
| `itb_value` | 0.08 pts per £0.1m | value of money in the bank as future flexibility |
| `hit_cost` | 4 | points per transfer beyond free |
| `opposing_play_penalty` | 0.5 | penalty for owning players on both sides of a fixture |
| `max_defenders_per_team` | 3 | defensive-stacking guard |
| `MOVER_BLEND` | 0.50 | **added 18 Aug.** For players who changed clubs, weight on the inherited start rate vs the price-rank pecking-order prior at the new club. 1.0 reproduces the pre-fix behaviour |
| `PHASE_SHRINK` (K) | 2.0 | **added 19 Aug.** Shrinkage of the season-phase multiplier toward 1.0. See below |
| `PHASE_CLIP` | 0.75 to 1.50 | bounds on the shrunk season-phase multiplier |
| `PHASE_SCOPE` | attacking returns only | the multiplier applies to goals and assists, not to clean sheets, saves, DefCon, bonus or appearance points |

**Benchmarked against community practice, 19 Aug 2026.** `ft_value` at 1.5 sits inside the normal band: FPL Review's solver default is 1.75 with roughly 2.0 used for skeleton planning, while the sertalp / open-fpl and Julia ports instead run `ft_value` around 0.8 paired with an `ft_use_penalty` of 1.0. Those are two different routes to the same anti-churn behaviour. Ours currently leans almost entirely on `ft_value`, because `ft_use_penalty` is only 0.2.

**If the weekly engine starts manufacturing marginal moves, raise `ft_use_penalty` toward 1.0 rather than inflating `ft_value`.** They are not interchangeable: `ft_value` raises the bar for every transfer including genuinely good ones and distorts the horizon valuation, whereas `ft_use_penalty` adds friction only at the point of use. Inflating `ft_value` to suppress churn is the crude fix.

`decay_base` at 0.90 is at the patient end of the 0.80 to 0.95 range; the common community value is 0.84 to 0.85. Keep 0.90, it is coherent with an 8 GW horizon and a hold-by-default posture, but know that it makes the model more willing to accept a worse present for a better future than most solvers would.

**Add a commit buffer inside the horizon.** FPL Review deliberately plans over roughly 8 gameweeks but only commits transfers in the first 6, so the solver does not make moves whose payoff sits in the final horizon week where it cannot be followed through. We should do the same: plan over 8, commit over 6.

**Check the free transfer cap.** Free transfers bank to a maximum of 5 and are retained when a chip is played. Any rollover past 5 is destroyed. Confirm the weekly engine never accumulates above 5.

`ft_value` at 1.5 is the important one: it encodes the ghost-ship finding directly. A transfer must gain more than 1.5 points over the horizon before it is worth making, before any hit is even considered.

**`optimise.py` note:** the GW1 solver uses a flat 0.09 bench weight for outfield slots rather than the ordered 0.21/0.06/0.002 above. This is a known simplification and it is why the raw solver output will happily park a £4.0m non-player on the bench. Restrict the pool by p(start) when building initial squads.

## Season-phase correction

**Added 19 Aug 2026. This is the most material model change since `MOVER_BLEND`, and it reversed the GW1 Haaland call.**

The model estimates every rate as a season average, then the solver optimises an **8 gameweek horizon starting at GW1**. That is only valid if players score at a constant rate across the season. Some do not, and the deviation is stable enough across seasons to be predictable.

Measured on four seasons of vaastav per-match data (2022/23 to 2025/26), on a **per-90 basis** so the minutes and injury confound is removed: for each player, points per 90 in GW1-6 against points per 90 in GW7-38, requiring 270+ early minutes and 900+ later minutes.

- League median ratio **0.976**, so this is a redistribution across players, not a global inflation. Applying it does not inflate the model's total.
- Applied as a per-player multiplier, shrunk toward 1.0 with K = 2, clipped to 0.75 to 1.50, at full strength for GW1-6 and tapering to zero by GW9.
- **Scope is attacking returns only.** Clean sheets, saves, DefCon and bonus are lumpy and team-driven, and the apparent phase signal in them is mostly noise. Restricting scope also stopped the solver reaching for front-loaded goalkeepers, which was the tell that the wide version was overfitting.

**The Haaland result.** Haaland is the most rate-front-loaded player in the league over the four seasons measured, at the **94th percentile**, and he is above the league median in **all four**:

| Season | GW1-6 pts/90 | GW7-38 pts/90 | Ratio |
|---|---|---|---|
| 22/23 | 12.54 | 8.07 | 1.55 |
| 23/24 | 8.68 | 7.38 | 1.18 |
| 24/25 | 10.85 | 4.75 | 2.28 |
| 25/26 | 11.09 | 6.50 | 1.71 |

Mean 1.68, shrunk to 1.45. His raw GW1-6 totals were 67, 51, 65 and 62 points, mean 61.2, with nine goals a season on average. The floor across four seasons is 51.

**Why this is a correction and not a fudge.** It is derived league-wide from a mechanism that applies to everyone, it is neutral at the median, it is computed per-90 so it is not a restatement of the minutes model, and it is measured out-of-sample across four independent seasons. There is also a plausible structural mechanism: City's European load, late-season games with the title already decided, and Haaland carrying knocks into the back half all depress his late-season rate without depressing his minutes.

**Caveats to carry.** n = 4 is small. City rebuilt heavily this window, so the attacking pattern that produced those numbers may not survive. And the correction is fitted on the same seasons that produce the underlying rates, so it is a decomposition rather than a clean out-of-sample test. Retire the correction once 2026/27 match data exists; it is a cold-start device.

## Bonus modelling after the BPS rebalance

`BONUS_POS_TILT` currently applies a flat 0.80 to all defenders. That is right in direction and roughly right in size for stationary centre-backs, who lose about a third of their bonus in the published back-test, but it over-penalises attacking full-backs, who **gain**. Splitting the defender tilt by archetype (full-back against centre-back) is the correct refinement.

Stress-tested 19 Aug: Gabriel survives in the optimal squad up to a further 50% haircut on his remaining bonus and only drops out at 75%. The published back-test implies roughly a third. He is therefore **already adequately priced** at the current tilt and needs no manual adjustment.

Model bonus and DefCon **separately**. The rebalance cut CBI from 1 BPS per 2 actions to 1 per 3 specifically to break the double-dip, so treating them as co-occurring now overstates high-CBI defenders.

## Set pieces and penalties

**Added 19 Aug 2026.** A penalty is worth roughly 0.76 expected goals, and FPL prices players off last season's points rather than the job they are about to inherit. Newly appointed penalty and set-piece takers are therefore systematically under-priced at launch, and the mispricing decays over the first few gameweeks as the market updates.

Add a confidence-weighted set-piece and penalty term to player valuation. The value is concentrated in the cheap end, where the game has not repriced at all: a defender on penalties is the rarest and most mispriced combination. Antonee Robinson at Fulham (4.5m, 2.1% owned, listed as first-choice penalty taker) is the current standout to check. Confirm duty before acting, since pre-season taker lists are unreliable until competitive minutes confirm them.

## Chip roadmap (first half, provisional)

First set expires 13:30 GMT Sat 2 Jan 2027, the GW19 deadline. All four must be spent inside GW1-19 regardless of whether good doubles appear, which is why early and aggressive use is now standard rather than hoarding. First-half blank and double structure is **unknown** until the FA Cup and EFL Cup draws.

- **Wildcard GW6** — after the extended three-week September break, five gameweeks of real data, and the first honest review point for `MOVER_BLEND` and the season-phase correction. GW4 is the aggressive alternative. **Treat this as a trigger, not a date.** With five free transfers rolling, a bank of transfers is already a mini-wildcard; play it when a genuine fixture swing lands or when accumulated problems outrun the free transfers, not because the calendar said GW6.
- **Bench Boost** — lean post-Wildcard, once the bench is deliberately built for it. An early GW1/GW2 play is defensible only because no first-half double is confirmed, so the chip is a "field a full 15" play either way, and playing it after the Wildcard means the 15 is optimised for it.
- **Triple Captain** — **re-planned 19 Aug 2026, and now executable again.** The named windows were Haaland at home to a promoted side: **GW3 Coventry, GW7 Ipswich, GW16 Hull**. These were unexecutable under the no-Haaland build. If the Haaland build is adopted they are live again, and GW3 is the natural primary given the season-phase evidence points at the earliest gameweeks being his strongest. GW16 has the softest raw fixture but sits in the congested pre-Christmas run with rotation risk, and it collides with any GW16 Free Hit.
  - Fallback if Haaland is not owned: **Bruno Fernandes GW2, home to Ipswich**, off the back of Hull away in GW1. Cole Palmer GW4 at home to Hull is the secondary.
- **Free Hit** — hold as insurance for GW13/GW16 chaos rather than spending it early on fixture-chasing. One known proactive window if no emergency emerges: **GW3**, which pairs Arsenal against Chelsea with Man City against Coventry and Liverpool against Ipswich, and is awkward for squads holding players on both sides. Note the expiry: an unused Free Hit past GW16 is close to destroyed value.

Under the stated max-points posture, chips carry a larger share of the upside than weekly transfers do. Re-solve chip timing every wildcard-eligible week against actual fixture data, and hard-stop review at GW17. Chips left on the table on 2 Jan are pure destroyed value.

## Known modelling risks

- **Minutes dominate, and the model has already been caught here once.** On 18 Aug a defect was found where the transfer adjustment scaled attacking rates but left `p_start` untouched, so movers inherited their old club's start rate unchanged. It had three new Man City signings rated more likely to start than Haaland. Fixed via `MOVER_BLEND`, but the class of error stands: every point of xP is conditional on the player being on the pitch, and p(start) is what the API tells us least about.
- **BPS recalibration.** The 2026/27 BPS weights changed materially. Any bonus model trained on 2025/26 is misspecified until roughly GW6 of live data. Under-weight bonus early and say so in commentary.
- **Cold start.** GW1-4 has no 2026/27 match data. The model runs on 2025/26 priors from `vaastav/Fantasy-Premier-League`, blended with current prices and fixtures. A proxy for form, not a measurement of it.
- **Price inflation between seasons is material and easy to miss.** The hindsight-optimal 2025/26 squad cost £99.5m at that season's prices and £117.0m at this season's. Premium assets inflated far less than budget enablers (Haaland +11%, the £4.5m defenders +33%). Never carry a prior season's value judgement across without repricing it.
- **DefCon is a threshold, not a rate.** Modelling it off season averages will systematically misprice high-variance defenders.
- **T-48h cadence precedes most press conferences.** For a Saturday deadline the call lands Thursday, before Friday pressers. Rotation and fitness news is therefore incomplete, which compounds the minutes risk above. **A T-3h final sweep is now mandatory** rather than optional, and the T-48h output must be labelled provisional on late news. See `00-system-brief.md` section 6. Cross-reference at least two of Ben Dinnery / Premier Injuries, Fantasy Football Scout predicted lineups, and the FPL status flags. Widen minutes uncertainty for European clubs (nine in Europe, five in the Champions League) in midweek-adjacent gameweeks and across the festive congestion.
- **Season-average rates on a short horizon.** Addressed by the season-phase correction above, but the general class of error stands: any rate estimated over 38 gameweeks and applied to 8 assumes stationarity the season does not have.
- **Mirror model code drifts from the docs.** Confirmed 19 Aug: `model/features.py` did not contain the `MOVER_BLEND` fix the gameweek log recorded as committed, and `model/squad_ids.json` still held Revision 1. Verify the repo against the docs before trusting any scheduled run.
- **Published academic MILP work is weaker than it looks.** The arXiv framework benchmarked here optimises lineup selection only: no transfers, no hit costs, no chips, no injury modelling. Useful for forecasting-method comparison, not as an architecture to copy.

## Sources

- [AlpsCode: Hindsight optimization for FPL](https://alpscode.com/blog/hindsight-optimization/)
- [Premier League: FPL champion Erik Ibsen on captaincy and chips](https://www.premierleague.com/en/news/4672128/fpl-champion-how-to-pick-your-captain-and-maximise-your-chips)
- [open-fpl-solver (community reference MILP implementation)](https://github.com/sertalpbilal/FPL-Optimization-Tools)
- [arXiv 2505.02170: A data-driven framework for team selection in FPL](https://arxiv.org/abs/2505.02170)
- [All About FPL: 2026/27 chip strategy guide, first half](https://allaboutfpl.com/2026/08/2026-27-fpl-chip-strategy-guide-first-half-of-the-season/)
- [Fantasy Football Scout: BPS rebalance back-tested on 2025/26](https://www.fantasyfootballscout.co.uk/2026/07/20/fpl-2026-27-5-rule-changes-new-features-announced)
- [Premier League: Erik Ibsen interview, zero hits and captaincy](https://www.premierleague.com/en/news/4671784/fpl-champion-the-secrets-to-my-success)
- [FPL Review solver settings documentation](https://docs.fplreview.com/the-model/solvers/settings/)
- [RotoWire: Premier League set-piece takers 2026/27](https://www.rotowire.com/soccer/article/premier-league-set-piece-takers-2026-27-penalties-corners-free-kicks-for-every-team-126070)
