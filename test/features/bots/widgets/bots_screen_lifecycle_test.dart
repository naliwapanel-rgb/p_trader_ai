import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/features/bots/bots_screen.dart';
import 'package:p_trader_ai/features/bots/data/backend_trading_bot.dart';
import 'package:p_trader_ai/features/bots/domain/trading_bot_repository.dart';
import 'package:p_trader_ai/features/bots/providers/backend_trading_bot_provider.dart';

void main() {
  testWidgets('runs start pause resume and stop actions', (tester) async {
    final repository = _FakeRepository(initialStatus: TradingBotStatus.stopped);

    await _pumpScreen(tester, repository);

    expect(find.byKey(const Key('bot-7-start-button')), findsOneWidget);

    await tester.tap(find.byKey(const Key('bot-7-start-button')));
    await tester.pumpAndSettle();

    expect(repository.actions, <TradingBotLifecycleAction>[
      TradingBotLifecycleAction.start,
    ]);

    expect(find.byKey(const Key('bot-7-pause-button')), findsOneWidget);

    expect(find.byKey(const Key('bot-7-stop-button')), findsOneWidget);

    await tester.tap(find.byKey(const Key('bot-7-pause-button')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('bot-7-resume-button')), findsOneWidget);

    await tester.tap(find.byKey(const Key('bot-7-resume-button')));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('bot-7-stop-button')));
    await tester.pumpAndSettle();

    expect(repository.actions, <TradingBotLifecycleAction>[
      TradingBotLifecycleAction.start,
      TradingBotLifecycleAction.pause,
      TradingBotLifecycleAction.resume,
      TradingBotLifecycleAction.stop,
    ]);

    expect(find.byKey(const Key('bot-7-start-button')), findsOneWidget);
  });

  testWidgets('prepares a draft bot before start', (tester) async {
    final repository = _FakeRepository(initialStatus: TradingBotStatus.draft);

    await _pumpScreen(tester, repository);

    await tester.tap(find.byKey(const Key('bot-7-prepare-button')));
    await tester.pumpAndSettle();

    expect(repository.actions, <TradingBotLifecycleAction>[
      TradingBotLifecycleAction.prepare,
    ]);

    expect(find.byKey(const Key('bot-7-start-button')), findsOneWidget);
  });
}

Future<void> _pumpScreen(
  WidgetTester tester,
  TradingBotRepository repository,
) async {
  tester.view.physicalSize = const Size(1000, 1400);
  tester.view.devicePixelRatio = 1;

  addTearDown(() {
    tester.view.resetPhysicalSize();
    tester.view.resetDevicePixelRatio();
  });

  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        backendTradingBotRepositoryProvider.overrideWithValue(repository),
      ],
      child: const MaterialApp(home: BotsScreen()),
    ),
  );

  await tester.pumpAndSettle();
}

class _FakeRepository implements TradingBotRepository {
  _FakeRepository({required TradingBotStatus initialStatus})
    : bot = _bot(initialStatus);

  BackendTradingBot bot;

  final List<TradingBotLifecycleAction> actions = <TradingBotLifecycleAction>[];

  @override
  Future<List<BackendTradingBot>> listBots({
    TradingBotStatus? status,
    int limit = 50,
    int offset = 0,
  }) async {
    return <BackendTradingBot>[bot];
  }

  @override
  Future<BackendTradingBot> getBot(int botId) async {
    return bot;
  }

  @override
  Future<TradingBotLifecycleResult> performLifecycle({
    required int botId,
    required TradingBotLifecycleAction action,
  }) async {
    actions.add(action);

    final previousStatus = bot.status;

    final nextStatus = switch (action) {
      TradingBotLifecycleAction.prepare => TradingBotStatus.stopped,
      TradingBotLifecycleAction.start => TradingBotStatus.running,
      TradingBotLifecycleAction.pause => TradingBotStatus.paused,
      TradingBotLifecycleAction.resume => TradingBotStatus.running,
      TradingBotLifecycleAction.stop => TradingBotStatus.stopped,
    };

    bot = _copyWithStatus(bot, nextStatus);

    return TradingBotLifecycleResult(
      action: action,
      previousStatus: previousStatus,
      status: nextStatus,
      changed: previousStatus != nextStatus,
      bot: bot,
    );
  }

  @override
  Future<BackendTradingBot> createBot(TradingBotCreateRequest request) {
    throw UnsupportedError('Not used');
  }

  @override
  Future<BackendTradingBot> updateBot({
    required int botId,
    required TradingBotUpdateRequest request,
  }) {
    throw UnsupportedError('Not used');
  }

  @override
  Future<void> deleteBot(int botId) {
    throw UnsupportedError('Not used');
  }
}

BackendTradingBot _bot(TradingBotStatus status) {
  final timestamp = DateTime.utc(2026, 8, 3, 12);

  return BackendTradingBot(
    id: 7,
    userId: 4,
    exchangeAccountId: null,
    name: 'Lifecycle Test Bot',
    description: 'Widget lifecycle test',
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
    strategyConfig: const <String, dynamic>{},
    lastError: null,
    startedAt: null,
    stoppedAt: null,
    lastRunAt: null,
    createdAt: timestamp,
    updatedAt: timestamp,
  );
}

BackendTradingBot _copyWithStatus(
  BackendTradingBot bot,
  TradingBotStatus status,
) {
  return BackendTradingBot(
    id: bot.id,
    userId: bot.userId,
    exchangeAccountId: bot.exchangeAccountId,
    name: bot.name,
    description: bot.description,
    strategyType: bot.strategyType,
    symbol: bot.symbol,
    category: bot.category,
    timeframe: bot.timeframe,
    status: status,
    paperTrading: bot.paperTrading,
    dryRun: bot.dryRun,
    riskPerTradePercent: bot.riskPerTradePercent,
    maxPositionValueUsd: bot.maxPositionValueUsd,
    maxDailyLossPercent: bot.maxDailyLossPercent,
    maxDrawdownPercent: bot.maxDrawdownPercent,
    stopLossPercent: bot.stopLossPercent,
    takeProfitPercent: bot.takeProfitPercent,
    strategyConfig: bot.strategyConfig,
    lastError: bot.lastError,
    startedAt: bot.startedAt,
    stoppedAt: bot.stoppedAt,
    lastRunAt: bot.lastRunAt,
    createdAt: bot.createdAt,
    updatedAt: bot.updatedAt,
  );
}
