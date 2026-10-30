import 'dart:typed_data';

class GroupUploadFile {
  const GroupUploadFile({
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
