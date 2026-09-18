String normalizeApiOrigin(String raw) {
  var normalized = raw.trim();
  while (normalized.endsWith('/')) {
    normalized = normalized.substring(0, normalized.length - 1);
  }

  const legacySuffix = '/api/v1';
  if (normalized.toLowerCase().endsWith(legacySuffix)) {
    normalized = normalized.substring(0, normalized.length - legacySuffix.length);
  }

  return normalized;
}
