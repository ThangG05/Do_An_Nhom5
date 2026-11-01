import 'package:flutter/material.dart';

import '../../../../core/widgets/app_page_bar.dart';
import '../../domain/repositories/user_repository.dart';
import 'social_pages.dart';

class PrivacySettingsPage extends StatefulWidget {
  const PrivacySettingsPage({
    super.key,
    required this.repository,
    this.onPasswordChanged,
  });

  final UserRepository repository;
  final Future<void> Function()? onPasswordChanged;

  @override
  State<PrivacySettingsPage> createState() => _PrivacySettingsPageState();
}

class _PrivacySettingsPageState extends State<PrivacySettingsPage> {
  Future<void> _changePassword() async {
    final current = TextEditingController();
    final next = TextEditingController();
    final confirmed = TextEditingController();
    String? error;
    var saving = false;
    final changed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text('Đổi mật khẩu'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: current,
                  obscureText: true,
                  decoration: const InputDecoration(
                    labelText: 'Mật khẩu hiện tại',
                  ),
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: next,
                  obscureText: true,
                  decoration: const InputDecoration(labelText: 'Mật khẩu mới'),
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: confirmed,
                  obscureText: true,
                  decoration: const InputDecoration(
                    labelText: 'Nhập lại mật khẩu mới',
                  ),
                ),
                if (error != null) ...[
                  const SizedBox(height: 8),
                  Align(
                    alignment: Alignment.centerLeft,
                    child: Text(
                      error!,
                      style: const TextStyle(color: Colors.red),
                    ),
                  ),
                ],
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: saving ? null : () => Navigator.pop(dialogContext),
              child: const Text('Hủy'),
            ),
            FilledButton(
              onPressed: saving
                  ? null
                  : () async {
                      if (current.text.isEmpty || next.text.length < 8) {
                        setDialogState(() {
                          error =
                              'Nhập mật khẩu hiện tại và mật khẩu mới từ 8 ký tự.';
                        });
                        return;
                      }
                      if (next.text != confirmed.text) {
                        setDialogState(
                          () => error = 'Hai mật khẩu mới chưa khớp.',
                        );
                        return;
                      }
                      setDialogState(() {
                        saving = true;
                        error = null;
                      });
                      try {
                        await widget.repository.changePassword(
                          currentPassword: current.text,
                          newPassword: next.text,
                        );
                        if (dialogContext.mounted) {
                          Navigator.pop(dialogContext, true);
                        }
                      } catch (exception) {
                        setDialogState(() {
                          saving = false;
                          error = exception.toString();
                        });
                      }
                    },
              child: Text(saving ? 'Đang lưu...' : 'Cập nhật'),
            ),
          ],
        ),
      ),
    );
    current.dispose();
    next.dispose();
    confirmed.dispose();
    if (changed == true && mounted) {
      final onPasswordChanged = widget.onPasswordChanged;
      if (onPasswordChanged != null) await onPasswordChanged();
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: const AppPageBar(title: 'Cài đặt quyền riêng tư'),
    body: ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Card(
          child: Column(
            children: [
              ListTile(
                leading: const Icon(Icons.block_outlined),
                title: const Text('Danh sách đã chặn'),
                subtitle: const Text('Xem và quản lý tài khoản đã chặn.'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) =>
                        BlockedUsersPage(repository: widget.repository),
                  ),
                ),
              ),
              const Divider(height: 1),
              ListTile(
                leading: const Icon(Icons.lock_outline),
                title: const Text('Đổi mật khẩu'),
                subtitle: const Text('Cập nhật mật khẩu đăng nhập.'),
                trailing: const Icon(Icons.chevron_right),
                onTap: _changePassword,
              ),
            ],
          ),
        ),
      ],
    ),
  );
}
