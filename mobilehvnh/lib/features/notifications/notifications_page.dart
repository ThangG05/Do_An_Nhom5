import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../../core/utils/app_date_time.dart';
import '../../core/widgets/app_avatar.dart';
import '../../core/widgets/app_page_bar.dart';
import '../../core/theme/app_theme.dart';
import '../feed/domain/repositories/feed_repository.dart';
import '../feed/feed_page.dart';
import 'domain/repositories/notification_repository.dart';

class NotificationsPage extends StatefulWidget {
  const NotificationsPage({
    super.key,
    required this.repository,
    required this.feedRepository,
    this.refreshSignal,
  });
  final NotificationRepository repository;
  final FeedRepository feedRepository;
  final ValueListenable<int>? refreshSignal;

  @override
  State<NotificationsPage> createState() => _NotificationsPageState();
}

class _NotificationsPageState extends State<NotificationsPage> {
  List<dynamic> _items = [];
  int _unread = 0;
  int _total = 0;
  bool _loading = true;
  bool _loadingMore = false;
  String _filter = 'all';
  String? _error;
  int _generation = 0;

  @override
  void initState() {
    super.initState();
    widget.refreshSignal?.addListener(_refresh);
    _load();
  }

  @override
  void dispose() {
    widget.refreshSignal?.removeListener(_refresh);
    super.dispose();
  }

  void _refresh() {
    if (mounted) _load();
  }

  Future<void> _load() async {
    final generation = ++_generation;
    if (mounted) setState(() => _loading = true);
    try {
      final page = await widget.repository.getPage(filter: _filter);
      if (!mounted || generation != _generation) return;
      _items = (page['items'] as List?) ?? [];
      _unread = (page['unread_count'] as num?)?.toInt() ?? 0;
      _total = (page['total'] as num?)?.toInt() ?? _items.length;
      _error = null;
    } catch (_) {
      if (mounted && generation == _generation) {
        _error = 'Không thể tải thông báo. Vui lòng thử lại.';
      }
    } finally {
      if (mounted && generation == _generation) {
        setState(() => _loading = false);
      }
    }
  }

  Future<void> _loadMore() async {
    if (_loadingMore || _items.length >= _total) return;
    final generation = _generation;
    setState(() => _loadingMore = true);
    try {
      final page = await widget.repository.getPage(
        filter: _filter,
        offset: _items.length,
      );
      if (mounted && generation == _generation) {
        setState(() => _items.addAll((page['items'] as List?) ?? []));
      }
    } catch (_) {
      if (mounted && generation == _generation) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Không thể tải thêm thông báo. Vui lòng thử lại.'),
          ),
        );
      }
    } finally {
      if (mounted && generation == _generation) {
        setState(() => _loadingMore = false);
      }
    }
  }

  Future<void> _readAll() async {
    await widget.repository.readAll();
    await _load();
  }

  Future<void> _remove(Map<dynamic, dynamic> item) async {
    await widget.repository.delete('${item['id']}');
    await _load();
  }

  Future<void> _open(Map<dynamic, dynamic> item) async {
    if (item['is_unread'] == true) {
      await widget.repository.setRead('${item['id']}', true);
      await _load();
    }
    if (!mounted ||
        item['reference_type']?.toString() != 'POST' ||
        item['reference_id'] == null) {
      return;
    }
    final payload = item['payload'] is Map ? item['payload'] as Map : const {};
    final commentId = payload['comment_id']?.toString();
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => PostDetailPage(
          postId: '${item['reference_id']}',
          repository: widget.feedRepository,
          highlightCommentId: commentId,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final children = <Widget>[
      Card(
        child: Padding(
          padding: const EdgeInsets.all(17),
          child: Column(
            children: [
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Thông báo của tôi',
                          style: TextStyle(
                            fontSize: 25,
                            fontWeight: FontWeight.w800,
                            color: AppTheme.ink,
                          ),
                        ),
                        const SizedBox(height: 3),
                        Text(
                          _unread > 0
                              ? 'Bạn có $_unread thông báo chưa đọc'
                              : 'Bạn đã cập nhật mọi hoạt động',
                          style: const TextStyle(
                            color: AppTheme.muted,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
                  if (_unread > 0)
                    TextButton(
                      onPressed: _readAll,
                      child: const Text('Đánh dấu đã đọc'),
                    ),
                ],
              ),
              const SizedBox(height: 13),
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    _filterChip('all', 'Tất cả ($_total)'),
                    const SizedBox(width: 7),
                    _filterChip('unread', 'Chưa đọc ($_unread)'),
                    const SizedBox(width: 7),
                    _filterChip('friends', 'Lời mời kết bạn'),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
      const SizedBox(height: 14),
    ];
    if (_loading && _items.isEmpty) {
      children.add(
        const Center(
          child: Padding(
            padding: EdgeInsets.all(30),
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
        ),
      );
    } else if (_error != null) {
      children.add(
        Card(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              children: [
                Text(_error!),
                TextButton(onPressed: _load, child: const Text('Thử lại')),
              ],
            ),
          ),
        ),
      );
    } else if (_items.isEmpty) {
      children.add(
        const Card(
          child: Padding(
            padding: EdgeInsets.symmetric(horizontal: 24, vertical: 42),
            child: Column(
              children: [
                CircleAvatar(
                  radius: 28,
                  backgroundColor: Color(0xffe5f1f8),
                  child: Icon(
                    Icons.notifications_none,
                    color: AppTheme.blue,
                    size: 28,
                  ),
                ),
                SizedBox(height: 13),
                Text(
                  'Chưa có thông báo',
                  style: TextStyle(
                    color: AppTheme.ink,
                    fontWeight: FontWeight.w800,
                    fontSize: 16,
                  ),
                ),
                SizedBox(height: 5),
                Text(
                  'Lượt thích và bình luận mới sẽ xuất hiện tại đây.',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: AppTheme.muted, height: 1.4),
                ),
              ],
            ),
          ),
        ),
      );
    }
    for (final value in _items) {
      final item = value as Map<dynamic, dynamic>;
      final unread = item['is_unread'] == true;
      children.add(
        Dismissible(
          key: ValueKey('${item['id']}'),
          direction: DismissDirection.endToStart,
          confirmDismiss: (_) async {
            try {
              await _remove(item);
              return false;
            } catch (error) {
              if (!context.mounted) return false;
              ScaffoldMessenger.of(
                context,
              ).showSnackBar(SnackBar(content: Text(error.toString())));
              return false;
            }
          },
          background: Container(
            alignment: Alignment.centerRight,
            padding: const EdgeInsets.only(right: 22),
            color: Colors.red,
            child: const Icon(Icons.delete_outline, color: Colors.white),
          ),
          child: Card(
            margin: const EdgeInsets.only(bottom: 8),
            color: unread ? const Color(0xfff0f7fb) : Colors.white,
            child: ListTile(
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 15,
                vertical: 7,
              ),
              onTap: () => _open(item),
              leading: AppAvatar(
                url: item['actor_avatar']?.toString(),
                name: item['actor_name']?.toString(),
              ),
              title: Text(
                '${item['title'] ?? 'Thông báo'}',
                style: TextStyle(
                  fontWeight: unread ? FontWeight.w800 : FontWeight.w600,
                ),
              ),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '${item['content'] ?? ''}',
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 3),
                  Tooltip(
                    message: AppDateTime.full(item['created_at']),
                    child: Text(
                      AppDateTime.relative(item['created_at']),
                      style: const TextStyle(
                        fontSize: 11,
                        color: Color(0xff71839a),
                      ),
                    ),
                  ),
                ],
              ),
              trailing: unread
                  ? const Icon(Icons.circle, size: 9, color: Color(0xff0866c6))
                  : null,
            ),
          ),
        ),
      );
    }
    if (_items.length < _total) {
      children.add(
        Center(
          child: TextButton(
            onPressed: _loadingMore ? null : _loadMore,
            child: Text(_loadingMore ? 'Đang tải...' : 'Tải thêm'),
          ),
        ),
      );
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 760),
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 20, 16, 32),
            children: children,
          ),
        ),
      ),
    );
  }

  Widget _filterChip(String value, String label) => ChoiceChip(
    label: Text(label),
    selected: _filter == value,
    onSelected: (_) {
      if (_filter == value) return;
      setState(() {
        _filter = value;
        _items = [];
        _total = 0;
      });
      _load();
    },
  );
}

class PostDetailPage extends StatefulWidget {
  const PostDetailPage({
    super.key,
    required this.postId,
    required this.repository,
    this.highlightCommentId,
  });
  final String postId;
  final FeedRepository repository;
  final String? highlightCommentId;

  @override
  State<PostDetailPage> createState() => _PostDetailPageState();
}

class _PostDetailPageState extends State<PostDetailPage> {
  Map<dynamic, dynamic>? _post;
  String? _error;
  bool _openedComment = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      _post = await widget.repository.getPost(widget.postId);
    } catch (error) {
      _error = error.toString();
    }
    if (mounted) {
      setState(() {});
      if (_post != null &&
          widget.highlightCommentId != null &&
          !_openedComment) {
        _openedComment = true;
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (!mounted) return;
          showModalBottomSheet<void>(
            context: context,
            isScrollControlled: true,
            builder: (_) => CommentSheet(
              postId: widget.postId,
              repository: widget.repository,
              highlightCommentId: widget.highlightCommentId,
            ),
          );
        });
      }
    }
  }

  Future<void> _like() async {
    if (_post == null) return;
    final result = await widget.repository.setLike(
      widget.postId,
      !(_post!['isLiked'] ?? false),
    );
    if (mounted) {
      setState(() {
        _post!['isLiked'] = result['isLiked'];
        _post!['likesCount'] = result['likesCount'];
      });
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: const AppPageBar(title: 'Bài viết'),
    body: _post != null
        ? ListView(
            padding: const EdgeInsets.all(12),
            children: [
              PostCard(
                post: _post!,
                repository: widget.repository,
                onLike: _like,
              ),
            ],
          )
        : Center(child: Text(_error ?? 'Đang tải bài viết...')),
  );
}
