import 'portfolio_sync_snapshot.dart';

class PortfolioSyncResult {
  const PortfolioSyncResult({
    required this.snapshot,
    required this.created,
    required this.portfolioTotalValue,
    required this.portfolioProfitLoss,
    required this.sourceErrors,
  });

  final PortfolioSyncSnapshot snapshot;
  final bool created;
  final double portfolioTotalValue;
  final double portfolioProfitLoss;
  final Map<String, String> sourceErrors;

  factory PortfolioSyncResult.fromJson(Map<String, dynamic> json) {
    final snapshotValue = json['snapshot'];
    final createdValue = json['created'];
    final sourceErrorsValue = json['source_errors'];

    if (snapshotValue is! Map ||
        createdValue is! bool ||
        sourceErrorsValue is! Map) {
      throw const FormatException(
        'The portfolio synchronization result is invalid.',
      );
    }

    final sourceErrors = <String, String>{};

    for (final entry in sourceErrorsValue.entries) {
      final key = entry.key;
      final value = entry.value;

      if (key is! String || value is! String) {
        throw const FormatException(
          'The synchronization source errors are invalid.',
        );
      }

      sourceErrors[key] = value;
    }

    return PortfolioSyncResult(
      snapshot: PortfolioSyncSnapshot.fromJson(
        Map<String, dynamic>.from(snapshotValue),
      ),
      created: createdValue,
      portfolioTotalValue: _requiredDouble(
        json['portfolio_total_value'],
        'The synchronized portfolio value is invalid.',
      ),
      portfolioProfitLoss: _requiredDouble(
        json['portfolio_profit_loss'],
        'The synchronized portfolio profit or loss is invalid.',
      ),
      sourceErrors: Map<String, String>.unmodifiable(sourceErrors),
    );
  }
}

double _requiredDouble(Object? value, String message) {
  if (value is num) {
    return value.toDouble();
  }

  throw FormatException(message);
}
