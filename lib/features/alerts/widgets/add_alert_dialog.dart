import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_spacing.dart';

import '../data/price_alert.dart';
import '../providers/price_alert_provider.dart';

class AddAlertDialog extends ConsumerStatefulWidget {
  const AddAlertDialog({super.key});

  @override
  ConsumerState<AddAlertDialog> createState() => _AddAlertDialogState();
}

class _AddAlertDialogState extends ConsumerState<AddAlertDialog> {
  final _symbolController = TextEditingController();
  final _priceController = TextEditingController();

  PriceAlertCondition _condition = PriceAlertCondition.above;

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Create Price Alert'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          TextField(
            controller: _symbolController,
            decoration: const InputDecoration(
              labelText: 'Coin Symbol',
              hintText: 'BTC',
            ),
          ),
          const SizedBox(height: AppSpacing.md),
          TextField(
            controller: _priceController,
            decoration: const InputDecoration(
              labelText: 'Target Price',
              hintText: '120000',
            ),
            keyboardType: TextInputType.number,
          ),
          const SizedBox(height: AppSpacing.md),
          DropdownButtonFormField<PriceAlertCondition>(
            initialValue: _condition,
            decoration: const InputDecoration(labelText: 'Condition'),
            items: const [
              DropdownMenuItem(
                value: PriceAlertCondition.above,
                child: Text('Price Above'),
              ),
              DropdownMenuItem(
                value: PriceAlertCondition.below,
                child: Text('Price Below'),
              ),
            ],
            onChanged: (value) {
              if (value == null) return;

              setState(() {
                _condition = value;
              });
            },
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancel'),
        ),
        FilledButton(
          onPressed: () async {
            final symbol = _symbolController.text.trim().toUpperCase();
            final price = double.tryParse(_priceController.text.trim());

            if (symbol.isEmpty || price == null || price <= 0) {
              return;
            }

            final alert = PriceAlert(
              id: DateTime.now().millisecondsSinceEpoch.toString(),
              coinId: symbol.toLowerCase(),
              symbol: symbol,
              targetPrice: price,
              condition: _condition,
              isEnabled: true,
              createdAt: DateTime.now(),
            );

            await ref.read(priceAlertsProvider.notifier).addAlert(alert);

            if (context.mounted) {
              Navigator.pop(context);
            }
          },
          child: const Text('Save'),
        ),
      ],
    );
  }
}
