import 'package:flutter/widgets.dart';
import 'package:google_sign_in_web/web_only.dart' as google_web;

Widget renderGoogleButton(double width) => google_web.renderButton(
  configuration: google_web.GSIButtonConfiguration(
    type: google_web.GSIButtonType.standard,
    theme: google_web.GSIButtonTheme.outline,
    size: google_web.GSIButtonSize.large,
    text: google_web.GSIButtonText.signinWith,
    shape: google_web.GSIButtonShape.pill,
    minimumWidth: width.clamp(160.0, 400.0).toDouble(),
    locale: 'vi',
  ),
);
