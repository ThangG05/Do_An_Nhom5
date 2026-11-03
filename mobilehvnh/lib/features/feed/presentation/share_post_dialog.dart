import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../core/app_config.dart';
import '../../../core/api_client.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/app_avatar.dart';
import '../../chat/domain/repositories/chat_repository.dart';
import '../../user/domain/repositories/user_repository.dart';
import '../domain/repositories/feed_repository.dart';

Future<bool> showSharePostDialog({
  required BuildContext context,
  required Map<String, dynamic> post,
  required String? viewerId,
  required FeedRepository feedRepository,
  ChatRepository? chatRepository,
  UserRepository? userRepository,
  ValueChanged<int>? onSharesUpdated,
}) async =>
    await showDialog<bool>(
      context: context,
      barrierDismissible: true,
      builder: (_) => _SharePostDialog(
        post: post,
        viewerId: viewerId,
        feedRepository: feedRepository,
        chatRepository: chatRepository,
        userRepository: userRepository,
        onSharesUpdated: onSharesUpdated,
      ),
    ) ??
    false;

class _SharePostDialog extends StatefulWidget {
  const _SharePostDialog({
    required this.post,
    required this.viewerId,
    required this.feedRepository,
    required this.chatRepository,
    required this.userRepository,
    required this.onSharesUpdated,
  });

  final Map<String, dynamic> post;
  final String? viewerId;
  final FeedRepository feedRepository;
  final ChatRepository? chatRepository;
  final UserRepository? userRepository;
  final ValueChanged<int>? onSharesUpdated;

  @override
  State<_SharePostDialog> createState() => _SharePostDialogState();
}

class _SharePostDialogState extends State<_SharePostDialog> {
  final _caption = TextEditingController();
  final _search = TextEditingController();
  final _selectedFriends = <String>{};
  List<Map<String, dynamic>> _friends = const [];
  String _tab = 'profile';
  String _privacy = 'friends';
  bool _loadingFriends = false;
  bool _busy = false;
  String? _error;
  bool _copied = false;

  String get _postId => widget.post['id']?.toString() ?? '';
  String get _postUrl =>
      '${AppConfig.webBaseUrl.replaceFirst(RegExp(r'/$'), '')}/posts/$_postId';
  Map get _author =>
      widget.post['author'] is Map ? widget.post['author'] as Map : const {};

  @override
  void initState() {
    super.initState();
    if (widget.chatRepository == null || widget.userRepository == null) {
      _tab = 'profile';
    }
  }

  @override
  void dispose() {
    _caption.dispose();
    _search.dispose();
    super.dispose();
  }

  Future<void> _loadFriends() async {
    if (_friends.isNotEmpty || _loadingFriends) return;
    if (widget.viewerId == null || widget.userRepository == null) {
      setState(() => _error = 'Danh sách bạn bè hiện chưa khả dụng.');
      return;
    }
    setState(() {
      _loadingFriends = true;
      _error = null;
    });
    try {
      final rows = await widget.userRepository!.getFriends(widget.viewerId!);
      if (!mounted) return;
      setState(() {
        _friends = rows
            .where((row) => row['id']?.toString() != widget.viewerId)
            .toList();
      });
    } catch (error) {
      if (mounted) setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _loadingFriends = false);
    }
  }

  Future<void> _copyLink() async {
    try {
      await Clipboard.setData(ClipboardData(text: _postUrl));
      if (mounted) setState(() => _copied = true);
    } catch (error) {
      if (mounted) {
        setState(() => _error = 'Không sao chép được liên kết: $error');
      }
    }
  }

  Future<void> _submit() async {
    if (_busy || _postId.isEmpty) return;
    if (_tab == 'link') {
      await _copyLink();
      return;
    }
    if (_tab == 'message' && _selectedFriends.isEmpty) {
      setState(() => _error = 'Hãy chọn ít nhất một người bạn để gửi.');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      if (_tab == 'profile') {
        final created = await widget.feedRepository.createPost(
          content: _caption.text.trim().isEmpty
              ? 'Đã chia sẻ bài viết này.'
              : _caption.text.trim(),
          files: const [],
          privacy: _privacy,
        );
        final destinationId = created['id']?.toString() ?? '';
        if (destinationId.isEmpty) {
          throw StateError('Không nhận được mã bài viết chia sẻ.');
        }
        Map<String, dynamic> result;
        try {
          result = await widget.feedRepository.registerShare(
            _postId,
            destinationType: 'POST',
            destinationId: destinationId,
          );
        } catch (error) {
          // A definite client-side rejection means this destination cannot be
          // attached to the source post. Remove the caption-only orphan, but
          // keep it on network/5xx errors where registration may have committed.
          if (error is ApiException && error.statusCode >= 400 && error.statusCode < 500) {
            try {
              await widget.feedRepository.deletePost(destinationId);
            } catch (_) {
              // Preserve the original share error for the user.
            }
          }
          rethrow;
        }
        widget.onSharesUpdated?.call(
          (result['sharesCount'] as num?)?.toInt() ?? 0,
        );
      } else {
        final chat = widget.chatRepository!;
        final note = _caption.text.trim();
        final recipients = _friends
            .where(
              (friend) => _selectedFriends.contains(friend['id']?.toString()),
            )
            .toList();
        var sent = 0;
        for (final friend in recipients) {
          final conversation = await chat.createDirectConversation(
            friend['id'].toString(),
          );
          final message = await chat.sendMessage(
            conversation['id'].toString(),
            '${note.isEmpty ? '' : '$note\n'}$_postUrl',
            const [],
          );
          final result = await widget.feedRepository.registerShare(
            _postId,
            destinationType: 'MESSAGE',
            destinationId: message['id'].toString(),
          );
          widget.onSharesUpdated?.call(
            (result['sharesCount'] as num?)?.toInt() ?? 0,
          );
          sent++;
        }
        if (sent == 0) throw StateError('Không có người nhận hợp lệ.');
      }
      if (mounted) Navigator.of(context).pop(true);
    } catch (error) {
      if (mounted) setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final screen = MediaQuery.sizeOf(context);
    final query = _search.text.trim().toLowerCase();
    final friends = _friends.where((friend) {
      final name = '${friend['name'] ?? ''} ${friend['username'] ?? ''}'
          .toLowerCase();
      return query.isEmpty || name.contains(query);
    }).toList();
    final postContent = widget.post['content']?.toString().trim() ?? '';

    return Dialog(
      insetPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 20),
      backgroundColor: Colors.white,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(22)),
      child: ConstrainedBox(
        constraints: BoxConstraints(
          maxWidth: 500,
          maxHeight: screen.height * .9,
          minWidth: screen.width < 540 ? screen.width - 24 : 420,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(18, 16, 12, 12),
              child: Row(
                children: [
                  const Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'HVNH HUB',
                          style: TextStyle(
                            color: AppTheme.blue,
                            fontSize: 10,
                            fontWeight: FontWeight.w800,
                            letterSpacing: 1,
                          ),
                        ),
                        SizedBox(height: 4),
                        Text(
                          'Chia sẻ bài viết',
                          style: TextStyle(
                            color: AppTheme.ink,
                            fontSize: 21,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    tooltip: 'Đóng',
                    onPressed: _busy ? null : () => Navigator.pop(context),
                    icon: const Icon(Icons.close_rounded),
                    style: IconButton.styleFrom(
                      backgroundColor: AppTheme.canvas,
                    ),
                  ),
                ],
              ),
            ),
            Flexible(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    _PostSharePreview(
                      author: _author,
                      post: widget.post,
                      content: postContent,
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        _TabButton(
                          label: 'Tin nhắn',
                          active: _tab == 'message',
                          onTap:
                              widget.chatRepository == null ||
                                  widget.userRepository == null
                              ? null
                              : () {
                                  setState(() {
                                    _tab = 'message';
                                    _error = null;
                                  });
                                  _loadFriends();
                                },
                        ),
                        _TabButton(
                          label: 'Trang cá nhân',
                          active: _tab == 'profile',
                          onTap: () => setState(() {
                            _tab = 'profile';
                            _error = null;
                          }),
                        ),
                        _TabButton(
                          label: 'Sao chép link',
                          active: _tab == 'link',
                          onTap: () => setState(() {
                            _tab = 'link';
                            _error = null;
                          }),
                        ),
                      ],
                    ),
                    const Divider(height: 1),
                    const SizedBox(height: 14),
                    if (_tab == 'profile') ...[
                      const _FieldLabel('Bạn muốn nói gì về bài viết này?'),
                      const SizedBox(height: 7),
                      TextField(
                        controller: _caption,
                        minLines: 3,
                        maxLines: 5,
                        maxLength: 2000,
                        decoration: const InputDecoration(
                          hintText: 'Viết cảm nghĩ của bạn…',
                          alignLabelWithHint: true,
                        ),
                      ),
                      const SizedBox(height: 8),
                      const _FieldLabel('Ai có thể xem bài chia sẻ?'),
                      const SizedBox(height: 7),
                      DropdownButtonFormField<String>(
                        initialValue: _privacy,
                        items: const [
                          DropdownMenuItem(
                            value: 'public',
                            child: Text('Công khai'),
                          ),
                          DropdownMenuItem(
                            value: 'friends',
                            child: Text('Bạn bè'),
                          ),
                          DropdownMenuItem(
                            value: 'private',
                            child: Text('Chỉ mình tôi'),
                          ),
                        ],
                        onChanged: _busy
                            ? null
                            : (value) {
                                if (value != null) {
                                  setState(() => _privacy = value);
                                }
                              },
                        decoration: const InputDecoration(
                          contentPadding: EdgeInsets.symmetric(
                            horizontal: 12,
                            vertical: 12,
                          ),
                        ),
                      ),
                    ],
                    if (_tab == 'message') ...[
                      const _FieldLabel('Gửi cho bạn bè'),
                      const SizedBox(height: 7),
                      TextField(
                        controller: _search,
                        onChanged: (_) => setState(() {}),
                        decoration: const InputDecoration(
                          hintText: 'Tìm tên bạn bè…',
                          prefixIcon: Icon(Icons.search),
                          isDense: true,
                        ),
                      ),
                      const SizedBox(height: 6),
                      ConstrainedBox(
                        constraints: const BoxConstraints(maxHeight: 170),
                        child: _loadingFriends
                            ? const Center(
                                child: Padding(
                                  padding: EdgeInsets.all(18),
                                  child: CircularProgressIndicator(),
                                ),
                              )
                            : friends.isEmpty
                            ? Padding(
                                padding: const EdgeInsets.all(12),
                                child: Text(
                                  _friends.isEmpty
                                      ? 'Bạn chưa có bạn bè để gửi.'
                                      : 'Không tìm thấy bạn bè phù hợp.',
                                  style: const TextStyle(color: AppTheme.muted),
                                ),
                              )
                            : ListView.builder(
                                shrinkWrap: true,
                                itemCount: friends.length,
                                itemBuilder: (context, index) {
                                  final friend = friends[index];
                                  final id = friend['id']?.toString() ?? '';
                                  return CheckboxListTile(
                                    dense: true,
                                    contentPadding: EdgeInsets.zero,
                                    value: _selectedFriends.contains(id),
                                    onChanged: _busy
                                        ? null
                                        : (selected) => setState(() {
                                            if (selected == true) {
                                              _selectedFriends.add(id);
                                            } else {
                                              _selectedFriends.remove(id);
                                            }
                                          }),
                                    secondary: AppAvatar(
                                      radius: 19,
                                      url: friend['avatar']?.toString(),
                                      name: friend['name']?.toString(),
                                    ),
                                    title: Text(
                                      '${friend['name'] ?? 'Sinh viên HVNH'}',
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                    subtitle: Text(
                                      '@${friend['username'] ?? ''}',
                                    ),
                                  );
                                },
                              ),
                      ),
                      const SizedBox(height: 8),
                      TextField(
                        controller: _caption,
                        minLines: 2,
                        maxLines: 4,
                        maxLength: 500,
                        decoration: const InputDecoration(
                          hintText: 'Thêm lời nhắn (không bắt buộc)…',
                          alignLabelWithHint: true,
                        ),
                      ),
                    ],
                    if (_tab == 'link') ...[
                      const _FieldLabel('Liên kết bài viết'),
                      const SizedBox(height: 7),
                      SelectableText(_postUrl),
                    ],
                    const Text(
                      'Người mở liên kết vẫn cần có quyền xem bài gốc; bài trong nhóm chỉ hiển thị với thành viên.',
                      style: TextStyle(
                        color: AppTheme.muted,
                        fontSize: 11,
                        height: 1.4,
                      ),
                    ),
                    if (_copied && _tab == 'link')
                      const Padding(
                        padding: EdgeInsets.only(top: 8),
                        child: Text(
                          'Đã sao chép liên kết bài viết.',
                          style: TextStyle(color: Color(0xff16824b)),
                        ),
                      ),
                    if (_error != null)
                      Padding(
                        padding: const EdgeInsets.only(top: 8),
                        child: Text(
                          _error!,
                          style: const TextStyle(color: Colors.red),
                        ),
                      ),
                  ],
                ),
              ),
            ),
            const Divider(height: 1),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 10, 16, 14),
              child: Row(
                children: [
                  OutlinedButton(
                    onPressed: _busy ? null : () => Navigator.pop(context),
                    child: const Text('Đóng'),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: FilledButton(
                      onPressed: _busy ? null : _submit,
                      child: _busy
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: Colors.white,
                              ),
                            )
                          : Text(
                              _tab == 'link'
                                  ? (_copied ? 'Đã sao chép' : 'Sao chép link')
                                  : _tab == 'message'
                                  ? 'Gửi bài viết'
                                  : 'Chia sẻ bài viết',
                            ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _PostSharePreview extends StatelessWidget {
  const _PostSharePreview({
    required this.author,
    required this.post,
    required this.content,
  });

  final Map author;
  final Map<String, dynamic> post;
  final String content;

  @override
  Widget build(BuildContext context) {
    final privacy = switch (post['privacy']?.toString().toLowerCase()) {
      'friends' => 'Bạn bè',
      'private' => 'Chỉ mình tôi',
      _ => 'Công khai',
    };
    final groupName = post['groupName']?.toString();
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xfff5f8fc),
        border: Border.all(color: const Color(0xffdce5ef)),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '${author['name'] ?? 'Sinh viên HVNH'}',
            style: const TextStyle(
              fontWeight: FontWeight.w800,
              color: AppTheme.ink,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            '${groupName == null || groupName.isEmpty ? 'Bài viết cá nhân' : 'Bài viết trong nhóm $groupName'} · $privacy',
            style: const TextStyle(color: AppTheme.muted, fontSize: 11),
          ),
          if (content.isNotEmpty) ...[
            const SizedBox(height: 6),
            Text(content, maxLines: 2, overflow: TextOverflow.ellipsis),
          ],
        ],
      ),
    );
  }
}

class _FieldLabel extends StatelessWidget {
  const _FieldLabel(this.label);
  final String label;

  @override
  Widget build(BuildContext context) => Text(
    label,
    style: const TextStyle(
      fontSize: 12,
      fontWeight: FontWeight.w800,
      color: AppTheme.ink,
    ),
  );
}

class _TabButton extends StatelessWidget {
  const _TabButton({
    required this.label,
    required this.active,
    required this.onTap,
  });

  final String label;
  final bool active;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) => Expanded(
    child: Padding(
      padding: const EdgeInsets.symmetric(horizontal: 2),
      child: TextButton(
        onPressed: onTap,
        style: TextButton.styleFrom(
          backgroundColor: active ? AppTheme.softBlue : Colors.transparent,
          foregroundColor: active ? AppTheme.blue : AppTheme.muted,
          padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 10),
          textStyle: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700),
        ),
        child: FittedBox(fit: BoxFit.scaleDown, child: Text(label)),
      ),
    ),
  );
}
