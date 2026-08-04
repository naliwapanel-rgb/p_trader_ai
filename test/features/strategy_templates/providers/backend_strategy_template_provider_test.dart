import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/core/errors/app_exception.dart';
import 'package:p_trader_ai/features/bots/data/backend_trading_bot.dart';
import 'package:p_trader_ai/features/strategy_templates/data/backend_strategy_template.dart';
import 'package:p_trader_ai/features/strategy_templates/domain/strategy_template_repository.dart';
import 'package:p_trader_ai/features/strategy_templates/providers/backend_strategy_template_provider.dart';

void main() {
  group('BackendStrategyTemplateNotifier', () {
    test('loads and sorts owned and public templates', () async {
      final repository = _FakeRepository(
        ownedTemplates: <BackendStrategyTemplate>[
          _template(id: 1, hour: 8, status: StrategyTemplateStatus.draft),
          _template(
            id: 2,
            hour: 10,
            status: StrategyTemplateStatus.published,
            visibility: StrategyTemplateVisibility.publicTemplate,
          ),
        ],
      );

      final container = _container(repository);
      addTearDown(container.dispose);

      await container
          .read(backendStrategyTemplateProvider.notifier)
          .loadOwned();

      await container
          .read(backendStrategyTemplateProvider.notifier)
          .loadPublic();

      final state = container.read(backendStrategyTemplateProvider);

      expect(repository.listOwnedCalls, 1);
      expect(repository.listPublicCalls, 1);
      expect(state.ownedTemplates.map((template) => template.id), <int>[2, 1]);

      expect(state.publicTemplates.map((template) => template.id), <int>[2]);

      expect(state.hasLoadedOwned, isTrue);
      expect(state.hasLoadedPublic, isTrue);
    });

    test('creates and appends a template', () async {
      final repository = _FakeRepository();
      final container = _container(repository);
      addTearDown(container.dispose);

      final template = await container
          .read(backendStrategyTemplateProvider.notifier)
          .createTemplate(
            const StrategyTemplateCreateRequest(
              name: 'Momentum Template',
              symbol: 'BTCUSDT',
            ),
          );

      expect(template, isNotNull);
      expect(repository.createCalls, 1);

      final state = container.read(backendStrategyTemplateProvider);

      expect(state.ownedTemplates, hasLength(1));
      expect(state.ownedTemplates.single.name, 'Momentum Template');
    });

    test('updates and publishes an owned template', () async {
      final repository = _FakeRepository(
        ownedTemplates: <BackendStrategyTemplate>[
          _template(id: 4, status: StrategyTemplateStatus.draft),
        ],
      );

      final container = _container(repository);
      addTearDown(container.dispose);

      final notifier = container.read(backendStrategyTemplateProvider.notifier);

      await notifier.loadOwned();
      await notifier.loadPublic();

      final updated = await notifier.updateTemplate(
        templateId: 4,
        request: const StrategyTemplateUpdateRequest(name: 'Updated Template'),
      );

      expect(updated?.name, 'Updated Template');
      expect(repository.updateCalls, 1);

      final result = await notifier.performAction(
        templateId: 4,
        action: StrategyTemplateAction.publish,
      );

      expect(result?.status, StrategyTemplateStatus.published);

      expect(repository.actionCalls, 1);

      final state = container.read(backendStrategyTemplateProvider);

      expect(state.ownedTemplates.single.name, 'Updated Template');

      expect(
        state.ownedTemplates.single.status,
        StrategyTemplateStatus.published,
      );

      expect(state.publicTemplates, hasLength(1));

      expect(
        state.publicTemplates.single.visibility,
        StrategyTemplateVisibility.publicTemplate,
      );
    });

    test('deletes an existing template', () async {
      final repository = _FakeRepository(
        ownedTemplates: <BackendStrategyTemplate>[
          _template(
            id: 5,
            status: StrategyTemplateStatus.published,
            visibility: StrategyTemplateVisibility.publicTemplate,
          ),
        ],
      );

      final container = _container(repository);
      addTearDown(container.dispose);

      final notifier = container.read(backendStrategyTemplateProvider.notifier);

      await notifier.loadOwned();
      await notifier.loadPublic();

      final deleted = await notifier.deleteTemplate(5);

      expect(deleted, isTrue);
      expect(repository.deleteCalls, 1);

      final state = container.read(backendStrategyTemplateProvider);

      expect(state.ownedTemplates, isEmpty);
      expect(state.publicTemplates, isEmpty);
    });

    test('creates a safe bot from a template', () async {
      final repository = _FakeRepository(
        ownedTemplates: <BackendStrategyTemplate>[
          _template(
            id: 6,
            status: StrategyTemplateStatus.published,
            visibility: StrategyTemplateVisibility.publicTemplate,
          ),
        ],
      );

      final container = _container(repository);
      addTearDown(container.dispose);

      final bot = await container
          .read(backendStrategyTemplateProvider.notifier)
          .createBotFromTemplate(
            templateId: 6,
            request: const StrategyTemplateBotCreateRequest(name: 'Copied Bot'),
          );

      expect(bot?.name, 'Copied Bot');
      expect(bot?.paperTrading, isTrue);
      expect(bot?.dryRun, isTrue);
      expect(repository.createBotCalls, 1);
    });

    test('stores repository load errors', () async {
      final repository = _FakeRepository(
        listError: const AppException('Unable to load templates'),
      );

      final container = _container(repository);
      addTearDown(container.dispose);

      await container
          .read(backendStrategyTemplateProvider.notifier)
          .loadOwned();

      expect(
        container.read(backendStrategyTemplateProvider).errorMessage,
        'Unable to load templates',
      );
    });
  });
}

ProviderContainer _container(StrategyTemplateRepository repository) {
  return ProviderContainer(
    overrides: [
      backendStrategyTemplateRepositoryProvider.overrideWithValue(repository),
    ],
  );
}

class _FakeRepository implements StrategyTemplateRepository {
  _FakeRepository({
    List<BackendStrategyTemplate>? ownedTemplates,
    this.listError,
  }) : ownedTemplates = ownedTemplates ?? <BackendStrategyTemplate>[];

  List<BackendStrategyTemplate> ownedTemplates;

  final AppException? listError;

  int listOwnedCalls = 0;
  int listPublicCalls = 0;
  int createCalls = 0;
  int updateCalls = 0;
  int deleteCalls = 0;
  int actionCalls = 0;
  int createBotCalls = 0;

  @override
  Future<List<BackendStrategyTemplate>> listOwned({
    StrategyTemplateStatus? status,
    StrategyTemplateVisibility? visibility,
    int limit = 50,
    int offset = 0,
  }) async {
    listOwnedCalls += 1;

    final error = listError;

    if (error != null) {
      throw error;
    }

    return ownedTemplates
        .where(
          (template) =>
              (status == null || template.status == status) &&
              (visibility == null || template.visibility == visibility),
        )
        .toList(growable: false);
  }

  @override
  Future<List<BackendStrategyTemplate>> listPublic({
    int limit = 50,
    int offset = 0,
  }) async {
    listPublicCalls += 1;

    return ownedTemplates
        .where(
          (template) =>
              template.status == StrategyTemplateStatus.published &&
              template.visibility == StrategyTemplateVisibility.publicTemplate,
        )
        .toList(growable: false);
  }

  @override
  Future<BackendStrategyTemplate> getTemplate(int templateId) async {
    return ownedTemplates.firstWhere((template) => template.id == templateId);
  }

  @override
  Future<BackendStrategyTemplate> createTemplate(
    StrategyTemplateCreateRequest request,
  ) async {
    createCalls += 1;

    final nextId = ownedTemplates.isEmpty
        ? 1
        : ownedTemplates
                  .map((template) => template.id)
                  .reduce((first, second) => first > second ? first : second) +
              1;

    final template = _template(
      id: nextId,
      name: request.name.trim(),
      status: StrategyTemplateStatus.draft,
      visibility: request.visibility,
    );

    ownedTemplates = <BackendStrategyTemplate>[...ownedTemplates, template];

    return template;
  }

  @override
  Future<BackendStrategyTemplate> updateTemplate({
    required int templateId,
    required StrategyTemplateUpdateRequest request,
  }) async {
    updateCalls += 1;

    final current = await getTemplate(templateId);

    final updated = _copyTemplate(
      current,
      name: request.name,
      visibility: request.visibility,
    );

    ownedTemplates = ownedTemplates
        .map((template) => template.id == templateId ? updated : template)
        .toList(growable: false);

    return updated;
  }

  @override
  Future<void> deleteTemplate(int templateId) async {
    deleteCalls += 1;

    ownedTemplates = ownedTemplates
        .where((template) => template.id != templateId)
        .toList(growable: false);
  }

  @override
  Future<StrategyTemplateActionResult> performAction({
    required int templateId,
    required StrategyTemplateAction action,
  }) async {
    actionCalls += 1;

    final current = await getTemplate(templateId);

    final nextStatus = switch (action) {
      StrategyTemplateAction.publish => StrategyTemplateStatus.published,
      StrategyTemplateAction.unpublish => StrategyTemplateStatus.draft,
      StrategyTemplateAction.archive => StrategyTemplateStatus.archived,
      StrategyTemplateAction.restore => StrategyTemplateStatus.draft,
    };

    final nextVisibility = switch (action) {
      StrategyTemplateAction.publish =>
        StrategyTemplateVisibility.publicTemplate,
      StrategyTemplateAction.unpublish || StrategyTemplateAction.restore =>
        StrategyTemplateVisibility.privateTemplate,
      StrategyTemplateAction.archive => current.visibility,
    };

    final updated = _copyTemplate(
      current,
      status: nextStatus,
      visibility: nextVisibility,
    );

    ownedTemplates = ownedTemplates
        .map((template) => template.id == templateId ? updated : template)
        .toList(growable: false);

    return StrategyTemplateActionResult(
      action: action,
      previousStatus: current.status,
      status: nextStatus,
      changed: current.status != nextStatus,
      template: updated,
    );
  }

  @override
  Future<BackendTradingBot> createBotFromTemplate({
    required int templateId,
    required StrategyTemplateBotCreateRequest request,
  }) async {
    createBotCalls += 1;

    final template = await getTemplate(templateId);

    return _bot(id: 20, name: request.name.trim(), template: template);
  }
}

BackendStrategyTemplate _template({
  required int id,
  required StrategyTemplateStatus status,
  StrategyTemplateVisibility visibility =
      StrategyTemplateVisibility.privateTemplate,
  String? name,
  int hour = 9,
}) {
  final timestamp = DateTime.utc(2026, 8, 4, hour);

  return BackendStrategyTemplate(
    id: id,
    userId: 7,
    name: name ?? 'Template $id',
    description: 'Provider test template',
    strategyType: TradingBotStrategyType.momentum,
    symbol: 'BTCUSDT',
    category: TradingBotCategory.linear,
    timeframe: TradingBotTimeframe.fiveMinutes,
    visibility: visibility,
    paperTrading: true,
    dryRun: true,
    riskPerTradePercent: 1,
    maxPositionValueUsd: 25,
    maxDailyLossPercent: 3,
    maxDrawdownPercent: 10,
    stopLossPercent: 2,
    takeProfitPercent: 4,
    strategyConfig: const <String, dynamic>{'period': 14},
    status: status,
    version: 1,
    publishedAt: null,
    archivedAt: null,
    createdAt: timestamp,
    updatedAt: timestamp,
  );
}

BackendStrategyTemplate _copyTemplate(
  BackendStrategyTemplate template, {
  String? name,
  StrategyTemplateStatus? status,
  StrategyTemplateVisibility? visibility,
}) {
  return BackendStrategyTemplate(
    id: template.id,
    userId: template.userId,
    name: name ?? template.name,
    description: template.description,
    strategyType: template.strategyType,
    symbol: template.symbol,
    category: template.category,
    timeframe: template.timeframe,
    visibility: visibility ?? template.visibility,
    paperTrading: template.paperTrading,
    dryRun: template.dryRun,
    riskPerTradePercent: template.riskPerTradePercent,
    maxPositionValueUsd: template.maxPositionValueUsd,
    maxDailyLossPercent: template.maxDailyLossPercent,
    maxDrawdownPercent: template.maxDrawdownPercent,
    stopLossPercent: template.stopLossPercent,
    takeProfitPercent: template.takeProfitPercent,
    strategyConfig: template.strategyConfig,
    status: status ?? template.status,
    version: template.version + 1,
    publishedAt: template.publishedAt,
    archivedAt: template.archivedAt,
    createdAt: template.createdAt,
    updatedAt: DateTime.utc(2026, 8, 4, 12),
  );
}

BackendTradingBot _bot({
  required int id,
  required String name,
  required BackendStrategyTemplate template,
}) {
  final timestamp = DateTime.utc(2026, 8, 4, 12);

  return BackendTradingBot(
    id: id,
    userId: 7,
    exchangeAccountId: null,
    name: name,
    description: 'Created from template',
    strategyType: template.strategyType,
    symbol: template.symbol,
    category: template.category,
    timeframe: template.timeframe,
    status: TradingBotStatus.draft,
    paperTrading: true,
    dryRun: true,
    riskPerTradePercent: template.riskPerTradePercent,
    maxPositionValueUsd: template.maxPositionValueUsd,
    maxDailyLossPercent: template.maxDailyLossPercent,
    maxDrawdownPercent: template.maxDrawdownPercent,
    stopLossPercent: template.stopLossPercent,
    takeProfitPercent: template.takeProfitPercent,
    strategyConfig: template.strategyConfig,
    lastError: null,
    startedAt: null,
    stoppedAt: null,
    lastRunAt: null,
    createdAt: timestamp,
    updatedAt: timestamp,
  );
}
