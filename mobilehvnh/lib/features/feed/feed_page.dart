import 'package:file_picker/file_picker.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/storage/auth_session.dart';
import '../../core/utils/app_date_time.dart';
import '../../core/widgets/app_avatar.dart';
import '../../core/widgets/app_network_image.dart';
import '../../core/widgets/premium_hero_card.dart';
import '../../core/widgets/app_state_view.dart';
import '../../core/theme/app_theme.dart';
import 'domain/entities/upload_file.dart';
import 'domain/repositories/feed_repository.dart';
import '../groups/domain/repositories/group_repository.dart';
import 'presentation/enhanced_post_composer_sheet.dart';

Future<void> _openMediaUrl(BuildContext context, String value) async {
  final uri = Uri.tryParse(value);
  if (uri == null ||
      !await launchUrl(uri, mode: LaunchMode.externalApplication)) {
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Không thể mở tệp đính kèm này.')),
      );
    }
  }
}

class FeedPage extends StatefulWidget {
  const FeedPage({
    super.key,
    required this.repository,
    required this.groupRepository,
    this.currentUser,
    this.refreshSignal,
    this.onOpenGroups,
    this.onOpenProfile,
  });
  final FeedRepository repository;
  final GroupRepository groupRepository;
  final Map<String, dynamic>? currentUser;
  final ValueListenable<int>? refreshSignal;
  final VoidCallback? onOpenGroups;
  final VoidCallback? onOpenProfile;

  @override
  State<FeedPage> createState() => _FeedPageState();
}

class _FeedPageState extends State<FeedPage> {
  final _scrollController = ScrollController();
  List<dynamic> _posts = [];
  bool _loading = true;
  bool _loadingMore = false;
  bool _hasMore = true;
  String? _nextCursor;
  String? _error;
  String? _myId;
  String? _category;
  List<String> _joinedCategories = const [];
  int _loadGeneration = 0;
  final Set<String> _likingPostIds = <String>{};

  static const _categories = <(String?, String)>[
    (null, 'Tất cả'),
    ('market', 'Pass đồ'),
    ('roommate', 'Phòng trọ'),
    ('event', 'Sự kiện'),
    ('study', 'Học tập'),
  ];

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
    widget.refreshSignal?.addListener(_refreshHome);
    _load();
    _loadJoinedCategories();
    AuthSession().userId.then((value) {
      if (mounted) setState(() => _myId = value);
    });
  }

  @override
  void dispose() {
    _scrollController.dispose();
    widget.refreshSignal?.removeListener(_refreshHome);
    super.dispose();
  }

  void _onScroll() {
    if (_scrollController.position.extentAfter < 600) _loadMore();
  }

  void _refreshHome() {
    _load();
    _loadJoinedCategories();
  }

  Future<void> _load() async {
    final generation = ++_loadGeneration;
    setState(() => _loading = true);
    try {
      final page = await widget.repository.getFeedPage(
        category: _category,
        limit: 10,
      );
      if (!mounted || generation != _loadGeneration) return;
      _posts = page.items;
      _nextCursor = page.nextCursor;
      _hasMore = page.nextCursor != null;
      _error = null;
    } catch (error) {
      if (!mounted || generation != _loadGeneration) return;
      _error = error.toString();
      _hasMore = false;
    } finally {
      if (mounted && generation == _loadGeneration) {
        setState(() => _loading = false);
      }
    }
  }

  Future<void> _loadMore() async {
    if (_loading || _loadingMore || !_hasMore || _nextCursor == null) return;
    final generation = _loadGeneration;
    setState(() => _loadingMore = true);
    try {
      final page = await widget.repository.getFeedPage(
        category: _category,
        cursor: _nextCursor,
        limit: 10,
      );
      if (!mounted || generation != _loadGeneration) return;
      final knownIds = _posts
          .map((item) => (item as Map)['id']?.toString())
          .toSet();
      _posts.addAll(
        page.items.where((item) => !knownIds.contains(item['id']?.toString())),
      );
      _nextCursor = page.nextCursor;
      _hasMore = page.nextCursor != null;
    } catch (_) {
      // Giữ các bài đã tải; người dùng có thể kéo để làm mới toàn bộ feed.
    } finally {
      if (mounted) setState(() => _loadingMore = false);
    }
  }

  Future<void> _create(EnhancedPostDraft draft) async {
    await widget.repository.createPost(
      content: draft.content,
      files: draft.files
          .map(
            (file) => UploadFile(
              name: file.name,
              size: file.size,
              path: file.path,
              bytes: file.bytes,
            ),
          )
          .toList(),
      category: draft.category,
      marketListing: draft.marketListing,
      roomListing: draft.roomListing,
      eventListing: draft.eventListing,
      studyListing: draft.studyListing,
      location: draft.location,
    );
    await _load();
  }

  Future<void> _loadJoinedCategories() async {
    const categoryBySlug = <String, String>{
      'pass-do': 'market',
      'ghep-phong-tim-tro': 'roommate',
      'su-kien': 'event',
      'hoc-tap': 'study',
    };
    try {
      final groups = await widget.groupRepository.getGroups();
      if (!mounted) return;
      setState(() {
        _joinedCategories = groups
            .where(
              (group) =>
                  group['membership'] == 'MEMBER' ||
                  group['membership'] == 'ADMIN' ||
                  group['membership'] == 'PUBLIC',
            )
            .map((group) => categoryBySlug[group['slug']])
            .whereType<String>()
            .toSet()
            .toList();
      });
    } catch (_) {
      // Composer verifies membership again before offering a group.
    }
  }

  void _selectCategory(String? category) {
    if (_category == category) return;
    HapticFeedback.selectionClick();
    setState(() {
      _category = category;
      _posts = [];
      _nextCursor = null;
      _hasMore = true;
    });
    _load();
  }

  Future<void> _compose([String? initialCategory]) {
    final groupsFuture = widget.groupRepository.getGroups();
    const categoryBySlug = <String, String>{
      'pass-do': 'market',
      'ghep-phong-tim-tro': 'roommate',
      'su-kien': 'event',
      'hoc-tap': 'study',
    };
    return showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (_) => FutureBuilder<List<Map<String, dynamic>>>(
        future: groupsFuture,
        builder: (context, snapshot) {
          if (snapshot.hasError) {
            return SafeArea(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text('Không tải được danh sách nhóm: ${snapshot.error}'),
              ),
            );
          }
          if (!snapshot.hasData) {
            return const SafeArea(
              child: SizedBox(
                height: 170,
                child: Center(child: CircularProgressIndicator()),
              ),
            );
          }
          final categories = <String>[
            'general',
            ...snapshot.data!
                .where(
                  (group) =>
                      group['membership'] == 'MEMBER' ||
                      group['membership'] == 'ADMIN' ||
                      group['membership'] == 'PUBLIC',
                )
                .map((group) => categoryBySlug[group['slug']])
                .whereType<String>(),
          ];
          return EnhancedPostComposerSheet(
            repository: widget.repository,
            allowedCategories: categories,
            initialCategory:
                initialCategory != null && categories.contains(initialCategory)
                ? initialCategory
                : 'general',
            onSubmit: _create,
          );
        },
      ),
    );
  }

  Future<void> _like(Map<dynamic, dynamic> post) async {
    final postId = '${post['id']}';
    if (!_likingPostIds.add(postId)) return;
    final previousLiked = post['isLiked'] == true;
    final previousCount = (post['likesCount'] as num?)?.toInt() ?? 0;
    final nextLiked = !previousLiked;
    HapticFeedback.lightImpact();
    setState(() {
      post['isLiked'] = nextLiked;
      post['likesCount'] = (previousCount + (nextLiked ? 1 : -1)).clamp(
        0,
        1 << 30,
      );
    });
    try {
      final result = await widget.repository.setLike(postId, nextLiked);
      if (mounted) {
        setState(() {
          post['isLiked'] = result['isLiked'];
          post['likesCount'] = result['likesCount'];
        });
      }
    } catch (error) {
      if (mounted) {
        setState(() {
          post['isLiked'] = previousLiked;
          post['likesCount'] = previousCount;
        });
      }
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.toString())));
      }
    } finally {
      _likingPostIds.remove(postId);
    }
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: _load,
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 760),
          child: CustomScrollView(
            controller: _scrollController,
            physics: const BouncingScrollPhysics(
              parent: AlwaysScrollableScrollPhysics(),
            ),
            slivers: [
              SliverPadding(
                padding: const EdgeInsets.fromLTRB(16, 18, 16, 0),
                sliver: SliverList(
                  delegate: SliverChildListDelegate([
                    if (_loading) const LinearProgressIndicator(minHeight: 2),
                    _FeedWelcome(name: widget.currentUser?['name']?.toString()),
                    const SizedBox(height: 14),
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.fromLTRB(16, 16, 16, 10),
                        child: Column(
                          children: [
                            Row(
                              children: [
                                AppAvatar(
                                  radius: 23,
                                  url: widget.currentUser?['avatar']
                                      ?.toString(),
                                  name: widget.currentUser?['name']?.toString(),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: InkWell(
                                    onTap: _compose,
                                    borderRadius: BorderRadius.circular(18),
                                    child: Container(
                                      padding: const EdgeInsets.symmetric(
                                        horizontal: 16,
                                        vertical: 14,
                                      ),
                                      decoration: BoxDecoration(
                                        color: AppTheme.canvas,
                                        border: Border.all(
                                          color: const Color(0xffe1eaf0),
                                        ),
                                        borderRadius: BorderRadius.circular(18),
                                      ),
                                      child: Text(
                                        widget.currentUser?['name'] == null
                                            ? 'Bạn đang nghĩ gì?'
                                            : 'Bạn đang nghĩ gì, ${widget.currentUser!['name']}?',
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                        style: const TextStyle(
                                          color: Color(0xff62758b),
                                        ),
                                      ),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            const Padding(
                              padding: EdgeInsets.only(top: 13),
                              child: Divider(),
                            ),
                            SizedBox(
                              height: 48,
                              child: ListView(
                                physics: const BouncingScrollPhysics(),
                                scrollDirection: Axis.horizontal,
                                children: [
                                  _ComposeAction(
                                    icon: CupertinoIcons.photo_on_rectangle,
                                    color: AppTheme.blue,
                                    label: 'Ảnh / Video',
                                    onTap: () => _compose('general'),
                                  ),
                                  if (_joinedCategories.contains('market'))
                                    _ComposeAction(
                                      icon: CupertinoIcons.bag,
                                      color: AppTheme.blue,
                                      label: 'Pass đồ',
                                      onTap: () => _compose('market'),
                                    ),
                                  if (_joinedCategories.contains('roommate'))
                                    _ComposeAction(
                                      icon: CupertinoIcons.house,
                                      color: AppTheme.blue,
                                      label: 'Ghép phòng',
                                      onTap: () => _compose('roommate'),
                                    ),
                                  if (_joinedCategories.contains('event'))
                                    _ComposeAction(
                                      icon: CupertinoIcons.calendar,
                                      color: AppTheme.blue,
                                      label: 'Sự kiện',
                                      onTap: () => _compose('event'),
                                    ),
                                  if (_joinedCategories.contains('study'))
                                    _ComposeAction(
                                      icon: CupertinoIcons.book,
                                      color: AppTheme.blue,
                                      label: 'Học tập',
                                      onTap: () => _compose('study'),
                                    ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 12),
                    _HomeCommunityCard(
                      onOpenGroups: widget.onOpenGroups,
                      onOpenProfile: widget.onOpenProfile,
                    ),
                    const SizedBox(height: 18),
                    SizedBox(
                      height: 42,
                      child: ListView.separated(
                        scrollDirection: Axis.horizontal,
                        itemCount: _categories.length,
                        separatorBuilder: (_, _) => const SizedBox(width: 8),
                        itemBuilder: (context, index) {
                          final item = _categories[index];
                          return ChoiceChip(
                            label: Text(item.$2),
                            selected: _category == item.$1,
                            onSelected: (_) => _selectCategory(item.$1),
                          );
                        },
                      ),
                    ),
                    const SizedBox(height: 14),
                    Padding(
                      padding: const EdgeInsets.only(left: 2, bottom: 10),
                      child: Row(
                        children: [
                          const Expanded(
                            child: Text(
                              'Bảng tin của bạn',
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.w800,
                                color: AppTheme.ink,
                              ),
                            ),
                          ),
                          Text(
                            '${_posts.length} bài viết',
                            style: const TextStyle(
                              color: AppTheme.muted,
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                    ),
                    if (_loading && _posts.isEmpty)
                      const SizedBox(
                        height: 165,
                        child: AppLoadingList(count: 1),
                      )
                    else if (_error != null)
                      AppStateView(
                        icon: Icons.wifi_off_rounded,
                        title: 'Chưa tải được bảng tin',
                        message: _error!,
                        actionLabel: 'Thử lại',
                        onAction: _load,
                      )
                    else if (_posts.isEmpty)
                      const AppStateView(
                        icon: Icons.auto_stories_outlined,
                        title: 'Chưa có bài viết',
                        message:
                            'Bảng tin đang chờ câu chuyện đầu tiên từ cộng đồng.',
                      ),
                  ]),
                ),
              ),
              if (_posts.isNotEmpty)
                SliverPadding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  sliver: SliverList.builder(
                    itemCount: _posts.length,
                    itemBuilder: (context, index) {
                      final item = _posts[index];
                      return PostCard(
                        key: ValueKey(item['id']),
                        post: item as Map<dynamic, dynamic>,
                        repository: widget.repository,
                        currentUserId: _myId,
                        onLike: () => _like(item),
                        onChanged: _load,
                      );
                    },
                  ),
                ),
              if (_loadingMore)
                const SliverToBoxAdapter(
                  child: Padding(
                    padding: EdgeInsets.symmetric(vertical: 18),
                    child: Center(
                      child: CircularProgressIndicator(strokeWidth: 2),
                    ),
                  ),
                ),
              const SliverToBoxAdapter(child: SizedBox(height: 32)),
            ],
          ),
        ),
      ),
    );
  }
}

class _FeedWelcome extends StatelessWidget {
  const _FeedWelcome({this.name});
  final String? name;

  @override
  Widget build(BuildContext context) => PremiumHeroCard(
    padding: const EdgeInsets.fromLTRB(20, 22, 20, 22),
    child: Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'CỘNG ĐỒNG HVNH',
                style: TextStyle(
                  color: AppTheme.gold,
                  fontSize: 10,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 1,
                ),
              ),
              const SizedBox(height: 9),
              Text(
                name == null || name!.trim().isEmpty
                    ? 'Chào mừng trở lại'
                    : 'Chào mừng trở lại, $name',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 23,
                  fontWeight: FontWeight.w800,
                  height: 1.18,
                ),
              ),
              const SizedBox(height: 6),
              const Text(
                'Cập nhật bài đăng, hoạt động và thông tin mới nhất trong cộng đồng.',
                style: TextStyle(
                  color: Color(0xffd5eafa),
                  fontSize: 12.5,
                  height: 1.4,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(width: 8),
        Container(
          width: 50,
          height: 50,
          decoration: BoxDecoration(
            color: const Color(0x22ffffff),
            borderRadius: BorderRadius.circular(17),
            border: Border.all(color: const Color(0x35ffffff)),
          ),
          child: const Icon(
            CupertinoIcons.person_2_fill,
            color: AppTheme.gold,
            size: 25,
          ),
        ),
      ],
    ),
  );
}

class _ComposeAction extends StatelessWidget {
  const _ComposeAction({
    required this.icon,
    required this.color,
    required this.label,
    required this.onTap,
  });
  final IconData icon;
  final Color color;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(right: 7),
    child: InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12),
        constraints: const BoxConstraints(minHeight: 44),
        decoration: BoxDecoration(
          color: AppTheme.softBlue,
          borderRadius: BorderRadius.circular(14),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: color, size: 17),
            const SizedBox(width: 5),
            Text(
              label,
              maxLines: 1,
              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700),
            ),
          ],
        ),
      ),
    ),
  );
}

class _HomeCommunityCard extends StatelessWidget {
  const _HomeCommunityCard({
    required this.onOpenGroups,
    required this.onOpenProfile,
  });

  final VoidCallback? onOpenGroups;
  final VoidCallback? onOpenProfile;

  @override
  Widget build(BuildContext context) => Row(
    children: [
      Expanded(
        child: _HomeShortcut(
          icon: CupertinoIcons.person_crop_circle,
          title: 'Trang cá nhân',
          subtitle: 'Hồ sơ của bạn',
          onTap: onOpenProfile,
        ),
      ),
      const SizedBox(width: 10),
      Expanded(
        child: _HomeShortcut(
          icon: CupertinoIcons.person_2_fill,
          title: 'Hội nhóm',
          subtitle: 'Khám phá cộng đồng',
          onTap: onOpenGroups,
        ),
      ),
    ],
  );
}

class _HomeShortcut extends StatelessWidget {
  const _HomeShortcut({
    required this.icon,
    required this.title,
    required this.subtitle,
    this.onTap,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) => Card(
    child: InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(20),
      child: Padding(
        padding: const EdgeInsets.all(13),
        child: Row(
          children: [
            Icon(icon, color: AppTheme.blue, size: 23),
            const SizedBox(width: 9),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  Text(
                    subtitle,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 10, color: AppTheme.muted),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    ),
  );
}

class PostCard extends StatelessWidget {
  const PostCard({
    super.key,
    required this.post,
    required this.repository,
    required this.onLike,
    this.currentUserId,
    this.onChanged,
  });

  final Map<dynamic, dynamic> post;
  final FeedRepository repository;
  final VoidCallback onLike;
  final String? currentUserId;
  final Future<void> Function()? onChanged;

  Future<void> _showLikes(BuildContext context) async {
    final likesFuture = repository.getPostLikes('${post['id']}');
    HapticFeedback.selectionClick();
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      showDragHandle: true,
      builder: (sheetContext) => DraggableScrollableSheet(
        expand: false,
        initialChildSize: .58,
        minChildSize: .35,
        maxChildSize: .9,
        builder: (context, scrollController) =>
            FutureBuilder<Map<String, dynamic>>(
              future: likesFuture,
              builder: (context, snapshot) {
                final items = (snapshot.data?['items'] as List?) ?? const [];
                return Column(
                  children: [
                    const Padding(
                      padding: EdgeInsets.fromLTRB(20, 8, 20, 14),
                      child: Align(
                        alignment: Alignment.centerLeft,
                        child: Text(
                          'Người đã thích',
                          style: TextStyle(
                            fontSize: 19,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ),
                    ),
                    const Divider(height: 1),
                    Expanded(
                      child: snapshot.connectionState != ConnectionState.done
                          ? const Center(
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : snapshot.hasError
                          ? Center(
                              child: Text(
                                'Không tải được danh sách: ${snapshot.error}',
                              ),
                            )
                          : items.isEmpty
                          ? const Center(child: Text('Chưa có lượt thích nào.'))
                          : ListView.separated(
                              controller: scrollController,
                              physics: const BouncingScrollPhysics(),
                              padding: const EdgeInsets.symmetric(vertical: 8),
                              itemCount: items.length,
                              separatorBuilder: (_, _) =>
                                  const Divider(height: 1, indent: 68),
                              itemBuilder: (context, index) {
                                final user = Map<String, dynamic>.from(
                                  items[index] as Map,
                                );
                                final isMe =
                                    user['id']?.toString() == currentUserId;
                                return ListTile(
                                  leading: AppAvatar(
                                    radius: 21,
                                    url: user['avatar']?.toString(),
                                    name: user['name']?.toString(),
                                  ),
                                  title: Text(
                                    isMe
                                        ? 'Bạn'
                                        : '${user['name'] ?? 'Sinh viên HVNH'}',
                                    style: const TextStyle(
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                  subtitle: Text(
                                    isMe
                                        ? 'Bạn đã thích bài viết này'
                                        : '@${user['username'] ?? ''}',
                                  ),
                                );
                              },
                            ),
                    ),
                  ],
                );
              },
            ),
      ),
    );
  }

  Future<void> _edit(BuildContext context) async {
    final controller = TextEditingController(text: '${post['content'] ?? ''}');
    var privacy = post['privacy']?.toString().toLowerCase() ?? 'public';
    var category = post['category']?.toString() ?? 'general';
    final media = ((post['media'] as List?) ?? const [])
        .map((item) => Map<String, dynamic>.from(item as Map))
        .toList();
    final retainedIds = media
        .map((item) => item['id']?.toString())
        .whereType<String>()
        .toSet();
    final result = await showModalBottomSheet<Map<String, dynamic>>(
      context: context,
      isScrollControlled: true,
      builder: (sheetContext) => StatefulBuilder(
        builder: (context, setSheetState) => SafeArea(
          child: Padding(
            padding: EdgeInsets.fromLTRB(
              20,
              18,
              20,
              20 + MediaQuery.of(context).viewInsets.bottom,
            ),
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Text(
                    'Chỉnh sửa bài viết',
                    style: TextStyle(fontSize: 21, fontWeight: FontWeight.w800),
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: controller,
                    minLines: 4,
                    maxLines: 8,
                    autofocus: true,
                    maxLength: 10000,
                    decoration: const InputDecoration(
                      hintText: 'Nội dung bài viết',
                      alignLabelWithHint: true,
                    ),
                  ),
                  const SizedBox(height: 10),
                  DropdownButtonFormField<String>(
                    initialValue: privacy,
                    decoration: const InputDecoration(
                      labelText: 'Quyền riêng tư',
                      prefixIcon: Icon(Icons.visibility_outlined),
                    ),
                    items: const [
                      DropdownMenuItem(
                        value: 'public',
                        child: Text('Công khai'),
                      ),
                      DropdownMenuItem(value: 'friends', child: Text('Bạn bè')),
                      DropdownMenuItem(
                        value: 'private',
                        child: Text('Chỉ mình tôi'),
                      ),
                    ],
                    onChanged: (value) {
                      if (value != null) setSheetState(() => privacy = value);
                    },
                  ),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    initialValue: category,
                    decoration: const InputDecoration(
                      labelText: 'Danh mục',
                      prefixIcon: Icon(Icons.category_outlined),
                    ),
                    items: const [
                      DropdownMenuItem(
                        value: 'general',
                        child: Text('Bài chung'),
                      ),
                      DropdownMenuItem(value: 'market', child: Text('Pass đồ')),
                      DropdownMenuItem(
                        value: 'roommate',
                        child: Text('Phòng trọ'),
                      ),
                      DropdownMenuItem(value: 'event', child: Text('Sự kiện')),
                      DropdownMenuItem(value: 'study', child: Text('Học tập')),
                    ],
                    onChanged: (value) {
                      if (value != null) setSheetState(() => category = value);
                    },
                  ),
                  if (media.isNotEmpty) ...[
                    const SizedBox(height: 16),
                    const Text(
                      'Ảnh và tệp đang đính kèm',
                      style: TextStyle(fontWeight: FontWeight.w800),
                    ),
                    const SizedBox(height: 6),
                    ...media.map((item) {
                      final id = item['id']?.toString();
                      final retained = id != null && retainedIds.contains(id);
                      return CheckboxListTile(
                        dense: true,
                        contentPadding: EdgeInsets.zero,
                        value: retained,
                        secondary: Icon(
                          item['type'] == 'image'
                              ? Icons.image_outlined
                              : Icons.attach_file,
                        ),
                        title: Text(
                          item['name']?.toString() ?? 'Tệp đính kèm',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        subtitle: Text(
                          retained ? 'Giữ lại' : 'Sẽ gỡ khỏi bài viết',
                        ),
                        onChanged: id == null
                            ? null
                            : (checked) => setSheetState(() {
                                if (checked == true) {
                                  retainedIds.add(id);
                                } else {
                                  retainedIds.remove(id);
                                }
                              }),
                      );
                    }),
                  ],
                  const SizedBox(height: 14),
                  FilledButton.icon(
                    onPressed: () {
                      final content = controller.text.trim();
                      if (content.isEmpty) return;
                      Navigator.pop(sheetContext, {
                        'content': content,
                        'privacy': privacy,
                        'category': category,
                        'mediaIds': retainedIds.toList(),
                      });
                    },
                    icon: const Icon(Icons.save_outlined),
                    label: const Text('Lưu thay đổi'),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
    controller.dispose();
    if (result == null) return;
    try {
      await repository.updatePost(
        '${post['id']}',
        content: result['content'] as String,
        privacy: result['privacy'] as String,
        category: result['category'] as String,
        mediaIds: (result['mediaIds'] as List).cast<String>(),
      );
      await onChanged?.call();
    } catch (error) {
      if (context.mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.toString())));
      }
    }
  }

  Future<void> _delete(BuildContext context) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Xóa bài viết?'),
        content: const Text('Thao tác này không thể hoàn tác.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Hủy'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(dialogContext, true),
            child: const Text('Xóa'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    try {
      await repository.deletePost('${post['id']}');
      await onChanged?.call();
    } catch (error) {
      if (context.mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.toString())));
      }
    }
  }

  Future<void> _report(BuildContext context) async {
    final controller = TextEditingController();
    final reason = await showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Báo cáo bài viết'),
        content: TextField(
          controller: controller,
          autofocus: true,
          minLines: 3,
          maxLines: 5,
          maxLength: 1000,
          decoration: const InputDecoration(
            labelText: 'Lý do báo cáo',
            hintText: 'Mô tả nội dung không phù hợp...',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Hủy'),
          ),
          FilledButton(
            onPressed: () {
              final value = controller.text.trim();
              if (value.length >= 3) Navigator.pop(dialogContext, value);
            },
            child: const Text('Gửi báo cáo'),
          ),
        ],
      ),
    );
    controller.dispose();
    if (reason == null || !context.mounted) return;
    try {
      await repository.reportPost('${post['id']}', reason);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Đã gửi báo cáo tới quản trị viên.')),
        );
      }
    } catch (error) {
      if (context.mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.toString())));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final author = (post['author'] as Map?) ?? {};
    final media = (post['media'] as List?) ?? [];
    final liked = post['isLiked'] == true;
    final mine =
        currentUserId != null && author['id']?.toString() == currentUserId;
    return Card(
      clipBehavior: Clip.antiAlias,
      margin: const EdgeInsets.only(bottom: 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ListTile(
            leading: AppAvatar(
              url: author['avatar']?.toString(),
              name: author['name']?.toString(),
            ),
            title: Text.rich(
              TextSpan(
                children: [
                  TextSpan(
                    text: '${author['name'] ?? 'Sinh viên HVNH'}',
                    style: const TextStyle(fontWeight: FontWeight.w800),
                  ),
                  if ('${post['groupName'] ?? ''}'.trim().isNotEmpty) ...[
                    const TextSpan(
                      text: '  ›  ',
                      style: TextStyle(color: AppTheme.muted),
                    ),
                    TextSpan(
                      text: '${post['groupName']}',
                      style: const TextStyle(
                        color: AppTheme.blue,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ],
                ],
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            subtitle: Tooltip(
              message: AppDateTime.full(post['createdAt']),
              child: Text(
                '${AppDateTime.relative(post['createdAt'])} · Công khai',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
            trailing: PopupMenuButton<String>(
              onSelected: (value) {
                if (value == 'edit') _edit(context);
                if (value == 'delete') _delete(context);
                if (value == 'report') _report(context);
              },
              itemBuilder: (_) => mine
                  ? const [
                      PopupMenuItem(value: 'edit', child: Text('Chỉnh sửa')),
                      PopupMenuItem(
                        value: 'delete',
                        child: Text('Xóa bài viết'),
                      ),
                    ]
                  : const [
                      PopupMenuItem(
                        value: 'report',
                        child: Text('Báo cáo bài viết'),
                      ),
                    ],
            ),
          ),
          _PostCategoryDetails(post: post),
          if ('${post['content']}'.trim().isNotEmpty)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 14),
              child: Text(
                '${post['content']}',
                style: const TextStyle(
                  fontSize: 15,
                  height: 1.5,
                  color: AppTheme.ink,
                ),
              ),
            ),
          if (media.isNotEmpty) _PostMediaGrid(media: media),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 10),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                InkWell(
                  onTap: (post['likesCount'] as num? ?? 0) > 0
                      ? () => _showLikes(context)
                      : null,
                  borderRadius: BorderRadius.circular(12),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(
                      vertical: 5,
                      horizontal: 3,
                    ),
                    child: Row(
                      children: [
                        const Icon(
                          CupertinoIcons.heart_fill,
                          size: 14,
                          color: Color(0xffdd5b69),
                        ),
                        const SizedBox(width: 5),
                        Text(
                          '${post['likesCount'] ?? 0} lượt thích',
                          style: const TextStyle(
                            color: AppTheme.muted,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                Text(
                  '${post['commentsCount'] ?? 0} bình luận',
                  style: const TextStyle(color: AppTheme.muted, fontSize: 12),
                ),
              ],
            ),
          ),
          const Divider(height: 1),
          Row(
            children: [
              Expanded(
                child: TextButton.icon(
                  onPressed: onLike,
                  icon: TweenAnimationBuilder<double>(
                    tween: Tween<double>(begin: 1, end: liked ? 1.22 : 1),
                    duration: const Duration(milliseconds: 360),
                    curve: Curves.easeOutBack,
                    builder: (context, scale, child) =>
                        Transform.scale(scale: scale, child: child),
                    child: Icon(
                      liked ? CupertinoIcons.heart_fill : CupertinoIcons.heart,
                      color: liked ? Colors.red : null,
                    ),
                  ),
                  label: Text(
                    'Thích',
                    style: TextStyle(color: liked ? Colors.red : null),
                  ),
                ),
              ),
              Expanded(
                child: TextButton.icon(
                  onPressed: () {
                    HapticFeedback.lightImpact();
                    _comments(context);
                  },
                  icon: const Icon(CupertinoIcons.chat_bubble),
                  label: const Text('Bình luận'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  void _comments(BuildContext context) => showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    useSafeArea: true,
    showDragHandle: true,
    backgroundColor: Colors.white,
    builder: (_) =>
        CommentSheet(postId: '${post['id']}', repository: repository),
  );
}

class _PostCategoryDetails extends StatelessWidget {
  const _PostCategoryDetails({required this.post});

  final Map<dynamic, dynamic> post;

  String? _price(dynamic value, {bool monthly = false}) {
    final amount = num.tryParse('${value ?? ''}');
    if (amount == null || amount <= 0) return null;
    final digits = amount.toStringAsFixed(0);
    final formatted = digits.replaceAllMapped(
      RegExp(r'\B(?=(\d{3})+(?!\d))'),
      (_) => '.',
    );
    return '$formatted đ${monthly ? '/tháng' : ''}';
  }

  @override
  Widget build(BuildContext context) {
    final category = '${post['category'] ?? 'general'}';
    if (category == 'general') return const SizedBox.shrink();
    final listing =
        (post[switch (category) {
              'market' => 'marketListing',
              'roommate' => 'roomListing',
              'event' => 'eventListing',
              _ => 'studyListing',
            }]
            as Map?) ??
        const {};
    final (label, icon, color) = switch (category) {
      'market' => ('Pass đồ', CupertinoIcons.bag, const Color(0xffbb3b68)),
      'roommate' => (
        'Ghép phòng',
        CupertinoIcons.house,
        const Color(0xff15805a),
      ),
      'event' => ('Sự kiện', CupertinoIcons.calendar, const Color(0xffbf6b13)),
      _ => ('Học tập', CupertinoIcons.book, AppTheme.blue),
    };
    final title =
        listing['productName'] ??
        listing['eventName'] ??
        listing['subjectName'];
    final price = category == 'market'
        ? _price(listing['price'])
        : category == 'roommate'
        ? _price(listing['rentPerMonth'], monthly: true)
        : null;
    final eventDate = listing['eventDate']?.toString() ?? '';
    final eventTime = listing['eventTime']?.toString() ?? '';
    final rawLocation = post['location'];
    final location = rawLocation is Map
        ? rawLocation['name']?.toString()
        : listing['location']?.toString();
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
            decoration: BoxDecoration(
              color: color.withValues(alpha: .09),
              border: Border.all(color: color.withValues(alpha: .2)),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(icon, size: 15, color: color),
                const SizedBox(width: 5),
                Text(
                  label,
                  style: TextStyle(
                    color: color,
                    fontSize: 11,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ],
            ),
          ),
          if (title != null && '$title'.trim().isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(
              '$title',
              style: const TextStyle(
                color: AppTheme.ink,
                fontWeight: FontWeight.w800,
                fontSize: 15,
              ),
            ),
          ],
          if (price != null) ...[
            const SizedBox(height: 5),
            Text(
              price,
              style: TextStyle(
                color: color,
                fontWeight: FontWeight.w800,
                fontSize: 17,
              ),
            ),
          ],
          if (category == 'event' &&
              (eventDate.isNotEmpty || eventTime.isNotEmpty)) ...[
            const SizedBox(height: 7),
            Text(
              '▣ $eventDate${eventTime.isNotEmpty ? ' · $eventTime' : ''}',
              style: const TextStyle(color: AppTheme.muted, fontSize: 12),
            ),
          ],
          if (location != null && location.trim().isNotEmpty) ...[
            const SizedBox(height: 7),
            Text(
              '⌖ $location',
              style: const TextStyle(
                color: AppTheme.blue,
                fontSize: 12,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _Attachment extends StatelessWidget {
  const _Attachment({
    required this.type,
    required this.name,
    required this.url,
  });
  final String? type;
  final String name;
  final String url;
  @override
  Widget build(BuildContext context) => InkWell(
    onTap: url.isEmpty ? null : () => _openMediaUrl(context, url),
    borderRadius: BorderRadius.circular(12),
    child: Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xfff3f7fb),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Icon(switch (type) {
            'video' => Icons.play_circle_outline,
            'audio' => Icons.audio_file_outlined,
            _ => Icons.attach_file,
          }, color: const Color(0xff0866c6)),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              name,
              style: const TextStyle(fontWeight: FontWeight.w700),
              overflow: TextOverflow.ellipsis,
            ),
          ),
          if (url.isNotEmpty)
            const Icon(Icons.open_in_new, size: 18, color: Color(0xff71839a)),
        ],
      ),
    ),
  );
}

class _PostMediaGrid extends StatelessWidget {
  const _PostMediaGrid({required this.media});

  final List media;

  @override
  Widget build(BuildContext context) {
    final items = media
        .map((value) => Map<String, dynamic>.from(value as Map))
        .toList();
    final images = items
        .where(
          (item) =>
              item['type'] == 'image' && '${item['url'] ?? ''}'.isNotEmpty,
        )
        .toList();
    final attachments = items.where((item) => item['type'] != 'image').toList();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (images.length == 1)
          _PostImage(item: images.first, height: 310)
        else if (images.isNotEmpty)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 2),
            child: GridView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: images.length > 4 ? 4 : images.length,
              gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                mainAxisSpacing: 2,
                crossAxisSpacing: 2,
                childAspectRatio: images.length == 2 ? 1.05 : 1,
              ),
              itemBuilder: (context, index) => Stack(
                fit: StackFit.expand,
                children: [
                  _PostImage(item: images[index]),
                  if (index == 3 && images.length > 4)
                    ColoredBox(
                      color: const Color(0x88000000),
                      child: Center(
                        child: Text(
                          '+${images.length - 4}',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 28,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ),
        if (attachments.isNotEmpty)
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 10, 16, 4),
            child: Column(
              children: attachments
                  .map(
                    (item) => Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: _Attachment(
                        type: item['type']?.toString(),
                        name: item['name']?.toString() ?? 'Tệp đính kèm',
                        url: item['url']?.toString() ?? '',
                      ),
                    ),
                  )
                  .toList(),
            ),
          ),
      ],
    );
  }
}

class _PostImage extends StatelessWidget {
  const _PostImage({required this.item, this.height});

  final Map<String, dynamic> item;
  final double? height;

  @override
  Widget build(BuildContext context) => GestureDetector(
    onTap: () => showDialog<void>(
      context: context,
      builder: (dialogContext) => Dialog.fullscreen(
        backgroundColor: Colors.black,
        child: Stack(
          children: [
            InteractiveViewer(
              minScale: .8,
              maxScale: 4,
              child: Center(child: AppNetworkImage('${item['url']}')),
            ),
            SafeArea(
              child: IconButton.filled(
                onPressed: () => Navigator.pop(dialogContext),
                icon: const Icon(Icons.close),
              ),
            ),
          ],
        ),
      ),
    ),
    child: AppNetworkImage(
      '${item['url']}',
      height: height,
      width: double.infinity,
      fit: BoxFit.cover,
      errorBuilder: (_, _, _) => Container(
        height: height ?? 160,
        color: const Color(0xffeef3f8),
        alignment: Alignment.center,
        child: const Icon(
          Icons.broken_image_outlined,
          color: Color(0xff71839a),
        ),
      ),
    ),
  );
}

class CommentSheet extends StatefulWidget {
  const CommentSheet({
    super.key,
    required this.postId,
    required this.repository,
    this.highlightCommentId,
  });
  final String postId;
  final FeedRepository repository;
  final String? highlightCommentId;

  @override
  State<CommentSheet> createState() => _CommentSheetState();
}

class _CommentSheetState extends State<CommentSheet> {
  final _text = TextEditingController();
  final _listController = ScrollController();
  List<dynamic> _items = [];
  bool _loading = true;
  bool _sending = false;
  String? _myId;
  Map<String, dynamic>? _replyingTo;
  PlatformFile? _image;
  List<Map<String, dynamic>> _friends = const [];
  final _mentions = <Map<String, dynamic>>[];
  String? _mentionQuery;
  int _mentionStart = -1;

  @override
  void initState() {
    super.initState();
    _load();
    AuthSession().userId.then((value) {
      if (mounted) setState(() => _myId = value);
      if (value != null) _loadFriends(value);
    });
  }

  Future<void> _loadFriends(String userId) async {
    try {
      final friends = await widget.repository.getMentionableFriends(userId);
      if (mounted) setState(() => _friends = friends);
    } catch (_) {
      // Commenting remains available when the friend list cannot load.
    }
  }

  void _onCommentChanged() {
    final content = _text.text;
    _mentions.removeWhere((mention) {
      final start = mention['start'] as int;
      final end = mention['end'] as int;
      return end > content.length ||
          content.substring(start, end) != '@${mention['name']}';
    });
    final caret = _text.selection.baseOffset;
    final before = caret >= 0 && caret <= content.length
        ? content.substring(0, caret)
        : content;
    final at = before.lastIndexOf('@');
    if (at < 0 || (at > 0 && !RegExp(r'\s').hasMatch(before[at - 1]))) {
      setState(() => _mentionQuery = null);
      return;
    }
    final query = before.substring(at + 1);
    if (query.contains('@') ||
        query.contains('\n') ||
        _mentions.any((mention) => mention['start'] == at)) {
      setState(() => _mentionQuery = null);
      return;
    }
    setState(() {
      _mentionStart = at;
      _mentionQuery = query;
    });
  }

  void _insertMention(Map<String, dynamic> friend) {
    final content = _text.text;
    final caret = _text.selection.baseOffset.clamp(
      _mentionStart,
      content.length,
    );
    final label = '@${friend['name']}';
    final next =
        '${content.substring(0, _mentionStart)}$label ${content.substring(caret)}';
    _mentions.removeWhere(
      (mention) =>
          (mention['start'] as int) >= _mentionStart &&
          (mention['start'] as int) < caret,
    );
    _mentions.add({
      'user_id': friend['id'],
      'name': friend['name'],
      'start': _mentionStart,
      'end': _mentionStart + label.length,
    });
    _text.value = TextEditingValue(
      text: next,
      selection: TextSelection.collapsed(
        offset: _mentionStart + label.length + 1,
      ),
    );
    setState(() => _mentionQuery = null);
  }

  void _replyTo(Map item) {
    final author = (item['author'] as Map?) ?? const {};
    setState(() => _replyingTo = Map<String, dynamic>.from(item));
    final id = author['id']?.toString();
    final name = author['name']?.toString() ?? '';
    if (id == null || id == _myId || name.isEmpty) return;
    final label = '@$name';
    _text.value = TextEditingValue(
      text: '$label ${_text.text}',
      selection: TextSelection.collapsed(offset: label.length + 1),
    );
    _mentions.clear();
    _mentions.add({
      'user_id': id,
      'name': name,
      'start': 0,
      'end': label.length,
    });
    setState(() => _mentionQuery = null);
  }

  @override
  void dispose() {
    _text.dispose();
    _listController.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      _items = await widget.repository.getComments(widget.postId);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _send() async {
    final content = _text.text.trim();
    if ((content.isEmpty && _image == null) || _sending) return;
    setState(() => _sending = true);
    try {
      final image = _image;
      final leadingTrim = _text.text.length - _text.text.trimLeft().length;
      final mentions = _mentions
          .where((mention) {
            final start = mention['start'] as int;
            final end = mention['end'] as int;
            return end <= _text.text.length &&
                _text.text.substring(start, end) == '@${mention['name']}';
          })
          .map(
            (mention) => {
              'user_id': mention['user_id'],
              'start': (mention['start'] as int) - leadingTrim,
              'end': (mention['end'] as int) - leadingTrim,
            },
          )
          .where((mention) => (mention['start'] as int) >= 0)
          .toList();
      await widget.repository.addComment(
        widget.postId,
        content,
        parentId: _replyingTo?['id']?.toString(),
        image: image == null
            ? null
            : UploadFile(
                name: image.name,
                size: image.size,
                path: image.path,
                bytes: image.bytes,
              ),
        mentions: mentions,
      );
      _text.clear();
      _mentions.clear();
      if (mounted) {
        setState(() {
          _image = null;
          _replyingTo = null;
          _mentionQuery = null;
        });
      }
      await _load();
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.toString())));
      }
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  Future<void> _pickImage() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.image,
      withData: kIsWeb,
    );
    if (result != null && mounted) setState(() => _image = result.files.first);
  }

  Future<void> _remove(String commentId) async {
    await widget.repository.deleteComment(commentId);
    await _load();
  }

  Future<void> _editComment(Map item) async {
    final controller = TextEditingController(text: '${item['content'] ?? ''}');
    final content = await showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Sửa bình luận'),
        content: TextField(
          controller: controller,
          autofocus: true,
          minLines: 2,
          maxLines: 5,
          maxLength: 2000,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Hủy'),
          ),
          FilledButton(
            onPressed: () =>
                Navigator.pop(dialogContext, controller.text.trim()),
            child: const Text('Lưu'),
          ),
        ],
      ),
    );
    controller.dispose();
    if (content == null || content.isEmpty) return;
    await widget.repository.updateComment('${item['id']}', content: content);
    await _load();
  }

  Widget _commentText(Map item) {
    final content = '${item['content'] ?? ''}';
    final raw = (item['mentions'] as List?) ?? const [];
    final mentions = raw.whereType<Map>().toList()
      ..sort(
        (a, b) => ((a['start'] as num?)?.toInt() ?? 0).compareTo(
          (b['start'] as num?)?.toInt() ?? 0,
        ),
      );
    final spans = <InlineSpan>[];
    var cursor = 0;
    for (final mention in mentions) {
      final start = (mention['start'] as num?)?.toInt() ?? -1;
      final end = (mention['end'] as num?)?.toInt() ?? -1;
      if (start < cursor ||
          end > content.length ||
          end <= start ||
          content.substring(start, end) != '@${mention['name']}') {
        continue;
      }
      if (start > cursor) {
        spans.add(TextSpan(text: content.substring(cursor, start)));
      }
      spans.add(
        TextSpan(
          text: content.substring(start, end),
          style: const TextStyle(
            fontWeight: FontWeight.w800,
            color: Color(0xff07599c),
          ),
        ),
      );
      cursor = end;
    }
    if (cursor < content.length) {
      spans.add(TextSpan(text: content.substring(cursor)));
    }
    return Text.rich(TextSpan(children: spans));
  }

  @override
  Widget build(BuildContext context) => SafeArea(
    child: Padding(
      padding: EdgeInsets.fromLTRB(
        18,
        14,
        18,
        16 + MediaQuery.of(context).viewInsets.bottom,
      ),
      child: SizedBox(
        height: MediaQuery.of(context).size.height * .7,
        child: Column(
          children: [
            const Text(
              'Bình luận',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800),
            ),
            Expanded(
              child: _loading
                  ? const Center(child: CircularProgressIndicator())
                  : ListView(
                      controller: _listController,
                      children: _items.map((value) {
                        final item = value as Map;
                        final author = (item['author'] as Map?) ?? {};
                        final mine =
                            _myId != null && author['id']?.toString() == _myId;
                        final highlighted =
                            widget.highlightCommentId == item['id']?.toString();
                        final isReply = item['parentId'] != null;
                        final imageUrl = item['imageUrl']?.toString() ?? '';
                        return Container(
                          margin: EdgeInsets.only(
                            left: isReply ? 38 : 0,
                            bottom: 8,
                          ),
                          padding: const EdgeInsets.fromLTRB(10, 8, 8, 7),
                          decoration: BoxDecoration(
                            color: highlighted
                                ? const Color(0xffe6f2ff)
                                : const Color(0xfff3f6fa),
                            borderRadius: BorderRadius.circular(16),
                            border: Border.all(
                              color: highlighted
                                  ? const Color(0xff8bbce8)
                                  : const Color(0xffe4ebf3),
                            ),
                          ),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              AppAvatar(
                                radius: 18,
                                url: author['avatar']?.toString(),
                                name: author['name']?.toString(),
                              ),
                              const SizedBox(width: 9),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      '${author['name'] ?? 'Sinh viên'}',
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w800,
                                      ),
                                    ),
                                    if ('${item['content'] ?? ''}'
                                        .trim()
                                        .isNotEmpty)
                                      Padding(
                                        padding: const EdgeInsets.only(top: 3),
                                        child: _commentText(item),
                                      ),
                                    if (imageUrl.isNotEmpty)
                                      Padding(
                                        padding: const EdgeInsets.only(top: 7),
                                        child: ClipRRect(
                                          borderRadius: BorderRadius.circular(
                                            12,
                                          ),
                                          child: AppNetworkImage(
                                            imageUrl,
                                            width: 190,
                                            height: 150,
                                            fit: BoxFit.cover,
                                            errorBuilder: (_, _, _) =>
                                                const SizedBox(
                                                  height: 70,
                                                  child: Center(
                                                    child: Icon(
                                                      Icons
                                                          .broken_image_outlined,
                                                    ),
                                                  ),
                                                ),
                                          ),
                                        ),
                                      ),
                                    const SizedBox(height: 5),
                                    Row(
                                      children: [
                                        Text(
                                          AppDateTime.relative(
                                            item['createdAt'],
                                          ),
                                          style: const TextStyle(
                                            fontSize: 11,
                                            color: Color(0xff71839a),
                                          ),
                                        ),
                                        const SizedBox(width: 12),
                                        InkWell(
                                          onTap: () => _replyTo(item),
                                          child: const Text(
                                            'Trả lời',
                                            style: TextStyle(
                                              fontSize: 11,
                                              color: Color(0xff0866c6),
                                              fontWeight: FontWeight.w700,
                                            ),
                                          ),
                                        ),
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                              if (mine)
                                PopupMenuButton<String>(
                                  padding: EdgeInsets.zero,
                                  onSelected: (value) {
                                    if (value == 'edit') _editComment(item);
                                    if (value == 'delete') {
                                      _remove('${item['id']}');
                                    }
                                  },
                                  itemBuilder: (_) => const [
                                    PopupMenuItem(
                                      value: 'edit',
                                      child: Text('Sửa bình luận'),
                                    ),
                                    PopupMenuItem(
                                      value: 'delete',
                                      child: Text('Xóa bình luận'),
                                    ),
                                  ],
                                ),
                            ],
                          ),
                        );
                      }).toList(),
                    ),
            ),
            if (_replyingTo != null)
              Container(
                margin: const EdgeInsets.only(bottom: 8),
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 8,
                ),
                decoration: BoxDecoration(
                  color: const Color(0xffeef5fc),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.reply, size: 18, color: Color(0xff0866c6)),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Đang trả lời ${((_replyingTo!['author'] as Map?)?['name'] ?? 'bình luận')}',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    IconButton(
                      visualDensity: VisualDensity.compact,
                      onPressed: () => setState(() => _replyingTo = null),
                      icon: const Icon(Icons.close, size: 18),
                    ),
                  ],
                ),
              ),
            if (_image != null)
              Align(
                alignment: Alignment.centerLeft,
                child: InputChip(
                  avatar: const Icon(Icons.image_outlined, size: 18),
                  label: Text(
                    _image!.name,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  onDeleted: _sending
                      ? null
                      : () => setState(() => _image = null),
                ),
              ),
            if (_mentionQuery != null && _friends.isNotEmpty)
              ConstrainedBox(
                constraints: const BoxConstraints(maxHeight: 170),
                child: ListView(
                  shrinkWrap: true,
                  children: _friends
                      .where(
                        (friend) =>
                            '${friend['name'] ?? ''}'.toLowerCase().contains(
                              _mentionQuery!.toLowerCase(),
                            ) ||
                            '${friend['username'] ?? ''}'
                                .toLowerCase()
                                .contains(_mentionQuery!.toLowerCase()),
                      )
                      .take(5)
                      .map(
                        (friend) => ListTile(
                          dense: true,
                          leading: AppAvatar(
                            radius: 16,
                            url: friend['avatar']?.toString(),
                            name: friend['name']?.toString(),
                          ),
                          title: Text(
                            '${friend['name'] ?? ''}',
                            style: const TextStyle(fontWeight: FontWeight.w700),
                          ),
                          subtitle: Text('@${friend['username'] ?? ''}'),
                          onTap: () => _insertMention(friend),
                        ),
                      )
                      .toList(),
                ),
              ),
            Row(
              children: [
                IconButton(
                  tooltip: 'Đính kèm ảnh',
                  onPressed: _sending ? null : _pickImage,
                  icon: const Icon(
                    Icons.image_outlined,
                    color: Color(0xff0866c6),
                  ),
                ),
                Expanded(
                  child: TextField(
                    controller: _text,
                    onChanged: (_) => _onCommentChanged(),
                    minLines: 1,
                    maxLines: 4,
                    textInputAction: TextInputAction.newline,
                    decoration: const InputDecoration(
                      hintText: 'Viết bình luận...',
                    ),
                  ),
                ),
                IconButton(
                  onPressed: _sending ? null : _send,
                  icon: _sending
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.send, color: Color(0xff0866c6)),
                ),
              ],
            ),
          ],
        ),
      ),
    ),
  );
}
