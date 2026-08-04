import 'dart:convert';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import 'package:uuid/uuid.dart';
import 'package:drift/drift.dart' as drift;
import 'package:image_picker/image_picker.dart';
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';
import 'package:record/record.dart';
import '../../../data/drift/database.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/data/culinary_data.dart';
import '../../../core/clinical/glucose_ocr_shield.dart';
import '../../../services/api_client.dart';

// ── Portion model ─────────────────────────────────────────────────────────────

enum _Portion { petit, moyen, grand }

extension _PortionExt on _Portion {
  String get label => switch (this) {
    _Portion.petit => 'petit',
    _Portion.moyen => 'moyen',
    _Portion.grand => 'grand',
  };
  int carbsFor(String glycemic) {
    final base = switch (glycemic) { 'low' => 10, 'medium' => 25, _ => 40 };
    final mult = switch (this) { _Portion.petit => 0.5, _Portion.moyen => 1.0, _Portion.grand => 1.5 };
    return (base * mult).round();
  }
}

class _SelectedFood {
  final CulinaryItem item;
  _Portion portion = _Portion.moyen;
  _SelectedFood({required this.item});
}

class AddLogSheet extends StatefulWidget {
  final bool isPage;
  const AddLogSheet({super.key, this.isPage = false});

  @override
  State<AddLogSheet> createState() => _AddLogSheetState();
}

class _AddLogSheetState extends State<AddLogSheet> {
  double _glucoseValue = 110.0;
  double _insulinDose  = 0.0;
  static const double _insulinStep = 0.5;
  String _mealType = 'À jeun';
  DateTime _selectedTime = DateTime.now();
  bool _isRamadanMode = false;

  // Food selection
  String _foodSearch = '';
  final TextEditingController _searchController = TextEditingController();
  final List<_SelectedFood> _selectedFoods = [];
  List<CulinaryItem> _recentFoods = [];
  final TextEditingController _mealNoteController = TextEditingController();

  // Health state
  bool _isSick = false;
  bool _isStressed = false;
  bool _isActive = false;
  String? _sleepQuality;
  int? _fatigueLevel;
  bool _isFirstLogToday = true;
  bool _showHealthExpanded = false;

  // Express mode — mobile default: only glucose + meal type visible.
  // User taps "+ Détails" to expand insulin / food / health / Ramadan.
  // Wide layout (≥720px) always shows full detail (enough screen space).
  bool _expressMode = true;

  // Manual input
  final TextEditingController _manualController = TextEditingController();
  bool _saving      = false;
  bool _ocrScanning  = false; // true while ML Kit / Gemini OCR is processing
  bool _mealScanning = false; // true while Gemini Vision is analysing meal photo

  // Vocal input for meal note
  final AudioRecorder _audioRecorder = AudioRecorder();
  bool _noteRecording    = false; // mic held for meal note dictation
  bool _noteTranscribing = false; // STT in flight
  final List<Uint8List> _noteAudioChunks = [];

  final List<String> _mealTypesNormal  = ['À jeun', 'Petit-déjeuner', 'Déjeuner', 'Dîner', 'Collation', 'Sport'];
  final List<String> _mealTypesRamadan = ['Iftar', 'Suhoor', 'Nuit', 'Avant Jeûne', 'Libre'];

  // ── Color helpers ─────────────────────────────────────────────────────────────

  static Color _mealColor(String type) => switch (type) {
    'Petit-déjeuner' || 'Suhoor'      => const Color(0xFFD97706),
    'Déjeuner'       || 'Iftar'       => const Color(0xFF059669),
    'Dîner'          || 'Nuit'        => const Color(0xFF4F46E5),
    'Collation'      || 'Avant Jeûne' => const Color(0xFFEA580C),
    'Sport'                           => const Color(0xFF7C3AED),
    _                                 => const Color(0xFF64748B),
  };

  Color _glucoseColor(double val) {
    if (val < 54)   return const Color(0xFFDC2626);
    if (val < 70)   return const Color(0xFFF97316);
    if (val <= 180) return AminaTheme.teal500;
    if (val <= 250) return const Color(0xFFF59E0B);
    return const Color(0xFFDC2626);
  }

  Color _glucoseBg(double val) {
    if (val < 70)   return const Color(0xFFFEF2F2);
    if (val <= 180) return const Color(0xFFECFBF6);
    if (val <= 250) return const Color(0xFFFEF7E6);
    return const Color(0xFFFEE2E2);
  }

  String _glucoseLabel(double val) {
    if (val < 54)   return 'Hypoglycémie sévère';
    if (val < 70)   return 'Hypoglycémie';
    if (val <= 180) return 'Dans la cible';
    if (val <= 250) return 'Hyperglycémie modérée';
    return 'Hyperglycémie sévère';
  }

  Color _insulinColor(double dose) {
    if (dose == 0)  return AminaTheme.textSecondary(context);
    if (dose <= 6)  return const Color(0xFF059669);
    if (dose <= 12) return const Color(0xFFF59E0B);
    if (dose <= 20) return const Color(0xFFEA580C);
    return const Color(0xFFDC2626);
  }

  String _insulinRiskLabel(double dose) {
    if (dose == 0)  return 'Aucune dose';
    if (dose <= 6)  return 'Zone normale';
    if (dose <= 12) return 'Dose standard';
    if (dose <= 20) return 'Dose élevée';
    return 'Dose critique';
  }

  Color _giColor(String gi) => switch (gi) {
    'low'    => const Color(0xFF10B981),
    'medium' => const Color(0xFFF59E0B),
    _        => const Color(0xFFEF4444),
  };

  String _timeLabel() {
    final now = DateTime.now();
    final isToday     = _selectedTime.year == now.year && _selectedTime.month == now.month && _selectedTime.day == now.day;
    final isYesterday = _selectedTime.year == now.year && _selectedTime.month == now.month && _selectedTime.day == now.day - 1;
    final hhmm = '${_selectedTime.hour.toString().padLeft(2, '0')}:${_selectedTime.minute.toString().padLeft(2, '0')}';
    if (isToday)     return 'Aujourd\'hui · $hhmm';
    if (isYesterday) return 'Hier · $hhmm';
    return '${_selectedTime.day.toString().padLeft(2, '0')}/${_selectedTime.month.toString().padLeft(2, '0')} · $hhmm';
  }

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _checkFirstLogToday();
      _loadRecentFoods();
    });
  }

  Future<void> _checkFirstLogToday() async {
    if (!mounted) return;
    final db = context.read<AppDatabase>();
    final today = DateTime.now();
    final startOfDay = DateTime(today.year, today.month, today.day);
    final rows = await (db.select(db.logEntries)
      ..where((t) => t.createdAt.isBiggerOrEqualValue(startOfDay)))
      .get();
    if (mounted) setState(() => _isFirstLogToday = rows.isEmpty);
  }

  Future<void> _loadRecentFoods() async {
    if (!mounted) return;
    final db = context.read<AppDatabase>();
    final cutoff = DateTime.now().subtract(const Duration(days: 30));
    final rows = await (db.select(db.logEntries)
      ..where((t) => t.mealType.equals(_mealType))
      ..where((t) => t.createdAt.isBiggerOrEqualValue(cutoff))
      ..orderBy([(t) => drift.OrderingTerm(expression: t.loggedAt, mode: drift.OrderingMode.desc)])
      ..limit(40))
      .get();

    final seen = <String>{};
    final matched = <CulinaryItem>[];
    for (final row in rows) {
      if (row.mealDescription == null) continue;
      for (final label in row.mealDescription!.split(',')) {
        final clean = label.split('(').first.trim();
        if (clean.isEmpty || seen.contains(clean)) continue;
        final found = universalFoods.where((f) =>
          f.label.toLowerCase() == clean.toLowerCase()).firstOrNull;
        if (found != null) {
          seen.add(clean);
          matched.add(found);
          if (matched.length >= 7) break;
        }
      }
      if (matched.length >= 7) break;
    }
    if (mounted) setState(() => _recentFoods = matched);
  }

  // ── Vocal input for meal note ─────────────────────────────────────────────

  Future<void> _toggleNoteRecording(ApiClient api) async {
    if (_noteRecording) {
      // Stop and transcribe
      await _audioRecorder.stop();
      setState(() { _noteRecording = false; _noteTranscribing = true; });

      final totalLen = _noteAudioChunks.fold<int>(0, (s, c) => s + c.length);
      final bytes = Uint8List(totalLen);
      var off = 0;
      for (final chunk in _noteAudioChunks) {
        bytes.setRange(off, off + chunk.length, chunk);
        off += chunk.length;
      }
      _noteAudioChunks.clear();

      if (bytes.isNotEmpty) {
        const mime = kIsWeb ? 'audio/webm' : 'audio/mp4';
        final transcript = await api.transcribeAudio(bytes, mime);
        if (mounted && transcript != null && transcript.isNotEmpty) {
          setState(() {
            _mealNoteController.text =
                _mealNoteController.text.isEmpty ? transcript : '${_mealNoteController.text} $transcript';
          });
        }
      }
      if (mounted) setState(() => _noteTranscribing = false);
      return;
    }

    // Start recording
    final hasPermission = await _audioRecorder.hasPermission();
    if (!hasPermission) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Accès au micro refusé — vérifie les permissions'),
          behavior: SnackBarBehavior.floating,
        ));
      }
      return;
    }
    _noteAudioChunks.clear();
    final stream = await _audioRecorder.startStream(const RecordConfig(
      encoder: AudioEncoder.aacLc,
      sampleRate: 16000,
      numChannels: 1,
    ));
    stream.listen((chunk) => _noteAudioChunks.add(chunk));
    if (mounted) setState(() => _noteRecording = true);
  }

  @override
  void dispose() {
    _manualController.dispose();
    _mealNoteController.dispose();
    _searchController.dispose();
    _audioRecorder.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final db      = context.read<AppDatabase>();
    final profile = context.watch<PatientProfileData?>();
    final unit    = profile?.unitPreference ?? 'mg/dL';
    final isWide  = MediaQuery.of(context).size.width >= 720;

    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) async {
        if (didPop) return;
        // In express mode, only glucose input counts as "dirty".
        // In detailed mode, any touched field counts.
        final hasData = _expressMode
            ? _manualController.text.isNotEmpty
            : (_manualController.text.isNotEmpty || _insulinDose != 0 ||
               _mealType != 'À jeun' || _selectedFoods.isNotEmpty ||
               _mealNoteController.text.isNotEmpty);
        if (!hasData) {
          if (widget.isPage) { GoRouter.of(context).go('/dashboard'); }
          else { Navigator.pop(context); }
          return;
        }
        final leave = await showDialog<bool>(
          context: context,
          builder: (_) => AlertDialog(
            title: const Text('Abandonner la saisie ?'),
            content: const Text('Les données non enregistrées seront perdues.'),
            actions: [
              TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Continuer')),
              TextButton(
                onPressed: () => Navigator.pop(context, true),
                child: Text('Abandonner', style: TextStyle(color: Colors.red.shade700)),
              ),
            ],
          ),
        );
        if (leave == true && context.mounted) {
          if (widget.isPage) { GoRouter.of(context).go('/dashboard'); }
          else { Navigator.pop(context); }
        }
      },
      child: Container(
        color: AminaTheme.bg(context),
        child: Stack(
          children: [
            SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(0, 0, 0, 120),
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 760),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 28),
                    child: isWide
                        ? _buildWideLayout(unit, db)
                        : _buildNarrowLayout(unit, db),
                  ),
                ),
              ),
            ),
            Positioned(
              left: 0, right: 0, bottom: 0,
              child: _buildSaveBar(db, context),
            ),
          ],
        ),
      ),
    );
  }

  // ── Wide layout (desktop) ─────────────────────────────────────────────────────

  Widget _buildWideLayout(String unit, AppDatabase db) {
    return Column(
      children: [
        _buildHeader(context),
        const SizedBox(height: 28),
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Left column: glucose + moment + time
            Expanded(
              flex: 5,
              child: Column(children: [
                _buildGlucoseCard(unit),
                const SizedBox(height: 24),
                _buildMealTypeSelector(),
                const SizedBox(height: 20),
                _buildTimeRow(context),
                const SizedBox(height: 20),
                _buildInsulinSection(),
              ]),
            ),
            const SizedBox(width: 28),
            // Right column: food + health
            Expanded(
              flex: 6,
              child: Column(children: [
                if (_mealType != 'À jeun') ...[
                  _buildCompositionSection(),
                  const SizedBox(height: 24),
                ],
                _buildHealthSection(),
                const SizedBox(height: 20),
                _buildRamadanToggle(),
                const SizedBox(height: 20),
                _buildIAminaTeaser(),
              ]),
            ),
          ],
        ),
      ],
    );
  }

  // ── Narrow layout (mobile) — express vs. detailed ────────────────────────────
  //
  // Express mode (default): glucose + meal type only → save in 3 taps.
  // Detailed mode: full form — insulin, food, health, Ramadan.
  // Tapping "+ Détails" expands once and stays expanded for the session.

  Widget _buildNarrowLayout(String unit, AppDatabase db) {
    return Column(
      children: [
        _buildHeader(context),
        const SizedBox(height: 24),
        _buildGlucoseCard(unit),
        const SizedBox(height: 24),
        _buildMealTypeSelector(),

        if (_expressMode) ...[
          // ── Express: just the expand affordance + IAmina teaser ──
          const SizedBox(height: 20),
          _buildDetailsToggle(),
          const SizedBox(height: 20),
          _buildIAminaTeaser(),
        ] else ...[
          // ── Detailed: full form ──
          const SizedBox(height: 20),
          _buildTimeRow(context),
          if (_mealType != 'À jeun') ...[
            const SizedBox(height: 24),
            _buildCompositionSection(),
          ],
          const SizedBox(height: 24),
          _buildInsulinSection(),
          const SizedBox(height: 24),
          _buildHealthSection(),
          const SizedBox(height: 20),
          _buildRamadanToggle(),
          const SizedBox(height: 20),
          _buildIAminaTeaser(),
        ],
      ],
    );
  }

  // ── "+ Détails" expand button ─────────────────────────────────────────────────

  Widget _buildDetailsToggle() {
    return GestureDetector(
      onTap: () {
        HapticFeedback.lightImpact();
        setState(() => _expressMode = false);
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 220),
        curve: Curves.easeOut,
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
        decoration: BoxDecoration(
          color: AminaTheme.subtleBg(context),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AminaTheme.divider(context)),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.expand_more_rounded, size: 18, color: AminaTheme.textSecondary(context)),
            const SizedBox(width: 8),
            Text(
              '+ Détails : insuline, aliments, santé…',
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: AminaTheme.textSecondary(context),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ── Header ────────────────────────────────────────────────────────────────────

  Widget _buildHeader(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(top: MediaQuery.of(context).padding.top + 20, bottom: 4),
      child: Row(
        children: [
          GestureDetector(
            onTap: () {
              if (widget.isPage) { GoRouter.of(context).go('/dashboard'); }
              else { Navigator.pop(context); }
            },
            child: Container(
              width: 40, height: 40,
              decoration: BoxDecoration(
                color: AminaTheme.subtleBg(context),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AminaTheme.divider(context)),
              ),
              child: Icon(Icons.arrow_back_ios_new, size: 16, color: AminaTheme.textPrimary(context)),
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('Nouvelle mesure', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: AminaTheme.textPrimary(context), letterSpacing: -0.5)),
              Text(_timeLabel(), style: TextStyle(fontSize: 12, color: AminaTheme.textSecondary(context))),
            ]),
          ),
        ],
      ),
    );
  }

  // ── Glucose card ──────────────────────────────────────────────────────────────

  Widget _buildGlucoseCard(String unit) {
    final color = _glucoseColor(_glucoseValue);
    final bgCol = _glucoseBg(_glucoseValue);
    final label = _glucoseLabel(_glucoseValue);
    final sliderMax = unit == 'mmol/L' ? 22.2 : 400.0;
    final sliderMin = unit == 'mmol/L' ? 2.2  : 40.0;
    final isDanger  = _glucoseValue < 70 || _glucoseValue > 250;

    final quickValues = unit == 'mmol/L'
        ? [3.3, 4.4, 6.1, 7.8, 10.0, 12.2, 14.4]
        : [60.0, 80.0, 110.0, 140.0, 180.0, 220.0, 260.0];

    return AnimatedContainer(
      duration: const Duration(milliseconds: 280),
      curve: Curves.easeInOut,
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 20),
      decoration: BoxDecoration(
        color: bgCol,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withValues(alpha: isDanger ? 0.5 : 0.2), width: isDanger ? 1.5 : 1),
        boxShadow: [BoxShadow(color: color.withValues(alpha: isDanger ? 0.18 : 0.08), blurRadius: 20, offset: const Offset(0, 6))],
      ),
      child: Column(
        children: [
          // Camera / OCR button — mobile: ML Kit on-device; web: Gemini Vision backend
          Align(
            alignment: Alignment.centerRight,
            child: GestureDetector(
              onTap: _ocrScanning ? null : () => _runOcr(context, unit),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
                decoration: BoxDecoration(
                  color: AminaTheme.teal500.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(99),
                  border: Border.all(color: AminaTheme.teal500.withValues(alpha: 0.3)),
                ),
                child: _ocrScanning
                    ? const SizedBox(
                        width: 14, height: 14,
                        child: CircularProgressIndicator(strokeWidth: 2, color: AminaTheme.teal500),
                      )
                    : const Row(mainAxisSize: MainAxisSize.min, children: [
                        Icon(Icons.camera_alt_outlined, size: 14, color: AminaTheme.teal600),
                        SizedBox(width: 5),
                        Text('Lire le glucomètre',
                          style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AminaTheme.teal600)),
                      ]),
              ),
            ),
          ),
          const SizedBox(height: 8),
          // Zone badge
          AnimatedSwitcher(
            duration: const Duration(milliseconds: 200),
            child: Container(
              key: ValueKey(label),
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(99),
                border: Border.all(color: color.withValues(alpha: 0.35)),
              ),
              child: Row(mainAxisSize: MainAxisSize.min, children: [
                if (isDanger) ...[
                  Icon(Icons.warning_rounded, size: 13, color: color),
                  const SizedBox(width: 5),
                ],
                Container(width: 7, height: 7, decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
                const SizedBox(width: 7),
                Text(label, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: color)),
              ]),
            ),
          ),
          const SizedBox(height: 12),
          // Large number input
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: [
              SizedBox(
                width: 180,
                child: TextField(
                  controller: _manualController,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 84, fontWeight: FontWeight.w800, height: 1.0, letterSpacing: -4, color: color),
                  decoration: InputDecoration(
                    border: InputBorder.none,
                    contentPadding: EdgeInsets.zero,
                    hintText: '---',
                    hintStyle: TextStyle(fontSize: 84, fontWeight: FontWeight.w800, height: 1.0, letterSpacing: -4, color: color.withValues(alpha: 0.25)),
                  ),
                  onChanged: (val) {
                    final d = double.tryParse(val);
                    if (d != null) setState(() => _glucoseValue = d.clamp(sliderMin, sliderMax));
                  },
                ),
              ),
              const SizedBox(width: 6),
              Text(unit, style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: color.withValues(alpha: 0.6))),
            ],
          ),
          const SizedBox(height: 12),
          // Quick shortcuts
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: quickValues.map((v) {
                final active = (_glucoseValue - v).abs() < (unit == 'mmol/L' ? 0.1 : 0.5);
                final lbl = unit == 'mmol/L' ? v.toStringAsFixed(1) : v.toInt().toString();
                return Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 3),
                  child: GestureDetector(
                    onTap: () {
                      HapticFeedback.selectionClick();
                      setState(() { _glucoseValue = v; _manualController.text = lbl; });
                    },
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 150),
                      padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 7),
                      decoration: BoxDecoration(
                        color: active ? color : Colors.white.withValues(alpha: 0.65),
                        borderRadius: BorderRadius.circular(99),
                        border: Border.all(color: active ? color : color.withValues(alpha: 0.2)),
                      ),
                      child: Text(lbl, style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: active ? Colors.white : color)),
                    ),
                  ),
                );
              }).toList(),
            ),
          ),
          const SizedBox(height: 12),
          // Slider
          SliderTheme(
            data: SliderTheme.of(context).copyWith(
              activeTrackColor: color,
              inactiveTrackColor: color.withValues(alpha: 0.15),
              thumbColor: color,
              overlayColor: color.withValues(alpha: 0.12),
              trackHeight: 5,
              thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 10),
            ),
            child: Slider(
              value: _glucoseValue.clamp(sliderMin, sliderMax),
              min: sliderMin, max: sliderMax,
              onChanged: (val) {
                HapticFeedback.selectionClick();
                final r = unit == 'mmol/L' ? double.parse(val.toStringAsFixed(1)) : val.roundToDouble();
                setState(() { _glucoseValue = r; _manualController.text = unit == 'mmol/L' ? r.toStringAsFixed(1) : r.toInt().toString(); });
              },
            ),
          ),
          // Zone labels
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 6),
            child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
              _SliderLabel(unit == 'mmol/L' ? '2.2' : '40',  color),
              _SliderLabel(unit == 'mmol/L' ? '3.9' : '70',  color),
              _SliderLabel(unit == 'mmol/L' ? '10' : '180',  color),
              _SliderLabel(unit == 'mmol/L' ? '22' : '400',  color),
            ]),
          ),
        ],
      ),
    );
  }

  // ── Meal type selector — ghost colored buttons ────────────────────────────────

  Widget _buildMealTypeSelector() {
    final types = _isRamadanMode ? _mealTypesRamadan : _mealTypesNormal;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _SectionLabel('MOMENT DU REPAS', context),
        const SizedBox(height: 12),
        Wrap(
          spacing: 10,
          runSpacing: 10,
          children: types.map((type) {
            final sel   = _mealType == type;
            final col   = _mealColor(type);
            return GestureDetector(
              onTap: () {
                HapticFeedback.selectionClick();
                setState(() {
                  _mealType = type;
                  _selectedFoods.clear();
                  _foodSearch = '';
                  _searchController.clear();
                  _recentFoods = [];
                });
                _loadRecentFoods();
              },
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 180),
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 11),
                decoration: BoxDecoration(
                  color: sel ? col : Colors.transparent,
                  borderRadius: BorderRadius.circular(99),
                  border: Border.all(color: sel ? col : col.withValues(alpha: 0.4), width: sel ? 1.5 : 1),
                ),
                child: Text(
                  type,
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: sel ? FontWeight.w700 : FontWeight.w500,
                    color: sel ? Colors.white : col,
                  ),
                ),
              ),
            );
          }).toList(),
        ),
      ],
    );
  }

  // ── Time row ──────────────────────────────────────────────────────────────────

  Widget _buildTimeRow(BuildContext context) {
    return GestureDetector(
      onTap: () async {
        final pickedDate = await showDatePicker(
          context: context,
          initialDate: _selectedTime,
          firstDate: DateTime.now().subtract(const Duration(days: 90)),
          lastDate: DateTime.now(),
          builder: (ctx, child) => Theme(
            data: Theme.of(ctx).copyWith(colorScheme: Theme.of(ctx).colorScheme.copyWith(primary: AminaTheme.teal500)),
            child: child!,
          ),
        );
        if (pickedDate == null || !context.mounted) return;
        final pickedTime = await showTimePicker(
          context: context,
          initialTime: TimeOfDay.fromDateTime(_selectedTime),
          builder: (ctx, child) => Theme(
            data: Theme.of(ctx).copyWith(colorScheme: Theme.of(ctx).colorScheme.copyWith(primary: AminaTheme.teal500)),
            child: child!,
          ),
        );
        if (pickedTime == null) return;
        setState(() => _selectedTime = DateTime(pickedDate.year, pickedDate.month, pickedDate.day, pickedTime.hour, pickedTime.minute));
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: AminaTheme.subtleBg(context),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AminaTheme.divider(context)),
        ),
        child: Row(children: [
          Icon(Icons.schedule_outlined, size: 16, color: AminaTheme.textSecondary(context)),
          const SizedBox(width: 10),
          Text(_timeLabel(), style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: AminaTheme.textPrimary(context))),
          const Spacer(),
          Icon(Icons.edit_outlined, size: 14, color: AminaTheme.textSecondary(context)),
        ]),
      ),
    );
  }

  // ── Helpers ──────────────────────────────────────────────────────────────────

  int _giNumeric(String glycemic) => switch (glycemic) { 'low' => 35, 'medium' => 60, _ => 75 };

  // ── Composition section ───────────────────────────────────────────────────────

  Widget _buildCompositionSection() {
    final isSearching = _foodSearch.isNotEmpty;
    final displayList = isSearching
        ? universalFoods.where((f) => f.label.toLowerCase().contains(_foodSearch.toLowerCase())).take(25).toList()
        : foodsForMeal(_mealType).isNotEmpty
            ? foodsForMeal(_mealType)
            : universalFoods.take(30).toList();
    final listLabel = isSearching
        ? 'RÉSULTATS POUR "${_foodSearch.toUpperCase()}"'
        : 'SUGGESTIONS POUR CE REPAS';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // ── Header ──
        Row(children: [
          Expanded(child: _SectionLabel('ALIMENTS', context)),
          GestureDetector(
              onTap: _mealScanning ? null : () => _runMealAnalysis(context),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                decoration: BoxDecoration(
                  color: const Color(0xFF059669).withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(99),
                  border: Border.all(color: const Color(0xFF059669).withValues(alpha: 0.3)),
                ),
                child: _mealScanning
                    ? const SizedBox(width: 12, height: 12, child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF059669)))
                    : const Row(mainAxisSize: MainAxisSize.min, children: [
                        Icon(Icons.camera_alt_outlined, size: 13, color: Color(0xFF059669)),
                        SizedBox(width: 4),
                        Text('Photo', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: Color(0xFF059669))),
                      ]),
              ),
            ),
        ]),
        const SizedBox(height: 14),

        // ── Selected zone — fixed height, horizontal scroll, no reflow ──
        if (_selectedFoods.isNotEmpty) ...[
          SizedBox(
            height: 72,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              itemCount: _selectedFoods.length,
              padding: const EdgeInsets.only(right: 4),
              itemBuilder: (_, i) => _buildSelectedCard(_selectedFoods[i]),
            ),
          ),
          const SizedBox(height: 12),
          _buildImpactBar(),
          const SizedBox(height: 16),
        ],

        // ── Recents ──
        if (_foodSearch.isEmpty) ...[
          Text('RÉCENTS', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: AminaTheme.textSecondary(context), letterSpacing: 0.6)),
          const SizedBox(height: 8),
          if (_recentFoods.isEmpty)
            Row(children: [
              Icon(Icons.history, size: 14, color: AminaTheme.textSecondary(context).withValues(alpha: 0.4)),
              const SizedBox(width: 6),
              Text('Vos aliments habituels apparaîtront ici', style: TextStyle(fontSize: 12, color: AminaTheme.textSecondary(context).withValues(alpha: 0.5))),
            ])
          else
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: _recentFoods.map((item) {
                  final isSel = _selectedFoods.any((s) => s.item.id == item.id);
                  final giCol = _giColor(item.glycemic);
                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: GestureDetector(
                      onTap: () {
                        HapticFeedback.selectionClick();
                        setState(() {
                          if (isSel) { _selectedFoods.removeWhere((s) => s.item.id == item.id); }
                          else { _selectedFoods.add(_SelectedFood(item: item)); }
                        });
                      },
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 140),
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
                        decoration: BoxDecoration(
                          color: isSel ? AminaTheme.teal500.withValues(alpha: 0.08) : AminaTheme.surface(context),
                          borderRadius: BorderRadius.circular(99),
                          border: Border.all(
                            color: isSel ? AminaTheme.teal500 : AminaTheme.divider(context),
                            width: isSel ? 1.5 : 1,
                          ),
                        ),
                        child: Row(mainAxisSize: MainAxisSize.min, children: [
                          Container(width: 6, height: 6, decoration: BoxDecoration(color: giCol, shape: BoxShape.circle)),
                          const SizedBox(width: 6),
                          Text(item.label, style: TextStyle(
                            fontSize: 12, fontWeight: FontWeight.w600,
                            color: isSel ? AminaTheme.teal700 : AminaTheme.textPrimary(context),
                          )),
                        ]),
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),
          const SizedBox(height: 14),
        ],

        // ── Search bar ──
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
          decoration: BoxDecoration(
            color: AminaTheme.subtleBg(context),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: isSearching ? AminaTheme.teal200 : AminaTheme.divider(context)),
          ),
          child: TextField(
            controller: _searchController,
            style: TextStyle(fontSize: 14, color: AminaTheme.textPrimary(context)),
            decoration: InputDecoration(
              hintText: 'Rechercher un aliment…',
              hintStyle: TextStyle(color: AminaTheme.textSecondary(context), fontSize: 13),
              border: InputBorder.none, isDense: true,
              contentPadding: const EdgeInsets.symmetric(vertical: 11),
              prefixIcon: Icon(Icons.search, size: 18, color: AminaTheme.textSecondary(context)),
              suffixIcon: isSearching
                  ? GestureDetector(
                      onTap: () => setState(() { _foodSearch = ''; _searchController.clear(); }),
                      child: Icon(Icons.close, size: 16, color: AminaTheme.textSecondary(context)),
                    )
                  : null,
            ),
            onChanged: (v) => setState(() => _foodSearch = v),
          ),
        ),
        const SizedBox(height: 14),

        // ── Section label ──
        Text(listLabel, style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: AminaTheme.textSecondary(context), letterSpacing: 0.6)),
        const SizedBox(height: 8),

        // ── Food list — compact rows with 4px GI band ──
        if (displayList.isEmpty)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 16),
            child: Text('Aucun résultat', style: TextStyle(fontSize: 13, color: AminaTheme.textSecondary(context))),
          )
        else
          Column(children: displayList.map(_buildFoodRow).toList()),

        const SizedBox(height: 16),
        // ── Free note + mic vocal input ──────────────────────────────────────
        _buildMealNoteField(context),
      ],
    );
  }

  Widget _buildMealNoteField(BuildContext context) {
    final api = context.read<ApiClient>();
    return Container(
      decoration: BoxDecoration(
        color: AminaTheme.subtleBg(context),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AminaTheme.divider(context)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Expanded(
            child: TextField(
              controller: _mealNoteController,
              maxLines: null,
              style: TextStyle(fontSize: 13, color: AminaTheme.textPrimary(context)),
              decoration: InputDecoration(
                hintText: _noteRecording
                    ? '🎤 Enregistrement…'
                    : _noteTranscribing
                        ? '⏳ Transcription…'
                        : 'Note libre (repas, ressenti…)',
                hintStyle: TextStyle(fontSize: 12, color: AminaTheme.textSecondary(context)),
                border: InputBorder.none,
                isDense: true,
                contentPadding: const EdgeInsets.fromLTRB(14, 12, 0, 12),
              ),
            ),
          ),
          // Mic button
          GestureDetector(
            onTap: (_noteTranscribing) ? null : () => _toggleNoteRecording(api),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              width: 40, height: 40,
              margin: const EdgeInsets.only(right: 6),
              decoration: BoxDecoration(
                color: _noteRecording
                    ? const Color(0xFFEF4444).withValues(alpha: 0.12)
                    : Colors.transparent,
                shape: BoxShape.circle,
              ),
              child: _noteTranscribing
                  ? const Center(child: SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: AminaTheme.teal500)))
                  : Icon(
                      _noteRecording ? Icons.stop_rounded : Icons.mic_none_rounded,
                      size: 20,
                      color: _noteRecording
                          ? const Color(0xFFEF4444)
                          : AminaTheme.textSecondary(context),
                    ),
            ),
          ),
        ],
      ),
    );
  }

  // ── Selected food card (fixed-height zone) ────────────────────────────────────

  Widget _buildSelectedCard(_SelectedFood sf) {
    final giCol = _giColor(sf.item.glycemic);
    final giNum = _giNumeric(sf.item.glycemic);
    return Container(
      margin: const EdgeInsets.only(right: 10),
      decoration: BoxDecoration(
        color: AminaTheme.surface(context),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: giCol.withValues(alpha: 0.25)),
        boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.06), blurRadius: 8, offset: const Offset(0, 2))],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(14),
        child: IntrinsicWidth(
          child: Row(children: [
            // 4px GI band
            Container(width: 4, color: giCol),
            // Name + IG
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisSize: MainAxisSize.min, children: [
                Text(sf.item.label, style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AminaTheme.textPrimary(context))),
                const SizedBox(height: 2),
                Text('IG $giNum', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: giCol)),
              ]),
            ),
            // P | M | G segmented
            _buildPortionSegment(sf, giCol),
            const SizedBox(width: 6),
            // Remove
            GestureDetector(
              onTap: () { HapticFeedback.selectionClick(); setState(() => _selectedFoods.removeWhere((s) => s.item.id == sf.item.id)); },
              child: Padding(
                padding: const EdgeInsets.only(right: 12, top: 8, bottom: 8),
                child: Icon(Icons.close, size: 14, color: AminaTheme.textSecondary(context)),
              ),
            ),
          ]),
        ),
      ),
    );
  }

  // ── P | M | G segmented portion control ──────────────────────────────────────

  Widget _buildPortionSegment(_SelectedFood sf, Color giCol) {
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 18),
      decoration: BoxDecoration(
        color: giCol.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [_Portion.petit, _Portion.moyen, _Portion.grand].map((p) {
          final isActive = sf.portion == p;
          final label = switch (p) { _Portion.petit => 'P', _Portion.moyen => 'M', _Portion.grand => 'G' };
          return GestureDetector(
            onTap: () { HapticFeedback.selectionClick(); setState(() => sf.portion = p); },
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 140),
              padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
              decoration: BoxDecoration(
                color: isActive ? giCol : Colors.transparent,
                borderRadius: BorderRadius.circular(7),
              ),
              child: Text(label, style: TextStyle(
                fontSize: 11, fontWeight: FontWeight.w700,
                color: isActive ? Colors.white : giCol.withValues(alpha: 0.65),
              )),
            ),
          );
        }).toList(),
      ),
    );
  }

  // ── Compact food row with 4px GI band ────────────────────────────────────────

  Widget _buildFoodRow(CulinaryItem item) {
    final isSel = _selectedFoods.any((s) => s.item.id == item.id);
    final giCol = _giColor(item.glycemic);
    final giNum = _giNumeric(item.glycemic);
    final carbs = _Portion.moyen.carbsFor(item.glycemic);

    return GestureDetector(
      onTap: () {
        HapticFeedback.selectionClick();
        setState(() {
          if (isSel) { _selectedFoods.removeWhere((s) => s.item.id == item.id); }
          else { _selectedFoods.add(_SelectedFood(item: item)); }
        });
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        margin: const EdgeInsets.only(bottom: 2),
        decoration: BoxDecoration(
          color: isSel ? AminaTheme.teal500.withValues(alpha: 0.06) : Colors.transparent,
          borderRadius: BorderRadius.circular(10),
        ),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(10),
          child: Row(children: [
            // 4px GI band — brighter when selected
            AnimatedContainer(
              duration: const Duration(milliseconds: 150),
              width: 4, height: 52,
              color: isSel ? giCol : giCol.withValues(alpha: 0.35),
            ),
            const SizedBox(width: 12),
            // Name + carbs info
            Expanded(
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 10),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(item.label, style: TextStyle(
                    fontSize: 14,
                    fontWeight: isSel ? FontWeight.w600 : FontWeight.w500,
                    color: AminaTheme.textPrimary(context),
                  )),
                  const SizedBox(height: 2),
                  Text('~${carbs}g glucides · IG $giNum',
                    style: TextStyle(fontSize: 11, color: isSel ? giCol : AminaTheme.textSecondary(context))),
                ]),
              ),
            ),
            // + / check action icon
            AnimatedContainer(
              duration: const Duration(milliseconds: 150),
              width: 30, height: 30,
              margin: const EdgeInsets.only(right: 12),
              decoration: BoxDecoration(
                color: isSel ? AminaTheme.teal500 : Colors.transparent,
                shape: BoxShape.circle,
                border: isSel ? null : Border.all(color: AminaTheme.divider(context)),
              ),
              child: Icon(isSel ? Icons.check : Icons.add, size: 15,
                color: isSel ? Colors.white : AminaTheme.textSecondary(context)),
            ),
          ]),
        ),
      ),
    );
  }

  // ── Glycemic impact bar ───────────────────────────────────────────────────────

  Widget _buildImpactBar() {
    final totalCarbs = _selectedFoods.fold(0, (sum, sf) => sum + sf.portion.carbsFor(sf.item.glycemic));
    final (label, color) = totalCarbs < 30
        ? ('Impact faible', const Color(0xFF10B981))
        : totalCarbs < 60
            ? ('Impact modéré', const Color(0xFFF59E0B))
            : ('Impact élevé', const Color(0xFFEF4444));
    final fraction = (totalCarbs / 80).clamp(0.0, 1.0);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.07),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withValues(alpha: 0.2)),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Text(label, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: color)),
          const Spacer(),
          Text('~$totalCarbs g glucides', style: TextStyle(fontSize: 12, color: AminaTheme.textSecondary(context))),
        ]),
        const SizedBox(height: 8),
        ClipRRect(
          borderRadius: BorderRadius.circular(99),
          child: LinearProgressIndicator(
            value: fraction,
            minHeight: 5,
            backgroundColor: color.withValues(alpha: 0.15),
            valueColor: AlwaysStoppedAnimation<Color>(color),
          ),
        ),
      ]),
    );
  }

  // ── Insulin section — with risk color indicator ───────────────────────────────

  Widget _buildInsulinSection() {
    final iCol  = _insulinColor(_insulinDose);
    final iRisk = _insulinRiskLabel(_insulinDose);
    final dark  = AminaTheme.isDark(context);

    // Quick-dose suggestions per 0.5 increments — common clinical presets
    const suggestions = [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 16.0, 20.0];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _SectionLabel('DOSE D\'INSULINE', context),
        const SizedBox(height: 14),

        // ── Ambient gradient card ──
        AnimatedContainer(
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeInOut,
          width: double.infinity,
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                dark
                    ? iCol.withValues(alpha: _insulinDose == 0 ? 0.04 : 0.10)
                    : iCol.withValues(alpha: _insulinDose == 0 ? 0.03 : 0.07),
                dark
                    ? Colors.transparent
                    : iCol.withValues(alpha: 0.02),
              ],
            ),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: iCol.withValues(alpha: _insulinDose == 0 ? 0.12 : 0.28),
              width: 1.2,
            ),
            boxShadow: _insulinDose > 0
                ? [BoxShadow(color: iCol.withValues(alpha: 0.18), blurRadius: 22, offset: const Offset(0, 6))]
                : null,
          ),
          child: Column(
            children: [
              // ── Dose display + fine-tune stepper ──
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 22, 20, 14),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    // − button
                    GestureDetector(
                      onTap: () {
                        HapticFeedback.selectionClick();
                        if (_insulinDose > 0) setState(() => _insulinDose = (_insulinDose - _insulinStep).clamp(0.0, 100.0));
                      },
                      child: Container(
                        width: 40, height: 40,
                        decoration: BoxDecoration(
                          color: iCol.withValues(alpha: 0.1),
                          shape: BoxShape.circle,
                          border: Border.all(color: iCol.withValues(alpha: 0.25)),
                        ),
                        child: Icon(Icons.remove, size: 18, color: iCol),
                      ),
                    ),

                    // Dose value
                    Flexible(child: Column(children: [
                      AnimatedDefaultTextStyle(
                        duration: const Duration(milliseconds: 200),
                        style: TextStyle(
                          fontSize: 58,
                          fontWeight: FontWeight.w800,
                          height: 1.0,
                          letterSpacing: -2,
                          color: _insulinDose == 0
                              ? AminaTheme.textSecondary(context).withValues(alpha: 0.4)
                              : iCol,
                        ),
                        child: Text(
                          _insulinDose == _insulinDose.truncateToDouble()
                              ? _insulinDose.toInt().toString()
                              : _insulinDose.toStringAsFixed(1),
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text('UNITÉS', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, letterSpacing: 1.0, color: AminaTheme.textSecondary(context))),
                      const SizedBox(height: 6),
                      AnimatedSwitcher(
                        duration: const Duration(milliseconds: 200),
                        child: Container(
                          key: ValueKey(iRisk),
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                          decoration: BoxDecoration(
                            color: iCol.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(99),
                            border: Border.all(color: iCol.withValues(alpha: 0.2)),
                          ),
                          child: Text(iRisk, style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: iCol), overflow: TextOverflow.ellipsis),
                        ),
                      ),
                    ])),

                    // + button
                    GestureDetector(
                      onTap: () {
                        HapticFeedback.selectionClick();
                        setState(() => _insulinDose = (_insulinDose + _insulinStep).clamp(0.0, 100.0));
                      },
                      child: Container(
                        width: 40, height: 40,
                        decoration: BoxDecoration(
                          color: iCol.withValues(alpha: 0.1),
                          shape: BoxShape.circle,
                          border: Border.all(color: iCol.withValues(alpha: 0.25)),
                        ),
                        child: Icon(Icons.add, size: 18, color: iCol),
                      ),
                    ),
                  ],
                ),
              ),

              // ── Divider ──
              Container(height: 1, color: iCol.withValues(alpha: 0.1)),

              // ── Horizontal quick-dose suggestions ──
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 14),
                child: SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: Row(
                    children: suggestions.map((dose) {
                      final isSelected = (_insulinDose - dose).abs() < 0.01;
                      final doseCol = _insulinColor(dose);
                      return Padding(
                        padding: const EdgeInsets.only(right: 8),
                        child: GestureDetector(
                          onTap: () {
                            HapticFeedback.selectionClick();
                            setState(() => _insulinDose = dose);
                          },
                          child: AnimatedContainer(
                            duration: const Duration(milliseconds: 180),
                            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 9),
                            decoration: BoxDecoration(
                              gradient: isSelected
                                  ? LinearGradient(
                                      colors: [doseCol, doseCol.withValues(alpha: 0.75)],
                                      begin: Alignment.topLeft,
                                      end: Alignment.bottomRight,
                                    )
                                  : null,
                              color: isSelected ? null : iCol.withValues(alpha: 0.06),
                              borderRadius: BorderRadius.circular(99),
                              border: Border.all(
                                color: isSelected ? Colors.transparent : iCol.withValues(alpha: 0.18),
                                width: 1,
                              ),
                              boxShadow: isSelected
                                  ? [BoxShadow(color: doseCol.withValues(alpha: 0.35), blurRadius: 8, offset: const Offset(0, 3))]
                                  : null,
                            ),
                            child: Text(
                              dose == 0 ? 'Aucune' : '${dose.toInt()} U',
                              style: TextStyle(
                                fontSize: 13,
                                fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
                                color: isSelected
                                    ? Colors.white
                                    : AminaTheme.textSecondary(context),
                              ),
                            ),
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  // ── Health state — once a day ─────────────────────────────────────────────────

  Widget _buildHealthSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(children: [
          Expanded(child: _SectionLabel('ÉTAT DU JOUR', context)),
          if (!_isFirstLogToday)
            GestureDetector(
              onTap: () => setState(() => _showHealthExpanded = !_showHealthExpanded),
              child: Text(
                _showHealthExpanded ? 'Masquer' : 'Modifier',
                style: const TextStyle(fontSize: 12, color: AminaTheme.teal600, fontWeight: FontWeight.w600),
              ),
            ),
        ]),
        if (!_isFirstLogToday && !_showHealthExpanded)
          Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Text(
              'Déjà renseigné aujourd\'hui — appuyez sur Modifier pour changer.',
              style: TextStyle(fontSize: 12, color: AminaTheme.textSecondary(context), fontStyle: FontStyle.italic),
            ),
          )
        else ...[
          const SizedBox(height: 12),
          // Context states — text-only ghost buttons
          Wrap(
            spacing: 10, runSpacing: 10,
            children: [
              _buildContextBtn('Malade',  _isSick,     () => setState(() => _isSick = !_isSick),     const Color(0xFFDC2626)),
              _buildContextBtn('Stressé', _isStressed, () => setState(() => _isStressed = !_isStressed), const Color(0xFFF59E0B)),
              _buildContextBtn('Actif',   _isActive,   () => setState(() => _isActive = !_isActive),  const Color(0xFF059669)),
            ],
          ),
          const SizedBox(height: 20),
          // Sleep
          Text('SOMMEIL', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: AminaTheme.textSecondary(context), letterSpacing: 0.6)),
          const SizedBox(height: 10),
          Row(children: [
            Expanded(child: _buildToggleBtn('Reposé', _sleepQuality == 'good', () => setState(() => _sleepQuality = _sleepQuality == 'good' ? null : 'good'), const Color(0xFF059669))),
            const SizedBox(width: 10),
            Expanded(child: _buildToggleBtn('Mauvaise nuit', _sleepQuality == 'bad', () => setState(() => _sleepQuality = _sleepQuality == 'bad' ? null : 'bad'), const Color(0xFFDC2626))),
          ]),
          const SizedBox(height: 20),
          // Energy
          Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
            Text('NIVEAU D\'ÉNERGIE', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: AminaTheme.textSecondary(context), letterSpacing: 0.6)),
            if (_fatigueLevel != null)
              GestureDetector(
                onTap: () => setState(() => _fatigueLevel = null),
                child: Text('Effacer', style: TextStyle(fontSize: 11, color: AminaTheme.textSecondary(context))),
              ),
          ]),
          const SizedBox(height: 10),
          Row(children: [
            Expanded(child: _buildToggleBtn('Pleine énergie', _fatigueLevel == 5, () => setState(() => _fatigueLevel = _fatigueLevel == 5 ? null : 5), const Color(0xFF059669))),
            const SizedBox(width: 8),
            Expanded(child: _buildToggleBtn('Correct', _fatigueLevel == 3, () => setState(() => _fatigueLevel = _fatigueLevel == 3 ? null : 3), const Color(0xFFF59E0B))),
            const SizedBox(width: 8),
            Expanded(child: _buildToggleBtn('Épuisé', _fatigueLevel == 1, () => setState(() => _fatigueLevel = _fatigueLevel == 1 ? null : 1), const Color(0xFFDC2626))),
          ]),
        ],
      ],
    );
  }

  Widget _buildContextBtn(String label, bool active, VoidCallback onTap, Color col) {
    return GestureDetector(
      onTap: () { HapticFeedback.selectionClick(); onTap(); },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 160),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 11),
        decoration: BoxDecoration(
          color: active ? col.withValues(alpha: 0.1) : Colors.transparent,
          borderRadius: BorderRadius.circular(99),
          border: Border.all(color: active ? col : col.withValues(alpha: 0.35), width: active ? 1.5 : 1),
        ),
        child: Text(label, style: TextStyle(fontSize: 14, fontWeight: active ? FontWeight.w700 : FontWeight.w500, color: active ? col : col.withValues(alpha: 0.7))),
      ),
    );
  }

  Widget _buildToggleBtn(String label, bool active, VoidCallback onTap, Color col) {
    return GestureDetector(
      onTap: () { HapticFeedback.selectionClick(); onTap(); },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 160),
        padding: const EdgeInsets.symmetric(vertical: 13),
        decoration: BoxDecoration(
          color: active ? col.withValues(alpha: 0.1) : Colors.transparent,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: active ? col : AminaTheme.divider(context), width: active ? 1.5 : 1),
        ),
        child: Center(
          child: Text(label, style: TextStyle(fontSize: 13, fontWeight: active ? FontWeight.w700 : FontWeight.w500, color: active ? col : AminaTheme.textSecondary(context))),
        ),
      ),
    );
  }

  // ── Ramadan toggle ────────────────────────────────────────────────────────────

  Widget _buildRamadanToggle() {
    final dark = AminaTheme.isDark(context);
    return GestureDetector(
      onTap: () => setState(() { _isRamadanMode = !_isRamadanMode; _mealType = _isRamadanMode ? 'Iftar' : 'À jeun'; }),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
        decoration: BoxDecoration(
          color: _isRamadanMode ? (dark ? AminaTheme.dark700 : const Color(0xFF0D1A17)) : AminaTheme.subtleBg(context),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: _isRamadanMode ? AminaTheme.teal500.withValues(alpha: 0.3) : Colors.transparent),
        ),
        child: Row(children: [
          Icon(_isRamadanMode ? Icons.nightlight_round : Icons.wb_sunny_outlined, color: _isRamadanMode ? Colors.amber : AminaTheme.textSecondary(context)),
          const SizedBox(width: 14),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Mode Ramadan', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14, color: _isRamadanMode ? Colors.white : AminaTheme.textPrimary(context))),
            Text(_isRamadanMode ? 'Activé — horaires adaptés' : 'Désactivé', style: TextStyle(fontSize: 12, color: _isRamadanMode ? Colors.white70 : AminaTheme.textSecondary(context))),
          ])),
          Switch(value: _isRamadanMode, onChanged: (v) => setState(() { _isRamadanMode = v; _mealType = v ? 'Iftar' : 'À jeun'; }), activeThumbColor: AminaTheme.teal500, activeTrackColor: AminaTheme.teal500.withValues(alpha: 0.5)),
        ]),
      ),
    );
  }

  // ── IAmina teaser ─────────────────────────────────────────────────────────────

  Widget _buildIAminaTeaser() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
      decoration: BoxDecoration(
        color: AminaTheme.teal500.withValues(alpha: 0.06),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AminaTheme.teal500.withValues(alpha: 0.18)),
      ),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Container(width: 40, height: 40, decoration: BoxDecoration(gradient: AminaTheme.heroGradient, shape: BoxShape.circle),
          child: const Center(child: Text('I', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w800)))),
        const SizedBox(width: 12),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            const Text('IAmina · ', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AminaTheme.teal500)),
            Text('Après enregistrement', style: TextStyle(fontSize: 11, color: AminaTheme.teal500.withValues(alpha: 0.7))),
          ]),
          const SizedBox(height: 6),
          Text('IAmina analysera cette mesure dans le contexte de ton historique et te donnera un conseil personnalisé.',
            style: TextStyle(fontSize: 12, height: 1.45, color: AminaTheme.textSecondary(context))),
        ])),
      ]),
    );
  }

  // ── Save bar ──────────────────────────────────────────────────────────────────

  Widget _buildSaveBar(AppDatabase db, BuildContext context) {
    return Container(
      padding: EdgeInsets.fromLTRB(28, 14, 28, MediaQuery.of(context).padding.bottom + 14),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter, end: Alignment.bottomCenter,
          colors: [AminaTheme.bg(context).withValues(alpha: 0.0), AminaTheme.bg(context).withValues(alpha: 0.96), AminaTheme.bg(context)],
          stops: const [0.0, 0.3, 1.0],
        ),
      ),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 760),
          child: SizedBox(
            width: double.infinity,
            height: 54,
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: _saving ? null : const LinearGradient(colors: [AminaTheme.teal500, AminaTheme.teal700], begin: Alignment.topLeft, end: Alignment.bottomRight),
                color: _saving ? AminaTheme.teal500.withValues(alpha: 0.5) : null,
                borderRadius: BorderRadius.circular(99),
                boxShadow: _saving ? null : AminaTheme.shadowFab,
              ),
              child: ElevatedButton.icon(
                onPressed: _saving ? null : () => _saveLog(db, context),
                icon: _saving
                    ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : const Icon(Icons.check, size: 18, color: Colors.white),
                label: Text(_saving ? 'Enregistrement…' : 'Enregistrer la mesure',
                  style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: Colors.white)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.transparent, shadowColor: Colors.transparent,
                  disabledBackgroundColor: Colors.transparent,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(99)),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  // ── Save logic ────────────────────────────────────────────────────────────────

  Future<void> _saveLog(AppDatabase db, BuildContext context) async {
    if (_manualController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Veuillez saisir une glycémie'), behavior: SnackBarBehavior.floating),
      );
      return;
    }

    final mgdlValue = context.read<PatientProfileData?>()?.unitPreference == 'mmol/L'
        ? _glucoseValue * 18.0
        : _glucoseValue;

    if (mgdlValue < 54 || mgdlValue > 350) {
      final confirm = await showDialog<bool>(
        context: context,
        builder: (_) => AlertDialog(
          title: Text(mgdlValue < 54 ? '⚠️ Hypoglycémie sévère' : '⚠️ Valeur élevée'),
          content: Text(mgdlValue < 54
              ? 'Une glycémie de ${mgdlValue.toInt()} mg/dL est dangereuse. Prenez 15g de glucides rapides maintenant. Confirmer quand même ?'
              : 'Une glycémie de ${mgdlValue.toInt()} mg/dL est très élevée. Confirmer l\'enregistrement ?'),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Annuler')),
            ElevatedButton(
              onPressed: () => Navigator.pop(context, true),
              style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFFDC2626)),
              child: const Text('Confirmer', style: TextStyle(color: Colors.white)),
            ),
          ],
        ),
      );
      if (confirm != true || !context.mounted) return;
    }

    // Mild/moderate hypoglycemia gate (54–69 mg/dL) — show pre-validated advice
    // BEFORE saving so the user can act immediately. <54 already handled above.
    if (mgdlValue >= 54 && mgdlValue < 70) {
      await _showHypoAdviceSheet(context, mgdlValue);
      if (!context.mounted) return;
    }

    setState(() => _saving = true);

    final profile   = context.read<PatientProfileData?>();
    final unit      = profile?.unitPreference ?? 'mg/dL';
    final bloodSugarMgdl = unit == 'mmol/L' ? _glucoseValue * 18.0 : _glucoseValue;
    final foodChips = _selectedFoods.map((sf) => '${sf.item.label} (${sf.portion.label})').join(', ');
    final freeNote  = _mealNoteController.text.trim();
    final foodDesc  = [foodChips, freeNote].where((s) => s.isNotEmpty).join(' — ');

    await db.into(db.logEntries).insert(
      LogEntriesCompanion.insert(
        createdAt: DateTime.now(),
        bloodSugar: bloodSugarMgdl,
        insulinUnits: drift.Value(_insulinDose),
        mealType: drift.Value(_mealType),
        mealDescription: drift.Value(foodDesc.isNotEmpty ? foodDesc : null),
        clientUuid: const Uuid().v4(),
        loggedAt: drift.Value(_selectedTime),
        ramadanMode: drift.Value(_isRamadanMode),
        isSick: drift.Value(_isSick),
        isStressed: drift.Value(_isStressed),
        // isTired = true si fatigueLevel ≤ 2 (épuisé / très fatigué)
        isTired: drift.Value(_fatigueLevel != null && _fatigueLevel! <= 2),
        isActive: drift.Value(_isActive),
        sleepQuality: drift.Value(_sleepQuality),
        fatigueLevel: drift.Value(_fatigueLevel),
      ),
    );

    if (!mounted || !context.mounted) return;
    setState(() => _saving = false);

    // ── Success toast — immediate feedback before IAmina sheet opens ──────────
    final displayVal = unit == 'mmol/L'
        ? '${_glucoseValue.toStringAsFixed(1)} mmol/L'
        : '${bloodSugarMgdl.toInt()} mg/dL';
    final mealLabel = _mealType.isNotEmpty ? ' · $_mealType' : '';
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(children: [
          const Icon(Icons.check_circle_rounded, color: Colors.white, size: 16),
          const SizedBox(width: 8),
          Text('Glycémie enregistrée · $displayVal$mealLabel'),
        ]),
        backgroundColor: AminaTheme.teal600,
        behavior: SnackBarBehavior.floating,
        duration: const Duration(seconds: 2),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );

    final apiClient = context.read<ApiClient>();
    final contextMsg = _buildIAminaContextMessage(bloodSugarMgdl, unit);

    if (widget.isPage) {
      await _showPostSaveSheet(context, apiClient, contextMsg);
      if (!context.mounted) return;
      GoRouter.of(context).go('/dashboard');
    } else {
      Navigator.pop(context);
      await _showPostSaveSheet(context, apiClient, contextMsg);
    }
  }

  String _buildIAminaContextMessage(double mgdl, String unit) {
    final val = unit == 'mmol/L' ? '${(mgdl / 18.0).toStringAsFixed(1)} mmol/L' : '${mgdl.toInt()} mg/dL';
    final parts = <String>['Je viens de mesurer $val'];
    if (_mealType != 'À jeun') parts.add('après ${_mealType.toLowerCase()}');
    if (_selectedFoods.isNotEmpty) parts.add('(${_selectedFoods.map((sf) => sf.item.label).join(', ')})');
    if (_isSick)     parts.add('je suis malade');
    if (_isStressed) parts.add('je suis stressé');
    if (_sleepQuality == 'bad') parts.add('j\'ai mal dormi');
    if (_fatigueLevel == 1) parts.add('je suis épuisé');
    parts.add('Que penses-tu de cette mesure ?');
    return parts.join(', ');
  }

  // ── OCR pipeline ──────────────────────────────────────────────────────────
  // Phase 11-B: on-device glucometer reader.
  // No LLM involved — ML Kit + GlucoseOcrShield only.

  /// Entry point: asks camera vs gallery, runs OCR, shows confirmation sheet.
  /// Mobile: ML Kit on-device (offline, fast).
  /// Web: Gemini Vision backend (Phase 11-D).
  Future<void> _runOcr(BuildContext context, String unit) async {
    final api = context.read<ApiClient>();

    final source = await _showImageSourceSheet(context);
    if (source == null || !context.mounted) return;

    XFile? file;
    try {
      file = await ImagePicker().pickImage(
        source: source,
        imageQuality: 85,
        maxWidth: 1024,
      );
    } catch (_) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('Impossible d\'accéder à la caméra'),
        behavior: SnackBarBehavior.floating,
      ));
      return;
    }
    if (file == null || !context.mounted) return;

    setState(() => _ocrScanning = true);
    GlucoseOcrResult result;

    if (kIsWeb) {
      // Web path: read bytes → base64 → Gemini Vision backend
      try {
        final bytes   = await file.readAsBytes();
        final b64     = base64Encode(bytes);
        final mime    = file.mimeType ?? 'image/jpeg';
        final resp    = await api.analyzeGlucometerImage(b64, mime);
        if (!context.mounted) return;

        if (resp == null || resp.fallback || resp.value == null) {
          setState(() => _ocrScanning = false);
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text('Lecture impossible — veuillez saisir manuellement'),
            behavior: SnackBarBehavior.floating,
          ));
          return;
        }
        // Convert to mg/dL if needed so GlucoseOcrResult is always mg/dL
        final mgdl = resp.unit == 'mmol/L' ? resp.value! * 18.0 : resp.value!;
        result = GlucoseOcrResult(
          value:       mgdl,
          confidence:  resp.confidence == 'high' ? 0.95 : 0.70,
          rawText:     'Gemini Vision: ${resp.value} ${resp.unit}',
          unitWasMmol: resp.unit == 'mmol/L',
        );
      } catch (_) {
        if (!context.mounted) return;
        setState(() => _ocrScanning = false);
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Lecture impossible — veuillez saisir manuellement'),
          behavior: SnackBarBehavior.floating,
        ));
        return;
      }
    } else {
      // Mobile path: ML Kit on-device OCR (offline)
      try {
        final inputImage = InputImage.fromFilePath(file.path);
        final recognizer = TextRecognizer(script: TextRecognitionScript.latin);
        try {
          final recognized = await recognizer.processImage(inputImage);
          result = GlucoseOcrShield.extract(recognized.text);
        } finally {
          recognizer.close();
        }
      } catch (_) {
        if (!context.mounted) return;
        setState(() => _ocrScanning = false);
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Lecture impossible — veuillez saisir manuellement'),
          behavior: SnackBarBehavior.floating,
        ));
        return;
      }
    }

    if (!context.mounted) return;
    setState(() => _ocrScanning = false);
    await _showOcrResultSheet(context, result, unit);
  }

  /// Bottom sheet: camera vs gallery picker.
  Future<ImageSource?> _showImageSourceSheet(BuildContext context) {
    return showModalBottomSheet<ImageSource>(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (_) => Container(
        padding: EdgeInsets.fromLTRB(24, 16, 24, MediaQuery.of(context).padding.bottom + 20),
        decoration: BoxDecoration(
          color: AminaTheme.bg(context),
          borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
        ),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Container(width: 40, height: 4, decoration: BoxDecoration(color: AminaTheme.divider(context), borderRadius: BorderRadius.circular(99))),
          const SizedBox(height: 20),
          const Text('Lire la glycémie', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
          const SizedBox(height: 6),
          Text('Pointez vers l\'écran de votre glucomètre', style: TextStyle(fontSize: 12, color: AminaTheme.textSecondary(context))),
          const SizedBox(height: 20),
          _OcrSourceTile(
            icon: Icons.camera_alt_outlined,
            label: 'Prendre une photo',
            onTap: () => Navigator.pop(context, ImageSource.camera),
          ),
          const SizedBox(height: 10),
          _OcrSourceTile(
            icon: Icons.photo_library_outlined,
            label: 'Choisir depuis la galerie',
            onTap: () => Navigator.pop(context, ImageSource.gallery),
          ),
        ]),
      ),
    );
  }

  /// Confirmation sheet: shows what the OCR read, user accepts or corrects.
  Future<void> _showOcrResultSheet(BuildContext context, GlucoseOcrResult result, String unit) async {
    final accepted = await showModalBottomSheet<double?>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => _OcrResultSheet(result: result, userUnit: unit),
    );

    if (accepted == null || !mounted) return;

    // Convert back to user unit if needed
    final displayValue = unit == 'mmol/L' ? accepted / 18.0 : accepted;
    final displayStr   = unit == 'mmol/L'
        ? displayValue.toStringAsFixed(1)
        : displayValue.toInt().toString();

    setState(() {
      _glucoseValue = displayValue;
      _manualController.text = displayStr;
    });
    HapticFeedback.mediumImpact();
  }

  // ── Meal photo pipeline (Phase 11-C) ────────────────────────────────────
  // Gemini Vision identifies foods in the meal photo.
  // Result is mapped to CulinaryItem chips — fuzzy match on French labels.
  // Never auto-selects silently: a SnackBar confirms what was added.

  /// Entry point: pick source → send to backend → pre-fill food chips.
  Future<void> _runMealAnalysis(BuildContext context) async {
    // Capture context-dependent objects BEFORE any await to satisfy
    // use_build_context_synchronously — ScaffoldMessenger and ApiClient
    // must not be read after an async gap.
    final messenger = ScaffoldMessenger.of(context);
    final api       = context.read<ApiClient>();

    // Reuse the glucometer source picker (same UX)
    final source = await _showImageSourceSheet(context);
    if (source == null || !mounted) return;

    XFile? file;
    try {
      file = await ImagePicker().pickImage(
        source: source,
        imageQuality: 80,
        maxWidth: 1280,
      );
    } catch (_) {
      if (!mounted) return;
      messenger.showSnackBar(const SnackBar(
        content: Text('Impossible d\'accéder à la caméra'),
        behavior: SnackBarBehavior.floating,
      ));
      return;
    }
    if (file == null || !mounted) return;

    setState(() => _mealScanning = true);

    final bytes  = await file.readAsBytes();
    final mime   = _mimeFromPath(file.path);
    final result = await api.analyzeMealImage(bytes, mimeType: mime);

    if (!mounted) return;
    setState(() => _mealScanning = false);

    if (result == null) {
      messenger.showSnackBar(const SnackBar(
        content: Text('Analyse indisponible — sélectionnez manuellement'),
        behavior: SnackBarBehavior.floating,
      ));
      return;
    }

    if (result.fallback || result.foods.isEmpty) {
      messenger.showSnackBar(const SnackBar(
        content: Text('Je n\'ai pas reconnu les aliments — sélectionnez manuellement'),
        behavior: SnackBarBehavior.floating,
      ));
      return;
    }

    final matched = _matchFoodsToChips(result.foods);
    if (matched.isEmpty) {
      messenger.showSnackBar(SnackBar(
        content: Text(
          'Aliments détectés (${result.foods.join(', ')}) — '
          'introuvables dans la liste, sélectionnez manuellement',
        ),
        behavior: SnackBarBehavior.floating,
      ));
      return;
    }

    setState(() {
      for (final item in matched) {
        if (!_selectedFoods.any((s) => s.item.id == item.id)) {
          _selectedFoods.add(_SelectedFood(item: item));
        }
      }
    });
    HapticFeedback.mediumImpact();

    final names  = matched.map((f) => f.label).join(', ');
    final suffix = result.confidence == 'high' ? '' : ' (vérifiez)';
    messenger.showSnackBar(SnackBar(
      content: Text(
        '${matched.length} aliment${matched.length > 1 ? 's' : ''} '
        'ajouté${matched.length > 1 ? 's' : ''} : $names$suffix',
      ),
      behavior: SnackBarBehavior.floating,
    ));
  }

  /// Fuzzy-match Gemini food names to CulinaryItem chips.
  /// Tries exact match first, then containment in both directions.
  List<CulinaryItem> _matchFoodsToChips(List<String> foodNames) {
    final matched = <CulinaryItem>[];
    for (final food in foodNames) {
      final lower = food.toLowerCase().trim();
      CulinaryItem? found;
      for (final item in universalFoods) {
        final label = item.label.toLowerCase();
        if (label == lower || label.contains(lower) || lower.contains(label)) {
          found = item;
          break;
        }
      }
      if (found != null) matched.add(found);
    }
    return matched;
  }

  /// Derive MIME type from file extension.
  String _mimeFromPath(String path) {
    final ext = path.toLowerCase().split('.').last;
    return switch (ext) {
      'png'  => 'image/png',
      'webp' => 'image/webp',
      _      => 'image/jpeg',
    };
  }

  Future<void> _showHypoAdviceSheet(BuildContext context, double mgdlValue) async {
    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => _HypoAdviceSheet(mgdl: mgdlValue),
    );
  }

  Future<void> _showPostSaveSheet(BuildContext context, ApiClient api, String message) async {
    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => _IaminaPostSaveSheet(apiClient: api, contextMessage: message),
    );
  }
}

// ── Post-save IAmina sheet ────────────────────────────────────────────────────

class _IaminaPostSaveSheet extends StatefulWidget {
  final ApiClient apiClient;
  final String contextMessage;
  const _IaminaPostSaveSheet({required this.apiClient, required this.contextMessage});

  @override
  State<_IaminaPostSaveSheet> createState() => _IaminaPostSaveSheetState();
}

class _IaminaPostSaveSheetState extends State<_IaminaPostSaveSheet> {
  String? _reply;
  bool _loading = true;
  bool _isEmergency = false;

  @override
  void initState() { super.initState(); _fetchReply(); }

  Future<void> _fetchReply() async {
    try {
      final resp = await widget.apiClient.chatWithAmina(widget.contextMessage);
      if (!mounted) return;
      setState(() { _reply = resp?.reply ?? 'Je n\'ai pas pu analyser cette mesure. Réessaie dans un instant.'; _isEmergency = resp?.isEmergency ?? false; _loading = false; });
    } catch (_) {
      if (!mounted) return;
      setState(() { _reply = 'Analyse temporairement indisponible — tes données sont bien enregistrées.'; _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    const emergencyColor = Color(0xFFDC2626);
    return Container(
      padding: EdgeInsets.fromLTRB(24, 20, 24, MediaQuery.of(context).padding.bottom + 24),
      decoration: BoxDecoration(color: AminaTheme.bg(context), borderRadius: const BorderRadius.vertical(top: Radius.circular(28))),
      child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
        Center(child: Container(width: 40, height: 4, decoration: BoxDecoration(color: AminaTheme.divider(context), borderRadius: BorderRadius.circular(99)))),
        const SizedBox(height: 20),
        Row(children: [
          Container(width: 44, height: 44, decoration: BoxDecoration(gradient: AminaTheme.heroGradient, shape: BoxShape.circle),
            child: const Center(child: Text('I', style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w800)))),
          const SizedBox(width: 12),
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('IAmina', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: AminaTheme.textPrimary(context))),
            Text('Analyse de ta mesure', style: TextStyle(fontSize: 12, color: AminaTheme.textSecondary(context))),
          ]),
        ]),
        const SizedBox(height: 20),
        AnimatedSwitcher(
          duration: const Duration(milliseconds: 350),
          child: _loading
              ? _buildSkeleton(context)
              : Container(
                  key: const ValueKey('reply'),
                  width: double.infinity,
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: _isEmergency ? emergencyColor.withValues(alpha: 0.08) : AminaTheme.teal500.withValues(alpha: 0.06),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: _isEmergency ? emergencyColor.withValues(alpha: 0.3) : AminaTheme.teal500.withValues(alpha: 0.2)),
                  ),
                  child: Text(_reply!, style: TextStyle(fontSize: 14, height: 1.55, color: AminaTheme.textPrimary(context))),
                ),
        ),
        const SizedBox(height: 20),
        SizedBox(
          width: double.infinity, height: 50,
          child: ElevatedButton(
            onPressed: () => Navigator.pop(context),
            style: ElevatedButton.styleFrom(backgroundColor: AminaTheme.teal500, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(99)), elevation: 0),
            child: const Text('Continuer', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: Colors.white)),
          ),
        ),
      ]),
    );
  }

  Widget _buildSkeleton(BuildContext context) {
    return Column(key: const ValueKey('skeleton'), crossAxisAlignment: CrossAxisAlignment.start, children: [
      const _SkeletonLine(width: double.infinity, height: 14),
      const SizedBox(height: 8),
      const _SkeletonLine(width: double.infinity, height: 14),
      const SizedBox(height: 8),
      const _SkeletonLine(width: 200, height: 14),
      const SizedBox(height: 6),
      Text('IAmina analyse ta mesure…', style: TextStyle(fontSize: 12, color: AminaTheme.textSecondary(context))),
    ]);
  }
}

// ── Hypo Advice Sheet (pre-validated, non-AI) ────────────────────────────────
// Shown when glucose is 54–69 mg/dL — immediate, fixed ADA advice.

class _HypoAdviceSheet extends StatelessWidget {
  final double mgdl;
  const _HypoAdviceSheet({required this.mgdl});

  @override
  Widget build(BuildContext context) {
    const hypoColor = Color(0xFFF97316); // orange
    const hypoBg    = Color(0xFFFFF7ED);

    return Container(
      padding: EdgeInsets.fromLTRB(24, 20, 24, MediaQuery.of(context).padding.bottom + 28),
      decoration: BoxDecoration(color: AminaTheme.bg(context), borderRadius: const BorderRadius.vertical(top: Radius.circular(28))),
      child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
        Center(child: Container(width: 40, height: 4, decoration: BoxDecoration(color: AminaTheme.divider(context), borderRadius: BorderRadius.circular(99)))),
        const SizedBox(height: 20),
        // Header
        Row(children: [
          Container(
            width: 44, height: 44,
            decoration: BoxDecoration(color: hypoBg, borderRadius: BorderRadius.circular(14), border: Border.all(color: hypoColor.withValues(alpha: 0.35))),
            child: const Center(child: Text('⚡', style: TextStyle(fontSize: 22))),
          ),
          const SizedBox(width: 12),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('Hypoglycémie détectée', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w800, color: hypoColor)),
            Text('${mgdl.toInt()} mg/dL · Règle 15-15 ADA', style: TextStyle(fontSize: 12, color: AminaTheme.textSecondary(context))),
          ])),
        ]),
        const SizedBox(height: 18),
        // Rule 15-15 card
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: hypoBg,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: hypoColor.withValues(alpha: 0.3)),
          ),
          child: const Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Que faire maintenant ?', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: hypoColor)),
            SizedBox(height: 10),
            _HypoStep('1', 'Prenez 15 g de glucides rapides', '3 morceaux de sucre · 150 mL de jus · 1 sachet de gel'),
            SizedBox(height: 10),
            _HypoStep('2', 'Attendez 15 minutes', 'Ne resucrez pas immédiatement — l\'effet prend du temps'),
            SizedBox(height: 10),
            _HypoStep('3', 'Remesurer', 'Si toujours < 70 mg/dL, répétez le cycle'),
            SizedBox(height: 10),
            _HypoStep('4', 'Mangez un encas si le repas est loin', 'Ex : 1 biscuit ou 1 tranche de pain'),
          ]),
        ),
        const SizedBox(height: 12),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(color: AminaTheme.subtleBg(context), borderRadius: BorderRadius.circular(10)),
          child: Row(children: [
            const Icon(Icons.info_outline, size: 14, color: AminaTheme.ink400),
            const SizedBox(width: 8),
            Expanded(child: Text('Ta mesure est bien enregistrée. IAmina sera informée de l\'hypoglycémie.',
              style: TextStyle(fontSize: 11, color: AminaTheme.textSecondary(context), height: 1.4))),
          ]),
        ),
        const SizedBox(height: 20),
        SizedBox(
          width: double.infinity, height: 50,
          child: ElevatedButton(
            onPressed: () => Navigator.pop(context),
            style: ElevatedButton.styleFrom(
              backgroundColor: hypoColor,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(99)),
              elevation: 0,
            ),
            child: const Text('J\'ai compris', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: Colors.white)),
          ),
        ),
      ]),
    );
  }
}

class _HypoStep extends StatelessWidget {
  final String number;
  final String title;
  final String sub;
  const _HypoStep(this.number, this.title, this.sub);

  @override
  Widget build(BuildContext context) => Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
    Container(
      width: 22, height: 22,
      decoration: BoxDecoration(color: const Color(0xFFF97316), borderRadius: BorderRadius.circular(6)),
      child: Center(child: Text(number, style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w800))),
    ),
    const SizedBox(width: 10),
    Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(title, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: Color(0xFF7C2D12))),
      Text(sub, style: const TextStyle(fontSize: 11, color: Color(0xFF9A3412), height: 1.35)),
    ])),
  ]);
}

// ── Reusable widgets ──────────────────────────────────────────────────────────

class _SliderLabel extends StatelessWidget {
  final String text;
  final Color color;
  const _SliderLabel(this.text, this.color);
  @override
  Widget build(BuildContext context) =>
      Text(text, style: TextStyle(fontSize: 10, color: color.withValues(alpha: 0.5), fontWeight: FontWeight.w600));
}

class _SectionLabel extends StatelessWidget {
  final String text;
  final BuildContext ctx;
  const _SectionLabel(this.text, this.ctx);
  @override
  Widget build(BuildContext context) =>
      Text(text, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AminaTheme.textSecondary(ctx), letterSpacing: 0.6));
}



class _SkeletonLine extends StatefulWidget {
  final double width;
  final double height;
  const _SkeletonLine({required this.width, required this.height});
  @override
  State<_SkeletonLine> createState() => _SkeletonLineState();
}

class _SkeletonLineState extends State<_SkeletonLine> with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  late final Animation<double> _anim;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 1100))..repeat(reverse: true);
    _anim = Tween<double>(begin: 0.3, end: 0.7).animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeInOut));
  }

  @override
  void dispose() { _ctrl.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _anim,
      builder: (_, __) => Container(
        width: widget.width, height: widget.height,
        decoration: BoxDecoration(color: AminaTheme.divider(context).withValues(alpha: _anim.value), borderRadius: BorderRadius.circular(6)),
      ),
    );
  }
}

// ── OCR: source picker tile ───────────────────────────────────────────────────

class _OcrSourceTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  const _OcrSourceTile({required this.icon, required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        decoration: BoxDecoration(
          color: AminaTheme.subtleBg(context),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AminaTheme.divider(context)),
        ),
        child: Row(children: [
          Container(
            width: 40, height: 40,
            decoration: BoxDecoration(
              color: AminaTheme.teal500.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, size: 20, color: AminaTheme.teal600),
          ),
          const SizedBox(width: 14),
          Text(label, style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: AminaTheme.textPrimary(context))),
          const Spacer(),
          Icon(Icons.chevron_right, size: 18, color: AminaTheme.textSecondary(context)),
        ]),
      ),
    );
  }
}

// ── OCR: result confirmation sheet ───────────────────────────────────────────
// Shown after ML Kit + GlucoseOcrShield — user MUST confirm before value lands.
// Never auto-fills silently: every path requires an explicit user action.
//
// Cases handled:
//   isHI / isLO          → warning card + forced manual entry
//   hasValue, conf ≥ 0.80 → large value display + "Utiliser cette valeur"
//   hasValue, conf < 0.80 → value display + editable correction field + "Confirmer"
//   !hasValue             → no OCR read → editable field only

class _OcrResultSheet extends StatefulWidget {
  final GlucoseOcrResult result;
  final String userUnit; // 'mg/dL' or 'mmol/L' — for display only; we always return mg/dL
  const _OcrResultSheet({required this.result, required this.userUnit});

  @override
  State<_OcrResultSheet> createState() => _OcrResultSheetState();
}

class _OcrResultSheetState extends State<_OcrResultSheet> {
  late final TextEditingController _ctrl;

  @override
  void initState() {
    super.initState();
    final r = widget.result;
    String initial = '';
    if (r.hasValue) {
      final v = r.value!;
      initial = widget.userUnit == 'mmol/L'
          ? (v / 18.0).toStringAsFixed(1)
          : v.toInt().toString();
    }
    _ctrl = TextEditingController(text: initial);
  }

  @override
  void dispose() { _ctrl.dispose(); super.dispose(); }

  // ── confirm handler ──────────────────────────────────────────────────────────

  void _onConfirm() {
    final r = widget.result;
    double mgdl;

    if (r.isHI || r.isLO || !r.hasValue || r.confidence < 0.80) {
      // User provided or corrected the value manually
      final raw    = _ctrl.text.trim().replaceAll(',', '.');
      final parsed = double.tryParse(raw);
      if (parsed == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Valeur invalide'), behavior: SnackBarBehavior.floating),
        );
        return;
      }
      mgdl = widget.userUnit == 'mmol/L' ? parsed * 18.0 : parsed;
    } else {
      // High-confidence OCR — GlucoseOcrShield already output mg/dL
      mgdl = r.value!;
    }

    Navigator.pop(context, mgdl);
  }

  // ── build ────────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final r = widget.result;
    return Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: Container(
        padding: EdgeInsets.fromLTRB(24, 20, 24, MediaQuery.of(context).padding.bottom + 28),
        decoration: BoxDecoration(
          color: AminaTheme.bg(context),
          borderRadius: const BorderRadius.vertical(top: Radius.circular(28)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(child: Container(
              width: 40, height: 4,
              decoration: BoxDecoration(color: AminaTheme.divider(context), borderRadius: BorderRadius.circular(99)),
            )),
            const SizedBox(height: 20),
            _buildHeader(context, r),
            const SizedBox(height: 18),
            if (r.isHI || r.isLO)
              _buildHiLoContent(context, r)
            else
              _buildValueContent(context, r),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context, GlucoseOcrResult r) {
    final String emoji;
    final String title;
    final String sub;
    final Color color;

    if (r.isHI) {
      emoji = '⚠️'; title = 'Glucomètre saturé — HI';
      sub   = 'Valeur trop élevée pour être mesurée (> ~600 mg/dL)';
      color = const Color(0xFFF59E0B);
    } else if (r.isLO) {
      emoji = '⚠️'; title = 'Glucomètre saturé — LO';
      sub   = 'Valeur trop basse pour être mesurée (< ~20 mg/dL)';
      color = const Color(0xFFDC2626);
    } else if (!r.hasValue) {
      emoji = '🔍'; title = 'Aucune valeur détectée';
      sub   = 'Saisissez la valeur manuellement';
      color = const Color(0xFF64748B);
    } else if (r.confidence >= 0.80) {
      emoji = '📷'; title = 'Valeur lue par la caméra';
      sub   = 'Vérifiez puis confirmez';
      color = AminaTheme.teal500;
    } else {
      emoji = '🔍'; title = 'Lecture incertaine';
      sub   = 'Corrigez la valeur si nécessaire';
      color = const Color(0xFFF59E0B);
    }

    return Row(children: [
      Text(emoji, style: const TextStyle(fontSize: 28)),
      const SizedBox(width: 12),
      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(title, style: TextStyle(fontSize: 15, fontWeight: FontWeight.w800, color: color)),
        Text(sub,   style: TextStyle(fontSize: 12, color: AminaTheme.textSecondary(context))),
      ])),
    ]);
  }

  // ── HI / LO content ─────────────────────────────────────────────────────────

  Widget _buildHiLoContent(BuildContext context, GlucoseOcrResult r) {
    final col = r.isHI ? const Color(0xFFF59E0B) : const Color(0xFFDC2626);
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Container(
        width: double.infinity,
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: col.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: col.withValues(alpha: 0.3)),
        ),
        child: Text(
          r.isHI
              ? 'Votre glucomètre affiche "HI" — glycémie supérieure à la plage mesurable. Contactez votre médecin si cela persiste.'
              : 'Votre glucomètre affiche "LO" — glycémie inférieure à la plage mesurable. Prenez du sucre rapidement.',
          style: TextStyle(fontSize: 13, height: 1.5, color: AminaTheme.textPrimary(context)),
        ),
      ),
      const SizedBox(height: 16),
      Text('Saisissez manuellement la valeur :', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AminaTheme.textPrimary(context))),
      const SizedBox(height: 10),
      _buildManualField(context),
      const SizedBox(height: 16),
      _buildConfirmButton(col, 'Confirmer'),
    ]);
  }

  // ── normal value content ─────────────────────────────────────────────────────

  Widget _buildValueContent(BuildContext context, GlucoseOcrResult r) {
    final isHighConf = r.hasValue && r.confidence >= 0.80;
    final confColor  = isHighConf ? AminaTheme.teal500 : const Color(0xFFF59E0B);
    final confLabel  = isHighConf ? 'Confiance élevée' : 'Confiance faible — vérifiez';
    final btnColor   = isHighConf ? AminaTheme.teal500 : const Color(0xFFF59E0B);
    final btnLabel   = isHighConf ? 'Utiliser cette valeur' : 'Confirmer';

    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [

      // Value display card — only when a value was actually extracted
      if (r.hasValue) ...[
        Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(vertical: 20),
          decoration: BoxDecoration(
            color: AminaTheme.teal500.withValues(alpha: 0.06),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AminaTheme.teal500.withValues(alpha: 0.2)),
          ),
          child: Column(children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.baseline,
              textBaseline: TextBaseline.alphabetic,
              children: [
                Text(
                  widget.userUnit == 'mmol/L'
                      ? (r.value! / 18.0).toStringAsFixed(1)
                      : r.value!.toInt().toString(),
                  style: const TextStyle(
                    fontSize: 60, fontWeight: FontWeight.w800,
                    height: 1.0, letterSpacing: -2, color: AminaTheme.teal500,
                  ),
                ),
                const SizedBox(width: 6),
                Text(widget.userUnit,
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: AminaTheme.teal500.withValues(alpha: 0.7))),
              ],
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(color: confColor.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(99)),
              child: Text(confLabel, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: confColor)),
            ),
            if (r.unitWasMmol) ...[
              const SizedBox(height: 6),
              Text('Converti depuis mmol/L × 18',
                style: TextStyle(fontSize: 10, color: AminaTheme.textSecondary(context))),
            ],
          ]),
        ),
        const SizedBox(height: 12),
      ],

      // Raw OCR text (transparency / debug aid for the user)
      if (r.rawText.isNotEmpty && r.rawText.length < 60)
        Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: Text('Texte reconnu : "${r.rawText}"',
            style: TextStyle(fontSize: 11, color: AminaTheme.textSecondary(context), fontStyle: FontStyle.italic)),
        ),

      // Editable correction field for low-confidence or no-value
      if (!isHighConf) ...[
        Text('Corrigez si nécessaire :', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AminaTheme.textPrimary(context))),
        const SizedBox(height: 10),
        _buildManualField(context),
        const SizedBox(height: 16),
      ],

      // Primary action
      _buildConfirmButton(btnColor, btnLabel),
      const SizedBox(height: 10),

      // Secondary: dismiss without applying value
      SizedBox(
        width: double.infinity, height: 44,
        child: TextButton(
          onPressed: () => Navigator.pop(context, null),
          child: Text('Saisir manuellement',
            style: TextStyle(fontSize: 14, color: AminaTheme.textSecondary(context))),
        ),
      ),
    ]);
  }

  // ── shared helpers ───────────────────────────────────────────────────────────

  Widget _buildManualField(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AminaTheme.subtleBg(context),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AminaTheme.divider(context)),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: TextField(
        controller: _ctrl,
        keyboardType: const TextInputType.numberWithOptions(decimal: true),
        style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: AminaTheme.textPrimary(context)),
        decoration: InputDecoration(
          border: InputBorder.none,
          hintText: widget.userUnit == 'mmol/L' ? 'Ex : 6.5' : 'Ex : 120',
          hintStyle: TextStyle(color: AminaTheme.textSecondary(context)),
          suffixText: widget.userUnit,
          suffixStyle: TextStyle(fontSize: 13, color: AminaTheme.textSecondary(context)),
        ),
      ),
    );
  }

  Widget _buildConfirmButton(Color col, String label) {
    return SizedBox(
      width: double.infinity, height: 50,
      child: ElevatedButton(
        onPressed: _onConfirm,
        style: ElevatedButton.styleFrom(
          backgroundColor: col,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(99)),
          elevation: 0,
        ),
        child: Text(label, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: Colors.white)),
      ),
    );
  }
}
