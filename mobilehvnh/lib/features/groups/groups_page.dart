import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../../core/widgets/app_avatar.dart';
import '../../core/widgets/app_page_bar.dart';
import '../../core/widgets/app_state_view.dart';
import '../../core/widgets/premium_hero_card.dart';
import '../../core/theme/app_theme.dart';
import '../feed/domain/repositories/feed_repository.dart';
import '../feed/feed_page.dart';
import '../feed/presentation/enhanced_post_composer_sheet.dart';
import 'domain/entities/group_upload_file.dart';
import 'domain/repositories/group_repository.dart';
import 'presentation/pages/group_admin_page.dart';
import 'presentation/pages/study_library_page.dart';

class GroupsPage extends StatefulWidget {
  const GroupsPage({
    super.key,
    required this.feedRepository,
    required this.groupRepository,
    this.currentUser,
    this.refreshSignal,
  });

  final FeedRepository feedRepository;
  final GroupRepository groupRepository;
  final Map<String, dynamic>? currentUser;
  final ValueListenable<int>? refreshSignal;

  @override
  State<GroupsPage> createState() => _GroupsPageState();
}

class _GroupsPageState extends State<GroupsPage> {
  List<dynamic> _groups = [];
  bool _loading = true;
  String? _error;
  String? _selectedGroupId;
  List<dynamic> _previewPosts = [];
  bool _previewLoading = false;
  int _previewGeneration = 0;
  static const _groupOrder = [
    'pass-do',
    'ghep-phong-tim-tro',
    'su-kien',
    'hoc-tap',
  ];

  @override
  void initState() {
    super.initState();
    widget.refreshSignal?.addListener(_load);
    _load();
  }

  @override
  void dispose() {
    widget.refreshSignal?.removeListener(_load);
    super.dispose();
  }

  Future<void> _load() async {
    if (mounted) setState(() => _loading = true);
    try {
      final groups = await widget.groupRepository.getGroups();
      groups.sort((a, b) {
        final left = _groupOrder.indexOf((a as Map)['slug']?.toString() ?? '');
        final right = _groupOrder.indexOf((b as Map)['slug']?.toString() ?? '');
        return (left < 0 ? 99 : left).compareTo(right < 0 ? 99 : right);
      });
      if (!mounted) return;
      _groups = groups;
      if (!_groups.any((group) => '${group['id']}' == _selectedGroupId)) {
        _selectedGroupId = _groups.isEmpty ? null : '${_groups.first['id']}';
      }
      _error = null;
      _loadPreview();
    } catch (error) {
      if (!mounted) return;
      _error = error.toString();
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _loadPreview() async {
    final generation = ++_previewGeneration;
    final group = _selectedGroup;
    final membership = group?['membership']?.toString();
    if (group == null ||
        (membership != 'MEMBER' &&
            membership != 'ADMIN' &&
            membership != 'PUBLIC')) {
      if (mounted) setState(() {
        _previewPosts = [];
        _previewLoading = false;
      });
      return;
    }
    if (mounted) {
      setState(() {
        _previewLoading = true;
        _previewPosts = [];
      });
    }
    try {
      final posts = await widget.groupRepository.getPosts(
        '${group['id']}',
        limit: 4,
      );
      if (mounted && generation == _previewGeneration) {
        setState(() => _previewPosts = posts);
      }
    } catch (_) {
      if (mounted && generation == _previewGeneration) {
        setState(() => _previewPosts = []);
      }
    } finally {
      if (mounted && generation == _previewGeneration) {
        setState(() => _previewLoading = false);
      }
    }
  }

  Map<dynamic, dynamic>? get _selectedGroup {
    for (final group in _groups) {
      if ('${group['id']}' == _selectedGroupId) {
        return group as Map<dynamic, dynamic>;
      }
    }
    return null;
  }

  Future<void> _openGroup(Map<dynamic, dynamic> group) async {
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => GroupDetailPage(
          group: group,
          feedRepository: widget.feedRepository,
          groupRepository: widget.groupRepository,
          currentUser: widget.currentUser,
        ),
      ),
    );
    if (mounted) _load();
  }

  @override
  Widget build(BuildContext context) {
    if (_loading && _groups.isEmpty) return const AppLoadingList(count: 4);
    if (_error != null && _groups.isEmpty) {
      return AppStateView(
        icon: Icons.wifi_off_rounded,
        title: 'Chưa tải được hội nhóm',
        message: _error!,
        actionLabel: 'Thử lại',
        onAction: _load,
      );
    }
    final selected = _selectedGroup;
    final membership = selected?['membership']?.toString() ?? 'NONE';
    final joined =
        membership == 'MEMBER' ||
        membership == 'ADMIN' ||
        membership == 'PUBLIC';
    return RefreshIndicator(
      onRefresh: _load,
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 820),
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
            children: [
              if (_loading) const LinearProgressIndicator(minHeight: 2),
              const PremiumHeroCard(
                padding: EdgeInsets.fromLTRB(20, 22, 20, 24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'CỘNG ĐỒNG HVNH',
                      style: TextStyle(
                        color: AppTheme.gold,
                        fontSize: 10,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 1,
                      ),
                    ),
                    SizedBox(height: 8),
                    Text(
                      'Bốn không gian dành cho sinh viên',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 23,
                        fontWeight: FontWeight.w800,
                        height: 1.2,
                      ),
                    ),
                    SizedBox(height: 7),
                    Text(
                      'Tham gia nhóm, chia sẻ và theo dõi bài viết được duyệt.',
                      style: TextStyle(color: Color(0xffd5eafa), height: 1.4),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              SizedBox(
                height: 92,
                child: ListView.separated(
                  scrollDirection: Axis.horizontal,
                  itemCount: _groups.length,
                  separatorBuilder: (_, _) => const SizedBox(width: 9),
                  itemBuilder: (context, index) {
                    final group = _groups[index] as Map<dynamic, dynamic>;
                    final active = '${group['id']}' == _selectedGroupId;
                    return _GroupSelector(
                      group: group,
                      selected: active,
                      onTap: () {
                        setState(() => _selectedGroupId = '${group['id']}');
                        _loadPreview();
                      },
                    );
                  },
                ),
              ),
              const SizedBox(height: 16),
              if (selected == null)
                const AppStateView(
                  icon: Icons.groups_outlined,
                  title: 'Chưa có hội nhóm',
                  message: 'Vui lòng quay lại sau.',
                )
              else ...[
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(18),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '${selected['name']}',
                          style: const TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.w800,
                            color: AppTheme.ink,
                          ),
                        ),
                        const SizedBox(height: 5),
                        Text(
                          '${selected['description'] ?? ''}',
                          style: const TextStyle(
                            color: AppTheme.muted,
                            height: 1.4,
                          ),
                        ),
                        const SizedBox(height: 9),
                        Text(
                          selected['slug'] == 'su-kien'
                              ? 'Công khai với mọi user'
                              : '${selected['member_count'] ?? 0} thành viên',
                          style: const TextStyle(
                            color: AppTheme.muted,
                            fontSize: 12,
                          ),
                        ),
                        const SizedBox(height: 14),
                        FilledButton(
                          onPressed: () => _openGroup(selected),
                          child: Text(
                            membership == 'PUBLIC'
                                ? 'Xem và đăng sự kiện công khai'
                                : joined
                                ? 'Xem bài viết và đăng trong nhóm'
                                : membership == 'PENDING'
                                ? 'Xem yêu cầu tham gia'
                                : 'Tham gia nhóm',
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                if (!joined)
                  const AppStateView(
                    icon: Icons.lock_outline_rounded,
                    title: 'Tham gia để xem bài viết',
                    message:
                        'Chỉ thành viên mới xem, thích và bình luận bài trong nhóm.',
                  )
                else ...[
                  Row(
                    children: [
                      const Expanded(
                        child: Text(
                          'Bài viết trong nhóm',
                          style: TextStyle(
                            fontSize: 17,
                            fontWeight: FontWeight.w800,
                            color: AppTheme.ink,
                          ),
                        ),
                      ),
                      Text(
                        '${_previewPosts.length} bài',
                        style: const TextStyle(
                          color: AppTheme.muted,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  if (_previewLoading)
                    const Center(
                      child: Padding(
                        padding: EdgeInsets.all(24),
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                    )
                  else if (_previewPosts.isEmpty)
                    const _GroupEmpty()
                  else
                    ..._previewPosts
                        .take(3)
                        .map(
                          (post) => PostCard(
                            post: post as Map<dynamic, dynamic>,
                            repository: widget.feedRepository,
                            onLike: () async {
                              await widget.feedRepository.setLike(
                                '${post['id']}',
                                !(post['isLiked'] ?? false),
                              );
                              _loadPreview();
                            },
                            onChanged: _loadPreview,
                          ),
                        ),
                  if (_previewPosts.length > 3)
                    Center(
                      child: TextButton(
                        onPressed: () => _openGroup(selected),
                        child: const Text('Xem tất cả bài viết'),
                      ),
                    ),
                ],
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _GroupSelector extends StatelessWidget {
  const _GroupSelector({
    required this.group,
    required this.selected,
    required this.onTap,
  });

  final Map<dynamic, dynamic> group;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final slug = '${group['slug']}';
    final icon = slug == 'pass-do'
        ? Icons.shopping_bag_outlined
        : slug == 'su-kien'
        ? Icons.event_outlined
        : slug == 'hoc-tap'
        ? Icons.menu_book_outlined
        : Icons.home_outlined;
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        width: 154,
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: selected ? AppTheme.softBlue : Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: selected ? AppTheme.blue : AppTheme.hairline,
            width: selected ? 1.5 : 1,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, size: 17, color: AppTheme.blue),
                const SizedBox(width: 5),
                Expanded(
                  child: Text(
                    '${group['name']}',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w800,
                      color: AppTheme.ink,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 7),
            Text(
              '${group['member_count'] ?? 0} thành viên',
              style: const TextStyle(fontSize: 11, color: AppTheme.muted),
            ),
          ],
        ),
      ),
    );
  }
}

class GroupDetailPage extends StatefulWidget {
  const GroupDetailPage({
    super.key,
    required this.group,
    required this.feedRepository,
    required this.groupRepository,
    this.currentUser,
  });
  final Map<dynamic, dynamic> group;
  final FeedRepository feedRepository;
  final GroupRepository groupRepository;
  final Map<String, dynamic>? currentUser;

  @override
  State<GroupDetailPage> createState() => _GroupDetailPageState();
}

class _GroupDetailPageState extends State<GroupDetailPage> {
  List<dynamic> _posts = [];
  bool _loading = true;
  bool _loadingMore = false;
  bool _hasMore = true;
  String? _error;
  late String _membership;
  final _search = TextEditingController();
  final _scrollController = ScrollController();
  String _sort = 'latest';
  bool _mine = false;
  int _loadGeneration = 0;

  @override
  void initState() {
    super.initState();
    _membership = widget.group['membership']?.toString() ?? 'NONE';
    _scrollController.addListener(_onScroll);
    _load();
  }

  bool get _joined =>
      _membership == 'MEMBER' ||
      _membership == 'ADMIN' ||
      _membership == 'PUBLIC';

  @override
  void dispose() {
    _search.dispose();
    _scrollController
      ..removeListener(_onScroll)
      ..dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollController.hasClients &&
        _scrollController.position.extentAfter < 500) {
      _loadMore();
    }
  }

  Future<void> _load() async {
    final generation = ++_loadGeneration;
    if (mounted) {
      setState(() {
        _loading = true;
        _loadingMore = false;
        _hasMore = true;
        _posts = [];
      });
    }
    if (!_joined) {
      if (mounted) {
        setState(() {
          _posts = [];
          _hasMore = false;
          _error = null;
          _loading = false;
        });
      }
      return;
    }
    try {
      final posts = await widget.groupRepository.getPosts(
        '${widget.group['id']}',
        query: _mine ? '' : _search.text,
        sort: _sort,
        mine: _mine,
        limit: 10,
        offset: 0,
      );
      if (!mounted || generation != _loadGeneration) return;
      setState(() {
        _posts = posts;
        _hasMore = posts.length == 10;
        _error = null;
      });
    } catch (error) {
      if (mounted && generation == _loadGeneration) {
        setState(() => _error = error.toString());
      }
    } finally {
      if (mounted && generation == _loadGeneration) {
        setState(() => _loading = false);
      }
    }
  }

  Future<void> _loadMore() async {
    if (_loading || _loadingMore || !_hasMore || !_joined) return;
    final generation = _loadGeneration;
    setState(() => _loadingMore = true);
    try {
      final incoming = await widget.groupRepository.getPosts(
        '${widget.group['id']}',
        query: _mine ? '' : _search.text,
        sort: _sort,
        mine: _mine,
        limit: 10,
        offset: _posts.length,
      );
      if (!mounted || generation != _loadGeneration) return;
      final ids = _posts.map((item) => item['id']?.toString()).toSet();
      setState(() {
        _posts.addAll(
          incoming.where((item) => !ids.contains(item['id']?.toString())),
        );
        _hasMore = incoming.length == 10;
      });
    } catch (error) {
      if (mounted && generation == _loadGeneration) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Không tải thêm được bài viết: $error')),
        );
      }
    } finally {
      if (mounted && generation == _loadGeneration) {
        setState(() => _loadingMore = false);
      }
    }
  }

  Future<void> _join() async {
    try {
      await widget.groupRepository.requestJoin('${widget.group['id']}');
      if (mounted) {
        setState(() => _membership = 'PENDING');
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Yêu cầu tham gia đã được gửi.')),
        );
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.toString())));
      }
    }
  }

  Future<void> _leave() async {
    try {
      await widget.groupRepository.leaveGroup('${widget.group['id']}');
      if (mounted) {
        setState(() {
          _membership = 'NONE';
          _posts = [];
        });
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('Bạn đã rời hội nhóm.')));
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.toString())));
      }
    }
  }

  Future<void> _compose() {
    const categoryBySlug = <String, String>{
      'pass-do': 'market',
      'ghep-phong-tim-tro': 'roommate',
      'su-kien': 'event',
      'hoc-tap': 'study',
    };
    final category = categoryBySlug[widget.group['slug']] ?? 'general';
    return showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (_) => EnhancedPostComposerSheet(
        repository: widget.feedRepository,
        initialCategory: category,
        allowedCategories: [category],
        groupName: widget.group['name']?.toString(),
        onSubmit: _createPost,
      ),
    );
  }

  Future<void> _createPost(EnhancedPostDraft draft) async {
    await widget.groupRepository.createPost(
      '${widget.group['id']}',
      draft.content,
      draft.files
          .map(
            (file) => GroupUploadFile(
              name: file.name,
              size: file.size,
              path: file.path,
              bytes: file.bytes,
            ),
          )
          .toList(),
      marketListing: draft.marketListing,
      roomListing: draft.roomListing,
      eventListing: draft.eventListing,
      studyListing: draft.studyListing,
      location: draft.location,
    );
    await _load();
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Bài viết đã gửi, chờ quản trị viên duyệt.'),
        ),
      );
    }
  }

  Future<void> _like(Map<dynamic, dynamic> post) async {
    try {
      final result = await widget.feedRepository.setLike(
        '${post['id']}',
        !(post['isLiked'] ?? false),
      );
      if (mounted) {
        setState(() {
          post['isLiked'] = result['isLiked'];
          post['likesCount'] = result['likesCount'];
        });
      }
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
    appBar: AppPageBar(title: '${widget.group['name']}'),
    body: RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        controller: _scrollController,
        physics: const BouncingScrollPhysics(
          parent: AlwaysScrollableScrollPhysics(),
        ),
        padding: const EdgeInsets.fromLTRB(12, 12, 12, 32),
        children: [
          Card(
            clipBehavior: Clip.antiAlias,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  height: 86,
                  width: double.infinity,
                  alignment: Alignment.centerLeft,
                  padding: const EdgeInsets.only(left: 20),
                  decoration: const BoxDecoration(
                    gradient: LinearGradient(
                      colors: [Color(0xff0a2b4b), Color(0xff246b98)],
                    ),
                  ),
                  child: Container(
                    width: 52,
                    height: 52,
                    decoration: BoxDecoration(
                      color: const Color(0xf7ffffff),
                      borderRadius: BorderRadius.circular(15),
                    ),
                    child: const Icon(
                      Icons.groups_rounded,
                      color: AppTheme.blue,
                    ),
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.fromLTRB(18, 15, 18, 18),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              '${widget.group['name']}',
                              style: const TextStyle(
                                fontSize: 22,
                                fontWeight: FontWeight.w800,
                                color: AppTheme.ink,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 5),
                      Text(
                        widget.group['slug'] == 'su-kien'
                            ? 'Công khai với mọi user'
                            : '${widget.group['member_count'] ?? 0} thành viên',
                        style: const TextStyle(
                          color: AppTheme.muted,
                          fontSize: 13,
                        ),
                      ),
                      if ('${widget.group['description'] ?? ''}'
                          .trim()
                          .isNotEmpty) ...[
                        const SizedBox(height: 10),
                        Text(
                          '${widget.group['description']}',
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            color: AppTheme.ink,
                            height: 1.4,
                          ),
                        ),
                      ],
                      const SizedBox(height: 15),
                      if (_membership != 'ADMIN' &&
                          widget.group['slug'] == 'su-kien')
                        const Chip(
                          avatar: Icon(Icons.public, size: 16),
                          label: Text('Công khai · Không cần xin tham gia'),
                        ),
                      if (_membership == 'ADMIN')
                        OutlinedButton.icon(
                          onPressed: () => Navigator.of(context).push(
                            MaterialPageRoute(
                              builder: (_) => GroupAdminPage(
                                groupId: '${widget.group['id']}',
                                groupName: '${widget.group['name']}',
                                groupSlug: '${widget.group['slug']}',
                                groupRepository: widget.groupRepository,
                                feedRepository: widget.feedRepository,
                              ),
                            ),
                          ),
                          icon: const Icon(
                            Icons.admin_panel_settings_outlined,
                          ),
                          label: const Text('Quản trị nhóm'),
                        )
                      else if (_membership == 'MEMBER' &&
                          widget.group['slug'] != 'su-kien')
                        OutlinedButton.icon(
                          onPressed: _leave,
                          icon: const Icon(Icons.check_circle_outline),
                          label: const Text('Đã tham gia · Rời nhóm'),
                        )
                      else if (!_joined)
                        FilledButton.icon(
                          onPressed: _membership == 'PENDING' ? null : _join,
                          icon: Icon(
                            _membership == 'PENDING'
                                ? Icons.schedule
                                : Icons.group_add_outlined,
                          ),
                          label: Text(
                            _membership == 'PENDING'
                                ? 'Đang chờ duyệt'
                                : 'Tham gia nhóm',
                          ),
                        ),
                      if (_joined && widget.group['slug'] == 'hoc-tap')
                        OutlinedButton.icon(
                          onPressed: () => Navigator.of(context).push(
                            MaterialPageRoute(
                              builder: (_) => StudyLibraryPage(
                                groupId: '${widget.group['id']}',
                                repository: widget.groupRepository,
                                isAdmin: _membership == 'ADMIN',
                              ),
                            ),
                          ),
                          icon: const Icon(Icons.library_books_outlined),
                          label: const Text('Kho tài liệu'),
                        ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          if (_joined) ...[
            Card(
              child: InkWell(
                onTap: _compose,
                borderRadius: BorderRadius.circular(20),
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(16, 14, 16, 12),
                  child: Column(
                    children: [
                      Row(
                        children: [
                          AppAvatar(
                            radius: 23,
                            url: widget.currentUser?['avatar']?.toString(),
                            name: widget.currentUser?['name']?.toString(),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  '${widget.currentUser?['name'] ?? 'Sinh viên HVNH'}',
                                  style: const TextStyle(
                                    color: AppTheme.ink,
                                    fontSize: 13,
                                    fontWeight: FontWeight.w800,
                                  ),
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  'Bạn muốn chia sẻ điều gì?',
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(
                                    color: AppTheme.muted,
                                    fontSize: 13,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          const Icon(
                            Icons.edit_outlined,
                            color: AppTheme.blue,
                            size: 20,
                          ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      const Divider(),
                      const SizedBox(height: 9),
                      const Row(
                        children: [
                          Icon(
                            Icons.add_photo_alternate_outlined,
                            color: AppTheme.blue,
                            size: 18,
                          ),
                          SizedBox(width: 7),
                          Text(
                            'Ảnh / Video / Tệp',
                            style: TextStyle(
                              color: AppTheme.blue,
                              fontSize: 12,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                          SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              'Chờ duyệt trước khi hiển thị',
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              textAlign: TextAlign.end,
                              style: TextStyle(
                                color: AppTheme.muted,
                                fontSize: 11,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 12),
          ],
          if (_joined)
            Padding(
              padding: const EdgeInsets.fromLTRB(4, 2, 4, 10),
              child: Row(
                children: [
                  const Expanded(
                    child: Text(
                      'Bài viết trong nhóm',
                      style: TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.w800,
                        color: AppTheme.ink,
                      ),
                    ),
                  ),
                  Text(
                    '${_posts.length} bài',
                    style: const TextStyle(color: AppTheme.muted, fontSize: 12),
                  ),
                ],
              ),
            ),
          if (_joined)
            TextField(
              controller: _search,
              textInputAction: TextInputAction.search,
              onChanged: (_) => setState(() {}),
              onSubmitted: (_) => _load(),
              decoration: InputDecoration(
                hintText: 'Tìm bài viết trong nhóm',
                prefixIcon: const Icon(Icons.search_rounded),
                suffixIcon: _search.text.isEmpty
                    ? null
                    : IconButton(
                        tooltip: 'Xóa tìm kiếm',
                        onPressed: () {
                          _search.clear();
                          _load();
                        },
                        icon: const Icon(Icons.close_rounded),
                      ),
              ),
            ),
          if (_joined) const SizedBox(height: 9),
          if (_joined)
            Row(
              children: [
                PopupMenuButton<String>(
                  tooltip: 'Sắp xếp bài viết',
                  onSelected: (value) {
                    _sort = value;
                    _load();
                  },
                  itemBuilder: (_) => const [
                    PopupMenuItem(value: 'latest', child: Text('Mới nhất')),
                    PopupMenuItem(value: 'featured', child: Text('Nổi bật')),
                    PopupMenuItem(value: 'pinned', child: Text('Đã ghim')),
                  ],
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 13,
                      vertical: 10,
                    ),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      border: Border.all(color: AppTheme.hairline),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(
                          Icons.sort_rounded,
                          size: 18,
                          color: AppTheme.blue,
                        ),
                        const SizedBox(width: 6),
                        Text(switch (_sort) {
                          'featured' => 'Nổi bật',
                          'pinned' => 'Đã ghim',
                          _ => 'Mới nhất',
                        }, style: const TextStyle(fontWeight: FontWeight.w700)),
                      ],
                    ),
                  ),
                ),
                const SizedBox(width: 9),
                FilterChip(
                  selected: _mine,
                  avatar: const Icon(Icons.person_outline, size: 18),
                  label: const Text('Bài của tôi'),
                  onSelected: (value) {
                    setState(() => _mine = value);
                    _load();
                  },
                ),
              ],
            ),
          if (_joined) const SizedBox(height: 12),
          if (!_joined)
            const AppStateView(
              icon: Icons.lock_outline_rounded,
              title: 'Tham gia nhóm để xem bài viết',
              message: 'Quản trị viên sẽ duyệt yêu cầu tham gia của bạn.',
            )
          else if (_loading)
            const Padding(
              padding: EdgeInsets.all(24),
              child: Center(child: CircularProgressIndicator()),
            )
          else if (_error != null)
            Card(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  children: [
                    Text(_error!, textAlign: TextAlign.center),
                    const SizedBox(height: 10),
                    OutlinedButton.icon(
                      onPressed: _load,
                      icon: const Icon(Icons.refresh),
                      label: const Text('Thử lại'),
                    ),
                  ],
                ),
              ),
            )
          else if (_posts.isEmpty)
            const _GroupEmpty()
          else
            ..._posts.map(
              (post) => PostCard(
                post: post as Map<dynamic, dynamic>,
                repository: widget.feedRepository,
                onLike: () => _like(post),
              ),
            ),
          if (_loadingMore)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 18),
              child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
            ),
        ],
      ),
    ),
  );
}

class _GroupEmpty extends StatelessWidget {
  const _GroupEmpty();

  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(34),
      child: Column(
        children: const [
          Icon(Icons.forum_outlined, size: 42, color: Color(0xff86a0bf)),
          SizedBox(height: 12),
          Text(
            'Chưa có bài viết được duyệt',
            style: TextStyle(fontWeight: FontWeight.w800),
          ),
          SizedBox(height: 6),
          Text(
            'Hãy quay lại sau hoặc đóng góp bài viết đầu tiên.',
            textAlign: TextAlign.center,
            style: TextStyle(color: Color(0xff63758c)),
          ),
        ],
      ),
    ),
  );
}
