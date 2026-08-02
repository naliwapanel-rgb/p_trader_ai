class BackendNotificationPreferences {
  const BackendNotificationPreferences({
    required this.id,
    required this.userId,
    required this.emailEnabled,
    required this.pushEnabled,
    required this.soundEnabled,
    required this.priceAlerts,
    required this.arbitrageAlerts,
    required this.aiAlerts,
    required this.newsAlerts,
    required this.updatedAt,
  });

  final int id;
  final int userId;
  final bool emailEnabled;
  final bool pushEnabled;
  final bool soundEnabled;
  final bool priceAlerts;
  final bool arbitrageAlerts;
  final bool aiAlerts;
  final bool newsAlerts;
  final DateTime updatedAt;

  factory BackendNotificationPreferences.fromJson(Map<String, dynamic> json) {
    return BackendNotificationPreferences(
      id: _readPositiveInt(json, 'id'),
      userId: _readPositiveInt(json, 'user_id'),
      emailEnabled: _readBool(json, 'email_enabled'),
      pushEnabled: _readBool(json, 'push_enabled'),
      soundEnabled: _readBool(json, 'sound_enabled'),
      priceAlerts: _readBool(json, 'price_alerts'),
      arbitrageAlerts: _readBool(json, 'arbitrage_alerts'),
      aiAlerts: _readBool(json, 'ai_alerts'),
      newsAlerts: _readBool(json, 'news_alerts'),
      updatedAt: _readDateTime(json, 'updated_at'),
    );
  }

  BackendNotificationPreferences copyWith({
    int? id,
    int? userId,
    bool? emailEnabled,
    bool? pushEnabled,
    bool? soundEnabled,
    bool? priceAlerts,
    bool? arbitrageAlerts,
    bool? aiAlerts,
    bool? newsAlerts,
    DateTime? updatedAt,
  }) {
    return BackendNotificationPreferences(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      emailEnabled: emailEnabled ?? this.emailEnabled,
      pushEnabled: pushEnabled ?? this.pushEnabled,
      soundEnabled: soundEnabled ?? this.soundEnabled,
      priceAlerts: priceAlerts ?? this.priceAlerts,
      arbitrageAlerts: arbitrageAlerts ?? this.arbitrageAlerts,
      aiAlerts: aiAlerts ?? this.aiAlerts,
      newsAlerts: newsAlerts ?? this.newsAlerts,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  static int _readPositiveInt(Map<String, dynamic> json, String key) {
    final value = json[key];

    if (value is! num || value.toInt() != value || value.toInt() <= 0) {
      throw FormatException(
        'The notification-preference field "$key" is invalid.',
      );
    }

    return value.toInt();
  }

  static bool _readBool(Map<String, dynamic> json, String key) {
    final value = json[key];

    if (value is! bool) {
      throw FormatException(
        'The notification-preference field "$key" is invalid.',
      );
    }

    return value;
  }

  static DateTime _readDateTime(Map<String, dynamic> json, String key) {
    final value = json[key];

    if (value is DateTime) {
      return value.toUtc();
    }

    if (value is! String) {
      throw FormatException(
        'The notification-preference field "$key" is invalid.',
      );
    }

    final parsed = DateTime.tryParse(value);

    if (parsed == null) {
      throw FormatException(
        'The notification-preference field "$key" is invalid.',
      );
    }

    return parsed.toUtc();
  }
}

class NotificationPreferenceUpdate {
  const NotificationPreferenceUpdate({
    this.emailEnabled,
    this.pushEnabled,
    this.soundEnabled,
    this.priceAlerts,
    this.arbitrageAlerts,
    this.aiAlerts,
    this.newsAlerts,
  });

  final bool? emailEnabled;
  final bool? pushEnabled;
  final bool? soundEnabled;
  final bool? priceAlerts;
  final bool? arbitrageAlerts;
  final bool? aiAlerts;
  final bool? newsAlerts;

  bool get hasChanges {
    return emailEnabled != null ||
        pushEnabled != null ||
        soundEnabled != null ||
        priceAlerts != null ||
        arbitrageAlerts != null ||
        aiAlerts != null ||
        newsAlerts != null;
  }

  Map<String, Object> toJson() {
    final data = <String, Object>{};

    if (emailEnabled != null) {
      data['email_enabled'] = emailEnabled!;
    }

    if (pushEnabled != null) {
      data['push_enabled'] = pushEnabled!;
    }

    if (soundEnabled != null) {
      data['sound_enabled'] = soundEnabled!;
    }

    if (priceAlerts != null) {
      data['price_alerts'] = priceAlerts!;
    }

    if (arbitrageAlerts != null) {
      data['arbitrage_alerts'] = arbitrageAlerts!;
    }

    if (aiAlerts != null) {
      data['ai_alerts'] = aiAlerts!;
    }

    if (newsAlerts != null) {
      data['news_alerts'] = newsAlerts!;
    }

    return data;
  }
}
