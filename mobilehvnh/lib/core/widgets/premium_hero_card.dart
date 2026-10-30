import 'package:flutter/material.dart';

import '../theme/app_design_tokens.dart';
import '../theme/app_theme.dart';

/// One restrained focal surface for welcome/landing sections. It tilts only
/// while the user touches it and immediately becomes static for reduced motion.
class PremiumHeroCard extends StatefulWidget {
  const PremiumHeroCard({super.key, required this.child, this.padding});

  final Widget child;
  final EdgeInsetsGeometry? padding;

  @override
  State<PremiumHeroCard> createState() => _PremiumHeroCardState();
}

class _PremiumHeroCardState extends State<PremiumHeroCard> {
  double _turnX = 0;
  double _turnY = 0;
  bool _pressed = false;

  void _move(PointerEvent event, double width) {
    if (!_pressed || MediaQuery.maybeOf(context)?.disableAnimations == true) {
      return;
    }
    final nextY = ((event.localPosition.dx / width) - .5).clamp(-.5, .5) * .045;
    final nextX = ((event.localPosition.dy / 240) - .5).clamp(-.5, .5) * -.035;
    setState(() {
      _turnX = nextX;
      _turnY = nextY;
    });
  }

  void _reset() => setState(() {
    _pressed = false;
    _turnX = 0;
    _turnY = 0;
  });

  @override
  Widget build(BuildContext context) => LayoutBuilder(
    builder: (context, constraints) {
      final reducedMotion =
          MediaQuery.maybeOf(context)?.disableAnimations == true;
      return Listener(
        onPointerDown: (_) => _pressed = true,
        onPointerMove: (event) => _move(event, constraints.maxWidth),
        onPointerUp: (_) => _reset(),
        onPointerCancel: (_) => _reset(),
        child: AnimatedContainer(
          duration: AppMotion.duration(context, AppMotion.surface),
          curve: AppMotion.curve,
          transform: reducedMotion
              ? Matrix4.identity()
              : (Matrix4.identity()
                  ..setEntry(3, 2, .00065)
                  ..rotateX(_turnX)
                  ..rotateY(_turnY)),
          transformAlignment: Alignment.center,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(AppRadii.hero),
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [Color(0xff071e36), AppTheme.navy, Color(0xff2674a4)],
              stops: [0, .48, 1],
            ),
            boxShadow: [
              BoxShadow(
                color: const Color(0xff0b3151).withValues(alpha: .18),
                blurRadius: _pressed ? 30 : 24,
                offset: Offset(0, _pressed ? 14 : 10),
              ),
            ],
          ),
          clipBehavior: Clip.antiAlias,
          child: Stack(
            children: [
              const Positioned(
                right: -56,
                top: -86,
                child: _Orb(size: 195, color: Color(0x20ffffff)),
              ),
              const Positioned(
                right: 48,
                bottom: -94,
                child: _Orb(size: 180, color: Color(0x20f9c64a)),
              ),
              const Positioned(
                right: 34,
                top: 26,
                child: _Orb(size: 9, color: AppTheme.gold),
              ),
              Padding(
                padding: widget.padding ?? const EdgeInsets.all(AppSpacing.xl),
                child: widget.child,
              ),
            ],
          ),
        ),
      );
    },
  );
}

class _Orb extends StatelessWidget {
  const _Orb({required this.size, required this.color});
  final double size;
  final Color color;

  @override
  Widget build(BuildContext context) => Container(
    width: size,
    height: size,
    decoration: BoxDecoration(
      shape: BoxShape.circle,
      border: Border.all(color: color, width: 1.4),
      gradient: RadialGradient(
        colors: [color.withValues(alpha: .35), Colors.transparent],
      ),
    ),
  );
}
