/// Explicit, Preview-only same-origin API transport. Never stores credentials.
const bool kIaminaPreviewSameOriginApi = bool.fromEnvironment(
  'IAMINA_PREVIEW_SAME_ORIGIN_API',
  defaultValue: false,
);

String resolveIaminaApiOrigin(String configuredBaseUrl) =>
    resolveIaminaApiOriginForMode(
      configuredBaseUrl,
      sameOriginPreview: kIaminaPreviewSameOriginApi,
      browserUri: Uri.base,
    );

/// Pure routing contract to make Preview/Production choices verifiable offline.
/// Only the compile-time flag above selects Preview in the actual application.
String resolveIaminaApiOriginForMode(
  String configuredBaseUrl, {
  required bool sameOriginPreview,
  required Uri browserUri,
}) {
  if (!sameOriginPreview) return configuredBaseUrl;
  if (browserUri.scheme != 'https' || browserUri.host.isEmpty ||
      browserUri.userInfo.isNotEmpty) {
    throw StateError('IAMINA Preview API requires an HTTPS browser origin');
  }
  return browserUri.origin;
}
