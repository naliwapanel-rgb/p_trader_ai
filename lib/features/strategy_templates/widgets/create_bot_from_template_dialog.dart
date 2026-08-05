import 'package:flutter/material.dart';

import '../../bots/data/backend_trading_bot.dart';
import '../data/backend_strategy_template.dart';

class CreateBotFromTemplateDialog extends StatefulWidget {
  const CreateBotFromTemplateDialog({required this.template, super.key});

  final BackendStrategyTemplate template;

  @override
  State<CreateBotFromTemplateDialog> createState() =>
      _CreateBotFromTemplateDialogState();
}

class _CreateBotFromTemplateDialogState
    extends State<CreateBotFromTemplateDialog> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _exchangeAccountController = TextEditingController();
  final _descriptionController = TextEditingController();

  String? _validationMessage;

  @override
  void dispose() {
    _nameController.dispose();
    _exchangeAccountController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Create Bot from Template'),
      content: SizedBox(
        width: 500,
        child: SingleChildScrollView(
          child: Form(
            key: _formKey,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Source: ${widget.template.name}\n'
                  '${widget.template.symbol} • '
                  '${widget.template.timeframe.backendValue}',
                ),
                const SizedBox(height: 8),
                const Text(
                  'The bot will start with paper trading and dry run enabled.',
                ),
                const SizedBox(height: 16),
                TextFormField(
                  key: const Key('template-bot-name-field'),
                  controller: _nameController,
                  autofocus: true,
                  maxLength: 150,
                  textInputAction: TextInputAction.next,
                  decoration: const InputDecoration(
                    labelText: 'Bot name',
                    hintText: 'Example: BTC Momentum Bot',
                    prefixIcon: Icon(Icons.smart_toy_outlined),
                  ),
                  validator: _validateName,
                ),
                const SizedBox(height: 12),
                TextFormField(
                  key: const Key('template-bot-exchange-account-field'),
                  controller: _exchangeAccountController,
                  keyboardType: TextInputType.number,
                  textInputAction: TextInputAction.next,
                  decoration: const InputDecoration(
                    labelText: 'Exchange account ID',
                    hintText: 'Optional positive account ID',
                    prefixIcon: Icon(Icons.account_balance_wallet_outlined),
                  ),
                  validator: _validateExchangeAccountId,
                ),
                const SizedBox(height: 12),
                TextFormField(
                  key: const Key('template-bot-description-field'),
                  controller: _descriptionController,
                  maxLength: 2000,
                  minLines: 2,
                  maxLines: 4,
                  decoration: const InputDecoration(
                    labelText: 'Description',
                    hintText: 'Optional bot description',
                    alignLabelWithHint: true,
                    prefixIcon: Icon(Icons.notes_outlined),
                  ),
                  validator: _validateDescription,
                ),
                if (_validationMessage != null) ...[
                  const SizedBox(height: 12),
                  Text(
                    _validationMessage!,
                    key: const Key('template-bot-validation-message'),
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
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Cancel'),
        ),
        FilledButton.icon(
          key: const Key('create-bot-from-template-button'),
          onPressed: _submit,
          icon: const Icon(Icons.add),
          label: const Text('Create Bot'),
        ),
      ],
    );
  }

  void _submit() {
    setState(() => _validationMessage = null);

    if (!(_formKey.currentState?.validate() ?? false)) {
      return;
    }

    final exchangeAccount = _exchangeAccountController.text.trim();
    final description = _descriptionController.text.trim();

    final request = StrategyTemplateBotCreateRequest(
      name: _normalizeWhitespace(_nameController.text),
      exchangeAccountId: exchangeAccount.isEmpty
          ? null
          : int.parse(exchangeAccount),
      description: description.isEmpty ? null : description,
    );

    try {
      request.toJson();
    } on FormatException catch (error) {
      setState(() => _validationMessage = error.message);
      return;
    }

    Navigator.of(context).pop(request);
  }

  static String? _validateName(String? value) {
    final normalized = _normalizeWhitespace(value ?? '');

    if (normalized.isEmpty) {
      return 'Bot name is required.';
    }
    if (normalized.length < 2) {
      return 'Bot name must contain at least 2 characters.';
    }
    if (normalized.length > 150) {
      return 'Bot name cannot exceed 150 characters.';
    }
    return null;
  }

  static String? _validateExchangeAccountId(String? value) {
    final normalized = value?.trim() ?? '';

    if (normalized.isEmpty) {
      return null;
    }

    final parsed = int.tryParse(normalized);
    if (parsed == null || parsed <= 0) {
      return 'Exchange account ID must be a positive whole number.';
    }
    return null;
  }

  static String? _validateDescription(String? value) {
    if ((value ?? '').trim().length > 2000) {
      return 'Description cannot exceed 2000 characters.';
    }
    return null;
  }

  static String _normalizeWhitespace(String value) {
    return value.trim().split(RegExp(r'\s+')).join(' ');
  }
}
