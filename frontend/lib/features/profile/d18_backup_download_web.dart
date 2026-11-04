// Web-only adapter for the repository's file_picker 8.x generation.
// The browser requires a direct click to initiate a Blob download.
import 'dart:html' as html;
import 'dart:typed_data';

bool triggerD18BackupDownload(Uint8List bytes) {
  final blob = html.Blob(<Object>[bytes], 'application/octet-stream');
  final url = html.Url.createObjectUrlFromBlob(blob);
  final anchor = html.AnchorElement(href: url)
    ..download = 'iamina-d18-backup.iamina';
  anchor.style.display = 'none';
  html.document.body?.children.add(anchor);
  try {
    anchor.click();
    return true;
  } finally {
    anchor.remove();
    // Give the browser time to consume the URL; this is not confirmation
    // that the patient saved the downloaded file.
    Future<void>.delayed(const Duration(seconds: 3), () {
      html.Url.revokeObjectUrl(url);
    });
  }
}
