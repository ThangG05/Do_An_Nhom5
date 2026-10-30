import 'dart:async';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../../../../core/widgets/app_page_bar.dart';
import '../../domain/entities/group_upload_file.dart';
import '../../domain/repositories/group_repository.dart';

const studyDocumentTypes = <String, String>{
  'EXAM': 'Đề thi / Kiểm tra',
  'EXERCISE': 'Bài tập / Thực hành',
  'LECTURE': 'Giáo trình / Bài giảng',
  'REVIEW': 'Đề cương / Ôn tập',
  'OTHER': 'Tài liệu khác',
};
const studyAssessmentTypes = <String, String>{
  'MIDTERM': 'Giữa kỳ',
  'FINAL': 'Cuối kỳ',
};

bool allowsStudyAssessment(String? type) =>
    type == 'EXAM' || type == 'EXERCISE' || type == 'REVIEW';

class StudyDocumentSharePage extends StatefulWidget {
  const StudyDocumentSharePage({
    super.key,
    required this.groupId,
    required this.repository,
    this.isAdmin = false,
  });

  final String groupId;
  final GroupRepository repository;
  final bool isAdmin;

  @override
  State<StudyDocumentSharePage> createState() => _StudyDocumentSharePageState();
}

class _StudyDocumentSharePageState extends State<StudyDocumentSharePage> {
  final _title = TextEditingController();
  final _description = TextEditingController();
  Map<String, dynamic>? _major;
  Map<String, dynamic>? _subject;
  String? _documentType;
  String? _assessmentType;
  final _files = <PlatformFile>[];
  String? _error;
  bool _submitting = false;

  @override
  void dispose() {
    _title.dispose();
    _description.dispose();
    super.dispose();
  }

  Future<void> _chooseMajor() async {
    final selected = await showModalBottomSheet<Map<String, dynamic>>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (_) => StudyCatalogPickerSheet(
        title: 'Chọn ngành học',
        search: (_) => widget.repository.getStudyMajors(),
      ),
    );
    if (!mounted || selected == null) return;
    setState(() {
      if (_major?['id'] != selected['id']) _subject = null;
      _major = selected;
      _error = null;
    });
  }

  Future<void> _chooseSubject() async {
    final majorId = _major?['id']?.toString();
    if (majorId == null) return;
    final selected = await showModalBottomSheet<Map<String, dynamic>>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (_) => StudyCatalogPickerSheet(
        title: 'Chọn môn học',
        search: (query) =>
            widget.repository.getStudySubjects(query, majorId: majorId),
      ),
    );
    if (!mounted || selected == null) return;
    setState(() {
      _subject = selected;
      _error = null;
    });
  }

  Future<void> _pickFiles() async {
    try {
      final picked = await FilePicker.platform.pickFiles(
        type: FileType.any,
        allowMultiple: true,
        withData: kIsWeb,
      );
      if (!mounted || picked == null || picked.files.isEmpty) return;
      final next = [..._files, ...picked.files];
      if (next.length > 10) {
        setState(() => _error = 'Mỗi bộ tài liệu có tối đa 10 tệp.');
        return;
      }
      setState(() {
        _files.addAll(picked.files);
        _error = null;
        if (_title.text.trim().isEmpty) {
          final suggestion = picked.files.first.name
              .replaceFirst(RegExp(r'\.[^.]+$'), '')
              .replaceAll(RegExp(r'[_-]+'), ' ')
              .replaceAll(RegExp(r'\s+'), ' ')
              .trim();
          if (suggestion.length >= 5)
            _title.text = suggestion.substring(
              0,
              suggestion.length.clamp(0, 120),
            );
        }
      });
    } catch (_) {
      if (mounted)
        setState(() => _error = 'Chưa chọn được tệp. Vui lòng thử lại.');
    }
  }

  Future<void> _submit() async {
    if (_submitting) return;
    final bytes = _files.fold<int>(0, (sum, file) => sum + file.size);
    String? error;
    if (_major == null)
      error = 'Vui lòng chọn ngành học.';
    else if (_subject == null)
      error = 'Vui lòng chọn môn học thuộc ngành đã chọn.';
    else if (_documentType == null)
      error = 'Vui lòng chọn loại tài liệu.';
    else if (_files.isEmpty)
      error = 'Vui lòng đính kèm ít nhất một tệp.';
    else if (bytes > 50 * 1024 * 1024)
      error = 'Tổng dung lượng vượt 50 MB.';
    else if (_title.text.trim().length < 5 || _title.text.trim().length > 120) {
      error = 'Tiêu đề cần từ 5 đến 120 ký tự.';
    }
    if (error != null) {
      setState(() => _error = error);
      return;
    }
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      await widget.repository.shareStudyDocument(
        widget.groupId,
        '${_major!['id']}',
        '${_subject!['id']}',
        _documentType!,
        allowsStudyAssessment(_documentType) ? _assessmentType : null,
        _title.text.trim(),
        _description.text.trim(),
        _files
            .map(
              (file) => GroupUploadFile(
                name: file.name,
                size: file.size,
                path: file.path,
                bytes: file.bytes,
              ),
            )
            .toList(),
      );
      if (mounted) Navigator.of(context).pop(true);
    } catch (error) {
      if (mounted) setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final assessmentVisible = allowsStudyAssessment(_documentType);
    final bytes = _files.fold<int>(0, (sum, file) => sum + file.size);
    return Scaffold(
      appBar: const AppPageBar(title: 'Chia sẻ tài liệu'),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 620),
            child: ListView(
              padding: const EdgeInsets.fromLTRB(18, 18, 18, 24),
              children: [
                const Text(
                  'Chia sẻ kiến thức với thành viên nhóm',
                  style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 6),
                Text(
                  widget.isAdmin
                      ? 'Tài liệu của admin sẽ hiển thị ngay trong kho.'
                      : 'Tài liệu sẽ được admin xem xét trước khi hiển thị.',
                  style: const TextStyle(color: Colors.blueGrey),
                ),
                const SizedBox(height: 24),
                _label('Ngành học *'),
                _selection(
                  _major?['name']?.toString() ?? 'Chọn ngành học',
                  _chooseMajor,
                  selected: _major != null,
                ),
                const SizedBox(height: 16),
                _label('Môn học *'),
                _selection(
                  _subject == null
                      ? 'Chọn môn học theo ngành'
                      : '${_subject!['code'] ?? ''} · ${_subject!['name']}',
                  _major == null ? null : _chooseSubject,
                  selected: _subject != null,
                ),
                const SizedBox(height: 20),
                _label('Loại tài liệu *'),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: studyDocumentTypes.entries.map((entry) {
                    final selected = _documentType == entry.key;
                    return ChoiceChip(
                      label: Text(entry.value),
                      selected: selected,
                      onSelected: (_) => setState(() {
                        _documentType = entry.key;
                        if (!allowsStudyAssessment(entry.key))
                          _assessmentType = null;
                        _error = null;
                      }),
                    );
                  }).toList(),
                ),
                AnimatedSize(
                  duration: const Duration(milliseconds: 220),
                  curve: Curves.easeInOut,
                  child: assessmentVisible
                      ? Padding(
                          padding: const EdgeInsets.only(top: 20),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              _label('Kỳ đánh giá (tùy chọn)'),
                              Wrap(
                                spacing: 8,
                                children: [
                                  ChoiceChip(
                                    label: const Text(
                                      'Không áp dụng / Không rõ',
                                    ),
                                    selected: _assessmentType == null,
                                    onSelected: (_) =>
                                        setState(() => _assessmentType = null),
                                  ),
                                  ...studyAssessmentTypes.entries.map(
                                    (entry) => ChoiceChip(
                                      label: Text(entry.value),
                                      selected: _assessmentType == entry.key,
                                      onSelected: (_) => setState(
                                        () => _assessmentType = entry.key,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        )
                      : const SizedBox.shrink(),
                ),
                const SizedBox(height: 20),
                _label('Tệp tài liệu *'),
                OutlinedButton.icon(
                  onPressed: _submitting ? null : _pickFiles,
                  icon: const Icon(CupertinoIcons.paperclip),
                  label: Text(_files.isEmpty ? 'Chọn tệp' : 'Thêm tệp'),
                ),
                Text(
                  '${_files.length}/10 tệp · ${(bytes / (1024 * 1024)).toStringAsFixed(1)} / 50 MB',
                  style: const TextStyle(color: Colors.blueGrey, fontSize: 12),
                ),
                ..._files.asMap().entries.map(
                  (entry) => ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: const Icon(CupertinoIcons.doc),
                    title: Text(
                      entry.value.name,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    subtitle: Text('${(entry.value.size / 1024).ceil()} KB'),
                    trailing: IconButton(
                      tooltip: 'Gỡ tệp',
                      onPressed: _submitting
                          ? null
                          : () => setState(() => _files.removeAt(entry.key)),
                      icon: const Icon(CupertinoIcons.xmark_circle),
                    ),
                  ),
                ),
                const SizedBox(height: 18),
                _label('Tiêu đề tài liệu *'),
                TextField(
                  controller: _title,
                  maxLength: 120,
                  decoration: const InputDecoration(
                    hintText: 'Ví dụ: Bài tập SQL chương 1–3',
                  ),
                ),
                _label('Mô tả (tùy chọn)'),
                TextField(
                  controller: _description,
                  maxLength: 500,
                  minLines: 3,
                  maxLines: 5,
                  decoration: const InputDecoration(
                    hintText:
                        'Ví dụ: Tài liệu gồm bài tập SQL chương 1–3, dùng để ôn giữa kỳ.',
                  ),
                ),
                if (_error != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 6),
                    child: Text(
                      _error!,
                      style: const TextStyle(color: Colors.red),
                    ),
                  ),
                const SizedBox(height: 12),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(14),
                    child: Text(
                      'Xem trước: ${_subject?['name'] ?? 'Chưa chọn môn'} · '
                      '${studyDocumentTypes[_documentType] ?? 'Chưa chọn loại'}'
                      '${_assessmentType == null ? '' : ' · ${studyAssessmentTypes[_assessmentType]}'}',
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
      bottomNavigationBar: SafeArea(
        top: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(18, 10, 18, 12),
          child: FilledButton(
            onPressed: _submitting ? null : _submit,
            child: Padding(
              padding: const EdgeInsets.symmetric(vertical: 13),
              child: Text(
                _submitting
                    ? 'Đang gửi…'
                    : widget.isAdmin
                    ? 'Chia sẻ tài liệu'
                    : 'Gửi tài liệu để duyệt',
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _label(String value) => Padding(
    padding: const EdgeInsets.only(bottom: 8),
    child: Text(value, style: const TextStyle(fontWeight: FontWeight.w700)),
  );

  Widget _selection(
    String label,
    VoidCallback? onTap, {
    bool selected = false,
  }) => OutlinedButton(
    onPressed: onTap,
    style: OutlinedButton.styleFrom(
      minimumSize: const Size.fromHeight(52),
      alignment: Alignment.centerLeft,
    ),
    child: Row(
      children: [
        Expanded(
          child: Text(
            label,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(color: selected ? null : Colors.blueGrey),
          ),
        ),
        const Icon(CupertinoIcons.chevron_down, size: 16),
      ],
    ),
  );
}

class StudyCatalogPickerSheet extends StatefulWidget {
  const StudyCatalogPickerSheet({
    super.key,
    required this.title,
    required this.search,
  });
  final String title;
  final Future<List<Map<String, dynamic>>> Function(String) search;

  @override
  State<StudyCatalogPickerSheet> createState() => _CatalogPickerSheetState();
}

class _CatalogPickerSheetState extends State<StudyCatalogPickerSheet> {
  final _query = TextEditingController();
  Timer? _debounce;
  List<Map<String, dynamic>> _items = [];
  bool _loading = true;
  int _request = 0;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final request = ++_request;
    setState(() => _loading = true);
    try {
      final rows = await widget.search(_query.text.trim());
      if (mounted && request == _request) setState(() => _items = rows);
    } catch (_) {
      if (mounted && request == _request) setState(() => _items = []);
    } finally {
      if (mounted && request == _request) setState(() => _loading = false);
    }
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _query.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => FractionallySizedBox(
    heightFactor: .82,
    child: Padding(
      padding: EdgeInsets.fromLTRB(
        18,
        20,
        18,
        MediaQuery.viewInsetsOf(context).bottom + 12,
      ),
      child: Column(
        children: [
          Text(
            widget.title,
            style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 14),
          TextField(
            controller: _query,
            autofocus: true,
            decoration: const InputDecoration(
              prefixIcon: Icon(CupertinoIcons.search),
              hintText: 'Tìm theo tên hoặc mã',
            ),
            onChanged: (_) {
              _debounce?.cancel();
              _debounce = Timer(const Duration(milliseconds: 220), _load);
            },
          ),
          const SizedBox(height: 10),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _items.isEmpty
                ? const Center(child: Text('Không tìm thấy trong danh mục.'))
                : ListView.builder(
                    itemCount: _items.length,
                    itemBuilder: (context, index) {
                      final item = _items[index];
                      final code = item['code']?.toString();
                      return ListTile(
                        title: Text('${item['name'] ?? ''}'),
                        subtitle: code == null || code.isEmpty
                            ? null
                            : Text(code),
                        onTap: () => Navigator.of(context).pop(item),
                      );
                    },
                  ),
          ),
        ],
      ),
    ),
  );
}
