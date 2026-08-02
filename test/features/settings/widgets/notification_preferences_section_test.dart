import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/core/errors/app_exception.dart';
import 'package:p_trader_ai/features/settings/data/backend_notification_preferences.dart';
import 'package:p_trader_ai/features/settings/domain/notification_preferences_repository.dart';
import 'package:p_trader_ai/features/settings/providers/backend_notification_preferences_provider.dart';
import 'package:p_trader_ai/features/settings/widgets/notification_preferences_section.dart';

void main() {
  group('NotificationPreferencesSection', () {
    testWidgets('loads and renders all backend preferences', (tester) async {
      final repository = _FakeRepository();

      await tester.pumpWidget(_app(repository: repository));
      await tester.pumpAndSettle();

      expect(repository.getCalls, 1);
      expect(find.text('Notification Preferences'), findsOneWidget);
      expect(find.byType(SwitchListTile), findsNWidgets(7));
      expect(find.text('Push Notifications'), findsOneWidget);
      expect(find.text('Market News'), findsOneWidget);
    });

    testWidgets('updates a single preference switch', (tester) async {
      final repository = _FakeRepository();

      await tester.pumpWidget(_app(repository: repository));
      await tester.pumpAndSettle();

      await tester.tap(
        find.widgetWithText(SwitchListTile, 'Push Notifications'),
      );
      await tester.pumpAndSettle();

      expect(repository.updateCalls, 1);
      expect(repository.lastUpdate?.pushEnabled, isFalse);

      final pushTile = tester
          .widgetList<SwitchListTile>(find.byType(SwitchListTile))
          .firstWhere(
            (tile) => (tile.title as Text).data == 'Push Notifications',
          );

      expect(pushTile.value, isFalse);
    });

    testWidgets('shows an error and supports retry', (tester) async {
      final repository = _FakeRepository(
        getError: const AppException('Unable to load preferences'),
      );

      await tester.pumpWidget(_app(repository: repository));
      await tester.pumpAndSettle();

      expect(find.text('Notification settings unavailable'), findsOneWidget);

      repository.getError = null;

      await tester.tap(find.text('Retry'));
      await tester.pumpAndSettle();

      expect(repository.getCalls, 2);
      expect(find.text('Push Notifications'), findsOneWidget);
    });

    testWidgets('does not load while disabled', (tester) async {
      final repository = _FakeRepository();

      await tester.pumpWidget(_app(repository: repository, enabled: false));
      await tester.pumpAndSettle();

      expect(repository.getCalls, 0);
      expect(find.text('Sign in to manage notifications.'), findsOneWidget);
    });
  });
}

Widget _app({
  required NotificationPreferencesRepository repository,
  bool enabled = true,
}) {
  return ProviderScope(
    overrides: [
      notificationPreferencesRepositoryProvider.overrideWithValue(repository),
    ],
    child: MaterialApp(
      home: Scaffold(
        body: SingleChildScrollView(
          child: NotificationPreferencesSection(enabled: enabled),
        ),
      ),
    ),
  );
}

class _FakeRepository implements NotificationPreferencesRepository {
  _FakeRepository({this.getError});

  AppException? getError;

  int getCalls = 0;
  int updateCalls = 0;

  NotificationPreferenceUpdate? lastUpdate;

  BackendNotificationPreferences current = BackendNotificationPreferences(
    id: 4,
    userId: 9,
    emailEnabled: true,
    pushEnabled: true,
    soundEnabled: true,
    priceAlerts: true,
    arbitrageAlerts: true,
    aiAlerts: true,
    newsAlerts: false,
    updatedAt: DateTime.utc(2026, 8, 3),
  );

  @override
  Future<BackendNotificationPreferences> getPreferences() async {
    getCalls += 1;

    final error = getError;

    if (error != null) {
      throw error;
    }

    return current;
  }

  @override
  Future<BackendNotificationPreferences> updatePreferences(
    NotificationPreferenceUpdate update,
  ) async {
    updateCalls += 1;
    lastUpdate = update;

    current = current.copyWith(
      emailEnabled: update.emailEnabled,
      pushEnabled: update.pushEnabled,
      soundEnabled: update.soundEnabled,
      priceAlerts: update.priceAlerts,
      arbitrageAlerts: update.arbitrageAlerts,
      aiAlerts: update.aiAlerts,
      newsAlerts: update.newsAlerts,
      updatedAt: DateTime.utc(2026, 8, 3, 1),
    );

    return current;
  }
}
