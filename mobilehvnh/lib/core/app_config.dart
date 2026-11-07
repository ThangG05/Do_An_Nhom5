import 'package:flutter/foundation.dart';
import 'platform/device_environment.dart';

class AppConfig {
  const AppConfig._();

  static const _configuredApiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: '',
  );

  /// Local development IP for iOS physical devices.
  static const _iosPhysicalLanHost = '192.168.88.116:8000';

  // Android Emulator reaches the development computer through 10.0.2.2,
  // while desktop and web targets use the host loopback directly.
  // Physical iOS devices reach the computer via LAN IP (192.168.88.116).
  static String get apiBaseUrl {
    if (_configuredApiBaseUrl.isNotEmpty) return _configuredApiBaseUrl;
    if (kReleaseMode) return 'https://hvnhhub.id.vn/api/v1';

    // Web runs inside browser on the host machine
    if (kIsWeb) {
      return 'http://127.0.0.1:8000/api/v1';
    }

    // Android emulator
    if (defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:8000/api/v1';
    }

    // iOS physical device (iPhone/iPad)
    if (defaultTargetPlatform == TargetPlatform.iOS && isIosPhysical) {
      return 'http://$_iosPhysicalLanHost/api/v1';
    }

    // iOS Simulator, macOS, Windows, Linux
    return 'http://127.0.0.1:8000/api/v1';
  }

  static const _configuredWebBaseUrl = String.fromEnvironment(
    'WEB_BASE_URL',
    defaultValue: '',
  );

  static const _iosPhysicalLanWebHost = '192.168.88.116:3000';

  static String get webBaseUrl {
    if (_configuredWebBaseUrl.isNotEmpty) return _configuredWebBaseUrl;
    if (kReleaseMode) return 'https://hvnhhub.id.vn';

    if (kIsWeb) {
      return 'http://localhost:3000';
    }

    if (defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:3000';
    }

    if (defaultTargetPlatform == TargetPlatform.iOS && isIosPhysical) {
      return 'http://$_iosPhysicalLanWebHost';
    }

    return 'http://localhost:3000';
  }
}
