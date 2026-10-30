import 'package:flutter_test/flutter_test.dart';
import 'package:mobilehvnh/core/utils/app_date_time.dart';

void main() {
  final now = DateTime(2026, 10, 7, 10);

  test('hiển thị vừa xong khi dưới một phút', () {
    expect(
      AppDateTime.relative(now.subtract(const Duration(seconds: 20)), now: now),
      'Vừa xong',
    );
  });

  test('hiển thị thời gian tương đối trong ngày', () {
    expect(
      AppDateTime.relative(now.subtract(const Duration(minutes: 12)), now: now),
      '12 phút trước',
    );
    expect(
      AppDateTime.relative(now.subtract(const Duration(hours: 3)), now: now),
      '3 giờ trước',
    );
  });

  test('hiển thị ngày tháng cho dữ liệu cũ', () {
    expect(AppDateTime.relative(DateTime(2026, 9, 15), now: now), '15/09/2026');
  });
}
