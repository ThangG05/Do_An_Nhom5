import 'dart:async';

import 'package:flutter/material.dart';
import '../../../../core/widgets/app_page_bar.dart';
import '../../../../core/widgets/app_avatar.dart';

import '../../../user/domain/repositories/user_repository.dart';
import '../../domain/repositories/chat_repository.dart';

class NewConversationPage extends StatefulWidget {
  const NewConversationPage({
    super.key,
    required this.chatRepository,
    required this.userRepository,
  });

  final ChatRepository chatRepository;
  final UserRepository userRepository;

  @override
  State<NewConversationPage> createState() => _NewConversationPageState();
}

class _NewConversationPageState extends State<NewConversationPage> {
  final _query = TextEditingController();
  Timer? _debounce;
  List<Map<String, dynamic>> _users = [];
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _debounce?.cancel();
    _query.dispose();
    super.dispose();
  }

  void _search(String value) {
    _debounce?.cancel();
    if (value.trim().length < 2) {
      setState(() {
        _users = [];
        _error = null;
      });
      return;
    }
    _debounce = Timer(const Duration(milliseconds: 350), () async {
      setState(() {
        _loading = true;
        _error = null;
      });
      try {
        final users = await widget.userRepository.searchUsers(value.trim());
        if (mounted) setState(() => _users = users);
      } catch (error) {
        if (mounted) setState(() => _error = error.toString());
      } finally {
        if (mounted) setState(() => _loading = false);
      }
    });
  }

  Future<void> _start(Map<String, dynamic> user) async {
    try {
      final conversation = await widget.chatRepository.createDirectConversation(
        '${user['id']}',
      );
      if (mounted) Navigator.of(context).pop(conversation);
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
    appBar: const AppPageBar(title: 'Tin nhắn mới'),
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
              hintText: 'Tìm tên, email hoặc mã sinh viên',
            ),
          ),
        ),
        Expanded(
          child: _loading
              ? const Center(child: CircularProgressIndicator())
              : _error != null
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Text(_error!),
                  ),
                )
              : _users.isEmpty
              ? const Center(
                  child: Text('Nhập ít nhất 2 ký tự để tìm sinh viên.'),
                )
              : ListView.separated(
                  itemCount: _users.length,
                  separatorBuilder: (_, _) => const Divider(height: 1),
                  itemBuilder: (context, index) {
                    final user = _users[index];
                    return ListTile(
                      onTap: () => _start(user),
                      leading: AppAvatar(
                        radius: 20,
                        url: user['avatar']?.toString(),
                        name: user['name']?.toString(),
                      ),
                      title: Text('${user['name'] ?? 'Sinh viên HVNH'}'),
                      subtitle: Text(
                        user['studentCode']?.toString().isNotEmpty == true
                            ? 'Mã sinh viên: ${user['studentCode']}'
                            : '@${user['username'] ?? ''}',
                      ),
                      trailing: const Icon(Icons.chat_bubble_outline),
                    );
                  },
                ),
        ),
      ],
    ),
  );
}
