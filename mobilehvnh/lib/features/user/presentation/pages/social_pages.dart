import 'dart:async';

import 'package:flutter/material.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/app_avatar.dart';
import '../../../../core/widgets/app_page_bar.dart';
import '../../../../core/widgets/app_network_image.dart';
import '../../domain/repositories/user_repository.dart';
import '../../../feed/domain/repositories/feed_repository.dart';
import '../widgets/profile_content_tabs.dart';

class UserSearchPage extends StatefulWidget {
  const UserSearchPage({
    super.key,
    required this.repository,
    this.feedRepository,
  });
  final UserRepository repository;
  final FeedRepository? feedRepository;

  @override
  State<UserSearchPage> createState() => _UserSearchPageState();
}

class _UserSearchPageState extends State<UserSearchPage> {
  final _query = TextEditingController();
  Timer? _debounce;
  List<Map<String, dynamic>> _items = [];
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _debounce?.cancel();
    _query.dispose();
    super.dispose();
  }

  void _search(String query) {
    _debounce?.cancel();
    if (query.trim().length < 2) {
      setState(() => _items = []);
      return;
    }
    _debounce = Timer(const Duration(milliseconds: 350), () async {
      setState(() => _loading = true);
      try {
        final result = await widget.repository.searchUsers(query.trim());
        if (mounted) {
          setState(() {
            _items = result;
            _error = null;
          });
        }
      } catch (error) {
        if (mounted) setState(() => _error = error.toString());
      } finally {
        if (mounted) setState(() => _loading = false);
      }
    });
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: const AppPageBar(title: 'Tìm kiếm sinh viên'),
    body: Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(16),
          child: TextField(
            controller: _query,
            autofocus: true,
            onChanged: _search,
            decoration: const InputDecoration(
              prefixIcon: Icon(Icons.search),
              hintText: 'Tên, mã sinh viên hoặc username',
            ),
          ),
        ),
        Expanded(
          child: _loading
              ? const Center(child: CircularProgressIndicator())
              : _error != null
              ? _SearchState(icon: Icons.wifi_off_rounded, message: _error!)
              : _items.isEmpty
              ? const Center(
                  child: Text('Nhập ít nhất 2 ký tự để tìm sinh viên.'),
                )
              : ListView.separated(
                  itemCount: _items.length,
                  separatorBuilder: (_, _) => const Divider(height: 1),
                  itemBuilder: (context, index) => _UserTile(
                    user: _items[index],
                    onTap: () => Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => PublicProfilePage(
                          repository: widget.repository,
                          userId: '${_items[index]['id']}',
                          feedRepository: widget.feedRepository,
                        ),
                      ),
                    ),
                  ),
                ),
        ),
      ],
    ),
  );
}

class PublicProfilePage extends StatefulWidget {
  const PublicProfilePage({
    super.key,
    required this.repository,
    required this.userId,
    this.feedRepository,
  });
  final UserRepository repository;
  final String userId;
  final FeedRepository? feedRepository;

  @override
  State<PublicProfilePage> createState() => _PublicProfilePageState();
}

class _PublicProfilePageState extends State<PublicProfilePage> {
  Map<String, dynamic>? _profile;
  bool _busy = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      _profile = await widget.repository.getProfile(widget.userId);
      _error = null;
    } catch (error) {
      _error = error.toString();
    }
    if (mounted) setState(() {});
  }

  Future<void> _friendship(String action) async {
    setState(() => _busy = true);
    try {
      await widget.repository.updateFriendship(widget.userId, action);
      await _load();
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.toString())));
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _block() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Chặn người dùng?'),
        content: const Text(
          'Người này sẽ không thể xem hồ sơ, bài viết hoặc liên hệ với bạn.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Hủy'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(dialogContext, true),
            child: const Text('Chặn'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    await widget.repository.setBlocked(widget.userId, true);
    if (mounted) Navigator.pop(context);
  }

  Widget _friendButton(String status) {
    if (status == 'friends') {
      return OutlinedButton.icon(
        onPressed: _busy ? null : () => _friendship('unfriend'),
        icon: const Icon(Icons.people_alt_outlined),
        label: const Text('Bạn bè'),
      );
    }
    if (status == 'pending_sent') {
      return OutlinedButton(
        onPressed: _busy ? null : () => _friendship('cancel'),
        child: const Text('Đã gửi lời mời'),
      );
    }
    if (status == 'pending_received') {
      return Row(
        children: [
          Expanded(
            child: FilledButton(
              onPressed: _busy ? null : () => _friendship('accept'),
              child: const Text('Chấp nhận'),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: OutlinedButton(
              onPressed: _busy ? null : () => _friendship('reject'),
              child: const Text('Từ chối'),
            ),
          ),
        ],
      );
    }
    return FilledButton.icon(
      onPressed: _busy ? null : () => _friendship('add'),
      icon: const Icon(Icons.person_add_alt_1),
      label: const Text('Thêm bạn bè'),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_profile == null) {
      return Scaffold(
        appBar: const AppPageBar(title: 'Trang cá nhân'),
        body: Center(child: Text(_error ?? 'Đang tải hồ sơ...')),
      );
    }
    final profile = _profile!;
    final rawCover = profile['coverBanner']?.toString() ?? '';
    final hasCover = rawCover.startsWith('http');
    return Scaffold(
      appBar: const AppPageBar(title: 'Trang cá nhân'),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
          children: [
            Card(
              clipBehavior: Clip.antiAlias,
              child: Column(
                children: [
                  GestureDetector(
                    onTap: hasCover
                        ? () => showDialog<void>(
                            context: context,
                            builder: (_) => Dialog(
                              backgroundColor: Colors.black,
                              insetPadding: const EdgeInsets.all(12),
                              child: InteractiveViewer(
                                child: AppNetworkImage(
                                  rawCover,
                                  fit: BoxFit.contain,
                                ),
                              ),
                            ),
                          )
                        : null,
                    child: Container(
                      height: 158,
                      width: double.infinity,
                      decoration: const BoxDecoration(
                        gradient: LinearGradient(
                          colors: [AppTheme.navy, AppTheme.blue],
                        ),
                      ),
                      child: hasCover
                          ? AppNetworkImage(
                              rawCover,
                              fit: BoxFit.cover,
                              errorBuilder: (_, _, _) =>
                                  const SizedBox.shrink(),
                            )
                          : null,
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.fromLTRB(18, 12, 18, 18),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            SizedBox(
                              width: 112,
                              height: 94,
                              child: Stack(
                                clipBehavior: Clip.none,
                                children: [
                                  Positioned(
                                    left: 0,
                                    top: -38,
                                    child: AppAvatar(
                                      radius: 53,
                                      url: profile['avatar']?.toString(),
                                      name: profile['name']?.toString(),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(width: 14),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    '${profile['name']}',
                                    maxLines: 2,
                                    overflow: TextOverflow.ellipsis,
                                    style: const TextStyle(
                                      fontSize: 22,
                                      height: 1.15,
                                      fontWeight: FontWeight.w800,
                                    ),
                                  ),
                                  const SizedBox(height: 8),
                                  Text(
                                    profile['studentCode']
                                                ?.toString()
                                                .isNotEmpty ==
                                            true
                                        ? 'Mã sinh viên: ${profile['studentCode']}'
                                        : '@${profile['username'] ?? ''}',
                                    style: const TextStyle(
                                      color: AppTheme.blue,
                                      fontSize: 12,
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                  if ('${profile['bio'] ?? ''}'
                                      .trim()
                                      .isNotEmpty) ...[
                                    const SizedBox(height: 9),
                                    Text(
                                      '${profile['bio']}',
                                      style: const TextStyle(
                                        color: AppTheme.muted,
                                        fontSize: 13,
                                      ),
                                    ),
                                  ],
                                ],
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        _friendButton(
                          '${profile['friendshipStatus'] ?? 'none'}',
                        ),
                        Align(
                          alignment: Alignment.centerRight,
                          child: TextButton.icon(
                            onPressed: _block,
                            icon: const Icon(Icons.block_outlined, size: 17),
                            label: const Text('Chặn người dùng'),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 4),
            ProfileContentTabs(
              repository: widget.repository,
              feedRepository: widget.feedRepository,
              userId: widget.userId,
              profile: profile,
              onOpenFriends: () => Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => UserFriendsPage(
                    repository: widget.repository,
                    userId: widget.userId,
                    title: 'Bạn bè của ${profile['name'] ?? ''}',
                    feedRepository: widget.feedRepository,
                  ),
                ),
              ),
              onOpenFriend: (id) => Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => PublicProfilePage(
                    repository: widget.repository,
                    userId: id,
                    feedRepository: widget.feedRepository,
                  ),
                ),
              ),
              aboutPanel: Card(
                child: Column(
                  children: [
                    ListTile(
                      leading: const Icon(Icons.group_outlined),
                      title: const Text('Bạn bè'),
                      subtitle: Text(
                        '${profile['friendsCount'] ?? 0} người bạn',
                      ),
                      trailing: const Icon(Icons.chevron_right),
                      onTap: () => Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => UserFriendsPage(
                            repository: widget.repository,
                            userId: widget.userId,
                            title: 'Bạn bè của ${profile['name'] ?? ''}',
                            feedRepository: widget.feedRepository,
                          ),
                        ),
                      ),
                    ),
                    ListTile(
                      leading: const Icon(Icons.school_outlined),
                      title: const Text('Học vấn'),
                      subtitle: Text(
                        '${profile['education'] ?? 'Học viện Ngân hàng (BAV)'}',
                      ),
                    ),
                    if ('${profile['faculty'] ?? ''}'.isNotEmpty)
                      ListTile(
                        leading: const Icon(Icons.account_balance_outlined),
                        title: const Text('Khoa / Viện'),
                        subtitle: Text('${profile['faculty']}'),
                      ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class UserFriendsPage extends StatefulWidget {
  const UserFriendsPage({
    super.key,
    required this.repository,
    required this.userId,
    required this.title,
    this.feedRepository,
  });

  final UserRepository repository;
  final String userId;
  final String title;
  final FeedRepository? feedRepository;

  @override
  State<UserFriendsPage> createState() => _UserFriendsPageState();
}

class _UserFriendsPageState extends State<UserFriendsPage> {
  List<Map<String, dynamic>> _users = [];
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      _users = await widget.repository.getFriends(widget.userId);
      _error = null;
    } catch (error) {
      _error = error.toString();
    }
    if (mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppPageBar(title: widget.title),
    body: _error != null
        ? Center(child: Text(_error!))
        : _users.isEmpty
        ? const Center(child: Text('Chưa có bạn bè để hiển thị.'))
        : RefreshIndicator(
            onRefresh: _load,
            child: ListView.separated(
              itemCount: _users.length,
              separatorBuilder: (_, _) => const Divider(height: 1),
              itemBuilder: (context, index) => _UserTile(
                user: _users[index],
                onTap: () => Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => PublicProfilePage(
                      repository: widget.repository,
                      userId: '${_users[index]['id']}',
                      feedRepository: widget.feedRepository,
                    ),
                  ),
                ),
              ),
            ),
          ),
  );
}

class BlockedUsersPage extends StatefulWidget {
  const BlockedUsersPage({super.key, required this.repository});
  final UserRepository repository;

  @override
  State<BlockedUsersPage> createState() => _BlockedUsersPageState();
}

class _BlockedUsersPageState extends State<BlockedUsersPage> {
  List<Map<String, dynamic>> _users = [];
  bool _loading = true;
  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      _users = await widget.repository.getBlockedUsers();
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: const AppPageBar(title: 'Danh sách đã chặn'),
    body: _loading
        ? const Center(child: CircularProgressIndicator())
        : _users.isEmpty
        ? const Center(child: Text('Bạn chưa chặn người dùng nào.'))
        : ListView.separated(
            itemCount: _users.length,
            separatorBuilder: (_, _) => const Divider(height: 1),
            itemBuilder: (context, index) {
              final user = _users[index];
              return _UserTile(
                user: user,
                trailing: TextButton(
                  onPressed: () async {
                    await widget.repository.setBlocked('${user['id']}', false);
                    await _load();
                  },
                  child: const Text('Bỏ chặn'),
                ),
              );
            },
          ),
  );
}

class _UserTile extends StatelessWidget {
  const _UserTile({required this.user, this.onTap, this.trailing});
  final Map<String, dynamic> user;
  final VoidCallback? onTap;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      onTap: onTap,
      leading: AppAvatar(
        url: user['avatar']?.toString() ?? user['avatar_url']?.toString(),
        name: user['name']?.toString() ?? user['full_name']?.toString(),
      ),
      title: Text(
        '${user['name'] ?? user['full_name'] ?? user['username'] ?? 'Sinh viên HVNH'}',
      ),
      subtitle: Text(
        user['studentCode']?.toString().isNotEmpty == true
            ? 'Mã SV: ${user['studentCode']}'
            : '@${user['username'] ?? ''}',
      ),
      trailing: trailing,
    );
  }
}

class _SearchState extends StatelessWidget {
  const _SearchState({required this.icon, required this.message});

  final IconData icon;
  final String message;

  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(28),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 42, color: const Color(0xff7890aa)),
          const SizedBox(height: 12),
          Text(message, textAlign: TextAlign.center),
        ],
      ),
    ),
  );
}
