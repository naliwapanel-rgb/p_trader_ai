import 'package:flutter/material.dart';

import '../../bots/data/backend_trading_bot.dart';
import '../data/backend_strategy_template.dart';

class EditStrategyTemplateDialog extends StatefulWidget {
  const EditStrategyTemplateDialog({required this.template, super.key});

  final BackendStrategyTemplate template;

  @override
  State<EditStrategyTemplateDialog> createState() {
    return _EditStrategyTemplateDialogState();
  }
}

class _EditStrategyTemplateDialogState
    extends State<EditStrategyTemplateDialog> {
  final _formKey = GlobalKey<FormState>();

  late final TextEditingController _nameController;
  late final TextEditingController _descriptionController;
  late final TextEditingController _symbolController;
  late final TextEditingController _riskController;
  late final TextEditingController _maxPositionController;
  late final TextEditingController _dailyLossController;
  late final TextEditingController _drawdownController;
  late final TextEditingController _stopLossController;
  late final TextEditingController _takeProfitController;

  late TradingBotStrategyType _strategy;
  late TradingBotCategory _category;
  late TradingBotTimeframe _timeframe;
  late StrategyTemplateVisibility _visibility;
  late bool _paperTrading;
  late bool _dryRun;

  String? _validationMessage;

  @override
  void initState() {
    super.initState();

    final template = widget.template;

    _nameController = TextEditingController(text: template.name);

    _descriptionController = TextEditingController(
      text: template.description ?? '',
    );

    _symbolController = TextEditingController(text: template.symbol);

    _riskController = TextEditingController(
      text: _formatNumber(template.riskPerTradePercent),
    );

    _maxPositionController = TextEditingController(
      text: _formatNumber(template.maxPositionValueUsd),
    );

    _dailyLossController = TextEditingController(
      text: _formatNumber(template.maxDailyLossPercent),
    );

    _drawdownController = TextEditingController(
      text: _formatNumber(template.maxDrawdownPercent),
    );

    _stopLossController = TextEditingController(
      text: _formatOptionalNumber(template.stopLossPercent),
    );

    _takeProfitController = TextEditingController(
      text: _formatOptionalNumber(template.takeProfitPercent),
    );

    _strategy = template.strategyType;
    _category = template.category;
    _timeframe = template.timeframe;
    _visibility = template.visibility;
    _paperTrading = template.paperTrading;
    _dryRun = template.dryRun;
  }

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
      title: const Text('Edit Strategy Template'),
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
                  key: const Key('edit-template-name-field'),
                  controller: _nameController,
                  maxLength: 150,
                  textInputAction: TextInputAction.next,
                  decoration: const InputDecoration(labelText: 'Template name'),
                  validator: _validateName,
                ),
                const SizedBox(height: 12),
                TextFormField(
                  key: const Key('edit-template-description-field'),
                  controller: _descriptionController,
                  maxLength: 2000,
                  minLines: 2,
                  maxLines: 4,
                  decoration: const InputDecoration(
                    labelText: 'Description',
                    alignLabelWithHint: true,
                  ),
                  validator: _validateDescription,
                ),
                const SizedBox(height: 12),
                TextFormField(
                  key: const Key('edit-template-symbol-field'),
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
                _dropdownField<TradingBotStrategyType>(
                  keyName: 'edit-template-strategy-field',
                  label: 'Strategy type',
                  value: _strategy,
                  values: TradingBotStrategyType.values,
                  itemLabel: (value) => _humanize(value.backendValue),
                  onChanged: (value) {
                    setState(() {
                      _strategy = value;
                    });
                  },
                ),
                const SizedBox(height: 12),
                _dropdownField<TradingBotCategory>(
                  keyName: 'edit-template-category-field',
                  label: 'Market category',
                  value: _category,
                  values: TradingBotCategory.values,
                  itemLabel: (value) => _humanize(value.backendValue),
                  onChanged: (value) {
                    setState(() {
                      _category = value;
                    });
                  },
                ),
                const SizedBox(height: 12),
                _dropdownField<TradingBotTimeframe>(
                  keyName: 'edit-template-timeframe-field',
                  label: 'Timeframe',
                  value: _timeframe,
                  values: TradingBotTimeframe.values,
                  itemLabel: (value) => value.backendValue,
                  onChanged: (value) {
                    setState(() {
                      _timeframe = value;
                    });
                  },
                ),
                const SizedBox(height: 12),
                _dropdownField<StrategyTemplateVisibility>(
                  keyName: 'edit-template-visibility-field',
                  label: 'Visibility',
                  value: _visibility,
                  values: StrategyTemplateVisibility.values,
                  itemLabel: (value) => _humanize(value.backendValue),
                  onChanged: (value) {
                    setState(() {
                      _visibility = value;
                    });
                  },
                ),
                const SizedBox(height: 20),
                Text(
                  'Risk controls',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 12),
                _numberField(
                  keyName: 'edit-template-risk-field',
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
                  keyName: 'edit-template-max-position-field',
                  controller: _maxPositionController,
                  label: 'Maximum position value (USD)',
                  validator: (value) => _validateRequiredNumber(
                    value,
                    label: 'Maximum position value',
                  ),
                ),
                const SizedBox(height: 12),
                _numberField(
                  keyName: 'edit-template-daily-loss-field',
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
                  keyName: 'edit-template-drawdown-field',
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
                  keyName: 'edit-template-stop-loss-field',
                  controller: _stopLossController,
                  label: 'Stop loss (%) - optional',
                  validator: (value) => _validateOptionalPercentage(
                    value,
                    label: 'Stop loss',
                    maximum: 100,
                  ),
                ),
                const SizedBox(height: 12),
                _numberField(
                  keyName: 'edit-template-take-profit-field',
                  controller: _takeProfitController,
                  label: 'Take profit (%) — optional',
                  validator: (value) => _validateOptionalPercentage(
                    value,
                    label: 'Take profit',
                    maximum: 1000,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'Blank optional percentages keep their current '
                  'backend values. Existing values cannot be cleared '
                  'from this editor.',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                const SizedBox(height: 20),
                Text(
                  'Safety mode',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                SwitchListTile(
                  key: const Key('edit-template-paper-trading-switch'),
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
                  key: const Key('edit-template-dry-run-switch'),
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
                if (_validationMessage != null) ...[
                  const SizedBox(height: 16),
                  Container(
                    key: const Key('edit-template-validation-message'),
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
          key: const Key('save-template-changes-button'),
          onPressed: _submit,
          icon: const Icon(Icons.save_outlined),
          label: const Text('Save Changes'),
        ),
      ],
    );
  }

  Widget _dropdownField<T>({
    required String keyName,
    required String label,
    required T value,
    required List<T> values,
    required String Function(T value) itemLabel,
    required ValueChanged<T> onChanged,
  }) {
    return DropdownButtonFormField<T>(
      key: Key(keyName),
      initialValue: value,
      isExpanded: true,
      decoration: InputDecoration(labelText: label),
      items: values
          .map(
            (item) =>
                DropdownMenuItem<T>(value: item, child: Text(itemLabel(item))),
          )
          .toList(growable: false),
      onChanged: (selected) {
        if (selected != null) {
          onChanged(selected);
        }
      },
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

    final template = widget.template;

    final name = _nameController.text.trim();
    final description = _descriptionController.text.trim();
    final symbol = _symbolController.text.trim().toUpperCase();

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

    final enteredStopLoss = _optionalDouble(_stopLossController.text);

    final enteredTakeProfit = _optionalDouble(_takeProfitController.text);

    final currentDescription = (template.description ?? '').trim();

    final request = StrategyTemplateUpdateRequest(
      name: name == template.name ? null : name,
      description: description == currentDescription ? null : description,
      strategyType: _strategy == template.strategyType ? null : _strategy,
      symbol: symbol == template.symbol ? null : symbol,
      category: _category == template.category ? null : _category,
      timeframe: _timeframe == template.timeframe ? null : _timeframe,
      visibility: _visibility == template.visibility ? null : _visibility,
      paperTrading: _paperTrading == template.paperTrading
          ? null
          : _paperTrading,
      dryRun: _dryRun == template.dryRun ? null : _dryRun,
      riskPerTradePercent: _differentDouble(risk, template.riskPerTradePercent)
          ? risk
          : null,
      maxPositionValueUsd:
          _differentDouble(maxPosition, template.maxPositionValueUsd)
          ? maxPosition
          : null,
      maxDailyLossPercent:
          _differentDouble(dailyLoss, template.maxDailyLossPercent)
          ? dailyLoss
          : null,
      maxDrawdownPercent:
          _differentDouble(drawdown, template.maxDrawdownPercent)
          ? drawdown
          : null,
      stopLossPercent: _changedOptionalNumber(
        entered: enteredStopLoss,
        current: template.stopLossPercent,
      ),
      takeProfitPercent: _changedOptionalNumber(
        entered: enteredTakeProfit,
        current: template.takeProfitPercent,
      ),
    );

    if (!request.hasChanges) {
      _showValidation('Change at least one field before saving.');
      return;
    }

    try {
      request.toJson();
    } on FormatException catch (error) {
      _showValidation(error.message.toString());
      return;
    } catch (_) {
      _showValidation('The strategy template update is invalid.');
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

  static double? _changedOptionalNumber({
    required double? entered,
    required double? current,
  }) {
    if (entered == null) {
      return null;
    }

    if (current != null && !_differentDouble(entered, current)) {
      return null;
    }

    return entered;
  }

  static bool _differentDouble(double first, double second) {
    return (first - second).abs() > 0.000000001;
  }

  static double? _optionalDouble(String value) {
    final normalized = value.trim();

    if (normalized.isEmpty) {
      return null;
    }

    return double.parse(normalized);
  }

  static String _formatNumber(double value) {
    if (value == value.roundToDouble()) {
      return value.toInt().toString();
    }

    return value.toString();
  }

  static String _formatOptionalNumber(double? value) {
    if (value == null) {
      return '';
    }

    return _formatNumber(value);
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
    required double maximum,
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

    if (parsed > maximum) {
      return '$label cannot exceed $maximum.';
    }

    return null;
  }

  static String _humanize(String value) {
    return value
        .toLowerCase()
        .split('_')
        .map(
          (part) => part.isEmpty
              ? part
              : '${part[0].toUpperCase()}${part.substring(1)}',
        )
        .join(' ');
  }
}
