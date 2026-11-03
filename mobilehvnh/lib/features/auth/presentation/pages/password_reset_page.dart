import 'dart:async';

import 'package:flutter/material.dart';
import '../../../../core/widgets/app_page_bar.dart';

import '../../../../app/di/app_dependencies.dart';
import '../../../../core/api_client.dart';
import '../../../../core/utils/hvnh_email.dart';
import '../../../../core/widgets/otp_code_input.dart';

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
  Timer? _otpTimer;
  DateTime? _otpExpiresAt;
  DateTime? _resendAvailableAt;
  int _otpSecondsLeft = 0;
  int _resendSecondsLeft = 0;
  int _otpVersion = 0;

  @override
  void dispose() {
    _email.dispose();
    _code.dispose();
    _password.dispose();
    _otpTimer?.cancel();
    super.dispose();
  }

  String _formatDuration(int seconds) =>
      '${seconds ~/ 60}:${(seconds % 60).toString().padLeft(2, '0')}';

  int _remaining(DateTime? deadline, DateTime now) {
    if (deadline == null) return 0;
    final seconds = deadline.difference(now).inSeconds;
    return seconds > 0 ? seconds : 0;
  }

  void _startOtpCountdown() {
    _otpTimer?.cancel();
    final now = DateTime.now();
    _otpExpiresAt = now.add(const Duration(minutes: 5));
    _resendAvailableAt = now.add(const Duration(seconds: 60));
    setState(() {
      _otpSecondsLeft = 300;
      _resendSecondsLeft = 60;
      _otpVersion++;
      _code.clear();
    });
    _otpTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (!mounted) {
        timer.cancel();
        return;
      }
      final current = DateTime.now();
      setState(() {
        _otpSecondsLeft = _remaining(_otpExpiresAt, current);
        _resendSecondsLeft = _remaining(_resendAvailableAt, current);
      });
      if (_otpSecondsLeft == 0 && _resendSecondsLeft == 0) timer.cancel();
    });
  }

  Future<void> _resendCode() async {
    if (_busy || _resendSecondsLeft > 0) return;
    setState(() {
      _busy = true;
      _error = null;
      _message = null;
    });
    try {
      await widget.dependencies.authRepository.requestPasswordReset(
        _email.text.trim().toLowerCase(),
      );
      _startOtpCountdown();
      if (mounted) {
        setState(() => _message = 'Mã OTP mới đã được gửi nếu tài khoản hợp lệ.');
      }
    } on ApiException catch (error) {
      if (mounted) setState(() => _error = error.message);
    } catch (_) {
      if (mounted) setState(() => _error = 'Không thể gửi lại mã OTP.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _requestCode() async {
    final email = _email.text.trim().toLowerCase();
    if (!isValidHvnhEmail(email)) {
      setState(
        () => _error = 'Nhập đầy đủ email HVNH, ví dụ 26A4041111@hvnh.edu.vn.',
      );
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await widget.dependencies.authRepository.requestPasswordReset(email);
      if (mounted) {
        _startOtpCountdown();
        setState(() {
          _sent = true;
          _message = 'Nếu tài khoản hợp lệ, mã OTP đã được gửi tới email.';
        });
      }
    } on ApiException catch (error) {
      if (mounted) setState(() => _error = error.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _reset() async {
    if (_otpSecondsLeft <= 0) {
      setState(() => _error = 'Mã OTP đã hết hạn. Hãy gửi lại mã mới.');
      return;
    }
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
                  Row(
                    children: [
                      const Icon(Icons.timer_outlined, size: 16),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          _otpSecondsLeft > 0
                              ? 'Mã có hiệu lực ${_formatDuration(_otpSecondsLeft)}'
                              : 'Mã OTP đã hết hạn',
                          style: TextStyle(
                            color: _otpSecondsLeft > 0 ? null : Colors.red,
                            fontWeight: FontWeight.w700,
                            fontSize: 12,
                          ),
                        ),
                      ),
                      TextButton(
                        onPressed: _busy || _resendSecondsLeft > 0 ? null : _resendCode,
                        child: Text(_resendSecondsLeft > 0
                            ? 'Gửi lại ${_formatDuration(_resendSecondsLeft)}'
                            : 'Gửi lại mã'),
                      ),
                    ],
                  ),
                  OtpCodeInput(
                    key: ValueKey('password-reset-otp-$_otpVersion'),
                    autofocus: true,
                    onChanged: (value) => _code.text = value,
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
