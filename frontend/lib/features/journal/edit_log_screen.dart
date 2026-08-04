import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:drift/drift.dart' as drift;
import '../../data/drift/database.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/amina_button.dart';

class EditLogScreen extends StatefulWidget {
  final int logId;
  const EditLogScreen({super.key, required this.logId});

  @override
  State<EditLogScreen> createState() => _EditLogScreenState();
}

class _EditLogScreenState extends State<EditLogScreen> {
  bool _loading = true;

  late final TextEditingController _glucoseController;
  double _glucoseValue = 110.0;
  double _insulinDose = 0.0;
  String _mealType = 'À jeun';
  bool _isRamadanMode = false;

  final List<String> _mealTypes = [
    'À jeun',
    'Post-prandial',
    'Avant le coucher',
    'En-cas',
    'Libre',
    'Iftar',
    'Suhoor',
    'Nuit',
    'Avant Jeûne',
  ];

  @override
  void initState() {
    super.initState();
    _glucoseController = TextEditingController();
    _loadLog();
  }

  @override
  void dispose() {
    _glucoseController.dispose();
    super.dispose();
  }

  Future<void> _loadLog() async {
    final db = context.read<AppDatabase>();
    final profile = context
        .read<PatientProfileData?>(); // read before async gap
    final log = await db.getLogById(widget.logId);
    if (log != null) {
      final unit = profile?.unitPreference ?? 'mg/dL';
      final displayValue = unit == 'mmol/L'
          ? log.bloodSugar / 18.0
          : log.bloodSugar;
      setState(() {
        _glucoseValue = displayValue;
        _glucoseController.text = displayValue.toStringAsFixed(
          unit == 'mmol/L' ? 1 : 0,
        );
        _insulinDose = log.insulinUnits ?? 0.0;
        _mealType = log.mealType ?? 'À jeun';
        _isRamadanMode = log.ramadanMode;
        _loading = false;
      });
    } else {
      if (mounted) context.pop();
    }
  }

  @override
  Widget build(BuildContext context) {
    final profile = context.watch<PatientProfileData?>();
    final unit = profile?.unitPreference ?? 'mg/dL';

    return Scaffold(
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : Column(
              children: [
                _buildHeader(context),
                Expanded(
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.symmetric(horizontal: 24),
                    child: Column(
                      children: [
                        const SizedBox(height: 40),
                        _buildGlucoseInput(unit),
                        const SizedBox(height: 40),
                        _buildMealTypeSelector(),
                        const SizedBox(height: 40),
                        _buildInsulinSection(),
                        const SizedBox(height: 40),
                        _buildRamadanToggle(),
                        const SizedBox(height: 60),
                        AminaButton(
                          label: 'Enregistrer les modifications',
                          onPressed: _saveChanges,
                        ),
                        const SizedBox(height: 40),
                      ],
                    ),
                  ),
                ),
              ],
            ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsetsDirectional.fromSTEB(12, 16, 24, 8),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            IconButton(
              onPressed: () => context.pop(),
              icon: const Icon(Icons.arrow_back_ios_new, size: 20),
            ),
            const Text(
              'Modifier la mesure',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w900,
                letterSpacing: -0.5,
              ),
            ),
            const SizedBox(width: 48),
          ],
        ),
      ),
    );
  }

  Widget _buildGlucoseInput(String unit) {
    return Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.baseline,
          textBaseline: TextBaseline.alphabetic,
          children: [
            SizedBox(
              width: 140,
              child: TextField(
                controller: _glucoseController,
                keyboardType: TextInputType.number,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 80,
                  fontWeight: FontWeight.w900,
                  height: 1.0,
                  letterSpacing: -4,
                ),
                decoration: const InputDecoration(
                  border: InputBorder.none,
                  contentPadding: EdgeInsets.zero,
                ),
                onChanged: (val) {
                  final d = double.tryParse(val);
                  if (d != null) setState(() => _glucoseValue = d);
                },
              ),
            ),
            const SizedBox(width: 8),
            Text(
              unit,
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.w800,
                color: AminaTheme.textMuted.withValues(alpha: 0.5),
              ),
            ),
          ],
        ),
        Container(
          width: 120,
          height: 3,
          decoration: BoxDecoration(
            gradient: AminaTheme.heroGradient,
            borderRadius: BorderRadius.circular(2),
          ),
        ),
      ],
    );
  }

  Widget _buildMealTypeSelector() {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: _mealTypes.map((type) {
          final isSelected = _mealType == type;
          return Padding(
            padding: const EdgeInsetsDirectional.only(end: 12),
            child: InkWell(
              onTap: () => setState(() => _mealType = type),
              borderRadius: BorderRadius.circular(100),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                padding: const EdgeInsets.symmetric(
                  horizontal: 20,
                  vertical: 10,
                ),
                decoration: BoxDecoration(
                  color: isSelected ? AminaTheme.teal500 : AminaTheme.ink100,
                  borderRadius: BorderRadius.circular(100),
                ),
                child: Text(
                  type,
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: isSelected ? FontWeight.w900 : FontWeight.w600,
                    color: isSelected ? Colors.white : AminaTheme.textMuted,
                  ),
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildInsulinSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(
              Icons.colorize_outlined,
              size: 20,
              color: AminaTheme.primaryTeal.withValues(alpha: 0.7),
            ),
            const SizedBox(width: 12),
            const Text(
              "DOSE D'INSULINE",
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w900,
                letterSpacing: 0.5,
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            _stepperBtn(Icons.remove, () {
              if (_insulinDose > 0) setState(() => _insulinDose--);
            }),
            const SizedBox(width: 32),
            Column(
              children: [
                Text(
                  _insulinDose.toInt().toString(),
                  style: const TextStyle(
                    fontSize: 56,
                    fontWeight: FontWeight.w900,
                    height: 1.0,
                  ),
                ),
                const Text(
                  'UNITÉS',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w800,
                    color: AminaTheme.textMuted,
                  ),
                ),
              ],
            ),
            const SizedBox(width: 32),
            _stepperBtn(Icons.add, () => setState(() => _insulinDose++)),
          ],
        ),
      ],
    );
  }

  Widget _stepperBtn(IconData icon, VoidCallback onTap) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(100),
      child: Container(
        width: 48,
        height: 48,
        decoration: const BoxDecoration(
          color: AminaTheme.ink100,
          shape: BoxShape.circle,
        ),
        child: Icon(icon, size: 24),
      ),
    );
  }

  Widget _buildRamadanToggle() {
    return InkWell(
      onTap: () => setState(() => _isRamadanMode = !_isRamadanMode),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
        decoration: BoxDecoration(
          color: _isRamadanMode ? const Color(0xFF0D1A17) : AminaTheme.ink50,
          borderRadius: BorderRadius.circular(24),
          border: Border.all(
            color: _isRamadanMode
                ? AminaTheme.primaryTeal.withValues(alpha: 0.3)
                : Colors.transparent,
          ),
        ),
        child: Row(
          children: [
            Icon(
              _isRamadanMode ? Icons.nightlight_round : Icons.wb_sunny_outlined,
              color: _isRamadanMode ? Colors.amber : AminaTheme.textMuted,
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Mode Ramadan',
                    style: TextStyle(
                      fontWeight: FontWeight.w700,
                      fontSize: 14,
                      color: _isRamadanMode ? Colors.white : AminaTheme.ink900,
                    ),
                  ),
                  Text(
                    _isRamadanMode ? 'Activé — horaires adaptés' : 'Désactivé',
                    style: TextStyle(
                      fontSize: 12,
                      color: _isRamadanMode
                          ? Colors.white70
                          : AminaTheme.ink500,
                    ),
                  ),
                ],
              ),
            ),
            Switch(
              value: _isRamadanMode,
              onChanged: (v) => setState(() => _isRamadanMode = v),
              activeThumbColor: AminaTheme.primaryTeal,
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _saveChanges() async {
    final db = context.read<AppDatabase>();
    final profile = context.read<PatientProfileData?>();
    final unit = profile?.unitPreference ?? 'mg/dL';
    final bloodSugarMgdl = unit == 'mmol/L'
        ? _glucoseValue * 18.0
        : _glucoseValue;

    await db.updateLog(
      widget.logId,
      LogEntriesCompanion(
        bloodSugar: drift.Value(bloodSugarMgdl),
        insulinUnits: drift.Value(_insulinDose > 0 ? _insulinDose : null),
        mealType: drift.Value(_mealType),
        ramadanMode: drift.Value(_isRamadanMode),
        syncStatus: const drift.Value('pending'),
      ),
    );
    if (!mounted) return;
    context.pop();
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Mesure mise à jour'),
        backgroundColor: AminaTheme.successEmerald,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }
}
