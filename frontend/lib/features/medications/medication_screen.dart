import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

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

  Future<void> _pickTakenAt() async {
    final date = await showDatePicker(
      context: context,
      initialDate: _takenAt,
      firstDate: DateTime.now().subtract(const Duration(days: 365)),
      lastDate: DateTime.now(),
    );
    if (date == null || !mounted) return;
    final time = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(_takenAt),
    );
    if (time == null || !mounted) return;
    setState(() {
      _takenAt = DateTime(
        date.year,
        date.month,
        date.day,
        time.hour,
        time.minute,
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    final db = context.read<AppDatabase>();
    final mobile = MediaQuery.sizeOf(context).width < 700;
    final title = _mt(context, 'Médicaments', 'Medications', 'الأدوية');
    final subtitle = _mt(
      context,
      'Journal de vos prises réellement effectuées',
      'A log of treatment you actually took',
      'سجل لما تناولته فعلاً من علاج',
    );

    return Scaffold(
      backgroundColor: AminaTheme.bg(context),
      appBar: mobile ? null : AppBar(title: Text(title)),
      body: Column(
        children: [
          if (mobile) AminaMobilePageHeader(title: title, subtitle: subtitle),
          Expanded(
            child: ListView(
              physics: const BouncingScrollPhysics(),
              padding: EdgeInsetsDirectional.fromSTEB(
                mobile ? 18 : 24,
                mobile ? 6 : 18,
                mobile ? 18 : 24,
                112,
              ),
              children: [
                _DashboardPanel(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const _IconBadge(icon: Icons.medication_outlined),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Text(
                              _mt(
                                context,
                                'Enregistrez uniquement un traitement réellement pris. IAmina ne recommande ni médicament ni dose.',
                                'Record only treatment you actually took. IAmina does not recommend a medication or dose.',
                                'سجّل فقط علاجاً تناولته فعلاً. IAmina لا توصي بدواء أو جرعة.',
                              ),
                              style: TextStyle(
                                color: AminaTheme.textSecondary(context),
                                fontSize: 12.5,
                                height: 1.42,
                              ),
                            ),
                          ),
                        ],
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
                          prefixIcon: const Icon(Icons.medication_rounded),
                        ),
                      ),
                      const SizedBox(height: 10),
                      Row(
                        children: [
                          Expanded(
                            child: TextField(
                              controller: _dose,
                              keyboardType:
                                  const TextInputType.numberWithOptions(
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
                                labelText: _mt(
                                  context,
                                  'Unité',
                                  'Unit',
                                  'الوحدة',
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      _DateAction(
                        icon: Icons.schedule_rounded,
                        title: _mt(
                          context,
                          'Heure de prise',
                          'Time taken',
                          'وقت التناول',
                        ),
                        value: DateFormat(
                          'dd/MM/yyyy · HH:mm',
                        ).format(_takenAt),
                        onTap: _pickTakenAt,
                      ),
                      const SizedBox(height: 12),
                      FilledButton.icon(
                        key: const Key('save-medication-event'),
                        onPressed: _saving ? null : _save,
                        icon: _saving
                            ? const SizedBox(
                                width: 18,
                                height: 18,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              )
                            : const Icon(Icons.check_rounded),
                        label: Text(
                          _mt(
                            context,
                            'Enregistrer la prise',
                            'Save intake',
                            'حفظ التناول',
                          ),
                        ),
                        style: FilledButton.styleFrom(
                          minimumSize: const Size.fromHeight(50),
                          backgroundColor: const Color(0xFF064E52),
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(16),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 18),
                _SectionTitle(
                  title: _mt(
                    context,
                    'Prises récentes',
                    'Recent intakes',
                    'آخر مرات التناول',
                  ),
                ),
                const SizedBox(height: 8),
                StreamBuilder<List<MedicationEventData>>(
                  stream: db.watchMedicationEvents(),
                  builder: (context, snapshot) {
                    final items =
                        snapshot.data ?? const <MedicationEventData>[];
                    if (items.isEmpty) {
                      return _DashboardPanel(
                        child: Row(
                          children: [
                            const _IconBadge(icon: Icons.history_rounded),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Text(
                                _mt(
                                  context,
                                  'Aucune prise enregistrée.',
                                  'No intake recorded.',
                                  'لا توجد جرعات مسجلة.',
                                ),
                                style: TextStyle(
                                  color: AminaTheme.textSecondary(context),
                                  fontSize: 13,
                                ),
                              ),
                            ),
                          ],
                        ),
                      );
                    }
                    return Column(
                      children: items.map((item) {
                        final dose = item.dose == null
                            ? ''
                            : ' · ${item.dose!.toStringAsFixed(item.dose! % 1 == 0 ? 0 : 1)} ${item.unit ?? ''}'
                                  .trimRight();
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 8),
                          child: _DashboardPanel(
                            padding: const EdgeInsetsDirectional.fromSTEB(
                              14,
                              12,
                              8,
                              12,
                            ),
                            child: Row(
                              children: [
                                const _IconBadge(
                                  icon: Icons.medication_outlined,
                                  size: 38,
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        '${item.label}$dose',
                                        style: TextStyle(
                                          color: AminaTheme.textPrimary(
                                            context,
                                          ),
                                          fontSize: 14,
                                          fontWeight: FontWeight.w800,
                                        ),
                                      ),
                                      const SizedBox(height: 3),
                                      Text(
                                        DateFormat(
                                          'dd/MM/yyyy · HH:mm',
                                        ).format(item.takenAt),
                                        style: TextStyle(
                                          color: AminaTheme.textSecondary(
                                            context,
                                          ),
                                          fontSize: 11.5,
                                          fontWeight: FontWeight.w600,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                IconButton(
                                  tooltip: _mt(
                                    context,
                                    'Supprimer',
                                    'Delete',
                                    'حذف',
                                  ),
                                  icon: const Icon(
                                    Icons.delete_outline_rounded,
                                  ),
                                  color: AminaTheme.textSecondary(context),
                                  onPressed: () =>
                                      db.deleteMedicationEvent(item.id),
                                ),
                              ],
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
    );
  }
}

class _DashboardPanel extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;

  const _DashboardPanel({
    required this.child,
    this.padding = const EdgeInsets.all(16),
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: padding,
      decoration: BoxDecoration(
        color: AminaTheme.surface(context),
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: AminaTheme.divider(context)),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF064E52).withValues(alpha: 0.045),
            blurRadius: 18,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: child,
    );
  }
}

class _IconBadge extends StatelessWidget {
  final IconData icon;
  final double size;

  const _IconBadge({required this.icon, this.size = 42});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: const Color(0xFFE5F5EF),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Icon(icon, size: size * 0.48, color: const Color(0xFF064E52)),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  final String title;

  const _SectionTitle({required this.title});

  @override
  Widget build(BuildContext context) {
    return Text(
      title,
      style: TextStyle(
        color: AminaTheme.textPrimary(context),
        fontSize: 15.5,
        fontWeight: FontWeight.w800,
        letterSpacing: -0.25,
      ),
    );
  }
}

class _DateAction extends StatelessWidget {
  final IconData icon;
  final String title;
  final String value;
  final VoidCallback onTap;

  const _DateAction({
    required this.icon,
    required this.title,
    required this.value,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        constraints: const BoxConstraints(minHeight: 54),
        padding: const EdgeInsetsDirectional.fromSTEB(12, 8, 10, 8),
        decoration: BoxDecoration(
          color: AminaTheme.subtleBg(context),
          borderRadius: BorderRadius.circular(16),
        ),
        child: Row(
          children: [
            Icon(icon, size: 20, color: const Color(0xFF064E52)),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    title,
                    style: TextStyle(
                      color: AminaTheme.textPrimary(context),
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    value,
                    style: TextStyle(
                      color: AminaTheme.textSecondary(context),
                      fontSize: 11.5,
                    ),
                  ),
                ],
              ),
            ),
            Icon(
              Icons.chevron_right_rounded,
              color: AminaTheme.textSecondary(context),
            ),
          ],
        ),
      ),
    );
  }
}
