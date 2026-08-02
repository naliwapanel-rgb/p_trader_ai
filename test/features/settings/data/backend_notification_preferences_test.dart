import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/features/settings/data/backend_notification_preferences.dart';

void main() {
  group('BackendNotificationPreferences', () {
    test('parses backend defaults', () {
      final preferences = BackendNotificationPreferences.fromJson(
        _preferencesJson(),
      );

      expect(preferences.id, 4);
      expect(preferences.userId, 9);
      expect(preferences.emailEnabled, isTrue);
      expect(preferences.pushEnabled, isTrue);
      expect(preferences.soundEnabled, isTrue);
      expect(preferences.priceAlerts, isTrue);
      expect(preferences.arbitrageAlerts, isTrue);
      expect(preferences.aiAlerts, isTrue);
      expect(preferences.newsAlerts, isFalse);
      expect(preferences.updatedAt.isUtc, isTrue);
    });

    test('parses disabled preference values', () {
      final preferences = BackendNotificationPreferences.fromJson(
        _preferencesJson(
          emailEnabled: false,
          pushEnabled: false,
          priceAlerts: false,
          newsAlerts: true,
        ),
      );

      expect(preferences.emailEnabled, isFalse);
      expect(preferences.pushEnabled, isFalse);
      expect(preferences.priceAlerts, isFalse);
      expect(preferences.newsAlerts, isTrue);
    });

    test('rejects invalid backend data', () {
      final json = _preferencesJson();
      json['updated_at'] = 'invalid-date';

      expect(
        () => BackendNotificationPreferences.fromJson(json),
        throwsFormatException,
      );
    });

    test('serializes only supplied update fields', () {
      const update = NotificationPreferenceUpdate(
        pushEnabled: false,
        newsAlerts: true,
      );

      expect(update.hasChanges, isTrue);
      expect(update.toJson(), <String, Object>{
        'push_enabled': false,
        'news_alerts': true,
      });

      const empty = NotificationPreferenceUpdate();

      expect(empty.hasChanges, isFalse);
      expect(empty.toJson(), isEmpty);
    });
  });
}

Map<String, dynamic> _preferencesJson({
  bool emailEnabled = true,
  bool pushEnabled = true,
  bool soundEnabled = true,
  bool priceAlerts = true,
  bool arbitrageAlerts = true,
  bool aiAlerts = true,
  bool newsAlerts = false,
}) {
  return <String, dynamic>{
    'id': 4,
    'user_id': 9,
    'email_enabled': emailEnabled,
    'push_enabled': pushEnabled,
    'sound_enabled': soundEnabled,
    'price_alerts': priceAlerts,
    'arbitrage_alerts': arbitrageAlerts,
    'ai_alerts': aiAlerts,
    'news_alerts': newsAlerts,
    'updated_at': '2026-08-03T00:00:00Z',
  };
}
