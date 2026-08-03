import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/features/bots/bots_screen.dart';
import 'package:p_trader_ai/features/bots/data/backend_trading_bot.dart';
import 'package:p_trader_ai/features/bots/domain/trading_bot_repository.dart';
import 'package:p_trader_ai/features/bots/providers/backend_trading_bot_provider.dart';

void main() {
  testWidgets('opens bot creation from app bar and empty state', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(900, 1200);
    tester.view.devicePixelRatio = 1;

    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });

    final repository = _FakeRepository();

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          backendTradingBotRepositoryProvider.overrideWithValue(repository),
        ],
        child: const MaterialApp(home: BotsScreen()),
      ),
    );

    await tester.pumpAndSettle();

    expect(repository.listCalls, 1);
    expect(find.text('No trading bots yet'), findsOneWidget);

    await tester.tap(find.byTooltip('Create trading bot'));
    await tester.pumpAndSettle();

    expect(find.text('Create Trading Bot'), findsOneWidget);

    await tester.tap(find.text('Cancel'));
    await tester.pumpAndSettle();

    expect(find.text('Create Trading Bot'), findsNothing);

    await tester.tap(find.byKey(const Key('create-first-bot-button')));
    await tester.pumpAndSettle();

    expect(find.text('Create Trading Bot'), findsOneWidget);
  });
}

class _FakeRepository implements TradingBotRepository {
  int listCalls = 0;

  @override
  Future<List<BackendTradingBot>> listBots({
    TradingBotStatus? status,
    int limit = 50,
    int offset = 0,
  }) async {
    listCalls += 1;
    return const <BackendTradingBot>[];
  }

  @override
  Future<BackendTradingBot> getBot(int botId) {
    throw UnsupportedError('Not used');
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

  @override
  Future<TradingBotLifecycleResult> performLifecycle({
    required int botId,
    required TradingBotLifecycleAction action,
  }) {
    throw UnsupportedError('Not used');
  }
}
