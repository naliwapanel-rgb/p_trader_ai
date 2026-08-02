import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_spacing.dart';
import '../data/backend_price_alert.dart';
import '../providers/backend_price_alert_provider.dart';

class AddAlertDialog extends ConsumerStatefulWidget {
  const AddAlertDialog({super.key});

  @override
  ConsumerState<AddAlertDialog> createState() => _AddAlertDialogState();
}

class _AddAlertDialogState extends ConsumerState<AddAlertDialog> {
  static const List<String> _supportedExchanges = <String>[
    'BYBIT',
    'BINANCE',
    'MEXC',
    'GATEIO',
  ];

  final _symbolController = TextEditingController();
  final _priceController = TextEditingController();

  BackendPriceAlertCondition _condition = BackendPriceAlertCondition.above;

  String _exchange = PriceAlertSymbolMapper.defaultExchange;

  String? _errorMessage;

  @override
  void dispose() {
    _symbolController.dispose();
    _priceController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(backendPriceAlertProvider);

    return AlertDialog(
      title: const Text('Create Price Alert'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: _symbolController,
              textCapitalization: TextCapitalization.characters,
              decoration: const InputDecoration(
                labelText: 'Asset Symbol',
                hintText: 'BTC',
                helperText: 'Enter the base asset only.',
              ),
            ),
            const SizedBox(height: AppSpacing.md),
            DropdownButtonFormField<String>(
              initialValue: _exchange,
              decoration: const InputDecoration(labelText: 'Exchange'),
              items: _supportedExchanges
                  .map(
                    (exchange) => DropdownMenuItem(
                      value: exchange,
                      child: Text(exchange),
                    ),
                  )
                  .toList(growable: false),
              onChanged: state.isMutating
                  ? null
                  : (value) {
                      if (value == null) {
                        return;
                      }

                      setState(() {
                        _exchange = value;
                      });
                    },
            ),
            const SizedBox(height: AppSpacing.md),
            TextField(
              controller: _priceController,
              decoration: const InputDecoration(
                labelText: 'Target Price',
                hintText: '120000',
                prefixText: '\$',
              ),
              keyboardType: const TextInputType.numberWithOptions(
                decimal: true,
              ),
            ),
            const SizedBox(height: AppSpacing.md),
            DropdownButtonFormField<BackendPriceAlertCondition>(
              initialValue: _condition,
              decoration: const InputDecoration(labelText: 'Condition'),
              items: BackendPriceAlertCondition.values
                  .map(
                    (condition) => DropdownMenuItem(
                      value: condition,
                      child: Text(condition.label),
                    ),
                  )
                  .toList(growable: false),
              onChanged: state.isMutating
                  ? null
                  : (value) {
                      if (value == null) {
                        return;
                      }

                      setState(() {
                        _condition = value;
                      });
                    },
            ),
            if (_errorMessage != null) ...[
              const SizedBox(height: AppSpacing.md),
              Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  _errorMessage!,
                  style: TextStyle(color: Theme.of(context).colorScheme.error),
                ),
              ),
            ],
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: state.isMutating
              ? null
              : () => Navigator.pop(context, false),
          child: const Text('Cancel'),
        ),
        FilledButton(
          onPressed: state.isMutating ? null : _createAlert,
          child: state.isMutating
              ? const SizedBox.square(
                  dimension: 18,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Text('Save'),
        ),
      ],
    );
  }

  Future<void> _createAlert() async {
    final symbol = _symbolController.text.trim();
    final price = double.tryParse(_priceController.text.trim());

    if (symbol.length < 2) {
      setState(() {
        _errorMessage = 'Enter a valid asset symbol such as BTC.';
      });
      return;
    }

    if (price == null || !price.isFinite || price <= 0) {
      setState(() {
        _errorMessage = 'Enter a target price greater than zero.';
      });
      return;
    }

    setState(() {
      _errorMessage = null;
    });

    final created = await ref
        .read(backendPriceAlertProvider.notifier)
        .createAlert(
          symbol: symbol,
          exchange: _exchange,
          condition: _condition,
          targetPrice: price,
        );

    if (!mounted) {
      return;
    }

    if (created == null) {
      setState(() {
        _errorMessage =
            ref.read(backendPriceAlertProvider).errorMessage ??
            'The price alert could not be created.';
      });
      return;
    }

    Navigator.pop(context, true);
  }
}
