abstract final class AppDateTime {
  static String relative(dynamic value, {DateTime? now}) {
    final date = value is DateTime
        ? value.toLocal()
        : DateTime.tryParse('${value ?? ''}')?.toLocal();
    if (date == null) return '';
    final elapsed = (now ?? DateTime.now()).difference(date);
    if (elapsed.isNegative || elapsed.inMinutes < 1) return 'Vừa xong';
    if (elapsed.inHours < 1) return '${elapsed.inMinutes} phút trước';
    if (elapsed.inDays < 1) return '${elapsed.inHours} giờ trước';
    if (elapsed.inDays < 7) return '${elapsed.inDays} ngày trước';
    return '${_two(date.day)}/${_two(date.month)}/${date.year}';
  }

  static String full(dynamic value) {
    final date = value is DateTime
        ? value.toLocal()
        : DateTime.tryParse('${value ?? ''}')?.toLocal();
    if (date == null) return '';
    return '${_two(date.hour)}:${_two(date.minute)} · ${_two(date.day)}/${_two(date.month)}/${date.year}';
  }

  static String _two(int value) => value.toString().padLeft(2, '0');
}
