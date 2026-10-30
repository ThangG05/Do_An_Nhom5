import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';

import '../theme/app_theme.dart';
import 'app_back_button.dart';

/// Shared iPhone-style navigation chrome for pages pushed above the tab shell.
/// It keeps the HVNH palette while giving every feature the same title,
/// back affordance, translucency and touch target.
class AppPageBar extends StatelessWidget implements PreferredSizeWidget {
  const AppPageBar({
    super.key,
    required this.title,
    this.actions,
    this.showBack = true,
    this.centerTitle = true,
    this.leading,
  });

  final String title;
  final List<Widget>? actions;
  final bool showBack;
  final bool centerTitle;
  final Widget? leading;

  @override
  Size get preferredSize => const Size.fromHeight(44);

  @override
  Widget build(BuildContext context) => CupertinoNavigationBar(
    automaticallyImplyLeading: false,
    leading: leading ?? (showBack ? const AppBackButton() : null),
    middle: Text(
      title,
      maxLines: 1,
      overflow: TextOverflow.ellipsis,
      style: const TextStyle(
        color: AppTheme.ink,
        fontSize: 17,
        fontWeight: FontWeight.w700,
        letterSpacing: -.35,
      ),
    ),
    trailing: actions == null
        ? null
        : Material(
            type: MaterialType.transparency,
            child: Row(mainAxisSize: MainAxisSize.min, children: actions!),
          ),
    backgroundColor: const Color(0xf2fafcff),
    border: const Border(
      bottom: BorderSide(color: AppTheme.hairline, width: .5),
    ),
    transitionBetweenRoutes: false,
  );
}

/// A quiet, rounded action used on translucent navigation bars.
class AppPageBarAction extends StatelessWidget {
  const AppPageBarAction({
    super.key,
    required this.icon,
    required this.tooltip,
    required this.onPressed,
  });

  final IconData icon;
  final String tooltip;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) => Tooltip(
    message: tooltip,
    child: CupertinoButton(
      padding: EdgeInsets.zero,
      onPressed: onPressed,
      child: SizedBox(
        width: 44,
        height: 44,
        child: Center(child: Icon(icon, size: 21, color: AppTheme.blue)),
      ),
    ),
  );
}
