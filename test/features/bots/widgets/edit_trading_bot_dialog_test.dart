import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/features/bots/data/backend_trading_bot.dart';
import 'package:p_trader_ai/features/bots/domain/trading_bot_repository.dart';
import 'package:p_trader_ai/features/bots/providers/backend_trading_bot_provider.dart';
import 'package:p_trader_ai/features/bots/widgets/edit_trading_bot_dialog.dart';

void main() {
  testWidgets('updates an inactive bot with safe values', (tester) async {
    final repository = _FakeRepository(
      bot: _bot(status: TradingBotStatus.stopped),
    );

    await _pumpLauncher(tester, repository);

    await tester.tap(find.byKey(const Key('open-edit-dialog-button')));
    await tester.pumpAndSettle();

    expect(find.text('Edit Trading Bot'), findsOneWidget);

    final nameField = tester.widget<TextFormField>(
      find.byKey(const Key('edit-bot-name-field')),
    );

    final symbolField = tester.widget<TextFormField>(
      find.byKey(const Key('edit-bot-symbol-field')),
    );

    expect(nameField.controller?.text, 'Editable Bot');

    expect(symbolField.controller?.text, 'BTCUSDT');

    await tester.enterText(
      find.byKey(const Key('edit-bot-name-field')),
      'Updated Safe Bot',
    );

    await tester.enterText(
      find.byKey(const Key('edit-bot-symbol-field')),
      'ethusdt',
    );

    await tester.tap(find.byKey(const Key('edit-paper-trading-switch')));

    await tester.tap(find.byKey(const Key('save-bot-changes-button')));

    await tester.pumpAndSettle();

    expect(repository.updateCalls, 1);

    expect(repository.lastRequest?.name, 'Updated Safe Bot');

    expect(repository.lastRequest?.symbol, 'ethusdt');

    expect(repository.lastRequest?.paperTrading, isFalse);

    expect(repository.lastRequest?.dryRun, isTrue);

    expect(repository.bot.symbol, 'ETHUSDT');

    expect(find.text('Saved: Updated Safe Bot'), findsOneWidget);

    expect(find.text('Edit Trading Bot'), findsNothing);
  });

  testWidgets('blocks editing for an active bot', (tester) async {
    final repository = _FakeRepository(
      bot: _bot(status: TradingBotStatus.running),
    );

    await _pumpLauncher(tester, repository);

    await tester.tap(find.byKey(const Key('open-edit-dialog-button')));

    await tester.pumpAndSettle();

    expect(find.byKey(const Key('active-bot-edit-warning')), findsOneWidget);

    expect(
      find.text(
        'Active trading bots cannot '
        'be edited. Stop the bot '
        'before editing.',
      ),
      findsOneWidget,
    );

    final saveButton = tester.widget<FilledButton>(
      find.byKey(const Key('save-bot-changes-button')),
    );

    expect(saveButton.onPressed, isNull);
    expect(repository.updateCalls, 0);
  });
}

Future<void> _pumpLauncher(
  WidgetTester tester,
  _FakeRepository repository,
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
      child: MaterialApp(home: _DialogLauncher(bot: repository.bot)),
    ),
  );

  await tester.pumpAndSettle();
}

class _DialogLauncher extends StatefulWidget {
  const _DialogLauncher({required this.bot});

  final BackendTradingBot bot;

  @override
  State<_DialogLauncher> createState() => _DialogLauncherState();
}

class _DialogLauncherState extends State<_DialogLauncher> {
  String? _savedName;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            FilledButton(
              key: const Key('open-edit-dialog-button'),
              onPressed: () async {
                final result = await showDialog<BackendTradingBot>(
                  context: context,
                  builder: (_) => EditTradingBotDialog(bot: widget.bot),
                );

                if (result != null && mounted) {
                  setState(() {
                    _savedName = result.name;
                  });
                }
              },
              child: const Text('Open Editor'),
            ),
            if (_savedName != null) Text('Saved: $_savedName'),
          ],
        ),
      ),
    );
  }
}

class _FakeRepository implements TradingBotRepository {
  _FakeRepository({required this.bot});

  BackendTradingBot bot;
  int updateCalls = 0;

  TradingBotUpdateRequest? lastRequest;

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
  Future<BackendTradingBot> updateBot({
    required int botId,
    required TradingBotUpdateRequest request,
  }) async {
    updateCalls += 1;
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

BackendTradingBot _bot({required TradingBotStatus status}) {
  final timestamp = DateTime.utc(2026, 8, 3, 12);

  return BackendTradingBot(
    id: 12,
    userId: 4,
    exchangeAccountId: 3,
    name: 'Editable Bot',
    description: 'Edit dialog test',
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
    updatedAt: bot.updatedAt,
  );
}
