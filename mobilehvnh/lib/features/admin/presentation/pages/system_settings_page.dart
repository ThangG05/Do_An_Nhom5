import 'package:flutter/material.dart';
import '../../../../core/widgets/app_page_bar.dart';

import '../../domain/repositories/admin_repository.dart';

class SystemSettingsPage extends StatefulWidget {
  const SystemSettingsPage({super.key, required this.repository});
  final AdminRepository repository;

  @override
  State<SystemSettingsPage> createState() => _SystemSettingsPageState();
}

class _SystemSettingsPageState extends State<SystemSettingsPage> {
  Map<String, dynamic>? _maintenance;
  List<Map<String, dynamic>> _keywords = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final maintenance = widget.repository.getMaintenance();
      final keywords = widget.repository.getKeywords();
      _maintenance = await maintenance;
      _keywords = await keywords;
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.toString())));
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _editMaintenance() async {
    final current = _maintenance ?? const <String, dynamic>{};
    var enabled = current['enabled'] == true;
    final message = TextEditingController(
      text:
          current['message']?.toString() ??
          'Hệ thống đang bảo trì. Vui lòng quay lại sau.',
    );
    final saved = await showDialog<bool>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text('Chế độ bảo trì'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              SwitchListTile.adaptive(
                contentPadding: EdgeInsets.zero,
                title: const Text('Bật bảo trì'),
                value: enabled,
                onChanged: (value) => setDialogState(() => enabled = value),
              ),
              TextField(
                controller: message,
                minLines: 2,
                maxLines: 4,
                decoration: const InputDecoration(
                  labelText: 'Thông báo hiển thị cho người dùng',
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Hủy'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Lưu cấu hình'),
            ),
          ],
        ),
      ),
    );
    if (saved == true) {
      try {
        if (message.text.trim().length < 3) {
          throw Exception('Thông báo cần ít nhất 3 ký tự.');
        }
        await widget.repository.updateMaintenance(
          enabled: enabled,
          message: message.text.trim(),
        );
        await _load();
      } catch (error) {
        if (mounted) {
          ScaffoldMessenger.of(
            context,
          ).showSnackBar(SnackBar(content: Text(error.toString())));
        }
      }
    }
    message.dispose();
  }

  Future<void> _editKeyword([Map<String, dynamic>? item]) async {
    final text = TextEditingController(
      text: item?['keyword']?.toString() ?? '',
    );
    var action = item?['action']?.toString() ?? 'BLOCK';
    final saved = await showDialog<bool>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: Text(item == null ? 'Thêm từ khóa' : 'Sửa từ khóa'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: text,
                autofocus: true,
                decoration: const InputDecoration(labelText: 'Từ khóa'),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: action,
                decoration: const InputDecoration(labelText: 'Cách xử lý'),
                items: const [
                  DropdownMenuItem(value: 'BLOCK', child: Text('Chặn bài')),
                  DropdownMenuItem(
                    value: 'REVIEW',
                    child: Text('Đưa vào kiểm duyệt'),
                  ),
                ],
                onChanged: (value) =>
                    setDialogState(() => action = value ?? action),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Hủy'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Lưu'),
            ),
          ],
        ),
      ),
    );
    if (saved == true) {
      try {
        if (text.text.trim().length < 2) {
          throw Exception('Từ khóa cần ít nhất 2 ký tự.');
        }
        if (item == null) {
          await widget.repository.createKeyword(
            keyword: text.text.trim(),
            action: action,
          );
        } else {
          await widget.repository.updateKeyword(
            '${item['id']}',
            keyword: text.text.trim(),
            action: action,
          );
        }
        await _load();
      } catch (error) {
        if (mounted) {
          ScaffoldMessenger.of(
            context,
          ).showSnackBar(SnackBar(content: Text(error.toString())));
        }
      }
    }
    text.dispose();
  }

  Future<void> _deleteKeyword(Map<String, dynamic> item) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Xóa từ khóa?'),
        content: Text('Xóa “${item['keyword']}” khỏi danh sách kiểm duyệt?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Hủy'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Xóa'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    try {
      await widget.repository.deleteKeyword('${item['id']}');
      await _load();
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.toString())));
      }
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: const AppPageBar(title: 'Cấu hình hệ thống'),
    floatingActionButton: FloatingActionButton.extended(
      onPressed: () => _editKeyword(),
      icon: const Icon(Icons.add),
      label: const Text('Từ khóa'),
    ),
    body: _loading
        ? const Center(child: CircularProgressIndicator())
        : RefreshIndicator(
            onRefresh: _load,
            child: ListView(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 92),
              children: [
                Card(
                  child: ListTile(
                    leading: Icon(
                      (_maintenance?['enabled'] == true)
                          ? Icons.warning_amber_rounded
                          : Icons.verified_outlined,
                      color: (_maintenance?['enabled'] == true)
                          ? Colors.orange.shade700
                          : Colors.green.shade700,
                    ),
                    title: Text(
                      (_maintenance?['enabled'] == true)
                          ? 'Đang bật chế độ bảo trì'
                          : 'Hệ thống đang hoạt động bình thường',
                    ),
                    subtitle: Text(
                      '${_maintenance?['message'] ?? ''}',
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    trailing: const Icon(Icons.edit_outlined),
                    onTap: _editMaintenance,
                  ),
                ),
                const SizedBox(height: 18),
                Text(
                  'Từ khóa kiểm duyệt (${_keywords.length})',
                  style: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 8),
                if (_keywords.isEmpty)
                  const Card(
                    child: Padding(
                      padding: EdgeInsets.all(24),
                      child: Center(child: Text('Chưa có từ khóa kiểm duyệt.')),
                    ),
                  )
                else
                  ..._keywords.map(
                    (item) => Card(
                      child: ListTile(
                        title: Text(
                          '${item['keyword']}',
                          style: TextStyle(
                            decoration: item['is_active'] == false
                                ? TextDecoration.lineThrough
                                : null,
                          ),
                        ),
                        subtitle: Text(
                          item['action'] == 'REVIEW'
                              ? 'Đưa vào kiểm duyệt'
                              : 'Chặn bài tự động',
                        ),
                        leading: Switch(
                          value: item['is_active'] == true,
                          onChanged: (value) async {
                            await widget.repository.updateKeyword(
                              '${item['id']}',
                              isActive: value,
                            );
                            await _load();
                          },
                        ),
                        trailing: PopupMenuButton<String>(
                          onSelected: (value) {
                            if (value == 'edit') _editKeyword(item);
                            if (value == 'delete') _deleteKeyword(item);
                          },
                          itemBuilder: (_) => const [
                            PopupMenuItem(
                              value: 'edit',
                              child: Text('Chỉnh sửa'),
                            ),
                            PopupMenuItem(value: 'delete', child: Text('Xóa')),
                          ],
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          ),
  );
}
