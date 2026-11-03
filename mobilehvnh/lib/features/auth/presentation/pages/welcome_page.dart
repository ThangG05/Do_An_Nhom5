import 'dart:math' as math;

import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';

import '../../../../app/di/app_dependencies.dart';
import '../../../../core/theme/app_theme.dart';
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
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(2),
                            decoration: BoxDecoration(
                              color: Colors.white,
                              borderRadius: BorderRadius.circular(5),
                            ),
                            child: const _OfficialHvnhLogo(size: 34),
                          ),
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
                      const SizedBox(height: 16),
                      const _WelcomeUniverse(),
                      const SizedBox(height: 20),
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
    elevation: 0,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(20),
      side: const BorderSide(color: Color(0xffe6edf4)),
    ),
    child: Padding(
      padding: const EdgeInsets.all(15),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          DecoratedBox(
            decoration: BoxDecoration(
              color: const Color(0xffe9f3fb),
              borderRadius: BorderRadius.circular(11),
            ),
            child: SizedBox(
              width: 38,
              height: 38,
              child: Icon(icon, color: AppTheme.blue, size: 21),
            ),
          ),
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

/// Compact, animated interpretation of the 3D Community Universe on web.
class _WelcomeUniverse extends StatefulWidget {
  const _WelcomeUniverse();

  @override
  State<_WelcomeUniverse> createState() => _WelcomeUniverseState();
}

class _WelcomeUniverseState extends State<_WelcomeUniverse>
    with SingleTickerProviderStateMixin {
  static const _spaces = [
    ('Học tập', 'Chia sẻ tài liệu. Cùng nhau tiến bộ.', CupertinoIcons.book, Color(0xff86baff)),
    ('Sự kiện', 'Khám phá hoạt động. Tạo thêm kỷ niệm.', CupertinoIcons.sparkles, Color(0xffffd483)),
    ('Pass đồ', 'Trao lại món đồ. Nối dài giá trị.', CupertinoIcons.bag, Color(0xffffa4ca)),
    ('Ghép phòng', 'Tìm chốn ở mới. Gặp người bạn mới.', CupertinoIcons.house, Color(0xff85e1c0)),
  ];

  late final AnimationController _orbit = AnimationController(
    vsync: this,
    duration: const Duration(seconds: 18),
  )..repeat();
  int _selected = 0;

  @override
  void dispose() {
    _orbit.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final reducedMotion = MediaQuery.of(context).disableAnimations;
    if (reducedMotion && _orbit.isAnimating) _orbit.stop();
    if (!reducedMotion && !_orbit.isAnimating) _orbit.repeat();

    return Column(
      children: [
        SizedBox(
          height: 274,
          child: LayoutBuilder(
        builder: (context, constraints) {
          final width = constraints.maxWidth;
          final tileWidth = math.min(174.0, (width - 20) / 2).toDouble();
          return AnimatedBuilder(
            animation: _orbit,
            builder: (context, _) {
              final phase = reducedMotion ? 0.0 : _orbit.value * math.pi * 2;
              final tilt = reducedMotion ? 0.0 : math.sin(phase) * .035;
              return Stack(
                clipBehavior: Clip.none,
                children: [
                  Positioned.fill(
                    child: DecoratedBox(
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(20),
                        gradient: const RadialGradient(
                          center: Alignment(0, .1),
                          radius: .82,
                          colors: [Color(0x263d9ac2), Color(0x000b3155)],
                        ),
                      ),
                    ),
                  ),
                  Center(
                    child: Transform.rotate(
                      angle: -.15 + phase * .12,
                      child: Container(
                        width: math.min(width * .87, 390).toDouble(),
                        height: 218,
                        decoration: BoxDecoration(
                          border: Border.all(color: const Color(0x55d8efff), width: 1),
                          borderRadius: BorderRadius.circular(100),
                        ),
                      ),
                    ),
                  ),
                  Center(
                    child: Transform.rotate(
                      angle: phase * -.08,
                      child: Container(
                        width: math.min(width * .68, 300).toDouble(),
                        height: 168,
                        decoration: BoxDecoration(
                          border: Border.all(color: const Color(0x66ffd483), width: .8),
                          borderRadius: BorderRadius.circular(100),
                        ),
                      ),
                    ),
                  ),
                  Positioned(
                    left: width * .3,
                    bottom: 31,
                    child: Container(
                      width: width * .4,
                      height: 34,
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(100),
                        color: _spaces[_selected].$4.withValues(alpha: .15),
                        border: Border.all(color: const Color(0x668fd9ff)),
                        boxShadow: const [BoxShadow(color: Color(0x553c9bd3), blurRadius: 18)],
                      ),
                    ),
                  ),
                  Center(
                    child: Transform(
                      alignment: Alignment.center,
                      transform: Matrix4.identity()
                        ..setEntry(3, 2, .0014)
                        ..translate(0.0, math.sin(phase) * 4.0)
                        ..rotateX(-.11 + tilt)
                        ..rotateY(math.sin(phase) * .09),
                      child: Container(
                        width: 112,
                        height: 112,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          gradient: const RadialGradient(
                            center: Alignment(-.35, -.45),
                            colors: [Color(0xff3980a6), Color(0xff0c355e), Color(0xff06182b)],
                          ),
                          border: Border.all(color: const Color(0xffb7e4ff), width: 1),
                          boxShadow: const [
                            BoxShadow(color: Color(0x557db6d7), blurRadius: 28, spreadRadius: 2),
                            BoxShadow(color: Color(0x88031629), blurRadius: 22, offset: Offset(0, 12)),
                          ],
                        ),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Container(
                              padding: const EdgeInsets.all(4),
                              decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(7)),
                              child: const _OfficialHvnhLogo(size: 39),
                            ),
                            const SizedBox(height: 4),
                            const Text('HVNH', style: TextStyle(color: Colors.white, fontSize: 12, letterSpacing: 2, fontWeight: FontWeight.w900)),
                            const Text('H U B', style: TextStyle(color: Color(0xffbddff5), fontSize: 7, letterSpacing: 1.3)),
                          ],
                        ),
                      ),
                    ),
                  ),
                  Positioned(
                    left: 0,
                    top: 13,
                    child: _UniverseTile(
                      width: tileWidth,
                      icon: CupertinoIcons.book,
                      label: 'Học tập',
                      caption: 'Chia sẻ kiến thức',
                      color: _spaces[0].$4,
                      angle: -.055 + tilt,
                      lift: reducedMotion ? 0 : math.sin(phase) * 7,
                      selected: _selected == 0,
                      onTap: () => setState(() => _selected = 0),
                    ),
                  ),
                  Positioned(
                    right: 0,
                    top: 32,
                    child: _UniverseTile(
                      width: tileWidth,
                      icon: CupertinoIcons.sparkles,
                      label: 'Sự kiện',
                      caption: 'Hoạt động sinh viên',
                      color: _spaces[1].$4,
                      angle: .055 - tilt,
                      lift: reducedMotion ? 0 : -math.sin(phase) * 7,
                      selected: _selected == 1,
                      onTap: () => setState(() => _selected = 1),
                    ),
                  ),
                  Positioned(
                    left: 0,
                    bottom: 12,
                    child: _UniverseTile(
                      width: tileWidth,
                      icon: CupertinoIcons.bag,
                      label: 'Pass đồ',
                      caption: 'Trao đổi đồ dùng',
                      color: _spaces[2].$4,
                      angle: .055 - tilt,
                      lift: reducedMotion ? 0 : -math.sin(phase) * 7,
                      selected: _selected == 2,
                      onTap: () => setState(() => _selected = 2),
                    ),
                  ),
                  Positioned(
                    right: 0,
                    bottom: 0,
                    child: _UniverseTile(
                      width: tileWidth,
                      icon: CupertinoIcons.house,
                      label: 'Ghép phòng',
                      caption: 'Tìm nơi ở phù hợp',
                      color: _spaces[3].$4,
                      angle: -.055 + tilt,
                      lift: reducedMotion ? 0 : math.sin(phase) * 7,
                      selected: _selected == 3,
                      onTap: () => setState(() => _selected = 3),
                    ),
                  ),
                  Positioned(
                    right: width * .18,
                    top: 0,
                    child: const _OrbitDot(color: AppTheme.gold, size: 8),
                  ),
                  Positioned(
                    left: width * .17,
                    bottom: 1,
                    child: const _OrbitDot(color: Color(0xff9ce5d0), size: 6),
                  ),
                ],
              );
            },
          );
        },
          ),
        ),
        const SizedBox(height: 7),
        Row(
          children: [
            Expanded(
              child: AnimatedSwitcher(
                duration: const Duration(milliseconds: 240),
                child: Column(
                  key: ValueKey(_selected),
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(_spaces[_selected].$1, style: TextStyle(color: _spaces[_selected].$4, fontWeight: FontWeight.w800, fontSize: 12)),
                    const SizedBox(height: 3),
                    Text(_spaces[_selected].$2, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(color: Color(0xffc6dceb), fontSize: 10)),
                  ],
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }
}

class _UniverseTile extends StatelessWidget {
  const _UniverseTile({
    required this.width,
    required this.icon,
    required this.label,
    required this.caption,
    required this.color,
    required this.angle,
    required this.lift,
    required this.selected,
    required this.onTap,
  });

  final double width;
  final IconData icon;
  final String label;
  final String caption;
  final Color color;
  final double angle;
  final double lift;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => GestureDetector(
    onTap: onTap,
    child: Transform.translate(
      offset: Offset(0, lift),
      child: Transform(
      alignment: Alignment.center,
      transform: Matrix4.identity()
        ..setEntry(3, 2, .001)
        ..rotateY(angle),
      child: Container(
        width: width,
        padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 10),
        decoration: BoxDecoration(
          color: const Color(0xe61a4567),
          borderRadius: BorderRadius.circular(15),
          border: Border.all(color: color.withValues(alpha: selected ? .95 : .55), width: selected ? 1.3 : 1),
          boxShadow: const [
            BoxShadow(color: Color(0x55001122), blurRadius: 16, offset: Offset(0, 8)),
          ],
        ),
        child: Row(
          children: [
            Icon(icon, color: color, size: 20),
            const SizedBox(width: 8),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(label, style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w800)),
                  const SizedBox(height: 2),
                  Text(caption, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(color: Color(0xffc6d9e8), fontSize: 9)),
                ],
              ),
            ),
          ],
        ),
      ),
    ),
  ),
  );
}

class _OfficialHvnhLogo extends StatelessWidget {
  const _OfficialHvnhLogo({required this.size});
  final double size;

  @override
  Widget build(BuildContext context) => Image.asset(
    'assets/brand/hvnh-official-logo.png',
    width: size,
    height: size,
    fit: BoxFit.contain,
    semanticLabel: 'Logo chính thức Học viện Ngân hàng',
  );
}

class _OrbitDot extends StatelessWidget {
  const _OrbitDot({required this.color, required this.size});
  final Color color;
  final double size;

  @override
  Widget build(BuildContext context) => Container(
    width: size,
    height: size,
    decoration: BoxDecoration(
      shape: BoxShape.circle,
      color: color,
      boxShadow: [BoxShadow(color: color.withValues(alpha: .6), blurRadius: 9)],
    ),
  );
}
