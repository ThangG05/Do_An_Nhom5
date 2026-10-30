import 'package:flutter/foundation.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';

import '../../../../app/di/app_dependencies.dart';
import '../../../../core/api_client.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/app_brand_mark.dart';
import '../../../../core/widgets/app_page_bar.dart';
import '../../../../core/widgets/premium_hero_card.dart';
import 'password_reset_page.dart';
import 'registration_page.dart';
import '../widgets/google_web_sign_in_button.dart';

class LoginPage extends StatefulWidget {
  const LoginPage({
    super.key,
    required this.dependencies,
    required this.onSignedIn,
  });

  final AppDependencies dependencies;
  final Future<void> Function() onSignedIn;

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _formKey = GlobalKey<FormState>();
  final _email = TextEditingController();
  final _password = TextEditingController();
  bool _busy = false;
  bool _obscure = true;
  String? _error;

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _signIn() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await widget.dependencies.signIn(
        email: _email.text.trim(),
        password: _password.text,
      );
      await widget.onSignedIn();
    } on ApiException catch (error) {
      if (mounted) setState(() => _error = error.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _signInWithGoogle() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await widget.dependencies.authRepository.signInWithGoogle();
      await widget.onSignedIn();
    } on ApiException catch (error) {
      if (mounted) setState(() => _error = error.message);
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'Không thể đăng nhập Google. Hãy thử lại.');
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _completeWebGoogle(String credential) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await widget.dependencies.authRepository.signInWithGoogleCredential(
        credential,
      );
      await widget.onSignedIn();
    } on ApiException catch (error) {
      if (mounted) setState(() => _error = error.message);
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'Không thể đăng nhập Google. Hãy thử lại.');
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  void _openRegistration() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => RegistrationPage(
          dependencies: widget.dependencies,
          onRegistered: widget.onSignedIn,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: const AppPageBar(title: 'Đăng nhập'),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(18, 20, 18, 28),
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 460),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  PremiumHeroCard(
                    padding: const EdgeInsets.fromLTRB(24, 26, 24, 28),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            const AppBrandMark(size: 42),
                            const SizedBox(width: 11),
                            Text(
                              'HVNH Hub',
                              style: theme.textTheme.titleLarge?.copyWith(
                                color: Colors.white,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 28),
                        const Text(
                          'CỘNG ĐỒNG SINH VIÊN',
                          style: TextStyle(
                            color: AppTheme.gold,
                            fontSize: 11,
                            fontWeight: FontWeight.w800,
                            letterSpacing: 1.6,
                          ),
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          'Kết nối, chia sẻ\nvà khám phá.',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 28,
                            fontWeight: FontWeight.w800,
                            height: 1.2,
                          ),
                        ),
                        const SizedBox(height: 10),
                        const Text(
                          'Bài viết, hội nhóm và trợ lý AI dành riêng cho sinh viên Học viện Ngân hàng.',
                          style: TextStyle(
                            color: Color(0xffc9deec),
                            height: 1.5,
                            fontSize: 13,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  Container(
                    padding: const EdgeInsets.fromLTRB(22, 25, 22, 23),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(27),
                      border: Border.all(color: AppTheme.hairline),
                      boxShadow: const [
                        BoxShadow(
                          color: Color(0x0c0a2b4b),
                          blurRadius: 20,
                          offset: Offset(0, 8),
                        ),
                      ],
                    ),
                    child: Form(
                      key: _formKey,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Text(
                            'Chào mừng trở lại',
                            style: theme.textTheme.headlineSmall?.copyWith(
                              fontWeight: FontWeight.w800,
                              color: AppTheme.ink,
                            ),
                          ),
                          const SizedBox(height: 6),
                          const Text(
                            'Đăng nhập bằng email HVNH để tiếp tục.',
                            style: TextStyle(color: AppTheme.muted),
                          ),
                          const SizedBox(height: 25),
                          TextFormField(
                            controller: _email,
                            keyboardType: TextInputType.emailAddress,
                            textInputAction: TextInputAction.next,
                            autofillHints: const [AutofillHints.email],
                            decoration: const InputDecoration(
                              labelText: 'Email HVNH',
                              prefixIcon: Icon(CupertinoIcons.mail, size: 20),
                            ),
                            validator: (value) =>
                                value != null &&
                                    value.trim().toLowerCase().endsWith(
                                      '@hvnh.edu.vn',
                                    )
                                ? null
                                : 'Vui lòng dùng email @hvnh.edu.vn',
                          ),
                          const SizedBox(height: 14),
                          TextFormField(
                            controller: _password,
                            obscureText: _obscure,
                            textInputAction: TextInputAction.done,
                            autofillHints: const [AutofillHints.password],
                            onFieldSubmitted: (_) {
                              if (!_busy) _signIn();
                            },
                            decoration: InputDecoration(
                              labelText: 'Mật khẩu',
                              prefixIcon: const Icon(
                                CupertinoIcons.lock,
                                size: 20,
                              ),
                              suffixIcon: IconButton(
                                onPressed: () =>
                                    setState(() => _obscure = !_obscure),
                                icon: Icon(
                                  _obscure
                                      ? CupertinoIcons.eye
                                      : CupertinoIcons.eye_slash,
                                ),
                              ),
                            ),
                            validator: (value) =>
                                value != null && value.length >= 8
                                ? null
                                : 'Mật khẩu tối thiểu 8 ký tự',
                          ),
                          Align(
                            alignment: Alignment.centerRight,
                            child: TextButton(
                              onPressed: _busy
                                  ? null
                                  : () => Navigator.of(context).push(
                                      MaterialPageRoute(
                                        builder: (_) => PasswordResetPage(
                                          dependencies: widget.dependencies,
                                        ),
                                      ),
                                    ),
                              child: const Text('Quên mật khẩu?'),
                            ),
                          ),
                          if (_error != null)
                            Padding(
                              padding: const EdgeInsets.only(top: 14),
                              child: Text(
                                _error!,
                                style: const TextStyle(color: Colors.red),
                              ),
                            ),
                          const SizedBox(height: 12),
                          FilledButton(
                            onPressed: _busy ? null : _signIn,
                            child: Padding(
                              padding: const EdgeInsets.all(13),
                              child: Text(
                                _busy ? 'Đang đăng nhập...' : 'Đăng nhập',
                              ),
                            ),
                          ),
                          const Padding(
                            padding: EdgeInsets.symmetric(vertical: 16),
                            child: Row(
                              children: [
                                Expanded(child: Divider()),
                                Padding(
                                  padding: EdgeInsets.symmetric(horizontal: 12),
                                  child: Text(
                                    'HOẶC',
                                    style: TextStyle(
                                      color: Color(0xff71839a),
                                      fontSize: 11,
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                ),
                                Expanded(child: Divider()),
                              ],
                            ),
                          ),
                          if (kIsWeb)
                            AbsorbPointer(
                              absorbing: _busy,
                              child: GoogleWebSignInButton(
                                repository: widget.dependencies.authRepository,
                                onCredential: _completeWebGoogle,
                                onError: (message) {
                                  if (mounted) setState(() => _error = message);
                                },
                              ),
                            )
                          else
                            OutlinedButton.icon(
                              onPressed: _busy ? null : _signInWithGoogle,
                              icon: Container(
                                width: 24,
                                height: 24,
                                alignment: Alignment.center,
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  border: Border.all(
                                    color: const Color(0xffd6dee8),
                                  ),
                                  shape: BoxShape.circle,
                                ),
                                child: const Text(
                                  'G',
                                  style: TextStyle(
                                    color: Color(0xff4285f4),
                                    fontWeight: FontWeight.w900,
                                  ),
                                ),
                              ),
                              label: const Padding(
                                padding: EdgeInsets.symmetric(vertical: 13),
                                child: Text('Tiếp tục với Google'),
                              ),
                            ),
                          const SizedBox(height: 12),
                          OutlinedButton.icon(
                            onPressed: _busy ? null : _openRegistration,
                            icon: const Icon(Icons.person_add_alt_1),
                            label: const Text('Đăng ký bằng email HVNH'),
                          ),
                          const SizedBox(height: 8),
                          const Text(
                            'Chỉ email @hvnh.edu.vn được chấp nhận.',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              fontSize: 11,
                              color: AppTheme.muted,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'Một tài khoản cho web và ứng dụng di động.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: AppTheme.muted, fontSize: 11),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
