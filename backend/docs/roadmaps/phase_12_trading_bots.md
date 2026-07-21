# Phase 12 - Trading Bots
This roadmap was recovered and frozen after Phase 12C so the
remaining implementation can continue consistently.
## Completed
- 12A - Trading Bot Persistence Foundation
- 12B - Trading Bot Service and CRUD API
- 12C - Trading Bot Lifecycle Controls
## Remaining
- 12D - Bot Runtime and Scheduler Integration
- 12E - Strategy Interface and Rule-Based Runner
- 12F - Paper Trading Engine
- 12G - Bot Trade History and Performance Tracking
- 12H - Backtesting Engine
- 12I - DCA and Grid Bot Strategies
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
