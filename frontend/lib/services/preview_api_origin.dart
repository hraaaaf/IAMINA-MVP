/// Explicit, Preview-only same-origin API transport. Never stores credentials.
const bool kIaminaPreviewSameOriginApi = bool.fromEnvironment(
  'IAMINA_PREVIEW_SAME_ORIGIN_API',
  defaultValue: false,
);

String resolveIaminaApiOrigin(String configuredBaseUrl) {
  if (!kIaminaPreviewSameOriginApi) return configuredBaseUrl;
  final base = Uri.base;
  if (base.scheme != 'https' || base.host.isEmpty) {
    throw StateError('IAMINA Preview API requires an HTTPS browser origin');
  }
  return base.origin;
}
