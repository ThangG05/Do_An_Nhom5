import 'package:flutter/material.dart';

import '../../../../core/widgets/app_avatar.dart';
import '../../../../core/widgets/app_back_button.dart';
import '../../../feed/domain/repositories/feed_repository.dart';
import '../../../feed/feed_page.dart';
import '../../domain/repositories/group_repository.dart';
import 'study_library_page.dart';

class GroupAdminPage extends StatefulWidget {
  const GroupAdminPage({
    super.key,
    required this.groupId,
    required this.groupName,
    this.groupSlug = '',
    required this.groupRepository,
    required this.feedRepository,
    this.adminGroups = const [],
    this.onSelectGroup,
    this.onLogout,
  });

  final String groupId;
  final String groupName;
  final String groupSlug;
  final GroupRepository groupRepository;
  final FeedRepository feedRepository;
  final List<Map<String, dynamic>> adminGroups;
  final ValueChanged<String>? onSelectGroup;
  final Future<void> Function()? onLogout;

  @override
  State<GroupAdminPage> createState() => _GroupAdminPageState();
}

class _GroupAdminPageState extends State<GroupAdminPage> {
  List<Map<String, dynamic>> _pendingPosts = [];
  List<Map<String, dynamic>> _approvedPosts = [];
  List<Map<String, dynamic>> _members = [];
  List<Map<String, dynamic>> _requests = [];
  List<Map<String, dynamic>> _reports = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final values = await Future.wait([
        widget.groupRepository.getPendingPosts(widget.groupId),
        widget.groupRepository.getPosts(widget.groupId, limit: 100),
        widget.groupRepository.getMembers(widget.groupId),
        widget.groupRepository.getJoinRequests(widget.groupId),
        widget.groupRepository.getGroupReports(widget.groupId),
      ]);
      _pendingPosts = values[0];
      _approvedPosts = values[1];
      _members = values[2];
      _requests = values[3];
      _reports = values[4];
      _error = null;
    } catch (error) {
      _error = error.toString();
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _moderate(String postId, bool approved) async {
    try {
      await widget.groupRepository.moderatePost(
        widget.groupId,
        postId,
        approved: approved,
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

  Future<void> _resolveReport(Map<String, dynamic> report, bool hide) async {
    final alreadyRemoved = report['target_removed'] == true;
    if (alreadyRemoved) {
      try {
        await widget.groupRepository.resolveGroupReport(
          '${report['id']}',
          false,
          '',
          alreadyRemoved: true,
        );
        await _load();
      } catch (error) {
        if (mounted) {
          ScaffoldMessenger.of(
            context,
          ).showSnackBar(SnackBar(content: Text(error.toString())));
        }
      }
      return;
    }
    final controller = TextEditingController();
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(hide ? 'Xác nhận và gỡ nội dung' : 'Bác bỏ báo cáo'),
        content: TextField(
          controller: controller,
          minLines: 2,
          maxLines: 4,
          decoration: const InputDecoration(
            labelText: 'Lý do xử lý (ít nhất 3 ký tự)',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Hủy'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Xác nhận'),
          ),
        ],
      ),
    );
    final note = controller.text.trim();
    controller.dispose();
    if (confirmed != true) return;
    if (note.length < 3) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Vui lòng ghi rõ lý do xử lý.')),
        );
      }
      return;
    }
    try {
      await widget.groupRepository.resolveGroupReport(
        '${report['id']}',
        hide,
        note,
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

  Future<void> _decideJoin(String requestId, bool approved) async {
    try {
      await widget.groupRepository.decideJoinRequest(
        widget.groupId,
        requestId,
        approved: approved,
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

  Future<bool> _confirm({
    required String title,
    required String message,
    required String confirm,
  }) async {
    return await showDialog<bool>(
          context: context,
          builder: (context) => AlertDialog(
            title: Text(title),
            content: Text(message),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context, false),
                child: const Text('Hủy'),
              ),
              FilledButton(
                onPressed: () => Navigator.pop(context, true),
                child: Text(confirm),
              ),
            ],
          ),
        ) ??
        false;
  }

  Future<void> _removeMember(Map<String, dynamic> member) async {
    if (member['role']?.toString() == 'ADMIN') {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Không thể mời quản trị viên ra khỏi nhóm tại đây.'),
        ),
      );
      return;
    }
    final confirmed = await _confirm(
      title: 'Mời thành viên rời nhóm?',
      message:
          '${member['name'] ?? member['username']} sẽ không còn thấy nội dung riêng của nhóm.',
      confirm: 'Mời rời nhóm',
    );
    if (!confirmed) return;
    try {
      await widget.groupRepository.removeMember(
        widget.groupId,
        '${member['id']}',
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

  Future<void> _togglePin(Map<String, dynamic> post) async {
    try {
      await widget.groupRepository.pinPost(
        widget.groupId,
        '${post['id']}',
        pinned: post['isPinned'] != true,
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

  Future<void> _removePost(Map<String, dynamic> post) async {
    final reason = TextEditingController();
    final submitted = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Gỡ bài viết'),
        content: TextField(
          controller: reason,
          minLines: 2,
          maxLines: 4,
          decoration: const InputDecoration(
            labelText: 'Lý do gỡ bài',
            hintText: 'Tối thiểu 3 ký tự',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Hủy'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Gỡ bài'),
          ),
        ],
      ),
    );
    if (submitted != true) {
      reason.dispose();
      return;
    }
    try {
      final value = reason.text.trim();
      if (value.length < 3) {
        throw Exception('Vui lòng nhập lý do gỡ bài từ 3 ký tự.');
      }
      await widget.groupRepository.removePost(
        widget.groupId,
        '${post['id']}',
        reason: value,
      );
      await _load();
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

  Widget _tabList(List<Widget> children) => RefreshIndicator(
    onRefresh: _load,
    child: ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(12, 12, 12, 30),
      children: children,
    ),
  );

  Widget _empty(String message, IconData icon) => Padding(
    padding: const EdgeInsets.only(top: 54),
    child: Column(
      children: [
        Icon(icon, size: 46, color: const Color(0xff8aa1b9)),
        const SizedBox(height: 12),
        Text(message, style: const TextStyle(color: Color(0xff63758c))),
      ],
    ),
  );

  @override
  Widget build(BuildContext context) => DefaultTabController(
    length: 5,
    child: Scaffold(
      appBar: AppBar(
        centerTitle: false,
        leading: const AppBackButton(),
        title: widget.adminGroups.length > 1
            ? DropdownButtonHideUnderline(
                child: DropdownButton<String>(
                  value: widget.groupId,
                  isExpanded: false,
                  items: widget.adminGroups
                      .map(
                        (group) => DropdownMenuItem<String>(
                          value: '${group['id']}',
                          child: Text('${group['name']}'),
                        ),
                      )
                      .toList(),
                  onChanged: (value) {
                    if (value != null && value != widget.groupId) {
                      widget.onSelectGroup?.call(value);
                    }
                  },
                ),
              )
            : Text('Quản trị ${widget.groupName}'),
        actions: [
          if (widget.groupSlug == 'hoc-tap')
            IconButton(
              tooltip: 'Kho tài liệu Học tập',
              icon: const Icon(Icons.library_books_outlined),
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => StudyLibraryPage(
                    groupId: widget.groupId,
                    repository: widget.groupRepository,
                    isAdmin: true,
                  ),
                ),
              ),
            ),
          if (widget.onLogout != null)
            IconButton(
              tooltip: 'Đăng xuất',
              onPressed: widget.onLogout,
              icon: const Icon(Icons.logout),
            ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
          ? Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.cloud_off_outlined, size: 48),
                    const SizedBox(height: 12),
                    Text(_error!, textAlign: TextAlign.center),
                    const SizedBox(height: 12),
                    OutlinedButton.icon(
                      onPressed: _load,
                      icon: const Icon(Icons.refresh),
                      label: const Text('Thử lại'),
                    ),
                  ],
                ),
              ),
            )
          : Column(
              children: [
                Container(
                  width: double.infinity,
                  margin: const EdgeInsets.fromLTRB(12, 12, 12, 8),
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(20),
                    gradient: const LinearGradient(
                      colors: [Color(0xff062f59), Color(0xff176aa0)],
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'GROUP ADMIN WORKSPACE',
                        style: TextStyle(
                          color: Color(0xffffdf32),
                          fontSize: 11,
                          fontWeight: FontWeight.w800,
                          letterSpacing: .7,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        widget.groupName,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 24,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      const SizedBox(height: 14),
                      Row(
                        children: [
                          _Count(
                            label: 'Chờ duyệt',
                            value: _pendingPosts.length,
                            icon: Icons.pending_actions_outlined,
                          ),
                          _Count(
                            label: 'Yêu cầu',
                            value: _requests.length,
                            icon: Icons.person_add_alt_1_outlined,
                          ),
                          _Count(
                            label: 'Thành viên',
                            value: _members.length,
                            icon: Icons.groups_outlined,
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                const TabBar(
                  isScrollable: true,
                  tabAlignment: TabAlignment.start,
                  tabs: [
                    Tab(text: 'Kiểm duyệt'),
                    Tab(text: 'Bài đã duyệt'),
                    Tab(text: 'Yêu cầu'),
                    Tab(text: 'Thành viên'),
                    Tab(text: 'Báo cáo'),
                  ],
                ),
                Expanded(
                  child: TabBarView(
                    children: [
                      _tabList([
                        if (_pendingPosts.isEmpty)
                          _empty(
                            'Không có bài viết chờ duyệt.',
                            Icons.task_alt_outlined,
                          )
                        else
                          ..._pendingPosts.map(
                            (post) => Column(
                              children: [
                                PostCard(
                                  post: post,
                                  repository: widget.feedRepository,
                                  onLike: () {},
                                ),
                                OverflowBar(
                                  alignment: MainAxisAlignment.end,
                                  children: [
                                    TextButton(
                                      onPressed: () =>
                                          _moderate('${post['id']}', false),
                                      child: const Text('Từ chối'),
                                    ),
                                    FilledButton.icon(
                                      onPressed: () =>
                                          _moderate('${post['id']}', true),
                                      icon: const Icon(Icons.check),
                                      label: const Text('Duyệt bài'),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 12),
                              ],
                            ),
                          ),
                      ]),
                      _tabList([
                        if (_approvedPosts.isEmpty)
                          _empty(
                            'Chưa có bài viết nào được duyệt.',
                            Icons.article_outlined,
                          )
                        else
                          ..._approvedPosts.map(
                            (post) => Column(
                              children: [
                                PostCard(
                                  post: post,
                                  repository: widget.feedRepository,
                                  onLike: () {},
                                ),
                                Row(
                                  children: [
                                    OutlinedButton.icon(
                                      onPressed: () => _togglePin(post),
                                      icon: Icon(
                                        post['isPinned'] == true
                                            ? Icons.push_pin
                                            : Icons.push_pin_outlined,
                                      ),
                                      label: Text(
                                        post['isPinned'] == true
                                            ? 'Bỏ ghim'
                                            : 'Ghim bài',
                                      ),
                                    ),
                                    const Spacer(),
                                    TextButton.icon(
                                      onPressed: () => _removePost(post),
                                      style: TextButton.styleFrom(
                                        foregroundColor: Colors.red,
                                      ),
                                      icon: const Icon(Icons.delete_outline),
                                      label: const Text('Gỡ bài'),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 12),
                              ],
                            ),
                          ),
                      ]),
                      _tabList([
                        if (_requests.isEmpty)
                          _empty(
                            'Không có yêu cầu tham gia mới.',
                            Icons.person_add_disabled_outlined,
                          )
                        else
                          ..._requests.map(
                            (request) => Card(
                              child: ListTile(
                                leading: AppAvatar(
                                  url: request['avatar_url']?.toString(),
                                  name:
                                      request['name']?.toString() ??
                                      request['username']?.toString(),
                                ),
                                title: Text(
                                  '${request['name'] ?? request['username']}',
                                ),
                                subtitle: Text(
                                  request['student_code']
                                              ?.toString()
                                              .isNotEmpty ==
                                          true
                                      ? 'Mã SV: ${request['student_code']}'
                                      : '${request['username'] ?? ''}',
                                ),
                                trailing: Wrap(
                                  children: [
                                    IconButton(
                                      tooltip: 'Từ chối',
                                      onPressed: () => _decideJoin(
                                        '${request['id']}',
                                        false,
                                      ),
                                      icon: const Icon(
                                        Icons.close,
                                        color: Colors.red,
                                      ),
                                    ),
                                    IconButton(
                                      tooltip: 'Chấp nhận',
                                      onPressed: () =>
                                          _decideJoin('${request['id']}', true),
                                      icon: const Icon(
                                        Icons.check,
                                        color: Color(0xff087f4d),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ),
                      ]),
                      _tabList([
                        if (_members.isEmpty)
                          _empty(
                            'Nhóm chưa có thành viên.',
                            Icons.group_off_outlined,
                          )
                        else
                          ..._members.map(
                            (member) => Card(
                              child: ListTile(
                                leading: AppAvatar(
                                  url: member['avatar_url']?.toString(),
                                  name:
                                      member['name']?.toString() ??
                                      member['username']?.toString(),
                                ),
                                title: Text(
                                  '${member['name'] ?? member['username']}',
                                ),
                                subtitle: Text(
                                  member['student_code']
                                              ?.toString()
                                              .isNotEmpty ==
                                          true
                                      ? 'Mã SV: ${member['student_code']}'
                                      : '${member['username'] ?? ''}',
                                ),
                                trailing: Wrap(
                                  crossAxisAlignment: WrapCrossAlignment.center,
                                  children: [
                                    Chip(
                                      label: Text(
                                        member['role'] == 'ADMIN'
                                            ? 'Quản trị viên'
                                            : 'Thành viên',
                                      ),
                                    ),
                                    if (member['role']?.toString() != 'ADMIN')
                                      IconButton(
                                        tooltip: 'Mời rời nhóm',
                                        onPressed: () => _removeMember(member),
                                        icon: const Icon(
                                          Icons.person_remove_outlined,
                                          color: Colors.red,
                                        ),
                                      ),
                                  ],
                                ),
                              ),
                            ),
                          ),
                      ]),
                      _tabList([
                        if (_reports.isEmpty)
                          _empty(
                            'Không có báo cáo cần xử lý.',
                            Icons.verified_outlined,
                          )
                        else
                          ..._reports.map(
                            (report) => Card(
                              child: Padding(
                                padding: const EdgeInsets.all(14),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      '${report['target_type'] ?? ''} · ${report['reporter_name'] ?? ''}',
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w800,
                                      ),
                                    ),
                                    const SizedBox(height: 5),
                                    Text('${report['target_summary'] ?? ''}'),
                                    Text('Lý do: ${report['reason'] ?? ''}'),
                                    if (report['target_removed'] == true)
                                      const Text(
                                        'Nội dung đã được gỡ trước khi xử lý báo cáo.',
                                      ),
                                    OverflowBar(
                                      alignment: MainAxisAlignment.end,
                                      children: [
                                        if (report['target_removed'] != true)
                                          TextButton(
                                            onPressed: () =>
                                                _resolveReport(report, false),
                                            child: const Text('Bác bỏ'),
                                          ),
                                        FilledButton(
                                          onPressed: () =>
                                              _resolveReport(report, true),
                                          child: Text(
                                            report['target_removed'] == true
                                                ? 'Kết thúc · nội dung đã gỡ'
                                                : 'Xác nhận & gỡ',
                                          ),
                                        ),
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ),
                      ]),
                    ],
                  ),
                ),
              ],
            ),
    ),
  );
}

class _Count extends StatelessWidget {
  const _Count({required this.label, required this.value, required this.icon});
  final String label;
  final int value;
  final IconData icon;

  @override
  Widget build(BuildContext context) => Expanded(
    child: Card(
      child: Padding(
        padding: const EdgeInsets.all(8),
        child: Column(
          children: [
            Icon(icon, color: const Color(0xffcfe9ff), size: 19),
            const SizedBox(height: 6),
            Text(
              '$value',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 20,
                fontWeight: FontWeight.w800,
              ),
            ),
            Text(
              label,
              textAlign: TextAlign.center,
              style: const TextStyle(color: Color(0xffd5eafa), fontSize: 10),
            ),
          ],
        ),
      ),
    ),
  );
}
