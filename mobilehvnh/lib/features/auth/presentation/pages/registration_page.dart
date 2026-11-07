import 'dart:async';

import 'package:flutter/material.dart';

import '../../../../app/di/app_dependencies.dart';
import '../../../../core/api_client.dart';
import '../../../../core/utils/hvnh_email.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/otp_code_input.dart';

class RegistrationPage extends StatefulWidget {
  const RegistrationPage({
    super.key,
    required this.dependencies,
    required this.onRegistered,
  });

  final AppDependencies dependencies;
  final Future<void> Function() onRegistered;

  @override
  State<RegistrationPage> createState() => _RegistrationPageState();
}

class _RegistrationPageState extends State<RegistrationPage> {
  final _email = TextEditingController();
  final _code = TextEditingController();
  final _name = TextEditingController();
  final _password = TextEditingController();
  int _step = 0;
  bool _busy = false;
  bool _obscure = true;
  String? _registrationToken;
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
    _name.dispose();
    _password.dispose();
    _otpTimer?.cancel();
    super.dispose();
  }

  String _formatDuration(int seconds) =>
      '${seconds ~/ 60}:${(seconds % 60).toString().padLeft(2, '0')}';

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

  int _remaining(DateTime? deadline, DateTime now) {
    if (deadline == null) return 0;
    final seconds = deadline.difference(now).inSeconds;
    return seconds > 0 ? seconds : 0;
  }

  Future<void> _resendCode() async {
    if (_busy || _resendSecondsLeft > 0) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await widget.dependencies.authRepository
          .requestRegistrationCode(_email.text.trim().toLowerCase());
      _startOtpCountdown();
    } on ApiException catch (error) {
      if (mounted) setState(() => _error = error.message);
    } catch (_) {
      if (mounted) setState(() => _error = 'Không thể gửi lại mã OTP.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _continue() async {
    final email = _email.text.trim().toLowerCase();
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      if (_step == 0) {
        if (!isValidHvnhEmail(email)) {
          throw const ApiException(
            'Nhập đầy đủ email HVNH, ví dụ 26A4041111@hvnh.edu.vn.',
            400,
          );
        }
        await widget.dependencies.authRepository.requestRegistrationCode(email);
        _startOtpCountdown();
        setState(() => _step = 1);
      } else if (_step == 1) {
        if (_otpSecondsLeft <= 0) {
          throw const ApiException('Mã xác thực đã hết hạn. Hãy gửi lại mã mới.', 400);
        }
        final data = await widget.dependencies.authRepository
            .verifyRegistrationCode(email, _code.text.trim());
        _registrationToken = data['registration_token']?.toString();
        _name.text = data['full_name']?.toString() ?? '';
        if (_registrationToken == null || _registrationToken!.isEmpty) {
          throw const ApiException(
            'Mã xác thực không hợp lệ hoặc đã hết hạn.',
            400,
          );
        }
        setState(() => _step = 2);
      } else {
        if (_name.text.trim().length < 2 || _password.text.length < 8) {
          throw const ApiException(
            'Hãy nhập họ tên và mật khẩu tối thiểu 8 ký tự.',
            400,
          );
        }
        await widget.dependencies.authRepository.completeRegistration(
          registrationToken: _registrationToken!,
          fullName: _name.text.trim(),
          password: _password.text,
        );
        await widget.onRegistered();
        if (mounted && Navigator.of(context).canPop()) {
          Navigator.of(context).pop();
        }
      }
    } on ApiException catch (error) {
      if (mounted) setState(() => _error = error.message);
    } catch (_) {
      if (mounted) {
        setState(
          () => _error = 'Không thể hoàn tất đăng ký. Vui lòng thử lại.',
        );
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final title = ['Email HVNH', 'Xác thực OTP', 'Hoàn tất đăng ký'][_step];
    final description = _step == 0
        ? 'Nhập email sinh viên để nhận mã xác thực.'
        : _step == 1
        ? 'Mã gồm 4 chữ số đã gửi tới ${_email.text.trim()}.'
        : 'Kiểm tra và hoàn tất thông tin tài khoản của bạn.';
    return Scaffold(
      backgroundColor: AppTheme.canvas,
      body: SafeArea(
        child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 28),
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 480),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Row(
                      children: [
                        IconButton.filledTonal(
                          tooltip: _step > 0 ? 'Bước trước' : 'Quay lại',
                          onPressed: _busy
                              ? null
                              : () {
                                  if (_step > 0) {
                                    setState(() {
                                      _step--;
                                      _error = null;
                                    });
                                  } else {
                                    Navigator.of(context).maybePop();
                                  }
                                },
                          icon: const Icon(Icons.arrow_back_rounded),
                        ),
                        const SizedBox(width: 12),
                        const Expanded(
                          child: Text(
                            'Tạo tài khoản',
                            style: TextStyle(
                              color: AppTheme.ink,
                              fontSize: 19,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                        ),
                        Text(
                          '${_step + 1}/3',
                          style: const TextStyle(
                            color: AppTheme.muted,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 26),
                    Row(
                      children: [
                        Container(
                          width: 48,
                          height: 48,
                          padding: const EdgeInsets.all(5),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(14),
                            border: Border.all(color: const Color(0xffe0eaf1)),
                            boxShadow: const [
                              BoxShadow(
                                color: Color(0x10122f4d),
                                blurRadius: 12,
                                offset: Offset(0, 4),
                              ),
                            ],
                          ),
                          child: Image.asset(
                            'assets/brand/hvnh-official-logo.png',
                            fit: BoxFit.contain,
                            semanticLabel: 'Logo chính thức Học viện Ngân hàng',
                          ),
                        ),
                        const SizedBox(width: 12),
                        const Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'HVNH Hub',
                              style: TextStyle(
                                color: AppTheme.ink,
                                fontSize: 18,
                                fontWeight: FontWeight.w900,
                              ),
                            ),
                            SizedBox(height: 3),
                            Text(
                              'KHÔNG GIAN KẾT NỐI SINH VIÊN',
                              style: TextStyle(
                                color: AppTheme.muted,
                                fontSize: 9,
                                letterSpacing: 1,
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                    const SizedBox(height: 25),
                    _RegistrationProgress(step: _step),
                    const SizedBox(height: 17),
                    Container(
                      padding: const EdgeInsets.fromLTRB(22, 24, 22, 22),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(26),
                        border: Border.all(color: const Color(0xffdfe8ef)),
                        boxShadow: const [
                          BoxShadow(
                            color: Color(0x10122f4d),
                            blurRadius: 28,
                            offset: Offset(0, 12),
                          ),
                        ],
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Text(
                            ['THAM GIA HVNH HUB', 'XÁC MINH EMAIL', 'THÔNG TIN CỦA BẠN'][_step],
                            style: const TextStyle(
                              color: AppTheme.blue,
                              fontSize: 10,
                              letterSpacing: 1.4,
                              fontWeight: FontWeight.w900,
                            ),
                          ),
                          const SizedBox(height: 8),
                          AnimatedSwitcher(
                            duration: const Duration(milliseconds: 220),
                            child: Text(
                              title,
                              key: ValueKey(_step),
                              style: const TextStyle(
                                color: AppTheme.ink,
                                fontSize: 27,
                                height: 1.15,
                                letterSpacing: -.7,
                                fontWeight: FontWeight.w900,
                              ),
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            description,
                            style: const TextStyle(
                              color: AppTheme.muted,
                              height: 1.55,
                              fontSize: 13,
                            ),
                          ),
                          const SizedBox(height: 25),
                          AnimatedSize(
                            duration: const Duration(milliseconds: 220),
                            curve: Curves.easeOutCubic,
                            child: Column(
                              key: ValueKey('fields-$_step'),
                              crossAxisAlignment: CrossAxisAlignment.stretch,
                              children: [
                                if (_step == 0)
                                  TextField(
                                    controller: _email,
                                    keyboardType: TextInputType.emailAddress,
                                    textInputAction: TextInputAction.done,
                                    autocorrect: false,
                                    decoration: const InputDecoration(
                                      labelText: 'Email sinh viên',
                                      hintText: 'mssv@hvnh.edu.vn',
                                      prefixIcon: Icon(Icons.alternate_email),
                                      suffixIcon: Icon(Icons.verified_user_outlined),
                                    ),
                                  ),
                                if (_step == 1)
                                  Column(
                                    crossAxisAlignment: CrossAxisAlignment.stretch,
                                    children: [
                                      Row(
                                        children: [
                                          const Icon(Icons.timer_outlined, size: 16, color: AppTheme.blue),
                                          const SizedBox(width: 6),
                                          Expanded(
                                            child: Text(
                                              _otpSecondsLeft > 0
                                                  ? 'Mã có hiệu lực ${_formatDuration(_otpSecondsLeft)}'
                                                  : 'Mã OTP đã hết hạn',
                                              style: TextStyle(
                                                color: _otpSecondsLeft > 0 ? AppTheme.muted : const Color(0xffbd3434),
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
                                      const SizedBox(height: 6),
                                      OtpCodeInput(
                                        key: ValueKey('registration-otp-$_otpVersion'),
                                        autofocus: true,
                                        onChanged: (value) => _code.text = value,
                                      ),
                                    ],
                                  ),
                                if (_step == 2) ...[
                                  TextField(
                                    controller: _name,
                                    textCapitalization: TextCapitalization.words,
                                    textInputAction: TextInputAction.next,
                                    decoration: const InputDecoration(
                                      labelText: 'Họ và tên',
                                      hintText: 'Tên hiển thị của bạn',
                                      prefixIcon: Icon(Icons.person_outline),
                                    ),
                                  ),
                                  const SizedBox(height: 14),
                                  TextField(
                                    controller: _password,
                                    obscureText: _obscure,
                                    textInputAction: TextInputAction.done,
                                    decoration: InputDecoration(
                                      labelText: 'Mật khẩu',
                                      hintText: 'Tối thiểu 8 ký tự',
                                      prefixIcon: const Icon(Icons.lock_outline),
                                      suffixIcon: IconButton(
                                        tooltip: _obscure ? 'Hiện mật khẩu' : 'Ẩn mật khẩu',
                                        onPressed: () => setState(() => _obscure = !_obscure),
                                        icon: Icon(_obscure ? Icons.visibility_outlined : Icons.visibility_off_outlined),
                                      ),
                                    ),
                                  ),
                                  const SizedBox(height: 8),
                                  const Text(
                                    'Hãy dùng mật khẩu riêng, khó đoán để bảo vệ tài khoản.',
                                    style: TextStyle(color: AppTheme.muted, fontSize: 11, height: 1.45),
                                  ),
                                ],
                              ],
                            ),
                          ),
                          if (_error != null) ...[
                            const SizedBox(height: 14),
                            Container(
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: const Color(0xfffff1f1),
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(color: const Color(0xffffd1d1)),
                              ),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Icon(Icons.error_outline, color: Color(0xffbd3434), size: 18),
                                  const SizedBox(width: 8),
                                  Expanded(child: Text(_error!, style: const TextStyle(color: Color(0xffa52e35), fontSize: 12, height: 1.4))),
                                ],
                              ),
                            ),
                          ],
                          const SizedBox(height: 22),
                          SizedBox(
                            height: 52,
                            child: FilledButton.icon(
                              onPressed: _busy ? null : _continue,
                              style: FilledButton.styleFrom(
                                backgroundColor: AppTheme.navy,
                                foregroundColor: Colors.white,
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                              ),
                              icon: _busy
                                  ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                                  : Icon(_step == 2 ? Icons.person_add_alt_1 : Icons.arrow_forward_rounded, size: 19),
                              label: Text(
                                _busy
                                    ? 'Đang xử lý...'
                                    : _step == 0
                                    ? 'Gửi mã xác thực'
                                    : _step == 1
                                    ? 'Xác nhận email'
                                    : 'Tạo tài khoản',
                                style: const TextStyle(fontWeight: FontWeight.w800),
                              ),
                            ),
                          ),
                          if (_step == 1)
                            Padding(
                              padding: const EdgeInsets.only(top: 12),
                              child: TextButton(
                                onPressed: _busy ? null : () => setState(() { _step = 0; _error = null; }),
                                child: const Text('Gửi mã tới email khác'),
                              ),
                            ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 18),
                    const Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.lock_outline, color: AppTheme.muted, size: 14),
                        SizedBox(width: 6),
                        Text(
                          'Chỉ sử dụng email sinh viên @hvnh.edu.vn',
                          style: TextStyle(color: AppTheme.muted, fontSize: 11),
                        ),
                      ],
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

class _RegistrationProgress extends StatelessWidget {
  const _RegistrationProgress({required this.step});
  final int step;

  static const _labels = ['Email', 'Xác thực', 'Hồ sơ'];

  @override
  Widget build(BuildContext context) => Row(
    children: [
      for (var index = 0; index < _labels.length; index++) ...[
        Expanded(
          child: Row(
            children: [
              AnimatedContainer(
                duration: const Duration(milliseconds: 220),
                width: 27,
                height: 27,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: index <= step ? AppTheme.navy : Colors.white,
                  border: Border.all(
                    color: index <= step ? AppTheme.navy : const Color(0xffd4e0e9),
                  ),
                ),
                child: index < step
                    ? const Icon(Icons.check_rounded, color: Colors.white, size: 15)
                    : Text(
                        '${index + 1}',
                        style: TextStyle(
                          color: index == step ? Colors.white : AppTheme.muted,
                          fontSize: 11,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
              ),
              const SizedBox(width: 6),
              Flexible(
                child: Text(
                  _labels[index],
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    color: index <= step ? AppTheme.ink : AppTheme.muted,
                    fontSize: 10,
                    fontWeight: index == step ? FontWeight.w800 : FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
        ),
        if (index < _labels.length - 1)
          Container(
            width: 20,
            height: 1,
            margin: const EdgeInsets.symmetric(horizontal: 5),
            color: index < step ? AppTheme.blue : const Color(0xffdbe4eb),
          ),
      ],
    ],
  );
}
