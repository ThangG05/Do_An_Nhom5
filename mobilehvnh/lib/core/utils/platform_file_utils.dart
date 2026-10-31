import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';

/// Web file picker exposes the selected data as bytes; touching [PlatformFile.path]
/// on web throws. Keep path access behind this helper for native platforms.
String? platformFilePath(PlatformFile file) => kIsWeb ? null : file.path;
