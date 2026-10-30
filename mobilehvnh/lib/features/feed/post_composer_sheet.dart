import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

class PostComposerSheet extends StatefulWidget {
  const PostComposerSheet({super.key, required this.onSubmit});

  final Future<void> Function(String content, List<PlatformFile> files)
  onSubmit;

  @override
  State<PostComposerSheet> createState() => _PostComposerSheetState();
}

class _PostComposerSheetState extends State<PostComposerSheet> {
  final _content = TextEditingController();
  final List<PlatformFile> _files = [];
  bool _sending = false;

  @override
  void dispose() {
    _content.dispose();
    super.dispose();
  }

  Future<void> _pickFiles() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.any,
      allowMultiple: true,
      withData: false,
    );
    if (result == null || !mounted) return;
    setState(() {
      final knownPaths = _files.map((file) => file.path ?? file.name).toSet();
      _files.addAll(
        result.files.where((file) => knownPaths.add(file.path ?? file.name)),
      );
    });
  }

  Future<void> _submit() async {
    final content = _content.text.trim();
    if (content.isEmpty && _files.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Hãy viết nội dung hoặc chọn ít nhất một tệp.'),
        ),
      );
      return;
    }
    setState(() => _sending = true);
    try {
      await widget.onSubmit(content, _files);
      if (mounted) Navigator.pop(context);
    } catch (error) {
      if (mounted)
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.toString())));
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  IconData _iconFor(PlatformFile file) {
    final extension = file.extension?.toLowerCase() ?? '';
    if (const {'jpg', 'jpeg', 'png', 'webp', 'gif'}.contains(extension))
      return Icons.image_outlined;
    if (const {'mp4', 'mov', 'mkv', 'webm'}.contains(extension))
      return Icons.video_library_outlined;
    if (const {'mp3', 'wav', 'm4a', 'aac'}.contains(extension))
      return Icons.music_note_outlined;
    return Icons.attach_file_outlined;
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: EdgeInsets.fromLTRB(
          20,
          14,
          20,
          18 + MediaQuery.of(context).viewInsets.bottom,
        ),
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 42,
                  height: 4,
                  decoration: BoxDecoration(
                    color: Colors.blueGrey.shade200,
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              const Text(
                'Tạo bài viết',
                style: TextStyle(
                  fontSize: 21,
                  fontWeight: FontWeight.w800,
                  color: Color(0xff062f59),
                ),
              ),
              const SizedBox(height: 4),
              const Text(
                'Chia sẻ với cộng đồng HVNH',
                style: TextStyle(color: Color(0xff61728a)),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _content,
                minLines: 4,
                maxLines: 8,
                autofocus: true,
                decoration: const InputDecoration(
                  hintText: 'Bạn đang nghĩ gì?',
                  alignLabelWithHint: true,
                ),
              ),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                onPressed: _sending ? null : _pickFiles,
                icon: const Icon(Icons.add_photo_alternate_outlined),
                label: const Text('Ảnh, video hoặc tệp'),
                style: OutlinedButton.styleFrom(
                  minimumSize: const Size.fromHeight(48),
                ),
              ),
              if (_files.isNotEmpty) ...[
                const SizedBox(height: 10),
                Container(
                  constraints: const BoxConstraints(maxHeight: 138),
                  decoration: BoxDecoration(
                    color: const Color(0xfff4f8fc),
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: ListView.builder(
                    shrinkWrap: true,
                    itemCount: _files.length,
                    itemBuilder: (context, index) {
                      final file = _files[index];
                      return ListTile(
                        dense: true,
                        leading: Icon(
                          _iconFor(file),
                          color: const Color(0xff0866c6),
                        ),
                        title: Text(
                          file.name,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        subtitle: Text('${(file.size / 1024).ceil()} KB'),
                        trailing: IconButton(
                          tooltip: 'Bỏ tệp',
                          onPressed: _sending
                              ? null
                              : () => setState(() => _files.removeAt(index)),
                          icon: const Icon(Icons.close),
                        ),
                      );
                    },
                  ),
                ),
              ],
              const SizedBox(height: 16),
              FilledButton.icon(
                onPressed: _sending ? null : _submit,
                icon: _sending
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Icon(Icons.send_rounded),
                label: Text(_sending ? 'Đang đăng...' : 'Đăng bài viết'),
                style: FilledButton.styleFrom(
                  minimumSize: const Size.fromHeight(50),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
