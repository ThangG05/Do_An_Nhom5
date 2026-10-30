import 'package:flutter/material.dart';

/// R2 signs downloads on a different origin from Flutter Web. A browser image
/// element can display that URL even when the bucket has no fetch CORS rule.
WebHtmlElementStrategy imageWebStrategy(String url) {
  final host = Uri.tryParse(url)?.host.toLowerCase() ?? '';
  if (host.endsWith('.r2.cloudflarestorage.com') || host.endsWith('.r2.dev')) {
    return WebHtmlElementStrategy.prefer;
  }
  return WebHtmlElementStrategy.fallback;
}

class AppNetworkImage extends StatelessWidget {
  const AppNetworkImage(
    this.url, {
    super.key,
    this.width,
    this.height,
    this.fit,
    this.errorBuilder,
  });

  final String url;
  final double? width;
  final double? height;
  final BoxFit? fit;
  final ImageErrorWidgetBuilder? errorBuilder;

  @override
  Widget build(BuildContext context) {
    final source = url.trim();
    if (source == '/assets/logo.png') {
      return Image.asset(
        'assets/brand/hvnh-logo.png',
        width: width,
        height: height,
        fit: fit,
      );
    }
    final uri = Uri.tryParse(source);
    if (uri == null || (uri.scheme != 'http' && uri.scheme != 'https')) {
      return errorBuilder?.call(
            context,
            ArgumentError('Invalid image URL'),
            null,
          ) ??
          const Icon(Icons.broken_image_outlined);
    }
    return Image.network(
      source,
      width: width,
      height: height,
      fit: fit,
      webHtmlElementStrategy: imageWebStrategy(source),
      errorBuilder: errorBuilder,
    );
  }
}
