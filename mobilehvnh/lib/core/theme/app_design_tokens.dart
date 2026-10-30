import 'package:flutter/material.dart';

/// Shared visual language for the student app. Keep the HVNH navy/blue/gold
/// palette while making spacing, surfaces and motion predictable across pages.
abstract final class AppSpacing {
  static const xxs = 4.0;
  static const xs = 8.0;
  static const sm = 12.0;
  static const md = 16.0;
  static const lg = 20.0;
  static const xl = 24.0;
  static const xxl = 32.0;
}

abstract final class AppRadii {
  static const chip = 14.0;
  static const field = 17.0;
  static const card = 22.0;
  static const hero = 28.0;
  static const sheet = 30.0;
}

abstract final class AppMotion {
  static const press = Duration(milliseconds: 130);
  static const selection = Duration(milliseconds: 210);
  static const surface = Duration(milliseconds: 340);
  static const curve = Curves.easeOutCubic;

  static Duration duration(BuildContext context, Duration normal) =>
      MediaQuery.maybeOf(context)?.disableAnimations == true
      ? Duration.zero
      : normal;
}

@immutable
class AppPalette extends ThemeExtension<AppPalette> {
  const AppPalette({
    required this.canvas,
    required this.surface,
    required this.surfaceSecondary,
    required this.primary,
    required this.primarySoft,
    required this.ink,
    required this.muted,
    required this.hairline,
  });

  final Color canvas;
  final Color surface;
  final Color surfaceSecondary;
  final Color primary;
  final Color primarySoft;
  final Color ink;
  final Color muted;
  final Color hairline;

  static const light = AppPalette(
    canvas: Color(0xfff3f7fb),
    surface: Colors.white,
    surfaceSecondary: Color(0xffedf4fa),
    primary: Color(0xff155784),
    primarySoft: Color(0xffe7f2fb),
    ink: Color(0xff102b46),
    muted: Color(0xff607489),
    hairline: Color(0xffe0eaf2),
  );

  static const dark = AppPalette(
    canvas: Color(0xff0d1825),
    surface: Color(0xff172738),
    surfaceSecondary: Color(0xff203449),
    primary: Color(0xff82c7f2),
    primarySoft: Color(0xff213f58),
    ink: Color(0xfff4f8fb),
    muted: Color(0xffadc1d2),
    hairline: Color(0xff31485d),
  );

  static AppPalette of(BuildContext context) =>
      Theme.of(context).extension<AppPalette>() ?? light;

  @override
  AppPalette copyWith({
    Color? canvas,
    Color? surface,
    Color? surfaceSecondary,
    Color? primary,
    Color? primarySoft,
    Color? ink,
    Color? muted,
    Color? hairline,
  }) => AppPalette(
    canvas: canvas ?? this.canvas,
    surface: surface ?? this.surface,
    surfaceSecondary: surfaceSecondary ?? this.surfaceSecondary,
    primary: primary ?? this.primary,
    primarySoft: primarySoft ?? this.primarySoft,
    ink: ink ?? this.ink,
    muted: muted ?? this.muted,
    hairline: hairline ?? this.hairline,
  );

  @override
  AppPalette lerp(ThemeExtension<AppPalette>? other, double t) {
    if (other is! AppPalette) return this;
    return AppPalette(
      canvas: Color.lerp(canvas, other.canvas, t)!,
      surface: Color.lerp(surface, other.surface, t)!,
      surfaceSecondary: Color.lerp(
        surfaceSecondary,
        other.surfaceSecondary,
        t,
      )!,
      primary: Color.lerp(primary, other.primary, t)!,
      primarySoft: Color.lerp(primarySoft, other.primarySoft, t)!,
      ink: Color.lerp(ink, other.ink, t)!,
      muted: Color.lerp(muted, other.muted, t)!,
      hairline: Color.lerp(hairline, other.hairline, t)!,
    );
  }
}
