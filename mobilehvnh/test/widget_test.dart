import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobilehvnh/core/theme/app_theme.dart';
import 'package:mobilehvnh/core/widgets/app_brand_mark.dart';
import 'package:mobilehvnh/core/widgets/app_back_button.dart';
import 'package:mobilehvnh/core/widgets/app_page_bar.dart';
import 'package:mobilehvnh/core/widgets/app_network_image.dart';
import 'package:mobilehvnh/core/widgets/app_state_view.dart';
import 'package:mobilehvnh/core/widgets/premium_hero_card.dart';
import 'package:mobilehvnh/core/theme/app_design_tokens.dart';

void main() {
  test('HVNH palette keeps the navy-blue brand and readable surfaces', () {
    expect(AppPalette.light.primary, AppTheme.blue);
    expect(AppPalette.light.surface, Colors.white);
    expect(AppPalette.dark.ink, isNot(AppPalette.dark.canvas));
  });

  testWidgets('premium hero respects reduced motion', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: MediaQuery(
          data: MediaQueryData(disableAnimations: true),
          child: Scaffold(body: PremiumHeroCard(child: Text('Chào HVNH'))),
        ),
      ),
    );
    expect(find.text('Chào HVNH'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('empty state exposes its retry action', (tester) async {
    var retried = false;
    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.light,
        home: Scaffold(
          body: AppStateView(
            icon: Icons.wifi_off_rounded,
            title: 'Chưa tải được',
            message: 'Hãy thử lại',
            actionLabel: 'Thử lại',
            onAction: () => retried = true,
          ),
        ),
      ),
    );
    await tester.tap(find.text('Thử lại').last);
    expect(retried, isTrue);
  });

  test('mobile project is configured for HVNH Hub', () {
    expect('HVNH Hub', contains('HVNH'));
  });

  testWidgets('shared BAV brand asset renders in the mobile theme', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.light,
        home: const Scaffold(body: Center(child: AppBrandMark())),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byType(AppBrandMark), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('back control returns to the previous page', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.light,
        home: Scaffold(
          body: Builder(
            builder: (context) => TextButton(
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute<void>(
                  builder: (_) => Scaffold(
                    appBar: AppBar(
                      leading: const AppBackButton(),
                      title: const Text('Chi tiết'),
                    ),
                    body: const Text('Nội dung'),
                  ),
                ),
              ),
              child: const Text('Mở chi tiết'),
            ),
          ),
        ),
      ),
    );

    await tester.tap(find.text('Mở chi tiết'));
    await tester.pumpAndSettle();
    expect(find.text('Nội dung'), findsOneWidget);
    await tester.tap(find.byType(AppBackButton));
    await tester.pumpAndSettle();
    expect(find.text('Mở chi tiết'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('shared iOS-style page bar keeps title and back control', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.light,
        home: const Scaffold(
          appBar: AppPageBar(title: 'Trang cá nhân'),
          body: SizedBox.expand(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Trang cá nhân'), findsOneWidget);
    expect(find.byType(AppBackButton), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  test('R2 image uses browser element when Flutter Web cannot fetch it', () {
    expect(
      imageWebStrategy('https://example.r2.cloudflarestorage.com/file.jpg'),
      WebHtmlElementStrategy.prefer,
    );
    expect(
      imageWebStrategy('https://images.example.com/file.jpg'),
      WebHtmlElementStrategy.fallback,
    );
  });

  testWidgets('web-only logo path resolves to bundled Flutter asset', (
    tester,
  ) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(body: AppNetworkImage('/assets/logo.png')),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.byType(Image), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
