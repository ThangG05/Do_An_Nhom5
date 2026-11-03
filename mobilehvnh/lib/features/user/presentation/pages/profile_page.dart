import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../../../../core/utils/app_date_time.dart';
import '../../../../core/utils/platform_file_utils.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/app_avatar.dart';
import '../../../../core/widgets/app_page_bar.dart';
import '../../../../core/widgets/app_network_image.dart';
import '../../domain/entities/avatar_upload_file.dart';
import '../../domain/repositories/user_repository.dart';
import '../../../feed/domain/repositories/feed_repository.dart';
import '../../../chat/domain/repositories/chat_repository.dart';
import 'social_pages.dart';
import '../widgets/profile_content_tabs.dart';

class ProfilePage extends StatefulWidget {
  const ProfilePage({
    super.key,
    required this.repository,
    this.feedRepository,
    this.chatRepository,
    this.onPasswordChanged,
  });

  final UserRepository repository;
  final FeedRepository? feedRepository;
  final ChatRepository? chatRepository;
  final Future<void> Function()? onPasswordChanged;

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  static const _faculties = [
    'Khoa Ngân hàng',
    'Khoa Tài chính',
    'Khoa Kế toán - Kiểm toán',
    'Khoa Quản trị kinh doanh',
    'Khoa Kinh doanh quốc tế',
    'Khoa Công nghệ thông tin và Kinh tế số',
    'Khoa Ngoại ngữ',
    'Khoa Luật',
    'Khoa Kinh tế',
    'Viện Đào tạo quốc tế',
  ];
  static const _provinces = [
    'Hà Nội', 'Cao Bằng', 'Tuyên Quang', 'Điện Biên', 'Lai Châu', 'Sơn La',
    'Lào Cai', 'Thái Nguyên', 'Lạng Sơn', 'Quảng Ninh', 'Bắc Ninh', 'Phú Thọ',
    'Hải Phòng', 'Hưng Yên', 'Ninh Bình', 'Thanh Hóa', 'Nghệ An', 'Hà Tĩnh',
    'Quảng Trị', 'Huế', 'Đà Nẵng', 'Quảng Ngãi', 'Gia Lai', 'Khánh Hòa',
    'Đắk Lắk', 'Lâm Đồng', 'Đồng Nai', 'Thành phố Hồ Chí Minh', 'Tây Ninh',
    'Đồng Tháp', 'Vĩnh Long', 'An Giang', 'Cần Thơ', 'Cà Mau',
  ];

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
    final pronouns = TextEditingController(text: _profile!['pronouns']?.toString());
    final workplace = TextEditingController(text: _profile!['workplace']?.toString());
    final facebook = TextEditingController(text: _socialLink('facebook'));
    final instagram = TextEditingController(text: _socialLink('instagram'));
    final linkedin = TextEditingController(text: _socialLink('linkedin'));
    var faculty = _profile!['faculty']?.toString() ?? '';
    var currentCity = _profile!['currentCity']?.toString() ?? '';
    var hometown = _profile!['hometown']?.toString() ?? '';
    final saved = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: Theme.of(context).colorScheme.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (sheetContext) => SizedBox(
          height: (MediaQuery.sizeOf(sheetContext).height -
                  MediaQuery.of(sheetContext).viewInsets.bottom) *
              .88,
          child: StatefulBuilder(
            builder: (context, setSheetState) => Column(
              children: [
                const Padding(
                  padding: EdgeInsets.only(top: 10, bottom: 8),
                  child: SizedBox(width: 38, child: Divider(thickness: 3)),
                ),
                const Padding(
                  padding: EdgeInsets.fromLTRB(20, 8, 20, 12),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: Text('Chỉnh sửa hồ sơ', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
                  ),
                ),
                Expanded(
                  child: ListView(
                    padding: const EdgeInsets.fromLTRB(20, 0, 20, 16),
                    keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
                    children: [
                      _editSection('Thông tin cơ bản'),
                      TextField(controller: name, maxLength: 150, decoration: const InputDecoration(labelText: 'Họ và tên')),
                      const SizedBox(height: 10),
                      TextField(controller: pronouns, maxLength: 50, decoration: const InputDecoration(labelText: 'Danh xưng / Pronouns', hintText: 'she/her, he/him...')),
                      const SizedBox(height: 10),
                      TextField(controller: bio, maxLength: 150, maxLines: 3, decoration: const InputDecoration(labelText: 'Tiểu sử')),
                      _editSection('Học vấn & công việc'),
                      DropdownButtonFormField<String>(
                        value: _dropdownValue(faculty, _faculties),
                        decoration: const InputDecoration(labelText: 'Khoa / Chuyên ngành'),
                        items: _dropdownItems(faculty, _faculties, 'Chọn khoa/chuyên ngành'),
                        onChanged: (value) => setSheetState(() => faculty = value ?? ''),
                      ),
                      const SizedBox(height: 10),
                      TextFormField(initialValue: 'Học viện Ngân hàng (BAV)', readOnly: true, decoration: const InputDecoration(labelText: 'Trường đại học')),
                      const SizedBox(height: 10),
                      TextFormField(initialValue: _courseYear(), readOnly: true, decoration: const InputDecoration(labelText: 'Khóa học', helperText: 'Tự xác định từ mã sinh viên.')),
                      const SizedBox(height: 10),
                      TextField(controller: workplace, maxLength: 150, decoration: const InputDecoration(labelText: 'Nơi làm việc / CLB')),
                      _editSection('Tỉnh / Thành phố'),
                      DropdownButtonFormField<String>(
                        value: _dropdownValue(currentCity, _provinces),
                        decoration: const InputDecoration(labelText: 'Nơi ở hiện tại'),
                        items: _dropdownItems(currentCity, _provinces, 'Chọn tỉnh/thành phố'),
                        onChanged: (value) => setSheetState(() => currentCity = value ?? ''),
                      ),
                      const SizedBox(height: 10),
                      DropdownButtonFormField<String>(
                        value: _dropdownValue(hometown, _provinces),
                        decoration: const InputDecoration(labelText: 'Quê quán'),
                        items: _dropdownItems(hometown, _provinces, 'Chọn tỉnh/thành phố'),
                        onChanged: (value) => setSheetState(() => hometown = value ?? ''),
                      ),
                      _editSection('Liên kết mạng xã hội'),
                      TextField(controller: facebook, keyboardType: TextInputType.url, decoration: const InputDecoration(labelText: 'Facebook URL', hintText: 'https://facebook.com/...')),
                      const SizedBox(height: 10),
                      TextField(controller: instagram, keyboardType: TextInputType.url, decoration: const InputDecoration(labelText: 'Instagram URL', hintText: 'https://instagram.com/...')),
                      const SizedBox(height: 10),
                      TextField(controller: linkedin, keyboardType: TextInputType.url, decoration: const InputDecoration(labelText: 'LinkedIn URL', hintText: 'https://linkedin.com/in/...')),
                    ],
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.fromLTRB(20, 8, 20, 16),
                  child: SizedBox(
                    width: double.infinity,
                    child: FilledButton(
                      onPressed: () => Navigator.pop(sheetContext, true),
                      child: const Text('Lưu thay đổi'),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
    );
    if (saved == true) {
      try {
        await widget.repository.updateMyProfile({
          'name': name.text.trim(),
          'bio': bio.text.trim(),
          'pronouns': pronouns.text.trim(),
          'faculty': faculty,
          'workplace': workplace.text.trim(),
          'currentCity': currentCity,
          'hometown': hometown,
          'socialLinks': {
            'facebook': _normalizeUrl(facebook.text),
            'instagram': _normalizeUrl(instagram.text),
            'linkedin': _normalizeUrl(linkedin.text),
          },
        });
        await _load();
      } finally {
        name.dispose();
        bio.dispose();
        pronouns.dispose();
        workplace.dispose();
        facebook.dispose();
        instagram.dispose();
        linkedin.dispose();
      }
    } else {
      name.dispose();
      bio.dispose();
      pronouns.dispose();
      workplace.dispose();
      facebook.dispose();
      instagram.dispose();
      linkedin.dispose();
    }
  }

  String _socialLink(String key) {
    final links = _profile?['socialLinks'];
    return links is Map ? links[key]?.toString() ?? '' : '';
  }

  String _courseYear() {
    final code = _profile?['studentCode']?.toString() ?? '';
    final match = RegExp(r'^(\d{2})').firstMatch(code.trim());
    if (match == null) return _profile?['courseYear']?.toString() ?? '';
    final cohort = int.tryParse(match.group(1)!);
    if (cohort == null || cohort < 18 || cohort > 60) return '';
    final start = 1997 + cohort;
    return 'K$cohort ($start-${start + 4})';
  }

  String? _dropdownValue(String value, List<String> options) =>
      value.isNotEmpty && options.contains(value) ? value : null;

  List<DropdownMenuItem<String>> _dropdownItems(
    String value,
    List<String> options,
    String prompt,
  ) => [
    DropdownMenuItem<String>(value: '', child: Text(prompt)),
    if (value.isNotEmpty && !options.contains(value))
      DropdownMenuItem<String>(value: value, child: Text(value)),
    ...options.map((option) => DropdownMenuItem(value: option, child: Text(option))),
  ];

  Widget _editSection(String title) => Padding(
    padding: const EdgeInsets.only(top: 20, bottom: 10),
    child: Text(title, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
  );

  String _normalizeUrl(String value) {
    final trimmed = value.trim();
    if (trimmed.isEmpty || RegExp(r'^https?://', caseSensitive: false).hasMatch(trimmed)) return trimmed;
    return 'https://$trimmed';
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
          path: platformFilePath(file),
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
          path: platformFilePath(file),
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
    var hideCurrent = true;
    var hideNext = true;
    var hideConfirm = true;
    final saved = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
    builder: (sheetContext) => StatefulBuilder(
      builder: (context, setSheetState) => Padding(
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
              obscureText: hideCurrent,
              decoration: InputDecoration(
                labelText: 'Mật khẩu hiện tại',
                suffixIcon: IconButton(
                  tooltip: 'Hiện/ẩn mật khẩu hiện tại',
                  onPressed: () => setSheetState(() => hideCurrent = !hideCurrent),
                  icon: Icon(hideCurrent ? Icons.visibility_outlined : Icons.visibility_off_outlined),
                ),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: next,
              obscureText: hideNext,
              decoration: InputDecoration(
                labelText: 'Mật khẩu mới',
                suffixIcon: IconButton(
                  tooltip: 'Hiện/ẩn mật khẩu mới',
                  onPressed: () => setSheetState(() => hideNext = !hideNext),
                  icon: Icon(hideNext ? Icons.visibility_outlined : Icons.visibility_off_outlined),
                ),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: confirm,
              obscureText: hideConfirm,
              decoration: InputDecoration(
                labelText: 'Nhập lại mật khẩu mới',
                suffixIcon: IconButton(
                  tooltip: 'Hiện/ẩn mật khẩu xác nhận',
                  onPressed: () => setSheetState(() => hideConfirm = !hideConfirm),
                  icon: Icon(hideConfirm ? Icons.visibility_outlined : Icons.visibility_off_outlined),
                ),
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
      final onPasswordChanged = widget.onPasswordChanged;
      if (onPasswordChanged != null) {
        await onPasswordChanged();
        return;
      }
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
              chatRepository: widget.chatRepository,
              userId: '${profile['id']}',
              profile: profile,
              onOpenFriends: () => Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => UserFriendsPage(
                    repository: widget.repository,
                    userId: '${profile['id']}',
                    title: 'Bạn bè của tôi',
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
                            chatRepository: widget.chatRepository,
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
