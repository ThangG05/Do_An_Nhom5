import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobilehvnh/app/app.dart';
import 'package:mobilehvnh/app/di/app_dependencies.dart';
import 'package:mobilehvnh/core/theme/app_theme.dart';
import 'package:mobilehvnh/core/widgets/app_back_button.dart';
import 'package:mobilehvnh/features/auth/presentation/pages/login_page.dart';
import 'package:mobilehvnh/features/auth/presentation/pages/welcome_page.dart';

class _Dependencies implements AppDependencies {
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  testWidgets('a fresh app launch starts at the introduction', (tester) async {
    await tester.pumpWidget(HvnhHubApp(dependencies: _Dependencies()));
    expect(find.byType(WelcomePage), findsOneWidget);
    expect(find.byType(LoginPage), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('welcome opens login and iOS-style back returns to welcome', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.light,
        home: WelcomePage(
          dependencies: _Dependencies(),
          onSignedIn: () async {},
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('Một cộng đồng.\nVô vàn kết nối.'), findsOneWidget);

    await tester.tap(find.text('Tôi đã có tài khoản'));
    await tester.pumpAndSettle();
    expect(find.byType(LoginPage), findsOneWidget);
    await tester.tap(find.byType(AppBackButton));
    await tester.pumpAndSettle();
    expect(find.byType(WelcomePage), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
