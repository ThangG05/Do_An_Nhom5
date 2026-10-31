import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:file_picker/file_picker.dart';

import 'app_config.dart';

class ApiException implements Exception {
  const ApiException(this.message, this.statusCode);
  final String message;
  final int statusCode;
  @override
  String toString() => message;
}

class ApiClient {
  ApiClient(
    this._tokenProvider, {
    this.refreshTokenProvider,
    this.onSessionRefreshed,
  });
  final Future<String?> Function() _tokenProvider;
  final Future<String?> Function()? refreshTokenProvider;
  final Future<void> Function(Map<String, dynamic> tokens)? onSessionRefreshed;
  // Reuse one connection pool for API calls instead of opening a new client
  // for every request (especially costly on mobile networks).
  final http.Client _httpClient = http.Client();
  Future<bool>? _refreshing;

  Future<bool> _refreshAccessToken() {
    final active = _refreshing;
    if (active != null) return active;
    final operation = _performRefresh();
    _refreshing = operation;
    return operation.whenComplete(() => _refreshing = null);
  }

  Future<bool> _performRefresh() async {
    final refreshToken = await refreshTokenProvider?.call();
    if (refreshToken == null ||
        refreshToken.isEmpty ||
        onSessionRefreshed == null) {
      return false;
    }
    try {
      final response = await _httpClient.post(
        Uri.parse('${AppConfig.apiBaseUrl}/auth/refresh'),
        headers: const {
          'Content-Type': 'application/json',
          'X-HVNH-Client': 'mobile',
        },
        body: jsonEncode({'refresh_token': refreshToken}),
      );
      if (response.statusCode < 200 ||
          response.statusCode >= 300 ||
          response.body.isEmpty) {
        return false;
      }
      final tokens = Map<String, dynamic>.from(
        jsonDecode(response.body) as Map,
      );
      await onSessionRefreshed!(tokens);
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<http.Response> _send(
    Future<http.Response> Function(String? accessToken) request, {
    required bool authenticated,
  }) async {
    var token = authenticated ? await _tokenProvider() : null;
    var response = await request(token);
    if (authenticated &&
        response.statusCode == 401 &&
        await _refreshAccessToken()) {
      token = await _tokenProvider();
      response = await request(token);
    }
    return response;
  }

  Future<Map<String, dynamic>> post(
    String path,
    Map<String, dynamic> body, {
    bool authenticated = false,
  }) async {
    final headers = <String, String>{
      'Content-Type': 'application/json',
      'X-HVNH-Client': 'mobile',
    };
    try {
      final response = await _send(
        (token) => _httpClient.post(
          Uri.parse('${AppConfig.apiBaseUrl}$path'),
          headers: {
            ...headers,
            if (token != null) 'Authorization': 'Bearer $token',
          },
          body: jsonEncode(body),
        ),
        authenticated: authenticated,
      );
      final decoded = response.body.isEmpty
          ? <String, dynamic>{}
          : jsonDecode(response.body) as Map<String, dynamic>;
      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw ApiException(
          decoded['detail']?.toString() ?? 'Không thể kết nối máy chủ.',
          response.statusCode,
        );
      }
      return decoded;
    } on ApiException {
      rethrow;
    } catch (_) {
      throw const ApiException(
        'Không thể kết nối đến HVNH Hub. Hãy kiểm tra backend và địa chỉ API.',
        0,
      );
    }
  }

  Future<List<dynamic>> getList(String path) async {
    try {
      final response = await _send(
        (accessToken) => _httpClient.get(
          Uri.parse('${AppConfig.apiBaseUrl}$path'),
          headers: {
            'X-HVNH-Client': 'mobile',
            if (accessToken != null) 'Authorization': 'Bearer $accessToken',
          },
        ),
        authenticated: true,
      );
      final decoded = jsonDecode(response.body);
      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw ApiException(
          (decoded as Map)['detail']?.toString() ?? 'Không thể tải dữ liệu.',
          response.statusCode,
        );
      }
      return decoded as List<dynamic>;
    } catch (error) {
      if (error is ApiException) rethrow;
      throw const ApiException(
        'Không thể tải bảng tin. Hãy kiểm tra backend.',
        0,
      );
    }
  }

  Future<({List<dynamic> items, String? nextCursor})> getListPage(
    String path,
  ) async {
    try {
      final response = await _send(
        (accessToken) => _httpClient.get(
          Uri.parse('${AppConfig.apiBaseUrl}$path'),
          headers: {
            'X-HVNH-Client': 'mobile',
            if (accessToken != null) 'Authorization': 'Bearer $accessToken',
          },
        ),
        authenticated: true,
      );
      final decoded = response.body.isEmpty
          ? const []
          : jsonDecode(response.body);
      if (response.statusCode < 200 || response.statusCode >= 300) {
        final detail = decoded is Map ? decoded['detail']?.toString() : null;
        throw ApiException(
          detail ?? 'Không thể tải dữ liệu.',
          response.statusCode,
        );
      }
      return (
        items: List<dynamic>.from(decoded as List),
        nextCursor: response.headers['x-next-cursor'],
      );
    } on ApiException {
      rethrow;
    } catch (_) {
      throw const ApiException('Không thể kết nối đến HVNH Hub.', 0);
    }
  }

  Future<Map<String, dynamic>> getObject(String path) async {
    try {
      final response = await _send(
        (accessToken) => _httpClient.get(
          Uri.parse('${AppConfig.apiBaseUrl}$path'),
          headers: {
            'X-HVNH-Client': 'mobile',
            if (accessToken != null) 'Authorization': 'Bearer $accessToken',
          },
        ),
        authenticated: true,
      );
      final decoded = response.body.isEmpty
          ? <String, dynamic>{}
          : jsonDecode(response.body) as Map<String, dynamic>;
      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw ApiException(
          decoded['detail']?.toString() ?? 'Không thể tải dữ liệu.',
          response.statusCode,
        );
      }
      return decoded;
    } on ApiException {
      rethrow;
    } catch (_) {
      throw const ApiException('Không thể kết nối đến HVNH Hub.', 0);
    }
  }

  /// Fetches a public endpoint without attaching or refreshing a user session.
  Future<Map<String, dynamic>> getPublicObject(String path) async {
    try {
      final response = await _httpClient.get(
        Uri.parse('${AppConfig.apiBaseUrl}$path'),
        headers: const {'X-HVNH-Client': 'mobile'},
      );
      final decoded = response.body.isEmpty
          ? <String, dynamic>{}
          : jsonDecode(response.body) as Map<String, dynamic>;
      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw ApiException(
          decoded['detail']?.toString() ?? 'Không thể tải cấu hình công khai.',
          response.statusCode,
        );
      }
      return decoded;
    } on ApiException {
      rethrow;
    } catch (_) {
      throw const ApiException('Không thể kết nối đến HVNH Hub.', 0);
    }
  }

  Future<Map<String, dynamic>?> getOptionalObject(String path) async {
    try {
      final response = await _send(
        (accessToken) => _httpClient.get(
          Uri.parse('${AppConfig.apiBaseUrl}$path'),
          headers: {
            'X-HVNH-Client': 'mobile',
            if (accessToken != null) 'Authorization': 'Bearer $accessToken',
          },
        ),
        authenticated: true,
      );
      final decoded = response.body.isEmpty ? null : jsonDecode(response.body);
      if (response.statusCode < 200 || response.statusCode >= 300) {
        final detail = decoded is Map ? decoded['detail']?.toString() : null;
        throw ApiException(
          detail ?? 'Không thể tải dữ liệu.',
          response.statusCode,
        );
      }
      return decoded is Map ? Map<String, dynamic>.from(decoded) : null;
    } on ApiException {
      rethrow;
    } catch (_) {
      throw const ApiException('Không thể kết nối đến HVNH Hub.', 0);
    }
  }

  Future<Map<String, dynamic>> put(
    String path,
    Map<String, dynamic> body,
  ) async {
    final response = await _send(
      (accessToken) => _httpClient.put(
        Uri.parse('${AppConfig.apiBaseUrl}$path'),
        headers: {
          'Content-Type': 'application/json',
          'X-HVNH-Client': 'mobile',
          if (accessToken != null) 'Authorization': 'Bearer $accessToken',
        },
        body: jsonEncode(body),
      ),
      authenticated: true,
    );
    final decoded = response.body.isEmpty
        ? <String, dynamic>{}
        : jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw ApiException(
        decoded['detail']?.toString() ?? 'Không thể cập nhật.',
        response.statusCode,
      );
    }
    return decoded;
  }

  Future<Map<String, dynamic>> patch(
    String path,
    Map<String, dynamic> body,
  ) async {
    final response = await _send(
      (accessToken) => _httpClient.patch(
        Uri.parse('${AppConfig.apiBaseUrl}$path'),
        headers: {
          'Content-Type': 'application/json',
          'X-HVNH-Client': 'mobile',
          if (accessToken != null) 'Authorization': 'Bearer $accessToken',
        },
        body: jsonEncode(body),
      ),
      authenticated: true,
    );
    final decoded = response.body.isEmpty
        ? <String, dynamic>{}
        : jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw ApiException(
        decoded['detail']?.toString() ?? 'Không thể cập nhật.',
        response.statusCode,
      );
    }
    return decoded;
  }

  Future<void> delete(String path) async {
    final response = await _send(
      (accessToken) => _httpClient.delete(
        Uri.parse('${AppConfig.apiBaseUrl}$path'),
        headers: {
          'X-HVNH-Client': 'mobile',
          if (accessToken != null) 'Authorization': 'Bearer $accessToken',
        },
      ),
      authenticated: true,
    );
    if (response.statusCode < 200 || response.statusCode >= 300) {
      Map<dynamic, dynamic> decoded = const {};
      try {
        if (response.body.isNotEmpty) {
          decoded = jsonDecode(response.body) as Map;
        }
      } catch (_) {}
      throw ApiException(
        decoded['detail']?.toString() ?? 'Không thể xóa dữ liệu.',
        response.statusCode,
      );
    }
  }

  Future<Map<String, dynamic>> deleteObject(String path) async {
    final response = await _send(
      (accessToken) => _httpClient.delete(
        Uri.parse('${AppConfig.apiBaseUrl}$path'),
        headers: {
          'X-HVNH-Client': 'mobile',
          if (accessToken != null) 'Authorization': 'Bearer $accessToken',
        },
      ),
      authenticated: true,
    );
    final decoded = response.body.isEmpty
        ? <String, dynamic>{}
        : Map<String, dynamic>.from(jsonDecode(response.body) as Map);
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw ApiException(
        decoded['detail']?.toString() ?? 'Không thể thu hồi tin nhắn.',
        response.statusCode,
      );
    }
    return decoded;
  }

  /// DELETE endpoints that require an audit reason still need a JSON body.
  /// Keeping this separate avoids accidentally sending a body to ordinary
  /// resource deletes such as leaving a group.
  Future<void> deleteWithBody(String path, Map<String, dynamic> body) async {
    final response = await _send(
      (accessToken) => _httpClient.delete(
        Uri.parse('${AppConfig.apiBaseUrl}$path'),
        headers: {
          'Content-Type': 'application/json',
          'X-HVNH-Client': 'mobile',
          if (accessToken != null) 'Authorization': 'Bearer $accessToken',
        },
        body: jsonEncode(body),
      ),
      authenticated: true,
    );
    if (response.statusCode < 200 || response.statusCode >= 300) {
      Map<dynamic, dynamic> decoded = const {};
      try {
        if (response.body.isNotEmpty) {
          decoded = jsonDecode(response.body) as Map;
        }
      } catch (_) {}
      throw ApiException(
        decoded['detail']?.toString() ?? 'Không thể xóa dữ liệu.',
        response.statusCode,
      );
    }
  }

  Future<Map<String, dynamic>> postAuthenticated(
    String path,
    Map<String, dynamic> body,
  ) => post(path, body, authenticated: true);

  /// Uploads one selected local file through the existing FastAPI media endpoint.
  /// The server owns validation and sends the final object to Cloudflare R2.
  Future<String> uploadFile(
    PlatformFile file, {
    String endpoint = '/media/upload/post',
  }) async {
    try {
      final response = await _send((token) async {
        if (token == null || token.isEmpty) {
          return http.Response(
            jsonEncode({'detail': 'Phiên đăng nhập đã hết hạn.'}),
            401,
          );
        }
        // A multipart request cannot be sent twice, so rebuild it when a 401
        // triggers refresh-token rotation.
        final request = http.MultipartRequest(
          'POST',
          Uri.parse('${AppConfig.apiBaseUrl}$endpoint'),
        );
        request.headers.addAll({
          'Authorization': 'Bearer $token',
          'X-HVNH-Client': 'mobile',
        });
        if (kIsWeb && file.bytes != null) {
          request.files.add(
            http.MultipartFile.fromBytes(
              'file',
              file.bytes!,
              filename: file.name,
            ),
          );
        } else if (file.path != null) {
          request.files.add(
            await http.MultipartFile.fromPath(
              'file',
              file.path!,
              filename: file.name,
            ),
          );
        } else if (file.bytes != null) {
          request.files.add(
            http.MultipartFile.fromBytes(
              'file',
              file.bytes!,
              filename: file.name,
            ),
          );
        } else {
          throw const ApiException('Không thể đọc tệp đã chọn.', 0);
        }
        return http.Response.fromStream(await _httpClient.send(request));
      }, authenticated: true);
      final decoded = response.body.isEmpty
          ? <String, dynamic>{}
          : jsonDecode(response.body) as Map<String, dynamic>;
      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw ApiException(
          decoded['detail']?.toString() ?? 'Không thể tải tệp lên.',
          response.statusCode,
        );
      }
      final mediaId = decoded['media_id']?.toString();
      if (mediaId == null || mediaId.isEmpty) {
        throw const ApiException('Máy chủ chưa trả về tệp đã tải lên.', 0);
      }
      return mediaId;
    } on ApiException {
      rethrow;
    } catch (_) {
      throw const ApiException('Không thể tải tệp lên R2. Hãy thử lại.', 0);
    }
  }

  Future<String> uploadPostFile(PlatformFile file) => uploadFile(file);

  Future<Map<String, dynamic>> postFiles(
    String path,
    Map<String, String> fields,
    List<PlatformFile> files,
  ) async {
    final response = await _send((token) async {
      if (token == null || token.isEmpty) {
        return http.Response(
          jsonEncode({'detail': 'Phiên đăng nhập đã hết hạn.'}),
          401,
        );
      }
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('${AppConfig.apiBaseUrl}$path'),
      );
      request.headers.addAll({
        'Authorization': 'Bearer $token',
        'X-HVNH-Client': 'mobile',
      });
      request.fields.addAll(fields);
      for (final file in files) {
        if (kIsWeb && file.bytes != null) {
          request.files.add(
            http.MultipartFile.fromBytes(
              'files',
              file.bytes!,
              filename: file.name,
            ),
          );
        } else if (file.path != null) {
          request.files.add(
            await http.MultipartFile.fromPath(
              'files',
              file.path!,
              filename: file.name,
            ),
          );
        } else if (file.bytes != null) {
          request.files.add(
            http.MultipartFile.fromBytes(
              'files',
              file.bytes!,
              filename: file.name,
            ),
          );
        } else {
          throw const ApiException('Không thể đọc tệp tài liệu.', 0);
        }
      }
      return http.Response.fromStream(await _httpClient.send(request));
    }, authenticated: true);
    final decoded = response.body.isEmpty
        ? <String, dynamic>{}
        : Map<String, dynamic>.from(jsonDecode(response.body) as Map);
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw ApiException(
        decoded['detail']?.toString() ?? 'Không thể gửi tài liệu.',
        response.statusCode,
      );
    }
    return decoded;
  }

  Future<Uint8List> downloadBytes(String path) async {
    final response = await _send(
      (token) => _httpClient.get(
        Uri.parse('${AppConfig.apiBaseUrl}$path'),
        headers: {
          'X-HVNH-Client': 'mobile',
          if (token != null) 'Authorization': 'Bearer $token',
        },
      ),
      authenticated: true,
    );
    if (response.statusCode < 200 || response.statusCode >= 300) {
      String? detail;
      try {
        detail = (jsonDecode(response.body) as Map)['detail']?.toString();
      } catch (_) {}
      throw ApiException(
        detail ?? 'Không thể tải bộ tài liệu.',
        response.statusCode,
      );
    }
    return response.bodyBytes;
  }
}
