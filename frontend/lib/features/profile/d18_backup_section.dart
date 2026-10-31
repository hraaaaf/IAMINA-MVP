import 'dart:convert';
import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../../core/theme/amina_visual_language.dart';
import '../../data/drift/d18_encrypted_backup.dart';
import '../../data/drift/database.dart';

/// D18-specific backup UI: intentionally separate from clinical document import.
class D18BackupSection extends StatelessWidget {
  final AppDatabase db;
  const D18BackupSection({super.key, required this.db});

  String _t(BuildContext context, String fr, String en, String ar) =>
      switch (Localizations.localeOf(context).languageCode) {
        'fr' => fr, 'ar' => ar, _ => en,
      };

  @override
  Widget build(BuildContext context) {
    if (!kIsWeb || db.patientVaultScope == null ||
        db.patientVaultScope!.databaseName == 'amina_vault_v1_audit') {
      return const SizedBox.shrink();
    }
    return Column(
      key: const Key('d18-backup-section'),
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const SizedBox(height: 16),
        Divider(color: AminaVisualLanguage.controlBorder(context)),
        const SizedBox(height: 12),
        Text(
          _t(context, 'Sauvegarde personnelle', 'Personal backup',
              'النسخة الاحتياطية الشخصية'),
          style: TextStyle(
            fontWeight: FontWeight.w800,
            fontSize: 15,
            color: AminaVisualLanguage.primaryText(context),
          ),
        ),
        const SizedBox(height: 6),
        Text(
          _t(context,
              'Données D18 uniquement. Conservées sur cet appareil, sans synchronisation automatique. Le navigateur peut les effacer.',
              'D18 data only. Stored on this device without automatic sync. Browser data can be deleted.',
              'بيانات D18 فقط على هذا الجهاز دون مزامنة تلقائية. قد تُحذف بيانات المتصفح.'),
          style: Theme.of(context).textTheme.bodySmall,
        ),
        const SizedBox(height: 12),
        OutlinedButton.icon(
          key: const Key('d18-export-open'),
          onPressed: () => showDialog<void>(
            context: context,
            builder: (_) => _D18ExportDialog(db: db),
          ),
          icon: const Icon(Icons.lock_outline),
          label: Text(_t(context, 'Créer une sauvegarde chiffrée',
              'Create encrypted backup', 'إنشاء نسخة احتياطية مشفرة')),
        ),
        const SizedBox(height: 8),
        OutlinedButton.icon(
          key: const Key('d18-restore-open'),
          onPressed: () => showDialog<void>(
            context: context,
            builder: (_) => _D18RestoreDialog(db: db),
          ),
          icon: const Icon(Icons.restore_page_outlined),
          label: Text(_t(context, 'Restaurer une sauvegarde',
              'Restore a backup', 'استعادة نسخة احتياطية')),
        ),
      ],
    );
  }
}

class _D18ExportDialog extends StatefulWidget {
  final AppDatabase db;
  const _D18ExportDialog({required this.db});
  @override
  State<_D18ExportDialog> createState() => _D18ExportDialogState();
}

class _D18ExportDialogState extends State<_D18ExportDialog> {
  final _secret = TextEditingController();
  final _confirm = TextEditingController();
  bool _busy = false;
  String? _error;

  String _t(String fr, String en, String ar) =>
      switch (Localizations.localeOf(context).languageCode) {
        'fr' => fr, 'ar' => ar, _ => en,
      };

  @override
  void dispose() {
    _secret.dispose();
    _confirm.dispose();
    super.dispose();
  }

  Future<void> _export() async {
    if (_busy || _secret.text.length < 12 ||
        _secret.text != _confirm.text) {
      setState(() => _error = _t(
        'Utilisez au moins 12 caractères et confirmez exactement la phrase secrète.',
        'Use at least 12 characters and confirm the exact passphrase.',
        'استخدم 12 حرفًا على الأقل وأكّد العبارة السرية.'));
      return;
    }
    final db = widget.db;
    setState(() { _busy = true; _error = null; });
    try {
      final encrypted = await D18EncryptedBackup.exportEncrypted(
        db, passphrase: _secret.text,
      );
      // Never save plaintext, passphrases, identifiers or clinical values
      // into the filename or browser storage.
      if (!mounted || !identical(db, widget.db)) return;
      _secret.clear();
      _confirm.clear();
      final result = await FilePicker.platform.saveFile(
        dialogTitle: _t('Sauvegarde personnelle chiffrée',
            'Encrypted personal backup', 'نسخة احتياطية مشفرة'),
        fileName: 'iamina-d18-backup.iamina',
        type: FileType.custom,
        allowedExtensions: const ['iamina'],
        bytes: Uint8List.fromList(utf8.encode(encrypted)),
      );
      if (!mounted) return;
      if (result == null) {
        setState(() => _error = _t(
          'Téléchargement non confirmé. Aucune sauvegarde n’est garantie.',
          'Download not confirmed. No backup is guaranteed.',
          'لم يتم تأكيد التنزيل.'));
        return;
      }
      Navigator.of(context).pop();
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_t(
        'Fichier chiffré généré. Gardez-le et sa phrase secrète séparément ; testez la restauration.',
        'Encrypted file generated. Keep the file and passphrase separately; test restoration.',
        'تم إنشاء الملف المشفر. احتفظ به وبالعبارة السرية منفصلين واختبر الاستعادة.'))));
    } catch (_) {
      if (!mounted) return;
      setState(() => _error = _t(
        'Export impossible ; aucune sauvegarde créée.',
        'Export failed; no backup created.',
        'تعذر التصدير، لم تُنشأ نسخة احتياطية.'));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: Text(_t('Créer une sauvegarde chiffrée',
        'Create encrypted backup', 'إنشاء نسخة احتياطية مشفرة')),
    content: ConstrainedBox(
      constraints: const BoxConstraints(maxWidth: 460),
      child: SingleChildScrollView(child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(_t(
            'Cette sauvegarde contient uniquement votre année de naissance, identité déclarée et historique de poids, s’ils sont renseignés. Elle ne contient pas vos glycémies ni vos traitements.',
            'Only your optional birth year, declared identity and weight history are included; no glycemia or treatment data.',
            'تتضمن هذه النسخة البيانات الشخصية الاختيارية وسجل الوزن فقط.')),
          const SizedBox(height: 12),
          TextField(
            key: const Key('d18-export-secret'),
            controller: _secret,
            obscureText: true,
            enableSuggestions: false,
            autocorrect: false,
            decoration: InputDecoration(labelText: _t(
              'Phrase secrète (12 caractères minimum)',
              'Passphrase (at least 12 characters)',
              'العبارة السرية (12 حرفًا على الأقل)')),
          ),
          const SizedBox(height: 8),
          TextField(
            key: const Key('d18-export-confirm'),
            controller: _confirm,
            obscureText: true,
            enableSuggestions: false,
            autocorrect: false,
            decoration: InputDecoration(labelText: _t(
              'Confirmer la phrase secrète', 'Confirm passphrase',
              'تأكيد العبارة السرية')),
          ),
          const SizedBox(height: 12),
          Text(_t(
            'Sans cette phrase secrète, IAMINA ne pourra pas restaurer vos données. Elle n’est pas enregistrée.',
            'Without this passphrase IAMINA cannot restore your data. It is not stored.',
            'دون العبارة السرية لا يمكن استعادة البيانات. لا يتم حفظها.')),
          if (_error != null) Padding(
            padding: const EdgeInsets.only(top: 10),
            child: Text(_error!, key: const Key('d18-export-error'),
                style: TextStyle(color: Theme.of(context).colorScheme.error)),
          ),
        ],
      )),
    ),
    actions: [
      TextButton(onPressed: _busy ? null : () => Navigator.pop(context),
        child: Text(_t('Annuler', 'Cancel', 'إلغاء'))),
      FilledButton(
        key: const Key('d18-export-create'),
        onPressed: _busy ? null : _export,
        child: Text(_t('Chiffrer et télécharger',
            'Encrypt and download', 'تشفير وتنزيل')),
      ),
    ],
  );
}

class _D18RestoreDialog extends StatefulWidget {
  final AppDatabase db;
  const _D18RestoreDialog({required this.db});
  @override
  State<_D18RestoreDialog> createState() => _D18RestoreDialogState();
}

class _D18RestoreDialogState extends State<_D18RestoreDialog> {
  final _phrase = TextEditingController();
  String? _rawFile;
  D18BackupPreview? _preview;
  bool _busy = false;
  bool _confirm = false;
  bool _transfer = false;
  String? _error;

  String _t(String fr, String en, String ar) =>
      switch (Localizations.localeOf(context).languageCode) {
        'fr' => fr, 'ar' => ar, _ => en,
      };

  @override
  void dispose() {
    _phrase.dispose();
    _rawFile = null;
    _preview = null;
    super.dispose();
  }

  Future<void> _pick() async {
    if (_busy) return;
    setState(() { _busy = true; _preview = null; _rawFile = null; _error = null; });
    try {
      final selected = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: const ['iamina'],
        withData: true,
      );
      if (!mounted) return;
      if (selected == null) return;
      final file = selected.files.single;
      if (file.size > D18EncryptedBackup.maximumEnvelopeBytes ||
          file.bytes == null) {
        throw const FormatException('Invalid D18 encrypted backup');
      }
      setState(() { _rawFile = utf8.decode(file.bytes!); _confirm = false; _transfer = false; });
    } catch (_) {
      if (mounted) setState(() => _error = _t(
        'Fichier incompatible ou illisible.', 'Invalid or unreadable file.',
        'الملف غير صالح أو غير قابل للقراءة.'));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _inspect() async {
    if (_busy || _rawFile == null) return;
    setState(() { _busy = true; _error = null; _preview = null; });
    try {
      final data = await D18EncryptedBackup.open(
        _rawFile!, passphrase: _phrase.text,
      );
      if (!mounted) return;
      _phrase.clear();
      final target = widget.db.patientVaultScope?.databaseName;
      final sameOwner = target == data.sourceVaultName;
      if (!sameOwner && !(data.isDeviceOnly &&
          target?.startsWith('amina_vault_v1_device_') == true)) {
        throw StateError('D18 identity mismatch');
      }
      setState(() { _preview = data; _confirm = false; _transfer = false; });
    } catch (_) {
      if (mounted) setState(() => _error = _t(
        'Phrase secrète incorrecte, fichier altéré ou patient incompatible. Aucune donnée modifiée.',
        'Wrong passphrase, damaged file or incompatible patient. No data changed.',
        'العبارة السرية خاطئة أو الملف تالف أو المريض غير مطابق. لم تتغير البيانات.'));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _restore() async {
    final preview = _preview;
    if (_busy || !_confirm || preview == null) return;
    final db = widget.db;
    final needsTransfer = db.patientVaultScope?.databaseName != preview.sourceVaultName;
    if (needsTransfer && !_transfer) return;
    setState(() { _busy = true; _error = null; });
    try {
      await D18EncryptedBackup.restoreInto(
        db, preview, allowDeviceTransfer: needsTransfer && _transfer,
      );
      if (!mounted) return;
      _rawFile = null;
      _preview = null;
      Navigator.of(context).pop();
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_t(
        'Données D18 restaurées et vérifiées. Actualisez le profil.',
        'D18 data restored and checked. Refresh your profile.',
        'تمت استعادة بيانات D18 والتحقق منها. حدّث الملف الشخصي.'))));
    } catch (_) {
      if (mounted) setState(() => _error = _t(
        'Restauration refusée. Le coffre existant reste intact. Vérifiez qu’il est vide.',
        'Restore refused. Your existing vault is unchanged. Check that it is empty.',
        'تم رفض الاستعادة. بيانات الخزنة الحالية لم تتغير.'));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final preview = _preview;
    final needsTransfer = preview != null &&
        widget.db.patientVaultScope?.databaseName != preview.sourceVaultName;
    return AlertDialog(
      title: Text(_t('Restaurer une sauvegarde D18',
          'Restore a D18 backup', 'استعادة نسخة D18')),
      content: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 460),
        child: SingleChildScrollView(child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(_t(
              'La restauration ne remplace jamais vos données existantes. Seul un coffre D18 vide peut être rempli.',
              'Restore never replaces existing data. Only an empty D18 vault can be restored.',
              'لا تستبدل الاستعادة أي بيانات موجودة. يجب أن تكون خزنة D18 فارغة.')),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              key: const Key('d18-restore-pick'),
              onPressed: _busy ? null : _pick,
              icon: const Icon(Icons.file_open_outlined),
              label: Text(_t('Choisir un fichier .iamina',
                  'Choose a .iamina file', 'اختر ملف .iamina')),
            ),
            if (_rawFile != null && preview == null) ...[
              const SizedBox(height: 12),
              TextField(
                key: const Key('d18-restore-secret'),
                controller: _phrase,
                obscureText: true,
                enableSuggestions: false,
                autocorrect: false,
                decoration: InputDecoration(labelText: _t(
                  'Phrase secrète', 'Passphrase', 'العبارة السرية')),
              ),
              const SizedBox(height: 8),
              OutlinedButton(
                key: const Key('d18-restore-inspect'),
                onPressed: _busy ? null : _inspect,
                child: Text(_t('Déchiffrer et examiner',
                    'Decrypt and preview', 'فك التشفير والمعاينة')),
              ),
            ],
            if (preview != null) ...[
              const SizedBox(height: 14),
              Text(_t('Aperçu vérifié du fichier',
                  'Verified file preview', 'معاينة الملف بعد التحقق'),
                  style: const TextStyle(fontWeight: FontWeight.w700)),
              const SizedBox(height: 6),
              Text(_t('Informations personnelles : ', 'Personal information: ',
                  'المعلومات الشخصية: ') +
                  (preview.hasDemographics
                      ? _t('présentes', 'present', 'موجودة')
                      : _t('absentes', 'absent', 'غير موجودة'))),
              Text(_t('Pesées historiques : ', 'Weight observations: ',
                  'قياسات الوزن: ') + preview.observationCount.toString()),
              if (needsTransfer) ...[
                const SizedBox(height: 8),
                CheckboxListTile(
                  key: const Key('d18-device-transfer-consent'),
                  value: _transfer,
                  onChanged: _busy ? null :
                      (v) => setState(() => _transfer = v ?? false),
                  title: Text(_t(
                    'J’autorise le transfert vers mon nouveau coffre local vide. IAMINA ne peut pas vérifier mon identité sur cet appareil.',
                    'I authorize transfer into my new empty local vault. IAMINA cannot independently verify my identity on this device.',
                    'أوافق على النقل إلى خزنـتي المحلية الجديدة الفارغة دون تحقق مستقل من الهوية.')),
                  controlAffinity: ListTileControlAffinity.leading,
                ),
              ],
              CheckboxListTile(
                key: const Key('d18-restore-consent'),
                value: _confirm,
                onChanged: _busy ? null :
                    (v) => setState(() => _confirm = v ?? false),
                title: Text(_t(
                  'Je confirme restaurer ces informations dans mon coffre D18 vide.',
                  'I confirm restore into my empty D18 vault.',
                  'أؤكد الاستعادة في خزنة D18 الفارغة.')),
                controlAffinity: ListTileControlAffinity.leading,
              ),
            ],
            if (_error != null)
              Padding(padding: const EdgeInsets.only(top: 10),
                child: Text(_error!, key: const Key('d18-restore-error'),
                  style: TextStyle(color: Theme.of(context).colorScheme.error))),
          ],
        )),
      ),
      actions: [
        TextButton(onPressed: _busy ? null : () => Navigator.pop(context),
            child: Text(_t('Annuler', 'Cancel', 'إلغاء'))),
        if (preview != null)
          FilledButton(
            key: const Key('d18-restore-commit'),
            onPressed: !_busy && _confirm && (!needsTransfer || _transfer)
                ? _restore : null,
            child: Text(_t('Restaurer', 'Restore', 'استعادة')),
          ),
      ],
    );
  }
}
