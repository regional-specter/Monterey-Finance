<div align="center">

# Halal Quant Research Lab

<p>
  <img src="https://img.shields.io/badge/Phase-1%20Research-0A66C2" alt="Phase 1 Research">
  <img src="https://img.shields.io/badge/Strategies-15-f97316" alt="15 strategies">
  <img src="https://img.shields.io/badge/White%20Papers-Weekly-eab308" alt="Weekly white papers">
  <img src="https://img.shields.io/badge/Universe-AAOIFI%20%2F%20DJIM-22c55e" alt="AAOIFI / DJIM universe">
  <img src="https://img.shields.io/badge/Status-Active-16a34a" alt="Active">
</p>

<!--
  Hero image placeholder.
  Add `assets/research-hero.png` and uncomment the tag below.
-->
<!-- <img src="assets/research-hero.png" alt="Monterey Finance research lab" width="880"> -->

</div>

`Research/` is the **Phase 1 lab** for Monterey Finance: a backlog of **Halal quantitative strategies**, each taken from hypothesis through point-in-time backtest and into a published white paper. Work stays on historical market data. No live capital is deployed in this folder.

Every topic is researched against the **Halal-screened equity universe**, then written up in the same five-section report so weekly papers stay comparable: same metrics, same benchmarks, same friction accounting.

---

## How research is done here

Each of the **15 core strategy concepts** below follows the same loop:

1. **Pick a topic** from the backlog and lock the universe (AAOIFI vs. DJIM, sector screens, financial-ratio limits).
2. **Specify the strategy** with unambiguous entry, exit, sizing, and rebalancing rules — no look-ahead, point-in-time compliance only.
3. **Backtest** the strategy against a Halal index and an all-stock benchmark on real historical prices and fundamentals.
4. **Write the white paper** using the standardized structure below.
5. **Decide** whether the idea earns a follow-up, a revision, or a kill.

A topic is complete when its folder contains a finished white paper, the backtest artifacts needed to reproduce the tables, and an explicit note on purification drag, turnover, and stocks that enter or leave the universe.

Suggested layout as papers are opened:

```text
Research/
├── README.md
├── assets/                          
└── papers/
    ├── 01-fcf-ev/
    │   ├── whitepaper.md
    │   └── figures/
    ├── 02-roic-reinvestment/
    └── ...
```

---

## Standardized white paper structure

To deliver a clear report every week, every white paper uses this layout:

| Section | Target Content | Key Metrics to Include |
| --- | --- | --- |
| **1. Hypothesis & Theory** | Financial/economic logic behind the strategy and its interaction with Sharia constraints. | Target Factor, Universe Size, Screening Standard (AAOIFI vs. DJIM). |
| **2. Strategy Rules** | Unambiguous quantitative logic for selection, position sizing, and risk management. | Entry/Exit Rules, Rebalancing Frequency, Stop-Loss / Position Caps. |
| **3. Empirical Performance** | Backtest results comparing Strategy vs. Halal Index vs. All-Stock Benchmark. | CAGR, Max Drawdown, Sharpe Ratio, Sortino Ratio, Calmar Ratio. |
| **4. Factor Attribution** | Isolating whether outperformance stems from stock selection or structural sector bias. | Sector Exposure Delta, Alpha (α), Beta (β), Tracking Error. |
| **5. Limitations & Friction** | Realistic appraisal of implementation challenges. | Annualized Turnover, Slippage Estimate, Purification Drag. |

Sharia compliance is a **hard constraint**, not an optional overlay. Screens are applied at each point in time. If a held name fails during the sample, the paper must state the exit rule. Impure income that may require purification is reported, not ignored.

---

## Research backlog

Fifteen strategy concepts, grouped by the factor or structural mechanic they isolate inside a Halal-screened universe.

### Quality & Balance Sheet Dynamics

**1. Enterprise Value Cash Flow Yield (FCF/EV) ✅**

- **Mechanics:** Rank stocks by Free Cash Flow to Enterprise Value. Pair with AAOIFI debt-to-market cap limits (`< 30%`) to isolate capital-efficient firms.
- **White Paper Focus:** Measuring if leverage constraints naturally amplify the Quality Factor premium relative to the S&P 500.

<img width="5919" height="8060" alt="image 258" src="https://github.com/user-attachments/assets/a245e8d2-5fed-4f84-beeb-5499ef78d89a" />


**2. Return on Invested Capital (ROIC) Reinvestment Engine**

- **Mechanics:** Screen for high ROIC (`> 15%`) and high reinvestment rates among low-debt equities.
- **White Paper Focus:** Testing long-term compounding persistence in capital-light sectors like SaaS, Healthcare, and MedTech.

**3. Financial Distress & Distress-Risk Factor (SC_risk)**

- **Mechanics:** Sort stocks based on Altman Z-Score and Merton Distance-to-Default within Halal vs. non-Halal cohorts.
- **White Paper Focus:** Empirical proof of whether Sharia debt screens create an automatic systemic buffer against corporate bankruptcy during rate hikes.

### Momentum, Trend & Style Rotation

**4. Dual-Momentum Regime Switching**

- **Mechanics:** Combine 12-1 month relative price strength with a 200-day Simple Moving Average (SMA) absolute trend rule for market entry/exit.
- **White Paper Focus:** Evaluating drawdown protection during market crashes when speculative, highly leveraged momentum turnarounds are pre-filtered out.

**5. High-Beta Acceleration in Low-Debt Tech**

- **Mechanics:** Target top-quintile Beta stocks specifically in technology and clean energy, rebalanced monthly.
- **White Paper Focus:** Measuring downside capture vs. upside participation when running high-beta growth strategies without leverage risk.

**6. Earnings Momentum & Earnings Surprise (SUE)**

- **Mechanics:** Screen for Standardized Unanticipated Earnings (SUE) where actual EPS exceeds analyst consensus by `> 2σ`.
- **White Paper Focus:** Post-Earnings Announcement Drift (PEAD) efficacy in Halal equities vs. broad index constituents.

### Value & Dividend Mechanics

**7. Net Post-Purification Dividend Safety**

- **Mechanics:** Rank high-dividend Halal stocks by FCF coverage ratios, deducting calculated impure income (`< 5%` threshold) directly from net dividend yields.
- **White Paper Focus:** Designing post-purification yield optimization to prevent dividend drag.

**8. Debt-Adjusted Value (EBITDA / Enterprise Value)**

- **Mechanics:** Deep value strategy ranking stocks by EV/EBITDA rather than P/E to explicitly account for cash reserves and zero-interest debt models.
- **White Paper Focus:** Preventing "value traps" by enforcing point-in-time AAOIFI financial ratio screens on historically cheap stocks.

**9. Asset Light Book-to-Market (Intangible Adjusted)**

- **Mechanics:** Adjust Book Value by adding capitalized R&D and SG&A expenses, then rank the Halal universe by adjusted Price-to-Book.
- **White Paper Focus:** Fixing traditional Value metrics for technology-heavy Halal stock pools.

### Risk Parity & Volatility Modeling

**10. Inverse-Variance Low Volatility (Smart Beta)**

- **Mechanics:** Select the 50 lowest 252-day volatility stocks from the compliant universe and weight them by inverse variance.
- **White Paper Focus:** Evaluating Low-Vol anomaly returns as a structural proxy for fixed-income exposure.

**11. Minimum Variance Portfolio Optimization (MVO)**

- **Mechanics:** Apply Ledoit-Wolf covariance shrinkage estimation to construct a Minimum Variance portfolio within Halal equity bounds.
- **White Paper Focus:** Portfolio variance minimization in the absence of conventional bonds, preferred shares, or cash interest yields.

**12. Tail-Risk Constrained Downside Beta**

- **Mechanics:** Optimize position sizing based on Semi-Variance and Conditional Value at Risk (CVaR) rather than standard variance.
- **White Paper Focus:** Assessing left-tail risk asymmetry in Sharia vs. Non-Sharia index drawdowns during liquidity crunches.

### Macro, Sector & Arbitrage Strategies

**13. Dynamic Sector Neutralization (Factor Isolation)**

- **Mechanics:** Long top-factor stocks (e.g. Quality or Value) while neutralizing sector overweights (e.g. Tech/Staples) relative to the S&P 500 / MSCI World.
- **White Paper Focus:** Isolating pure factor performance from accidental sector tilt alpha.

**14. Point-in-Time Compliance Migration Arbitrage**

- **Mechanics:** Track stocks near financial ratio boundaries (e.g. `28%–29%` debt-to-market cap). Model forced buying/selling dynamics as stocks enter or exit official Islamic indices.
- **White Paper Focus:** Measuring price impact, liquidity drag, and exit rules for stocks losing compliance status.

**15. Sharia-ESG Multi-Factor Integration**

- **Mechanics:** Combine MSCI/AAOIFI financial screens with high ESG Governance (G) and Environmental (E) scores to build a composite multi-factor ranking.
- **White Paper Focus:** Synergies between Islamic financial restrictions and ESG sustainability factor premiums.

---

## What stays out of this folder

Live execution, brokerage integration, investor operations, and fund administration belong to **Phase 2**. This lab only produces a reproducible universe, fully specified strategies, backtests, and written findings — enough to decide whether further work is justified.
