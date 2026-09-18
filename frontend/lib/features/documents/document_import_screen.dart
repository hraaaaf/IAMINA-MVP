import 'package:amina/l10n/app_localizations.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../core/localization/document_import_localized_copy.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/responsive_content_surface.dart';
import '../../l10n/audited_page_copy.dart';
import '../../data/models/document_models.dart';
import '../../services/api_client.dart';

part 'document_import_screen_presentation.dart';

class DocumentImportScreen extends StatefulWidget {
  const DocumentImportScreen({super.key});

  @override
  State<DocumentImportScreen> createState() => _DocumentImportScreenState();
}

class _DocumentImportScreenState extends State<DocumentImportScreen> {
  _Phase _phase = _Phase.pick;
  bool _loading = false;
  String? _error;
  PulperPreview? _preview;
  PulperConfirmResult? _result;
  String _fileName = '';

  Future<void> _pickFile() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final picked = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: [
          'pdf',
          'jpg',
          'jpeg',
          'png',
          'webp',
          'heic',
          'csv',
          'xlsx',
          'xls',
          'docx',
          'doc',
        ],
        withData: false,
        withReadStream: true,
      );

      if (picked == null || picked.files.isEmpty) {
        setState(() => _loading = false);
        return;
      }

      final pf = picked.files.first;
      final stream = pf.readStream;
      if (stream == null) {
        setState(() {
          _loading = false;
          _error = AppLocalizations.of(context)!.fileReadFailed;
        });
        return;
      }

      _fileName = pf.name;
      await _ingest(
        stream,
        pf.size,
        pf.name,
        _mimeFromExt(pf.extension ?? ''),
      );
    } catch (e) {
      setState(() {
        _loading = false;
        _error = AppLocalizations.of(context)!.documentError(e);
      });
    }
  }

  Future<void> _ingest(
    Stream<List<int>> stream,
    int byteLength,
    String name,
    String mime,
  ) async {
    final api = context.read<ApiClient>();
    final preview = await api.ingestDocumentStream(
      stream,
      byteLength,
      name,
      mime,
    );

    setState(() {
      _loading = false;
      if (preview == null) {
        _error = AppLocalizations.of(context)!.documentAnalysisFailed;
      } else {
        _preview = preview;
        _phase = _Phase.preview;
      }
    });
  }

  Future<void> _confirm() async {
    if (_preview == null) return;
    setState(() {
      _loading = true;
      _error = null;
    });

    final api = context.read<ApiClient>();
    final result = await api.confirmDocumentImport(_preview!.batchId);

    setState(() {
      _loading = false;
      if (result == null) {
        _error = AppLocalizations.of(context)!.documentConfirmationFailed;
      } else {
        _result = result;
        _phase = _Phase.done;
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AminaTheme.bg(context),
      appBar: AppBar(
        backgroundColor: AminaTheme.surface(context),
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () =>
              context.canPop() ? context.pop() : context.go('/dashboard'),
        ),
        title: Text(
          AuditedPageCopy.of(context).documentTitle,
          style: TextStyle(
            color: AminaTheme.textPrimary(context),
            fontWeight: FontWeight.w700,
            fontSize: 17,
          ),
        ),
      ),
      body: ResponsiveContentSurface(
        maxWidth: MediaQuery.sizeOf(context).width >= 900 ? 760 : 980,
        child: SafeArea(
          child: _loading
              ? _buildLoading()
              : switch (_phase) {
                  _Phase.pick => _buildPick(),
                  _Phase.preview => _buildPreview(),
                  _Phase.done => _buildDone(),
                },
        ),
      ),
    );
  }

  Widget _buildPick() {
    final size = MediaQuery.sizeOf(context);
    final compactHeight = size.height <= 600;
    final desktop = size.width >= 900;
    final verticalPadding = compactHeight ? 12.0 : 24.0;
    return LayoutBuilder(
      builder: (context, constraints) => SingleChildScrollView(
        key: const ValueKey('document-import-pick-scroll'),
        padding: EdgeInsets.symmetric(
          horizontal: compactHeight ? 20 : 24,
          vertical: verticalPadding,
        ),
        child: ConstrainedBox(
          constraints: BoxConstraints(
            minHeight: constraints.maxHeight > verticalPadding * 2
                ? constraints.maxHeight - verticalPadding * 2
                : 0,
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const _DocumentImportIcon(),
              SizedBox(height: compactHeight ? 14 : 20),
              Text(
                AuditedPageCopy.of(context).documentIntro,
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: compactHeight ? 13 : 14,
                  color: AminaTheme.textSecondary(context),
                  height: compactHeight ? 1.4 : 1.5,
                ),
              ),
              SizedBox(height: compactHeight ? 20 : 32),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                alignment: WrapAlignment.center,
                children: [
                  const _FormatChip(icon: Icons.picture_as_pdf, label: 'PDF'),
                  _FormatChip(
                    icon: Icons.image,
                    label: AuditedPageCopy.of(context).photo,
                  ),
                  const _FormatChip(
                    icon: Icons.table_chart,
                    label: 'Excel / CSV',
                  ),
                  const _FormatChip(icon: Icons.description, label: 'Word'),
                ],
              ),
              SizedBox(height: compactHeight ? 12 : 20),
              const _PrivacyGateNotice(),
              SizedBox(height: compactHeight ? 14 : 24),
              SizedBox(
                width: desktop ? 260 : double.infinity,
                child: ElevatedButton.icon(
                  key: const ValueKey('choose-document-button'),
                  onPressed: _pickFile,
                  icon: const Icon(Icons.folder_open),
                  label: Text(AuditedPageCopy.of(context).chooseDocument),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AminaTheme.teal600,
                    foregroundColor: Colors.white,
                    padding: EdgeInsets.symmetric(
                      vertical: compactHeight ? 13 : 16,
                    ),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                    textStyle: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ),
              if (_error != null) ...[
                const SizedBox(height: 16),
                _ErrorCard(message: _error!),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildPreview() {
    final p = _preview!;
    final l10n = AppLocalizations.of(context)!;
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _ConfidenceBanner(
            confidence: p.confidence,
            needsReview: p.needsReview,
          ),
          const SizedBox(height: 16),
          _SectionTitle(title: l10n.analyzedDocument, subtitle: _fileName),
          const SizedBox(height: 20),
          if (p.errors.isNotEmpty) ...[
            _ErrorCard(message: p.errors.join('\n')),
            const SizedBox(height: 16),
          ],
          if (p.glucoseReadings.isNotEmpty) ...[
            _SectionHeader(
              title: l10n.glucoseReadings,
              count: p.glucoseReadings.length,
            ),
            const SizedBox(height: 8),
            _GlucoseReadingsList(readings: p.glucoseReadings),
            const SizedBox(height: 16),
          ],
          if (!p.labValues.isEmpty) ...[
            _SectionHeader(title: l10n.labResults),
            const SizedBox(height: 8),
            _LabValuesCard(values: p.labValues),
            const SizedBox(height: 16),
          ],
          if (p.medications.isNotEmpty) ...[
            _SectionHeader(
              title: l10n.medicines,
              count: p.medications.length,
            ),
            const SizedBox(height: 8),
            ...p.medications.map((m) => _MedicationTile(med: m)),
            const SizedBox(height: 16),
          ],
          if (p.clinicalNotes.isNotEmpty) ...[
            _SectionHeader(title: l10n.clinicalNotes),
            const SizedBox(height: 8),
            _NotesCard(notes: p.clinicalNotes),
            const SizedBox(height: 16),
          ],
          if (p.warnings.isNotEmpty) ...[
            ...p.warnings.map((w) => _WarningTile(warning: w)),
            const SizedBox(height: 16),
          ],
          if (!p.hasUsefulData) ...[
            const _EmptyCard(),
            const SizedBox(height: 16),
          ],
          if (p.hasUsefulData) ...[
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _confirm,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AminaTheme.teal600,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                  textStyle: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                child: Text(l10n.confirmImport),
              ),
            ),
          ],
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton(
              onPressed: () => setState(() {
                _phase = _Phase.pick;
                _preview = null;
                _error = null;
              }),
              style: OutlinedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
              ),
              child: Text(l10n.cancelImport),
            ),
          ),
          const SizedBox(height: 40),
        ],
      ),
    );
  }

  Widget _buildDone() {
    final r = _result!;
    final l10n = AppLocalizations.of(context)!;
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            r.ok ? Icons.check_circle : Icons.error_outline,
            size: 80,
            color: r.ok ? AminaTheme.teal500 : Colors.red,
          ),
          const SizedBox(height: 24),
          Text(
            r.ok ? l10n.documentImported : l10n.importFailed,
            style: TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w800,
              color: AminaTheme.textPrimary(context),
            ),
          ),
          const SizedBox(height: 12),
          if (r.ok) ...[
            _StatRow(
              label: l10n.importedGlucoseReadings,
              value: '${r.glucoseReadingsSaved}',
            ),
            if (r.glucoseDuplicates > 0)
              _StatRow(
                label: l10n.duplicatesIgnored,
                value: '${r.glucoseDuplicates}',
              ),
          ],
          if (r.errors.isNotEmpty) ...[
            const SizedBox(height: 12),
            _ErrorCard(message: r.errors.join('\n')),
          ],
          const SizedBox(height: 32),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () => context.go('/dashboard'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AminaTheme.teal600,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
                textStyle: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                ),
              ),
              child: Text(l10n.backToDashboard),
            ),
          ),
          const SizedBox(height: 12),
          TextButton(
            onPressed: () => setState(() {
              _phase = _Phase.pick;
              _preview = null;
              _result = null;
              _error = null;
            }),
            child: Text(l10n.importAnotherDocument),
          ),
        ],
      ),
    );
  }

  Widget _buildLoading() {
    final l10n = AppLocalizations.of(context)!;
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const CircularProgressIndicator(),
          const SizedBox(height: 20),
          Text(
            _phase == _Phase.pick
                ? l10n.analyzingDocument
                : l10n.savingDocument,
            style: TextStyle(color: AminaTheme.textSecondary(context)),
          ),
        ],
      ),
    );
  }

  String _mimeFromExt(String ext) =>
      const {
        'pdf': 'application/pdf',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'webp': 'image/webp',
        'heic': 'image/heic',
        'csv': 'text/csv',
        'xlsx':
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'xls': 'application/vnd.ms-excel',
        'docx':
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'doc': 'application/msword',
      }[ext.toLowerCase()] ??
      'application/octet-stream';
}

enum _Phase { pick, preview, done }
