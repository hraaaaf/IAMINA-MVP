import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../../core/theme/amina_visual_language.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/mobile_page_header.dart';
import '../../data/drift/database.dart';

String _mt(BuildContext context, String fr, String en, String ar) {
  final code = Localizations.localeOf(context).languageCode;
  if (code == 'ar') return ar;
  if (code == 'en') return en;
  return fr;
}

class MedicationScreen extends StatefulWidget {
  const MedicationScreen({super.key});

  @override
  State<MedicationScreen> createState() => _MedicationScreenState();
}

class _MedicationScreenState extends State<MedicationScreen> {
  final _name = TextEditingController();
  final _dose = TextEditingController();
  final _unit = TextEditingController();
  DateTime _takenAt = DateTime.now();
  bool _saving = false;
  String? _nameError;
  String? _doseError;
  String? _unitError;

  @override
  void dispose() {
    _name.dispose();
    _dose.dispose();
    _unit.dispose();
    super.dispose();
  }

  double? _parseDose(String raw) {
    if (raw.isEmpty) return null;
    final parsed = double.tryParse(raw.replaceAll(',', '.'));
    if (parsed == null || !parsed.isFinite || parsed <= 0) return null;
    return parsed;
  }

  bool _validate() {
    final label = _name.text.trim();
    final rawDose = _dose.text.trim();
    final rawUnit = _unit.text.trim();
    final parsedDose = _parseDose(rawDose);

    final nameError = label.isEmpty
        ? _mt(
            context,
            'Indiquez le traitement réellement pris.',
            'Enter the treatment you actually took.',
            'أدخل العلاج الذي تناولته فعلاً.',
          )
        : null;
    final doseError = rawDose.isNotEmpty && parsedDose == null
        ? _mt(
            context,
            'Saisissez une dose positive valide.',
            'Enter a valid positive dose.',
            'أدخل جرعة موجبة وصحيحة.',
          )
        : null;
    final unitError = rawUnit.isNotEmpty && rawDose.isEmpty
        ? _mt(
            context,
            'Ajoutez la dose ou effacez l’unité.',
            'Add the dose or clear the unit.',
            'أدخل الجرعة أو امسح الوحدة.',
          )
        : null;

    setState(() {
      _nameError = nameError;
      _doseError = doseError;
      _unitError = unitError;
    });
    return nameError == null && doseError == null && unitError == null;
  }

  Future<void> _save() async {
    if (_saving || !_validate()) return;

    final label = _name.text.trim();
    final rawDose = _dose.text.trim();
    final db = context.read<AppDatabase>();
    setState(() => _saving = true);
    try {
      await db.addMedicationEvent(
        label: label,
        dose: _parseDose(rawDose),
        unit: _unit.text,
        takenAt: _takenAt,
      );
      if (!mounted) return;
      _name.clear();
      _dose.clear();
      _unit.clear();
      setState(() {
        _takenAt = DateTime.now();
        _saving = false;
        _nameError = null;
        _doseError = null;
        _unitError = null;
      });
    } finally {
      if (mounted && _saving) setState(() => _saving = false);
    }
  }

  Future<void> _deleteMedicationEvent(AppDatabase db, int id) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(
          _mt(
            context,
            'Supprimer cette prise ?',
            'Delete this intake?',
            'حذف هذه الجرعة المسجلة؟',
          ),
        ),
        content: Text(
          _mt(
            context,
            'Cette action retire uniquement cet enregistrement du journal.',
            'This only removes this recorded intake from the journal.',
            'سيؤدي هذا إلى حذف هذا التسجيل فقط من السجل.',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: Text(_mt(context, 'Annuler', 'Cancel', 'إلغاء')),
          ),
          FilledButton(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: Text(_mt(context, 'Supprimer', 'Delete', 'حذف')),
          ),
        ],
      ),
    );
    if (confirmed == true) await db.deleteMedicationEvent(id);
  }

  @override
  Widget build(BuildContext context) {
    final db = context.read<AppDatabase>();
    final title = _mt(context, 'Médicaments', 'Medications', 'الأدوية');
    return Scaffold(
      backgroundColor: AminaTheme.isDark(context)
          ? AminaTheme.bg(context)
          : const Color(0xFFF4FBF9),
      body: Stack(
        children: [
          if (!AminaTheme.isDark(context))
            PositionedDirectional(
              top: -120,
              end: -100,
              child: Container(
                width: 280,
                height: 280,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: AminaVisualLanguage.mintWaveLight.withValues(alpha: .68),
                ),
              ),
            ),
          SafeArea(
            top: false,
            child: Column(
              children: [
                AminaMobilePageHeader(
                  title: title,
                  subtitle: _mt(
                    context,
                    'Journalisez uniquement ce que vous avez réellement pris.',
                    'Record only what you actually took.',
                    'سجّل فقط ما تناولته فعلاً.',
                  ),
                ),
                Expanded(
                  child: ListView(
                    padding: const EdgeInsetsDirectional.fromSTEB(20, 18, 20, 40),
                    children: [
                      Container(
                        padding: const EdgeInsets.all(20),
                        decoration: AminaVisualLanguage.cardDecoration(context),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            Row(
                              children: [
                                Container(
                                  width: 42,
                                  height: 42,
                                  decoration: AminaVisualLanguage.mintIconDecoration(context),
                                  child: const Icon(
                                    Icons.medication_outlined,
                                    color: AminaVisualLanguage.actionGreen,
                                    size: 21,
                                  ),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Text(
                                    _mt(
                                      context,
                                      'Nouvelle prise',
                                      'New intake',
                                      'تناول جديد',
                                    ),
                                    style: TextStyle(
                                      fontFamily: 'Georgia',
                                      fontSize: 20,
                                      fontWeight: FontWeight.w700,
                                      color: AminaVisualLanguage.primaryText(context),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 14),
                            Text(
                              _mt(
                                context,
                                'IAmina ne recommande ni médicament ni dose.',
                                'IAmina does not recommend a medication or dose.',
                                'IAmina لا توصي بدواء أو جرعة.',
                              ),
                              style: TextStyle(
                                color: AminaVisualLanguage.secondary(context),
                                height: 1.4,
                              ),
                            ),
                            const SizedBox(height: 18),
                            TextField(
                              key: const Key('medication-name-input'),
                              controller: _name,
                              onChanged: (_) {
                                if (_nameError != null || mounted) {
                                  setState(() => _nameError = null);
                                }
                              },
                              decoration: InputDecoration(
                                labelText: _mt(
                                  context,
                                  'Nom du traitement',
                                  'Treatment name',
                                  'اسم العلاج',
                                ),
                                errorText: _nameError,
                              ),
                            ),
                            const SizedBox(height: 12),
                            Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Expanded(
                                  child: TextField(
                                    key: const Key('medication-dose-input'),
                                    controller: _dose,
                                    onChanged: (_) {
                                      if (_doseError != null || _unitError != null) {
                                        setState(() {
                                          _doseError = null;
                                          _unitError = null;
                                        });
                                      }
                                    },
                                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                                    decoration: InputDecoration(
                                      labelText: _mt(
                                        context,
                                        'Dose (facultatif)',
                                        'Dose (optional)',
                                        'الجرعة (اختياري)',
                                      ),
                                      errorText: _doseError,
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 10),
                                Expanded(
                                  child: TextField(
                                    key: const Key('medication-unit-input'),
                                    controller: _unit,
                                    onChanged: (_) {
                                      if (_unitError != null) {
                                        setState(() => _unitError = null);
                                      }
                                    },
                                    decoration: InputDecoration(
                                      labelText: _mt(context, 'Unité', 'Unit', 'الوحدة'),
                                      errorText: _unitError,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 12),
                            ListTile(
                              contentPadding: EdgeInsets.zero,
                              leading: Container(
                                width: 38,
                                height: 38,
                                decoration: AminaVisualLanguage.mintIconDecoration(context),
                                child: const Icon(
                                  Icons.schedule_rounded,
                                  color: AminaVisualLanguage.actionGreen,
                                  size: 19,
                                ),
                              ),
                              title: Text(_mt(context, 'Heure de prise', 'Time taken', 'وقت التناول')),
                              subtitle: Text(DateFormat('dd/MM/yyyy HH:mm').format(_takenAt)),
                              onTap: () async {
                                final date = await showDatePicker(
                                  context: context,
                                  initialDate: _takenAt,
                                  firstDate: DateTime.now().subtract(const Duration(days: 365)),
                                  lastDate: DateTime.now(),
                                );
                                if (date == null || !context.mounted) return;
                                final time = await showTimePicker(
                                  context: context,
                                  initialTime: TimeOfDay.fromDateTime(_takenAt),
                                );
                                if (time == null || !context.mounted) return;
                                setState(() {
                                  _takenAt = DateTime(
                                    date.year,
                                    date.month,
                                    date.day,
                                    time.hour,
                                    time.minute,
                                  );
                                });
                              },
                            ),
                            const SizedBox(height: 8),
                            SizedBox(
                              height: 48,
                              child: FilledButton.icon(
                                key: const Key('save-medication-event'),
                                onPressed: _saving || _name.text.trim().isEmpty
                                    ? null
                                    : _save,
                                icon: const Icon(Icons.check_rounded),
                                label: Text(
                                  _mt(
                                    context,
                                    'Enregistrer la prise',
                                    'Save intake',
                                    'حفظ التناول',
                                  ),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 22),
                      Text(
                        _mt(context, 'Prises récentes', 'Recent intakes', 'آخر مرات التناول'),
                        style: TextStyle(
                          fontFamily: 'Georgia',
                          fontSize: 20,
                          fontWeight: FontWeight.w700,
                          color: AminaVisualLanguage.primaryText(context),
                        ),
                      ),
                      const SizedBox(height: 10),
                      StreamBuilder<List<MedicationEventData>>(
                        stream: db.watchMedicationEvents(),
                        builder: (context, snapshot) {
                          final items = snapshot.data ?? const <MedicationEventData>[];
                          if (items.isEmpty) {
                            return Container(
                              padding: const EdgeInsets.all(18),
                              decoration: AminaVisualLanguage.cardDecoration(context),
                              child: Text(
                                _mt(
                                  context,
                                  'Aucune prise enregistrée.',
                                  'No intake recorded.',
                                  'لا توجد جرعات مسجلة.',
                                ),
                                style: TextStyle(color: AminaVisualLanguage.secondary(context)),
                              ),
                            );
                          }
                          return Column(
                            children: items.map((item) {
                              final dose = item.dose == null
                                  ? ''
                                  : ' · ${item.dose!.toStringAsFixed(item.dose! % 1 == 0 ? 0 : 1)} ${item.unit ?? ''}'.trimRight();
                              return Container(
                                margin: const EdgeInsets.only(bottom: 10),
                                decoration: AminaVisualLanguage.cardDecoration(context),
                                child: ListTile(
                                  leading: Container(
                                    width: 40,
                                    height: 40,
                                    decoration: AminaVisualLanguage.mintIconDecoration(context),
                                    child: const Icon(
                                      Icons.medication_outlined,
                                      color: AminaVisualLanguage.actionGreen,
                                      size: 20,
                                    ),
                                  ),
                                  title: Text('${item.label}$dose'),
                                  subtitle: Text(DateFormat('dd/MM/yyyy HH:mm').format(item.takenAt)),
                                  trailing: IconButton(
                                    key: Key('delete-medication-event-${item.id}'),
                                    tooltip: _mt(context, 'Supprimer', 'Delete', 'حذف'),
                                    icon: const Icon(Icons.delete_outline_rounded),
                                    onPressed: () => _deleteMedicationEvent(db, item.id),
                                  ),
                                ),
                              );
                            }).toList(),
                          );
                        },
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
