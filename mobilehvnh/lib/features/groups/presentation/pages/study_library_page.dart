import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../../core/widgets/app_page_bar.dart';
import '../../../../core/widgets/app_state_view.dart';
import '../../domain/repositories/group_repository.dart';
import 'study_document_share_page.dart';

class StudyLibraryPage extends StatefulWidget {
  const StudyLibraryPage({
    super.key,
    required this.groupId,
    required this.repository,
    this.isAdmin = false,
  });

  final String groupId;
  final GroupRepository repository;
  final bool isAdmin;

  @override
  State<StudyLibraryPage> createState() => _StudyLibraryPageState();
}

class _StudyLibraryPageState extends State<StudyLibraryPage> {
  final _search = TextEditingController();
  Map<String, dynamic>? _filterSubject;
  String? _filterType;
  String? _filterAssessment;
  List<Map<String, dynamic>> _items = [];
  Map<String, Map<String, dynamic>> _aiAssessments = {};
  String _view = 'approved';
  int _page = 0;
  bool _loading = true;
  bool _busy = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      _items = _view == 'subjects'
          ? await widget.repository.getAdminStudySubjects(
              widget.groupId,
              _search.text.trim(),
              _page * 10,
            )
          : _view == 'reports'
          ? await widget.repository.getStudyDocumentReports(widget.groupId)
          : await widget.repository.getStudyDocuments(
              widget.groupId,
              query: _search.text.trim(),
              subjectId: _view == 'approved'
                  ? (_filterSubject?['id']?.toString())
                  : null,
              documentType: _view == 'approved' ? _filterType : null,
              assessmentType: _view == 'approved' ? _filterAssessment : null,
              offset: _page * (_view == 'approved' ? 6 : 5),
              mine: _view == 'mine',
              pending: _view == 'pending',
            );
      if (_view == 'pending' && _items.isNotEmpty) {
        try {
          final results = await widget.repository.getStudyAIAssessments(
            widget.groupId,
            _items.map((item) => '${item['id']}').toList(),
          );
          _aiAssessments = {
            for (final item in results) '${item['document_id']}': item,
          };
        } catch (_) {
          _aiAssessments = {};
        }
      } else {
        _aiAssessments = {};
      }
      _error = null;
    } catch (error) {
      _error = error.toString();
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _select(String view) {
    if (_view == view) return;
    setState(() {
      _view = view;
      _page = 0;
    });
    _load();
  }

  Future<String?> _ask(String title, {int minimum = 3}) async {
    final controller = TextEditingController();
    final result = await showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(title),
        content: TextField(
          controller: controller,
          minLines: 2,
          maxLines: 4,
          autofocus: true,
          decoration: const InputDecoration(hintText: 'Ghi rõ lý do'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Hủy'),
          ),
          FilledButton(
            onPressed: () =>
                Navigator.pop(dialogContext, controller.text.trim()),
            child: const Text('Xác nhận'),
          ),
        ],
      ),
    );
    controller.dispose();
    if (result == null) return null;
    if (result.length >= minimum) return result;
    if (mounted)
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Lý do cần ít nhất $minimum ký tự.')),
      );
    return null;
  }

  Future<bool> _act(Future<void> Function() operation) async {
    if (_busy) return false;
    setState(() => _busy = true);
    try {
      await operation();
      await _load();
      return true;
    } catch (error) {
      if (mounted)
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.toString())));
      return false;
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _openFile(
    Map<String, dynamic> document,
    Map file, {
    bool preview = false,
  }) async {
    try {
      final extension = '${file['extension'] ?? ''}'.toLowerCase().replaceFirst(
        '.',
        '',
      );
      if (preview && {'docx', 'xlsx'}.contains(extension)) {
        final data = await widget.repository.getStudyOfficePreview(
          widget.groupId,
          '${document['id']}',
          '${file['id']}',
        );
        if (!mounted) return;
        final lines = <String>[];
        if (data['kind'] == 'word') {
          lines.addAll(
            ((data['paragraphs'] as List?) ?? const []).map(
              (value) => '$value',
            ),
          );
          for (final table in (data['tables'] as List?) ?? const []) {
            for (final row in (table as List)) {
              lines.add((row as List).join('  |  '));
            }
          }
        } else if (data['kind'] == 'excel') {
          for (final sheet in (data['sheets'] as List?) ?? const []) {
            lines.add('Trang tính: ${(sheet as Map)['name']}');
            for (final row in (sheet['rows'] as List?) ?? const []) {
              lines.add((row as List).join('  |  '));
            }
          }
        }
        await showDialog<void>(
          context: context,
          builder: (context) => AlertDialog(
            title: Text('${file['original_name'] ?? 'Xem trước'}'),
            content: SizedBox(
              width: 650,
              height: 500,
              child: ListView(
                children: lines
                    .map(
                      (line) => Padding(
                        padding: const EdgeInsets.only(bottom: 7),
                        child: SelectableText(line),
                      ),
                    )
                    .toList(),
              ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Đóng'),
              ),
            ],
          ),
        );
        return;
      }
      final link = await widget.repository.getStudyFileLink(
        widget.groupId,
        '${document['id']}',
        '${file['id']}',
        preview: preview,
      );
      final url = Uri.tryParse('${link['url'] ?? ''}');
      if (url == null ||
          !await launchUrl(url, mode: LaunchMode.externalApplication))
        throw Exception('Không thể mở tệp.');
    } catch (error) {
      if (mounted)
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.toString())));
    }
  }

  Future<void> _downloadBundle(Map<String, dynamic> document) async {
    try {
      final bytes = await widget.repository.downloadStudyBundle(
        widget.groupId,
        '${document['id']}',
      );
      await FilePicker.platform.saveFile(
        dialogTitle: 'Lưu bộ tài liệu',
        fileName: 'tai-lieu-${document['id']}.zip',
        type: FileType.custom,
        allowedExtensions: const ['zip'],
        bytes: bytes,
      );
    } catch (error) {
      if (mounted)
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.toString())));
    }
  }

  Future<void> _upload() async {
    final shared = await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (_) => StudyDocumentSharePage(
          groupId: widget.groupId,
          repository: widget.repository,
          isAdmin: widget.isAdmin,
        ),
      ),
    );
    if (shared == true && mounted) {
      await _load();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            widget.isAdmin
                ? 'Tài liệu đã được chia sẻ trong kho.'
                : 'Tài liệu đã được gửi và đang chờ admin duyệt.',
          ),
        ),
      );
    }
  }

  Future<void> _chooseFilterSubject() async {
    final selected = await showModalBottomSheet<Map<String, dynamic>>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (_) => StudyCatalogPickerSheet(
        title: 'Lọc theo môn học',
        search: (query) => widget.repository.getStudySubjects(query),
      ),
    );
    if (!mounted || selected == null) return;
    setState(() {
      _filterSubject = selected;
      _page = 0;
    });
    _load();
  }

  Future<void> _editSubject([Map<String, dynamic>? subject]) async {
    final code = TextEditingController(text: '${subject?['code'] ?? ''}');
    final name = TextEditingController(text: '${subject?['name'] ?? ''}');
    final source = TextEditingController(
      text: '${subject?['source_note'] ?? ''}',
    );
    var category = '${subject?['category'] ?? 'GENERAL'}';
    var active = subject?['is_active'] != false;
    final submitted = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (dialogContext, setDialogState) => AlertDialog(
          title: Text(subject == null ? 'Thêm môn học' : 'Sửa môn học'),
          content: SizedBox(
            width: 420,
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  TextField(
                    controller: code,
                    decoration: const InputDecoration(labelText: 'Mã môn'),
                  ),
                  TextField(
                    controller: name,
                    decoration: const InputDecoration(labelText: 'Tên môn *'),
                  ),
                  TextField(
                    controller: source,
                    minLines: 2,
                    maxLines: 3,
                    decoration: const InputDecoration(
                      labelText: 'Nguồn xác minh *',
                    ),
                  ),
                  DropdownButtonFormField<String>(
                    initialValue: category,
                    items: const [
                      DropdownMenuItem(
                        value: 'GENERAL',
                        child: Text('Đại cương'),
                      ),
                      DropdownMenuItem(
                        value: 'SPECIALIZED',
                        child: Text('Chuyên ngành'),
                      ),
                    ],
                    onChanged: (value) =>
                        setDialogState(() => category = value ?? category),
                  ),
                  SwitchListTile(
                    title: const Text('Đang sử dụng'),
                    value: active,
                    onChanged: (value) => setDialogState(() => active = value),
                  ),
                ],
              ),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: const Text('Hủy'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(dialogContext, true),
              child: const Text('Lưu'),
            ),
          ],
        ),
      ),
    );
    if (submitted == true) {
      if (name.text.trim().length < 2 || source.text.trim().length < 5) {
        if (mounted)
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Tên môn hoặc nguồn xác minh chưa hợp lệ.'),
            ),
          );
      } else {
        await _act(
          () => widget.repository.saveStudySubject(widget.groupId, {
            if (subject != null) 'id': subject['id'],
            'code': code.text.trim().isEmpty ? null : code.text.trim(),
            'name': name.text.trim(),
            'source_note': source.text.trim(),
            'category': category,
            'is_active': active,
            'needs_review': subject?['needs_review'] == true,
            'major_ids': category == 'GENERAL'
                ? <String>[]
                : subject?['major_ids'],
          }),
        );
      }
    }
    code.dispose();
    name.dispose();
    source.dispose();
  }

  Widget _subject(Map<String, dynamic> subject) => Card(
    child: ListTile(
      title: Text(
        '${subject['code'] ?? ''} · ${subject['name'] ?? ''}',
        style: const TextStyle(fontWeight: FontWeight.w700),
      ),
      subtitle: Text(
        '${subject['category'] == 'GENERAL' ? 'Đại cương' : 'Chuyên ngành'} · ${subject['source_note'] ?? ''}${subject['is_active'] == false ? ' · Đã ẩn' : ''}',
      ),
      trailing: const Icon(Icons.edit_outlined),
      onTap: () => _editSubject(subject),
    ),
  );

  Widget _document(Map<String, dynamic> document) {
    final files = (document['files'] as List?) ?? const [];
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    '${document['title'] ?? ''}',
                    style: const TextStyle(
                      fontWeight: FontWeight.w800,
                      fontSize: 16,
                    ),
                  ),
                ),
                if (document['status'] != 'APPROVED')
                  Chip(label: Text('${document['status']}')),
              ],
            ),
            Text(
              '${document['subject_code'] ?? ''} · ${document['subject_name'] ?? ''}',
            ),
            Padding(
              padding: const EdgeInsets.only(top: 7),
              child: Wrap(
                spacing: 7,
                runSpacing: 5,
                children: [
                  Chip(
                    label: Text(
                      studyDocumentTypes[document['document_type']] ??
                          'Chưa phân loại',
                    ),
                  ),
                  if (studyAssessmentTypes[document['assessment_type']] != null)
                    Chip(
                      label: Text(
                        studyAssessmentTypes[document['assessment_type']]!,
                      ),
                    ),
                ],
              ),
            ),
            Text(
              'Chia sẻ bởi ${document['uploader_name'] ?? ''}',
              style: const TextStyle(fontSize: 12, color: Colors.blueGrey),
            ),
            if ('${document['description'] ?? ''}'.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text('${document['description']}'),
              ),
            if (_view == 'pending') _aiAdvice(document),
            const SizedBox(height: 8),
            ...files.whereType<Map>().map(
              (file) => ListTile(
                contentPadding: EdgeInsets.zero,
                dense: true,
                leading: const Icon(Icons.description_outlined),
                title: Text(
                  '${file['original_name'] ?? ''}',
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                trailing: IconButton(
                  tooltip: 'Tải tệp',
                  onPressed: () => _openFile(document, file),
                  icon: const Icon(Icons.download_outlined),
                ),
                onTap: () => _openFile(document, file, preview: true),
              ),
            ),
            Wrap(
              spacing: 8,
              children: [
                if (_view == 'approved' || _view == 'mine')
                  TextButton.icon(
                    onPressed: () => _downloadBundle(document),
                    icon: const Icon(Icons.folder_zip_outlined),
                    label: const Text('Tải cả bộ'),
                  ),
                if (_view == 'mine')
                  TextButton.icon(
                    onPressed: _busy
                        ? null
                        : () async {
                            final confirmed = await showDialog<bool>(
                              context: context,
                              builder: (context) => AlertDialog(
                                title: const Text('Xóa bộ tài liệu?'),
                                content: const Text(
                                  'Các tệp trong bộ tài liệu này sẽ không còn hiển thị.',
                                ),
                                actions: [
                                  TextButton(
                                    onPressed: () =>
                                        Navigator.pop(context, false),
                                    child: const Text('Hủy'),
                                  ),
                                  FilledButton(
                                    onPressed: () =>
                                        Navigator.pop(context, true),
                                    child: const Text('Xóa'),
                                  ),
                                ],
                              ),
                            );
                            if (confirmed == true)
                              _act(
                                () => widget.repository.deleteStudyDocument(
                                  widget.groupId,
                                  '${document['id']}',
                                ),
                              );
                          },
                    icon: const Icon(Icons.delete_outline),
                    label: const Text('Xóa'),
                  ),
                if (_view == 'approved')
                  TextButton.icon(
                    onPressed: _busy
                        ? null
                        : () async {
                            final reason = await _ask(
                              'Tố cáo tài liệu',
                              minimum: 5,
                            );
                            if (reason != null)
                              _act(
                                () => widget.repository.reportStudyDocument(
                                  widget.groupId,
                                  '${document['id']}',
                                  reason,
                                ),
                              );
                          },
                    icon: const Icon(Icons.flag_outlined),
                    label: const Text('Tố cáo'),
                  ),
                if (_view == 'pending') ...[
                  FilledButton(
                    onPressed: _busy
                        ? null
                        : () => _act(
                            () => widget.repository.moderateStudyDocument(
                              widget.groupId,
                              '${document['id']}',
                              true,
                              '',
                            ),
                          ),
                    child: const Text('Phê duyệt'),
                  ),
                  OutlinedButton(
                    onPressed: _busy
                        ? null
                        : () async {
                            final reason = await _ask('Lý do từ chối');
                            if (reason != null)
                              _act(
                                () => widget.repository.moderateStudyDocument(
                                  widget.groupId,
                                  '${document['id']}',
                                  false,
                                  reason,
                                ),
                              );
                          },
                    child: const Text('Từ chối'),
                  ),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _aiAdvice(Map<String, dynamic> document) {
    final assessment = _aiAssessments['${document['id']}'];
    final recommendation = assessment?['recommendation'];
    final status = assessment?['status'];
    final label = status == 'COMPLETED'
        ? recommendation == 'APPROVE'
              ? 'Gợi ý duyệt'
              : recommendation == 'REJECT'
              ? 'Gợi ý từ chối'
              : 'Cần xem kỹ'
        : status == 'FAILED' || assessment == null
        ? 'Cần xem thủ công'
        : 'Đang phân tích';
    final files = (assessment?['file_results'] as List?) ?? const [];
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(top: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerLow,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Theme.of(context).dividerColor),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Expanded(
                child: Text(
                  'AI đọc trước · chỉ để tham khảo',
                  style: TextStyle(fontWeight: FontWeight.w800),
                ),
              ),
              Text(label, style: const TextStyle(fontWeight: FontWeight.w700)),
            ],
          ),
          if ('${assessment?['reason'] ?? ''}'.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text('${assessment!['reason']}'),
          ],
          for (final file in files.whereType<Map>()) ...[
            const Divider(height: 20),
            Text(
              '${file['file_name'] ?? ''} · ${file['recommendation'] == 'APPROVE'
                  ? 'Phù hợp'
                  : file['recommendation'] == 'REJECT'
                  ? 'Có dấu hiệu sai môn/spam'
                  : 'Cần xem kỹ'}',
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 4),
            Text('${file['reason'] ?? ''}'),
            if ('${file['evidence_quote'] ?? ''}'.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 6),
                child: Text(
                  '${file['evidence_location'] ?? ''}: “${file['evidence_quote']}”',
                  style: TextStyle(
                    color: Theme.of(context).colorScheme.primary,
                  ),
                ),
              ),
            if (file['sampling_limited'] == true)
              const Text(
                'Chỉ đọc được một phần; cần kiểm tra file gốc.',
                style: TextStyle(fontSize: 12),
              ),
          ],
          const SizedBox(height: 8),
          const Text(
            'Admin vẫn là người quyết định cuối cùng.',
            style: TextStyle(fontSize: 12),
          ),
        ],
      ),
    );
  }

  Widget _report(Map<String, dynamic> report) => Card(
    child: Padding(
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '${report['title'] ?? ''}',
            style: const TextStyle(fontWeight: FontWeight.w800),
          ),
          Text(
            '${report['reporter_name'] ?? ''} báo cáo: ${report['reason'] ?? ''}',
          ),
          Wrap(
            spacing: 8,
            children: [
              OutlinedButton(
                onPressed: _busy
                    ? null
                    : () async {
                        final note = await _ask('Lý do bác bỏ báo cáo');
                        if (note != null)
                          _act(
                            () => widget.repository.decideStudyDocumentReport(
                              widget.groupId,
                              '${report['id']}',
                              false,
                              note,
                            ),
                          );
                      },
                child: const Text('Bác bỏ'),
              ),
              FilledButton(
                onPressed: _busy
                    ? null
                    : () async {
                        final note = await _ask('Lý do xóa tài liệu');
                        if (note != null)
                          _act(
                            () => widget.repository.decideStudyDocumentReport(
                              widget.groupId,
                              '${report['id']}',
                              true,
                              note,
                            ),
                          );
                      },
                child: const Text('Xóa tài liệu'),
              ),
            ],
          ),
        ],
      ),
    ),
  );

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: const AppPageBar(title: 'Kho tài liệu Học tập'),
    floatingActionButton: _view == 'subjects' && widget.isAdmin
        ? FloatingActionButton.extended(
            onPressed: _busy ? null : () => _editSubject(),
            icon: const Icon(Icons.add),
            label: const Text('Thêm môn'),
          )
        : _view == 'approved' || _view == 'mine'
        ? FloatingActionButton.extended(
            onPressed: _busy ? null : _upload,
            icon: const Icon(Icons.add),
            label: const Text('Chia sẻ'),
          )
        : null,
    body: Column(
      children: [
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              ChoiceChip(
                label: const Text('Đã duyệt'),
                selected: _view == 'approved',
                onSelected: (_) => _select('approved'),
              ),
              const SizedBox(width: 8),
              ChoiceChip(
                label: const Text('Tài liệu của tôi'),
                selected: _view == 'mine',
                onSelected: (_) => _select('mine'),
              ),
              if (widget.isAdmin) ...[
                const SizedBox(width: 8),
                ChoiceChip(
                  label: const Text('Chờ duyệt'),
                  selected: _view == 'pending',
                  onSelected: (_) => _select('pending'),
                ),
                const SizedBox(width: 8),
                ChoiceChip(
                  label: const Text('Tố cáo'),
                  selected: _view == 'reports',
                  onSelected: (_) => _select('reports'),
                ),
                const SizedBox(width: 8),
                ChoiceChip(
                  label: const Text('Môn học'),
                  selected: _view == 'subjects',
                  onSelected: (_) => _select('subjects'),
                ),
              ],
            ],
          ),
        ),
        if (_view == 'approved' || _view == 'subjects')
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: TextField(
              controller: _search,
              onSubmitted: (_) {
                _page = 0;
                _load();
              },
              decoration: InputDecoration(
                hintText: 'Tìm tài liệu theo tên hoặc môn học',
                suffixIcon: IconButton(
                  onPressed: () {
                    _page = 0;
                    _load();
                  },
                  icon: const Icon(Icons.search),
                ),
              ),
            ),
          ),
        if (_view == 'approved')
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.fromLTRB(12, 7, 12, 9),
            child: Row(
              children: [
                ActionChip(
                  label: Text(_filterSubject?['name']?.toString() ?? 'Môn học'),
                  onPressed: _chooseFilterSubject,
                ),
                const SizedBox(width: 8),
                if (_filterSubject != null)
                  IconButton(
                    tooltip: 'Bỏ lọc môn học',
                    onPressed: () {
                      setState(() {
                        _filterSubject = null;
                        _page = 0;
                      });
                      _load();
                    },
                    icon: const Icon(Icons.close, size: 18),
                  ),
                ...studyDocumentTypes.entries.map(
                  (entry) => Padding(
                    padding: const EdgeInsets.only(right: 7),
                    child: ChoiceChip(
                      label: Text(entry.value),
                      selected: _filterType == entry.key,
                      onSelected: (_) {
                        setState(() {
                          _filterType = _filterType == entry.key
                              ? null
                              : entry.key;
                          _page = 0;
                        });
                        _load();
                      },
                    ),
                  ),
                ),
                for (final entry in studyAssessmentTypes.entries)
                  Padding(
                    padding: const EdgeInsets.only(right: 7),
                    child: ChoiceChip(
                      label: Text(entry.value),
                      selected: _filterAssessment == entry.key,
                      onSelected: (_) {
                        setState(() {
                          _filterAssessment = _filterAssessment == entry.key
                              ? null
                              : entry.key;
                          _page = 0;
                        });
                        _load();
                      },
                    ),
                  ),
                TextButton(
                  onPressed: () {
                    setState(() {
                      _filterSubject = null;
                      _filterType = null;
                      _filterAssessment = null;
                      _page = 0;
                    });
                    _load();
                  },
                  child: const Text('Đặt lại'),
                ),
              ],
            ),
          ),
        Expanded(
          child: _loading
              ? const AppLoadingList(count: 3)
              : _error != null
              ? AppStateView(
                  icon: Icons.wifi_off_rounded,
                  title: 'Chưa tải được kho tài liệu',
                  message: _error!,
                  actionLabel: 'Thử lại',
                  onAction: _load,
                )
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView(
                    padding: const EdgeInsets.fromLTRB(12, 12, 12, 88),
                    children: [
                      if (_items.isEmpty)
                        const AppStateView(
                          icon: Icons.folder_open_outlined,
                          title: 'Chưa có tài liệu',
                          message: 'Nội dung của mục này sẽ xuất hiện tại đây.',
                        ),
                      ..._items.map(
                        (item) => _view == 'reports'
                            ? _report(item)
                            : _view == 'subjects'
                            ? _subject(item)
                            : _document(item),
                      ),
                      if (_view != 'reports')
                        Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            TextButton(
                              onPressed: _page == 0
                                  ? null
                                  : () {
                                      setState(() => _page--);
                                      _load();
                                    },
                              child: const Text('Trước'),
                            ),
                            Text('Trang ${_page + 1}'),
                            TextButton(
                              onPressed:
                                  _items.length <
                                      (_view == 'subjects'
                                          ? 10
                                          : _view == 'approved'
                                          ? 6
                                          : 5)
                                  ? null
                                  : () {
                                      setState(() => _page++);
                                      _load();
                                    },
                              child: const Text('Tiếp'),
                            ),
                          ],
                        ),
                    ],
                  ),
                ),
        ),
      ],
    ),
  );
}
