import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/features/bots/data/backend_trading_bot.dart';
import 'package:p_trader_ai/features/strategy_templates/data/backend_strategy_template.dart';
import 'package:p_trader_ai/features/strategy_templates/widgets/add_strategy_template_dialog.dart';

void main() {
  testWidgets('returns a safe normalized template request', (tester) async {
    StrategyTemplateCreateRequest? result;

    await _pumpDialogHost(
      tester,
      onResult: (value) {
        result = value;
      },
    );

    await tester.enterText(
      find.byKey(const Key('template-name-field')),
      '  Momentum Template  ',
    );

    await tester.enterText(
      find.byKey(const Key('template-description-field')),
      '  Safe momentum strategy  ',
    );

    await tester.enterText(
      find.byKey(const Key('template-symbol-field')),
      'ethusdt',
    );

    await tester.ensureVisible(
      find.byKey(const Key('create-strategy-template-button')),
    );

    await tester.tap(find.byKey(const Key('create-strategy-template-button')));

    await tester.pumpAndSettle();

    expect(result, isNotNull);
    expect(result?.name, 'Momentum Template');
    expect(result?.description, 'Safe momentum strategy');
    expect(result?.symbol, 'ETHUSDT');
    expect(result?.strategyType, TradingBotStrategyType.ruleBased);
    expect(result?.category, TradingBotCategory.linear);
    expect(result?.timeframe, TradingBotTimeframe.fiveMinutes);
    expect(result?.visibility, StrategyTemplateVisibility.privateTemplate);
    expect(result?.paperTrading, isTrue);
    expect(result?.dryRun, isTrue);
    expect(result?.riskPerTradePercent, 1);
    expect(result?.maxPositionValueUsd, 25);
    expect(result?.maxDailyLossPercent, 3);
    expect(result?.maxDrawdownPercent, 10);
    expect(result?.strategyConfig, isEmpty);
    expect(find.text('Create Strategy Template'), findsNothing);
  });

  testWidgets('blocks creation when all safety modes are disabled', (
    tester,
  ) async {
    StrategyTemplateCreateRequest? result;

    await _pumpDialogHost(
      tester,
      onResult: (value) {
        result = value;
      },
    );

    await tester.enterText(
      find.byKey(const Key('template-name-field')),
      'Safe Template',
    );

    await tester.enterText(
      find.byKey(const Key('template-symbol-field')),
      'BTCUSDT',
    );

    await tester.tap(find.byKey(const Key('template-paper-trading-switch')));

    await tester.pump();

    await tester.tap(find.byKey(const Key('template-dry-run-switch')));

    await tester.pump();

    await tester.ensureVisible(
      find.byKey(const Key('create-strategy-template-button')),
    );

    await tester.tap(find.byKey(const Key('create-strategy-template-button')));

    await tester.pumpAndSettle();

    expect(result, isNull);
    expect(
      find.text('Paper trading or dry run must remain enabled.'),
      findsOneWidget,
    );
    expect(find.text('Create Strategy Template'), findsOneWidget);
  });

  testWidgets('blocks invalid risk hierarchy', (tester) async {
    StrategyTemplateCreateRequest? result;

    await _pumpDialogHost(
      tester,
      onResult: (value) {
        result = value;
      },
    );

    await tester.enterText(
      find.byKey(const Key('template-name-field')),
      'Risk Test Template',
    );

    await tester.enterText(
      find.byKey(const Key('template-symbol-field')),
      'BTCUSDT',
    );

    await tester.enterText(find.byKey(const Key('template-risk-field')), '5');

    await tester.enterText(
      find.byKey(const Key('template-daily-loss-field')),
      '3',
    );

    await tester.ensureVisible(
      find.byKey(const Key('create-strategy-template-button')),
    );

    await tester.tap(find.byKey(const Key('create-strategy-template-button')));

    await tester.pumpAndSettle();

    expect(result, isNull);
    expect(
      find.text('Risk per trade cannot exceed maximum daily loss.'),
      findsOneWidget,
    );
  });
}

Future<void> _pumpDialogHost(
  WidgetTester tester, {
  required void Function(StrategyTemplateCreateRequest? result) onResult,
}) async {
  tester.view.physicalSize = const Size(1200, 1600);

  tester.view.devicePixelRatio = 1;

  addTearDown(() {
    tester.view.resetPhysicalSize();
    tester.view.resetDevicePixelRatio();
  });

  await tester.pumpWidget(
    MaterialApp(
      home: Builder(
        builder: (context) {
          return Scaffold(
            body: Center(
              child: FilledButton(
                key: const Key('open-template-dialog-button'),
                onPressed: () async {
                  final result =
                      await showDialog<StrategyTemplateCreateRequest>(
                        context: context,
                        builder: (_) => const AddStrategyTemplateDialog(),
                      );

                  onResult(result);
                },
                child: const Text('Open'),
              ),
            ),
          );
        },
      ),
    ),
  );

  await tester.tap(find.byKey(const Key('open-template-dialog-button')));

  await tester.pumpAndSettle();

  expect(find.text('Create Strategy Template'), findsOneWidget);
}
