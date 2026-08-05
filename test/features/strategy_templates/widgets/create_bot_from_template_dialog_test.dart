import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/features/bots/data/backend_trading_bot.dart';
import 'package:p_trader_ai/features/strategy_templates/data/backend_strategy_template.dart';
import 'package:p_trader_ai/features/strategy_templates/widgets/create_bot_from_template_dialog.dart';

void main() {
  testWidgets('returns a normalized bot request from a template', (
    tester,
  ) async {
    StrategyTemplateBotCreateRequest? result;

    await _pumpDialogHost(
      tester,
      onResult: (value) {
        result = value;
      },
    );

    expect(
      find.text('Source: Momentum Template\nBTCUSDT • 5m'),
      findsOneWidget,
    );
    expect(
      find.text('The bot will start with paper trading and dry run enabled.'),
      findsOneWidget,
    );

    await tester.enterText(
      find.byKey(const Key('template-bot-name-field')),
      '  Momentum   Copy  ',
    );

    await tester.enterText(
      find.byKey(const Key('template-bot-exchange-account-field')),
      '12',
    );

    await tester.enterText(
      find.byKey(const Key('template-bot-description-field')),
      '  Created from template  ',
    );

    await tester.ensureVisible(
      find.byKey(const Key('create-bot-from-template-button')),
    );

    await tester.tap(find.byKey(const Key('create-bot-from-template-button')));

    await tester.pumpAndSettle();

    expect(result, isNotNull);
    expect(result?.name, 'Momentum Copy');
    expect(result?.exchangeAccountId, 12);
    expect(result?.description, 'Created from template');
    expect(find.text('Create Bot from Template'), findsNothing);
  });

  testWidgets('allows optional bot fields to remain empty', (tester) async {
    StrategyTemplateBotCreateRequest? result;

    await _pumpDialogHost(
      tester,
      onResult: (value) {
        result = value;
      },
    );

    await tester.enterText(
      find.byKey(const Key('template-bot-name-field')),
      'Safe Bot',
    );

    await tester.ensureVisible(
      find.byKey(const Key('create-bot-from-template-button')),
    );

    await tester.tap(find.byKey(const Key('create-bot-from-template-button')));

    await tester.pumpAndSettle();

    expect(result, isNotNull);
    expect(result?.name, 'Safe Bot');
    expect(result?.exchangeAccountId, isNull);
    expect(result?.description, isNull);
  });

  testWidgets('blocks an invalid exchange account ID', (tester) async {
    StrategyTemplateBotCreateRequest? result;

    await _pumpDialogHost(
      tester,
      onResult: (value) {
        result = value;
      },
    );

    await tester.enterText(
      find.byKey(const Key('template-bot-name-field')),
      'Safe Bot',
    );

    await tester.enterText(
      find.byKey(const Key('template-bot-exchange-account-field')),
      '0',
    );

    await tester.ensureVisible(
      find.byKey(const Key('create-bot-from-template-button')),
    );

    await tester.tap(find.byKey(const Key('create-bot-from-template-button')));

    await tester.pumpAndSettle();

    expect(result, isNull);
    expect(
      find.text('Exchange account ID must be a positive whole number.'),
      findsOneWidget,
    );
    expect(find.text('Create Bot from Template'), findsOneWidget);
  });

  testWidgets('requires a valid bot name', (tester) async {
    StrategyTemplateBotCreateRequest? result;

    await _pumpDialogHost(
      tester,
      onResult: (value) {
        result = value;
      },
    );

    await tester.ensureVisible(
      find.byKey(const Key('create-bot-from-template-button')),
    );

    await tester.tap(find.byKey(const Key('create-bot-from-template-button')));

    await tester.pumpAndSettle();

    expect(result, isNull);
    expect(find.text('Bot name is required.'), findsOneWidget);
    expect(find.text('Create Bot from Template'), findsOneWidget);
  });
}

Future<void> _pumpDialogHost(
  WidgetTester tester, {
  required void Function(StrategyTemplateBotCreateRequest? result) onResult,
}) async {
  tester.view.physicalSize = const Size(1200, 1400);
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
                key: const Key('open-template-bot-dialog-button'),
                onPressed: () async {
                  final result =
                      await showDialog<StrategyTemplateBotCreateRequest>(
                        context: context,
                        builder: (_) =>
                            CreateBotFromTemplateDialog(template: _template()),
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

  await tester.tap(find.byKey(const Key('open-template-bot-dialog-button')));

  await tester.pumpAndSettle();

  expect(find.text('Create Bot from Template'), findsOneWidget);
}

BackendStrategyTemplate _template() {
  final timestamp = DateTime.utc(2026, 8, 5);

  return BackendStrategyTemplate(
    id: 21,
    userId: 7,
    name: 'Momentum Template',
    description: 'Safe reusable template',
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
