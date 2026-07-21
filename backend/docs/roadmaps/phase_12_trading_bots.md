# Phase 12 - Trading Bots
This roadmap was recovered and frozen after Phase 12C so the
remaining implementation can continue consistently.
## Completed
- 12A - Trading Bot Persistence Foundation
- 12B - Trading Bot Service and CRUD API
- 12C - Trading Bot Lifecycle Controls
- 12D - Bot Runtime and Scheduler Integration
- 12E - Strategy Interface and Rule-Based Runner
- 12F - Paper Trading Engine
- 12G - Bot Trade History and Performance Tracking
- 12H - Backtesting Engine
- 12I - DCA and Grid Bot Strategies
## Remaining
- 12J - Trend, Mean-Reversion and Scalping Strategies
- 12K - Arbitrage Bot Integration
- 12L - Strategy Builder and Copy-Trading Foundation
- 12M - Security, Recovery and Integration Testing
## Phase 12D scope
Phase 12D connects persisted trading-bot lifecycle state to the
existing in-memory automation runtime.
Included:
- Internal trading-bot heartbeat worker handler
- One internal schedule per running trading bot
- Schedule start, pause, resume and stop coordination
- Runtime heartbeat persistence through `last_run_at`
- Runtime errors persisted through `last_error`
- Failed runtime bots moved to `ERROR`
- Recovery of eligible `RUNNING` bots during application startup
- Graceful shutdown through the existing scheduler shutdown flow
Excluded:
- Strategy signal generation
- Paper-trade execution
- Live exchange execution
- Position opening or closing
- Backtesting
- DCA, Grid or Arbitrage strategy logic
## Safety boundary
The Phase 12D runtime handler must never import or invoke exchange
order-placement services. It performs heartbeat and runtime-state
management only.

## Phase 12E scope
Phase 12E introduces a common strategy architecture and connects
safe strategy evaluation to each running trading bot tick.
Included:
- Strategy context and decision schemas
- Common asynchronous strategy interface
- Strategy registry
- Initial `RULE_BASED` strategy
- Validated `BUY`, `SELL` and `HOLD` decisions
- Bybit normalized ticker context
- Strategy configuration validation before runtime startup
- Strategy evaluation during scheduled bot ticks
- Runtime errors persisted through the existing error boundary
Excluded:
- Market or limit-order placement
- Paper-trade creation
- Live exchange execution
- Position opening or closing
- Backtesting
- DCA, Grid or Arbitrage execution
## Phase 12E safety boundary
Strategy evaluation returns decisions only. It must not import or
invoke exchange order-placement or position-management services.

## Phase 12F scope
Phase 12F introduces isolated simulated execution for trading-bot
strategy decisions.
Included:
- Persistent paper-trading accounts
- Persistent paper orders and positions
- Simulated market-order fills
- Configurable trading fees and adverse slippage
- Long and short paper positions
- Same-direction position increases
- Opposite-direction position closes
- Weighted average entry-price calculation
- Realized and unrealized profit and loss
- Paper-account cash, reserved balance and equity updates
- HOLD decision mark-to-market updates
- Position-size limits using the bot risk configuration
- Transactional rollback on simulated execution failure
- Runtime execution only when `paper_trading` is enabled
- Paper-execution results included in runtime tick results
Excluded:
- Live exchange-order placement
- Real exchange position changes
- Limit-order simulation
- Stop-loss and take-profit execution
- Trade-history and performance APIs
- Backtesting
- DCA, Grid and Arbitrage strategy execution
## Phase 12F safety boundary
The paper-trading engine writes only to the isolated paper-trading
ledger. It must not import or invoke exchange-order placement
services. Public trade-history and performance access is deferred
to Phase 12G.

## Phase 12G scope
Phase 12G exposes authenticated, user-scoped paper-trading history
and performance reporting for each trading bot.
Included:
- Paper-trading account summary
- Paginated paper-order history
- Paginated open and closed position history
- Position-status filtering
- Order count
- Trade and completed-trade counts
- Open-trade count
- Winning, losing and breakeven trade counts
- Gross realized profit and loss
- Closed-position fees
- Net realized profit and loss
- Unrealized profit and loss
- Total fees
- Total net account profit and loss
- Win rate
- Average win
- Average loss
- Profit factor
- Account return percentage
- Authenticated and user-scoped read-only API endpoints
- OpenAPI route registration
Excluded:
- Backtesting
- Performance forecasting
- Equity-curve persistence
- Live exchange trade history
- Live exchange performance reporting
- Strategy modification
- DCA, Grid or Arbitrage execution
- Copy trading
## Phase 12G API endpoints
- `GET /trading-bots/{bot_id}/paper-trading/account`
- `GET /trading-bots/{bot_id}/paper-trading/orders`
- `GET /trading-bots/{bot_id}/paper-trading/positions`
- `GET /trading-bots/{bot_id}/paper-trading/performance`
## Phase 12G safety boundary
Phase 12G is read-only. It calculates performance from the isolated
paper-trading ledger and must not create orders, modify positions,
change account balances or invoke live exchange services.

## Phase 12H scope
Phase 12H introduces deterministic, in-memory backtesting for
persisted trading-bot configurations.
Included:
- Validated timezone-aware historical candle input
- OHLC range and chronological-sequence validation
- Overlapping-candle rejection
- Maximum historical-series size validation
- Deterministic chronological market replay
- Trailing 24-hour market context
- No-lookahead market-data handling
- Strategy evaluation through the existing strategy runner
- Warmup-frame handling
- In-memory simulated portfolio state
- Long and short position execution
- Same-direction position increases
- Opposite-direction position closes
- Adverse slippage and trading fees
- Risk-based position sizing
- Maximum-position-value enforcement
- Minimum-order-notional rejection
- Optional forced position closure at the end of a backtest
- Order-fill ledger
- Completed-trade ledger
- Per-frame portfolio snapshots
- Equity-curve generation
- Peak-equity tracking
- Maximum drawdown in USD and percentage
- Net trade performance metrics
- Win rate
- Average win and loss
- Profit factor
- Total return
- Authenticated and user-scoped backtest API
- OpenAPI route registration
Excluded:
- Persistent backtest database tables
- Persistent backtest result storage
- Automatic historical-data downloads
- Live exchange execution
- Paper-trading ledger modifications
- Background scheduling
- Strategy optimization
- Parameter searching
- Walk-forward optimization
- DCA, Grid and Arbitrage strategy logic
- Copy trading
## Phase 12H API endpoint
- `POST /trading-bots/{bot_id}/backtest`
## Phase 12H safety boundary
Backtest execution operates entirely in memory. It must not create
or modify paper-trading accounts, paper positions, paper orders or
live exchange orders. The database is used only to authenticate the
user and retrieve the user-owned trading-bot configuration.

## Phase 12I scope
Phase 12I introduces deterministic DCA and Grid trading strategies
using the existing strategy, paper-trading and backtesting
architecture.
Included:
- Validated DCA strategy configuration
- LONG and SHORT DCA directions
- Configurable DCA entry spacing
- Configurable DCA maximum-entry limits
- Optional initial DCA market-change threshold
- DCA take-profit exits
- Validated Grid strategy configuration
- Configurable Grid lower and upper prices
- Configurable Grid levels
- Equally spaced Grid price levels
- LONG and SHORT Grid directions
- Configurable Grid maximum-entry limits
- Grid take-profit exits
- Market-spread filters
- Minimum-turnover filters
- Deterministic strategy confidence
- Structured decision metadata
- Stateful strategy execution context
- Current position state
- Entry-count state
- Last-entry-price state
- Last-order state
- Completed-trade count state
- Paper-ledger strategy-state derivation
- Runtime strategy-state integration
- In-memory backtest strategy-state derivation
- DCA backtesting
- Grid backtesting
- Existing RULE_BASED strategy compatibility
- Strategy-registry integration
Excluded:
- Live exchange order placement
- Live position modification
- New database tables
- New Alembic migrations
- Persistent strategy-state tables
- Arbitrage strategy logic
- Trend strategy logic
- Mean-reversion strategy logic
- Scalping strategy logic
- Copy trading
- Automatic parameter optimization
- Walk-forward optimization
- New runtime schedulers
## Phase 12I strategy types
- `DCA`
- `GRID`
## Phase 12I safety boundary
DCA and Grid strategies generate validated BUY, SELL or HOLD
decisions only. They must not import or invoke live exchange order
services, paper-trading repositories, database sessions or runtime
schedulers.
Runtime state is derived from the isolated paper-trading ledger.
Backtest state is derived from the current in-memory backtest
portfolio and order history. Strategy evaluation does not directly
modify either state.
