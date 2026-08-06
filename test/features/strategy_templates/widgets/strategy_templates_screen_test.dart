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

    testWidgets('creates a bot from an owned draft strategy template', (
      tester,
    ) async {
      final repository = _ReadOnlyRepository(
        ownedTemplates: <BackendStrategyTemplate>[
          _template(
            id: 13,
            name: 'Draft Bot Source',
            status: StrategyTemplateStatus.draft,
          ),
        ],
      );

      await _pumpScreen(tester, repository);

      await tester.tap(find.byKey(const Key('template-13-details-button')));
      await tester.pumpAndSettle();

      expect(
        find.byKey(const Key('template-13-create-bot-button')),
        findsOneWidget,
      );

      await tester.tap(find.byKey(const Key('template-13-create-bot-button')));
      await tester.pumpAndSettle();

      expect(find.text('Create Bot from Template'), findsOneWidget);

      await tester.enterText(
        find.byKey(const Key('template-bot-name-field')),
        '  Draft   Momentum Bot  ',
      );
      await tester.enterText(
        find.byKey(const Key('template-bot-exchange-account-field')),
        '9',
      );
      await tester.enterText(
        find.byKey(const Key('template-bot-description-field')),
        '  Screen-created bot  ',
      );

      await tester.ensureVisible(
        find.byKey(const Key('create-bot-from-template-button')),
      );
      await tester.tap(
        find.byKey(const Key('create-bot-from-template-button')),
      );
      await tester.pumpAndSettle();

      expect(repository.createBotCalls, 1);
      expect(repository.lastCreateBotTemplateId, 13);
      expect(repository.lastCreateBotRequest?.name, 'Draft Momentum Bot');
      expect(repository.lastCreateBotRequest?.exchangeAccountId, 9);
      expect(
        repository.lastCreateBotRequest?.description,
        'Screen-created bot',
      );
      expect(
        find.text('Trading bot created from template successfully.'),
        findsOneWidget,
      );
      expect(find.text('Create Bot from Template'), findsNothing);
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

    testWidgets('creates a bot from a public published strategy template', (
      tester,
    ) async {
      final repository = _ReadOnlyRepository(
        ownedTemplates: <BackendStrategyTemplate>[
          _template(
            id: 14,
            name: 'Public Bot Source',
            status: StrategyTemplateStatus.published,
            visibility: StrategyTemplateVisibility.publicTemplate,
          ),
        ],
      );

      await _pumpScreen(tester, repository);

      await tester.tap(find.byKey(const Key('public-templates-tab')));
      await tester.pumpAndSettle();

      await tester.tap(find.byKey(const Key('template-14-details-button')));
      await tester.pumpAndSettle();

      expect(
        find.byKey(const Key('template-14-create-bot-button')),
        findsOneWidget,
      );
      expect(find.byKey(const Key('template-14-edit-button')), findsNothing);

      await tester.tap(find.byKey(const Key('template-14-create-bot-button')));
      await tester.pumpAndSettle();

      await tester.enterText(
        find.byKey(const Key('template-bot-name-field')),
        'Community Momentum Bot',
      );

      await tester.ensureVisible(
        find.byKey(const Key('create-bot-from-template-button')),
      );
      await tester.tap(
        find.byKey(const Key('create-bot-from-template-button')),
      );
      await tester.pumpAndSettle();

      expect(repository.createBotCalls, 1);
      expect(repository.lastCreateBotTemplateId, 14);
      expect(repository.lastCreateBotRequest?.name, 'Community Momentum Bot');
      expect(repository.lastCreateBotRequest?.exchangeAccountId, isNull);
      expect(repository.lastCreateBotRequest?.description, isNull);
      expect(
        find.text('Trading bot created from template successfully.'),
        findsOneWidget,
      );
    });

    testWidgets('does not offer bot creation for archived templates', (
      tester,
    ) async {
      final repository = _ReadOnlyRepository(
        ownedTemplates: <BackendStrategyTemplate>[
          _template(
            id: 15,
            name: 'Archived Bot Source',
            status: StrategyTemplateStatus.archived,
          ),
        ],
      );

      await _pumpScreen(tester, repository);

      await tester.tap(find.byKey(const Key('template-15-details-button')));
      await tester.pumpAndSettle();

      expect(
        find.byKey(const Key('template-15-create-bot-button')),
        findsNothing,
      );
      expect(
        find.byKey(const Key('template-15-restore-button')),
        findsOneWidget,
      );
      expect(repository.createBotCalls, 0);
    });

    testWidgets(
      'shows backend errors when bot creation from a template fails',
      (tester) async {
        final repository = _ReadOnlyRepository(
          ownedTemplates: <BackendStrategyTemplate>[
            _template(
              id: 16,
              name: 'Rejected Bot Source',
              status: StrategyTemplateStatus.draft,
            ),
          ],
          createBotError: const AppException('Bot creation was rejected'),
        );

        await _pumpScreen(tester, repository);

        await tester.tap(find.byKey(const Key('template-16-details-button')));
        await tester.pumpAndSettle();

        await tester.tap(
          find.byKey(const Key('template-16-create-bot-button')),
        );
        await tester.pumpAndSettle();

        await tester.enterText(
          find.byKey(const Key('template-bot-name-field')),
          'Rejected Template Bot',
        );

        await tester.ensureVisible(
          find.byKey(const Key('create-bot-from-template-button')),
        );
        await tester.tap(
          find.byKey(const Key('create-bot-from-template-button')),
        );
        await tester.pumpAndSettle();

        expect(repository.createBotCalls, 1);
        expect(repository.lastCreateBotTemplateId, 16);
        expect(repository.lastCreateBotRequest?.name, 'Rejected Template Bot');
        expect(find.text('Bot creation was rejected'), findsOneWidget);
        expect(find.text('Rejected Bot Source'), findsOneWidget);
        expect(find.text('Create Bot from Template'), findsNothing);
        expect(
          find.text('Trading bot created from template successfully.'),
          findsNothing,
        );
      },
    );

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

    testWidgets('publishes an owned draft strategy template', (tester) async {
      final repository = _ReadOnlyRepository(
        ownedTemplates: <BackendStrategyTemplate>[
          _template(
            id: 9,
            name: 'Draft Lifecycle Template',
            status: StrategyTemplateStatus.draft,
          ),
        ],
      );

      await _pumpScreen(tester, repository);

      await tester.tap(find.byKey(const Key('template-9-details-button')));
      await tester.pumpAndSettle();

      expect(
        find.byKey(const Key('template-9-publish-button')),
        findsOneWidget,
      );
      expect(
        find.byKey(const Key('template-9-archive-button')),
        findsOneWidget,
      );
      expect(
        find.byKey(const Key('template-9-unpublish-button')),
        findsNothing,
      );
      expect(find.byKey(const Key('template-9-restore-button')), findsNothing);

      await tester.tap(find.byKey(const Key('template-9-publish-button')));
      await tester.pumpAndSettle();

      expect(repository.actionCalls, 1);
      expect(repository.lastActionTemplateId, 9);
      expect(repository.lastAction, StrategyTemplateAction.publish);

      expect(find.text('PUBLISHED'), findsOneWidget);
      expect(find.text('Visibility: Public'), findsOneWidget);
      expect(
        find.text('Strategy template published successfully.'),
        findsOneWidget,
      );
    });

    testWidgets('unpublishes an owned published strategy template', (
      tester,
    ) async {
      final repository = _ReadOnlyRepository(
        ownedTemplates: <BackendStrategyTemplate>[
          _template(
            id: 10,
            name: 'Published Lifecycle Template',
            status: StrategyTemplateStatus.published,
            visibility: StrategyTemplateVisibility.publicTemplate,
          ),
        ],
      );

      await _pumpScreen(tester, repository);

      await tester.tap(find.byKey(const Key('template-10-details-button')));
      await tester.pumpAndSettle();

      expect(
        find.byKey(const Key('template-10-unpublish-button')),
        findsOneWidget,
      );
      expect(
        find.byKey(const Key('template-10-archive-button')),
        findsOneWidget,
      );
      expect(find.byKey(const Key('template-10-publish-button')), findsNothing);
      expect(find.byKey(const Key('template-10-restore-button')), findsNothing);

      await tester.tap(find.byKey(const Key('template-10-unpublish-button')));
      await tester.pumpAndSettle();

      expect(repository.actionCalls, 1);
      expect(repository.lastActionTemplateId, 10);
      expect(repository.lastAction, StrategyTemplateAction.unpublish);

      expect(find.text('DRAFT'), findsOneWidget);
      expect(find.text('Visibility: Private'), findsOneWidget);
      expect(
        find.text('Strategy template unpublished successfully.'),
        findsOneWidget,
      );
    });

    testWidgets('shows backend errors when lifecycle action fails', (
      tester,
    ) async {
      final repository = _ReadOnlyRepository(
        ownedTemplates: <BackendStrategyTemplate>[
          _template(
            id: 11,
            name: 'Protected Lifecycle Template',
            status: StrategyTemplateStatus.draft,
          ),
        ],
        actionError: const AppException(
          'Template lifecycle action was rejected',
        ),
      );

      await _pumpScreen(tester, repository);

      await tester.tap(find.byKey(const Key('template-11-details-button')));
      await tester.pumpAndSettle();

      await tester.tap(find.byKey(const Key('template-11-publish-button')));
      await tester.pumpAndSettle();

      expect(repository.actionCalls, 1);
      expect(repository.lastActionTemplateId, 11);
      expect(repository.lastAction, StrategyTemplateAction.publish);
      expect(
        find.text('Template lifecycle action was rejected'),
        findsOneWidget,
      );
      expect(find.text('Protected Lifecycle Template'), findsOneWidget);
      expect(find.text('DRAFT'), findsOneWidget);
      expect(find.text('Visibility: Private'), findsOneWidget);
    });

    testWidgets('archives and restores an owned strategy template', (
      tester,
    ) async {
      final repository = _ReadOnlyRepository(
        ownedTemplates: <BackendStrategyTemplate>[
          _template(
            id: 12,
            name: 'Archive Lifecycle Template',
            status: StrategyTemplateStatus.draft,
          ),
        ],
      );

      await _pumpScreen(tester, repository);

      await tester.tap(find.byKey(const Key('template-12-details-button')));
      await tester.pumpAndSettle();

      await tester.tap(find.byKey(const Key('template-12-archive-button')));
      await tester.pumpAndSettle();

      expect(repository.actionCalls, 1);
      expect(repository.lastActionTemplateId, 12);
      expect(repository.lastAction, StrategyTemplateAction.archive);
      expect(find.text('ARCHIVED'), findsOneWidget);
      expect(find.text('Visibility: Private'), findsOneWidget);
      expect(
        find.text('Strategy template archived successfully.'),
        findsOneWidget,
      );

      await tester.tap(find.byKey(const Key('template-12-details-button')));
      await tester.pumpAndSettle();

      expect(
        find.byKey(const Key('template-12-restore-button')),
        findsOneWidget,
      );
      expect(find.byKey(const Key('template-12-publish-button')), findsNothing);
      expect(
        find.byKey(const Key('template-12-unpublish-button')),
        findsNothing,
      );
      expect(find.byKey(const Key('template-12-archive-button')), findsNothing);

      await tester.tap(find.byKey(const Key('template-12-restore-button')));
      await tester.pumpAndSettle();

      expect(repository.actionCalls, 2);
      expect(repository.lastActionTemplateId, 12);
      expect(repository.lastAction, StrategyTemplateAction.restore);
      expect(find.text('DRAFT'), findsOneWidget);
      expect(find.text('Visibility: Private'), findsOneWidget);
      expect(
        find.text('Strategy template restored successfully.'),
        findsOneWidget,
      );
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
    this.actionError,
    this.createBotError,
  }) : ownedTemplates = ownedTemplates ?? <BackendStrategyTemplate>[];

  final List<BackendStrategyTemplate> ownedTemplates;

  final AppException? listOwnedError;
  final AppException? createError;
  final AppException? updateError;
  final AppException? deleteError;
  final AppException? actionError;
  final AppException? createBotError;

  int listOwnedCalls = 0;
  int listPublicCalls = 0;
  int createCalls = 0;
  int updateCalls = 0;
  int deleteCalls = 0;
  int actionCalls = 0;
  int createBotCalls = 0;

  StrategyTemplateCreateRequest? lastCreateRequest;
  StrategyTemplateUpdateRequest? lastUpdateRequest;
  int? lastUpdateTemplateId;
  int? lastDeleteTemplateId;
  int? lastActionTemplateId;
  StrategyTemplateAction? lastAction;
  int? lastCreateBotTemplateId;
  StrategyTemplateBotCreateRequest? lastCreateBotRequest;

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
  }) async {
    actionCalls += 1;
    lastActionTemplateId = templateId;
    lastAction = action;

    final error = actionError;
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
      StrategyTemplateAction.archive => existing.visibility,
    };

    final updated = _template(
      id: existing.id,
      name: existing.name,
      status: nextStatus,
      visibility: nextVisibility,
    );

    ownedTemplates[index] = updated;

    return StrategyTemplateActionResult(
      action: action,
      previousStatus: existing.status,
      status: nextStatus,
      changed: existing.status != nextStatus,
      template: updated,
    );
  }

  @override
  Future<BackendTradingBot> createBotFromTemplate({
    required int templateId,
    required StrategyTemplateBotCreateRequest request,
  }) async {
    createBotCalls += 1;
    lastCreateBotTemplateId = templateId;
    lastCreateBotRequest = request;

    final error = createBotError;
    if (error != null) {
      throw error;
    }

    final template = ownedTemplates.firstWhere(
      (candidate) => candidate.id == templateId,
    );
    final description = request.description?.trim();
    final timestamp = DateTime.utc(2026, 8, 6, createBotCalls);

    return BackendTradingBot(
      id: 200 + createBotCalls,
      userId: template.userId,
      exchangeAccountId: request.exchangeAccountId,
      name: request.name.trim().split(RegExp(r'\s+')).join(' '),
      description: description == null || description.isEmpty
          ? template.description
          : description,
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
