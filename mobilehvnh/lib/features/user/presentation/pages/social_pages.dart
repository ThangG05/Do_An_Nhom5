import 'dart:async';

import 'package:flutter/material.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/app_avatar.dart';
import '../../../../core/widgets/app_page_bar.dart';
import '../../../../core/widgets/app_network_image.dart';
import '../../domain/repositories/user_repository.dart';
import '../../../feed/domain/repositories/feed_repository.dart';
import '../../../chat/domain/repositories/chat_repository.dart';
import '../../../chat/chat_page.dart' show ConversationPage;
import '../widgets/profile_content_tabs.dart';

class UserSearchPage extends StatefulWidget {
  const UserSearchPage({
    super.key,
    required this.repository,
    this.feedRepository,
    this.chatRepository,
  });
  final UserRepository repository;
  final FeedRepository? feedRepository;
  final ChatRepository? chatRepository;

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
                          chatRepository: widget.chatRepository,
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
    this.chatRepository,
  });
  final UserRepository repository;
  final String userId;
  final FeedRepository? feedRepository;
  final ChatRepository? chatRepository;

  @override
  State<PublicProfilePage> createState() => _PublicProfilePageState();
}

class _PublicProfilePageState extends State<PublicProfilePage> {
  Map<String, dynamic>? _profile;
  bool _busy = false;
  bool _openingChat = false;
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

  Future<void> _message() async {
    final chat = widget.chatRepository;
    if (chat == null || _openingChat) return;
    setState(() => _openingChat = true);
    try {
      final conversation = await chat.createDirectConversation(widget.userId);
      if (!mounted) return;
      await Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => ConversationPage(
            conversation: conversation,
            repository: chat,
            userRepository: widget.repository,
            feedRepository: widget.feedRepository,
          ),
        ),
      );
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.toString())));
      }
    } finally {
      if (mounted) setState(() => _openingChat = false);
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
      return FilledButton.icon(
        onPressed: _busy ? null : _showFriendOptions,
        icon: const Icon(Icons.people_alt_rounded),
        label: const Text('Bạn bè'),
        style: FilledButton.styleFrom(
          backgroundColor: AppTheme.blue,
          foregroundColor: Colors.white,
        ),
      );
    }
    if (status == 'pending_sent') {
      return OutlinedButton.icon(
        onPressed: _busy ? null : () => _friendship('cancel'),
        icon: const Icon(Icons.person_add_alt_1),
        label: const Text('Đã gửi lời mời'),
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

  Future<void> _showFriendOptions() async {
    final remove = await showModalBottomSheet<bool>(
      context: context,
      builder: (sheetContext) => SafeArea(
        child: ListTile(
          leading: const Icon(Icons.person_remove_outlined, color: Colors.red),
          title: const Text('Hủy kết bạn'),
          onTap: () => Navigator.pop(sheetContext, true),
        ),
      ),
    );
    if (remove == true && mounted) await _friendship('unfriend');
  }

  Widget _infoLine(IconData icon, String label, String value) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 7),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 19, color: AppTheme.muted),
        const SizedBox(width: 12),
        Expanded(
          child: Text.rich(
            TextSpan(
              style: const TextStyle(color: AppTheme.ink, height: 1.4),
              children: [
                TextSpan(text: '$label '),
                TextSpan(
                  text: value,
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
              ],
            ),
          ),
        ),
      ],
    ),
  );

  Widget _personalInformation(Map<String, dynamic> profile) {
    final rows = <Widget>[];
    final city = '${profile['currentCity'] ?? ''}'.trim();
    final hometown = '${profile['hometown'] ?? ''}'.trim();
    final workplace = '${profile['workplace'] ?? ''}'.trim();
    final education = '${profile['education'] ?? ''}'.trim();
    final faculty = '${profile['faculty'] ?? ''}'.trim();
    final links = profile['socialLinks'] is Map
        ? Map<String, dynamic>.from(profile['socialLinks'] as Map)
        : <String, dynamic>{};
    final socialRows = links.entries
        .where((entry) => '${entry.value}'.trim().isNotEmpty)
        .toList();
    if (city.isNotEmpty) rows.add(_infoLine(Icons.location_on, 'Sống tại', city));
    if (hometown.isNotEmpty) rows.add(_infoLine(Icons.home, 'Đến từ', hometown));
    final joinedAt = DateTime.tryParse('${profile['joinedDate'] ?? ''}');
    if (joinedAt != null) {
      rows.add(_infoLine(Icons.access_time, 'Tham gia từ',
          '${joinedAt.day.toString().padLeft(2, '0')}/${joinedAt.month.toString().padLeft(2, '0')}/${joinedAt.year}'));
    }
    if (education.isNotEmpty) rows.add(_infoLine(Icons.school, 'Học tại', education));
    if (faculty.isNotEmpty) rows.add(_infoLine(Icons.school_outlined, 'Khoa', faculty));
    if (workplace.isNotEmpty) rows.add(_infoLine(Icons.work_outline, 'Làm việc tại', workplace));
    if (rows.isEmpty && socialRows.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
      child: Card(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 14, 16, 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Thông tin cá nhân', style: TextStyle(
                color: AppTheme.ink, fontSize: 17, fontWeight: FontWeight.w800,
              )),
              const SizedBox(height: 8),
              ...rows,
              if (socialRows.isNotEmpty) ...[
                if (rows.isNotEmpty) const Divider(height: 20),
                const Text('Kết nối', style: TextStyle(
                  color: AppTheme.ink, fontWeight: FontWeight.w800,
                )),
                const SizedBox(height: 4),
                ...socialRows.map((entry) => _infoLine(
                  Icons.alternate_email,
                  '${entry.key}:',
                  '${entry.value}',
                )),
              ],
            ],
          ),
        ),
      ),
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
    final name = '${profile['name'] ?? 'Trang cá nhân'}';
    final status = '${profile['friendshipStatus'] ?? 'none'}';
    final friendCount = profile['friendsCount'] ?? 0;
    final mutualCount = profile['mutualFriendsCount'] ?? 0;
    return Scaffold(
      appBar: AppPageBar(
        title: name,
        actions: [
          IconButton(
            tooltip: 'Tìm sinh viên',
            onPressed: () => Navigator.of(context).push(MaterialPageRoute(
              builder: (_) => UserSearchPage(
                repository: widget.repository,
                feedRepository: widget.feedRepository,
                chatRepository: widget.chatRepository,
              ),
            )),
            icon: const Icon(Icons.search_rounded),
          ),
          PopupMenuButton<String>(
            tooltip: 'Tùy chọn',
            onSelected: (_) => _block(),
            itemBuilder: (_) => const [
              PopupMenuItem(value: 'block', child: Text('Chặn người dùng')),
            ],
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          physics: const BouncingScrollPhysics(
            parent: AlwaysScrollableScrollPhysics(),
          ),
          padding: const EdgeInsets.only(bottom: 28),
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
                      height: 190,
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
                    padding: const EdgeInsets.fromLTRB(18, 0, 18, 16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        SizedBox(
                          height: 58,
                          child: Stack(
                            clipBehavior: Clip.none,
                            children: [
                              Positioned(
                                top: -58,
                                left: 0,
                                right: 0,
                                child: Center(
                                  child: AppAvatar(
                                    radius: 58,
                                    url: profile['avatar']?.toString(),
                                    name: name,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                        Text(
                          name,
                          textAlign: TextAlign.center,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            color: AppTheme.ink,
                            fontSize: 23,
                            height: 1.15,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        const SizedBox(height: 5),
                        Text(
                          mutualCount is num && mutualCount > 0
                              ? '$friendCount người bạn · $mutualCount bạn chung'
                              : '$friendCount người bạn',
                          textAlign: TextAlign.center,
                          style: const TextStyle(
                            color: AppTheme.muted,
                            fontSize: 13,
                          ),
                        ),
                        if (profile['studentCode']?.toString().isNotEmpty == true) ...[
                          const SizedBox(height: 4),
                          Text(
                            '${profile['studentCode']}',
                            textAlign: TextAlign.center,
                            style: const TextStyle(
                              color: AppTheme.muted,
                              fontSize: 12,
                            ),
                          ),
                        ],
                        if ('${profile['bio'] ?? ''}'.trim().isNotEmpty) ...[
                          const SizedBox(height: 8),
                          Text(
                            '${profile['bio']}',
                            textAlign: TextAlign.center,
                            style: const TextStyle(
                              color: AppTheme.ink,
                              fontSize: 14,
                            ),
                          ),
                        ],
                        const SizedBox(height: 16),
                        if (status == 'pending_received') ...[
                          _friendButton(status),
                          if (widget.chatRepository != null) ...[
                            const SizedBox(height: 8),
                            OutlinedButton.icon(
                              onPressed: _openingChat ? null : _message,
                              icon: const Icon(Icons.chat_bubble_outline),
                              label: const Text('Nhắn tin'),
                            ),
                          ],
                        ] else if (status != 'self')
                          Row(
                            children: [
                              Expanded(child: _friendButton(status)),
                              if (widget.chatRepository != null) ...[
                                const SizedBox(width: 9),
                                Expanded(
                                  child: OutlinedButton.icon(
                                    onPressed: _openingChat ? null : _message,
                                    icon: _openingChat
                                        ? const SizedBox.square(
                                            dimension: 16,
                                            child: CircularProgressIndicator(strokeWidth: 2),
                                          )
                                        : const Icon(Icons.chat_bubble_outline),
                                    label: const Text('Nhắn tin'),
                                  ),
                                ),
                              ],
                            ],
                          ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            _personalInformation(profile),
            const SizedBox(height: 12),
            ProfileContentTabs(
              repository: widget.repository,
              feedRepository: widget.feedRepository,
              chatRepository: widget.chatRepository,
              userId: widget.userId,
              profile: profile,
              onOpenFriends: () => Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => UserFriendsPage(
                    repository: widget.repository,
                    userId: widget.userId,
                    title: 'Bạn bè của ${profile['name'] ?? ''}',
                    feedRepository: widget.feedRepository,
                    chatRepository: widget.chatRepository,
                  ),
                ),
              ),
              onOpenFriend: (id) => Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => PublicProfilePage(
                    repository: widget.repository,
                    userId: id,
                    feedRepository: widget.feedRepository,
                    chatRepository: widget.chatRepository,
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
                            chatRepository: widget.chatRepository,
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
    this.chatRepository,
  });

  final UserRepository repository;
  final String userId;
  final String title;
  final FeedRepository? feedRepository;
  final ChatRepository? chatRepository;

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
                      chatRepository: widget.chatRepository,
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
