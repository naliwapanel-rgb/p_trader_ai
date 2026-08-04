import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/features/bots/bots_screen.dart';
import 'package:p_trader_ai/features/bots/data/backend_trading_bot.dart';
import 'package:p_trader_ai/features/bots/domain/trading_bot_repository.dart';
import 'package:p_trader_ai/features/bots/providers/backend_trading_bot_provider.dart';

void main() {
  testWidgets('opens editor and updates an inactive bot', (tester) async {
    final repository = _FakeRepository(initialStatus: TradingBotStatus.stopped);

    await _pumpScreen(tester, repository);

    final editButton = find.byKey(const Key('bot-14-edit-button'));

    expect(editButton, findsOneWidget);

    await tester.ensureVisible(editButton);
    await tester.tap(editButton);
    await tester.pumpAndSettle();

    expect(find.text('Edit Trading Bot'), findsOneWidget);

    final nameField = tester.widget<TextFormField>(
      find.byKey(const Key('edit-bot-name-field')),
    );

    final symbolField = tester.widget<TextFormField>(
      find.byKey(const Key('edit-bot-symbol-field')),
    );

    expect(nameField.controller?.text, 'Screen Editing Bot');

    expect(symbolField.controller?.text, 'BTCUSDT');

    await tester.enterText(
      find.byKey(const Key('edit-bot-name-field')),
      'Updated Screen Bot',
    );

    await tester.enterText(
      find.byKey(const Key('edit-bot-symbol-field')),
      'ethusdt',
    );

    await tester.tap(find.byKey(const Key('save-bot-changes-button')));

    await tester.pumpAndSettle();

    expect(repository.updateCalls, 1);
    expect(repository.lastBotId, 14);

    expect(repository.lastRequest?.name, 'Updated Screen Bot');

    expect(repository.lastRequest?.symbol, 'ethusdt');

    expect(find.text('Edit Trading Bot'), findsNothing);

    expect(find.text('Updated Screen Bot'), findsOneWidget);

    expect(find.textContaining('ETHUSDT'), findsOneWidget);
  });

  testWidgets('does not expose editing for an active bot', (tester) async {
    final repository = _FakeRepository(initialStatus: TradingBotStatus.running);

    await _pumpScreen(tester, repository);

    expect(find.byKey(const Key('bot-14-edit-button')), findsNothing);

    expect(find.byKey(const Key('bot-14-pause-button')), findsOneWidget);

    expect(find.byKey(const Key('bot-14-stop-button')), findsOneWidget);

    expect(repository.updateCalls, 0);
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

  int updateCalls = 0;
  int? lastBotId;

  TradingBotUpdateRequest? lastRequest;

  @override
  Future<List<BackendTradingBot>> listBots({
    TradingBotStatus? status,
    int limit = 50,
    int offset = 0,
  }) async {
    if (status != null && bot.status != status) {
      return const <BackendTradingBot>[];
    }

    return <BackendTradingBot>[bot];
  }

  @override
  Future<BackendTradingBot> getBot(int botId) async {
    return bot;
  }

  @override
  Future<BackendTradingBot> updateBot({
    required int botId,
    required TradingBotUpdateRequest request,
  }) async {
    updateCalls += 1;
    lastBotId = botId;
    lastRequest = request;

    bot = _copyBot(
      bot,
      name: request.name,
      symbol: request.symbol,
      strategyType: request.strategyType,
      timeframe: request.timeframe,
      paperTrading: request.paperTrading,
      dryRun: request.dryRun,
    );

    return bot;
  }

  @override
  Future<BackendTradingBot> createBot(TradingBotCreateRequest request) {
    throw UnsupportedError('Not used');
  }

  @override
  Future<void> deleteBot(int botId) {
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
  final timestamp = DateTime.utc(2026, 8, 4, 8);

  return BackendTradingBot(
    id: 14,
    userId: 4,
    exchangeAccountId: 3,
    name: 'Screen Editing Bot',
    description: 'Bots screen edit test',
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

BackendTradingBot _copyBot(
  BackendTradingBot bot, {
  String? name,
  String? symbol,
  TradingBotStrategyType? strategyType,
  TradingBotTimeframe? timeframe,
  bool? paperTrading,
  bool? dryRun,
}) {
  return BackendTradingBot(
    id: bot.id,
    userId: bot.userId,
    exchangeAccountId: bot.exchangeAccountId,
    name: name?.trim() ?? bot.name,
    description: bot.description,
    strategyType: strategyType ?? bot.strategyType,
    symbol: symbol?.trim().toUpperCase() ?? bot.symbol,
    category: bot.category,
    timeframe: timeframe ?? bot.timeframe,
    status: bot.status,
    paperTrading: paperTrading ?? bot.paperTrading,
    dryRun: dryRun ?? bot.dryRun,
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
    updatedAt: DateTime.utc(2026, 8, 4, 9),
  );
}
