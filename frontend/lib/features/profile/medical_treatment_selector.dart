import 'package:flutter/material.dart';
import '../../l10n/app_localizations.dart';
import 'medical_profile_choice_policy.dart';

/// Presentation only: "What do you already take?", never "What should you take?"
/// The collapsed list is context-sensitive. All patient declarations remain
/// reachable, including unusual treatments, to avoid losing true information.
class MedicalTreatmentSelector extends StatefulWidget {
  final String? diabetesType;
  final String? selectedTreatment;
  final ValueChanged<String> onSelected;

  const MedicalTreatmentSelector({
    super.key,
    required this.diabetesType,
    required this.selectedTreatment,
    required this.onSelected,
  });

  @override
  State<MedicalTreatmentSelector> createState() =>
      _MedicalTreatmentSelectorState();
}

class _MedicalTreatmentSelectorState extends State<MedicalTreatmentSelector> {
  bool _expanded = false;

  String _copy(BuildContext context, String fr, String en, String ar) {
    return switch (Localizations.localeOf(context).languageCode) {
      'fr' => fr,
      'ar' => ar,
      _ => en,
    };
  }

  String _label(BuildContext context, String type) {
    final l10n = AppLocalizations.of(context)!;
    return switch (type) {
      'insulin' => l10n.treatmentInsulin,
      'tablets' => _copy(context, 'Médicaments déclarés', 'Medicines I take',
          'أدوية أتناولها'),
      'lifestyle' => _copy(context, 'Habitudes de vie',
          'Lifestyle measures', 'نمط الحياة'),
      'other' => _copy(context, 'Autre traitement suivi',
          'Other treatment I take', 'علاج آخر أتناوله'),
      'unknown' => _copy(context, 'Je ne sais pas / plus tard',
          'Not sure / later', 'لا أعرف / لاحقًا'),
      _ => type,
    };
  }

  @override
  Widget build(BuildContext context) {
    final plan = treatmentPresentation(widget.diabetesType);
    final selectedIsSecondary = widget.selectedTreatment != null &&
        plan.onRequest.contains(widget.selectedTreatment);
    final showMore = _expanded || selectedIsSecondary || plan.primary.isEmpty;

    Widget chips(List<String> values) => Wrap(
      spacing: 8,
      runSpacing: 8,
      children: values.map((value) => ChoiceChip(
        key: Key('declared-treatment-$value'),
        label: Text(_label(context, value)),
        selected: widget.selectedTreatment == value,
        onSelected: (_) => widget.onSelected(value),
      )).toList(),
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          _copy(context,
            'Indiquez uniquement ce que vous suivez réellement, sans commencer ou modifier de traitement ici.',
            'Only report what you actually follow. Do not start or change treatment here.',
            'اذكر فقط العلاج الذي تتبعه فعلاً. لا تبدأ أو تغيّر علاجك هنا.',
          ),
          style: Theme.of(context).textTheme.bodySmall,
        ),
        const SizedBox(height: 10),
        if (plan.primary.isNotEmpty) chips(plan.primary),
        if (plan.onRequest.isNotEmpty && !showMore) ...[
          const SizedBox(height: 6),
          TextButton.icon(
            key: const Key('medical-show-other-declarations'),
            onPressed: () => setState(() => _expanded = true),
            icon: const Icon(Icons.expand_more, size: 18),
            label: Text(_copy(context,
              'Je suis un autre traitement / Je préfère répondre plus tard',
              'I follow a different treatment / Answer later',
              'أتبع علاجًا آخر / أجيب لاحقًا',
            )),
          ),
        ],
        if (showMore && plan.onRequest.isNotEmpty) ...[
          if (plan.primary.isNotEmpty) const SizedBox(height: 8),
          chips(plan.onRequest),
        ],
      ],
    );
  }
}
