import 'package:google_sign_in/google_sign_in.dart';
import 'package:flutter/foundation.dart';

import '../../../../core/api_client.dart';

class GoogleSignInDataSource {
  GoogleSignInDataSource(this._apiClient);

  final ApiClient _apiClient;
  final GoogleSignIn _google = GoogleSignIn.instance;
  Future<void>? _initialization;

  Future<void> _initialize() async {
    final active = _initialization;
    if (active != null) {
      await active;
      return;
    }
    final operation = _initializeFromBackend();
    _initialization = operation;
    try {
      await operation;
    } catch (_) {
      // A failed request or OAuth configuration must not poison retries.
      if (identical(_initialization, operation)) {
        _initialization = null;
      }
      rethrow;
    }
  }

  Future<void> _initializeFromBackend() async {
    final config = await _apiClient.getPublicObject('/system/public-config');
    final clientId = config['google_client_id']?.toString().trim() ?? '';
    if (clientId.isEmpty) {
      throw const ApiException(
        'Backend chưa cấu hình GOOGLE_CLIENT_ID cho đăng nhập Google.',
        503,
      );
    }
    await _google.initialize(
      clientId: kIsWeb ? clientId : null,
      serverClientId: kIsWeb ? null : clientId,
      hostedDomain: 'hvnh.edu.vn',
    );
  }

  Future<void> initialize() => _initialize();

  Future<String> authenticate() async {
    try {
      await _initialize();
      if (!_google.supportsAuthenticate()) {
        throw const ApiException(
          'Thiết bị này không hỗ trợ đăng nhập Google native.',
          0,
        );
      }
      final user = await _google.authenticate();
      if (!user.email.toLowerCase().endsWith('@hvnh.edu.vn')) {
        await _google.signOut();
        throw const ApiException(
          'Chỉ chấp nhận tài khoản Google @hvnh.edu.vn.',
          0,
        );
      }
      final idToken = user.authentication.idToken;
      if (idToken == null || idToken.isEmpty) {
        await _google.signOut();
        throw const ApiException(
          'Google không trả về mã xác thực. Vui lòng thử lại.',
          0,
        );
      }
      return idToken;
    } on ApiException {
      rethrow;
    } on GoogleSignInException catch (error) {
      if (kDebugMode) {
        debugPrint('Google Sign-In Android: ${error.code}');
      }
      throw ApiException(_messageFor(error), 0);
    } catch (_) {
      throw const ApiException(
        'Không thể đăng nhập Google. Hãy kiểm tra kết nối và thử lại.',
        0,
      );
    }
  }

  Future<void> reset() async {
    try {
      await _initialize();
      await _google.signOut();
    } catch (_) {
      // Việc xóa phiên HVNH không phụ thuộc trạng thái Google Play Services.
    }
  }

  String _messageFor(GoogleSignInException error) => switch (error.code) {
    GoogleSignInExceptionCode.canceled =>
      'Đã đóng cửa sổ Google. Nếu bạn không chủ động hủy, hãy kiểm tra OAuth Android (package và SHA-1).',
    GoogleSignInExceptionCode.clientConfigurationError =>
      'OAuth Android chưa khớp package, SHA-1 hoặc Web Client ID của ứng dụng.',
    GoogleSignInExceptionCode.providerConfigurationError =>
      'Google Play services/Credential Manager chưa sẵn sàng. Hãy dùng máy ảo có Google Play hoặc thử trên điện thoại thật.',
    GoogleSignInExceptionCode.uiUnavailable =>
      'Không thể mở cửa sổ chọn tài khoản Google.',
    _ => 'Đăng nhập Google thất bại. Vui lòng thử lại.',
  };
}
