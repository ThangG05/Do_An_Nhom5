import 'package:flutter/material.dart';

import '../../../../core/widgets/app_page_bar.dart';

import '../../../feed/domain/repositories/feed_repository.dart';
import '../../domain/repositories/group_repository.dart';
import 'group_admin_page.dart';

/// Role landing page used after a group administrator signs in.
/// It mirrors the web workspace by keeping group admins out of the user feed
/// and limiting the selector to groups assigned by the backend.
class GroupAdminRootPage extends StatefulWidget {
  const GroupAdminRootPage({
    super.key,
    required this.groupRepository,
    required this.feedRepository,
    required this.adminGroupSlugs,
    required this.onLogout,
  });

  final GroupRepository groupRepository;
  final FeedRepository feedRepository;
  final List<String> adminGroupSlugs;
  final Future<void> Function() onLogout;

  @override
  State<GroupAdminRootPage> createState() => _GroupAdminRootPageState();
}

class _GroupAdminRootPageState extends State<GroupAdminRootPage> {
  List<Map<String, dynamic>> _groups = const [];
  String? _selectedId;
  String? _error;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final all = await widget.groupRepository.getGroups();
      final assigned = all.where((group) {
        final slug = group['slug']?.toString() ?? '';
        return group['membership']?.toString() == 'ADMIN' ||
            widget.adminGroupSlugs.contains(slug);
      }).toList();
      if (!mounted) return;
      setState(() {
        _groups = assigned;
        _selectedId = assigned.any((group) => '${group['id']}' == _selectedId)
            ? _selectedId
            : assigned.isEmpty
            ? null
            : assigned.first['id']?.toString();
        _error = null;
        _loading = false;
      });
    } catch (error) {
      if (mounted) {
        setState(() {
          _error = error.toString();
          _loading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) {
      return Scaffold(
        appBar: AppPageBar(
          title: 'Quản trị nhóm',
          showBack: false,
          actions: [
            IconButton(
              onPressed: widget.onLogout,
              tooltip: 'Đăng xuất',
              icon: const Icon(Icons.logout),
            ),
          ],
        ),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
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
        ),
      );
    }
    if (_selectedId == null) {
      return Scaffold(
        appBar: AppPageBar(
          title: 'Quản trị nhóm',
          showBack: false,
          actions: [
            IconButton(
              onPressed: widget.onLogout,
              tooltip: 'Đăng xuất',
              icon: const Icon(Icons.logout),
            ),
          ],
        ),
        body: _loading
            ? const Center(child: CircularProgressIndicator())
            : const Center(
                child: Text('Tài khoản chưa được phân công quản trị nhóm.'),
              ),
      );
    }
    final selected = _groups.firstWhere(
      (group) => '${group['id']}' == _selectedId,
    );
    return GroupAdminPage(
      key: ValueKey(_selectedId),
      groupId: _selectedId!,
      groupName: '${selected['name']}',
      groupSlug: '${selected['slug']}',
      groupRepository: widget.groupRepository,
      feedRepository: widget.feedRepository,
      adminGroups: _groups,
      onSelectGroup: (id) => setState(() => _selectedId = id),
      onLogout: widget.onLogout,
    );
  }
}
