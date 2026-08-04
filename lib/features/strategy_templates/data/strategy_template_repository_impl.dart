import '../../bots/data/backend_trading_bot.dart';
import '../domain/strategy_template_repository.dart';
import 'backend_strategy_template.dart';
import 'strategy_template_remote_data_source.dart';

class StrategyTemplateRepositoryImpl implements StrategyTemplateRepository {
  const StrategyTemplateRepositoryImpl(this._remoteDataSource);

  final StrategyTemplateRemoteDataSource _remoteDataSource;

  @override
  Future<List<BackendStrategyTemplate>> listOwned({
    StrategyTemplateStatus? status,
    StrategyTemplateVisibility? visibility,
    int limit = 50,
    int offset = 0,
  }) {
    return _remoteDataSource.listOwned(
      status: status,
      visibility: visibility,
      limit: limit,
      offset: offset,
    );
  }

  @override
  Future<List<BackendStrategyTemplate>> listPublic({
    int limit = 50,
    int offset = 0,
  }) {
    return _remoteDataSource.listPublic(limit: limit, offset: offset);
  }

  @override
  Future<BackendStrategyTemplate> getTemplate(int templateId) {
    return _remoteDataSource.getTemplate(templateId);
  }

  @override
  Future<BackendStrategyTemplate> createTemplate(
    StrategyTemplateCreateRequest request,
  ) {
    return _remoteDataSource.createTemplate(request);
  }

  @override
  Future<BackendStrategyTemplate> updateTemplate({
    required int templateId,
    required StrategyTemplateUpdateRequest request,
  }) {
    return _remoteDataSource.updateTemplate(
      templateId: templateId,
      request: request,
    );
  }

  @override
  Future<void> deleteTemplate(int templateId) {
    return _remoteDataSource.deleteTemplate(templateId);
  }

  @override
  Future<StrategyTemplateActionResult> performAction({
    required int templateId,
    required StrategyTemplateAction action,
  }) {
    return _remoteDataSource.performAction(
      templateId: templateId,
      action: action,
    );
  }

  @override
  Future<BackendTradingBot> createBotFromTemplate({
    required int templateId,
    required StrategyTemplateBotCreateRequest request,
  }) {
    return _remoteDataSource.createBotFromTemplate(
      templateId: templateId,
      request: request,
    );
  }
}
