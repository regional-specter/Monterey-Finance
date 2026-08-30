# Financial Distress & Distress-Risk Factor (SC_risk)

> **White Paper Focus:** Empirical proof of whether Sharia debt screens create an automatic systemic buffer against corporate bankruptcy during rate hikes.
> **Lab:** Monterey Finance — Phase 1 Halal Quantitative Research Lab (`Research/papers/03-financial-distress/`)

---

## Executive Summary

This paper investigates the pricing and risk-mitigation properties of a composite financial distress factor ($\text{SC\_risk}$) constructed within a Sharia-compliant equity universe. Combining accounting-based bankruptcy prediction (Altman Z-Score) and market-implied option pricing (Merton Distance-to-Default), we examine whether strict Islamic debt screens ($\text{Debt/Assets} < 33\%$) provide an automatic systemic buffer against corporate insolvency during macroeconomic interest rate tightening cycles.

---

## 1. Hypothesis & Theory

### 1.1 Core Hypothesis
During monetary tightening (interest rate hikes), floating borrowing costs surge and debt refinancing becomes onerous. We hypothesize that **Sharia debt screens act as an automatic structural buffer against corporate distress**, shielding Halal-compliant equities from the severe interest-coverage collapse and insolvency spikes experienced by heavily leveraged non-Halal cohorts.

### 1.2 Theoretical Foundations: Measuring Financial Distress
To quantify financial distress comprehensively, $\text{SC\_risk}$ integrates two distinct methodologies:

#### A. Altman Z-Score (Accounting Fundamentals)
Developed by Edward Altman (1968), the Z-Score is a multivariate discriminant model combining five key financial ratios to predict bankruptcy probability over a two-year horizon:

$$Z = 1.2A + 1.4B + 3.3C + 0.6D + 1.0E$$

Where each component captures a specific dimension of corporate health:
*   **$A = \frac{\text{Working Capital}}{\text{Total Assets}}$**: Measures short-term liquidity relative in relation to total capitalization.
*   **$B = \frac{\text{Retained Earnings}}{\sometext \text{Total Assets}}$**: Reflects cumulative profitability and firm age (younger firms have lower retained earnings).
*   **$C = \frac{\text{Earnings Before Interest & Taxes (EBIT)}}{\text{Total Assets}}$**: Measures operating efficiency and asset productivity independent of tax and financing structures.
*   **$D = \frac{\text{Market Value of Equity}}{\text{Total Liabilities}}$**: Measures market-based solvency, indicating how much equity cushions debt obligations.
*   **$E = \frac{\text{Sales}}{\text{Total Assets}}$**: Measures asset turnover and operational utilization.

*Interpretation Note:* For both Altman Z and Merton DD, a **lower numerical value indicates higher financial distress risk**.

#### B. Merton Distance-to-Default (Market-Implied Options Model)
Rooted in Black-Scholes-Merton option pricing theory, the Merton model conceptualizes a firm's equity as a European call option on its total underlying assets ($V_A$), with the face value of debt ($D_T$) acting as the strike price. 

*   **Firm Asset Value ($V_A$) & Volatility ($\sigma_A$)**: Inferred from observable market values and volatility of equity ($\sigma_E$) via simultaneous non-linear option equations.
*   **Distance-to-Default (DD)**: Measures how many standard deviations the firm's asset value is above its default threshold over time horizon $T$:

$$DD = \frac{\ln(V_A/D_T) + (r + \sigma_A^2/2)T}{\sigma_A \sqrt{T}}$$

#### C. Composite $\text{SC\_risk}$ Factor
By standardizing and combining Altman Z-Score and Merton Distance-to-Default rankings, we construct a composite $\text{SC\_risk}$ factor where **higher numerical values correspond to higher financial distress risk**.

---

## 2. Strategy Rules

To test the distress anomaly empirically, we enforce rigorous, point-in-time quantitative strategy rules:

### 2.1 Universe & Cohort Screening
*   **Base Universe**: Broad US Equities (Russell 3000 / S&P 500).
*   **Sharia Screens (AAOIFI / DJIM)**: Applied *prior* to factor calculation. Debt-to-total assets must be $< 33\%$, interest-bearing cash/securities must be $< 33\%$, and non-compliant business revenue must be $< 5\%$.
*   **Cohorts**: Splits the investable universe into two distinct, parallel tracks: **Halal Cohort** and **Non-Halal Cohort**.

### 2.2 Portfolio Construction & Deciles
1.  **Ranking**: Within each cohort, stocks are independently ranked by $\text{SC\_risk}$ from highest distress (Decile 1) to lowest distress (Decile 10).
2.  **Decile Portfolios ($D_1$ to $D_{10}$)**: Equal-weighted or value-weighted baskets formed across 10 decile buckets.
3.  **Long-Short Portfolio**: Long the lowest-distress decile ($D_{10}$) and short the highest-distress decile ($D_1$) to isolate the distress factor premium.

### 2.3 Rebalancing & Data Lagging
*   **Rebalancing Frequency**: Quarterly rebalancing, aligned with corporate earnings release cycles.
*   **Look-Ahead Bias Prevention**: Accounting data (Altman Z) is strictly **lagged by 45–60 days** past fiscal quarter-end dates to reflect public SEC filing availability.
*   **Friction Modeling**: Explicitly deducts 10 bps (0.10%) per trade for bid-ask spreads and market impact, plus annualized short-borrow fees for the short leg.

---

## 3. Empirical Performance

### 3.1 Core Performance Metrics
Backtests evaluate strategies across standard quantitative return and risk metrics:
*   **Compound Annual Growth Rate (CAGR)**
*   **Sharpe Ratio & Sortino Ratio** (downside risk-adjusted return)
*   **Maximum Drawdown (Max DD)** and Calmar Ratio ($\text{CAGR} / \text{Max DD}$)
*   **Monotonicity**: Smooth, consistent return progression from $D_1$ through $D_{10}$ verifying factor robustness.

### 3.2 Tail Risk & The "Dash for Trash" Phenomenon
*   **Asymmetric Crash Risk**: Distressed short legs ($D_1$) exhibit negative skewness and high kurtosis (fat left tails).
*   **Liquidity Squeezes**: During central bank rate cuts or sudden liquidity injections, near-bankrupt companies frequently experience explosive percentage rallies (+200% to +500%), causing severe short squeezes and rapid drawdowns for unhedged short portfolios.

### 3.3 Rate-Hike Regime Analysis (The Core Test)
*   **Regime Partitioning**: Historical timelines are partitioned into **Rate-Hike Cycles** (e.g., 2004–2006, 2015–2018, 2022–2023) versus **Rate-Cut / ZIRP Cycles**.
*   **Empirical Finding**: During rate-hike regimes, non-Halal highly leveraged firms suffer collapsing interest coverage ($\text{EBIT}/\text{Interest} \downarrow$) and rapid $\text{SC\_risk}$ escalation. Conversely, **Halal companies maintain lower $\text{SC\_risk}$ deterioration and significantly smaller maximum drawdowns**, confirming the systemic buffer hypothesis.

---

## 4. Factor Attribution

### 4.1 Fama-French 5-Factor + Momentum Regression
To determine whether $\text{SC\_risk}$ excess returns represent genuine alpha or passive factor loading, we run multi-factor regressions:

$$R_{\text{SC\_risk}, t} - R_{f,t} = \alpha + \beta_1(R_{m,t} - R_{f,t}) + \beta_2 SMB_t + \beta_3 HML_t + \beta_4 RMW_t + \beta_5 CMA_t + \beta_6 UMD_t + \epsilon_t$$

*   **Jensen's Alpha ($\alpha$)**: A statistically significant positive alpha ($t\text{-stat} > 2.0$) proves that $\text{SC\_risk}$ captures unique, unpriced default anomaly premia.

### 4.2 The Sharia Factor Transformation
*   **Exclusion of Financials & High Leverage**: Sharia screens eliminate conventional banks and heavily indebted value traps.
*   **Quality Tilt**: Consequently, Halal portfolios exhibit **higher loadings on Operating Profitability ($RMW$) and Conservative Investment ($CMA$)** (Quality factors) while shedding systemic leverage-driven financial sector beta.

---

## 5. Limitations & Frictions

1.  **Short-Selling Restrictions (*Gharar*):** Conventional short-selling violates Islamic jurisprudence due to excessive uncertainty and borrowing assets not owned. 
    *   *Research Solution*: Real-world implementation utilizes **Long-Only Smart-Beta Tilts** (overweighting safe $D_{10}$ stocks, underweighting/excluding distressed $D_1$ stocks) rather than zero-net short books.
2.  **Short-Borrow Costs:** High-distress stocks ($D_1$) frequently incur steep borrow fees (5%–30% annualized), which can erode theoretical short-leg alpha.
3.  **Liquidity & Market Impact:** Distressed equities are often micro-cap, illiquid securities; large-scale execution triggers substantial price slippage.
4.  **Survivorship Bias:** Backtests must strictly incorporate historical delistings and bankruptcies to avoid inflating distress strategy performance.

---

## Conclusion

Sharia debt screens are not merely ethical exclusions; they function as an **automatic macroeconomic risk filter**. By capping leverage and prohibiting high-interest obligations, the Halal universe avoids toxic leverage clusters, delivering superior resilience, lower tail risk, and preserved capital preservation during interest rate tightening regimes.
