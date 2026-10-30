import 'package:flutter/material.dart';

import '../../../../app/di/app_dependencies.dart';
import '../../../../core/api_client.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/app_brand_mark.dart';
import '../../../../core/widgets/app_back_button.dart';
import '../../../../core/widgets/app_page_bar.dart';

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

  @override
  void dispose() {
    _email.dispose();
    _code.dispose();
    _name.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _continue() async {
    final email = _email.text.trim().toLowerCase();
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      if (_step == 0) {
        if (!email.endsWith('@hvnh.edu.vn')) {
          throw const ApiException('Vui lòng dùng email @hvnh.edu.vn.', 400);
        }
        await widget.dependencies.authRepository.requestRegistrationCode(email);
        setState(() => _step = 1);
      } else if (_step == 1) {
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
        if (mounted) Navigator.of(context).pop();
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
      appBar: AppPageBar(
        leading: AppBackButton(
          onPressed: () {
            if (_busy) return;
            if (_step > 0) {
              setState(() {
                _step--;
                _error = null;
              });
            } else {
              Navigator.of(context).maybePop();
            }
          },
        ),
        title: 'Tạo tài khoản',
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(18, 12, 18, 28),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 460),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Container(
                    padding: const EdgeInsets.all(22),
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(22),
                      gradient: const LinearGradient(
                        colors: [Color(0xff071e36), Color(0xff155784)],
                      ),
                    ),
                    child: const Row(
                      children: [
                        AppBrandMark(size: 42),
                        SizedBox(width: 13),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'HVNH Hub',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 18,
                                  fontWeight: FontWeight.w800,
                                ),
                              ),
                              SizedBox(height: 3),
                              Text(
                                'Một tài khoản cho mọi kết nối',
                                style: TextStyle(
                                  color: Color(0xffc9deec),
                                  fontSize: 12,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  Container(
                    padding: const EdgeInsets.fromLTRB(21, 25, 21, 22),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(22),
                      border: Border.all(color: const Color(0xffdbe6ee)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Text(
                          'BƯỚC ${_step + 1} / 3',
                          style: const TextStyle(
                            color: AppTheme.blue,
                            fontSize: 11,
                            fontWeight: FontWeight.w800,
                            letterSpacing: 1,
                          ),
                        ),
                        const SizedBox(height: 10),
                        LinearProgressIndicator(
                          value: (_step + 1) / 3,
                          minHeight: 5,
                          borderRadius: BorderRadius.circular(5),
                          backgroundColor: const Color(0xffe6eef3),
                          color: AppTheme.blue,
                        ),
                        const SizedBox(height: 20),
                        Text(
                          title,
                          style: Theme.of(context).textTheme.headlineSmall,
                        ),
                        const SizedBox(height: 6),
                        Text(
                          description,
                          style: const TextStyle(
                            color: AppTheme.muted,
                            height: 1.45,
                          ),
                        ),
                        const SizedBox(height: 23),
                        if (_step == 0)
                          TextField(
                            controller: _email,
                            keyboardType: TextInputType.emailAddress,
                            decoration: const InputDecoration(
                              labelText: 'Email @hvnh.edu.vn',
                              prefixIcon: Icon(Icons.mail_outline),
                            ),
                          ),
                        if (_step == 1)
                          TextField(
                            controller: _code,
                            keyboardType: TextInputType.number,
                            maxLength: 4,
                            autofocus: true,
                            decoration: const InputDecoration(
                              labelText: 'Mã OTP',
                              prefixIcon: Icon(Icons.password_outlined),
                            ),
                          ),
                        if (_step == 2) ...[
                          TextField(
                            controller: _name,
                            textCapitalization: TextCapitalization.words,
                            decoration: const InputDecoration(
                              labelText: 'Họ và tên',
                              prefixIcon: Icon(Icons.person_outline),
                            ),
                          ),
                          const SizedBox(height: 12),
                          TextField(
                            controller: _password,
                            obscureText: _obscure,
                            decoration: InputDecoration(
                              labelText: 'Mật khẩu tối thiểu 8 ký tự',
                              prefixIcon: const Icon(Icons.lock_outline),
                              suffixIcon: IconButton(
                                onPressed: () =>
                                    setState(() => _obscure = !_obscure),
                                icon: Icon(
                                  _obscure
                                      ? Icons.visibility_outlined
                                      : Icons.visibility_off_outlined,
                                ),
                              ),
                            ),
                          ),
                        ],
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
                          onPressed: _busy ? null : _continue,
                          child: Padding(
                            padding: const EdgeInsets.all(13),
                            child: Text(
                              _busy
                                  ? 'Đang xử lý...'
                                  : _step == 2
                                  ? 'Tạo tài khoản'
                                  : 'Tiếp tục',
                            ),
                          ),
                        ),
                        if (_step > 0)
                          TextButton(
                            onPressed: _busy
                                ? null
                                : () => setState(() => _step--),
                            child: const Text('Bước trước'),
                          ),
                      ],
                    ),
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
