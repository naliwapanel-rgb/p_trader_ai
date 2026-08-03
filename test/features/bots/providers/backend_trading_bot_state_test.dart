import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/features/bots/data/backend_trading_bot.dart';
import 'package:p_trader_ai/features/bots/providers/backend_trading_bot_state.dart';

void main() {
  group('BackendTradingBotState', () {
    test('starts empty and unloaded', () {
      const state = BackendTradingBotState.initial();

      expect(state.bots, isEmpty);
      expect(state.busyBotIds, isEmpty);
      expect(state.isLoading, isFalse);
      expect(state.isMutating, isFalse);
      expect(state.hasLoaded, isFalse);
      expect(state.errorMessage, isNull);
      expect(state.infoMessage, isNull);
    });

    test('filters active bot statuses', () {
      final state = BackendTradingBotState(
        bots: <BackendTradingBot>[
          _bot(id: 1, status: TradingBotStatus.running),
          _bot(id: 2, status: TradingBotStatus.starting),
          _bot(id: 3, status: TradingBotStatus.paused),
          _bot(id: 4, status: TradingBotStatus.stopped),
        ],
        busyBotIds: const <int>{},
        isLoading: false,
        isMutating: false,
        hasLoaded: true,
      );

      expect(state.activeBots.map((bot) => bot.id), <int>[1, 2, 3]);
      expect(state.runningBots.map((bot) => bot.id), <int>[1, 2]);
      expect(state.pausedBots.map((bot) => bot.id), <int>[3]);
    });

    test('finds bots and reports busy IDs', () {
      final state = BackendTradingBotState(
        bots: <BackendTradingBot>[
          _bot(id: 7, status: TradingBotStatus.stopped),
        ],
        busyBotIds: const <int>{7},
        isLoading: false,
        isMutating: false,
        hasLoaded: true,
      );

      expect(state.findById(7)?.id, 7);
      expect(state.findById(99), isNull);
      expect(state.isBotBusy(7), isTrue);
      expect(state.isBotBusy(99), isFalse);
    });

    test('clears transient messages', () {
      final state = BackendTradingBotState(
        bots: const <BackendTradingBot>[],
        busyBotIds: const <int>{},
        isLoading: false,
        isMutating: false,
        hasLoaded: true,
        errorMessage: 'Failed',
        infoMessage: 'Updated',
      );

      final cleared = state.copyWith(clearError: true, clearInfo: true);

      expect(cleared.errorMessage, isNull);
      expect(cleared.infoMessage, isNull);
      expect(cleared.hasLoaded, isTrue);
    });
  });
}

BackendTradingBot _bot({required int id, required TradingBotStatus status}) {
  final createdAt = DateTime.utc(2026, 8, 3, id);

  return BackendTradingBot(
    id: id,
    userId: 7,
    exchangeAccountId: 3,
    name: 'Bot $id',
    description: 'Test bot',
    strategyType: TradingBotStrategyType.momentum,
    symbol: 'BTCUSDT',
    category: TradingBotCategory.linear,
    timeframe: TradingBotTimeframe.fiveMinutes,
    status: status,
    paperTrading: true,
    dryRun: true,
    riskPerTradePercent: 1,
    maxPositionValueUsd: 25,
    maxDailyLossPercent: 3,
    maxDrawdownPercent: 10,
    stopLossPercent: 2,
    takeProfitPercent: 4,
    strategyConfig: const <String, dynamic>{'period': 14},
    lastError: null,
    startedAt: null,
    stoppedAt: null,
    lastRunAt: null,
    createdAt: createdAt,
    updatedAt: createdAt,
  );
}
