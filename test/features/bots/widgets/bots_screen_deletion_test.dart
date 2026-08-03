import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/features/bots/bots_screen.dart';
import 'package:p_trader_ai/features/bots/data/backend_trading_bot.dart';
import 'package:p_trader_ai/features/bots/domain/trading_bot_repository.dart';
import 'package:p_trader_ai/features/bots/providers/backend_trading_bot_provider.dart';

void main() {
  testWidgets('confirms before deleting an inactive bot', (tester) async {
    final repository = _FakeRepository(initialStatus: TradingBotStatus.stopped);

    await _pumpScreen(tester, repository);

    final deleteButton = find.byKey(const Key('bot-9-delete-button'));

    expect(deleteButton, findsOneWidget);

    await tester.ensureVisible(deleteButton);
    await tester.tap(deleteButton);
    await tester.pumpAndSettle();

    expect(find.text('Delete Trading Bot?'), findsOneWidget);
    expect(repository.deleteCalls, 0);

    await tester.tap(find.text('Cancel'));
    await tester.pumpAndSettle();

    expect(repository.deleteCalls, 0);
    expect(find.text('Deletion Test Bot'), findsOneWidget);

    await tester.tap(deleteButton);
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('confirm-delete-bot-button')));
    await tester.pumpAndSettle();

    expect(repository.deleteCalls, 1);
    expect(repository.bots, isEmpty);

    expect(find.text('No trading bots yet'), findsOneWidget);

    expect(find.text('Deletion Test Bot'), findsNothing);
  });

  testWidgets('does not expose deletion for an active bot', (tester) async {
    final repository = _FakeRepository(initialStatus: TradingBotStatus.running);

    await _pumpScreen(tester, repository);

    expect(find.byKey(const Key('bot-9-delete-button')), findsNothing);

    expect(find.byKey(const Key('bot-9-pause-button')), findsOneWidget);

    expect(find.byKey(const Key('bot-9-stop-button')), findsOneWidget);

    expect(repository.deleteCalls, 0);
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
    : bots = <BackendTradingBot>[_bot(initialStatus)];

  List<BackendTradingBot> bots;
  int deleteCalls = 0;

  @override
  Future<List<BackendTradingBot>> listBots({
    TradingBotStatus? status,
    int limit = 50,
    int offset = 0,
  }) async {
    return bots
        .where((bot) => status == null || bot.status == status)
        .toList(growable: false);
  }

  @override
  Future<BackendTradingBot> getBot(int botId) async {
    return bots.firstWhere((bot) => bot.id == botId);
  }

  @override
  Future<void> deleteBot(int botId) async {
    deleteCalls += 1;

    bots = bots.where((bot) => bot.id != botId).toList(growable: false);
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
  Future<TradingBotLifecycleResult> performLifecycle({
    required int botId,
    required TradingBotLifecycleAction action,
  }) {
    throw UnsupportedError('Not used');
  }
}

BackendTradingBot _bot(TradingBotStatus status) {
  final timestamp = DateTime.utc(2026, 8, 3, 12);

  return BackendTradingBot(
    id: 9,
    userId: 4,
    exchangeAccountId: 3,
    name: 'Deletion Test Bot',
    description: 'Deletion widget test',
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
