import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/core/errors/app_exception.dart';
import 'package:p_trader_ai/features/bots/data/backend_trading_bot.dart';
import 'package:p_trader_ai/features/bots/domain/trading_bot_repository.dart';
import 'package:p_trader_ai/features/bots/providers/backend_trading_bot_provider.dart';

void main() {
  group('BackendTradingBotNotifier', () {
    test('loads and sorts authenticated bots', () async {
      final repository = _FakeRepository(
        bots: <BackendTradingBot>[
          _bot(id: 1, status: TradingBotStatus.stopped, hour: 8),
          _bot(id: 2, status: TradingBotStatus.running, hour: 10),
        ],
      );

      final container = _container(repository);
      addTearDown(container.dispose);

      await container.read(backendTradingBotProvider.notifier).loadBots();

      final state = container.read(backendTradingBotProvider);

      expect(repository.listCalls, 1);
      expect(state.hasLoaded, isTrue);
      expect(state.bots.map((bot) => bot.id), <int>[2, 1]);
      expect(state.errorMessage, isNull);
    });

    test('creates and appends a bot', () async {
      final repository = _FakeRepository();
      final container = _container(repository);
      addTearDown(container.dispose);

      final bot = await container
          .read(backendTradingBotProvider.notifier)
          .createBot(
            const TradingBotCreateRequest(
              name: 'Momentum Bot',
              symbol: 'BTCUSDT',
            ),
          );

      expect(bot, isNotNull);
      expect(repository.createCalls, 1);
      expect(container.read(backendTradingBotProvider).bots, hasLength(1));
    });

    test('updates an existing bot', () async {
      final repository = _FakeRepository(
        bots: <BackendTradingBot>[
          _bot(id: 4, status: TradingBotStatus.stopped),
        ],
      );

      final container = _container(repository);
      addTearDown(container.dispose);

      await container.read(backendTradingBotProvider.notifier).loadBots();

      final updated = await container
          .read(backendTradingBotProvider.notifier)
          .updateBot(
            botId: 4,
            request: const TradingBotUpdateRequest(name: 'Updated Bot'),
          );

      expect(updated?.name, 'Updated Bot');
      expect(repository.updateCalls, 1);
      expect(
        container.read(backendTradingBotProvider).bots.single.name,
        'Updated Bot',
      );
    });

    test('deletes an existing bot', () async {
      final repository = _FakeRepository(
        bots: <BackendTradingBot>[
          _bot(id: 5, status: TradingBotStatus.stopped),
        ],
      );

      final container = _container(repository);
      addTearDown(container.dispose);

      await container.read(backendTradingBotProvider.notifier).loadBots();

      final deleted = await container
          .read(backendTradingBotProvider.notifier)
          .deleteBot(5);

      expect(deleted, isTrue);
      expect(repository.deleteCalls, 1);
      expect(container.read(backendTradingBotProvider).bots, isEmpty);
    });

    test('applies lifecycle result to state', () async {
      final repository = _FakeRepository(
        bots: <BackendTradingBot>[
          _bot(id: 6, status: TradingBotStatus.stopped),
        ],
      );

      final container = _container(repository);
      addTearDown(container.dispose);

      await container.read(backendTradingBotProvider.notifier).loadBots();

      final result = await container
          .read(backendTradingBotProvider.notifier)
          .performLifecycle(botId: 6, action: TradingBotLifecycleAction.start);

      expect(result?.status, TradingBotStatus.running);
      expect(repository.lifecycleCalls, 1);
      expect(
        container.read(backendTradingBotProvider).bots.single.status,
        TradingBotStatus.running,
      );
    });

    test('stores repository load errors', () async {
      final repository = _FakeRepository(
        listError: const AppException('Unable to load bots'),
      );

      final container = _container(repository);
      addTearDown(container.dispose);

      await container.read(backendTradingBotProvider.notifier).loadBots();

      expect(
        container.read(backendTradingBotProvider).errorMessage,
        'Unable to load bots',
      );
    });
  });
}

ProviderContainer _container(TradingBotRepository repository) {
  return ProviderContainer(
    overrides: [
      backendTradingBotRepositoryProvider.overrideWithValue(repository),
    ],
  );
}

class _FakeRepository implements TradingBotRepository {
  _FakeRepository({List<BackendTradingBot>? bots, this.listError})
    : bots = bots ?? <BackendTradingBot>[];

  List<BackendTradingBot> bots;
  final AppException? listError;

  int listCalls = 0;
  int createCalls = 0;
  int updateCalls = 0;
  int deleteCalls = 0;
  int lifecycleCalls = 0;

  @override
  Future<List<BackendTradingBot>> listBots({
    TradingBotStatus? status,
    int limit = 50,
    int offset = 0,
  }) async {
    listCalls += 1;

    final error = listError;

    if (error != null) {
      throw error;
    }

    return bots
        .where((bot) => status == null || bot.status == status)
        .toList(growable: false);
  }

  @override
  Future<BackendTradingBot> getBot(int botId) async {
    return bots.firstWhere((bot) => bot.id == botId);
  }

  @override
  Future<BackendTradingBot> createBot(TradingBotCreateRequest request) async {
    createCalls += 1;

    final bot = _bot(
      id: bots.length + 1,
      status: TradingBotStatus.draft,
      name: request.name.trim(),
    );

    bots = <BackendTradingBot>[...bots, bot];

    return bot;
  }

  @override
  Future<BackendTradingBot> updateBot({
    required int botId,
    required TradingBotUpdateRequest request,
  }) async {
    updateCalls += 1;

    final current = await getBot(botId);

    final updated = _copyBot(current, name: request.name ?? current.name);

    bots = bots
        .map((bot) => bot.id == botId ? updated : bot)
        .toList(growable: false);

    return updated;
  }

  @override
  Future<void> deleteBot(int botId) async {
    deleteCalls += 1;

    bots = bots.where((bot) => bot.id != botId).toList(growable: false);
  }

  @override
  Future<TradingBotLifecycleResult> performLifecycle({
    required int botId,
    required TradingBotLifecycleAction action,
  }) async {
    lifecycleCalls += 1;

    final current = await getBot(botId);

    final nextStatus = switch (action) {
      TradingBotLifecycleAction.prepare => TradingBotStatus.stopped,
      TradingBotLifecycleAction.start => TradingBotStatus.running,
      TradingBotLifecycleAction.pause => TradingBotStatus.paused,
      TradingBotLifecycleAction.resume => TradingBotStatus.running,
      TradingBotLifecycleAction.stop => TradingBotStatus.stopped,
    };

    final updated = _copyBot(current, status: nextStatus);

    bots = bots
        .map((bot) => bot.id == botId ? updated : bot)
        .toList(growable: false);

    return TradingBotLifecycleResult(
      action: action,
      previousStatus: current.status,
      status: nextStatus,
      changed: current.status != nextStatus,
      bot: updated,
    );
  }
}

BackendTradingBot _bot({
  required int id,
  required TradingBotStatus status,
  String? name,
  int hour = 9,
}) {
  final timestamp = DateTime.utc(2026, 8, 3, hour);

  return BackendTradingBot(
    id: id,
    userId: 7,
    exchangeAccountId: 3,
    name: name ?? 'Bot $id',
    description: 'Provider test bot',
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
    createdAt: timestamp,
    updatedAt: timestamp,
  );
}

BackendTradingBot _copyBot(
  BackendTradingBot bot, {
  String? name,
  TradingBotStatus? status,
}) {
  return BackendTradingBot(
    id: bot.id,
    userId: bot.userId,
    exchangeAccountId: bot.exchangeAccountId,
    name: name ?? bot.name,
    description: bot.description,
    strategyType: bot.strategyType,
    symbol: bot.symbol,
    category: bot.category,
    timeframe: bot.timeframe,
    status: status ?? bot.status,
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
