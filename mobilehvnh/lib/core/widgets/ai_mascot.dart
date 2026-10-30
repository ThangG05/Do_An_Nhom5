import 'package:flutter/material.dart';

import '../theme/app_theme.dart';

/// Lightweight Flutter rendition of the web assistant's cap-and-screen face.
class AiMascot extends StatelessWidget {
  const AiMascot({super.key, this.size = 64});

  final double size;

  @override
  Widget build(BuildContext context) => SizedBox(
    width: size,
    height: size,
    child: Stack(
      alignment: Alignment.center,
      children: [
        Positioned(
          top: size * .29,
          child: Container(
            width: size * .75,
            height: size * .55,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(size * .2),
              gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [Color(0xff2082b4), AppTheme.navy],
              ),
              boxShadow: const [
                BoxShadow(
                  color: Color(0x36071e36),
                  blurRadius: 12,
                  offset: Offset(0, 6),
                ),
              ],
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                _eye(size),
                SizedBox(width: size * .16),
                _eye(size),
              ],
            ),
          ),
        ),
        Positioned(
          top: size * .10,
          child: ClipPath(
            clipper: _CapClipper(),
            child: Container(
              width: size * .55,
              height: size * .28,
              color: AppTheme.gold,
            ),
          ),
        ),
        Positioned(left: size * .07, top: size * .49, child: _ear(size)),
        Positioned(right: size * .07, top: size * .49, child: _ear(size)),
        Positioned(
          bottom: size * .12,
          child: Container(
            width: size * .13,
            height: size * .025,
            decoration: BoxDecoration(
              color: const Color(0xff8ce4ef),
              borderRadius: BorderRadius.circular(8),
            ),
          ),
        ),
      ],
    ),
  );

  Widget _eye(double size) => Container(
    width: size * .075,
    height: size * .1,
    decoration: BoxDecoration(
      color: const Color(0xffb1f5fa),
      borderRadius: BorderRadius.circular(9),
    ),
  );

  Widget _ear(double size) => Container(
    width: size * .1,
    height: size * .18,
    decoration: BoxDecoration(
      color: AppTheme.blue,
      borderRadius: BorderRadius.circular(5),
    ),
  );
}

class _CapClipper extends CustomClipper<Path> {
  @override
  Path getClip(Size size) => Path()
    ..moveTo(0, size.height * .55)
    ..lineTo(size.width * .5, 0)
    ..lineTo(size.width, size.height * .55)
    ..quadraticBezierTo(size.width * .5, size.height, 0, size.height * .55)
    ..close();

  @override
  bool shouldReclip(covariant CustomClipper<Path> oldClipper) => false;
}
