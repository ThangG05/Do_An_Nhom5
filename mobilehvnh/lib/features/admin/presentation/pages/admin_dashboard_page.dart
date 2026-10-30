import 'package:flutter/material.dart';
import '../../../../core/widgets/app_page_bar.dart';
import '../../../../core/widgets/app_state_view.dart';

import '../../domain/repositories/admin_repository.dart';
import 'system_settings_page.dart';

class AdminDashboardPage extends StatefulWidget {
  const AdminDashboardPage({
    super.key,
    required this.repository,
    this.onLogout,
  });

  final AdminRepository repository;
  final Future<void> Function()? onLogout;

  @override
  State<AdminDashboardPage> createState() => _AdminDashboardPageState();
}

class _AdminDashboardPageState extends State<AdminDashboardPage> {
  Map<String, dynamic>? _dashboard;
  List<dynamic> _users = [];
  int _userTotal = 0;
  bool _loading = true;
  bool _loadingMoreUsers = false;
  String? _error;
  String _query = '';
  String _roleFilter = 'USER';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final values = await Future.wait([
        widget.repository.getDashboard(),
        widget.repository.getUsers(query: _query, role: _roleFilter, limit: 30),
      ]);
      _dashboard = values[0];
      _users = (values[1]['items'] as List?) ?? [];
      _userTotal = values[1]['total'] as int? ?? _users.length;
      _error = null;
    } catch (error) {
      _error = error.toString();
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _loadMoreUsers() async {
    if (_loadingMoreUsers || _users.length >= _userTotal) return;
    setState(() => _loadingMoreUsers = true);
    try {
      final page = await widget.repository.getUsers(
        query: _query,
        role: _roleFilter,
        limit: 30,
        offset: _users.length,
      );
      final incoming = (page['items'] as List?) ?? const [];
      final known = _users
          .whereType<Map>()
          .map((item) => item['id']?.toString())
          .toSet();
      setState(() {
        _users.addAll(
          incoming.where(
            (item) => item is Map && !known.contains(item['id']?.toString()),
          ),
        );
        _userTotal = page['total'] as int? ?? _userTotal;
      });
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.toString())));
      }
    } finally {
      if (mounted) setState(() => _loadingMoreUsers = false);
    }
  }

  Future<void> _changeStatus(Map<dynamic, dynamic> user) async {
    final reason = TextEditingController();
    String status = user['status']?.toString() == 'LOCKED'
        ? 'ACTIVE'
        : 'LOCKED';
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Cập nhật trạng thái tài khoản'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            DropdownButtonFormField<String>(
              initialValue: status,
              items: const [
                DropdownMenuItem(value: 'ACTIVE', child: Text('Hoạt động')),
                DropdownMenuItem(value: 'LOCKED', child: Text('Khóa')),
                DropdownMenuItem(value: 'DISABLED', child: Text('Vô hiệu hóa')),
              ],
              onChanged: (value) => status = value ?? status,
              decoration: const InputDecoration(labelText: 'Trạng thái'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: reason,
              minLines: 2,
              maxLines: 4,
              decoration: const InputDecoration(
                labelText: 'Lý do (ít nhất 3 ký tự)',
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Hủy'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(dialogContext, true),
            child: const Text('Cập nhật'),
          ),
        ],
      ),
    );
    if (confirmed != true) {
      reason.dispose();
      return;
    }
    try {
      await widget.repository.updateUserStatus(
        '${user['id']}',
        status: status,
        reason: reason.text.trim(),
      );
      await _load();
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('Đã cập nhật tài khoản.')));
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.toString())));
      }
    } finally {
      reason.dispose();
    }
  }

  Future<void> _discipline(Map<dynamic, dynamic> user, String action) async {
    final reason = TextEditingController();
    final duration = TextEditingController(text: '7');
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(switch (action) {
          'WARN' => 'Gửi cảnh cáo',
          'SUSPEND' => 'Tạm khóa tài khoản',
          'BAN' => 'Vô hiệu hóa tài khoản',
          _ => 'Mở khóa tài khoản',
        }),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (action == 'SUSPEND')
              TextField(
                controller: duration,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: 'Số ngày tạm khóa',
                ),
              ),
            if (action == 'SUSPEND') const SizedBox(height: 12),
            TextField(
              controller: reason,
              minLines: 2,
              maxLines: 4,
              decoration: const InputDecoration(
                labelText: 'Lý do',
                hintText: 'Tối thiểu 3 ký tự',
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Hủy'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(dialogContext, true),
            child: const Text('Xác nhận'),
          ),
        ],
      ),
    );
    if (confirmed != true) {
      reason.dispose();
      duration.dispose();
      return;
    }
    try {
      final days = int.tryParse(duration.text.trim());
      if (reason.text.trim().length < 3) {
        throw Exception('Vui lòng nhập lý do từ 3 ký tự.');
      }
      if (action == 'SUSPEND' && (days == null || days < 1)) {
        throw Exception('Số ngày tạm khóa không hợp lệ.');
      }
      await widget.repository.disciplineUser(
        '${user['id']}',
        action: action,
        reason: reason.text.trim(),
        durationDays: action == 'SUSPEND' ? days : null,
      );
      await _load();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Đã áp dụng biện pháp xử lý.')),
        );
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.toString())));
      }
    } finally {
      reason.dispose();
      duration.dispose();
    }
  }

  Widget _stat(String label, dynamic value, IconData icon) => Expanded(
    child: Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: const Color(0xff0866c6)),
            const SizedBox(height: 8),
            Text(
              '$value',
              style: const TextStyle(fontSize: 23, fontWeight: FontWeight.w800),
            ),
            Text(label, style: const TextStyle(color: Color(0xff63758c))),
          ],
        ),
      ),
    ),
  );

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(body: AppLoadingList(count: 4));
    }
    if (_error != null) {
      return Scaffold(
        appBar: const AppPageBar(title: 'Quản trị hệ thống'),
        body: AppStateView(
          icon: Icons.wifi_off_rounded,
          title: 'Chưa tải được bảng quản trị',
          message: _error!,
          actionLabel: 'Thử lại',
          onAction: _load,
        ),
      );
    }
    final dashboard = _dashboard ?? const <String, dynamic>{};
    return Scaffold(
      appBar: AppPageBar(
        title: 'Quản trị hệ thống',
        actions: [
          PopupMenuButton<String>(
            tooltip: 'Tùy chọn quản trị',
            icon: const Icon(Icons.more_horiz_rounded),
            onSelected: (value) {
              if (value == 'reports') {
                Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) =>
                        _ReportQueuePage(repository: widget.repository),
                  ),
                );
              } else if (value == 'audit') {
                Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) =>
                        _AuditLogPage(repository: widget.repository),
                  ),
                );
              } else if (value == 'settings') {
                Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) =>
                        SystemSettingsPage(repository: widget.repository),
                  ),
                );
              } else if (value == 'logout') {
                widget.onLogout?.call();
              }
            },
            itemBuilder: (_) => [
              const PopupMenuItem(
                value: 'reports',
                child: ListTile(
                  leading: Icon(Icons.flag_outlined),
                  title: Text('Báo cáo vi phạm'),
                ),
              ),
              const PopupMenuItem(
                value: 'audit',
                child: ListTile(
                  leading: Icon(Icons.history_outlined),
                  title: Text('Nhật ký quản trị'),
                ),
              ),
              const PopupMenuItem(
                value: 'settings',
                child: ListTile(
                  leading: Icon(Icons.settings_outlined),
                  title: Text('Cấu hình hệ thống'),
                ),
              ),
              if (widget.onLogout != null)
                const PopupMenuItem(
                  value: 'logout',
                  child: ListTile(
                    leading: Icon(Icons.logout, color: Colors.red),
                    title: Text('Đăng xuất'),
                  ),
                ),
            ],
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(12, 16, 12, 30),
          children: [
            const Text(
              'Tổng quan hệ thống',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.w800,
                color: Color(0xff062f59),
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                _stat(
                  'Người dùng',
                  dashboard['total_users'] ?? 0,
                  Icons.people_outline,
                ),
                _stat(
                  'Đang hoạt động',
                  dashboard['active_users'] ?? 0,
                  Icons.verified_user_outlined,
                ),
              ],
            ),
            Row(
              children: [
                _stat(
                  'Chờ duyệt',
                  dashboard['pending_posts'] ?? 0,
                  Icons.pending_actions_outlined,
                ),
                _stat(
                  'Báo cáo',
                  dashboard['rejected_posts'] ?? 0,
                  Icons.flag_outlined,
                ),
              ],
            ),
            const SizedBox(height: 18),
            const Text(
              'Tài khoản',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 10),
            TextField(
              onSubmitted: (value) {
                _query = value;
                _load();
              },
              decoration: const InputDecoration(
                prefixIcon: Icon(Icons.search),
                hintText: 'Tìm theo tên, email hoặc mã sinh viên',
              ),
            ),
            const SizedBox(height: 10),
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'USER', label: Text('Sinh viên')),
                ButtonSegment(value: 'ADMIN', label: Text('Quản trị')),
              ],
              selected: {_roleFilter},
              onSelectionChanged: (selection) {
                _roleFilter = selection.first;
                _load();
              },
            ),
            const SizedBox(height: 10),
            ..._users.map((value) {
              final user = value as Map<dynamic, dynamic>;
              return Card(
                margin: const EdgeInsets.only(bottom: 8),
                child: ListTile(
                  title: Text(
                    '${user['full_name'] ?? user['username']}',
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                  subtitle: Text(
                    '${user['student_code'] ?? user['email'] ?? ''}\n${user['status'] ?? ''} · ${user['system_role'] ?? 'USER'} · ${user['rag_total_tokens'] ?? 0} token RAG',
                  ),
                  isThreeLine: true,
                  onTap: () => Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => _RagUsagePage(
                        repository: widget.repository,
                        user: Map<String, dynamic>.from(user),
                      ),
                    ),
                  ),
                  trailing: PopupMenuButton<String>(
                    tooltip: 'Quản lý tài khoản',
                    onSelected: (value) {
                      if (value == 'status') {
                        _changeStatus(user);
                      } else {
                        _discipline(user, value);
                      }
                    },
                    itemBuilder: (_) => const [
                      PopupMenuItem(
                        value: 'status',
                        child: Text('Đổi trạng thái'),
                      ),
                      PopupMenuItem(value: 'WARN', child: Text('Gửi cảnh cáo')),
                      PopupMenuItem(value: 'SUSPEND', child: Text('Tạm khóa')),
                      PopupMenuItem(value: 'BAN', child: Text('Vô hiệu hóa')),
                      PopupMenuItem(value: 'UNLOCK', child: Text('Mở khóa')),
                    ],
                  ),
                ),
              );
            }),
            if (_users.length < _userTotal)
              Padding(
                padding: const EdgeInsets.only(top: 6),
                child: OutlinedButton.icon(
                  onPressed: _loadingMoreUsers ? null : _loadMoreUsers,
                  icon: _loadingMoreUsers
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.expand_more),
                  label: Text(
                    _loadingMoreUsers
                        ? 'Đang tải...'
                        : 'Xem thêm (${_users.length}/$_userTotal)',
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _ReportQueuePage extends StatefulWidget {
  const _ReportQueuePage({required this.repository});
  final AdminRepository repository;

  @override
  State<_ReportQueuePage> createState() => _ReportQueuePageState();
}

class _ReportQueuePageState extends State<_ReportQueuePage> {
  List<Map<String, dynamic>> _reports = [];
  String? _error;
  bool _loading = true;
  String? _status = 'PENDING';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      _reports = await widget.repository.getReports(status: _status);
      _error = null;
    } catch (error) {
      _error = error.toString();
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _resolve(
    Map<String, dynamic> report,
    String decision,
    String action,
  ) async {
    final alreadyRemoved = report['target_removed'] == true;
    final note = TextEditingController();
    final confirmed = alreadyRemoved
        ? true
        : await showDialog<bool>(
            context: context,
            builder: (dialogContext) => AlertDialog(
              title: Text(
                decision == 'REJECT' ? 'Từ chối báo cáo' : 'Xử lý báo cáo',
              ),
              content: TextField(
                controller: note,
                minLines: 3,
                maxLines: 5,
                decoration: const InputDecoration(
                  labelText: 'Ghi chú xử lý (ít nhất 3 ký tự)',
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(dialogContext),
                  child: const Text('Hủy'),
                ),
                FilledButton(
                  onPressed: () => Navigator.pop(dialogContext, true),
                  child: const Text('Xác nhận'),
                ),
              ],
            ),
          );
    if (confirmed != true) {
      note.dispose();
      return;
    }
    try {
      await widget.repository.resolveReport(
        '${report['id']}',
        decision: decision,
        action: action,
        note: note.text.trim(),
      );
      await _load();
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('Đã cập nhật báo cáo.')));
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.toString())));
      }
    } finally {
      note.dispose();
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: const AppPageBar(title: 'Báo cáo vi phạm'),
    body: Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
          child: SegmentedButton<String?>(
            segments: const [
              ButtonSegment(value: 'PENDING', label: Text('Chờ xử lý')),
              ButtonSegment(value: 'RESOLVED', label: Text('Đã xử lý')),
              ButtonSegment(value: null, label: Text('Tất cả')),
            ],
            selected: {_status},
            onSelectionChanged: (value) {
              _status = value.first;
              _load();
            },
          ),
        ),
        Expanded(
          child: _loading
              ? const Center(child: CircularProgressIndicator())
              : _error != null
              ? Center(child: Text(_error!))
              : _reports.isEmpty
              ? const Center(child: Text('Không có báo cáo phù hợp.'))
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView.builder(
                    padding: const EdgeInsets.fromLTRB(12, 4, 12, 28),
                    itemCount: _reports.length,
                    itemBuilder: (context, index) {
                      final report = _reports[index];
                      return Card(
                        child: Padding(
                          padding: const EdgeInsets.all(14),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Expanded(
                                    child: Text(
                                      '${report['target_type'] ?? 'Nội dung'} · ${report['status'] ?? ''}',
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w800,
                                      ),
                                    ),
                                  ),
                                  PopupMenuButton<String>(
                                    tooltip: 'Xử lý',
                                    onSelected: (value) {
                                      final parts = value.split(':');
                                      _resolve(report, parts[0], parts[1]);
                                    },
                                    itemBuilder: (_) =>
                                        report['target_removed'] == true
                                        ? const [
                                            PopupMenuItem(
                                              value: 'RESOLVE:NONE',
                                              child: Text(
                                                'Kết thúc · nội dung đã gỡ',
                                              ),
                                            ),
                                          ]
                                        : const [
                                            PopupMenuItem(
                                              value: 'RESOLVE:NONE',
                                              child: Text(
                                                'Đóng, không áp dụng biện pháp',
                                              ),
                                            ),
                                            PopupMenuItem(
                                              value: 'RESOLVE:HIDE_CONTENT',
                                              child: Text('Ẩn nội dung'),
                                            ),
                                            PopupMenuItem(
                                              value: 'RESOLVE:LOCK_USER',
                                              child: Text('Khóa tài khoản'),
                                            ),
                                            PopupMenuItem(
                                              value: 'RESOLVE:DISABLE_USER',
                                              child: Text(
                                                'Vô hiệu hóa tài khoản',
                                              ),
                                            ),
                                            PopupMenuItem(
                                              value: 'REJECT:NONE',
                                              child: Text('Từ chối báo cáo'),
                                            ),
                                          ],
                                  ),
                                ],
                              ),
                              const SizedBox(height: 8),
                              Text(
                                '${report['target_summary'] ?? ''}',
                                maxLines: 3,
                                overflow: TextOverflow.ellipsis,
                              ),
                              const SizedBox(height: 8),
                              Text('Lý do: ${report['reason'] ?? ''}'),
                              if (report['target_removed'] == true)
                                const Text(
                                  'Nội dung đã được gỡ trước khi xử lý báo cáo.',
                                ),
                              const SizedBox(height: 8),
                              Text(
                                'Gửi bởi ${report['reporter_name'] ?? 'Không rõ'} · ${report['created_at'] ?? ''}',
                                style: const TextStyle(
                                  color: Color(0xff63758c),
                                  fontSize: 12,
                                ),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
        ),
      ],
    ),
  );
}

class _AuditLogPage extends StatefulWidget {
  const _AuditLogPage({required this.repository});
  final AdminRepository repository;

  @override
  State<_AuditLogPage> createState() => _AuditLogPageState();
}

class _AuditLogPageState extends State<_AuditLogPage> {
  List<Map<String, dynamic>> _logs = [];
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      _logs = await widget.repository.getAuditLogs();
      _error = null;
    } catch (error) {
      _error = error.toString();
    }
    if (mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: const AppPageBar(title: 'Nhật ký quản trị'),
    body: _error != null
        ? Center(child: Text(_error!))
        : _logs.isEmpty
        ? const Center(child: Text('Chưa có hoạt động quản trị.'))
        : RefreshIndicator(
            onRefresh: _load,
            child: ListView.separated(
              padding: const EdgeInsets.only(bottom: 28),
              itemCount: _logs.length,
              separatorBuilder: (_, _) => const Divider(height: 1),
              itemBuilder: (context, index) {
                final log = _logs[index];
                return ListTile(
                  leading: const CircleAvatar(
                    child: Icon(Icons.manage_history_outlined),
                  ),
                  title: Text('${log['action'] ?? 'Thao tác quản trị'}'),
                  subtitle: Text(
                    '${log['actor_name'] ?? 'Hệ thống'} · ${log['created_at'] ?? ''}',
                  ),
                );
              },
            ),
          ),
  );
}

class _RagUsagePage extends StatefulWidget {
  const _RagUsagePage({required this.repository, required this.user});
  final AdminRepository repository;
  final Map<String, dynamic> user;

  @override
  State<_RagUsagePage> createState() => _RagUsagePageState();
}

class _RagUsagePageState extends State<_RagUsagePage> {
  String _period = '30d';
  int _page = 0;
  Map<String, dynamic>? _usage;
  String? _error;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      _usage = await widget.repository.getUserRagUsage(
        '${widget.user['id']}',
        period: _period,
        offset: _page * 10,
      );
      _error = null;
    } catch (error) {
      _error = error.toString();
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final calls = (_usage?['calls'] as List?) ?? const [];
    return Scaffold(
      appBar: AppBar(
        title: Text(
          'Token RAG · ${widget.user['full_name'] ?? widget.user['username']}',
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          DropdownButtonFormField<String>(
            initialValue: _period,
            decoration: const InputDecoration(labelText: 'Khoảng thời gian'),
            items: const [
              DropdownMenuItem(value: 'today', child: Text('Hôm nay')),
              DropdownMenuItem(value: '7d', child: Text('7 ngày')),
              DropdownMenuItem(value: '30d', child: Text('30 ngày')),
              DropdownMenuItem(value: 'all', child: Text('Toàn thời gian')),
            ],
            onChanged: (value) {
              if (value != null) {
                _period = value;
                _page = 0;
                _load();
              }
            },
          ),
          const SizedBox(height: 16),
          if (_loading)
            const Center(child: CircularProgressIndicator())
          else if (_error != null)
            Center(child: Text(_error!))
          else ...[
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                Chip(label: Text('Input: ${_usage?['input_tokens'] ?? '—'}')),
                Chip(label: Text('Output: ${_usage?['output_tokens'] ?? '—'}')),
                Chip(label: Text('Tổng: ${_usage?['total_tokens'] ?? '—'}')),
              ],
            ),
            Text(
              '${_usage?['usage_calls'] ?? 0} lượt gọi · ${_usage?['usage_missing'] ?? 0} lượt không có usage',
            ),
            const SizedBox(height: 16),
            const Text(
              'Lượt gọi gần nhất',
              style: TextStyle(fontWeight: FontWeight.w800, fontSize: 17),
            ),
            ...calls.whereType<Map>().map(
              (call) => Card(
                child: ListTile(
                  title: Text(
                    '${call['provider'] ?? ''} · ${call['model'] ?? ''}',
                  ),
                  subtitle: Text(
                    '${call['created_at'] ?? ''} · ${call['status'] ?? ''}',
                  ),
                  trailing: Text('${call['total_tokens'] ?? '—'}'),
                ),
              ),
            ),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                TextButton(
                  onPressed: _page == 0
                      ? null
                      : () {
                          _page--;
                          _load();
                        },
                  child: const Text('Trước'),
                ),
                Text('Trang ${_page + 1}'),
                TextButton(
                  onPressed: calls.length < 10
                      ? null
                      : () {
                          _page++;
                          _load();
                        },
                  child: const Text('Tiếp'),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}
