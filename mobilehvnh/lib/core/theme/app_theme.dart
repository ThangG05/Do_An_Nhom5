import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';

import 'app_design_tokens.dart';

abstract final class AppTheme {
  static const navy = Color(0xff0a2b4b);
  static const blue = Color(0xff155784);
  static const gold = Color(0xfff9c64a);
  static const ink = Color(0xff102b46);
  static const muted = Color(0xff607489);
  static const canvas = Color(0xfff2f6fa);
  static const hairline = Color(0xffe3ebf2);
  static const softBlue = Color(0xffeaf3f9);

  static ThemeData get light => ThemeData(
    extensions: const [AppPalette.light],
    colorScheme: ColorScheme.fromSeed(
      seedColor: blue,
      brightness: Brightness.light,
      primary: navy,
      surface: Colors.white,
    ),
    useMaterial3: true,
    scaffoldBackgroundColor: AppPalette.light.canvas,
    splashFactory: NoSplash.splashFactory,
    highlightColor: Colors.transparent,
    visualDensity: VisualDensity.standard,
    iconButtonTheme: IconButtonThemeData(
      style: IconButton.styleFrom(
        foregroundColor: blue,
        minimumSize: const Size(44, 44),
        shape: const CircleBorder(),
      ),
    ),
    cupertinoOverrideTheme: const CupertinoThemeData(
      brightness: Brightness.light,
      primaryColor: blue,
      scaffoldBackgroundColor: canvas,
      barBackgroundColor: Color(0xf7ffffff),
    ),
    textSelectionTheme: const TextSelectionThemeData(
      cursorColor: blue,
      selectionColor: Color(0x402a80b6),
      selectionHandleColor: blue,
    ),
    pageTransitionsTheme: const PageTransitionsTheme(
      builders: {
        TargetPlatform.android: CupertinoPageTransitionsBuilder(),
        TargetPlatform.iOS: CupertinoPageTransitionsBuilder(),
        TargetPlatform.windows: CupertinoPageTransitionsBuilder(),
        TargetPlatform.macOS: CupertinoPageTransitionsBuilder(),
        TargetPlatform.linux: CupertinoPageTransitionsBuilder(),
      },
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: Color(0xf7ffffff),
      foregroundColor: ink,
      surfaceTintColor: Colors.white,
      elevation: 0,
      shadowColor: Colors.transparent,
      scrolledUnderElevation: 0,
      centerTitle: true,
      toolbarHeight: 55,
      shape: Border(bottom: BorderSide(color: hairline, width: .5)),
      titleTextStyle: TextStyle(
        fontSize: 18,
        fontWeight: FontWeight.w700,
        color: ink,
        letterSpacing: -.25,
      ),
    ),
    cardTheme: CardThemeData(
      color: Colors.white,
      elevation: 0,
      margin: EdgeInsets.zero,
      surfaceTintColor: Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppRadii.card),
        side: const BorderSide(color: hairline, width: .5),
      ),
    ),
    bottomSheetTheme: const BottomSheetThemeData(
      backgroundColor: Colors.white,
      surfaceTintColor: Colors.white,
      modalBackgroundColor: Colors.white,
      showDragHandle: true,
      dragHandleColor: Color(0xffc5ced7),
      dragHandleSize: Size(36, 5),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(
          top: Radius.circular(AppRadii.sheet),
        ),
      ),
    ),
    dialogTheme: DialogThemeData(
      backgroundColor: Colors.white,
      surfaceTintColor: Colors.white,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
      titleTextStyle: const TextStyle(
        fontSize: 20,
        fontWeight: FontWeight.w800,
        color: ink,
      ),
    ),
    snackBarTheme: SnackBarThemeData(
      behavior: SnackBarBehavior.floating,
      backgroundColor: ink,
      contentTextStyle: const TextStyle(
        color: Colors.white,
        fontWeight: FontWeight.w600,
      ),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
    ),
    chipTheme: ChipThemeData(
      backgroundColor: Colors.white,
      selectedColor: softBlue,
      side: const BorderSide(color: hairline),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppRadii.chip),
      ),
      labelStyle: const TextStyle(
        color: ink,
        fontWeight: FontWeight.w700,
        fontSize: 12,
      ),
    ),
    tabBarTheme: const TabBarThemeData(
      labelColor: navy,
      unselectedLabelColor: muted,
      labelStyle: TextStyle(fontWeight: FontWeight.w800, fontSize: 14),
      unselectedLabelStyle: TextStyle(
        fontWeight: FontWeight.w600,
        fontSize: 14,
      ),
      dividerColor: hairline,
      indicatorColor: blue,
      indicatorSize: TabBarIndicatorSize.label,
    ),
    segmentedButtonTheme: SegmentedButtonThemeData(
      style: ButtonStyle(
        minimumSize: const WidgetStatePropertyAll(Size(44, 42)),
        padding: const WidgetStatePropertyAll(
          EdgeInsets.symmetric(horizontal: 14),
        ),
        side: const WidgetStatePropertyAll(BorderSide(color: hairline)),
        shape: WidgetStatePropertyAll(
          RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppRadii.chip),
          ),
        ),
        foregroundColor: WidgetStateProperty.resolveWith(
          (states) => states.contains(WidgetState.selected) ? navy : muted,
        ),
        backgroundColor: WidgetStateProperty.resolveWith(
          (states) =>
              states.contains(WidgetState.selected) ? softBlue : Colors.white,
        ),
      ),
    ),
    switchTheme: SwitchThemeData(
      thumbColor: WidgetStateProperty.resolveWith(
        (states) => states.contains(WidgetState.selected)
            ? Colors.white
            : const Color(0xfff8fbfd),
      ),
      trackColor: WidgetStateProperty.resolveWith(
        (states) => states.contains(WidgetState.selected)
            ? blue
            : const Color(0xffcbd9e5),
      ),
    ),
    dividerTheme: const DividerThemeData(
      color: hairline,
      space: 1,
      thickness: .5,
    ),
    listTileTheme: const ListTileThemeData(
      iconColor: blue,
      textColor: ink,
      contentPadding: EdgeInsets.symmetric(horizontal: 17, vertical: 2),
    ),
    popupMenuTheme: PopupMenuThemeData(
      color: Colors.white,
      surfaceTintColor: Colors.white,
      elevation: 12,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
      textStyle: const TextStyle(
        color: ink,
        fontSize: 14,
        fontWeight: FontWeight.w600,
      ),
    ),
    progressIndicatorTheme: const ProgressIndicatorThemeData(color: blue),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Color(0xfff5f7fa),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 15),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppRadii.field),
        borderSide: BorderSide.none,
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppRadii.field),
        borderSide: const BorderSide(color: hairline),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppRadii.field),
        borderSide: const BorderSide(color: blue, width: 1.5),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        minimumSize: const Size(44, 48),
        backgroundColor: navy,
        foregroundColor: Colors.white,
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 15),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        textStyle: const TextStyle(fontWeight: FontWeight.w700),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: blue,
        textStyle: const TextStyle(fontWeight: FontWeight.w700),
      ),
    ),
    floatingActionButtonTheme: const FloatingActionButtonThemeData(
      backgroundColor: navy,
      foregroundColor: Colors.white,
      elevation: 5,
      shape: StadiumBorder(),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        minimumSize: const Size(44, 44),
        foregroundColor: navy,
        side: const BorderSide(color: Color(0xffbfd3e8)),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
    ),
    navigationBarTheme: NavigationBarThemeData(
      height: 72,
      backgroundColor: Colors.white,
      indicatorColor: const Color(0xffe5f1f8),
      labelTextStyle: WidgetStateProperty.resolveWith(
        (states) => TextStyle(
          fontSize: 11,
          fontWeight: states.contains(WidgetState.selected)
              ? FontWeight.w800
              : FontWeight.w600,
          color: states.contains(WidgetState.selected) ? navy : muted,
        ),
      ),
      iconTheme: WidgetStateProperty.resolveWith(
        (states) => IconThemeData(
          color: states.contains(WidgetState.selected) ? navy : muted,
        ),
      ),
    ),
    badgeTheme: const BadgeThemeData(
      backgroundColor: Color(0xffdb5363),
      textColor: Colors.white,
    ),
    textTheme: const TextTheme(
      displaySmall: TextStyle(
        fontSize: 32,
        fontWeight: FontWeight.w800,
        color: ink,
        letterSpacing: -.8,
      ),
      headlineSmall: TextStyle(
        fontSize: 25,
        fontWeight: FontWeight.w800,
        color: ink,
        letterSpacing: -.4,
      ),
      titleLarge: TextStyle(
        fontSize: 20,
        fontWeight: FontWeight.w800,
        color: ink,
      ),
      titleMedium: TextStyle(
        fontSize: 16,
        fontWeight: FontWeight.w700,
        color: ink,
      ),
      bodyMedium: TextStyle(fontSize: 14, height: 1.45, color: ink),
      bodySmall: TextStyle(fontSize: 12.5, height: 1.35, color: muted),
    ),
  );
}

/// Soft iOS-like scrolling without Android's edge glow.
class AppScrollBehavior extends MaterialScrollBehavior {
  const AppScrollBehavior();

  @override
  ScrollPhysics getScrollPhysics(BuildContext context) =>
      const BouncingScrollPhysics(parent: AlwaysScrollableScrollPhysics());

  @override
  Widget buildOverscrollIndicator(
    BuildContext context,
    Widget child,
    ScrollableDetails details,
  ) => child;
}
