import '../data/backend_trading_bot.dart';

abstract interface class TradingBotRepository {
  Future<List<BackendTradingBot>> listBots({
    TradingBotStatus? status,
    int limit = 50,
    int offset = 0,
  });

  Future<BackendTradingBot> getBot(int botId);

  Future<BackendTradingBot> createBot(TradingBotCreateRequest request);

  Future<BackendTradingBot> updateBot({
    required int botId,
    required TradingBotUpdateRequest request,
  });

  Future<void> deleteBot(int botId);

  Future<TradingBotLifecycleResult> performLifecycle({
    required int botId,
    required TradingBotLifecycleAction action,
  });
}
