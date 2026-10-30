import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class AuthSession {
  static const _accessKey = 'access_token';
  static const _refreshKey = 'refresh_token';
  static const _nameKey = 'full_name';
  static const _roleKey = 'system_role';
  static const _userIdKey = 'user_id';
  static const _avatarKey = 'avatar_url';
  static const _adminGroupsKey = 'admin_group_slugs';
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  Future<String?> get accessToken => _storage.read(key: _accessKey);
  Future<String?> get refreshToken => _storage.read(key: _refreshKey);
  Future<String?> get displayName => _storage.read(key: _nameKey);
  Future<String?> get role => _storage.read(key: _roleKey);
  Future<String?> get userId => _storage.read(key: _userIdKey);
  Future<String?> get avatarUrl => _storage.read(key: _avatarKey);
  Future<List<String>> get adminGroupSlugs async {
    final raw = await _storage.read(key: _adminGroupsKey);
    if (raw == null || raw.isEmpty) return const [];
    try {
      return (jsonDecode(raw) as List)
          .map((value) => value.toString())
          .toList();
    } catch (_) {
      return const [];
    }
  }

  Future<bool> get isSignedIn async => (await accessToken)?.isNotEmpty == true;

  Future<void> save(Map<String, dynamic> tokens) async {
    final user = tokens['user'] as Map<String, dynamic>;
    await _storage.write(
      key: _accessKey,
      value: tokens['access_token'] as String?,
    );
    await _storage.write(
      key: _refreshKey,
      value: tokens['refresh_token'] as String?,
    );
    await _storage.write(key: _nameKey, value: user['full_name'] as String?);
    await _storage.write(key: _roleKey, value: user['system_role'] as String?);
    await _storage.write(key: _userIdKey, value: user['id'] as String?);
    await _storage.write(key: _avatarKey, value: user['avatar_url'] as String?);
    await _storage.write(
      key: _adminGroupsKey,
      value: jsonEncode((user['admin_group_slugs'] as List?) ?? const []),
    );
  }

  Future<void> clear() => _storage.deleteAll();
}
