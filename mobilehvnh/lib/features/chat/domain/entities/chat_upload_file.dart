import 'dart:typed_data';

class ChatUploadFile {
  const ChatUploadFile({
    required this.name,
    required this.size,
    this.path,
    this.bytes,
  });
  final String name;
  final int size;
  final String? path;
  final Uint8List? bytes;
}
