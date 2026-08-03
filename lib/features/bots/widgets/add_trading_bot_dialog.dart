import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/backend_trading_bot.dart';
import '../providers/backend_trading_bot_provider.dart';

class AddTradingBotDialog extends ConsumerStatefulWidget {
  const AddTradingBotDialog({super.key});

  @override
  ConsumerState<AddTradingBotDialog> createState() =>
      _AddTradingBotDialogState();
}

class _AddTradingBotDialogState extends ConsumerState<AddTradingBotDialog> {
  final _formKey = GlobalKey<FormState>();

  final _nameController = TextEditingController();
  final _symbolController = TextEditingController(text: 'BTCUSDT');

  TradingBotStrategyType _strategy = TradingBotStrategyType.ruleBased;

  bool _paperTrading = true;
  bool _dryRun = true;
  String? _validationMessage;

  @override
  void dispose() {
    _nameController.dispose();
    _symbolController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(backendTradingBotProvider);

    return AlertDialog(
      title: const Text('Create Trading Bot'),
      content: SizedBox(
        width: 460,
        child: Form(
          key: _formKey,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextFormField(
                  key: const Key('bot-name-field'),
                  controller: _nameController,
                  textInputAction: TextInputAction.next,
                  decoration: const InputDecoration(
                    labelText: 'Bot name',
                    hintText: 'Momentum BTC Bot',
                    prefixIcon: Icon(Icons.smart_toy_outlined),
                  ),
                  validator: (value) {
                    final name = value?.trim() ?? '';

                    if (name.length < 2) {
                      return 'Enter at least 2 characters.';
                    }

                    if (name.length > 150) {
                      return 'Use no more than 150 characters.';
                    }

                    return null;
                  },
                ),
                const SizedBox(height: 16),
                TextFormField(
                  key: const Key('bot-symbol-field'),
                  controller: _symbolController,
                  textCapitalization: TextCapitalization.characters,
                  decoration: const InputDecoration(
                    labelText: 'Trading symbol',
                    hintText: 'BTCUSDT',
                    prefixIcon: Icon(Icons.currency_bitcoin),
                  ),
                  validator: (value) {
                    final symbol = value?.trim() ?? '';

                    if (symbol.length < 2 || symbol.length > 30) {
                      return 'Enter a valid trading symbol.';
                    }

                    return null;
                  },
                ),
                const SizedBox(height: 16),
                DropdownButtonFormField<TradingBotStrategyType>(
                  key: const Key('bot-strategy-field'),
                  initialValue: _strategy,
                  decoration: const InputDecoration(
                    labelText: 'Strategy',
                    prefixIcon: Icon(Icons.analytics_outlined),
                  ),
                  items: TradingBotStrategyType.values
                      .map(
                        (strategy) => DropdownMenuItem(
                          value: strategy,
                          child: Text(_strategyLabel(strategy)),
                        ),
                      )
                      .toList(growable: false),
                  onChanged: state.isMutating
                      ? null
                      : (strategy) {
                          if (strategy != null) {
                            setState(() {
                              _strategy = strategy;
                            });
                          }
                        },
                ),
                const SizedBox(height: 16),
                SwitchListTile(
                  key: const Key('paper-trading-switch'),
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Paper trading'),
                  subtitle: const Text('Use simulated funds.'),
                  value: _paperTrading,
                  onChanged: state.isMutating
                      ? null
                      : (value) {
                          setState(() {
                            _paperTrading = value;
                          });
                        },
                ),
                SwitchListTile(
                  key: const Key('dry-run-switch'),
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Dry run'),
                  subtitle: const Text('Do not place live exchange orders.'),
                  value: _dryRun,
                  onChanged: state.isMutating
                      ? null
                      : (value) {
                          setState(() {
                            _dryRun = value;
                          });
                        },
                ),
                if (_validationMessage != null) ...[
                  const SizedBox(height: 12),
                  Text(
                    _validationMessage!,
                    key: const Key('bot-validation-message'),
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.error,
                    ),
                  ),
                ],
                if (state.errorMessage != null) ...[
                  const SizedBox(height: 12),
                  Text(
                    state.errorMessage!,
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.error,
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: state.isMutating ? null : () => Navigator.pop(context),
          child: const Text('Cancel'),
        ),
        FilledButton.icon(
          key: const Key('create-bot-button'),
          onPressed: state.isMutating ? null : _submit,
          icon: state.isMutating
              ? const SizedBox.square(
                  dimension: 18,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.add),
          label: Text(state.isMutating ? 'Creating...' : 'Create Bot'),
        ),
      ],
    );
  }

  Future<void> _submit() async {
    setState(() {
      _validationMessage = null;
    });

    if (!(_formKey.currentState?.validate() ?? false)) {
      return;
    }

    if (!_paperTrading && !_dryRun) {
      setState(() {
        _validationMessage = 'Paper trading or dry run must remain enabled.';
      });
      return;
    }

    final bot = await ref
        .read(backendTradingBotProvider.notifier)
        .createBot(
          TradingBotCreateRequest(
            name: _nameController.text,
            symbol: _symbolController.text,
            strategyType: _strategy,
            paperTrading: _paperTrading,
            dryRun: _dryRun,
          ),
        );

    if (bot != null && mounted) {
      Navigator.pop(context, bot);
    }
  }

  static String _strategyLabel(TradingBotStrategyType strategy) {
    return switch (strategy) {
      TradingBotStrategyType.ruleBased => 'Rule Based',
      TradingBotStrategyType.momentum => 'Momentum',
      TradingBotStrategyType.trend => 'Trend',
      TradingBotStrategyType.meanReversion => 'Mean Reversion',
      TradingBotStrategyType.scalping => 'Scalping',
      TradingBotStrategyType.grid => 'Grid',
      TradingBotStrategyType.dca => 'DCA',
      TradingBotStrategyType.arbitrage => 'Arbitrage',
      TradingBotStrategyType.custom => 'Custom',
    };
  }
}
