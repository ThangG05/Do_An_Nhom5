import 'package:file_picker/file_picker.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/api_client.dart';
import '../../core/chat_realtime.dart';
import '../../core/utils/app_date_time.dart';
import '../../core/widgets/app_avatar.dart';
import '../../core/widgets/app_back_button.dart';
import '../../core/widgets/app_network_image.dart';
import '../../core/widgets/app_state_view.dart';
import '../../core/theme/app_theme.dart';
import '../auth/auth_session.dart';
import '../user/domain/repositories/user_repository.dart';
import '../user/presentation/pages/social_pages.dart';
import 'domain/entities/chat_upload_file.dart';
import 'domain/repositories/chat_repository.dart';
import 'presentation/pages/new_conversation_page.dart';

Future<void> _openChatAttachment(BuildContext context, String value) async {
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

class ChatPage extends StatefulWidget {
  const ChatPage({
    super.key,
    required this.repository,
    required this.userRepository,
    required this.apiClient,
    this.refreshSignal,
  });

  final ChatRepository repository;
  final UserRepository userRepository;
  final ApiClient apiClient;
  final ValueListenable<int>? refreshSignal;

  @override
  State<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends State<ChatPage> {
  final _search = TextEditingController();
  List<dynamic> _items = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    widget.refreshSignal?.addListener(_load);
    _load();
  }

  @override
  void dispose() {
    _search.dispose();
    widget.refreshSignal?.removeListener(_load);
    super.dispose();
  }

  Future<void> _load() async {
    try {
      _items = await widget.repository.getConversations();
      _error = null;
    } catch (error) {
      _error = error.toString();
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _newConversation() async {
    final conversation = await Navigator.of(context).push<Map<String, dynamic>>(
      MaterialPageRoute(
        builder: (_) => NewConversationPage(
          chatRepository: widget.repository,
          userRepository: widget.userRepository,
        ),
      ),
    );
    if (conversation == null || !mounted) return;
    await Navigator.of(context)
        .push(
          MaterialPageRoute(
            builder: (_) => ConversationPage(
              conversation: conversation,
              repository: widget.repository,
              userRepository: widget.userRepository,
              apiClient: widget.apiClient,
            ),
          ),
        )
        .then((_) => _load());
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const AppLoadingList(count: 4);
    final query = _search.text.trim().toLowerCase();
    final visible = _items.where((value) {
      final item = value as Map;
      final name = '${item['nickname'] ?? item['participantName'] ?? ''}'
          .toLowerCase();
      return query.isEmpty || name.contains(query);
    }).toList();
    return Scaffold(
      body: RefreshIndicator(
        onRefresh: _load,
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 760),
            child: ListView(
              padding: const EdgeInsets.fromLTRB(16, 20, 16, 32),
              children: [
                Row(
                  children: [
                    const Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Tin nhắn',
                            style: TextStyle(
                              fontSize: 25,
                              fontWeight: FontWeight.w800,
                              color: AppTheme.ink,
                            ),
                          ),
                          SizedBox(height: 3),
                          Text(
                            'Trò chuyện cùng bạn bè HVNH',
                            style: TextStyle(
                              color: AppTheme.muted,
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                    ),
                    Tooltip(
                      message: 'Soạn tin nhắn mới',
                      child: CupertinoButton(
                        padding: EdgeInsets.zero,
                        onPressed: _newConversation,
                        child: const CircleAvatar(
                          radius: 23,
                          backgroundColor: AppTheme.softBlue,
                          child: Icon(
                            CupertinoIcons.square_pencil,
                            color: AppTheme.blue,
                            size: 21,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 18),
                TextField(
                  controller: _search,
                  onChanged: (_) => setState(() {}),
                  decoration: const InputDecoration(
                    hintText: 'Tìm cuộc trò chuyện',
                    prefixIcon: Icon(
                      CupertinoIcons.search,
                      color: AppTheme.muted,
                      size: 20,
                    ),
                  ),
                ),
                const SizedBox(height: 18),
                if (_error == null && _items.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 10, left: 2),
                    child: Text(
                      query.isEmpty ? 'Gần đây' : '${visible.length} kết quả',
                      style: const TextStyle(
                        color: AppTheme.ink,
                        fontWeight: FontWeight.w800,
                        fontSize: 15,
                      ),
                    ),
                  ),
                if (_error != null)
                  AppStateView(
                    icon: Icons.wifi_off_rounded,
                    title: 'Chưa tải được tin nhắn',
                    message: _error!,
                    actionLabel: 'Thử lại',
                    onAction: _load,
                  )
                else if (_items.isEmpty)
                  const AppStateView(
                    icon: Icons.chat_bubble_outline_rounded,
                    title: 'Chưa có cuộc trò chuyện',
                    message: 'Bắt đầu trò chuyện cùng bạn bè HVNH.',
                  )
                else if (visible.isEmpty)
                  const AppStateView(
                    icon: CupertinoIcons.search,
                    title: 'Không tìm thấy cuộc trò chuyện',
                    message: 'Hãy thử tên khác để tìm lại.',
                  )
                else
                  ...visible.map((value) {
                    final item = Map<String, dynamic>.from(value as Map);
                    return Card(
                      margin: const EdgeInsets.only(bottom: 9),
                      child: ListTile(
                        contentPadding: const EdgeInsets.symmetric(
                          horizontal: 15,
                          vertical: 7,
                        ),
                        onTap: () => Navigator.of(context)
                            .push(
                              MaterialPageRoute(
                                builder: (_) => ConversationPage(
                                  conversation: item,
                                  repository: widget.repository,
                                  userRepository: widget.userRepository,
                                  apiClient: widget.apiClient,
                                ),
                              ),
                            )
                            .then((_) => _load()),
                        leading: AppAvatar(
                          radius: 25,
                          url: item['participantAvatar']?.toString(),
                          name: item['participantName']?.toString(),
                          online: item['isOnline'] == true,
                        ),
                        title: Text(
                          '${item['nickname'] ?? item['participantName'] ?? 'Sinh viên HVNH'}',
                          style: const TextStyle(
                            fontWeight: FontWeight.w800,
                            color: AppTheme.ink,
                            fontSize: 14,
                          ),
                        ),
                        subtitle: Text(
                          '${item['lastMessageSnippet'] ?? ''}',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            color: AppTheme.muted,
                            fontSize: 12.5,
                          ),
                        ),
                        trailing: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: [
                            Text(
                              AppDateTime.relative(item['lastMessageTime']),
                              style: const TextStyle(
                                fontSize: 11,
                                color: Color(0xff71839a),
                              ),
                            ),
                            if ((item['unreadCount'] ?? 0) > 0) ...[
                              const SizedBox(height: 5),
                              CircleAvatar(
                                radius: 10,
                                backgroundColor: const Color(0xff0866c6),
                                child: Text(
                                  '${item['unreadCount']}',
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 10,
                                  ),
                                ),
                              ),
                            ],
                          ],
                        ),
                      ),
                    );
                  }),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class ConversationPage extends StatefulWidget {
  const ConversationPage({
    super.key,
    required this.conversation,
    required this.repository,
    required this.userRepository,
    required this.apiClient,
  });

  final Map<dynamic, dynamic> conversation;
  final ChatRepository repository;
  final UserRepository userRepository;
  final ApiClient apiClient;

  @override
  State<ConversationPage> createState() => _ConversationPageState();
}

class _ConversationPageState extends State<ConversationPage> {
  static const _themes = <String, Color>{
    'blue': Color(0xff0866c6),
    'indigo': Color(0xff4f46e5),
    'emerald': Color(0xff059669),
    'rose': Color(0xffe11d48),
    'violet': Color(0xff7c3aed),
    'amber': Color(0xffd97706),
  };

  late final ChatRealtime _realtime;
  final _messageScroll = ScrollController();
  final _input = TextEditingController();
  final _files = <PlatformFile>[];
  List<dynamic> _messages = [];
  bool _loading = true;
  bool _loadingOlder = false;
  bool _hasOlder = true;
  bool _sending = false;
  String? _myId;
  Map<String, dynamic>? _replyingTo;
  late String _theme;

  Color get _themeColor => _themes[_theme] ?? _themes['blue']!;

  @override
  void initState() {
    super.initState();
    _theme = widget.conversation['theme']?.toString() ?? 'blue';
    _realtime = ChatRealtime(widget.apiClient);
    _messageScroll.addListener(_onMessageScroll);
    _prepare();
  }

  void _onMessageScroll() {
    if (_messageScroll.hasClients &&
        _messageScroll.position.extentAfter < 240) {
      _loadOlder();
    }
  }

  Future<void> _prepare() async {
    _myId = await AuthSession().userId;
    await _load();
    await _realtime.connect(_onEvent);
  }

  @override
  void dispose() {
    _realtime.close();
    _messageScroll.dispose();
    _input.dispose();
    super.dispose();
  }

  void _onEvent(Map<String, dynamic> event) {
    if (event['conversation_id'] != widget.conversation['id']) {
      return;
    }
    final message = event['message'];
    if (event['event'] == 'message.recalled' && message is Map) {
      final index = _messages.indexWhere(
        (item) => item is Map && item['id'] == message['id'],
      );
      if (index >= 0 && mounted) setState(() => _messages[index] = message);
      return;
    }
    if (event['event'] != 'message.created' ||
        message is! Map ||
        _messages.any((item) => item is Map && item['id'] == message['id']))
      return;
    if (mounted) setState(() => _messages.add(message));
  }

  Future<void> _recall(Map<dynamic, dynamic> item) async {
    try {
      final recalled = await widget.repository.recallMessage(
        '${widget.conversation['id']}',
        '${item['id']}',
      );
      final index = _messages.indexWhere(
        (message) => message is Map && message['id'] == item['id'],
      );
      if (index >= 0 && mounted) setState(() => _messages[index] = recalled);
    } catch (error) {
      if (mounted)
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.toString())));
    }
  }

  void _messageActions(Map<dynamic, dynamic> item, bool mine) {
    showModalBottomSheet<void>(
      context: context,
      builder: (sheetContext) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.reply_rounded),
              title: const Text('Trả lời'),
              onTap: () {
                Navigator.pop(sheetContext);
                setState(() => _replyingTo = Map<String, dynamic>.from(item));
              },
            ),
            if (mine)
              ListTile(
                leading: const Icon(Icons.undo_rounded),
                title: const Text('Thu hồi tin nhắn'),
                onTap: () {
                  Navigator.pop(sheetContext);
                  _recall(item);
                },
              ),
          ],
        ),
      ),
    );
  }

  Future<void> _load() async {
    try {
      _messages = await widget.repository.getMessages(
        '${widget.conversation['id']}',
        limit: 50,
      );
      _hasOlder = _messages.length == 50;
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _loadOlder() async {
    if (_loading || _loadingOlder || !_hasOlder || _messages.isEmpty) return;
    setState(() => _loadingOlder = true);
    try {
      final older = await widget.repository.getMessages(
        '${widget.conversation['id']}',
        before: (_messages.first as Map)['timestamp']?.toString(),
        limit: 50,
      );
      final known = _messages
          .whereType<Map>()
          .map((item) => item['id']?.toString())
          .toSet();
      final fresh = older
          .where((item) => !known.contains(item['id']?.toString()))
          .toList();
      if (mounted) {
        setState(() {
          _messages.insertAll(0, fresh);
          _hasOlder = older.length == 50;
        });
      }
    } catch (_) {
      // Keep the current conversation usable; another scroll can retry.
    } finally {
      if (mounted) setState(() => _loadingOlder = false);
    }
  }

  Future<void> _pick() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.any,
      allowMultiple: true,
      withData: kIsWeb,
    );
    if (result != null && mounted) setState(() => _files.addAll(result.files));
  }

  Future<void> _send() async {
    final text = _input.text.trim();
    if ((text.isEmpty && _files.isEmpty) || _sending) return;
    final pendingFiles = List<PlatformFile>.from(_files);
    final reply = _replyingTo;
    _input.clear();
    setState(() {
      _sending = true;
      _files.clear();
      _replyingTo = null;
    });
    try {
      final message = await widget.repository.sendMessage(
        '${widget.conversation['id']}',
        text,
        pendingFiles
            .map(
              (file) => ChatUploadFile(
                name: file.name,
                size: file.size,
                path: file.path,
                bytes: file.bytes,
              ),
            )
            .toList(),
        replyToId: reply?['id']?.toString(),
      );
      if (!_messages.any(
            (item) => item is Map && item['id'] == message['id'],
          ) &&
          mounted) {
        setState(() => _messages.add(message));
      }
    } catch (error) {
      if (mounted) {
        if (_input.text.isEmpty) _input.text = text;
        setState(() {
          _files.insertAll(0, pendingFiles);
          _replyingTo = reply;
        });
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.toString())));
      }
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  Future<void> _changeTheme(String theme) async {
    if (theme == _theme) return;
    setState(() => _theme = theme);
    try {
      await widget.repository.updateConversationSettings(
        '${widget.conversation['id']}',
        theme: theme,
      );
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.toString())));
      }
    }
  }

  Future<void> _showShared() async {
    try {
      final shared = await widget.repository.getSharedAttachments(
        '${widget.conversation['id']}',
      );
      if (!mounted) return;
      showModalBottomSheet<void>(
        context: context,
        builder: (context) => SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Text(
                  'Ảnh và tệp đã chia sẻ',
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 12),
                if (shared['media']!.isEmpty && shared['files']!.isEmpty)
                  const Padding(
                    padding: EdgeInsets.all(20),
                    child: Text(
                      'Chưa có ảnh hoặc tệp nào trong cuộc trò chuyện.',
                    ),
                  )
                else
                  ...[...shared['media']!, ...shared['files']!].map(
                    (item) => ListTile(
                      leading: const Icon(Icons.attach_file),
                      title: Text('${item['name'] ?? 'Tệp đính kèm'}'),
                      subtitle: Text('${item['type'] ?? ''}'),
                      trailing: const Icon(Icons.open_in_new, size: 18),
                      onTap: () {
                        final url = item['url']?.toString() ?? '';
                        if (url.isNotEmpty) _openChatAttachment(context, url);
                      },
                    ),
                  ),
              ],
            ),
          ),
        ),
      );
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.toString())));
      }
    }
  }

  Future<void> _searchMessages() async {
    final query = TextEditingController();
    List<Map<String, dynamic>> results = [];
    var loading = false;
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (sheetContext) => StatefulBuilder(
        builder: (context, setSheetState) => SafeArea(
          child: Padding(
            padding: EdgeInsets.fromLTRB(
              20,
              20,
              20,
              20 + MediaQuery.of(context).viewInsets.bottom,
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Text(
                  'Tìm trong cuộc trò chuyện',
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: query,
                  autofocus: true,
                  textInputAction: TextInputAction.search,
                  onSubmitted: (value) async {
                    if (value.trim().isEmpty) return;
                    setSheetState(() => loading = true);
                    try {
                      results = await widget.repository.searchMessages(
                        '${widget.conversation['id']}',
                        value.trim(),
                      );
                    } catch (error) {
                      if (mounted) {
                        ScaffoldMessenger.of(this.context).showSnackBar(
                          SnackBar(content: Text(error.toString())),
                        );
                      }
                    } finally {
                      if (context.mounted) setSheetState(() => loading = false);
                    }
                  },
                  decoration: const InputDecoration(
                    prefixIcon: Icon(Icons.search),
                    hintText: 'Nhập từ khóa rồi nhấn tìm',
                  ),
                ),
                if (loading)
                  const Padding(
                    padding: EdgeInsets.all(20),
                    child: Center(child: CircularProgressIndicator()),
                  )
                else if (results.isNotEmpty)
                  ConstrainedBox(
                    constraints: const BoxConstraints(maxHeight: 320),
                    child: ListView.separated(
                      shrinkWrap: true,
                      itemCount: results.length,
                      separatorBuilder: (_, _) => const Divider(height: 1),
                      itemBuilder: (_, index) {
                        final item = results[index];
                        return ListTile(
                          leading: const Icon(Icons.chat_bubble_outline),
                          title: Text(
                            '${item['content'] ?? 'Tệp đính kèm'}',
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                          subtitle: Text('${item['createdAt'] ?? ''}'),
                          onTap: () => Navigator.pop(sheetContext),
                        );
                      },
                    ),
                  )
                else if (query.text.isNotEmpty)
                  const Padding(
                    padding: EdgeInsets.only(top: 16),
                    child: Text('Không tìm thấy tin nhắn phù hợp.'),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
    query.dispose();
  }

  Future<void> _changeNickname() async {
    final controller = TextEditingController(
      text: widget.conversation['nickname']?.toString() ?? '',
    );
    final nickname = await showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Đổi biệt danh'),
        content: TextField(
          controller: controller,
          maxLength: 100,
          autofocus: true,
          decoration: const InputDecoration(
            hintText: 'Tên hiển thị trong đoạn chat',
          ),
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
    if (nickname == null) return;
    try {
      await widget.repository.updateConversationSettings(
        '${widget.conversation['id']}',
        nickname: nickname,
      );
      if (mounted) {
        setState(
          () => widget.conversation['nickname'] = nickname.isEmpty
              ? null
              : nickname,
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

  Future<void> _toggleMute() async {
    final muted = widget.conversation['isMuted'] == true;
    try {
      await widget.repository.updateConversationSettings(
        '${widget.conversation['id']}',
        isMuted: !muted,
      );
      if (mounted) setState(() => widget.conversation['isMuted'] = !muted);
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.toString())));
      }
    }
  }

  Future<void> _openProfile() async {
    final userId = widget.conversation['participantId']?.toString() ?? '';
    if (userId.isEmpty) return;
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => PublicProfilePage(
          repository: widget.userRepository,
          userId: userId,
        ),
      ),
    );
  }

  Future<void> _blockParticipant() async {
    final userId = widget.conversation['participantId']?.toString() ?? '';
    if (userId.isEmpty) return;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Chặn người dùng?'),
        content: const Text(
          'Bạn sẽ không thể tiếp tục liên hệ hoặc xem nội dung công khai của người này.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Hủy'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Chặn'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    try {
      await widget.userRepository.setBlocked(userId, true);
      if (mounted) Navigator.pop(context);
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
    appBar: AppBar(
      centerTitle: false,
      leading: const AppBackButton(),
      title: InkWell(
        onTap: _openProfile,
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 6),
          child: Row(
            children: [
              AppAvatar(
                radius: 18,
                url: widget.conversation['participantAvatar']?.toString(),
                name: widget.conversation['participantName']?.toString(),
                online: widget.conversation['isOnline'] == true,
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      '${widget.conversation['nickname'] ?? widget.conversation['participantName']}',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    Text(
                      widget.conversation['isOnline'] == true
                          ? 'Đang hoạt động'
                          : '${widget.conversation['lastActive'] ?? 'Ngoại tuyến'}',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 11,
                        color: Color(0xff71839a),
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
      actions: [
        IconButton(
          tooltip: 'Tìm trong cuộc trò chuyện',
          onPressed: _searchMessages,
          icon: const Icon(Icons.search),
        ),
        IconButton(
          tooltip: 'Ảnh và tệp đã chia sẻ',
          onPressed: _showShared,
          icon: const Icon(Icons.perm_media_outlined),
        ),
        PopupMenuButton<String>(
          tooltip: 'Tùy chỉnh đoạn chat',
          onSelected: _changeTheme,
          itemBuilder: (_) => _themes.entries
              .map(
                (entry) => PopupMenuItem(
                  value: entry.key,
                  child: Row(
                    children: [
                      CircleAvatar(radius: 9, backgroundColor: entry.value),
                      const SizedBox(width: 10),
                      Text('Chủ đề ${entry.key}'),
                    ],
                  ),
                ),
              )
              .toList(),
          icon: const Icon(Icons.palette_outlined),
        ),
        PopupMenuButton<String>(
          tooltip: 'Tùy chọn',
          onSelected: (value) {
            if (value == 'nickname') _changeNickname();
            if (value == 'mute') _toggleMute();
            if (value == 'profile') _openProfile();
            if (value == 'block') _blockParticipant();
          },
          itemBuilder: (_) => [
            const PopupMenuItem(
              value: 'profile',
              child: Text('Xem trang cá nhân'),
            ),
            const PopupMenuItem(
              value: 'nickname',
              child: Text('Đổi biệt danh'),
            ),
            PopupMenuItem(
              value: 'mute',
              child: Text(
                widget.conversation['isMuted'] == true
                    ? 'Bật thông báo'
                    : 'Tắt thông báo',
              ),
            ),
            const PopupMenuItem(value: 'block', child: Text('Chặn người dùng')),
          ],
          icon: const Icon(Icons.more_vert),
        ),
      ],
    ),
    body: AnimatedContainer(
      duration: const Duration(milliseconds: 220),
      color: Color.alphaBlend(
        _themeColor.withValues(alpha: .025),
        AppTheme.canvas,
      ),
      child: Column(
        children: [
          if (_loadingOlder)
            LinearProgressIndicator(
              minHeight: 2,
              color: _themeColor,
              backgroundColor: _themeColor.withValues(alpha: .12),
            ),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : ListView.builder(
                    controller: _messageScroll,
                    reverse: true,
                    padding: const EdgeInsets.fromLTRB(14, 16, 14, 18),
                    itemCount: _messages.length,
                    itemBuilder: (context, index) {
                      final item =
                          _messages[_messages.length - 1 - index] as Map;
                      final mine = item['senderId']?.toString() == _myId;
                      final attachments =
                          (item['attachments'] as List?) ?? const [];
                      return GestureDetector(
                        onLongPress: item['isRecalled'] == true
                            ? null
                            : () => _messageActions(item, mine),
                        child: Align(
                          alignment: mine
                              ? Alignment.centerRight
                              : Alignment.centerLeft,
                          child: Container(
                            margin: const EdgeInsets.only(bottom: 10),
                            padding: const EdgeInsets.symmetric(
                              horizontal: 14,
                              vertical: 10,
                            ),
                            constraints: BoxConstraints(
                              maxWidth: MediaQuery.of(context).size.width * .76,
                            ),
                            decoration: BoxDecoration(
                              color: mine ? _themeColor : Colors.white,
                              borderRadius: BorderRadius.circular(18),
                              border: mine
                                  ? null
                                  : Border.all(color: const Color(0xffdbe6ee)),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                if (item['replyTo'] is Map)
                                  Container(
                                    margin: const EdgeInsets.only(bottom: 7),
                                    padding: const EdgeInsets.all(8),
                                    decoration: BoxDecoration(
                                      color: mine
                                          ? Colors.white.withValues(alpha: .16)
                                          : const Color(0xffedf3f8),
                                      borderRadius: BorderRadius.circular(9),
                                    ),
                                    child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          '${(item['replyTo'] as Map)['senderName'] ?? ''}',
                                          style: TextStyle(
                                            fontWeight: FontWeight.w700,
                                            fontSize: 11,
                                            color: mine
                                                ? Colors.white
                                                : AppTheme.ink,
                                          ),
                                        ),
                                        Text(
                                          '${(item['replyTo'] as Map)['content'] ?? ''}',
                                          maxLines: 2,
                                          overflow: TextOverflow.ellipsis,
                                          style: TextStyle(
                                            fontSize: 11,
                                            color: mine
                                                ? Colors.white70
                                                : AppTheme.muted,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                if ('${item['content'] ?? ''}'
                                    .trim()
                                    .isNotEmpty)
                                  Text(
                                    '${item['content']}',
                                    style: TextStyle(
                                      color: mine
                                          ? Colors.white
                                          : const Color(0xff18324d),
                                    ),
                                  ),
                                ...attachments.map(
                                  (attachment) => _MessageAttachment(
                                    attachment: Map<String, dynamic>.from(
                                      attachment as Map,
                                    ),
                                    mine: mine,
                                    themeColor: _themeColor,
                                  ),
                                ),
                                const SizedBox(height: 3),
                                Text(
                                  AppDateTime.full(item['timestamp']),
                                  style: TextStyle(
                                    fontSize: 9.5,
                                    color: mine
                                        ? Colors.white70
                                        : const Color(0xff71839a),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      );
                    },
                  ),
          ),
          if (_files.isNotEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 10),
              child: Wrap(
                children: _files
                    .map(
                      (file) => InputChip(
                        label: Text(file.name),
                        onDeleted: _sending
                            ? null
                            : () => setState(() => _files.remove(file)),
                      ),
                    )
                    .toList(),
              ),
            ),
          if (_replyingTo != null)
            ListTile(
              dense: true,
              title: Text(
                'Đang trả lời ${_replyingTo!['senderName'] ?? 'tin nhắn'}',
              ),
              subtitle: Text(
                '${_replyingTo!['content'] ?? ''}',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              trailing: IconButton(
                icon: const Icon(Icons.close),
                onPressed: () => setState(() => _replyingTo = null),
              ),
            ),
          SafeArea(
            top: false,
            child: Container(
              padding: const EdgeInsets.fromLTRB(10, 9, 10, 10),
              decoration: const BoxDecoration(
                color: Colors.white,
                border: Border(top: BorderSide(color: Color(0xffdbe6ee))),
              ),
              child: Row(
                children: [
                  IconButton.filledTonal(
                    onPressed: _sending ? null : _pick,
                    icon: const Icon(Icons.add, color: AppTheme.blue),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: TextField(
                      controller: _input,
                      onSubmitted: (_) => _send(),
                      decoration: const InputDecoration(
                        hintText: 'Nhập tin nhắn...',
                      ),
                    ),
                  ),
                  const SizedBox(width: 7),
                  IconButton.filled(
                    onPressed: _sending ? null : _send,
                    style: IconButton.styleFrom(backgroundColor: _themeColor),
                    icon: const Icon(Icons.send_rounded, color: Colors.white),
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

class _MessageAttachment extends StatelessWidget {
  const _MessageAttachment({
    required this.attachment,
    required this.mine,
    required this.themeColor,
  });

  final Map<String, dynamic> attachment;
  final bool mine;
  final Color themeColor;

  @override
  Widget build(BuildContext context) {
    final type = attachment['type']?.toString() ?? 'file';
    final url = attachment['url']?.toString() ?? '';
    if (type == 'image' && url.startsWith('http')) {
      return Padding(
        padding: const EdgeInsets.only(top: 7),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(12),
          child: AppNetworkImage(
            url,
            width: 220,
            height: 180,
            fit: BoxFit.cover,
            errorBuilder: (_, _, _) => const SizedBox(
              height: 80,
              child: Center(child: Icon(Icons.broken_image_outlined)),
            ),
          ),
        ),
      );
    }
    final icon = switch (type) {
      'video' => Icons.play_circle_outline,
      'audio' => Icons.audio_file_outlined,
      _ => Icons.description_outlined,
    };
    return InkWell(
      onTap: url.isEmpty ? null : () => _openChatAttachment(context, url),
      borderRadius: BorderRadius.circular(11),
      child: Container(
        margin: const EdgeInsets.only(top: 7),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 9),
        decoration: BoxDecoration(
          color: mine
              ? Colors.white.withValues(alpha: .14)
              : const Color(0xffeef4fa),
          borderRadius: BorderRadius.circular(11),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 20, color: mine ? Colors.white : themeColor),
            const SizedBox(width: 7),
            Flexible(
              child: Text(
                '${attachment['name'] ?? 'Tệp đính kèm'}',
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  color: mine ? Colors.white : const Color(0xff18324d),
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
            const SizedBox(width: 6),
            Icon(
              Icons.open_in_new,
              size: 16,
              color: mine ? Colors.white70 : const Color(0xff71839a),
            ),
          ],
        ),
      ),
    );
  }
}
