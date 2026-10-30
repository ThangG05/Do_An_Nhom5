import 'package:flutter/material.dart';

import '../core/theme/app_theme.dart';
import '../features/admin/admin.dart';
import '../features/auth/auth.dart';
import '../features/groups/groups.dart';
import 'app_shell.dart';
import 'di/app_dependencies.dart';

class HvnhHubApp extends StatefulWidget {
  const HvnhHubApp({super.key, required this.dependencies});
  final AppDependencies dependencies;

  @override
  State<HvnhHubApp> createState() => _HvnhHubAppState();
}

class _HvnhHubAppState extends State<HvnhHubApp> {
  // A stored token must not skip the introduction on a new app launch.
  // Session restoration only happens after an explicit sign-in/registration.
  bool _signedIn = false;
  String? _role;
  List<String> _adminGroupSlugs = const [];

  Future<void> _restoreSession() async {
    final signedIn = await widget.dependencies.session.isSignedIn;
    final role = signedIn ? await widget.dependencies.session.role : null;
    var adminGroups = signedIn
        ? await widget.dependencies.session.adminGroupSlugs
        : const <String>[];
    // Sessions created by an older mobile build did not persist this field.
    // Recover the assignment from the shared backend without forcing a logout.
    if (signedIn && role != 'SUPER_ADMIN' && adminGroups.isEmpty) {
      try {
        final groups = await widget.dependencies.groupRepository.getGroups();
        adminGroups = groups
            .where((group) => group['membership']?.toString() == 'ADMIN')
            .map((group) => group['slug']?.toString() ?? '')
            .where((slug) => slug.isNotEmpty)
            .toList();
      } catch (_) {
        // Giữ phiên đăng nhập; danh sách phân quyền sẽ được tải lại ở lần sau.
      }
    }
    if (mounted) {
      setState(() {
        _signedIn = signedIn;
        _role = role;
        _adminGroupSlugs = adminGroups;
      });
    }
  }

  Future<void> _logout() async {
    await widget.dependencies.authRepository.signOut();
    await _restoreSession();
  }

  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'HVNH Hub',
    debugShowCheckedModeBanner: false,
    theme: AppTheme.light,
    scrollBehavior: const AppScrollBehavior(),
    home: _signedIn
        ? _role == 'SUPER_ADMIN'
              ? AdminDashboardPage(
                  repository: widget.dependencies.adminRepository,
                  onLogout: _logout,
                )
              : _adminGroupSlugs.isNotEmpty
              ? GroupAdminRootPage(
                  groupRepository: widget.dependencies.groupRepository,
                  feedRepository: widget.dependencies.feedRepository,
                  adminGroupSlugs: _adminGroupSlugs,
                  onLogout: _logout,
                )
              : AppShell(dependencies: widget.dependencies, onLogout: _logout)
        : WelcomePage(
            dependencies: widget.dependencies,
            onSignedIn: _restoreSession,
          ),
  );
}
