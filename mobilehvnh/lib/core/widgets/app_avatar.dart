import 'package:flutter/material.dart';

import 'app_network_image.dart';

/// Avatar dùng chung, không bao giờ tạo NetworkImage từ URL rỗng.
class AppAvatar extends StatelessWidget {
  const AppAvatar({
    super.key,
    this.url,
    this.name,
    this.radius = 22,
    this.online = false,
    this.onTap,
    this.heroTag,
  });

  final String? url;
  final String? name;
  final double radius;
  final bool online;
  final VoidCallback? onTap;
  final Object? heroTag;

  String get _initials {
    final words = (name ?? '')
        .trim()
        .split(RegExp(r'\s+'))
        .where((word) => word.isNotEmpty)
        .toList();
    if (words.isEmpty) return 'HV';
    if (words.length == 1) return words.first.characters.first.toUpperCase();
    return '${words.first.characters.first}${words.last.characters.first}'
        .toUpperCase();
  }

  @override
  Widget build(BuildContext context) {
    final normalizedUrl = (url ?? '').trim();
    final hasImage =
        normalizedUrl == '/assets/logo.png' ||
        normalizedUrl.startsWith('http://') ||
        normalizedUrl.startsWith('https://');
    Widget avatar = Container(
      width: radius * 2,
      height: radius * 2,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: const Color(0xffe4f0fc),
        border: Border.all(color: Colors.white, width: radius >= 38 ? 4 : 2),
        boxShadow: radius >= 38
            ? const [
                BoxShadow(
                  color: Color(0x22062f59),
                  blurRadius: 14,
                  offset: Offset(0, 5),
                ),
              ]
            : null,
      ),
      clipBehavior: Clip.antiAlias,
      child: hasImage
          ? AppNetworkImage(
              normalizedUrl,
              fit: BoxFit.cover,
              errorBuilder: (_, _, _) =>
                  _Initials(text: _initials, radius: radius),
            )
          : _Initials(text: _initials, radius: radius),
    );
    if (heroTag != null) avatar = Hero(tag: heroTag!, child: avatar);
    return Semantics(
      button: onTap != null,
      label: name == null ? 'Ảnh đại diện' : 'Ảnh đại diện của $name',
      child: GestureDetector(
        onTap: onTap,
        child: Stack(
          clipBehavior: Clip.none,
          children: [
            avatar,
            if (online)
              Positioned(
                right: -1,
                bottom: -1,
                child: Container(
                  width: radius * .46,
                  height: radius * .46,
                  decoration: BoxDecoration(
                    color: const Color(0xff22a35a),
                    shape: BoxShape.circle,
                    border: Border.all(color: Colors.white, width: 2),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _Initials extends StatelessWidget {
  const _Initials({required this.text, required this.radius});

  final String text;
  final double radius;

  @override
  Widget build(BuildContext context) => Center(
    child: Text(
      text,
      style: TextStyle(
        color: const Color(0xff063763),
        fontSize: radius * .72,
        fontWeight: FontWeight.w800,
      ),
    ),
  );
}
