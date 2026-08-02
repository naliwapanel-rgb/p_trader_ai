class ExchangeConnectionResult {
  const ExchangeConnectionResult({required this.data});

  final Map<String, dynamic> data;

  factory ExchangeConnectionResult.fromJson(Map<String, dynamic> json) {
    return ExchangeConnectionResult(
      data: Map<String, dynamic>.unmodifiable(json),
    );
  }

  bool get appearsConnected {
    final connected = data['connected'];

    if (connected is bool) {
      return connected;
    }

    final success = data['success'];

    if (success is bool) {
      return success;
    }

    final status = data['status'];

    if (status is String) {
      final normalized = status.trim().toLowerCase();

      return normalized == 'connected' ||
          normalized == 'success' ||
          normalized == 'ok' ||
          normalized == 'active';
    }

    return true;
  }

  String get summary {
    for (final key in const <String>[
      'message',
      'detail',
      'status',
      'account_type',
      'accountType',
      'exchange',
      'exchange_name',
    ]) {
      final value = data[key];

      if (value is String && value.trim().isNotEmpty) {
        return value.trim();
      }
    }

    return appearsConnected
        ? 'The exchange accepted the stored credentials.'
        : 'The exchange did not confirm the connection.';
  }
}
