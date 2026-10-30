import 'dart:async';

import 'package:flutter/material.dart';
import 'package:google_sign_in/google_sign_in.dart';

import '../../domain/repositories/auth_repository.dart';
import 'google_button_stub.dart'
    if (dart.library.js_interop) 'google_button_web.dart'
    as platform_button;

/// GIS requires its own button on Web; a custom button cannot call authenticate().
class GoogleWebSignInButton extends StatefulWidget {
  const GoogleWebSignInButton({
    super.key,
    required this.repository,
    required this.onCredential,
    required this.onError,
  });

  final AuthRepository repository;
  final Future<void> Function(String credential) onCredential;
  final ValueChanged<String> onError;

  @override
  State<GoogleWebSignInButton> createState() => _GoogleWebSignInButtonState();
}

class _GoogleWebSignInButtonState extends State<GoogleWebSignInButton> {
  StreamSubscription<GoogleSignInAuthenticationEvent>? _subscription;
  bool _ready = false;
  bool _handling = false;
  bool _failed = false;

  @override
  void initState() {
    super.initState();
    _subscription = GoogleSignIn.instance.authenticationEvents.listen(
      _onEvent,
      onError: (Object _) {
        if (mounted) widget.onError('Google không thể xác thực. Hãy thử lại.');
      },
    );
    unawaited(_prepare());
  }

  Future<void> _prepare() async {
    try {
      await widget.repository.initializeGoogleSignIn();
      if (mounted) setState(() => _ready = true);
    } catch (_) {
      if (mounted) {
        setState(() => _failed = true);
        widget.onError('Không thể khởi tạo Google Sign-In. Hãy tải lại trang.');
      }
    }
  }

  void _onEvent(GoogleSignInAuthenticationEvent event) {
    if (event is GoogleSignInAuthenticationEventSignIn) {
      unawaited(_complete(event.user));
    }
  }

  Future<void> _complete(GoogleSignInAccount user) async {
    if (_handling || !mounted) return;
    _handling = true;
    try {
      if (!user.email.toLowerCase().endsWith('@hvnh.edu.vn')) {
        widget.onError('Chỉ chấp nhận tài khoản Google @hvnh.edu.vn.');
        await GoogleSignIn.instance.signOut();
        return;
      }
      final token = user.authentication.idToken;
      if (token == null || token.isEmpty) {
        widget.onError('Google không trả về mã xác thực. Hãy thử lại.');
        await GoogleSignIn.instance.signOut();
        return;
      }
      await widget.onCredential(token);
    } catch (_) {
      if (mounted) widget.onError('Không thể hoàn tất đăng nhập Google.');
    } finally {
      _handling = false;
    }
  }

  @override
  void dispose() {
    _subscription?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_failed) {
      return const Text(
        'Nút Google chưa tải được. Hãy tải lại trang.',
        textAlign: TextAlign.center,
      );
    }
    if (!_ready) {
      return const SizedBox(
        height: 48,
        child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
      );
    }
    return LayoutBuilder(
      builder: (_, constraints) => SizedBox(
        height: 48,
        child: Center(
          child: platform_button.renderGoogleButton(constraints.maxWidth),
        ),
      ),
    );
  }
}
