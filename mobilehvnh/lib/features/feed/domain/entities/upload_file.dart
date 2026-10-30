import 'dart:typed_data';

/// File selected on device. Domain does not depend on a picker widget.
class UploadFile {
  const UploadFile({
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
