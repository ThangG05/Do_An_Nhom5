class AvatarUploadFile {
  const AvatarUploadFile({required this.name, required this.size, this.path, this.bytes});

  final String name;
  final int size;
  final String? path;
  final List<int>? bytes;
}
