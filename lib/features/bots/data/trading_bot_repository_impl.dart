import '../domain/trading_bot_repository.dart';
import 'backend_trading_bot.dart';
import 'trading_bot_remote_data_source.dart';

class TradingBotRepositoryImpl implements TradingBotRepository {
  const TradingBotRepositoryImpl({
    required TradingBotRemoteDataSource remoteDataSource,
  }) : _remoteDataSource = remoteDataSource;

  final TradingBotRemoteDataSource _remoteDataSource;

  @override
  Future<List<BackendTradingBot>> listBots({
    TradingBotStatus? status,
    int limit = 50,
    int offset = 0,
  }) {
    return _remoteDataSource.listBots(
      status: status,
      limit: limit,
      offset: offset,
    );
  }

  @override
  Future<BackendTradingBot> getBot(int botId) {
    return _remoteDataSource.getBot(botId);
  }

  @override
  Future<BackendTradingBot> createBot(TradingBotCreateRequest request) {
    return _remoteDataSource.createBot(request);
  }

  @override
  Future<BackendTradingBot> updateBot({
    required int botId,
    required TradingBotUpdateRequest request,
  }) {
    return _remoteDataSource.updateBot(botId: botId, request: request);
  }

  @override
  Future<void> deleteBot(int botId) {
    return _remoteDataSource.deleteBot(botId);
  }

  @override
  Future<TradingBotLifecycleResult> performLifecycle({
    required int botId,
    required TradingBotLifecycleAction action,
  }) {
    return _remoteDataSource.performLifecycle(botId: botId, action: action);
  }
}
