import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/features/bots/data/backend_trading_bot.dart';
import 'package:p_trader_ai/features/strategy_templates/data/backend_strategy_template.dart';
import 'package:p_trader_ai/features/strategy_templates/widgets/edit_strategy_template_dialog.dart';

void main() {
  testWidgets('prefills fields and returns only safe changed values', (
    tester,
  ) async {
    StrategyTemplateUpdateRequest? savedRequest;

    await _pumpDialog(
      tester,
      onSaved: (request) {
        savedRequest = request;
      },
    );

    await tester.tap(find.byKey(const Key('open-template-editor-button')));

    await tester.pumpAndSettle();

    expect(find.text('Edit Strategy Template'), findsOneWidget);

    final nameField = tester.widget<TextFormField>(
      find.byKey(const Key('edit-template-name-field')),
    );

    final descriptionField = tester.widget<TextFormField>(
      find.byKey(const Key('edit-template-description-field')),
    );

    final symbolField = tester.widget<TextFormField>(
      find.byKey(const Key('edit-template-symbol-field')),
    );

    expect(nameField.controller?.text, 'Editable Momentum Template');

    expect(descriptionField.controller?.text, 'Safe edit dialog test');

    expect(symbolField.controller?.text, 'BTCUSDT');

    await tester.enterText(
      find.byKey(const Key('edit-template-name-field')),
      'Updated Momentum Template',
    );

    await tester.enterText(
      find.byKey(const Key('edit-template-symbol-field')),
      'ethusdt',
    );

    final paperSwitch = find.byKey(
      const Key('edit-template-paper-trading-switch'),
    );

    await tester.ensureVisible(paperSwitch);
    await tester.tap(paperSwitch);

    final stopLossField = find.byKey(
      const Key('edit-template-stop-loss-field'),
    );

    await tester.ensureVisible(stopLossField);
    await tester.enterText(stopLossField, '');

    final takeProfitField = find.byKey(
      const Key('edit-template-take-profit-field'),
    );

    await tester.ensureVisible(takeProfitField);
    await tester.enterText(takeProfitField, '');

    await tester.tap(find.byKey(const Key('save-template-changes-button')));

    await tester.pumpAndSettle();

    expect(savedRequest, isNotNull);
    expect(savedRequest?.name, 'Updated Momentum Template');
    expect(savedRequest?.symbol, 'ETHUSDT');
    expect(savedRequest?.paperTrading, isFalse);

    expect(savedRequest?.description, isNull);
    expect(savedRequest?.strategyType, isNull);
    expect(savedRequest?.category, isNull);
    expect(savedRequest?.timeframe, isNull);
    expect(savedRequest?.visibility, isNull);
    expect(savedRequest?.dryRun, isNull);

    expect(savedRequest?.riskPerTradePercent, isNull);
    expect(savedRequest?.maxPositionValueUsd, isNull);
    expect(savedRequest?.maxDailyLossPercent, isNull);
    expect(savedRequest?.maxDrawdownPercent, isNull);

    expect(savedRequest?.stopLossPercent, isNull);
    expect(savedRequest?.takeProfitPercent, isNull);

    expect(find.text('Edit Strategy Template'), findsNothing);
  });

  testWidgets('blocks unchanged and unsafe updates', (tester) async {
    StrategyTemplateUpdateRequest? savedRequest;

    await _pumpDialog(
      tester,
      onSaved: (request) {
        savedRequest = request;
      },
    );

    await tester.tap(find.byKey(const Key('open-template-editor-button')));

    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('save-template-changes-button')));

    await tester.pumpAndSettle();

    expect(savedRequest, isNull);

    expect(
      find.text('Change at least one field before saving.'),
      findsOneWidget,
    );

    final paperSwitch = find.byKey(
      const Key('edit-template-paper-trading-switch'),
    );

    final dryRunSwitch = find.byKey(const Key('edit-template-dry-run-switch'));

    await tester.ensureVisible(paperSwitch);
    await tester.tap(paperSwitch);

    await tester.ensureVisible(dryRunSwitch);
    await tester.tap(dryRunSwitch);

    await tester.tap(find.byKey(const Key('save-template-changes-button')));

    await tester.pumpAndSettle();

    expect(savedRequest, isNull);

    expect(
      find.text('Paper trading or dry run must remain enabled.'),
      findsOneWidget,
    );

    expect(find.text('Edit Strategy Template'), findsOneWidget);
  });
}

Future<void> _pumpDialog(
  WidgetTester tester, {
  required ValueChanged<StrategyTemplateUpdateRequest> onSaved,
}) async {
  tester.view.physicalSize = const Size(1200, 1800);
  tester.view.devicePixelRatio = 1;

  addTearDown(() {
    tester.view.resetPhysicalSize();
    tester.view.resetDevicePixelRatio();
  });

  await tester.pumpWidget(MaterialApp(home: _DialogLauncher(onSaved: onSaved)));

  await tester.pumpAndSettle();
}

class _DialogLauncher extends StatelessWidget {
  const _DialogLauncher({required this.onSaved});

  final ValueChanged<StrategyTemplateUpdateRequest> onSaved;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: FilledButton(
          key: const Key('open-template-editor-button'),
          onPressed: () async {
            final result = await showDialog<StrategyTemplateUpdateRequest>(
              context: context,
              builder: (_) => EditStrategyTemplateDialog(template: _template()),
            );

            if (result != null) {
              onSaved(result);
            }
          },
          child: const Text('Open Template Editor'),
        ),
      ),
    );
  }
}

BackendStrategyTemplate _template() {
  final timestamp = DateTime.utc(2026, 8, 4, 12);

  return BackendStrategyTemplate(
    id: 21,
    userId: 7,
    name: 'Editable Momentum Template',
    description: 'Safe edit dialog test',
    strategyType: TradingBotStrategyType.momentum,
    symbol: 'BTCUSDT',
    category: TradingBotCategory.linear,
    timeframe: TradingBotTimeframe.fiveMinutes,
    visibility: StrategyTemplateVisibility.privateTemplate,
    paperTrading: true,
    dryRun: true,
    riskPerTradePercent: 1,
    maxPositionValueUsd: 25,
    maxDailyLossPercent: 3,
    maxDrawdownPercent: 10,
    stopLossPercent: 2,
    takeProfitPercent: 4,
    strategyConfig: const <String, dynamic>{'period': 14},
    status: StrategyTemplateStatus.draft,
    version: 1,
    publishedAt: null,
    archivedAt: null,
    createdAt: timestamp,
    updatedAt: timestamp,
  );
}
