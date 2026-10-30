import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';

import '../../../../app/di/app_dependencies.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/app_brand_mark.dart';
import '../../../../core/widgets/premium_hero_card.dart';
import 'login_page.dart';
import 'registration_page.dart';

/// Mobile entry follows the web's welcome → authentication hierarchy.
class WelcomePage extends StatelessWidget {
  const WelcomePage({
    super.key,
    required this.dependencies,
    required this.onSignedIn,
  });

  final AppDependencies dependencies;
  final Future<void> Function() onSignedIn;

  Future<void> _complete(BuildContext context) async {
    final navigator = Navigator.of(context);
    await onSignedIn();
    navigator.popUntil((route) => route.isFirst);
  }

  void _login(BuildContext context) => Navigator.of(context).push(
    MaterialPageRoute<void>(
      builder: (_) => LoginPage(
        dependencies: dependencies,
        onSignedIn: () => _complete(context),
      ),
    ),
  );

  void _register(BuildContext context) => Navigator.of(context).push(
    MaterialPageRoute<void>(
      builder: (_) => RegistrationPage(
        dependencies: dependencies,
        onRegistered: () => _complete(context),
      ),
    ),
  );

  @override
  Widget build(BuildContext context) => Scaffold(
    body: SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(18, 24, 18, 32),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 550),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                PremiumHeroCard(
                  padding: const EdgeInsets.fromLTRB(24, 26, 24, 26),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Row(
                        children: [
                          AppBrandMark(size: 38),
                          SizedBox(width: 10),
                          Text(
                            'HVNH Hub',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 18,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 42),
                      const Text(
                        'NƠI SINH VIÊN HVNH KẾT NỐI',
                        style: TextStyle(
                          color: AppTheme.gold,
                          fontSize: 10,
                          letterSpacing: 1.1,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      const SizedBox(height: 12),
                      const Text.rich(
                        TextSpan(
                          children: [
                            TextSpan(text: 'Một cộng đồng.\n'),
                            TextSpan(
                              text: 'Vô vàn kết nối.',
                              style: TextStyle(color: AppTheme.gold),
                            ),
                          ],
                        ),
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 32,
                          fontWeight: FontWeight.w900,
                          height: 1.12,
                        ),
                      ),
                      const SizedBox(height: 14),
                      const Text(
                        'Học hỏi, chia sẻ và khám phá mọi điều đang diễn ra '
                        'tại Học viện Ngân hàng — cùng những người bạn thuộc về nơi này.',
                        style: TextStyle(color: Color(0xffd5eafa), height: 1.5),
                      ),
                      const SizedBox(height: 26),
                      SizedBox(
                        width: double.infinity,
                        child: FilledButton.icon(
                          style: FilledButton.styleFrom(
                            backgroundColor: AppTheme.gold,
                            foregroundColor: AppTheme.navy,
                            padding: const EdgeInsets.symmetric(vertical: 15),
                          ),
                          onPressed: () => _register(context),
                          icon: const Icon(
                            CupertinoIcons.arrow_right,
                            size: 18,
                          ),
                          label: const Text('Bắt đầu cùng HVNH Hub'),
                        ),
                      ),
                      const SizedBox(height: 9),
                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton(
                          style: OutlinedButton.styleFrom(
                            foregroundColor: Colors.white,
                            side: const BorderSide(color: Color(0x80ffffff)),
                            padding: const EdgeInsets.symmetric(vertical: 15),
                          ),
                          onPressed: () => _login(context),
                          child: const Text('Tôi đã có tài khoản'),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 23),
                const Text(
                  'Khám phá cộng đồng',
                  style: TextStyle(
                    color: AppTheme.ink,
                    fontSize: 19,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 12),
                const Row(
                  children: [
                    Expanded(
                      child: _WelcomeCategory(
                        icon: CupertinoIcons.bag,
                        title: 'Pass đồ',
                        subtitle: 'Trao đổi đồ dùng',
                      ),
                    ),
                    SizedBox(width: 10),
                    Expanded(
                      child: _WelcomeCategory(
                        icon: CupertinoIcons.calendar,
                        title: 'Sự kiện',
                        subtitle: 'Hoạt động sinh viên',
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                const Row(
                  children: [
                    Expanded(
                      child: _WelcomeCategory(
                        icon: CupertinoIcons.house,
                        title: 'Ghép phòng',
                        subtitle: 'Tìm nơi ở phù hợp',
                      ),
                    ),
                    SizedBox(width: 10),
                    Expanded(
                      child: _WelcomeCategory(
                        icon: CupertinoIcons.book,
                        title: 'Học tập',
                        subtitle: 'Cùng nhau tiến bộ',
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    ),
  );
}

class _WelcomeCategory extends StatelessWidget {
  const _WelcomeCategory({
    required this.icon,
    required this.title,
    required this.subtitle,
  });

  final IconData icon;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(13),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: AppTheme.blue, size: 23),
          const SizedBox(height: 9),
          Text(
            title,
            style: const TextStyle(
              color: AppTheme.ink,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 3),
          Text(
            subtitle,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(color: AppTheme.muted, fontSize: 11),
          ),
        ],
      ),
    ),
  );
}
