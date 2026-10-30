import 'dart:ui';

import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../core/chat_realtime.dart';
import '../core/theme/app_theme.dart';
import '../core/theme/app_design_tokens.dart';
import '../core/widgets/app_avatar.dart';
import '../core/widgets/app_brand_mark.dart';
import '../features/admin/admin.dart';
import '../features/ai/ai.dart';
import '../features/chat/chat.dart';
import '../features/feed/feed.dart';
import '../features/groups/groups.dart';
import '../features/notifications/notifications.dart';
import '../features/user/user.dart';
import 'di/app_dependencies.dart';

class AppShell extends StatefulWidget {
  const AppShell({
    super.key,
    required this.dependencies,
    required this.onLogout,
  });

  final AppDependencies dependencies;
  final Future<void> Function() onLogout;

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  final _chatSignal = ValueNotifier<int>(0);
  final _notificationSignal = ValueNotifier<int>(0);
  final _pageRefreshSignals = List.generate(2, (_) => ValueNotifier<int>(0));
  final _visitedTabs = <int>{0};
  final _lastTabRefresh = List.generate(4, (_) => DateTime.now());
  int _index = 0;
  int _chatUnread = 0;
  int _notificationUnread = 0;
  bool _isSuperAdmin = false;
  Map<String, dynamic>? _me;
  late final ChatRealtime _realtime;

  static const _titles = ['Trang chủ', 'Hội nhóm', 'Tin nhắn', 'Thông báo'];

  @override
  void initState() {
    super.initState();
    _realtime = ChatRealtime(widget.dependencies.apiClient);
    _connectRealtime();
    _loadCounts();
    _loadRole();
    _loadProfile();
  }

  Future<void> _connectRealtime() => _realtime.connect(_onRealtime);

  Future<void> _loadRole() async {
    final role = await widget.dependencies.session.role;
    if (mounted) setState(() => _isSuperAdmin = role == 'SUPER_ADMIN');
  }

  Future<void> _loadProfile() async {
    try {
      final profile = await widget.dependencies.userRepository.getMyProfile();
      if (mounted) setState(() => _me = profile);
    } catch (_) {
      // Thanh điều hướng vẫn dùng initials nếu hồ sơ chưa tải được.
    }
  }

  Future<void> _openProfile() async {
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) =>
            ProfilePage(repository: widget.dependencies.userRepository),
      ),
    );
    await _loadProfile();
  }

  void _onRealtime(Map<String, dynamic> event) {
    if (event['event'] == 'message.created') _chatSignal.value++;
    if (event['event'] == 'notification.created') _notificationSignal.value++;
    _loadCounts();
  }

  Future<void> _loadCounts() async {
    try {
      final values = await Future.wait([
        widget.dependencies.apiClient.getObject('/chat/unread-count'),
        widget.dependencies.apiClient.getObject('/notifications/unread-count'),
      ]);
      if (mounted) {
        setState(() {
          _chatUnread = (values[0]['unread_count'] as num?)?.toInt() ?? 0;
          _notificationUnread =
              (values[1]['unread_count'] as num?)?.toInt() ?? 0;
        });
      }
    } catch (_) {}
  }

  @override
  void dispose() {
    _realtime.close();
    _chatSignal.dispose();
    _notificationSignal.dispose();
    for (final signal in _pageRefreshSignals) {
      signal.dispose();
    }
    super.dispose();
  }

  Widget _badge(IconData icon, int count) => Badge(
    isLabelVisible: count > 0,
    label: Text('$count'),
    child: Icon(icon),
  );

  void _selectTab(int index) {
    if (_index == index) return;
    final previousIndex = _index;
    if (MediaQuery.maybeOf(context)?.disableAnimations != true) {
      HapticFeedback.selectionClick();
    }
    final wasVisited = _visitedTabs.contains(index);
    final now = DateTime.now();
    final shouldRefresh =
        wasVisited &&
        now.difference(_lastTabRefresh[index]) > const Duration(seconds: 30);
    setState(() {
      _visitedTabs.add(index);
      _index = index;
    });
    if (index == 0 && previousIndex == 1) {
      _pageRefreshSignals[0].value++;
    }
    if (shouldRefresh) {
      _lastTabRefresh[index] = now;
      if (index < 2 && !(index == 0 && previousIndex == 1)) {
        _pageRefreshSignals[index].value++;
      }
      if (index == 2) _chatSignal.value++;
      if (index == 3) _notificationSignal.value++;
    }
    if (index >= 2) _loadCounts();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(
      centerTitle: false,
      toolbarHeight: 64,
      titleSpacing: 16,
      backgroundColor: Colors.transparent,
      flexibleSpace: ClipRect(
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 18, sigmaY: 18),
          child: Container(color: const Color(0xf3ffffff)),
        ),
      ),
      bottom: PreferredSize(
        preferredSize: const Size.fromHeight(1),
        child: Container(height: 1, color: AppTheme.hairline),
      ),
      title: Row(
        children: [
          const AppBrandMark(size: 32),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text(
                  'HVNH Hub',
                  style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700),
                ),
                Text(
                  _titles[_index],
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontSize: 11,
                    color: Color(0xff62758b),
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
      actions: [
        IconButton(
          tooltip: 'Tìm kiếm sinh viên',
          onPressed: () => Navigator.of(context).push(
            MaterialPageRoute(
              builder: (_) => UserSearchPage(
                repository: widget.dependencies.userRepository,
              ),
            ),
          ),
          icon: const Icon(CupertinoIcons.search, size: 21),
        ),
        IconButton(
          tooltip: 'Trợ lý AI',
          onPressed: () => Navigator.of(context).push(
            MaterialPageRoute(
              builder: (_) =>
                  AiAssistantPage(repository: widget.dependencies.aiRepository),
            ),
          ),
          icon: const Icon(
            CupertinoIcons.sparkles,
            color: Color(0xff155784),
            size: 21,
          ),
        ),
        PopupMenuButton<String>(
          tooltip: 'Tài khoản và tùy chọn',
          icon: AppAvatar(
            radius: 17,
            url: _me?['avatar']?.toString(),
            name: _me?['name']?.toString(),
            online: true,
          ),
          onSelected: (value) {
            if (value == 'profile') _openProfile();
            if (value == 'admin') {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => AdminDashboardPage(
                    repository: widget.dependencies.adminRepository,
                  ),
                ),
              );
            }
            if (value == 'logout') widget.onLogout();
          },
          itemBuilder: (_) => [
            const PopupMenuItem(
              value: 'profile',
              child: ListTile(
                leading: Icon(Icons.person_outline),
                title: Text('Trang cá nhân'),
              ),
            ),
            if (_isSuperAdmin)
              const PopupMenuItem(
                value: 'admin',
                child: ListTile(
                  leading: Icon(Icons.admin_panel_settings_outlined),
                  title: Text('Quản trị hệ thống'),
                ),
              ),
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
    body: IndexedStack(
      index: _index,
      children: [
        _visitedTabs.contains(0)
            ? FeedPage(
                repository: widget.dependencies.feedRepository,
                groupRepository: widget.dependencies.groupRepository,
                currentUser: _me,
                refreshSignal: _pageRefreshSignals[0],
                onOpenGroups: () => _selectTab(1),
                onOpenProfile: _openProfile,
              )
            : const SizedBox.shrink(),
        _visitedTabs.contains(1)
            ? GroupsPage(
                feedRepository: widget.dependencies.feedRepository,
                groupRepository: widget.dependencies.groupRepository,
                currentUser: _me,
                refreshSignal: _pageRefreshSignals[1],
              )
            : const SizedBox.shrink(),
        _visitedTabs.contains(2)
            ? ChatPage(
                repository: widget.dependencies.chatRepository,
                userRepository: widget.dependencies.userRepository,
                apiClient: widget.dependencies.apiClient,
                refreshSignal: _chatSignal,
              )
            : const SizedBox.shrink(),
        _visitedTabs.contains(3)
            ? NotificationsPage(
                feedRepository: widget.dependencies.feedRepository,
                repository: widget.dependencies.notificationRepository,
                refreshSignal: _notificationSignal,
              )
            : const SizedBox.shrink(),
      ],
    ),
    bottomNavigationBar: ClipRect(
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
        child: DecoratedBox(
          decoration: const BoxDecoration(
            color: Color(0xf5ffffff),
            border: Border(top: BorderSide(color: AppTheme.hairline)),
          ),
          child: SafeArea(
            top: false,
            child: Center(
              heightFactor: 1,
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 680),
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(8, 8, 8, 7),
                  child: Row(
                    children: [
                      _tab(
                        0,
                        CupertinoIcons.house,
                        CupertinoIcons.house_fill,
                        'Trang chủ',
                      ),
                      _tab(
                        1,
                        CupertinoIcons.person_2,
                        CupertinoIcons.person_2_fill,
                        'Hội nhóm',
                      ),
                      _tab(
                        2,
                        CupertinoIcons.chat_bubble,
                        CupertinoIcons.chat_bubble_fill,
                        'Tin nhắn',
                        count: _chatUnread,
                      ),
                      _tab(
                        3,
                        CupertinoIcons.bell,
                        CupertinoIcons.bell_fill,
                        'Thông báo',
                        count: _notificationUnread,
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    ),
  );

  Widget _tab(
    int index,
    IconData icon,
    IconData selectedIcon,
    String label, {
    int count = 0,
  }) {
    final selected = _index == index;
    return Expanded(
      child: Semantics(
        button: true,
        selected: selected,
        label: label,
        child: CupertinoButton(
          padding: EdgeInsets.zero,
          onPressed: () => _selectTab(index),
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 2),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                AnimatedContainer(
                  duration: AppMotion.duration(context, AppMotion.selection),
                  curve: AppMotion.curve,
                  width: selected ? 55 : 48,
                  height: 38,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: selected
                        ? AppPalette.light.primarySoft
                        : Colors.transparent,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: count > 0
                      ? _badge(selected ? selectedIcon : icon, count)
                      : Icon(
                          selected ? selectedIcon : icon,
                          size: 23,
                          color: selected ? AppTheme.blue : AppTheme.muted,
                        ),
                ),
                const SizedBox(height: 4),
                Text(
                  label,
                  maxLines: 1,
                  overflow: TextOverflow.fade,
                  softWrap: false,
                  style: TextStyle(
                    fontSize: 11,
                    color: selected ? AppTheme.blue : AppTheme.muted,
                    fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
