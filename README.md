# Monterey-Finance

## 1. Product Vision

To build an institutional-grade, all-in-one research, backtesting, and execution terminal optimized exclusively for Halal investments. The platform eliminates compliance drift by baking AAOIFI quantitative screens directly into the core data pipeline, allowing traders to generate, natural-language prompt, backtest, and deploy strategies without ever trading non-compliant assets.

---

## 2. Target User Personas

- **The Independent Halal Swing Trader:** Wants to prompt or visually build strategies (e.g., "Buy large-cap tech when RSI < 30") but needs the system to *automatically* filter out companies that fail the 33% debt or 5% haram revenue thresholds.
- **The Systematic Halal Investor:** Requires point-in-time historical backtesting to see how a quantitative factor model (like low-debt quality tilt) performed over the last 5–10 years without look-ahead bias from changing corporate balance sheets.

---



## 3. Core Module Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Unified Terminal                     │
├──────────────────┬──────────────────┬───────────────────┤
│  AI Prompt &     │  Interactive     │  Historical       │
│  Strategy Builder│  Halal Screener  │  Backtesting Engine│
├──────────────────┴──────────────────┴───────────────────┤
│         Live Data Feeds & Brokerage Execution           │
└─────────────────────────────────────────────────────────┘

```

---



## 4. Key Functional Requirements



### Module 1: Natural Language & Visual Strategy Builder

- **Plain English to Rules:** Users can type a prompt (e.g., *"Backtest a momentum strategy on Shariah-compliant US equities where price crosses above the 50-day moving average"*).
- **Automatic Universe Constraint:** The builder automatically wraps every query with a global modifier: `AND Shariah_Status == COMPLIANT`. Users cannot write strategies that evaluate prohibited sectors or breached financial ratios.
- **Editable Rule Blocks:** Translates the prompt into structured visual or code logic blocks (Entries, Exits, Position Sizing, Risk Parameters) for easy refinement.



### Module 2: The Shariah Compliance Pipeline (Integrated)

- **Sector Screen Filter:** Automatically drops tickers whose primary operations involve non-permissible activities, ensuring non-permissible revenue remains $< 5$.
- **36-Month Rolling Denominator Engine:** Computes financial ratios against a rolling 36-month moving average of Market Capitalization:

$$\text{Debt Ratio} = \frac{\text{Total Interest-Bearing Debt}}{\text{Market Cap}_{36M}} < 33$$

$$\text{Liquidity Ratio} = \frac{\text{Cash} + \text{Interest-Bearing Securities}}{\text{Market Cap}_{36M}} < 33$$

$$\text{Receivables Ratio} = \frac{\text{Accounts Receivables}}{\text{Market Cap}_{36M}} < 49$$

- **Compliance Drift Guardrails:** If a quarterly earnings update pushes a stock past a threshold during an active backtest or live paper trade, the system flags a **"Compliance Event"** and executes a pre-set rule (e.g., immediate liquidation or 3-day grace period exit).



### Module 3: Historical Backtesting Engine

- **Point-in-Time Universe Selection:** Resolves survivorship bias by ensuring stocks entering or exiting Shariah compliance historically are only traded *after* their quarterly financial filings are officially public.
- **Performance Analytics Dashboard:** Computes Net Profit, Win Rate, Maximum Drawdown, Sharpe Ratio, and provides a **Purified Return Metric** (subtracting impure dividend yields intended for charity).
- **Regime Stress Testing:** Allows users to run strategies across major historical market shocks (e.g., 2020, 2022) to see how halal-constrained portfolios behave under stress.



### Module 4: Strategy Vault & Community Leaderboard

- **Strategy Vault:** Save, version control, and iterate on custom technical indicators and strategy rules.
- **Halal Strategy Leaderboard:** A public discovery space where users can share backtested halal strategies, inspect logic, and fork community-vetted ideas into their own workspace.

---



## 5. Non-Functional Requirements & Specs

- **Backtest Latency:** Complete a 5-year multi-asset historical backtest in $< 3$ seconds.
- **Data Precision:** Fundamental quarterly balance sheet mappings synchronized with daily market cap moving averages to eliminate calculation errors.
- **Execution Safety:** Strict risk guards preventing order routing if an asset's live compliance status flips to *Non-Compliant* mid-session.

