import 'package:flutter/material.dart';

import '../../bots/data/backend_trading_bot.dart';
import '../data/backend_strategy_template.dart';

class AddStrategyTemplateDialog extends StatefulWidget {
  const AddStrategyTemplateDialog({super.key});

  @override
  State<AddStrategyTemplateDialog> createState() {
    return _AddStrategyTemplateDialogState();
  }
}

class _AddStrategyTemplateDialogState extends State<AddStrategyTemplateDialog> {
  final _formKey = GlobalKey<FormState>();

  final _nameController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _symbolController = TextEditingController();

  final _riskController = TextEditingController(text: '1');
  final _maxPositionController = TextEditingController(text: '25');
  final _dailyLossController = TextEditingController(text: '3');
  final _drawdownController = TextEditingController(text: '10');
  final _stopLossController = TextEditingController();
  final _takeProfitController = TextEditingController();

  TradingBotStrategyType _strategy = TradingBotStrategyType.ruleBased;

  TradingBotCategory _category = TradingBotCategory.linear;

  TradingBotTimeframe _timeframe = TradingBotTimeframe.fiveMinutes;

  StrategyTemplateVisibility _visibility =
      StrategyTemplateVisibility.privateTemplate;

  bool _paperTrading = true;
  bool _dryRun = true;

  String? _validationMessage;

  @override
  void dispose() {
    _nameController.dispose();
    _descriptionController.dispose();
    _symbolController.dispose();
    _riskController.dispose();
    _maxPositionController.dispose();
    _dailyLossController.dispose();
    _drawdownController.dispose();
    _stopLossController.dispose();
    _takeProfitController.dispose();

    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Create Strategy Template'),
      content: SizedBox(
        width: 580,
        child: SingleChildScrollView(
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                TextFormField(
                  key: const Key('template-name-field'),
                  controller: _nameController,
                  maxLength: 150,
                  textInputAction: TextInputAction.next,
                  decoration: const InputDecoration(
                    labelText: 'Template name',
                    hintText: 'Example: BTC Momentum Template',
                  ),
                  validator: _validateName,
                ),
                const SizedBox(height: 12),
                TextFormField(
                  key: const Key('template-description-field'),
                  controller: _descriptionController,
                  maxLength: 2000,
                  minLines: 2,
                  maxLines: 4,
                  decoration: const InputDecoration(
                    labelText: 'Description',
                    hintText: 'Optional explanation of the strategy',
                    alignLabelWithHint: true,
                  ),
                  validator: _validateDescription,
                ),
                const SizedBox(height: 12),
                TextFormField(
                  key: const Key('template-symbol-field'),
                  controller: _symbolController,
                  maxLength: 30,
                  textCapitalization: TextCapitalization.characters,
                  textInputAction: TextInputAction.next,
                  decoration: const InputDecoration(
                    labelText: 'Trading symbol',
                    hintText: 'BTCUSDT',
                  ),
                  validator: _validateSymbol,
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<TradingBotStrategyType>(
                  key: const Key('template-strategy-field'),
                  initialValue: _strategy,
                  isExpanded: true,
                  decoration: const InputDecoration(labelText: 'Strategy type'),
                  items: TradingBotStrategyType.values
                      .map(
                        (strategy) => DropdownMenuItem<TradingBotStrategyType>(
                          value: strategy,
                          child: Text(_humanize(strategy.backendValue)),
                        ),
                      )
                      .toList(growable: false),
                  onChanged: (value) {
                    if (value != null) {
                      setState(() {
                        _strategy = value;
                      });
                    }
                  },
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<TradingBotCategory>(
                  key: const Key('template-category-field'),
                  initialValue: _category,
                  isExpanded: true,
                  decoration: const InputDecoration(
                    labelText: 'Market category',
                  ),
                  items: TradingBotCategory.values
                      .map(
                        (category) => DropdownMenuItem<TradingBotCategory>(
                          value: category,
                          child: Text(_humanize(category.backendValue)),
                        ),
                      )
                      .toList(growable: false),
                  onChanged: (value) {
                    if (value != null) {
                      setState(() {
                        _category = value;
                      });
                    }
                  },
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<TradingBotTimeframe>(
                  key: const Key('template-timeframe-field'),
                  initialValue: _timeframe,
                  isExpanded: true,
                  decoration: const InputDecoration(labelText: 'Timeframe'),
                  items: TradingBotTimeframe.values
                      .map(
                        (timeframe) => DropdownMenuItem<TradingBotTimeframe>(
                          value: timeframe,
                          child: Text(timeframe.backendValue),
                        ),
                      )
                      .toList(growable: false),
                  onChanged: (value) {
                    if (value != null) {
                      setState(() {
                        _timeframe = value;
                      });
                    }
                  },
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<StrategyTemplateVisibility>(
                  key: const Key('template-visibility-field'),
                  initialValue: _visibility,
                  isExpanded: true,
                  decoration: const InputDecoration(labelText: 'Visibility'),
                  items: StrategyTemplateVisibility.values
                      .map(
                        (visibility) =>
                            DropdownMenuItem<StrategyTemplateVisibility>(
                              value: visibility,
                              child: Text(_humanize(visibility.backendValue)),
                            ),
                      )
                      .toList(growable: false),
                  onChanged: (value) {
                    if (value != null) {
                      setState(() {
                        _visibility = value;
                      });
                    }
                  },
                ),
                const SizedBox(height: 20),
                Text(
                  'Risk controls',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 12),
                _numberField(
                  keyName: 'template-risk-field',
                  controller: _riskController,
                  label: 'Risk per trade (%)',
                  validator: (value) => _validateRequiredNumber(
                    value,
                    label: 'Risk per trade',
                    maximum: 100,
                  ),
                ),
                const SizedBox(height: 12),
                _numberField(
                  keyName: 'template-max-position-field',
                  controller: _maxPositionController,
                  label: 'Maximum position value (USD)',
                  validator: (value) => _validateRequiredNumber(
                    value,
                    label: 'Maximum position value',
                  ),
                ),
                const SizedBox(height: 12),
                _numberField(
                  keyName: 'template-daily-loss-field',
                  controller: _dailyLossController,
                  label: 'Maximum daily loss (%)',
                  validator: (value) => _validateRequiredNumber(
                    value,
                    label: 'Maximum daily loss',
                    maximum: 100,
                  ),
                ),
                const SizedBox(height: 12),
                _numberField(
                  keyName: 'template-drawdown-field',
                  controller: _drawdownController,
                  label: 'Maximum drawdown (%)',
                  validator: (value) => _validateRequiredNumber(
                    value,
                    label: 'Maximum drawdown',
                    maximum: 100,
                  ),
                ),
                const SizedBox(height: 12),
                _numberField(
                  keyName: 'template-stop-loss-field',
                  controller: _stopLossController,
                  label: 'Stop loss (%) — optional',
                  validator: (value) =>
                      _validateOptionalPercentage(value, label: 'Stop loss'),
                ),
                const SizedBox(height: 12),
                _numberField(
                  keyName: 'template-take-profit-field',
                  controller: _takeProfitController,
                  label: 'Take profit (%) — optional',
                  validator: (value) =>
                      _validateOptionalPercentage(value, label: 'Take profit'),
                ),
                const SizedBox(height: 20),
                Text(
                  'Safety mode',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                SwitchListTile(
                  key: const Key('template-paper-trading-switch'),
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Paper trading'),
                  subtitle: const Text(
                    'Simulate trades without using real funds.',
                  ),
                  value: _paperTrading,
                  onChanged: (value) {
                    setState(() {
                      _paperTrading = value;
                    });
                  },
                ),
                SwitchListTile(
                  key: const Key('template-dry-run-switch'),
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Dry run'),
                  subtitle: const Text(
                    'Evaluate decisions without submitting orders.',
                  ),
                  value: _dryRun,
                  onChanged: (value) {
                    setState(() {
                      _dryRun = value;
                    });
                  },
                ),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Theme.of(
                      context,
                    ).colorScheme.primaryContainer.withValues(alpha: 0.45),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Text(
                    'New templates use an empty strategy '
                    'configuration initially. Advanced strategy '
                    'parameters will be configured in the '
                    'dedicated strategy configuration stage.',
                  ),
                ),
                if (_validationMessage != null) ...[
                  const SizedBox(height: 16),
                  Container(
                    key: const Key('template-validation-message'),
                    width: double.infinity,
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.errorContainer,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      _validationMessage!,
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.onErrorContainer,
                      ),
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
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Cancel'),
        ),
        FilledButton.icon(
          key: const Key('create-strategy-template-button'),
          onPressed: _submit,
          icon: const Icon(Icons.add),
          label: const Text('Create Template'),
        ),
      ],
    );
  }

  Widget _numberField({
    required String keyName,
    required TextEditingController controller,
    required String label,
    required String? Function(String?) validator,
  }) {
    return TextFormField(
      key: Key(keyName),
      controller: controller,
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      textInputAction: TextInputAction.next,
      decoration: InputDecoration(labelText: label),
      validator: validator,
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
      _showValidation('Paper trading or dry run must remain enabled.');
      return;
    }

    final risk = double.parse(_riskController.text.trim());

    final maxPosition = double.parse(_maxPositionController.text.trim());

    final dailyLoss = double.parse(_dailyLossController.text.trim());

    final drawdown = double.parse(_drawdownController.text.trim());

    if (risk > dailyLoss) {
      _showValidation('Risk per trade cannot exceed maximum daily loss.');
      return;
    }

    if (dailyLoss > drawdown) {
      _showValidation('Maximum daily loss cannot exceed maximum drawdown.');
      return;
    }

    final description = _descriptionController.text.trim();

    final stopLoss = _optionalDouble(_stopLossController.text);

    final takeProfit = _optionalDouble(_takeProfitController.text);

    final request = StrategyTemplateCreateRequest(
      name: _nameController.text.trim(),
      description: description.isEmpty ? null : description,
      strategyType: _strategy,
      symbol: _symbolController.text.trim().toUpperCase(),
      category: _category,
      timeframe: _timeframe,
      visibility: _visibility,
      paperTrading: _paperTrading,
      dryRun: _dryRun,
      riskPerTradePercent: risk,
      maxPositionValueUsd: maxPosition,
      maxDailyLossPercent: dailyLoss,
      maxDrawdownPercent: drawdown,
      stopLossPercent: stopLoss,
      takeProfitPercent: takeProfit,
      strategyConfig: const <String, dynamic>{},
    );

    try {
      request.toJson();
    } catch (_) {
      _showValidation('The strategy template configuration is invalid.');
      return;
    }

    if (!mounted) {
      return;
    }

    Navigator.of(context).pop(request);
  }

  void _showValidation(String message) {
    setState(() {
      _validationMessage = message;
    });
  }

  static String? _validateName(String? value) {
    final normalized = value?.trim() ?? '';

    if (normalized.isEmpty) {
      return 'Template name is required.';
    }

    if (normalized.length < 2) {
      return 'Template name must contain at least 2 characters.';
    }

    if (normalized.length > 150) {
      return 'Template name cannot exceed 150 characters.';
    }

    return null;
  }

  static String? _validateDescription(String? value) {
    if ((value ?? '').trim().length > 2000) {
      return 'Description cannot exceed 2000 characters.';
    }

    return null;
  }

  static String? _validateSymbol(String? value) {
    final normalized = value?.trim() ?? '';

    if (normalized.isEmpty) {
      return 'Trading symbol is required.';
    }

    if (normalized.length < 2) {
      return 'Trading symbol must contain at least 2 characters.';
    }

    if (normalized.length > 30) {
      return 'Trading symbol cannot exceed 30 characters.';
    }

    return null;
  }

  static String? _validateRequiredNumber(
    String? value, {
    required String label,
    double? maximum,
  }) {
    final normalized = value?.trim() ?? '';

    if (normalized.isEmpty) {
      return '$label is required.';
    }

    final parsed = double.tryParse(normalized);

    if (parsed == null) {
      return '$label must be a valid number.';
    }

    if (!parsed.isFinite || parsed <= 0) {
      return '$label must be greater than zero.';
    }

    if (maximum != null && parsed > maximum) {
      return '$label cannot exceed $maximum.';
    }

    return null;
  }

  static String? _validateOptionalPercentage(
    String? value, {
    required String label,
  }) {
    final normalized = value?.trim() ?? '';

    if (normalized.isEmpty) {
      return null;
    }

    final parsed = double.tryParse(normalized);

    if (parsed == null) {
      return '$label must be a valid number.';
    }

    if (!parsed.isFinite || parsed <= 0) {
      return '$label must be greater than zero.';
    }

    if (parsed > 100) {
      return '$label cannot exceed 100.';
    }

    return null;
  }

  static double? _optionalDouble(String value) {
    final normalized = value.trim();

    if (normalized.isEmpty) {
      return null;
    }

    return double.parse(normalized);
  }

  static String _humanize(String value) {
    return value
        .toLowerCase()
        .split('_')
        .map(
          (part) => part.isEmpty
              ? part
              : '${part[0].toUpperCase()}'
                    '${part.substring(1)}',
        )
        .join(' ');
  }
}
