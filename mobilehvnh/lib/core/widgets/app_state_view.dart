import 'package:flutter/material.dart';

import '../theme/app_design_tokens.dart';

/// Consistent, readable loading/empty/error states without a distracting
/// infinite shimmer on long feeds.
class AppStateView extends StatelessWidget {
  const AppStateView({
    super.key,
    required this.icon,
    required this.title,
    required this.message,
    this.actionLabel,
    this.onAction,
  });

  final IconData icon;
  final String title;
  final String message;
  final String? actionLabel;
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) {
    final palette = AppPalette.of(context);
    return Semantics(
      liveRegion: true,
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 360),
          child: Padding(
            padding: const EdgeInsets.all(AppSpacing.xl),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 58,
                  height: 58,
                  decoration: BoxDecoration(
                    color: palette.primarySoft,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Icon(icon, color: palette.primary, size: 27),
                ),
                const SizedBox(height: AppSpacing.md),
                Text(
                  title,
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: AppSpacing.xs),
                Text(
                  message,
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                if (onAction != null && actionLabel != null) ...[
                  const SizedBox(height: AppSpacing.md),
                  OutlinedButton(
                    onPressed: onAction,
                    child: Text(actionLabel!),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class AppLoadingList extends StatelessWidget {
  const AppLoadingList({super.key, this.count = 3});
  final int count;

  @override
  Widget build(BuildContext context) {
    final palette = AppPalette.of(context);
    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 760),
        child: ListView.separated(
          padding: const EdgeInsets.all(AppSpacing.md),
          itemCount: count,
          separatorBuilder: (_, _) => const SizedBox(height: AppSpacing.md),
          itemBuilder: (_, index) => Semantics(
            label: 'Đang tải nội dung',
            child: Container(
              height: index == 0 ? 120 : 210,
              decoration: BoxDecoration(
                color: palette.surface,
                border: Border.all(color: palette.hairline),
                borderRadius: BorderRadius.circular(AppRadii.card),
              ),
              child: Padding(
                padding: const EdgeInsets.all(AppSpacing.md),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _bar(palette.surfaceSecondary, 120),
                    const SizedBox(height: AppSpacing.sm),
                    _bar(palette.surfaceSecondary, 220),
                    const SizedBox(height: AppSpacing.sm),
                    _bar(palette.surfaceSecondary, 170),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _bar(Color color, double width) => Container(
    width: width,
    height: 12,
    decoration: BoxDecoration(
      color: color,
      borderRadius: BorderRadius.circular(8),
    ),
  );
}
