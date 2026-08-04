import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/features/bots/data/backend_trading_bot.dart';
import 'package:p_trader_ai/features/strategy_templates/data/backend_strategy_template.dart';
import 'package:p_trader_ai/features/strategy_templates/providers/backend_strategy_template_state.dart';

void main() {
  group('BackendStrategyTemplateState', () {
    test('starts empty and unloaded', () {
      const state = BackendStrategyTemplateState.initial();

      expect(state.ownedTemplates, isEmpty);
      expect(state.publicTemplates, isEmpty);
      expect(state.busyTemplateIds, isEmpty);
      expect(state.isLoadingOwned, isFalse);
      expect(state.isLoadingPublic, isFalse);
      expect(state.isMutating, isFalse);
      expect(state.hasLoadedOwned, isFalse);
      expect(state.hasLoadedPublic, isFalse);
      expect(state.errorMessage, isNull);
      expect(state.infoMessage, isNull);
    });

    test('filters owned template statuses', () {
      final state = BackendStrategyTemplateState(
        ownedTemplates: <BackendStrategyTemplate>[
          _template(id: 1, status: StrategyTemplateStatus.draft),
          _template(id: 2, status: StrategyTemplateStatus.published),
          _template(id: 3, status: StrategyTemplateStatus.archived),
        ],
        publicTemplates: const <BackendStrategyTemplate>[],
        busyTemplateIds: const <int>{},
        isLoadingOwned: false,
        isLoadingPublic: false,
        isMutating: false,
        hasLoadedOwned: true,
        hasLoadedPublic: false,
      );

      expect(state.draftTemplates.map((template) => template.id), <int>[1]);

      expect(state.publishedTemplates.map((template) => template.id), <int>[2]);

      expect(state.archivedTemplates.map((template) => template.id), <int>[3]);
    });

    test('finds templates and reports busy IDs', () {
      final owned = _template(id: 7, status: StrategyTemplateStatus.draft);

      final public = _template(
        id: 8,
        status: StrategyTemplateStatus.published,
        visibility: StrategyTemplateVisibility.publicTemplate,
      );

      final state = BackendStrategyTemplateState(
        ownedTemplates: <BackendStrategyTemplate>[owned],
        publicTemplates: <BackendStrategyTemplate>[public],
        busyTemplateIds: const <int>{7},
        isLoadingOwned: false,
        isLoadingPublic: false,
        isMutating: false,
        hasLoadedOwned: true,
        hasLoadedPublic: true,
      );

      expect(state.findOwnedById(7)?.id, 7);
      expect(state.findOwnedById(99), isNull);
      expect(state.findPublicById(8)?.id, 8);
      expect(state.findPublicById(99), isNull);
      expect(state.isTemplateBusy(7), isTrue);
      expect(state.isTemplateBusy(8), isFalse);
    });

    test('clears transient messages', () {
      final state = BackendStrategyTemplateState(
        ownedTemplates: const <BackendStrategyTemplate>[],
        publicTemplates: const <BackendStrategyTemplate>[],
        busyTemplateIds: const <int>{},
        isLoadingOwned: false,
        isLoadingPublic: false,
        isMutating: false,
        hasLoadedOwned: true,
        hasLoadedPublic: true,
        errorMessage: 'Failed',
        infoMessage: 'Updated',
      );

      final cleared = state.copyWith(clearError: true, clearInfo: true);

      expect(cleared.errorMessage, isNull);
      expect(cleared.infoMessage, isNull);
      expect(cleared.hasLoadedOwned, isTrue);
      expect(cleared.hasLoadedPublic, isTrue);
    });
  });
}

BackendStrategyTemplate _template({
  required int id,
  required StrategyTemplateStatus status,
  StrategyTemplateVisibility visibility =
      StrategyTemplateVisibility.privateTemplate,
}) {
  final timestamp = DateTime.utc(2026, 8, 4, id);

  return BackendStrategyTemplate(
    id: id,
    userId: 7,
    name: 'Template $id',
    description: 'State test template',
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
