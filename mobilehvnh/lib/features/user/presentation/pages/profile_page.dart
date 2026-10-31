import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../../../../core/utils/app_date_time.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/app_avatar.dart';
import '../../../../core/widgets/app_page_bar.dart';
import '../../../../core/widgets/app_network_image.dart';
import '../../domain/entities/avatar_upload_file.dart';
import '../../domain/repositories/user_repository.dart';
import '../../../feed/domain/repositories/feed_repository.dart';
import 'social_pages.dart';
import '../widgets/profile_content_tabs.dart';

class ProfilePage extends StatefulWidget {
  const ProfilePage({super.key, required this.repository, this.feedRepository});

  final UserRepository repository;
  final FeedRepository? feedRepository;

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  Map<String, dynamic>? _profile;
  String? _error;
  bool _updatingAvatar = false;
  bool _updatingCover = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      _profile = await widget.repository.getMyProfile();
      _error = null;
    } catch (error) {
      _error = error.toString();
    }
    if (mounted) setState(() {});
  }

  Future<void> _edit() async {
    if (_profile == null) return;
    final name = TextEditingController(text: _profile!['name']?.toString());
    final bio = TextEditingController(text: _profile!['bio']?.toString());
    final saved = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      builder: (sheetContext) => Padding(
        padding: EdgeInsets.fromLTRB(
          20,
          20,
          20,
          20 + MediaQuery.of(sheetContext).viewInsets.bottom,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Chỉnh sửa hồ sơ',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: name,
              decoration: const InputDecoration(labelText: 'Họ và tên'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: bio,
              maxLines: 4,
              decoration: const InputDecoration(labelText: 'Giới thiệu'),
            ),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: () => Navigator.pop(sheetContext, true),
              child: const Text('Lưu thay đổi'),
            ),
          ],
        ),
      ),
    );
    if (saved == true) {
      try {
        await widget.repository.updateMyProfile({
          'name': name.text.trim(),
          'bio': bio.text.trim(),
        });
        await _load();
      } finally {
        name.dispose();
        bio.dispose();
      }
    } else {
      name.dispose();
      bio.dispose();
    }
  }

  Future<void> _pickAvatar() async {
    if (_updatingAvatar) return;
    final selected = await FilePicker.platform.pickFiles(
      type: FileType.image,
      withData: true,
    );
    final file = selected?.files.singleOrNull;
    if (file == null) return;
    setState(() => _updatingAvatar = true);
    try {
      await widget.repository.updateMyAvatar(
        AvatarUploadFile(
          name: file.name,
          size: file.size,
          path: file.path,
          bytes: file.bytes,
        ),
      );
      await _load();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Đã cập nhật ảnh đại diện.')),
        );
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.toString())));
      }
    } finally {
      if (mounted) setState(() => _updatingAvatar = false);
    }
  }

  Future<void> _pickCover() async {
    if (_updatingCover) return;
    final selected = await FilePicker.platform.pickFiles(
      type: FileType.image,
      withData: true,
    );
    final file = selected?.files.singleOrNull;
    if (file == null) return;
    setState(() => _updatingCover = true);
    try {
      await widget.repository.updateMyCover(
        AvatarUploadFile(
          name: file.name,
          size: file.size,
          path: file.path,
          bytes: file.bytes,
        ),
      );
      await _load();
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('Đã cập nhật ảnh bìa.')));
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.toString())));
      }
    } finally {
      if (mounted) setState(() => _updatingCover = false);
    }
  }

  Future<void> _showAvatarActions() async {
    if (_profile == null) return;
    final url = _profile!['avatar']?.toString() ?? '';
    await showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (sheetContext) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 4, 20, 20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                'Ảnh đại diện',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 16),
              Center(
                child: AppAvatar(
                  radius: 76,
                  url: url,
                  name: _profile!['name']?.toString(),
                ),
              ),
              const SizedBox(height: 18),
              if (url.startsWith('http'))
                OutlinedButton.icon(
                  onPressed: () {
                    Navigator.pop(sheetContext);
                    showDialog<void>(
                      context: context,
                      builder: (_) => Dialog(
                        backgroundColor: Colors.black,
                        insetPadding: const EdgeInsets.all(12),
                        child: InteractiveViewer(
                          child: AppNetworkImage(url, fit: BoxFit.contain),
                        ),
                      ),
                    );
                  },
                  icon: const Icon(Icons.visibility_outlined),
                  label: const Text('Xem ảnh đại diện'),
                ),
              FilledButton.icon(
                onPressed: _updatingAvatar
                    ? null
                    : () {
                        Navigator.pop(sheetContext);
                        _pickAvatar();
                      },
                icon: const Icon(Icons.photo_camera_outlined),
                label: const Text('Chọn ảnh mới'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _showCoverActions() async {
    if (_profile == null) return;
    final url = _profile!['coverBanner']?.toString() ?? '';
    await showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (sheetContext) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 4, 20, 20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                'Ảnh bìa',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800),
              ),
              if (url.startsWith('http')) ...[
                const SizedBox(height: 14),
                ClipRRect(
                  borderRadius: BorderRadius.circular(16),
                  child: AppNetworkImage(
                    url,
                    height: 170,
                    width: double.infinity,
                    fit: BoxFit.cover,
                  ),
                ),
                const SizedBox(height: 14),
                OutlinedButton.icon(
                  onPressed: () {
                    Navigator.pop(sheetContext);
                    showDialog<void>(
                      context: context,
                      builder: (_) => Dialog(
                        backgroundColor: Colors.black,
                        insetPadding: const EdgeInsets.all(12),
                        child: InteractiveViewer(
                          child: AppNetworkImage(url, fit: BoxFit.contain),
                        ),
                      ),
                    );
                  },
                  icon: const Icon(Icons.visibility_outlined),
                  label: const Text('Xem ảnh bìa'),
                ),
              ],
              FilledButton.icon(
                onPressed: _updatingCover
                    ? null
                    : () {
                        Navigator.pop(sheetContext);
                        _pickCover();
                      },
                icon: const Icon(Icons.photo_camera_outlined),
                label: const Text('Đổi ảnh bìa'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _changePassword() async {
    final current = TextEditingController();
    final next = TextEditingController();
    final confirm = TextEditingController();
    final saved = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      builder: (sheetContext) => Padding(
        padding: EdgeInsets.fromLTRB(
          20,
          20,
          20,
          20 + MediaQuery.of(sheetContext).viewInsets.bottom,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Đổi mật khẩu',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 8),
            const Text(
              'Mật khẩu mới có ít nhất 8 ký tự, gồm chữ cái và chữ số.',
            ),
            const SizedBox(height: 16),
            TextField(
              controller: current,
              obscureText: true,
              decoration: const InputDecoration(labelText: 'Mật khẩu hiện tại'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: next,
              obscureText: true,
              decoration: const InputDecoration(labelText: 'Mật khẩu mới'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: confirm,
              obscureText: true,
              decoration: const InputDecoration(
                labelText: 'Nhập lại mật khẩu mới',
              ),
            ),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: () => Navigator.pop(sheetContext, true),
              child: const Text('Cập nhật mật khẩu'),
            ),
          ],
        ),
      ),
    );
    if (saved != true) {
      current.dispose();
      next.dispose();
      confirm.dispose();
      return;
    }
    try {
      if (next.text.length < 8 || next.text != confirm.text) {
        throw Exception('Mật khẩu mới chưa hợp lệ hoặc không khớp.');
      }
      await widget.repository.changePassword(
        currentPassword: current.text,
        newPassword: next.text,
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Đã đổi mật khẩu thành công.')),
        );
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.toString())));
      }
    } finally {
      current.dispose();
      next.dispose();
      confirm.dispose();
    }
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
    final rawAvatar = profile['avatar']?.toString() ?? '';
    final rawCover = profile['coverBanner']?.toString() ?? '';
    final hasCover = rawCover.startsWith('http');
    final joined = profile['joinedDate']?.toString() ?? '';
    return Scaffold(
      appBar: const AppPageBar(title: 'Trang cá nhân'),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(14, 15, 14, 30),
          children: [
            Card(
              clipBehavior: Clip.antiAlias,
              child: Column(
                children: [
                  Stack(
                    children: [
                      Ink(
                        height: 158,
                        width: double.infinity,
                        decoration: BoxDecoration(
                          gradient: const LinearGradient(
                            colors: [Color(0xff071e36), Color(0xff155784)],
                          ),
                        ),
                        child: Stack(
                          fit: StackFit.expand,
                          children: [
                            if (hasCover)
                              AppNetworkImage(
                                rawCover,
                                fit: BoxFit.cover,
                                errorBuilder: (_, _, _) =>
                                    const SizedBox.shrink(),
                              ),
                            InkWell(
                              onTap: _updatingCover ? null : _showCoverActions,
                              child: DecoratedBox(
                                decoration: BoxDecoration(
                                  gradient: LinearGradient(
                                    begin: Alignment.topCenter,
                                    end: Alignment.bottomCenter,
                                    colors: [
                                      Colors.transparent,
                                      const Color(
                                        0xff062f59,
                                      ).withValues(alpha: .30),
                                    ],
                                  ),
                                ),
                                child: const SizedBox.expand(),
                              ),
                            ),
                          ],
                        ),
                      ),
                      Positioned(
                        right: 10,
                        bottom: 10,
                        child: FilledButton.tonalIcon(
                          onPressed: _updatingCover ? null : _pickCover,
                          icon: _updatingCover
                              ? const SizedBox(
                                  width: 15,
                                  height: 15,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                  ),
                                )
                              : const Icon(
                                  Icons.photo_camera_outlined,
                                  size: 18,
                                ),
                          label: const Text('Đổi ảnh bìa'),
                        ),
                      ),
                    ],
                  ),
                  Padding(
                    padding: const EdgeInsets.fromLTRB(18, 12, 18, 20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            SizedBox(
                              width: 112,
                              height: 94,
                              child: Align(
                                alignment: Alignment.topLeft,
                                child: Transform.translate(
                                  offset: const Offset(0, -35),
                                  child: Semantics(
                                    button: true,
                                    label: 'Xem hoặc đổi ảnh đại diện',
                                    child: AppAvatar(
                                      radius: 53,
                                      url: rawAvatar,
                                      name: profile['name']?.toString(),
                                      onTap: _updatingAvatar
                                          ? null
                                          : _showAvatarActions,
                                      heroTag: 'my-profile-avatar',
                                    ),
                                  ),
                                ),
                              ),
                            ),
                            const SizedBox(width: 14),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    '${profile['name'] ?? ''}',
                                    maxLines: 2,
                                    overflow: TextOverflow.ellipsis,
                                    style: const TextStyle(
                                      fontSize: 22,
                                      height: 1.15,
                                      color: AppTheme.ink,
                                      fontWeight: FontWeight.w800,
                                    ),
                                  ),
                                  const SizedBox(height: 8),
                                  Text(
                                    'Mã sinh viên: ${profile['studentCode'] ?? 'Chưa cập nhật'}',
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
                        OutlinedButton.icon(
                          onPressed: _edit,
                          icon: const Icon(Icons.edit_outlined, size: 17),
                          label: const Text('Chỉnh sửa trang cá nhân'),
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
              userId: '${profile['id']}',
              profile: profile,
              onOpenFriends: () => Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => UserFriendsPage(
                    repository: widget.repository,
                    userId: '${profile['id']}',
                    title: 'Bạn bè của tôi',
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
                      leading: const Icon(Icons.school_outlined),
                      title: const Text('Học vấn'),
                      subtitle: Text(
                        '${profile['education'] ?? 'Học viện Ngân hàng (BAV)'}',
                      ),
                    ),
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
                            userId: '${profile['id']}',
                            title: 'Bạn bè của tôi',
                            feedRepository: widget.feedRepository,
                          ),
                        ),
                      ),
                    ),
                    ListTile(
                      leading: const Icon(
                        Icons.photo_size_select_large_outlined,
                      ),
                      title: const Text('Ảnh bìa'),
                      subtitle: const Text(
                        'Chọn ảnh để cá nhân hóa trang cá nhân',
                      ),
                      trailing: _updatingCover
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.chevron_right),
                      onTap: _updatingCover ? null : _pickCover,
                    ),
                    ListTile(
                      leading: const Icon(Icons.calendar_today_outlined),
                      title: const Text('Tham gia HVNH Hub'),
                      subtitle: Text(
                        joined.isEmpty
                            ? 'Chưa cập nhật'
                            : AppDateTime.full(joined).split(' · ').last,
                      ),
                    ),
                    ListTile(
                      leading: const Icon(Icons.block_outlined),
                      title: const Text('Danh sách đã chặn'),
                      trailing: const Icon(Icons.chevron_right),
                      onTap: () => Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) =>
                              BlockedUsersPage(repository: widget.repository),
                        ),
                      ),
                    ),
                    ListTile(
                      leading: const Icon(Icons.lock_outline),
                      title: const Text('Đổi mật khẩu'),
                      subtitle: const Text('Bảo vệ tài khoản của bạn'),
                      trailing: const Icon(Icons.chevron_right),
                      onTap: _changePassword,
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
