import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_theme.dart';
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

  @override
  void dispose() {
    _name.dispose();
    _dose.dispose();
    _unit.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final label = _name.text.trim();
    if (label.isEmpty || _saving) return;
    final db = context.read<AppDatabase>();
    setState(() => _saving = true);
    try {
      await db.addMedicationEvent(
        label: label,
        dose: double.tryParse(_dose.text.trim().replaceAll(',', '.')),
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
      });
    } finally {
      if (mounted && _saving) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final db = context.read<AppDatabase>();
    return Scaffold(
      backgroundColor: AminaTheme.bg(context),
      appBar: AppBar(
        title: Text(_mt(context, 'Médicaments', 'Medications', 'الأدوية')),
      ),
      body: ListView(
        padding: const EdgeInsetsDirectional.fromSTEB(20, 16, 20, 40),
        children: [
          Text(
            _mt(
              context,
              'Enregistrez uniquement un traitement réellement pris. IAmina ne recommande ni médicament ni dose.',
              'Record only treatment you actually took. IAmina does not recommend a medication or dose.',
              'سجّل فقط علاجاً تناولته فعلاً. IAmina لا توصي بدواء أو جرعة.',
            ),
            style: TextStyle(
              color: AminaTheme.textSecondary(context),
              height: 1.4,
            ),
          ),
          const SizedBox(height: 18),
          TextField(
            key: const Key('medication-name-input'),
            controller: _name,
            decoration: InputDecoration(
              labelText: _mt(
                context,
                'Nom du traitement',
                'Treatment name',
                'اسم العلاج',
              ),
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _dose,
                  keyboardType: const TextInputType.numberWithOptions(
                    decimal: true,
                  ),
                  decoration: InputDecoration(
                    labelText: _mt(
                      context,
                      'Dose (facultatif)',
                      'Dose (optional)',
                      'الجرعة (اختياري)',
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: TextField(
                  controller: _unit,
                  decoration: InputDecoration(
                    labelText: _mt(context, 'Unité', 'Unit', 'الوحدة'),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: const Icon(Icons.schedule_rounded),
            title: Text(
              _mt(context, 'Heure de prise', 'Time taken', 'وقت التناول'),
            ),
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
          FilledButton.icon(
            key: const Key('save-medication-event'),
            onPressed: _saving ? null : _save,
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
          const SizedBox(height: 26),
          Text(
            _mt(
              context,
              'Prises récentes',
              'Recent intakes',
              'آخر مرات التناول',
            ),
            style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 10),
          StreamBuilder<List<MedicationEventData>>(
            stream: db.watchMedicationEvents(),
            builder: (context, snapshot) {
              final items = snapshot.data ?? const <MedicationEventData>[];
              if (items.isEmpty) {
                return Text(
                  _mt(
                    context,
                    'Aucune prise enregistrée.',
                    'No intake recorded.',
                    'لا توجد جرعات مسجلة.',
                  ),
                  style: TextStyle(color: AminaTheme.textSecondary(context)),
                );
              }
              return Column(
                children: items.map((item) {
                  final dose = item.dose == null
                      ? ''
                      : ' · ${item.dose!.toStringAsFixed(item.dose! % 1 == 0 ? 0 : 1)} ${item.unit ?? ''}'
                            .trimRight();
                  return ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: const Icon(Icons.medication_outlined),
                    title: Text('${item.label}$dose'),
                    subtitle: Text(
                      DateFormat('dd/MM/yyyy HH:mm').format(item.takenAt),
                    ),
                    trailing: IconButton(
                      tooltip: _mt(context, 'Supprimer', 'Delete', 'حذف'),
                      icon: const Icon(Icons.delete_outline_rounded),
                      onPressed: () => db.deleteMedicationEvent(item.id),
                    ),
                  );
                }).toList(),
              );
            },
          ),
        ],
      ),
    );
  }
}
