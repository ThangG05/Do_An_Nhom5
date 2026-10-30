import 'package:flutter/material.dart';

/// Uses the same academy mark as the web client.
class AppBrandMark extends StatelessWidget {
  const AppBrandMark({super.key, this.size = 36});

  final double size;

  @override
  Widget build(BuildContext context) => Image.asset(
    'assets/brand/hvnh-logo.png',
    width: size,
    height: size,
    fit: BoxFit.contain,
    semanticLabel: 'Biểu trưng Học viện Ngân hàng',
  );
}
