import '../../bots/data/backend_trading_bot.dart';
import '../data/backend_strategy_template.dart';

abstract interface class StrategyTemplateRepository {
  Future<List<BackendStrategyTemplate>> listOwned({
    StrategyTemplateStatus? status,
    StrategyTemplateVisibility? visibility,
    int limit = 50,
    int offset = 0,
  });

  Future<List<BackendStrategyTemplate>> listPublic({
    int limit = 50,
    int offset = 0,
  });

  Future<BackendStrategyTemplate> getTemplate(int templateId);

  Future<BackendStrategyTemplate> createTemplate(
    StrategyTemplateCreateRequest request,
  );

  Future<BackendStrategyTemplate> updateTemplate({
    required int templateId,
    required StrategyTemplateUpdateRequest request,
  });

  Future<void> deleteTemplate(int templateId);

  Future<StrategyTemplateActionResult> performAction({
    required int templateId,
    required StrategyTemplateAction action,
  });

  Future<BackendTradingBot> createBotFromTemplate({
    required int templateId,
    required StrategyTemplateBotCreateRequest request,
  });
}
