import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/backend_trading_bot.dart';
import '../providers/backend_trading_bot_provider.dart';

class EditTradingBotDialog extends ConsumerStatefulWidget {
  const EditTradingBotDialog({required this.bot, super.key});

  final BackendTradingBot bot;

  @override
  ConsumerState<EditTradingBotDialog> createState() =>
      _EditTradingBotDialogState();
}

class _EditTradingBotDialogState extends ConsumerState<EditTradingBotDialog> {
  final _formKey = GlobalKey<FormState>();

  late final TextEditingController _nameController;
  late final TextEditingController _symbolController;

  late TradingBotStrategyType _strategy;
  late TradingBotTimeframe _timeframe;
  late bool _paperTrading;
  late bool _dryRun;

  String? _validationMessage;

  @override
  void initState() {
    super.initState();

    _nameController = TextEditingController(text: widget.bot.name);

    _symbolController = TextEditingController(text: widget.bot.symbol);

    _strategy = widget.bot.strategyType;
    _timeframe = widget.bot.timeframe;
    _paperTrading = widget.bot.paperTrading;
    _dryRun = widget.bot.dryRun;
  }

  @override
  void dispose() {
    _nameController.dispose();
    _symbolController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(backendTradingBotProvider);

    final editingBlocked = widget.bot.status.isActive;

    return AlertDialog(
      title: const Text('Edit Trading Bot'),
      content: SizedBox(
        width: 480,
        child: Form(
          key: _formKey,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (editingBlocked) ...[
                  Container(
                    key: const Key('active-bot-edit-warning'),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.errorContainer,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      children: [
                        Icon(
                          Icons.lock_outline,
                          color: Theme.of(context).colorScheme.onErrorContainer,
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            'Active trading bots cannot '
                            'be edited. Stop the bot '
                            'before editing.',
                            style: TextStyle(
                              color: Theme.of(
                                context,
                              ).colorScheme.onErrorContainer,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                ],
                TextFormField(
                  key: const Key('edit-bot-name-field'),
                  controller: _nameController,
                  enabled: !state.isMutating && !editingBlocked,
                  textInputAction: TextInputAction.next,
                  decoration: const InputDecoration(
                    labelText: 'Bot name',
                    prefixIcon: Icon(Icons.smart_toy_outlined),
                  ),
                  validator: (value) {
                    final name = value?.trim() ?? '';

                    if (name.length < 2) {
                      return 'Enter at least '
                          '2 characters.';
                    }

                    if (name.length > 150) {
                      return 'Use no more than '
                          '150 characters.';
                    }

                    return null;
                  },
                ),
                const SizedBox(height: 16),
                TextFormField(
                  key: const Key('edit-bot-symbol-field'),
                  controller: _symbolController,
                  enabled: !state.isMutating && !editingBlocked,
                  textCapitalization: TextCapitalization.characters,
                  decoration: const InputDecoration(
                    labelText: 'Trading symbol',
                    hintText: 'BTCUSDT',
                    prefixIcon: Icon(Icons.currency_bitcoin),
                  ),
                  validator: (value) {
                    final symbol = value?.trim() ?? '';

                    if (symbol.length < 2 || symbol.length > 30) {
                      return 'Enter a valid '
                          'trading symbol.';
                    }

                    return null;
                  },
                ),
                const SizedBox(height: 16),
                DropdownButtonFormField<TradingBotStrategyType>(
                  key: const Key('edit-bot-strategy-field'),
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
                  onChanged: state.isMutating || editingBlocked
                      ? null
                      : (strategy) {
                          if (strategy == null) {
                            return;
                          }

                          setState(() {
                            _strategy = strategy;
                          });
                        },
                ),
                const SizedBox(height: 16),
                DropdownButtonFormField<TradingBotTimeframe>(
                  key: const Key('edit-bot-timeframe-field'),
                  initialValue: _timeframe,
                  decoration: const InputDecoration(
                    labelText: 'Timeframe',
                    prefixIcon: Icon(Icons.schedule),
                  ),
                  items: TradingBotTimeframe.values
                      .map(
                        (timeframe) => DropdownMenuItem(
                          value: timeframe,
                          child: Text(timeframe.backendValue),
                        ),
                      )
                      .toList(growable: false),
                  onChanged: state.isMutating || editingBlocked
                      ? null
                      : (timeframe) {
                          if (timeframe == null) {
                            return;
                          }

                          setState(() {
                            _timeframe = timeframe;
                          });
                        },
                ),
                const SizedBox(height: 8),
                SwitchListTile(
                  key: const Key('edit-paper-trading-switch'),
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Paper trading'),
                  subtitle: const Text('Use simulated funds.'),
                  value: _paperTrading,
                  onChanged: state.isMutating || editingBlocked
                      ? null
                      : (value) {
                          setState(() {
                            _paperTrading = value;
                          });
                        },
                ),
                SwitchListTile(
                  key: const Key('edit-dry-run-switch'),
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Dry run'),
                  subtitle: const Text(
                    'Do not place live '
                    'exchange orders.',
                  ),
                  value: _dryRun,
                  onChanged: state.isMutating || editingBlocked
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
                    key: const Key('edit-bot-validation-message'),
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
          key: const Key('save-bot-changes-button'),
          onPressed: state.isMutating || editingBlocked ? null : _submit,
          icon: state.isMutating
              ? const SizedBox.square(
                  dimension: 18,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.save_outlined),
          label: Text(state.isMutating ? 'Saving...' : 'Save Changes'),
        ),
      ],
    );
  }

  Future<void> _submit() async {
    setState(() {
      _validationMessage = null;
    });

    if (widget.bot.status.isActive) {
      setState(() {
        _validationMessage = 'Stop the active bot before editing.';
      });
      return;
    }

    if (!(_formKey.currentState?.validate() ?? false)) {
      return;
    }

    if (!_paperTrading && !_dryRun) {
      setState(() {
        _validationMessage =
            'Paper trading or dry run '
            'must remain enabled.';
      });
      return;
    }

    final updated = await ref
        .read(backendTradingBotProvider.notifier)
        .updateBot(
          botId: widget.bot.id,
          request: TradingBotUpdateRequest(
            name: _nameController.text,
            symbol: _symbolController.text,
            strategyType: _strategy,
            timeframe: _timeframe,
            paperTrading: _paperTrading,
            dryRun: _dryRun,
          ),
        );

    if (updated != null && mounted) {
      Navigator.pop(context, updated);
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
