import 'package:flutter/material.dart';
import '../../../../core/widgets/app_page_bar.dart';

import '../../../../app/di/app_dependencies.dart';
import '../../../../core/api_client.dart';

class PasswordResetPage extends StatefulWidget {
  const PasswordResetPage({super.key, required this.dependencies});

  final AppDependencies dependencies;

  @override
  State<PasswordResetPage> createState() => _PasswordResetPageState();
}

class _PasswordResetPageState extends State<PasswordResetPage> {
  final _email = TextEditingController();
  final _code = TextEditingController();
  final _password = TextEditingController();
  bool _sent = false;
  bool _busy = false;
  bool _obscure = true;
  String? _message;
  String? _error;

  @override
  void dispose() {
    _email.dispose();
    _code.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _requestCode() async {
    final email = _email.text.trim().toLowerCase();
    if (!email.endsWith('@hvnh.edu.vn')) {
      setState(() => _error = 'Vui lòng dùng email @hvnh.edu.vn.');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await widget.dependencies.authRepository.requestPasswordReset(email);
      if (mounted) {
        setState(() {
          _sent = true;
          _message = 'Mã khôi phục đã được gửi tới email của bạn.';
        });
      }
    } on ApiException catch (error) {
      if (mounted) setState(() => _error = error.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _reset() async {
    if (_code.text.trim().length != 4 || _password.text.length < 8) {
      setState(
        () => _error = 'Nhập mã gồm 4 chữ số và mật khẩu tối thiểu 8 ký tự.',
      );
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await widget.dependencies.authRepository.resetPassword(
        email: _email.text.trim().toLowerCase(),
        code: _code.text.trim(),
        newPassword: _password.text,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Đặt lại mật khẩu thành công. Hãy đăng nhập lại.'),
        ),
      );
      Navigator.of(context).pop();
    } on ApiException catch (error) {
      if (mounted) setState(() => _error = error.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: const AppPageBar(title: 'Khôi phục mật khẩu'),
    body: SafeArea(
      child: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 420),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  _sent ? 'Nhập mã xác thực' : 'Quên mật khẩu?',
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  _sent
                      ? 'Nhập mã 4 chữ số và chọn mật khẩu mới cho tài khoản HVNH Hub.'
                      : 'Chúng tôi sẽ gửi mã xác thực đến email HVNH của bạn.',
                ),
                const SizedBox(height: 24),
                TextField(
                  controller: _email,
                  enabled: !_sent && !_busy,
                  keyboardType: TextInputType.emailAddress,
                  decoration: const InputDecoration(
                    labelText: 'Email @hvnh.edu.vn',
                    prefixIcon: Icon(Icons.mail_outline),
                  ),
                ),
                if (_sent) ...[
                  const SizedBox(height: 12),
                  TextField(
                    controller: _code,
                    keyboardType: TextInputType.number,
                    maxLength: 4,
                    autofocus: true,
                    decoration: const InputDecoration(
                      labelText: 'Mã xác thực',
                      prefixIcon: Icon(Icons.password_outlined),
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _password,
                    obscureText: _obscure,
                    decoration: InputDecoration(
                      labelText: 'Mật khẩu mới',
                      prefixIcon: const Icon(Icons.lock_outline),
                      suffixIcon: IconButton(
                        onPressed: () => setState(() => _obscure = !_obscure),
                        icon: Icon(
                          _obscure
                              ? Icons.visibility_outlined
                              : Icons.visibility_off_outlined,
                        ),
                      ),
                    ),
                  ),
                ],
                if (_message != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 12),
                    child: Text(
                      _message!,
                      style: const TextStyle(color: Color(0xff187347)),
                    ),
                  ),
                if (_error != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 12),
                    child: Text(
                      _error!,
                      style: const TextStyle(color: Colors.red),
                    ),
                  ),
                const SizedBox(height: 20),
                FilledButton(
                  onPressed: _busy ? null : (_sent ? _reset : _requestCode),
                  child: Padding(
                    padding: const EdgeInsets.all(13),
                    child: Text(
                      _busy
                          ? 'Đang xử lý...'
                          : _sent
                          ? 'Đặt lại mật khẩu'
                          : 'Gửi mã xác thực',
                    ),
                  ),
                ),
                if (_sent)
                  TextButton(
                    onPressed: _busy
                        ? null
                        : () => setState(() {
                            _sent = false;
                            _message = null;
                            _error = null;
                          }),
                    child: const Text('Dùng email khác'),
                  ),
              ],
            ),
          ),
        ),
      ),
    ),
  );
}
