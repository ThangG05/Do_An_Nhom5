import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobilehvnh/core/theme/app_theme.dart';
import 'package:mobilehvnh/features/feed/domain/repositories/feed_repository.dart';
import 'package:mobilehvnh/features/groups/domain/repositories/group_repository.dart';
import 'package:mobilehvnh/features/groups/groups_page.dart';

class _Groups implements GroupRepository {
  final requestedPosts = <String>[];

  @override
  Future<List<Map<String, dynamic>>> getGroups() async => [
    {
      'id': 'pass',
      'slug': 'pass-do',
      'name': 'Pass đồ',
      'description': 'Trao đổi đồ dùng sinh viên',
      'member_count': 2,
      'membership': 'NONE',
    },
    {
      'id': 'room',
      'slug': 'ghep-phong-tim-tro',
      'name': 'Ghép phòng / Tìm phòng trọ',
      'description': 'Tìm người ở ghép',
      'member_count': 3,
      'membership': 'MEMBER',
    },
  ];

  @override
  Future<List<Map<String, dynamic>>> getPosts(
    String groupId, {
    String query = '',
    String sort = 'latest',
    bool mine = false,
  }) async {
    requestedPosts.add(groupId);
    return [];
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class _Feed implements FeedRepository {
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  testWidgets('groups match web order and keep non-member posts private', (
    tester,
  ) async {
    final groups = _Groups();
    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.light,
        home: Scaffold(
          body: GroupsPage(groupRepository: groups, feedRepository: _Feed()),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Bốn không gian dành cho sinh viên'), findsOneWidget);
    expect(find.text('Tham gia để xem bài viết'), findsOneWidget);
    expect(groups.requestedPosts, isEmpty);

    await tester.tap(find.text('Ghép phòng / Tìm phòng trọ').first);
    await tester.pumpAndSettle();
    expect(groups.requestedPosts, ['room']);
    expect(find.text('Bài viết trong nhóm'), findsOneWidget);
  });
}
