import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/features/bots/data/backend_trading_bot.dart';
import 'package:p_trader_ai/features/bots/domain/trading_bot_repository.dart';
import 'package:p_trader_ai/features/bots/providers/backend_trading_bot_provider.dart';
import 'package:p_trader_ai/features/bots/widgets/add_trading_bot_dialog.dart';

void main() {
  testWidgets('creates a safe backend trading bot', (tester) async {
    final repository = _FakeRepository();

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          backendTradingBotRepositoryProvider.overrideWithValue(repository),
        ],
        child: MaterialApp(
          home: Builder(
            builder: (context) {
              return Scaffold(
                body: Center(
                  child: FilledButton(
                    key: const Key('open-dialog-button'),
                    onPressed: () {
                      showDialog<BackendTradingBot>(
                        context: context,
                        builder: (_) => const AddTradingBotDialog(),
                      );
                    },
                    child: const Text('Open'),
                  ),
                ),
              );
            },
          ),
        ),
      ),
    );

    await tester.tap(find.byKey(const Key('open-dialog-button')));
    await tester.pumpAndSettle();

    expect(find.text('Create Trading Bot'), findsOneWidget);

    await tester.enterText(
      find.byKey(const Key('bot-name-field')),
      'Momentum Test Bot',
    );

    await tester.enterText(
      find.byKey(const Key('bot-symbol-field')),
      'ethusdt',
    );

    await tester.tap(find.byKey(const Key('create-bot-button')));
    await tester.pumpAndSettle();

    expect(repository.createCalls, 1);
    expect(repository.lastRequest?.name, 'Momentum Test Bot');
    expect(repository.lastRequest?.symbol, 'ethusdt');
    expect(repository.lastRequest?.paperTrading, isTrue);
    expect(repository.lastRequest?.dryRun, isTrue);
    expect(find.text('Create Trading Bot'), findsNothing);
  });
}

class _FakeRepository implements TradingBotRepository {
  int createCalls = 0;
  TradingBotCreateRequest? lastRequest;

  @override
  Future<List<BackendTradingBot>> listBots({
    TradingBotStatus? status,
    int limit = 50,
    int offset = 0,
  }) async {
    return const <BackendTradingBot>[];
  }

  @override
  Future<BackendTradingBot> getBot(int botId) {
    throw UnsupportedError('Not used');
  }

  @override
  Future<BackendTradingBot> createBot(TradingBotCreateRequest request) async {
    createCalls += 1;
    lastRequest = request;

    final timestamp = DateTime.utc(2026, 8, 3, 12);

    return BackendTradingBot(
      id: 1,
      userId: 7,
      exchangeAccountId: null,
      name: request.name.trim(),
      description: null,
      strategyType: request.strategyType,
      symbol: request.symbol.trim().toUpperCase(),
      category: TradingBotCategory.linear,
      timeframe: TradingBotTimeframe.fiveMinutes,
      status: TradingBotStatus.draft,
      paperTrading: request.paperTrading,
      dryRun: request.dryRun,
      riskPerTradePercent: 1,
      maxPositionValueUsd: 25,
      maxDailyLossPercent: 3,
      maxDrawdownPercent: 10,
      stopLossPercent: null,
      takeProfitPercent: null,
      strategyConfig: const <String, dynamic>{},
      lastError: null,
      startedAt: null,
      stoppedAt: null,
      lastRunAt: null,
      createdAt: timestamp,
      updatedAt: timestamp,
    );
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

  @override
  Future<TradingBotLifecycleResult> performLifecycle({
    required int botId,
    required TradingBotLifecycleAction action,
  }) {
    throw UnsupportedError('Not used');
  }
}
