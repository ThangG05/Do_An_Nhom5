import 'package:flutter/material.dart';

import '../../../../core/utils/app_date_time.dart';
import '../../../../core/widgets/app_network_image.dart';
import '../../../../core/widgets/app_avatar.dart';
import '../../domain/repositories/user_repository.dart';

/// Reuses the same profile-content API as the web app.  Keeping these tabs
/// data-driven prevents a profile from becoming a static information screen.
class ProfileContentTabs extends StatefulWidget {
  const ProfileContentTabs({
    super.key,
    required this.repository,
    required this.userId,
    required this.profile,
    this.aboutPanel,
    this.onOpenFriends,
    this.onOpenFriend,
  });

  final UserRepository repository;
  final String userId;
  final Map<String, dynamic> profile;
  final Widget? aboutPanel;
  final VoidCallback? onOpenFriends;
  final ValueChanged<String>? onOpenFriend;

  @override
  State<ProfileContentTabs> createState() => _ProfileContentTabsState();
}

class _ProfileContentTabsState extends State<ProfileContentTabs> {
  late Future<_ProfileContent> _future;
  int _selectedTab = 0;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<_ProfileContent> _load() async {
    final values = await Future.wait([
      widget.repository.getProfilePosts(widget.userId),
      widget.repository.getProfilePhotos(widget.userId),
      widget.repository.getProfileListings(widget.userId),
      widget.repository.getGroupPosts(widget.userId),
      widget.repository.getFriends(widget.userId),
    ]);
    return _ProfileContent(
      posts: values[0],
      photos: values[1],
      listings: values[2],
      groupPosts: values[3],
      friends: values[4],
    );
  }

  @override
  Widget build(BuildContext context) => FutureBuilder<_ProfileContent>(
    future: _future,
    builder: (context, snapshot) {
      if (snapshot.connectionState != ConnectionState.done) {
        return const Padding(
          padding: EdgeInsets.all(28),
          child: Center(child: CircularProgressIndicator()),
        );
      }
      if (snapshot.hasError) {
        return _ReloadCard(
          message: 'Không thể tải nội dung trang cá nhân.',
          onReload: () => setState(() => _future = _load()),
        );
      }
      final content = snapshot.data!;
      return DefaultTabController(
        length: 5,
        child: Column(
          children: [
            Card(
              margin: EdgeInsets.zero,
              child: TabBar(
                isScrollable: true,
                tabAlignment: TabAlignment.start,
                onTap: (index) => setState(() => _selectedTab = index),
                tabs: [
                  const Tab(text: 'Bài viết'),
                  const Tab(text: 'Giới thiệu'),
                  Tab(text: 'Bạn bè (${content.friends.length})'),
                  Tab(text: 'Ảnh (${content.photos.length})'),
                  Tab(text: 'Bài đăng hội nhóm (${content.groupPosts.length})'),
                ],
              ),
            ),
            const SizedBox(height: 10),
            AnimatedSwitcher(
              duration: const Duration(milliseconds: 180),
              child: switch (_selectedTab) {
                1 => widget.aboutPanel ?? _AboutCard(profile: widget.profile),
                2 => _FriendsList(
                  key: const ValueKey('friends'),
                  friends: content.friends,
                  onOpenFriends: widget.onOpenFriends,
                  onOpenFriend: widget.onOpenFriend,
                ),
                3 => _PhotoGrid(
                  key: const ValueKey('photos'),
                  photos: content.photos,
                ),
                4 => _PostsList(
                  key: const ValueKey('groups'),
                  posts: content.groupPosts,
                  empty: 'Chưa có bài viết hội nhóm.',
                ),
                _ => Column(
                  key: const ValueKey('posts'),
                  children: [
                    _ProfileOverview(
                      profile: widget.profile,
                      friends: content.friends,
                      photos: content.photos,
                      listings: content.listings,
                      onOpenFriends: widget.onOpenFriends,
                    ),
                    _PostsList(
                      posts: content.posts,
                      empty: 'Chưa có bài viết công khai.',
                    ),
                  ],
                ),
              },
            ),
          ],
        ),
      );
    },
  );
}

class _ProfileContent {
  const _ProfileContent({
    required this.posts,
    required this.photos,
    required this.listings,
    required this.groupPosts,
    required this.friends,
  });
  final List<Map<String, dynamic>> posts;
  final List<Map<String, dynamic>> photos;
  final List<Map<String, dynamic>> listings;
  final List<Map<String, dynamic>> groupPosts;
  final List<Map<String, dynamic>> friends;
}

class _AboutCard extends StatelessWidget {
  const _AboutCard({required this.profile});
  final Map<String, dynamic> profile;

  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(17),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Giới thiệu',
            style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 12),
          if ('${profile['bio'] ?? ''}'.trim().isNotEmpty)
            Text('${profile['bio']}'),
          const SizedBox(height: 10),
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: const Icon(Icons.school_outlined),
            title: const Text('Học vấn'),
            subtitle: Text(
              '${profile['education'] ?? 'Học viện Ngân hàng (BAV)'}',
            ),
          ),
          if ('${profile['faculty'] ?? ''}'.trim().isNotEmpty)
            ListTile(
              contentPadding: EdgeInsets.zero,
              leading: const Icon(Icons.account_balance_outlined),
              title: const Text('Khoa / Viện'),
              subtitle: Text('${profile['faculty']}'),
            ),
        ],
      ),
    ),
  );
}

class _ProfileOverview extends StatelessWidget {
  const _ProfileOverview({
    required this.profile,
    required this.friends,
    required this.photos,
    required this.listings,
    this.onOpenFriends,
  });
  final Map<String, dynamic> profile;
  final List<Map<String, dynamic>> friends;
  final List<Map<String, dynamic>> photos;
  final List<Map<String, dynamic>> listings;
  final VoidCallback? onOpenFriends;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      _AboutCard(profile: profile),
      const SizedBox(height: 10),
      Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Expanded(
                    child: Text(
                      'Bạn bè',
                      style: TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ),
                  TextButton(
                    onPressed: onOpenFriends,
                    child: const Text('Xem tất cả'),
                  ),
                ],
              ),
              Text('${profile['friendsCount'] ?? friends.length} người bạn'),
              if (friends.isNotEmpty) ...[
                const SizedBox(height: 12),
                SizedBox(
                  height: 58,
                  child: ListView.separated(
                    scrollDirection: Axis.horizontal,
                    itemCount: friends.length < 6 ? friends.length : 6,
                    separatorBuilder: (_, _) => const SizedBox(width: 9),
                    itemBuilder: (context, index) {
                      final friend = friends[index];
                      return AppAvatar(
                        radius: 26,
                        url:
                            friend['avatar']?.toString() ??
                            friend['avatar_url']?.toString(),
                        name:
                            friend['name']?.toString() ??
                            friend['full_name']?.toString(),
                      );
                    },
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
      if (photos.isNotEmpty) ...[
        const SizedBox(height: 10),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Ảnh',
                  style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 12),
                _PhotoGrid(photos: photos.take(3).toList()),
              ],
            ),
          ),
        ),
      ],
      if (listings.isNotEmpty) ...[
        const SizedBox(height: 10),
        const Padding(
          padding: EdgeInsets.fromLTRB(2, 8, 2, 10),
          child: Text(
            'Bài niêm yết',
            style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800),
          ),
        ),
        _ListingsList(listings: listings.take(2).toList()),
      ],
      const SizedBox(height: 12),
      const Padding(
        padding: EdgeInsets.fromLTRB(2, 0, 2, 10),
        child: Text(
          'Bài viết',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
        ),
      ),
    ],
  );
}

class _FriendsList extends StatelessWidget {
  const _FriendsList({
    super.key,
    required this.friends,
    this.onOpenFriends,
    this.onOpenFriend,
  });
  final List<Map<String, dynamic>> friends;
  final VoidCallback? onOpenFriends;
  final ValueChanged<String>? onOpenFriend;

  @override
  Widget build(BuildContext context) {
    if (friends.isEmpty) {
      return const _EmptyContent(
        icon: Icons.people_outline,
        message: 'Chưa có bạn bè để hiển thị.',
      );
    }
    return Card(
      child: Column(
        children: [
          ...friends
              .take(10)
              .map(
                (friend) => ListTile(
                  leading: AppAvatar(
                    url:
                        friend['avatar']?.toString() ??
                        friend['avatar_url']?.toString(),
                    name:
                        friend['name']?.toString() ??
                        friend['full_name']?.toString(),
                  ),
                  title: Text(
                    '${friend['name'] ?? friend['full_name'] ?? 'Sinh viên HVNH'}',
                  ),
                  onTap: friend['id'] == null || onOpenFriend == null
                      ? null
                      : () => onOpenFriend!(friend['id'].toString()),
                ),
              ),
          if (friends.length > 10)
            TextButton(
              onPressed: onOpenFriends,
              child: const Text('Xem tất cả bạn bè'),
            ),
        ],
      ),
    );
  }
}

class _PostsList extends StatelessWidget {
  const _PostsList({super.key, required this.posts, required this.empty});
  final List<Map<String, dynamic>> posts;
  final String empty;

  @override
  Widget build(BuildContext context) {
    if (posts.isEmpty) {
      return _EmptyContent(icon: Icons.article_outlined, message: empty);
    }
    return ListView.separated(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      padding: const EdgeInsets.only(bottom: 10),
      itemCount: posts.length,
      separatorBuilder: (_, _) => const SizedBox(height: 10),
      itemBuilder: (context, index) => _PostPreview(post: posts[index]),
    );
  }
}

class _PostPreview extends StatelessWidget {
  const _PostPreview({required this.post});
  final Map<String, dynamic> post;

  @override
  Widget build(BuildContext context) {
    final media = (post['media'] as List?) ?? const [];
    final thumbnail = media.isEmpty
        ? ''
        : (media.first as Map)['url']?.toString() ?? '';
    final group = post['groupName']?.toString() ?? '';
    final author = post['author'] is Map
        ? post['author'] as Map
        : const <String, dynamic>{};
    final authorName = author['name']?.toString() ?? 'Sinh viên HVNH';
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                AppAvatar(
                  radius: 21,
                  url: author['avatar']?.toString(),
                  name: authorName,
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        authorName,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontWeight: FontWeight.w800),
                      ),
                      if (group.isNotEmpty)
                        Text(
                          'Đăng trong $group',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            color: Color(0xff315a83),
                            fontWeight: FontWeight.w700,
                            fontSize: 12,
                          ),
                        ),
                      Text(
                        AppDateTime.relative(post['createdAt']),
                        style: const TextStyle(
                          color: Color(0xff63758c),
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),
            Text(
              '${post['content'] ?? ''}',
              maxLines: 4,
              overflow: TextOverflow.ellipsis,
            ),
            if (thumbnail.startsWith('http')) ...[
              const SizedBox(height: 12),
              ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child: AppNetworkImage(
                  thumbnail,
                  height: 145,
                  width: double.infinity,
                  fit: BoxFit.cover,
                ),
              ),
            ],
            const SizedBox(height: 12),
            Row(
              children: [
                const Icon(
                  Icons.thumb_up_alt_outlined,
                  size: 17,
                  color: Color(0xff63758c),
                ),
                const SizedBox(width: 4),
                Text(
                  '${post['likesCount'] ?? 0}',
                  style: const TextStyle(color: Color(0xff63758c)),
                ),
                const SizedBox(width: 16),
                const Icon(
                  Icons.mode_comment_outlined,
                  size: 17,
                  color: Color(0xff63758c),
                ),
                const SizedBox(width: 4),
                Text(
                  '${post['commentsCount'] ?? 0}',
                  style: const TextStyle(color: Color(0xff63758c)),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _PhotoGrid extends StatelessWidget {
  const _PhotoGrid({super.key, required this.photos});
  final List<Map<String, dynamic>> photos;

  @override
  Widget build(BuildContext context) {
    if (photos.isEmpty) {
      return const _EmptyContent(
        icon: Icons.photo_library_outlined,
        message: 'Chưa có ảnh công khai.',
      );
    }
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      padding: const EdgeInsets.only(bottom: 10),
      itemCount: photos.length,
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 3,
        mainAxisSpacing: 4,
        crossAxisSpacing: 4,
      ),
      itemBuilder: (context, index) {
        final photo = photos[index];
        final url = photo['url']?.toString() ?? '';
        return ClipRRect(
          borderRadius: BorderRadius.circular(10),
          child: url.startsWith('http')
              ? AppNetworkImage(url, fit: BoxFit.cover)
              : const ColoredBox(
                  color: Color(0xffeaf2fb),
                  child: Icon(Icons.image_outlined),
                ),
        );
      },
    );
  }
}

class _ListingsList extends StatelessWidget {
  const _ListingsList({required this.listings});
  final List<Map<String, dynamic>> listings;

  @override
  Widget build(BuildContext context) {
    if (listings.isEmpty) {
      return const _EmptyContent(
        icon: Icons.storefront_outlined,
        message: 'Chưa có bài đăng niêm yết.',
      );
    }
    return ListView.separated(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      padding: const EdgeInsets.only(bottom: 10),
      itemCount: listings.length,
      separatorBuilder: (_, _) => const SizedBox(height: 10),
      itemBuilder: (context, index) {
        final item = listings[index];
        final image = item['imageUrl']?.toString() ?? '';
        return Card(
          child: ListTile(
            contentPadding: const EdgeInsets.all(12),
            leading: ClipRRect(
              borderRadius: BorderRadius.circular(10),
              child: SizedBox(
                width: 58,
                height: 58,
                child: image.startsWith('http')
                    ? AppNetworkImage(image, fit: BoxFit.cover)
                    : const ColoredBox(
                        color: Color(0xffeaf2fb),
                        child: Icon(Icons.inventory_2_outlined),
                      ),
              ),
            ),
            title: Text(
              '${item['title'] ?? 'Bài đăng'}',
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            subtitle: Text(
              '${item['price'] ?? ''}${(item['location']?.toString().isNotEmpty ?? false) ? ' · ${item['location']}' : ''}',
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            trailing: _StatusChip(status: '${item['status'] ?? 'active'}'),
          ),
        );
      },
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.status});
  final String status;
  @override
  Widget build(BuildContext context) {
    final label = switch (status) {
      'sold' => 'Đã bán',
      'rented' => 'Đã cho thuê',
      'expired' => 'Hết hạn',
      _ => 'Đang hiển thị',
    };
    return Chip(label: Text(label, style: const TextStyle(fontSize: 11)));
  }
}

class _EmptyContent extends StatelessWidget {
  const _EmptyContent({required this.icon, required this.message});
  final IconData icon;
  final String message;
  @override
  Widget build(BuildContext context) => Center(
    child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 42, color: const Color(0xff86a0bf)),
        const SizedBox(height: 12),
        Text(message, style: const TextStyle(color: Color(0xff63758c))),
      ],
    ),
  );
}

class _ReloadCard extends StatelessWidget {
  const _ReloadCard({required this.message, required this.onReload});
  final String message;
  final VoidCallback onReload;
  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          Text(message),
          const SizedBox(height: 10),
          OutlinedButton.icon(
            onPressed: onReload,
            icon: const Icon(Icons.refresh),
            label: const Text('Thử lại'),
          ),
        ],
      ),
    ),
  );
}
