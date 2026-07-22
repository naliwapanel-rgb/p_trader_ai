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
- 12J - Trend, Mean-Reversion and Scalping Strategies
- 12K - Arbitrage Bot Integration
## Remaining
- 12L - Strategy Builder and Copy-Trading Foundation (Completed)
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

## Phase 12J scope
Phase 12J introduces deterministic Trend, Mean-Reversion and
Scalping strategies using bounded historical market context.
Included:
- `TREND` strategy type
- `MEAN_REVERSION` strategy type
- `SCALPING` strategy type
- Validated Trend configuration
- Fast and slow exponential moving averages
- Trend momentum confirmation
- EMA-separation filtering
- Bullish and bearish Trend signals
- Position-aware Trend reversal exits
- Validated Mean-Reversion configuration
- Simple moving averages
- Population standard deviation
- Statistical z-score calculation
- Relative Strength Index calculation
- Oversold and overbought confirmation
- Position-aware statistical-mean exits
- Validated Scalping configuration
- Short-term EMA alignment
- Short-term momentum confirmation
- RSI Scalping confirmation
- Average True Range calculation
- Minimum and maximum volatility filters
- Position-aware Scalping reversal exits
- LONG, SHORT and BOTH direction modes
- Spread filters
- Turnover filters
- Deterministic confidence calculations
- Structured decision metadata
- Bounded market-history schemas
- Maximum 500 strategy-history samples
- Strict chronological-history validation
- Future-data rejection
- Latest-price consistency validation
- Optional history support in the strategy runner
- Process-local runtime ticker history
- Bot-scoped runtime history
- Duplicate-timestamp replacement
- Backwards-time rejection
- Runtime history clearing
- Runtime paper-position state integration
- Historical-candle backtest integration
- No-lookahead backtest history
- Intraday indicator warmup
- Existing 24-hour warmup compatibility
- In-memory Trend backtesting
- In-memory Mean-Reversion backtesting
- In-memory Scalping backtesting
- Existing RULE_BASED compatibility
- Existing DCA compatibility
- Existing Grid compatibility
- Strategy-registry integration
Excluded:
- Live exchange order placement
- Live exchange position modification
- Persistent runtime-history tables
- Persistent indicator tables
- Persistent backtest results
- New database tables
- New Alembic migrations
- Automatic market-history downloads
- Machine-learning prediction
- Automatic parameter optimization
- Walk-forward optimization
- Arbitrage strategy logic
- Strategy-builder functionality
- Copy trading
- New runtime schedulers
## Phase 12J strategy types
- `TREND`
- `MEAN_REVERSION`
- `SCALPING`
## Phase 12J market-history boundary
Strategy history is strictly bounded to 500 samples.
Runtime history is process-local and isolated by user, bot, symbol,
category and timeframe. It is not persisted to the database.
Backtesting uses only the current candle and earlier candles.
Future candles are never included in strategy evaluation.
## Phase 12J safety boundary
Trend, Mean-Reversion and Scalping strategies generate validated
BUY, SELL or HOLD decisions only. They must not import or invoke
database repositories, live exchange-order services, paper-trading
engines or runtime schedulers.
The existing runtime service may pass strategy decisions to the
isolated paper-trading engine only when the bot has paper trading
enabled. Phase 12J does not enable live exchange execution.
## Phase 12K scope
Phase 12K integrates deterministic Arbitrage evaluation into the
existing trading-bot strategy and runtime architecture.
Included:
- `ARBITRAGE` trading-bot strategy type
- Validated Arbitrage strategy configuration
- `TRIANGULAR` opportunity mode
- `CROSS_EXCHANGE` opportunity mode
- Starting-asset and starting-amount configuration
- Minimum-profit threshold configuration
- Exchange and symbol filters
- Quote-age and quote-time-skew limits
- Full-liquidity requirements
- Explicit runtime market definitions
- Fee, slippage and fixed-cost configuration
- Bounded Arbitrage quote context
- Duplicate quote rejection
- Future quote rejection
- Strategy-runner Arbitrage quote forwarding
- Existing Arbitrage profit-service reuse
- Existing cross-exchange scanner reuse
- Existing triangular scanner reuse
- Deterministic opportunity ranking
- Structured opportunity metadata
- Evaluation-only `HOLD` decisions
- Insufficient-quote safe handling
- Bybit triangular public ticker integration
- Public market-data provider registry
- Cross-exchange provider foundation
- Injectable secondary public market-data clients
- Cross-exchange ticker-batch validation
- Cross-exchange quote construction
- Triangular runtime quote forwarding
- Cross-exchange runtime quote forwarding
- Provider failure runtime error handling
- Existing authenticated Arbitrage API compatibility
- Existing runtime strategy compatibility
- Existing DCA, Grid, Trend, Mean-Reversion and Scalping compatibility
Excluded:
- Live Arbitrage order placement
- Atomic multi-leg exchange execution
- Paper-ledger Arbitrage position creation
- Persistent Arbitrage opportunity tables
- Persistent Arbitrage quote tables
- New database tables
- New Alembic migrations
- Authenticated exchange-client use for public quote collection
- Automatic balance transfer between exchanges
- Capital rebalancing
- Arbitrage inventory management
- Exchange withdrawal or deposit automation
- Flash-loan execution
- Decentralized-exchange transaction execution
- Historical Arbitrage backtesting
- Automatic parameter optimization
- Strategy-builder functionality
- Copy trading
## Phase 12K strategy type
- `ARBITRAGE`
## Phase 12K opportunity types
- `TRIANGULAR`
- `CROSS_EXCHANGE`
## Phase 12K runtime boundary
Triangular runtime evaluation uses normalized public spot ticker
data from the bot's configured exchange.
Cross-exchange runtime evaluation uses a public market-data
provider registry. The bot's primary exchange batch is reused,
while additional exchange batches are obtained only through
explicitly registered public market-data providers.
A missing or invalid secondary provider is handled by the existing
runtime error boundary. No authenticated trading client is used to
collect Arbitrage quote context.
## Phase 12K execution boundary
Arbitrage strategies always return `HOLD`.
Detected opportunities are included as structured evaluation
metadata. They are not translated into ordinary directional paper
orders because a two-leg or three-leg Arbitrage cycle cannot be
represented accurately by the existing one-symbol paper ledger.
The Arbitrage strategy, quote services and public provider
foundation must not import or invoke live exchange-order services,
paper-trading execution services, database repositories or the
authenticated exchange factory.
Phase 12K remains evaluation-only.
## Phase 12L scope
Phase 12L introduces reusable strategy templates and a safe
copy-trading foundation.
Included:
- Persistent owner-scoped strategy templates
- Draft, published and archived template states
- Private and public visibility
- Registered-strategy configuration validation
- Template version tracking
- Safe trading-bot creation from templates
- Independent follower-owned trading bots
- Persistent copy-trading subscriptions
- Active, paused and stopped subscription states
- Public published templates as copy sources
- Strict template-to-bot compatibility validation
- Paper-only execution-mode enforcement
- Internal paper-decision mirroring
- Duplicate-decision protection
- Stale template-version protection
- Per-follower failure isolation
- Authenticated template and subscription APIs
- OpenAPI and regression coverage
Excluded:
- Live copy trading
- Cross-user exchange-account access
- API-key or secret copying
- Balance, position or order copying
- Automatic fund transfers
- Leader control over follower risk settings
- Anonymous template publishing
- Public decision-mirroring endpoints
- Performance rankings or social feeds
- Revenue sharing or subscription payments
## Phase 12L safety boundary
A strategy template contains strategy, market, risk and safety
configuration only. It must not contain exchange credentials,
runtime state, balances, positions, orders or performance history.
Each follower owns an independent destination trading bot and must
supply any exchange account from their own account inventory.
Template-created and copy-subscribed bots must enable both
`paper_trading` and `dry_run`.
Decision mirroring writes only to the isolated paper-trading ledger.
It must not import or invoke live exchange-order placement,
position-management, withdrawal or fund-transfer services.
The internal mirroring service is not exposed as a public API
endpoint in Phase 12L.
