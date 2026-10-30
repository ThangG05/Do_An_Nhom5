import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../domain/repositories/feed_repository.dart';
import 'location_picker_sheet.dart';

class EnhancedPostDraft {
  const EnhancedPostDraft({
    required this.content,
    required this.files,
    required this.category,
    this.marketListing,
    this.roomListing,
    this.eventListing,
    this.studyListing,
    this.location,
  });

  final String content;
  final List<PlatformFile> files;
  final String category;
  final Map<String, dynamic>? marketListing;
  final Map<String, dynamic>? roomListing;
  final Map<String, dynamic>? eventListing;
  final Map<String, dynamic>? studyListing;
  final Map<String, dynamic>? location;
}

class EnhancedPostComposerSheet extends StatefulWidget {
  const EnhancedPostComposerSheet({
    super.key,
    required this.repository,
    required this.onSubmit,
    this.allowedCategories = const [
      'general',
      'market',
      'roommate',
      'event',
      'study',
    ],
    this.initialCategory = 'general',
    this.groupName,
  });
  final FeedRepository repository;
  final Future<void> Function(EnhancedPostDraft draft) onSubmit;
  final List<String> allowedCategories;
  final String initialCategory;
  final String? groupName;

  @override
  State<EnhancedPostComposerSheet> createState() =>
      _EnhancedPostComposerSheetState();
}

class _EnhancedPostComposerSheetState extends State<EnhancedPostComposerSheet> {
  final _content = TextEditingController();
  final _price = TextEditingController();
  final _condition = TextEditingController();
  final _rent = TextEditingController();
  final _area = TextEditingController();
  final _amenities = TextEditingController();
  final _eventDate = TextEditingController();
  final _eventTime = TextEditingController();
  final _organizer = TextEditingController();
  final _productName = TextEditingController();
  final _eventName = TextEditingController();
  final _subjectName = TextEditingController();
  final _files = <PlatformFile>[];
  String _category = 'general';
  Map<String, dynamic>? _location;
  bool _sending = false;

  @override
  void initState() {
    super.initState();
    _category = widget.initialCategory;
  }

  @override
  void dispose() {
    for (final controller in [
      _content,
      _price,
      _condition,
      _rent,
      _area,
      _amenities,
      _eventDate,
      _eventTime,
      _organizer,
      _productName,
      _eventName,
      _subjectName,
    ]) {
      controller.dispose();
    }
    super.dispose();
  }

  Future<void> _pickFiles() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.any,
      allowMultiple: true,
      withData: kIsWeb,
    );
    if (result == null || !mounted) return;
    final incoming = result.files
        .where(
          (file) => !_files.any(
            (current) => current.path == file.path && current.name == file.name,
          ),
        )
        .toList();
    if (_files.length + incoming.length > 10) {
      _showError('Mỗi bài chỉ được đính kèm tối đa 10 tệp.');
      return;
    }
    setState(() => _files.addAll(incoming));
  }

  void _showError(String message) {
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(message)));
  }

  Future<void> _pickLocation() async {
    final selected = await showModalBottomSheet<Map<String, dynamic>>(
      context: context,
      isScrollControlled: true,
      builder: (_) => LocationPickerSheet(repository: widget.repository),
    );
    if (selected != null && mounted) {
      setState(() => _location = selected);
    }
  }

  Map<String, dynamic>? _listing() {
    final locationName = _location?['name']?.toString() ?? '';
    if (_category == 'market') {
      return {
        'productName': _productName.text.trim(),
        'price': _price.text.trim(),
        'condition': _condition.text.trim(),
        'location': locationName,
        'status': 'active',
      };
    }
    if (_category == 'roommate') {
      return {
        'rentPerMonth': _rent.text.trim(),
        'area': _area.text.trim(),
        'amenities': _amenities.text
            .split(',')
            .map((value) => value.trim())
            .where((value) => value.isNotEmpty)
            .toList(),
        'location': locationName,
        'status': 'active',
      };
    }
    if (_category == 'event') {
      return {
        'eventName': _eventName.text.trim(),
        'eventDate': _eventDate.text.trim(),
        'eventTime': _eventTime.text.trim(),
        'location': locationName,
        'organizer': _organizer.text.trim(),
        'status': 'active',
      };
    }
    if (_category == 'study') return {'subjectName': _subjectName.text.trim()};
    return null;
  }

  String? _validationError() {
    final content = _content.text.trim();
    final location = _location?['name']?.toString().trim() ?? '';
    if (_category == 'general')
      return content.isEmpty && _files.isEmpty
          ? 'Hãy viết nội dung hoặc chọn ít nhất một tệp.'
          : null;
    if (_category == 'market') {
      if (_productName.text.trim().isEmpty)
        return 'Vui lòng nhập tên vật phẩm.';
      if (!RegExp(r'^[0-9]{1,15}$').hasMatch(_price.text.trim()))
        return 'Giá phải là số nguyên VNĐ không âm, tối đa 15 chữ số.';
    }
    if (_category == 'event') {
      if (_eventName.text.trim().isEmpty) return 'Vui lòng nhập tên sự kiện.';
      final date = DateTime.tryParse(_eventDate.text.trim());
      if (date == null ||
          _eventDate.text.trim() !=
              '${date.year.toString().padLeft(4, '0')}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}')
        return 'Vui lòng chọn ngày diễn ra hợp lệ.';
      if (!RegExp(
        r'^([01][0-9]|2[0-3]):[0-5][0-9]$',
      ).hasMatch(_eventTime.text.trim()))
        return 'Vui lòng chọn giờ bắt đầu hợp lệ.';
    }
    if (_category == 'study' && _subjectName.text.trim().isEmpty)
      return 'Vui lòng nhập tên môn học.';
    if (_category == 'roommate' &&
        _rent.text.trim().isNotEmpty &&
        !RegExp(r'^[0-9]{1,15}$').hasMatch(_rent.text.trim()))
      return 'Giá thuê phải là số nguyên VNĐ không âm.';
    if (['market', 'roommate', 'event'].contains(_category) && location.isEmpty)
      return 'Vui lòng chọn vị trí.';
    if (['event', 'roommate', 'study'].contains(_category) && content.isEmpty)
      return 'Vui lòng nhập nội dung mô tả.';
    return null;
  }

  Future<void> _submit() async {
    final validationError = _validationError();
    if (validationError != null) {
      _showError(validationError);
      return;
    }
    setState(() => _sending = true);
    try {
      final listing = _listing();
      await widget.onSubmit(
        EnhancedPostDraft(
          content: _content.text.trim(),
          files: _files,
          category: _category,
          marketListing: _category == 'market' ? listing : null,
          roomListing: _category == 'roommate' ? listing : null,
          eventListing: _category == 'event' ? listing : null,
          studyListing: _category == 'study' ? listing : null,
          location: _location,
        ),
      );
      if (mounted) Navigator.pop(context);
    } catch (error) {
      if (mounted)
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.toString())));
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  Widget _listingFields() {
    if (_category == 'market') {
      return Column(
        children: [
          TextField(
            controller: _productName,
            decoration: const InputDecoration(labelText: 'Tên vật phẩm *'),
          ),
          const SizedBox(height: 10),
          TextField(
            controller: _price,
            decoration: const InputDecoration(labelText: 'Giá bán / trao đổi'),
          ),
          const SizedBox(height: 10),
          TextField(
            controller: _condition,
            decoration: const InputDecoration(labelText: 'Tình trạng món đồ'),
          ),
        ],
      );
    }
    if (_category == 'roommate') {
      return Column(
        children: [
          TextField(
            controller: _rent,
            decoration: const InputDecoration(labelText: 'Giá thuê mỗi tháng'),
          ),
          const SizedBox(height: 10),
          TextField(
            controller: _area,
            decoration: const InputDecoration(labelText: 'Diện tích'),
          ),
          const SizedBox(height: 10),
          TextField(
            controller: _amenities,
            decoration: const InputDecoration(
              labelText: 'Tiện nghi (cách nhau bởi dấu phẩy)',
            ),
          ),
        ],
      );
    }
    if (_category == 'event') {
      return Column(
        children: [
          TextField(
            controller: _eventName,
            decoration: const InputDecoration(labelText: 'Tên sự kiện *'),
          ),
          const SizedBox(height: 10),
          TextField(
            controller: _eventDate,
            readOnly: true,
            onTap: _pickEventDate,
            decoration: const InputDecoration(
              labelText: 'Ngày diễn ra *',
              suffixIcon: Icon(Icons.calendar_today_outlined),
            ),
          ),
          const SizedBox(height: 10),
          TextField(
            controller: _eventTime,
            readOnly: true,
            onTap: _pickEventTime,
            decoration: const InputDecoration(
              labelText: 'Giờ bắt đầu *',
              suffixIcon: Icon(Icons.access_time),
            ),
          ),
          const SizedBox(height: 10),
          TextField(
            controller: _organizer,
            decoration: const InputDecoration(labelText: 'Đơn vị tổ chức'),
          ),
        ],
      );
    }
    if (_category == 'study')
      return TextField(
        controller: _subjectName,
        decoration: const InputDecoration(labelText: 'Tên môn học *'),
      );
    return const SizedBox.shrink();
  }

  Future<void> _pickEventDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: DateTime.now(),
      firstDate: DateTime(2000),
      lastDate: DateTime(2100),
    );
    if (picked != null)
      _eventDate.text =
          '${picked.year.toString().padLeft(4, '0')}-${picked.month.toString().padLeft(2, '0')}-${picked.day.toString().padLeft(2, '0')}';
  }

  Future<void> _pickEventTime() async {
    final picked = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.now(),
    );
    if (picked != null)
      _eventTime.text =
          '${picked.hour.toString().padLeft(2, '0')}:${picked.minute.toString().padLeft(2, '0')}';
  }

  static const _labels = <String, String>{
    'general': 'Bài viết cá nhân',
    'market': 'Pass đồ',
    'roommate': 'Ghép phòng / Tìm trọ',
    'event': 'Sự kiện',
    'study': 'Học tập',
  };

  @override
  Widget build(BuildContext context) => SafeArea(
    child: Padding(
      padding: EdgeInsets.fromLTRB(
        20,
        14,
        20,
        18 + MediaQuery.of(context).viewInsets.bottom,
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                width: 42,
                height: 4,
                decoration: BoxDecoration(
                  color: Colors.blueGrey.shade200,
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text(
              widget.groupName == null
                  ? 'Tạo bài viết'
                  : 'Đăng trong ${widget.groupName}',
              style: const TextStyle(
                fontSize: 21,
                fontWeight: FontWeight.w800,
                color: Color(0xff062f59),
              ),
            ),
            const SizedBox(height: 14),
            if (widget.groupName != null)
              const Padding(
                padding: EdgeInsets.only(bottom: 12),
                child: Text(
                  'Bài viết sẽ được quản trị viên duyệt trước khi hiển thị.',
                ),
              ),
            if (widget.allowedCategories.length > 1)
              DropdownButtonFormField<String>(
                initialValue: _category,
                decoration: const InputDecoration(labelText: 'Đăng ở đâu?'),
                items: widget.allowedCategories
                    .map(
                      (category) => DropdownMenuItem(
                        value: category,
                        child: Text(_labels[category] ?? category),
                      ),
                    )
                    .toList(),
                onChanged: _sending
                    ? null
                    : (value) => setState(() => _category = value ?? 'general'),
              ),
            if (widget.allowedCategories.length > 1) const SizedBox(height: 12),
            TextField(
              controller: _content,
              minLines: 4,
              maxLines: 8,
              autofocus: true,
              decoration: const InputDecoration(
                hintText: 'Bạn đang nghĩ gì?',
                alignLabelWithHint: true,
              ),
            ),
            const SizedBox(height: 12),
            _listingFields(),
            if (_category != 'general') const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: _sending ? null : _pickLocation,
              icon: const Icon(Icons.location_on_outlined),
              label: Text(
                _location == null ? 'Thêm vị trí' : '${_location!['name']}',
              ),
              style: OutlinedButton.styleFrom(
                minimumSize: const Size.fromHeight(48),
                alignment: Alignment.centerLeft,
              ),
            ),
            const SizedBox(height: 10),
            OutlinedButton.icon(
              onPressed: _sending ? null : _pickFiles,
              icon: const Icon(Icons.add_photo_alternate_outlined),
              label: const Text('Ảnh, video hoặc tệp'),
              style: OutlinedButton.styleFrom(
                minimumSize: const Size.fromHeight(48),
                alignment: Alignment.centerLeft,
              ),
            ),
            if (_files.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Wrap(
                  spacing: 6,
                  children: _files
                      .map(
                        (file) => InputChip(
                          label: Text(file.name),
                          onDeleted: _sending
                              ? null
                              : () => setState(() => _files.remove(file)),
                        ),
                      )
                      .toList(),
                ),
              ),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: _sending ? null : _submit,
              icon: _sending
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                        color: Colors.white,
                        strokeWidth: 2,
                      ),
                    )
                  : const Icon(Icons.send_rounded),
              label: Text(_sending ? 'Đang đăng...' : 'Đăng bài viết'),
              style: FilledButton.styleFrom(
                minimumSize: const Size.fromHeight(50),
              ),
            ),
          ],
        ),
      ),
    ),
  );
}
