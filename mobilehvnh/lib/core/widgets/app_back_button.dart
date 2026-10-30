import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';

import '../theme/app_theme.dart';

/// One consistent, iOS-inspired back affordance for pushed Flutter pages.
class AppBackButton extends StatelessWidget {
  const AppBackButton({super.key, this.onPressed});

  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(left: 7),
    child: Tooltip(
      message: 'Quay lại',
      child: CupertinoButton(
        padding: EdgeInsets.zero,
        onPressed: onPressed ?? () => Navigator.of(context).maybePop(),
        child: const SizedBox(
          width: 44,
          height: 44,
          child: Center(
            child: Icon(
              CupertinoIcons.chevron_back,
              size: 23,
              color: AppTheme.blue,
            ),
          ),
        ),
      ),
    ),
  );
}
