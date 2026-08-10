# **Monterey Finance**

Monterey-Finance is a quantitative research project focused on designing, testing, and comparing investment strategies for a pool of Sharia-compliant stocks. All work in the first phase is grounded in historical market data, with strategies evaluated through backtests before any live trading is considered.

## **Project Phases**

### **Phase 1: Quantitative Research**

Phase 1 is research only, and no live capital will be deployed during this stage. The main tasks are to define the Sharia-compliant stock universe, build quantitative trading and investment strategies for that universe, backtest each strategy against real historical market data, and measure and compare strategy performance.

Phase 1 deliverables include a documented stock universe with compliance rules applied, one or more strategy definitions with clear entry, exit, and risk rules, backtest results with standard performance metrics, and a written summary of findings and limitations.

### **Phase 2: Fund Operations (Future)**

Phase 2 is not in scope for the current work, but it may eventually include live portfolio management, investor operations, and regulatory setup similar to a hedge fund. This phase will only be considered after Phase 1 research produces acceptable and repeatable results.

## **Research Scope**

### **Stock Universe**

The project considers only stocks that pass Sharia compliance screens, which may include sector filters to remove non-permissible business activities and financial ratio limits on debt, cash, and receivables relative to market value. Compliance rules must be applied at each point in time during a backtest, meaning a stock that fails a screen on a given date must not be held on that date.

### **Strategy Development**

Strategies are rule-based and quantitative, and each strategy must define how stocks are selected from the compliant universe, when to open and close positions, and how position sizing and risk limits are applied. All strategies must be testable on historical data without look-ahead bias.

### **Backtesting**

Backtests use real historical price and fundamental data, and each backtest must use point-in-time compliance status for each stock, account for stocks that enter or leave the universe over time, and report net return, drawdown, volatility, and risk-adjusted measures where the data allows. These results are used to compare strategies and determine whether further work is justified.

## **Compliance Principles**

Sharia compliance is a hard constraint rather than an optional filter. Non-compliant stocks are excluded from the universe, and if a held stock becomes non-compliant during a backtest, the strategy must follow a defined exit rule. Performance reports should also note any impure income that may require purification.

## **Out of Scope (Phase 1)**

The following items are not part of Phase 1: live order execution or brokerage integration, investor onboarding or fund administration, natural-language strategy builders or public strategy sharing, and real-time trading terminals. These items may be revisited in Phase 2 if the research results support them.

## **Success Criteria for Phase 1**

Phase 1 is complete when the project has a reproducible compliant stock universe for a defined market and time range, at least one fully specified and backtested strategy, documented backtest methodology and results, and a clear recommendation on whether to proceed to Phase 2.
