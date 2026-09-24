# Multi-strategy book construction and risk budget

**Status note.** 21 September 2026.  
**Scope.** Papers 07 and 08. Historical backtests only. No live capital.  
**Audience.** Applied data science. This note defines finance terms when they first appear.

This document uses short sentences and one meaning for each term (ASD-STE 100 style).

---

## 1. Where we stand

The working book is **not** a mix of four stock-picking rules.

The working book is:

1. One stock list from the FCF quality rule (paper 01).
2. A market on/off switch on the full book (SPY 200-day average).
3. A 10% cap on any one stock.

We tested other mixes. Those mixes did not give more stable growth on the 2020–2022 design window.

---

## 2. Goal

The product goal is a Halal stock book with **steady growth**.

Steady growth means:

- The book compounds over years.
- Large losses stay limited.
- Rules are clear enough to run again.
- Beating the Halal ETF (SPUS) is useful. It is not the primary score.

The primary scores are:

- Largest peak-to-trough loss (**max drawdown**).
- Return per unit of that loss (**Calmar**). See the glossary.

---

## 3. Glossary

Read this section first. Later sections use these words only.

| Term | Meaning in this lab |
| --- | --- |
| **Book** | The portfolio we would hold. One set of stock weights that sum to 1 (or cash). |
| **NAV** | Net asset value. The total value of the book on a day. |
| **Universe** | The stock list before ranking. Here: S&P 500 names after a business-activity filter. |
| **Halal / AAOIFI screen** | Hard filters. Banned businesses (banks, alcohol, weapons, and similar) plus debt, cash, and receivables ratios. A name that fails is out. |
| **Sleeve** | One ranking rule that outputs a list of names and weights. In a data pipeline, one sleeve is one model. |
| **Blend** | A weighted sum of sleeve outputs. Example: 40% of sleeve A plus 40% of sleeve B plus 20% of sleeve C. |
| **Rebalance** | Recalculate holdings. Monthly in this work, except SUE (event dates). |
| **Point-in-time** | Use only data that existed on that date. No future filings. |
| **SPY** | ETF that tracks the S&P 500. All-stock benchmark. |
| **SPUS** | Halal large-cap ETF. Halal benchmark. |
| **FCF** | Free cash flow. Cash from operations minus capital expenditure. Paper 01 ranks names by FCF / sales. |
| **ROIC** | Return on invested capital. Paper 02 keeps names with ROIC above 15%, then ranks by reinvestment. |
| **Dual momentum** | Paper 04. Keep names with strong 12-month return, skip the last month. That sleeve holds cash if SPY is below its 200-day average. |
| **SUE** | Standardized unexpected earnings. Paper 06. Buy names with a large earnings surprise. Hold 21 trading days. |
| **SMA** | Simple moving average. Here: mean of the last 200 daily SPY closes. |
| **Throttle / regime switch** | On/off rule for the **full book**. If off, the book holds cash. This is not the same as cash inside one 20% sleeve. |
| **Name cap** | Maximum weight for one stock. Extra weight goes to other names. |
| **CAGR** | Compound annual growth rate. Average yearly growth if the path were smooth. |
| **Volatility** | Annualised standard deviation of daily returns. A spread measure, not a loss measure. |
| **Max drawdown** | Worst fall from a peak to a later trough on the growth curve. Example: −30% means the curve fell 30% from a high. |
| **Sharpe** | Excess return over a 2% risk-free rate, divided by volatility. |
| **Calmar** | CAGR divided by the absolute max drawdown. Higher is better for this mandate. |
| **CVaR 5%** | Mean of the worst 5% of daily returns. A tail-loss measure. |
| **Top-5 weight** | Sum of the five largest stock weights on a date (or the mean of that sum across dates). |
| **Train window** | 2020-01-01 to 2022-12-31. Used to **design**. Contains the 2020 crash and the 2022 bear market. |
| **Test window** | 2023-01-01 to 2024-12-31. Used to **confirm**. A strong bull market. Do not retune after this window. |
| **Kill rule** | A pre-set fail condition. If a design fails, we stop it. We do not average it away. |

---

## 4. Data and test design

**Sample.** 19 December 2019 to 31 December 2024.

**Universe.** 503 S&P 500 tickers. 439 remain after the activity screen. Ratio screens run again at each month-end.

**Inputs.** Point-in-time AAOIFI snapshots, daily prices, ROIC history, SUE event file. Paper 07 stored these in `papers/07-book-construction/cache/`.

**Why a train/test split.** The full sample has one crash, one bear market, and two bull years. A search that maximises Calmar on the full sample will overweight 2023–2024. That is leakage. It is the same problem as tuning a model on the test set.

**Kill rules (frozen before the 12-config run).**

1. Train: 2022 calendar return more than 5 percentage points worse than SPUS.
2. Train: max drawdown worse than SPUS.
3. Train: Calmar below **both** FCF-only and SPUS.
4. Test: 2023 calendar return more than 15 percentage points worse than FCF-only.

ROIC-only cannot win as the engine if it has fewer than 252 live train days.

We did **not** use Monte Carlo to choose weights. Random mixes of this short sample hide the 2020 and 2022 paths. Those paths are the test.

---

## 5. Building blocks (sleeves)

Each sleeve is frozen. Papers 01, 02, 04, and 06 set the knobs. Papers 07 and 08 do not change those knobs. They only change **mix**, **on/off**, and **caps**.

| Sleeve | Paper | Job we assigned | Output |
| --- | --- | --- | --- |
| FCF quality | 01 | Always-on quality list | Monthly, cap-weighted |
| ROIC compounders | 02 | Second quality list | Monthly, cap-weighted |
| Dual momentum | 04 | Crash brake **inside that sleeve** | Monthly names, or cash if SPY < 200-day SMA |
| SUE | 06 | Short event satellite | Event dates, 21-day hold |
| High-beta | 05 | Risk / upside | **Out** of the steady-growth core |

**Important distinction.** Dual momentum cash is 20% of NAV if that sleeve has 20% weight. A throttle on NAV puts **100%** of the book in cash. These two designs are not the same product.

---

## 6. Paper 07 — first blend (the mix that failed)

**Design.** 40% FCF, 40% ROIC, 20% dual momentum. Optional 10% SUE. No name cap. No full-book SMA.

**Question.** Does this mix lose less than one sleeve, or is it the same large-tech book counted three times?

### Own-window results (each series from its first live day)

| Series | CAGR | Volatility | Sharpe | Max drawdown | Calmar |
| --- | ---: | ---: | ---: | ---: | ---: |
| 40/40/20 blend | 14.6% | 23.0% | 0.62 | −29.6% | 0.49 |
| Blend + 10% SUE | 17.3% | 22.7% | 0.73 | −31.0% | 0.56 |
| FCF only | 15.8% | 22.4% | 0.68 | −29.0% | 0.54 |
| ROIC only | 24.5% | 16.8% | 1.27 | −14.6% | 1.68 |
| Dual momentum only | 5.8% | 18.1% | 0.29 | −30.4% | 0.19 |
| SPY | 14.7% | 20.9% | 0.67 | −33.7% | 0.44 |
| SPUS | 17.8% | 21.6% | 0.77 | −30.8% | 0.58 |
| Full-book SMA preview | 16.5% | 14.5% | 0.99 | −11.5% | 1.44 |

ROIC looks best here. That result is not fair. ROIC has only 524 live days (about two years, late start). FCF and the blend have 1,259 live days and include 2020.

### Calendar years for the 40/40/20 blend

| Year | Blend | FCF | Dual momentum | SPY | SPUS |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2020 | 27.5% | 27.1% | 15.6% | 18.3% | 25.7% |
| 2021 | 28.9% | 32.0% | 22.5% | 28.7% | 35.6% |
| 2022 | **−26.6%** | −23.6% | −23.9% | **−18.2%** | −22.8% |
| 2023 | 33.9% | 33.0% | **3.3%** | 26.2% | 34.2% |
| 2024 | 21.9% | 21.6% | 18.6% | 25.3% | 27.7% |

### What this mix did

- The blend followed FCF. Overlap of FCF and ROIC names was moderate (mean Jaccard about 22%). Weights still sat in the same large names (MSFT, META, GOOG, AAPL).
- 2022 was worse than SPUS. The mix failed the “steady” test.
- Dual momentum at 20% did not stop 2022. It then missed 2023 (3.3% versus FCF 33%).
- Mean top-5 weight in the blend was 44%. Last date top names: MSFT 14%, META 11%, GOOG 11%, AAPL 7%, AVGO 5%.
- One-way turnover was 166% per year. At 10 basis points cost, drag was about 0.17% per year. Cost is not the failure.

**Decision.** Stop the 40/40/20 blend as the live book.

---

## 7. Paper 07 — 12-config search

Notebook: `papers/07-book-construction/blend-search.ipynb`.  
Figures: `papers/07-book-construction/figures/blend-search/`.  
Table: `papers/07-book-construction/cache/blend_search_results.csv`.

We changed **one** thing at a time. Sleeve rules stayed frozen.

| Set | Config | What we ran |
| --- | --- | --- |
| A | 1 | FCF 100% |
| A | 2 | ROIC 100% (report only) |
| A | 3 | FCF 50% / ROIC 50% |
| A | 4 | FCF 70% / ROIC 30% |
| B | 5 | Winner of A + 20% dual momentum |
| B | 6 | Winner of A (control) |
| C | 7–8 | Winner of A, SMA on **full NAV**; also FCF 100% with the same SMA |
| D | 9–10 | Best of A–C with SUE 10% versus SUE 0% |
| E | 11–12 | Winner so far with name cap 8% and 10% |

### Set A result

Only **FCF 100%** passed the train kill rules.

| Config | Train days | 2022 | Train max DD | Train Calmar | Train pass |
| --- | ---: | ---: | ---: | ---: | --- |
| FCF 100% | 756 | −23.5% | −29.0% | 0.30 | Yes |
| ROIC 100% | **22** | −9.8% | −13.5% | n/a | No. Too few train days |
| FCF 50 / ROIC 50 | 756 | −26.6% | −29.0% | 0.25 | No. Calmar below FCF and SPUS |
| FCF 70 / ROIC 30 | 756 | −25.4% | −29.0% | 0.27 | No. Same reason |

**Data-science reading.** ROIC is a second feature that is missing on the design window. Adding it to FCF did not add a new path in 2020. It made 2022 worse. Two labels. One book.

### Sets B and C result

Config 5 (FCF 80% + dual momentum 20%) failed train Calmar. 2023 was 29.7% versus FCF 32.9%. The 20% sleeve cash rule is too small to change 2022 and still costs 2023.

Config 8 (FCF 100%, SMA on full NAV) passed train and test.

| Book | 2022 | 2023 | Train Calmar | Train max DD | Full CAGR | Full max DD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| FCF 100%, no SMA | −23.5% | 32.9% | 0.30 | −29.0% | 15.7% | −29.0% |
| FCF 80% + dual mom 20% | −23.8% | 29.7% | 0.28 | −29.3% | 14.8% | −29.3% |
| **FCF 100% + NAV SMA (config 8)** | **−2.9%** | 21.6% | **1.66** | **−9.3%** | **17.9%** | **−9.3%** |
| SPUS | −22.8% | 34.2% | 0.31 | −30.8% | 17.8% | −30.8% |

2023 for config 8 is 21.6% versus FCF 32.9%. The gap is 11 points. Kill rule 4 allows 15 points. The switch costs bull-year return. It still passes the rule we froze.

### Set D (SUE) — we do not ship this

The search score maximised train Calmar and selected config 9: FCF 90% + SUE 10% + NAV SMA.

Config 9 numbers: 2022 −0.4%, 2023 +37.7%, full CAGR 25.3%, max DD −9.3%, Calmar 2.72.

We **rejected** this pick for the live book.

Reasons:

1. SUE did not stop 2022. The SMA already held cash. SUE added return in invested periods, mainly 2023–2024 (the test window).
2. The mandate is risk and path, not maximum Calmar on a bull sample.
3. SUE turnover is high. We did not want an event satellite before the risk budget.

Configs 11–12 (caps on the SUE book) are not the live line.

---

## 8. Paper 08 — risk budget on config 8

Notebook: `papers/08-risk-budget/code.ipynb`.  
Figures: `papers/08-risk-budget/figures/`.  
Table: `papers/08-risk-budget/name_cap_ladder.csv`.

**Locked book.** Config 8. FCF 100%. SMA on full NAV. No SUE. No ROIC. No dual-momentum weight.

**Remaining risk.** When the book is invested, a few large names hold most of the weight.

### Config 8 risk snapshot (no name cap)

| Item | Value |
| --- | --- |
| Live days | 1,259 |
| Days in cash | 326 (**25.9%**) |
| Days with SPY above 200-day SMA | 78.0% |
| SPY 2020 trough date | 23 March 2020. SMA already off (cash) |
| CAGR | 17.9% |
| Volatility | 13.6% |
| Max drawdown | −9.3% |
| Calmar | 1.93 |
| CVaR 5% (mean of worst days) | −2.08% per day |
| Beta versus SPY | 0.35 |
| Upside / downside capture versus SPY | 0.61 / 0.54 |
| Mean top-1 weight | 17.8% |
| Mean top-5 weight | 47.6% |
| Effective number of names (1 / HHI) | 15 |
| Names held | about 110 |

**How to read beta 0.35.** The book does not move 35% as much as the S&P 500 because it is in cash 26% of days. It is not because the stocks are defensive.

**How to read the 2020 path.** The 200-day SMA is slow. The book falls with the market first. Then it goes to cash. It misses part of the rebound. In 2022 the switch is on time. That is why 2022 is −2.9% and 2020 is still +20% but below always-on FCF.

**Sectors when invested.** Technology about 40–60%. Healthcare next. Communication services rise in 2023–2024. Those three groups are about 80% of weight. The activity screen already removed banks. A name cap does not create a multi-sector fund.

**Note on one figure.** In paper 08, the line labelled “FCF always on” used `throttle=None`. The code then kept the lab default SMA. That line is not a true always-on series. Use paper 07 for always-on FCF (−29% max drawdown).

### Name-cap ladder (same FCF, same SMA)

A cap does not remove names. It moves weight from the largest names to the next names. Count of names stays about 110.

| Book | 2020 | 2022 | 2023 | 2024 | CAGR | Max DD | Calmar | CVaR 5% | Top 5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Uncapped | 20.1% | −2.9% | 21.6% | 21.5% | 17.9% | −9.3% | 1.93 | −2.08% | 47.6% |
| Cap 15% | 19.7% | −3.1% | 21.6% | 21.4% | 17.7% | −9.4% | 1.89 | −2.05% | 45.0% |
| **Cap 10%** | 18.3% | −3.4% | 20.7% | 20.8% | **16.8%** | **−9.5%** | **1.77** | **−1.99%** | **37.2%** |
| Cap 8% | 17.7% | −3.3% | 19.4% | 19.9% | 16.1% | −9.6% | 1.69 | −1.95% | 32.5% |
| Cap 5% | 16.8% | −2.6% | 16.9% | 17.4% | 14.9% | −9.7% | 1.55 | −1.87% | 23.8% |

**Pass rule for a cap.** Top-5 falls by at least 3 percentage points. Train max drawdown does not get worse by more than 1 percentage point. CVaR does not get worse by more than 0.05 percentage points per day.

- Cap 15%: fails the top-5 cut (47.6% to 45.0%).
- Caps 10%, 8%, 5%: pass the tail checks.
- Rank of those three by train Calmar: 10% > 8% > 5%.

**Paper 08 pick: 10% name cap.**

You give up about 1.1 percentage points of CAGR (17.9% to 16.8%). Max drawdown stays about −9.5%. Mean top-5 falls from 48% to 37%. Top-1 falls from 18% to 10%.

Cap 5% starts to flatten the FCF engine. The largest quality names are the rule. A 5% cap fights the rule.

Caps do **not** change the 2020/2022 cash path. Drawdown charts for all caps sit in a band from about −7% to −9.7%. The SMA sets that floor. The cap only changes risk **while invested**.

---

## 9. Current live rule

Write the rule as code would write it:

```text
universe:     S&P 500, activity screen, point-in-time AAOIFI ratios
engine:       fcf_quality = 100%
              (top half of Halal names by FCF / sales, cap-weighted, monthly)
throttle:     spy_sma (200-day). Full NAV in cash if SPY is at or below the average
name_cap:     10%
breach_exit:  next_open (sell a failed AAOIFI name the session after the filing is known)
purify:       ex_date (donate impure dividend slice when the stock goes ex)
not in book:  roic, dual_momentum weight, sue, high_beta
cost assumption: 10 basis points one-way
```

In the `sleeves` package:

```python
FrozenRules().with_book(
    sleeve_weights={"fcf_quality": 1.0},
    throttle="spy_sma",
    name_cap=0.10,
    breach_exit="next_open",
    purify_schedule="ex_date",
)
```

Default `FrozenRules` still has older blend weights. The **research decision** is the block above. Update the package default when you freeze operations.

---

## 10. Designs we stopped

| Design | Status | Why |
| --- | --- | --- |
| 40% FCF / 40% ROIC / 20% dual momentum | Stop | Follows FCF. Worse 2022 than SPUS. Dual momentum misses 2023. |
| FCF + ROIC mixes | Stop | No extra 2020 path. Worse 2022. ROIC has almost no train history. |
| Dual momentum as 20% of NAV | Stop | Too small to change crashes. Costs the recovery year. |
| SUE 10% on the SMA book | Stop for now | Helps the bull test window. Does not add the crash control. |
| Name cap 15% | Stop | Almost no concentration cut. |
| Name cap 5% | Stop | Cuts CAGR more than it cuts crash loss. |

---

## 11. What this work does not prove

1. Results are one US sample, 2019–2024. One crash. One bear market. Two bull years.
2. The SMA is a slow switch. A faster crash than 2020 can still hit the book before cash.
3. Cash is US dollar cash in the backtest. Operations must still define the cash vehicle.
4. Technology weight stays high after the Halal screen. A 10% name cap does not remove sector concentration.
5. ROIC can still be useful when it has a 2020–2022 sample. It cannot be the engine today.
6. SUE can still be a small satellite after the risk budget. It is not in the live rule now.
7. Paper 08 compared caps. It did not compare a true always-on FCF line in the same figure (code default throttle). Paper 07 still holds that comparison.

---

## 12. Next work (papers 09–12)

The backlog in `README.md` still lists 09 as “book-level regime throttle”. **Paper 08 already uses that throttle.** Paper 09 should not search for the same switch. Paper 09 can document the SMA as a frozen operations rule, or test one alternative switch without a weight search.

Open items:

| Paper | Topic | Why it still matters |
| --- | --- | --- |
| 09 | Regime throttle write-up | Config 8 is live. Write the rule, cash days, and 2020 lag. Do not re-grid weights. |
| 10 | Compliance breach exits | Done. Next-session sell on a failed filing. Month-end wait left ~150 name-days non-compliant. P&L gap is tiny. |
| 11 | Purification | Done. Donate on the ex-date. Drag is about 1 bp of CAGR. 54% of held dividends have a usable ratio. |
| 12 | Turnover, costs, capacity | 10 bp was a stub. Measure real friction on this book. |
| Later | Diversification / CVaR sizing | Sector concentration remains after the 10% name cap. |

---

## 13. File map

| File | Content |
| --- | --- |
| `papers/07-book-construction/code.ipynb` | First 40/40/20 blend versus sleeves and benchmarks |
| `papers/07-book-construction/blend-search.ipynb` | 12-config search, train/test, kill rules |
| `papers/07-book-construction/cache/blend_search_results.csv` | Numbers for section 7 |
| `papers/07-book-construction/figures/` | Blend paths |
| `papers/07-book-construction/figures/blend-search/` | Search paths |
| `papers/08-risk-budget/code.ipynb` | Config 8 risk and name-cap ladder |
| `papers/08-risk-budget/name_cap_ladder.csv` | Numbers for section 8 |
| `papers/08-risk-budget/figures/` | Regime, sectors, cap ladder |
| `papers/09-regime-throttle/code.ipynb` | SMA-to-cash versus defensive sleeve |
| `papers/10-compliance-exits/code.ipynb` | Same-day / next-open / month-end AAOIFI exits |
| `papers/10-compliance-exits/exit_lag_results.csv` | Numbers for paper 10 |
| `papers/11-purification/code.ipynb` | Ex-date / quarter / year purification calendars |
| `papers/11-purification/purify_results.csv` | Numbers for paper 11 |
| `sleeves/` | Frozen live rules for papers 01, 02, 04, 05, 06, 10, 11 |

---

## 14. One-page recap

We asked if several Halal ranking rules, mixed as a blend, give steadier growth than one rule.

The mix did not.

One quality ranking (FCF) plus an on/off market switch on the full book plus a 10% single-name cap is the current research outcome.

The switch cuts the largest loss from about −29% to about −9%. The book is in cash about one day in four. The cap cuts typical top-5 weight from about 48% to about 37%. It does not change the cash path.

Paper 10: if a held name fails AAOIFI on a new filing, sell at the **next session**. Waiting until month-end left about 150 name-days of known non-compliance. The return path barely moves.

Paper 11: donate the impure slice of dividends on the **ex-date**. Covered hits are about 3.5 bp of NAV over five years (~1 bp of CAGR). Missing ratios on about half of dividends are a data gap, not a silent zero.

That is where we stand.
