import 'package:flutter/foundation.dart';

class AppConfig {
  const AppConfig._();

  static const _configuredApiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: '',
  );

  // Android Emulator reaches the development computer through 10.0.2.2,
  // while desktop and web targets use the host loopback directly. A physical
  // phone must still receive the computer LAN address through --dart-define.
  static String get apiBaseUrl {
    if (_configuredApiBaseUrl.isNotEmpty) return _configuredApiBaseUrl;
    if (kIsWeb || defaultTargetPlatform != TargetPlatform.android) {
      return 'http://127.0.0.1:8000/api/v1';
    }
    return 'http://10.0.2.2:8000/api/v1';
  }

}
