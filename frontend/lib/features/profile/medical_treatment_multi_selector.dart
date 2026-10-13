import 'package:flutter/material.dart';

import '../../l10n/app_localizations.dart';
import 'medical_treatment_declaration_v1.dart';

/// Isolated D7 widget: activate only after patient-owned persistence is proven.
class MedicalTreatmentMultiSelector extends StatefulWidget {
  final String? diabetesType;
  final D7TreatmentDeclaration value;
  final ValueChanged<D7TreatmentDeclaration> onChanged;

  const MedicalTreatmentMultiSelector({
    super.key,
    required this.diabetesType,
    required this.value,
    required this.onChanged,
  });

  @override
  State<MedicalTreatmentMultiSelector> createState() => _MultiState();
}

class _MultiState extends State<MedicalTreatmentMultiSelector> {
  bool _expanded = false;

  String _copy(BuildContext context, String fr, String en, String ar) =>
      switch (Localizations.localeOf(context).languageCode) {
        'fr' => fr,
        'ar' => ar,
        _ => en,
      };

  String _label(BuildContext context, String code) {
    final l10n = AppLocalizations.of(context)!;
    return switch (code) {
      'insulin' => l10n.treatmentInsulin,
      'oral_meds' => _copy(context, 'Médicaments oraux pris',
          'Oral medicines I take', 'أدوية فموية أتناولها'),
      'lifestyle' => _copy(context, 'Habitudes de vie', 'Lifestyle measures', 'نمط الحياة'),
      'other' => _copy(context, 'Autre traitement suivi',
          'Other treatment I follow', 'علاج آخر أتبعه'),
      _ => code,
    };
  }

  void _toggle(String code, bool selected) {
    final next = [...widget.value.codes];
    if (selected && !next.contains(code)) next.add(code);
    if (!selected) next.remove(code);
    widget.onChanged(D7TreatmentDeclaration(
      next.isEmpty ? D7TreatmentStatus.notAnswered : D7TreatmentStatus.declared,
      next,
    ));
  }

  void _choose(D7TreatmentStatus state) =>
      widget.onChanged(D7TreatmentDeclaration(state, const []));

  @override
  Widget build(BuildContext context) {
    final primary = d7PrimaryOptions(widget.diabetesType);
    final secondary = d7OtherOptions(widget.diabetesType);
    final show = _expanded || primary.isEmpty ||
        widget.value.codes.any(secondary.contains);
    Widget chips(List<String> options) => Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        for (final code in options)
          FilterChip(
            key: Key('d7-treatment-$code'),
            label: Text(_label(context, code)),
            selected: widget.value.codes.contains(code),
            onSelected: (yes) => _toggle(code, yes),
          ),
      ],
    );
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(_copy(context,
            'Déclarez seulement ce que vous suivez déjà, sans changer de traitement ici.',
            'Report only what you already follow. Do not change treatment here.',
            'اذكر فقط ما تتبعه فعلاً، دون تغيير العلاج هنا.')),
        const SizedBox(height: 10),
        if (primary.isNotEmpty) chips(primary),
        if (secondary.isNotEmpty && !show)
          TextButton(
            key: const Key('d7-show-other'),
            onPressed: () => setState(() => _expanded = true),
            child: Text(_copy(context, 'Déclarer un autre traitement',
                'Report another treatment', 'الإبلاغ عن علاج آخر')),
          ),
        if (secondary.isNotEmpty && show) chips(secondary),
        const SizedBox(height: 8),
        Wrap(spacing: 8, runSpacing: 8, children: [
          ChoiceChip(
            key: const Key('d7-unsure'),
            selected: widget.value.state == D7TreatmentStatus.unsure,
            label: Text(_copy(context, 'Je ne sais pas', 'Not sure', 'لا أعرف')),
            onSelected: (_) => _choose(D7TreatmentStatus.unsure),
          ),
          ChoiceChip(
            key: const Key('d7-none'),
            selected: widget.value.state == D7TreatmentStatus.noneDeclared,
            label: Text(_copy(context, 'Aucun traitement déclaré',
                'No treatment to report', 'لا يوجد علاج للإبلاغ عنه')),
            onSelected: (_) => _choose(D7TreatmentStatus.noneDeclared),
          ),
          TextButton(
            key: const Key('d7-later'),
            onPressed: () => _choose(D7TreatmentStatus.notAnswered),
            child: Text(_copy(context, 'Je répondrai plus tard',
                'Answer later', 'سأجيب لاحقًا')),
          ),
        ]),
      ],
    );
  }
}
