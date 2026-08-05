import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/core/errors/app_exception.dart';
import 'package:p_trader_ai/features/bots/data/backend_trading_bot.dart';
import 'package:p_trader_ai/features/strategy_templates/data/backend_strategy_template.dart';
import 'package:p_trader_ai/features/strategy_templates/domain/strategy_template_repository.dart';
import 'package:p_trader_ai/features/strategy_templates/providers/backend_strategy_template_provider.dart';
import 'package:p_trader_ai/features/strategy_templates/strategy_templates_screen.dart';

void main() {
  group('StrategyTemplatesScreen', () {
    testWidgets('shows owned templates and filters by status', (tester) async {
      final repository = _ReadOnlyRepository(
        ownedTemplates: <BackendStrategyTemplate>[
          _template(
            id: 1,
            name: 'Draft Momentum',
            status: StrategyTemplateStatus.draft,
          ),
          _template(
            id: 2,
            name: 'Published Trend',
            status: StrategyTemplateStatus.published,
            visibility: StrategyTemplateVisibility.publicTemplate,
          ),
        ],
      );

      await _pumpScreen(tester, repository);

      expect(find.text('Draft Momentum'), findsOneWidget);

      expect(find.text('Published Trend'), findsOneWidget);

      await tester.tap(find.byKey(const Key('owned-filter-draft')));

      await tester.pumpAndSettle();

      expect(find.text('Draft Momentum'), findsOneWidget);

      expect(find.text('Published Trend'), findsNothing);
    });

    testWidgets('shows published public templates', (tester) async {
      final repository = _ReadOnlyRepository(
        ownedTemplates: <BackendStrategyTemplate>[
          _template(
            id: 3,
            name: 'Community Trend',
            status: StrategyTemplateStatus.published,
            visibility: StrategyTemplateVisibility.publicTemplate,
          ),
        ],
      );

      await _pumpScreen(tester, repository);

      await tester.tap(find.byKey(const Key('public-templates-tab')));

      await tester.pumpAndSettle();

      expect(find.text('Community Trend'), findsOneWidget);

      expect(find.text('Visibility: Public'), findsOneWidget);

      expect(repository.listPublicCalls, 1);
    });

    testWidgets('creates a template through the creation dialog', (
      tester,
    ) async {
      final repository = _ReadOnlyRepository();

      await _pumpScreen(tester, repository);

      await tester.tap(
        find.byKey(const Key('create-strategy-template-screen-button')),
      );

      await tester.pumpAndSettle();

      expect(find.text('Create Strategy Template'), findsOneWidget);

      await tester.enterText(
        find.byKey(const Key('template-name-field')),
        'Wired Momentum Template',
      );

      await tester.enterText(
        find.byKey(const Key('template-symbol-field')),
        'ethusdt',
      );

      await tester.ensureVisible(
        find.byKey(const Key('create-strategy-template-button')),
      );

      await tester.tap(
        find.byKey(const Key('create-strategy-template-button')),
      );

      await tester.pumpAndSettle();

      expect(repository.createCalls, 1);
      expect(repository.lastCreateRequest?.name, 'Wired Momentum Template');
      expect(repository.lastCreateRequest?.symbol, 'ETHUSDT');
      expect(repository.lastCreateRequest?.paperTrading, isTrue);
      expect(repository.lastCreateRequest?.dryRun, isTrue);

      expect(find.text('Wired Momentum Template'), findsOneWidget);

      expect(
        find.text('Strategy template created successfully.'),
        findsOneWidget,
      );

      expect(find.text('Create Strategy Template'), findsNothing);
    });

    testWidgets('shows backend errors when template creation fails', (
      tester,
    ) async {
      final repository = _ReadOnlyRepository(
        createError: const AppException('Template creation was rejected'),
      );

      await _pumpScreen(tester, repository);

      await tester.tap(
        find.byKey(const Key('create-strategy-template-screen-button')),
      );

      await tester.pumpAndSettle();

      await tester.enterText(
        find.byKey(const Key('template-name-field')),
        'Rejected Template',
      );

      await tester.enterText(
        find.byKey(const Key('template-symbol-field')),
        'BTCUSDT',
      );

      await tester.ensureVisible(
        find.byKey(const Key('create-strategy-template-button')),
      );

      await tester.tap(
        find.byKey(const Key('create-strategy-template-button')),
      );

      await tester.pumpAndSettle();

      expect(repository.createCalls, 1);

      expect(find.text('Template creation was rejected'), findsOneWidget);

      expect(find.text('Rejected Template'), findsNothing);
    });

    testWidgets('edits an owned strategy template', (tester) async {
      final repository = _ReadOnlyRepository(
        ownedTemplates: <BackendStrategyTemplate>[
          _template(
            id: 4,
            name: 'Editable Draft',
            status: StrategyTemplateStatus.draft,
          ),
        ],
      );

      await _pumpScreen(tester, repository);

      await tester.tap(find.byKey(const Key('template-4-details-button')));
      await tester.pumpAndSettle();

      await tester.tap(find.byKey(const Key('template-4-edit-button')));
      await tester.pumpAndSettle();

      expect(find.text('Edit Strategy Template'), findsOneWidget);

      await tester.enterText(
        find.byKey(const Key('edit-template-name-field')),
        'Edited Draft',
      );

      await tester.ensureVisible(
        find.byKey(const Key('save-template-changes-button')),
      );
      await tester.tap(find.byKey(const Key('save-template-changes-button')));
      await tester.pumpAndSettle();

      expect(repository.updateCalls, 1);
      expect(repository.lastUpdateTemplateId, 4);
      expect(repository.lastUpdateRequest?.name, 'Edited Draft');
      expect(find.text('Edited Draft'), findsOneWidget);
      expect(
        find.text('Strategy template updated successfully.'),
        findsOneWidget,
      );
      expect(find.text('Edit Strategy Template'), findsNothing);
    });

    testWidgets('does not offer editing for public templates', (tester) async {
      final repository = _ReadOnlyRepository(
        ownedTemplates: <BackendStrategyTemplate>[
          _template(
            id: 5,
            name: 'Public Read Only',
            status: StrategyTemplateStatus.published,
            visibility: StrategyTemplateVisibility.publicTemplate,
          ),
        ],
      );

      await _pumpScreen(tester, repository);

      await tester.tap(find.byKey(const Key('public-templates-tab')));
      await tester.pumpAndSettle();

      await tester.tap(find.byKey(const Key('template-5-details-button')));
      await tester.pumpAndSettle();

      expect(find.text('Public Read Only'), findsWidgets);
      expect(find.byKey(const Key('template-5-edit-button')), findsNothing);
      expect(find.byKey(const Key('template-5-delete-button')), findsNothing);
    });

    testWidgets('shows backend errors when template editing fails', (
      tester,
    ) async {
      final repository = _ReadOnlyRepository(
        ownedTemplates: <BackendStrategyTemplate>[
          _template(
            id: 6,
            name: 'Original Draft',
            status: StrategyTemplateStatus.draft,
          ),
        ],
        updateError: const AppException('Template update was rejected'),
      );

      await _pumpScreen(tester, repository);

      await tester.tap(find.byKey(const Key('template-6-details-button')));
      await tester.pumpAndSettle();

      await tester.tap(find.byKey(const Key('template-6-edit-button')));
      await tester.pumpAndSettle();

      await tester.enterText(
        find.byKey(const Key('edit-template-name-field')),
        'Rejected Edit',
      );

      await tester.ensureVisible(
        find.byKey(const Key('save-template-changes-button')),
      );
      await tester.tap(find.byKey(const Key('save-template-changes-button')));
      await tester.pumpAndSettle();

      expect(repository.updateCalls, 1);
      expect(repository.lastUpdateTemplateId, 6);
      expect(repository.lastUpdateRequest?.name, 'Rejected Edit');
      expect(find.text('Template update was rejected'), findsOneWidget);
      expect(find.text('Original Draft'), findsOneWidget);
      expect(find.text('Rejected Edit'), findsNothing);
    });

    testWidgets('deletes an owned strategy template after confirmation', (
      tester,
    ) async {
      final repository = _ReadOnlyRepository(
        ownedTemplates: <BackendStrategyTemplate>[
          _template(
            id: 7,
            name: 'Delete Me',
            status: StrategyTemplateStatus.draft,
          ),
        ],
      );

      await _pumpScreen(tester, repository);

      await tester.tap(find.byKey(const Key('template-7-details-button')));
      await tester.pumpAndSettle();

      await tester.tap(find.byKey(const Key('template-7-delete-button')));
      await tester.pumpAndSettle();

      expect(find.text('Delete Strategy Template?'), findsOneWidget);
      expect(repository.deleteCalls, 0);

      await tester.tap(find.byKey(const Key('confirm-delete-template-button')));
      await tester.pumpAndSettle();

      expect(repository.deleteCalls, 1);
      expect(repository.lastDeleteTemplateId, 7);
      expect(find.text('Delete Me'), findsNothing);
      expect(
        find.text('Strategy template deleted successfully.'),
        findsOneWidget,
      );
    });

    testWidgets('shows backend errors when template deletion fails', (
      tester,
    ) async {
      final repository = _ReadOnlyRepository(
        ownedTemplates: <BackendStrategyTemplate>[
          _template(
            id: 8,
            name: 'Protected Draft',
            status: StrategyTemplateStatus.draft,
          ),
        ],
        deleteError: const AppException('Template deletion was rejected'),
      );

      await _pumpScreen(tester, repository);

      await tester.tap(find.byKey(const Key('template-8-details-button')));
      await tester.pumpAndSettle();

      await tester.tap(find.byKey(const Key('template-8-delete-button')));
      await tester.pumpAndSettle();

      await tester.tap(find.byKey(const Key('confirm-delete-template-button')));
      await tester.pumpAndSettle();

      expect(repository.deleteCalls, 1);
      expect(repository.lastDeleteTemplateId, 8);
      expect(find.text('Template deletion was rejected'), findsOneWidget);
      expect(find.text('Protected Draft'), findsOneWidget);
    });

    testWidgets('shows repository load errors', (tester) async {
      final repository = _ReadOnlyRepository(
        listOwnedError: const AppException(
          'Templates are temporarily unavailable',
        ),
      );

      await _pumpScreen(tester, repository);

      expect(
        find.text('Templates are temporarily unavailable'),
        findsOneWidget,
      );
    });
  });
}

Future<void> _pumpScreen(
  WidgetTester tester,
  StrategyTemplateRepository repository,
) async {
  tester.view.physicalSize = const Size(1200, 1600);
  tester.view.devicePixelRatio = 1;

  addTearDown(() {
    tester.view.resetPhysicalSize();
    tester.view.resetDevicePixelRatio();
  });

  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        backendStrategyTemplateRepositoryProvider.overrideWithValue(repository),
      ],
      child: const MaterialApp(home: StrategyTemplatesScreen()),
    ),
  );

  await tester.pumpAndSettle();
}

class _ReadOnlyRepository implements StrategyTemplateRepository {
  _ReadOnlyRepository({
    List<BackendStrategyTemplate>? ownedTemplates,
    this.listOwnedError,
    this.createError,
    this.updateError,
    this.deleteError,
  }) : ownedTemplates = ownedTemplates ?? <BackendStrategyTemplate>[];

  final List<BackendStrategyTemplate> ownedTemplates;

  final AppException? listOwnedError;
  final AppException? createError;
  final AppException? updateError;
  final AppException? deleteError;

  int listOwnedCalls = 0;
  int listPublicCalls = 0;
  int createCalls = 0;
  int updateCalls = 0;
  int deleteCalls = 0;

  StrategyTemplateCreateRequest? lastCreateRequest;
  StrategyTemplateUpdateRequest? lastUpdateRequest;
  int? lastUpdateTemplateId;
  int? lastDeleteTemplateId;

  @override
  Future<List<BackendStrategyTemplate>> listOwned({
    StrategyTemplateStatus? status,
    StrategyTemplateVisibility? visibility,
    int limit = 50,
    int offset = 0,
  }) async {
    listOwnedCalls += 1;

    final error = listOwnedError;

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
  Future<BackendStrategyTemplate> getTemplate(int templateId) {
    throw UnimplementedError();
  }

  @override
  Future<BackendStrategyTemplate> createTemplate(
    StrategyTemplateCreateRequest request,
  ) async {
    createCalls += 1;
    lastCreateRequest = request;

    final error = createError;

    if (error != null) {
      throw error;
    }

    return _template(
      id: 100 + createCalls,
      name: request.name.trim(),
      status: StrategyTemplateStatus.draft,
      visibility: request.visibility,
    );
  }

  @override
  Future<BackendStrategyTemplate> updateTemplate({
    required int templateId,
    required StrategyTemplateUpdateRequest request,
  }) async {
    updateCalls += 1;
    lastUpdateTemplateId = templateId;
    lastUpdateRequest = request;

    final error = updateError;
    if (error != null) {
      throw error;
    }

    final index = ownedTemplates.indexWhere(
      (template) => template.id == templateId,
    );

    if (index < 0) {
      throw StateError('Strategy template not found');
    }

    final existing = ownedTemplates[index];
    final updated = _template(
      id: existing.id,
      name: request.name?.trim() ?? existing.name,
      status: existing.status,
      visibility: request.visibility ?? existing.visibility,
    );

    ownedTemplates[index] = updated;
    return updated;
  }

  @override
  Future<void> deleteTemplate(int templateId) async {
    deleteCalls += 1;
    lastDeleteTemplateId = templateId;

    final error = deleteError;
    if (error != null) {
      throw error;
    }

    final index = ownedTemplates.indexWhere(
      (template) => template.id == templateId,
    );

    if (index < 0) {
      throw StateError('Strategy template not found');
    }

    ownedTemplates.removeAt(index);
  }

  @override
  Future<StrategyTemplateActionResult> performAction({
    required int templateId,
    required StrategyTemplateAction action,
  }) {
    throw UnimplementedError();
  }

  @override
  Future<BackendTradingBot> createBotFromTemplate({
    required int templateId,
    required StrategyTemplateBotCreateRequest request,
  }) {
    throw UnimplementedError();
  }
}

BackendStrategyTemplate _template({
  required int id,
  required String name,
  required StrategyTemplateStatus status,
  StrategyTemplateVisibility visibility =
      StrategyTemplateVisibility.privateTemplate,
}) {
  final timestamp = DateTime.utc(2026, 8, 4, id);

  return BackendStrategyTemplate(
    id: id,
    userId: 7,
    name: name,
    description: 'Read-only template',
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
    publishedAt: status == StrategyTemplateStatus.published ? timestamp : null,
    archivedAt: status == StrategyTemplateStatus.archived ? timestamp : null,
    createdAt: timestamp,
    updatedAt: timestamp,
  );
}
