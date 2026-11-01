import 'package:file_picker/file_picker.dart';

/// Infers a useful multipart MIME type even when browser file pickers report
/// `application/octet-stream` (which makes the API reject otherwise valid
/// images and office documents).
String uploadMimeType(PlatformFile file) {
  final bytes = file.bytes;
  if (bytes != null && bytes.length >= 12) {
    if (bytes.length >= 3 &&
        bytes[0] == 0xff &&
        bytes[1] == 0xd8 &&
        bytes[2] == 0xff) {
      return 'image/jpeg';
    }
    if (bytes.length >= 8 &&
        bytes[0] == 0x89 &&
        bytes[1] == 0x50 &&
        bytes[2] == 0x4e &&
        bytes[3] == 0x47) {
      return 'image/png';
    }
    if (String.fromCharCodes(bytes.take(4)) == 'RIFF' &&
        String.fromCharCodes(bytes.skip(8).take(4)) == 'WEBP') {
      return 'image/webp';
    }
    if (String.fromCharCodes(bytes.take(5)) == '%PDF-') {
      return 'application/pdf';
    }
    if (bytes[0] == 0x50 && bytes[1] == 0x4b) {
      return switch (file.extension?.toLowerCase()) {
        'docx' =>
          'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xlsx' =>
          'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'pptx' =>
          'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'zip' => 'application/zip',
        _ => 'application/zip',
      };
    }
  }

  return switch (file.extension?.toLowerCase()) {
    'jpg' || 'jpeg' => 'image/jpeg',
    'png' => 'image/png',
    'webp' => 'image/webp',
    'pdf' => 'application/pdf',
    'txt' => 'text/plain',
    'doc' => 'application/msword',
    'docx' =>
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'xls' => 'application/vnd.ms-excel',
    'xlsx' =>
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'ppt' => 'application/vnd.ms-powerpoint',
    'pptx' =>
      'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'zip' => 'application/zip',
    'mp4' => 'video/mp4',
    'mov' => 'video/quicktime',
    'webm' => 'video/webm',
    'mp3' => 'audio/mpeg',
    'm4a' => 'audio/mp4',
    'ogg' => 'audio/ogg',
    'wav' => 'audio/wav',
    _ => 'application/octet-stream',
  };
}
