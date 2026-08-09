import 'package:drift/drift.dart' as drift;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:uuid/uuid.dart';

import '../../../core/data/culinary_data.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/drift/database.dart';

/// Truthful metabolic-event capture.
///
/// This surface records what happened. It intentionally does not calculate an
/// insulin dose, classify a recorded dose, fabricate nutritional quantities,
/// invent numeric glycaemic-index values, or request a generative verdict after
/// saving. Deterministic low-glucose safety remains upstream of persistence.
class AddLogSheet extends StatefulWidget {
  final bool isPage;

  const AddLogSheet({super.key, this.isPage = false});

  @override
  State<AddLogSheet> createState() => _AddLogSheetState();
}

class _AddLogSheetState extends State<AddLogSheet> {
  final TextEditingController _glucoseController = TextEditingController();
  final TextEditingController _insulinController = TextEditingController();
  final TextEditingController _foodSearchController = TextEditingController();
  final TextEditingController _mealNoteController = TextEditingController();

  String _mealType = 'À jeun';
  DateTime _selectedTime = DateTime.now();
  bool _detailsExpanded = false;
  bool _saving = false;
  bool _isSick = false;
  bool _isStressed = false;
  bool _isActive = false;
  bool _badSleep = false;
  bool _isRamadanMode = false;
  String _foodSearch = '';
  final List<CulinaryItem> _selectedFoods = <CulinaryItem>[];

  static const List<String> _mealTypesNormal = <String>[
    'À jeun',
    'Petit-déjeuner',
    'Déjeuner',
    'Dîner',
    'Collation',
    'Sport',
  ];

  static const List<String> _mealTypesRamadan = <String>[
    'Iftar',
    'Suhoor',
    'Nuit',
    'Avant Jeûne',
    'Libre',
  ];

  @override
  void dispose() {
    _glucoseController.dispose();
    _insulinController.dispose();
    _foodSearchController.dispose();
    _mealNoteController.dispose();
    super.dispose();
  }

  double? _displayGlucose() {
    final raw = _glucoseController.text.trim().replaceAll(',', '.');
    return double.tryParse(raw);
  }

  double? _mgdlGlucose(String unit) {
    final value = _displayGlucose();
    if (value == null) return null;
    return unit == 'mmol/L' ? value * 18.0 : value;
  }

  bool get _hasUnsavedData =>
      _glucoseController.text.trim().isNotEmpty ||
      _insulinController.text.trim().isNotEmpty ||
      _mealType != 'À jeun' ||
      _selectedFoods.isNotEmpty ||
      _mealNoteController.text.trim().isNotEmpty ||
      _isSick ||
      _isStressed ||
      _isActive ||
      _badSleep ||
      _isRamadanMode;

  String _timeLabel() {
    final now = DateTime.now();
    final sameDay = _selectedTime.year == now.year &&
        _selectedTime.month == now.month &&
        _selectedTime.day == now.day;
    final hh = _selectedTime.hour.toString().padLeft(2, '0');
    final mm = _selectedTime.minute.toString().padLeft(2, '0');
    if (sameDay) return "Aujourd'hui · $hh:$mm";
    final dd = _selectedTime.day.toString().padLeft(2, '0');
    final mo = _selectedTime.month.toString().padLeft(2, '0');
    return '$dd/$mo · $hh:$mm';
  }

  Future<bool> _confirmLeave() async {
    if (!_hasUnsavedData) return true;
    final leave = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Abandonner la saisie ?'),
        content: const Text('Les données non enregistrées seront perdues.'),
        actions: <Widget>[
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: const Text('Continuer'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, true),
            child: const Text('Abandonner'),
          ),
        ],
      ),
    );
    return leave == true;
  }

  void _close() {
    if (widget.isPage) {
      GoRouter.of(context).go('/dashboard');
    } else {
      Navigator.maybePop(context);
    }
  }

  @override
  Widget build(BuildContext context) {
    final db = context.read<AppDatabase>();
    final profile = context.watch<PatientProfileData?>();
    final unit = profile?.unitPreference ?? 'mg/dL';
    final isWide = MediaQuery.sizeOf(context).width >= 720;

    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) async {
        if (didPop) return;
        if (await _confirmLeave() && mounted) _close();
      },
      child: ColoredBox(
        color: AminaTheme.bg(context),
        child: SafeArea(
          child: Stack(
            children: <Widget>[
              SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(20, 8, 20, 112),
                child: Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 820),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: <Widget>[
                        _header(),
                        const SizedBox(height: 20),
                        _glucoseCard(unit),
                        const SizedBox(height: 20),
                        _mealTypeSelector(),
                        if (!isWide && !_detailsExpanded) ...<Widget>[
                          const SizedBox(height: 18),
                          _detailsButton(),
                        ],
                        if (isWide || _detailsExpanded) ...<Widget>[
                          const SizedBox(height: 22),
                          _timeRow(),
                          if (_mealType != 'À jeun') ...<Widget>[
                            const SizedBox(height: 22),
                            _foodSection(),
                          ],
                          const SizedBox(height: 22),
                          _insulinSection(),
                          const SizedBox(height: 22),
                          _contextSection(),
                          const SizedBox(height: 22),
                          _ramadanSection(),
                        ],
                      ],
                    ),
                  ),
                ),
              ),
              PositionedDirectional(
                start: 0,
                end: 0,
                bottom: 0,
                child: _saveBar(db, unit),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _header() {
    return Row(
      children: <Widget>[
        IconButton(
          tooltip: 'Retour',
          onPressed: () async {
            if (await _confirmLeave() && mounted) _close();
          },
          icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 18),
        ),
        const SizedBox(width: 6),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                'Nouvelle mesure',
                style: TextStyle(
                  color: AminaTheme.textPrimary(context),
                  fontSize: 22,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                'Enregistre ce qui vient de se passer.',
                style: TextStyle(
                  color: AminaTheme.textSecondary(context),
                  fontSize: 13,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _glucoseCard(String unit) {
    final mgdl = _mgdlGlucose(unit);
    final isLow = mgdl != null && mgdl < 70;

    return Semantics(
      container: true,
      label: 'Saisie de la glycémie',
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: isLow
              ? const Color(0xFFFFF7ED)
              : AminaTheme.subtleBg(context),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isLow
                ? const Color(0xFFF97316)
                : AminaTheme.divider(context),
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(
              'GLYCÉMIE',
              style: TextStyle(
                color: AminaTheme.textSecondary(context),
                fontSize: 11,
                fontWeight: FontWeight.w800,
                letterSpacing: .7,
              ),
            ),
            const SizedBox(height: 12),
            Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: <Widget>[
                Expanded(
                  child: TextField(
                    key: const Key('glucose-input'),
                    controller: _glucoseController,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    inputFormatters: <TextInputFormatter>[
                      FilteringTextInputFormatter.allow(RegExp(r'[0-9,.]')),
                    ],
                    style: TextStyle(
                      color: AminaTheme.textPrimary(context),
                      fontSize: 48,
                      fontWeight: FontWeight.w800,
                    ),
                    decoration: const InputDecoration(
                      hintText: '—',
                      border: InputBorder.none,
                      isDense: true,
                    ),
                    onChanged: (_) => setState(() {}),
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: Text(
                    unit,
                    style: TextStyle(
                      color: AminaTheme.textSecondary(context),
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),
            if (mgdl == null)
              Text(
                'Aucune valeur n’est supposée avant ta saisie.',
                style: TextStyle(
                  color: AminaTheme.textSecondary(context),
                  fontSize: 12,
                ),
              )
            else if (isLow)
              const Text(
                'Valeur basse détectée — vérifie la mesure et suis le message de sécurité lors de l’enregistrement.',
                style: TextStyle(
                  color: Color(0xFFC2410C),
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              )
            else
              Text(
                'La cible personnelle n’est pas déduite de cette valeur seule.',
                style: TextStyle(
                  color: AminaTheme.textSecondary(context),
                  fontSize: 12,
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _mealTypeSelector() {
    final values = _isRamadanMode ? _mealTypesRamadan : _mealTypesNormal;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        _sectionLabel('MOMENT DU REPAS'),
        const SizedBox(height: 10),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: values.map((type) {
            final selected = _mealType == type;
            return ChoiceChip(
              label: Text(type),
              selected: selected,
              onSelected: (_) => setState(() {
                _mealType = type;
                _selectedFoods.clear();
                _foodSearch = '';
                _foodSearchController.clear();
              }),
            );
          }).toList(),
        ),
      ],
    );
  }

  Widget _detailsButton() {
    return OutlinedButton.icon(
      onPressed: () => setState(() => _detailsExpanded = true),
      icon: const Icon(Icons.expand_more_rounded),
      label: const Text('+ Détails : repas, insuline prise, contexte…'),
      style: OutlinedButton.styleFrom(
        minimumSize: const Size.fromHeight(50),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      ),
    );
  }

  Widget _timeRow() {
    return InkWell(
      borderRadius: BorderRadius.circular(14),
      onTap: _pickDateTime,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: AminaTheme.subtleBg(context),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AminaTheme.divider(context)),
        ),
        child: Row(
          children: <Widget>[
            const Icon(Icons.schedule_outlined, size: 18),
            const SizedBox(width: 10),
            Expanded(child: Text(_timeLabel())),
            const Icon(Icons.edit_outlined, size: 16),
          ],
        ),
      ),
    );
  }

  Future<void> _pickDateTime() async {
    final date = await showDatePicker(
      context: context,
      initialDate: _selectedTime,
      firstDate: DateTime.now().subtract(const Duration(days: 90)),
      lastDate: DateTime.now(),
    );
    if (date == null || !mounted) return;
    final time = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(_selectedTime),
    );
    if (time == null || !mounted) return;
    setState(() {
      _selectedTime = DateTime(
        date.year,
        date.month,
        date.day,
        time.hour,
        time.minute,
      );
    });
  }

  Widget _foodSection() {
    final source = _foodSearch.isEmpty
        ? foodsForMeal(_mealType)
        : universalFoods
            .where((item) => item.label
                .toLowerCase()
                .contains(_foodSearch.toLowerCase()))
            .toList();
    final visible = source.take(20).toList();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        _sectionLabel('CE QUE TU AS MANGÉ'),
        const SizedBox(height: 6),
        Text(
          'Ajoute uniquement les aliments réellement consommés. Aucune quantité nutritionnelle n’est déduite de leur catégorie.',
          style: TextStyle(
            color: AminaTheme.textSecondary(context),
            fontSize: 12,
            height: 1.35,
          ),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _foodSearchController,
          decoration: const InputDecoration(
            prefixIcon: Icon(Icons.search),
            hintText: 'Rechercher un aliment',
            border: OutlineInputBorder(),
          ),
          onChanged: (value) => setState(() => _foodSearch = value.trim()),
        ),
        if (_selectedFoods.isNotEmpty) ...<Widget>[
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: _selectedFoods
                .map(
                  (item) => InputChip(
                    label: Text(item.label),
                    onDeleted: () => setState(() => _selectedFoods.remove(item)),
                  ),
                )
                .toList(),
          ),
        ],
        const SizedBox(height: 12),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: visible.map((item) {
            final selected = _selectedFoods.any((e) => e.id == item.id);
            return FilterChip(
              label: Text(item.label),
              selected: selected,
              onSelected: (value) => setState(() {
                if (value) {
                  if (!selected) _selectedFoods.add(item);
                } else {
                  _selectedFoods.removeWhere((e) => e.id == item.id);
                }
              }),
            );
          }).toList(),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _mealNoteController,
          minLines: 2,
          maxLines: 4,
          decoration: const InputDecoration(
            labelText: 'Note facultative',
            hintText: 'Préparation, quantité approximative, boisson…',
            border: OutlineInputBorder(),
          ),
        ),
      ],
    );
  }

  Widget _insulinSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        _sectionLabel('INSULINE PRISE'),
        const SizedBox(height: 6),
        Text(
          'Renseigne uniquement une dose déjà administrée. IAmina ne calcule ni ne juge la dose ici.',
          style: TextStyle(
            color: AminaTheme.textSecondary(context),
            fontSize: 12,
            height: 1.35,
          ),
        ),
        const SizedBox(height: 10),
        TextField(
          key: const Key('insulin-taken-input'),
          controller: _insulinController,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          inputFormatters: <TextInputFormatter>[
            FilteringTextInputFormatter.allow(RegExp(r'[0-9,.]')),
          ],
          decoration: const InputDecoration(
            labelText: 'Dose réellement prise',
            suffixText: 'U',
            hintText: 'Facultatif',
            border: OutlineInputBorder(),
          ),
        ),
      ],
    );
  }

  Widget _contextSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        _sectionLabel('CONTEXTE FACULTATIF'),
        const SizedBox(height: 10),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: <Widget>[
            FilterChip(
              label: const Text('Malade'),
              selected: _isSick,
              onSelected: (v) => setState(() => _isSick = v),
            ),
            FilterChip(
              label: const Text('Stress inhabituel'),
              selected: _isStressed,
              onSelected: (v) => setState(() => _isStressed = v),
            ),
            FilterChip(
              label: const Text('Activité physique'),
              selected: _isActive,
              onSelected: (v) => setState(() => _isActive = v),
            ),
            FilterChip(
              label: const Text('Mauvais sommeil'),
              selected: _badSleep,
              onSelected: (v) => setState(() => _badSleep = v),
            ),
          ],
        ),
      ],
    );
  }

  Widget _ramadanSection() {
    return SwitchListTile.adaptive(
      contentPadding: EdgeInsets.zero,
      title: const Text('Mode Ramadan'),
      subtitle: const Text('Adapte uniquement les libellés de repas pour cette saisie.'),
      value: _isRamadanMode,
      onChanged: (value) => setState(() {
        _isRamadanMode = value;
        _mealType = value ? 'Iftar' : 'À jeun';
        _selectedFoods.clear();
      }),
    );
  }

  Widget _sectionLabel(String label) {
    return Text(
      label,
      style: TextStyle(
        color: AminaTheme.textSecondary(context),
        fontSize: 11,
        fontWeight: FontWeight.w800,
        letterSpacing: .7,
      ),
    );
  }

  Widget _saveBar(AppDatabase db, String unit) {
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 14),
      decoration: BoxDecoration(
        color: AminaTheme.bg(context),
        border: Border(top: BorderSide(color: AminaTheme.divider(context))),
      ),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 820),
          child: FilledButton.icon(
            onPressed: _saving ? null : () => _saveLog(db, unit),
            icon: _saving
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.check_rounded),
            label: Text(_saving ? 'Enregistrement…' : 'Enregistrer la mesure'),
            style: FilledButton.styleFrom(
              minimumSize: const Size.fromHeight(54),
              backgroundColor: AminaTheme.teal600,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _saveLog(AppDatabase db, String unit) async {
    final glucose = _displayGlucose();
    final mgdl = _mgdlGlucose(unit);
    if (glucose == null || mgdl == null || glucose <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Veuillez saisir une glycémie valide.'),
          behavior: SnackBarBehavior.floating,
        ),
      );
      return;
    }

    // Preserve the existing deterministic low-glucose gate. It runs before
    // persistence and never delegates the safety decision to a generative model.
    if (mgdl < 70) {
      final proceed = await showDialog<bool>(
        context: context,
        barrierDismissible: false,
        builder: (dialogContext) => AlertDialog(
          title: const Text('Valeur basse détectée'),
          content: Text(
            'La mesure enregistrée correspond à ${mgdl.toInt()} mg/dL. '
            'Vérifie la mesure et applique le plan de sécurité qui t’a été donné par ton équipe soignante.',
          ),
          actions: <Widget>[
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: const Text('Revenir à la saisie'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(dialogContext, true),
              child: const Text('Enregistrer quand même'),
            ),
          ],
        ),
      );
      if (proceed != true || !mounted) return;
    }

    final insulinRaw = _insulinController.text.trim().replaceAll(',', '.');
    final insulin = insulinRaw.isEmpty ? 0.0 : double.tryParse(insulinRaw);
    if (insulin == null || insulin < 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('La dose d’insuline saisie n’est pas valide.'),
          behavior: SnackBarBehavior.floating,
        ),
      );
      return;
    }

    setState(() => _saving = true);
    try {
      final foods = _selectedFoods.map((item) => item.label).join(', ');
      final note = _mealNoteController.text.trim();
      final description = <String>[foods, note]
          .where((part) => part.isNotEmpty)
          .join(' — ');

      await db.into(db.logEntries).insert(
        LogEntriesCompanion.insert(
          createdAt: DateTime.now(),
          bloodSugar: mgdl,
          insulinUnits: drift.Value(insulin),
          mealType: drift.Value(_mealType),
          mealDescription:
              drift.Value(description.isEmpty ? null : description),
          clientUuid: const Uuid().v4(),
          loggedAt: drift.Value(_selectedTime),
          ramadanMode: drift.Value(_isRamadanMode),
          isSick: drift.Value(_isSick),
          isStressed: drift.Value(_isStressed),
          isTired: const drift.Value(false),
          isActive: drift.Value(_isActive),
          sleepQuality: drift.Value(_badSleep ? 'bad' : null),
          fatigueLevel: const drift.Value(null),
        ),
      );

      if (!mounted) return;
      HapticFeedback.mediumImpact();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Mesure enregistrée.'),
          behavior: SnackBarBehavior.floating,
        ),
      );
      _close();
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }
}
