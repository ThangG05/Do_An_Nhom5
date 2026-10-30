import 'dart:async';

import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';

import '../domain/repositories/feed_repository.dart';

class LocationPickerSheet extends StatefulWidget {
  const LocationPickerSheet({super.key, required this.repository});

  final FeedRepository repository;

  @override
  State<LocationPickerSheet> createState() => _LocationPickerSheetState();
}

class _LocationPickerSheetState extends State<LocationPickerSheet> {
  final _query = TextEditingController();
  Timer? _debounce;
  List<Map<String, dynamic>> _suggestions = [];
  bool _findingDevice = false;
  bool _searching = false;
  String? _message;

  @override
  void dispose() {
    _debounce?.cancel();
    _query.dispose();
    super.dispose();
  }

  void _search(String text) {
    _debounce?.cancel();
    if (text.trim().length < 2) {
      setState(() => _suggestions = []);
      return;
    }
    _debounce = Timer(const Duration(milliseconds: 350), () async {
      setState(() {
        _searching = true;
        _message = null;
      });
      try {
        final result = await widget.repository.searchLocations(text.trim());
        if (mounted) setState(() => _suggestions = result);
      } catch (_) {
        if (mounted)
          setState(
            () =>
                _message = 'Chưa thể tìm địa điểm lúc này. Bạn có thể thử lại.',
          );
      } finally {
        if (mounted) setState(() => _searching = false);
      }
    });
  }

  Future<void> _useCurrentLocation() async {
    if (_findingDevice) return;
    setState(() {
      _findingDevice = true;
      _message = null;
    });
    try {
      if (!await Geolocator.isLocationServiceEnabled()) {
        throw Exception('Dịch vụ vị trí trên thiết bị đang tắt.');
      }
      var permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied)
        permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied ||
          permission == LocationPermission.deniedForever) {
        throw Exception('Bạn chưa cấp quyền vị trí cho HVNH Hub.');
      }
      final position = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.medium,
        ),
      );
      final location = await widget.repository.reverseLocation(
        position.latitude,
        position.longitude,
      );
      if (!mounted) return;
      Navigator.pop(
        context,
        location ??
            {
              'name': 'Vị trí hiện tại',
              'address':
                  '${position.latitude.toStringAsFixed(6)}, ${position.longitude.toStringAsFixed(6)}',
              'latitude': position.latitude,
              'longitude': position.longitude,
            },
      );
    } catch (error) {
      if (mounted)
        setState(
          () => _message = error.toString().replaceFirst('Exception: ', ''),
        );
    } finally {
      if (mounted) setState(() => _findingDevice = false);
    }
  }

  @override
  Widget build(BuildContext context) => SafeArea(
    child: Padding(
      padding: EdgeInsets.fromLTRB(
        20,
        18,
        20,
        20 + MediaQuery.of(context).viewInsets.bottom,
      ),
      child: SizedBox(
        height: MediaQuery.of(context).size.height * .68,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                const Expanded(
                  child: Text(
                    'Thêm vị trí',
                    style: TextStyle(fontSize: 21, fontWeight: FontWeight.w800),
                  ),
                ),
                IconButton(
                  onPressed: () => Navigator.pop(context),
                  icon: const Icon(Icons.close),
                ),
              ],
            ),
            const Text(
              'Vị trí chỉ được chia sẻ khi bạn chủ động chọn.',
              style: TextStyle(color: Color(0xff63758c)),
            ),
            const SizedBox(height: 16),
            OutlinedButton.icon(
              onPressed: _findingDevice ? null : _useCurrentLocation,
              icon: _findingDevice
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.my_location_outlined),
              label: Text(
                _findingDevice
                    ? 'Đang xác định vị trí...'
                    : 'Dùng vị trí hiện tại',
              ),
              style: OutlinedButton.styleFrom(
                minimumSize: const Size.fromHeight(50),
              ),
            ),
            const SizedBox(height: 14),
            TextField(
              controller: _query,
              onChanged: _search,
              decoration: InputDecoration(
                prefixIcon: const Icon(Icons.search),
                suffixIcon: _searching
                    ? const Padding(
                        padding: EdgeInsets.all(12),
                        child: SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        ),
                      )
                    : null,
                hintText: 'Tìm địa điểm, ví dụ Học viện Ngân hàng',
              ),
            ),
            if (_message != null)
              Padding(
                padding: const EdgeInsets.only(top: 10),
                child: Text(
                  _message!,
                  style: const TextStyle(color: Color(0xffb42318)),
                ),
              ),
            const SizedBox(height: 10),
            Expanded(
              child: _suggestions.isEmpty
                  ? const Center(
                      child: Text('Tìm theo tên hoặc dùng vị trí hiện tại.'),
                    )
                  : ListView.separated(
                      itemCount: _suggestions.length,
                      separatorBuilder: (_, _) => const Divider(height: 1),
                      itemBuilder: (context, index) {
                        final item = _suggestions[index];
                        return ListTile(
                          leading: const Icon(
                            Icons.location_on_outlined,
                            color: Color(0xff0866c6),
                          ),
                          title: Text('${item['name'] ?? 'Vị trí đã chọn'}'),
                          subtitle: Text(
                            '${item['address'] ?? ''}',
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                          onTap: () => Navigator.pop(context, item),
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
    ),
  );
}
