import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/ai_mascot.dart';
import '../../../../core/widgets/app_back_button.dart';
import '../../domain/repositories/ai_repository.dart';

class AiAssistantPage extends StatefulWidget {
  const AiAssistantPage({super.key, required this.repository});

  final AiRepository repository;

  @override
  State<AiAssistantPage> createState() => _AiAssistantPageState();
}

class _AiAssistantPageState extends State<AiAssistantPage> {
  final _input = TextEditingController();
  final _messages = <Map<String, dynamic>>[];
  String? _conversationId;
  bool _busy = false;

  @override
  void dispose() {
    _input.dispose();
    super.dispose();
  }

  Future<void> _ask() async {
    final question = _input.text.trim();
    if (question.isEmpty || _busy) return;
    setState(() {
      _messages.add({'role': 'user', 'text': question});
      _busy = true;
    });
    _input.clear();
    try {
      final result = await widget.repository.ask(
        question,
        conversationId: _conversationId,
      );
      _conversationId =
          result['conversation_id']?.toString() ?? _conversationId;
      final answer =
          result['answer'] ??
          result['content'] ??
          result['message'] ??
          'Trợ lý chưa có câu trả lời phù hợp.';
      if (mounted) {
        setState(
          () => _messages.add({
            'role': 'ai',
            'text': '$answer',
            'citations': _asList(result['citations']),
          }),
        );
      }
    } catch (error) {
      if (mounted) {
        setState(
          () => _messages.add({
            'role': 'ai',
            'text': 'Không thể kết nối Trợ lý AI: $error',
          }),
        );
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _startNew() async {
    setState(() {
      _conversationId = null;
      _messages.clear();
    });
  }

  void _askSuggestion(String question) {
    _input.text = question;
    _ask();
  }

  Future<void> _renameConversation(Map<String, dynamic> conversation) async {
    final title = TextEditingController(
      text: conversation['title']?.toString() ?? '',
    );
    final value = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Đổi tên cuộc trò chuyện'),
        content: TextField(
          controller: title,
          autofocus: true,
          maxLength: 500,
          decoration: const InputDecoration(hintText: 'Tên cuộc trò chuyện'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Hủy'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, title.text.trim()),
            child: const Text('Lưu'),
          ),
        ],
      ),
    );
    title.dispose();
    if (value == null || value.isEmpty) return;
    await widget.repository.renameConversation('${conversation['id']}', value);
  }

  Future<void> _openHistory() async {
    try {
      final conversations = await widget.repository.getConversations();
      if (!mounted) return;
      final selected = await showModalBottomSheet<Map<String, dynamic>>(
        context: context,
        isScrollControlled: true,
        builder: (sheetContext) => SafeArea(
          child: SizedBox(
            height: MediaQuery.of(sheetContext).size.height * .72,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Padding(
                  padding: const EdgeInsets.fromLTRB(20, 18, 12, 10),
                  child: Row(
                    children: [
                      const Expanded(
                        child: Text(
                          'Lịch sử Trợ lý AI',
                          style: TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ),
                      IconButton(
                        tooltip: 'Cuộc trò chuyện mới',
                        onPressed: () =>
                            Navigator.pop(sheetContext, <String, dynamic>{}),
                        icon: const Icon(Icons.add_comment_outlined),
                      ),
                    ],
                  ),
                ),
                const Divider(height: 1),
                Expanded(
                  child: conversations.isEmpty
                      ? const Center(child: Text('Chưa có lịch sử hội thoại.'))
                      : ListView.separated(
                          itemCount: conversations.length,
                          separatorBuilder: (_, _) => const Divider(height: 1),
                          itemBuilder: (context, index) {
                            final conversation = conversations[index];
                            return ListTile(
                              onTap: () =>
                                  Navigator.pop(sheetContext, conversation),
                              leading: const Icon(Icons.auto_awesome_outlined),
                              title: Text(
                                '${conversation['title'] ?? 'Cuộc trò chuyện AI'}',
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                              subtitle: Text(
                                '${conversation['last_message_at'] ?? ''}',
                              ),
                              trailing: PopupMenuButton<String>(
                                onSelected: (action) async {
                                  if (action == 'rename') {
                                    await _renameConversation(conversation);
                                    if (sheetContext.mounted) {
                                      Navigator.pop(sheetContext);
                                    }
                                    await _openHistory();
                                  }
                                  if (action == 'delete') {
                                    await widget.repository.deleteConversation(
                                      '${conversation['id']}',
                                    );
                                    if (sheetContext.mounted) {
                                      Navigator.pop(sheetContext);
                                    }
                                    await _openHistory();
                                  }
                                },
                                itemBuilder: (_) => const [
                                  PopupMenuItem(
                                    value: 'rename',
                                    child: Text('Đổi tên'),
                                  ),
                                  PopupMenuItem(
                                    value: 'delete',
                                    child: Text('Xóa hội thoại'),
                                  ),
                                ],
                              ),
                            );
                          },
                        ),
                ),
              ],
            ),
          ),
        ),
      );
      if (selected == null) return;
      if (selected.isEmpty) {
        await _startNew();
        return;
      }
      final conversationId = selected['id']?.toString();
      if (conversationId == null) return;
      setState(() => _busy = true);
      final messages = await widget.repository.getMessages(conversationId);
      if (!mounted) return;
      setState(() {
        _conversationId = conversationId;
        _messages
          ..clear()
          ..addAll(
            messages.map(
              (message) => {
                'role': _isAssistantRole(message['role']) ? 'ai' : 'user',
                'text': message['content']?.toString() ?? '',
                'citations': _asList(message['citations']),
              },
            ),
          );
      });
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

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(
      centerTitle: false,
      leading: const AppBackButton(),
      title: const Row(
        children: [
          AiMascot(size: 38),
          SizedBox(width: 9),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Trợ lý HVNH',
                  style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800),
                ),
                Text(
                  'Tra cứu từ nguồn chính thức',
                  style: TextStyle(fontSize: 10, color: AppTheme.muted),
                ),
              ],
            ),
          ),
        ],
      ),
      actions: [
        IconButton(
          tooltip: 'Cuộc trò chuyện mới',
          onPressed: _startNew,
          icon: const Icon(Icons.edit_note_outlined),
        ),
        IconButton(
          tooltip: 'Lịch sử hội thoại',
          onPressed: _busy ? null : _openHistory,
          icon: const Icon(Icons.history),
        ),
      ],
    ),
    body: Column(
      children: [
        Expanded(
          child: _messages.isEmpty
              ? Center(
                  child: SingleChildScrollView(
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(22, 24, 22, 30),
                      child: Column(
                        children: [
                          const AiMascot(size: 86),
                          const SizedBox(height: 12),
                          const Text(
                            'Chào bạn!',
                            style: TextStyle(
                              fontSize: 25,
                              fontWeight: FontWeight.w800,
                              color: AppTheme.ink,
                            ),
                          ),
                          const SizedBox(height: 7),
                          const Text(
                            'Mình có thể giúp bạn tra cứu quy chế, học vụ và thông báo của Học viện.',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              color: AppTheme.muted,
                              height: 1.5,
                            ),
                          ),
                          const SizedBox(height: 23),
                          ...[
                            'Chuẩn đầu ra ngoại ngữ là gì?',
                            'Điều kiện xét học bổng?',
                            'Quy định học lại thế nào?',
                          ].map(
                            (question) => Padding(
                              padding: const EdgeInsets.only(bottom: 9),
                              child: Card(
                                child: ListTile(
                                  onTap: () => _askSuggestion(question),
                                  title: Text(
                                    question,
                                    style: const TextStyle(
                                      fontSize: 13,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                  trailing: const Icon(
                                    Icons.arrow_forward_ios_rounded,
                                    size: 14,
                                    color: AppTheme.blue,
                                  ),
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                )
              : ListView.builder(
                  keyboardDismissBehavior:
                      ScrollViewKeyboardDismissBehavior.onDrag,
                  padding: const EdgeInsets.fromLTRB(14, 18, 14, 20),
                  itemCount: _messages.length,
                  itemBuilder: (context, index) {
                    final message = _messages[index];
                    final mine = message['role'] == 'user';
                    return _ChatMessage(
                      mine: mine,
                      text: message['text']?.toString() ?? '',
                      citations: _asList(message['citations']),
                    );
                  },
                ),
        ),
        SafeArea(
          top: false,
          child: Container(
            padding: const EdgeInsets.fromLTRB(12, 10, 12, 12),
            decoration: const BoxDecoration(
              color: Colors.white,
              border: Border(top: BorderSide(color: Color(0xffdbe6ee))),
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _input,
                    minLines: 1,
                    maxLines: 4,
                    textInputAction: TextInputAction.send,
                    onSubmitted: (_) => _ask(),
                    decoration: const InputDecoration(
                      hintText: 'Hỏi Trợ lý AI HVNH...',
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Tooltip(
                  message: 'Gửi câu hỏi',
                  child: SizedBox(
                    width: 46,
                    height: 46,
                    child: FilledButton(
                      onPressed: _busy ? null : _ask,
                      style: FilledButton.styleFrom(
                        padding: EdgeInsets.zero,
                        shape: const CircleBorder(),
                      ),
                      child: _busy
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: Colors.white,
                              ),
                            )
                          : const Icon(Icons.arrow_upward_rounded, size: 22),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    ),
  );
}

class _Citations extends StatelessWidget {
  const _Citations({required this.items});
  final List items;

  @override
  Widget build(BuildContext context) => Container(
    width: double.infinity,
    padding: const EdgeInsets.all(8),
    decoration: BoxDecoration(
      color: const Color(0xfff2f7fc),
      borderRadius: BorderRadius.circular(10),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Nguồn tham khảo',
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w800,
            color: Color(0xff315a83),
          ),
        ),
        const SizedBox(height: 4),
        ...items.map((raw) {
          final item = Map<String, dynamic>.from(raw as Map);
          final start = item['page_start'];
          final end = item['page_end'];
          final page = start == null
              ? null
              : 'Trang $start${end != null && end != start ? '–$end' : ''}';
          final section = item['section_title']?.toString();
          final details = [
            if (section != null && section.isNotEmpty) section,
            if (page != null) page,
          ].join(' · ');
          final source = item['source_url']?.toString();
          return InkWell(
            borderRadius: BorderRadius.circular(9),
            onTap: source == null || source.isEmpty
                ? null
                : () async {
                    final uri = Uri.tryParse(source);
                    if (uri != null && await canLaunchUrl(uri)) {
                      await launchUrl(
                        uri,
                        mode: LaunchMode.externalApplication,
                      );
                    }
                  },
            child: Padding(
              padding: const EdgeInsets.symmetric(vertical: 7, horizontal: 4),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  CircleAvatar(
                    radius: 13,
                    backgroundColor: const Color(0xffdbe9f5),
                    child: Text(
                      '${item['order'] ?? ''}',
                      style: const TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w800,
                        color: AppTheme.blue,
                      ),
                    ),
                  ),
                  const SizedBox(width: 9),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          item['title']?.toString() ?? 'Tài liệu HVNH',
                          style: const TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                            color: Color(0xff183f65),
                          ),
                        ),
                        if (details.isNotEmpty) ...[
                          const SizedBox(height: 3),
                          Text(
                            details,
                            style: const TextStyle(
                              fontSize: 11,
                              color: AppTheme.muted,
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                  if (source != null && source.isNotEmpty)
                    const Icon(
                      Icons.open_in_new_rounded,
                      size: 15,
                      color: AppTheme.muted,
                    ),
                ],
              ),
            ),
          );
        }),
      ],
    ),
  );
}

bool _isAssistantRole(Object? role) =>
    {'assistant', 'ai', 'bot'}.contains(role?.toString().toLowerCase());

List _asList(Object? value) => value is List ? value : const [];

class _ChatMessage extends StatelessWidget {
  const _ChatMessage({
    required this.mine,
    required this.text,
    required this.citations,
  });

  final bool mine;
  final String text;
  final List citations;

  @override
  Widget build(BuildContext context) {
    final maxWidth = MediaQuery.of(context).size.width * .82;
    final bubble = Container(
      constraints: BoxConstraints(maxWidth: maxWidth),
      padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 12),
      decoration: BoxDecoration(
        color: mine ? AppTheme.blue : Colors.white,
        borderRadius: BorderRadius.only(
          topLeft: Radius.circular(mine ? 18 : 5),
          topRight: Radius.circular(mine ? 5 : 18),
          bottomLeft: const Radius.circular(18),
          bottomRight: const Radius.circular(18),
        ),
        border: mine ? null : Border.all(color: const Color(0xffdbe6ee)),
      ),
      child: SelectableText(
        text,
        style: TextStyle(
          color: mine ? Colors.white : const Color(0xff18324d),
          height: 1.5,
          fontSize: 14,
        ),
      ),
    );

    return Padding(
      padding: const EdgeInsets.only(bottom: 18),
      child: Row(
        mainAxisAlignment: mine
            ? MainAxisAlignment.end
            : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!mine) ...[const AiMascot(size: 30), const SizedBox(width: 8)],
          Flexible(
            child: Column(
              crossAxisAlignment: mine
                  ? CrossAxisAlignment.end
                  : CrossAxisAlignment.start,
              children: [
                Padding(
                  padding: const EdgeInsets.only(bottom: 5, left: 2, right: 2),
                  child: Text(
                    mine ? 'Bạn' : 'Trợ lý HVNH',
                    style: const TextStyle(
                      color: AppTheme.muted,
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
                bubble,
                if (!mine && citations.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  ConstrainedBox(
                    constraints: BoxConstraints(maxWidth: maxWidth),
                    child: _Citations(items: citations),
                  ),
                ],
              ],
            ),
          ),
          if (mine) ...[
            const SizedBox(width: 8),
            CircleAvatar(
              radius: 15,
              backgroundColor: AppTheme.softBlue,
              child: const Text(
                'Bạn',
                style: TextStyle(
                  fontSize: 9,
                  fontWeight: FontWeight.w800,
                  color: AppTheme.blue,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
