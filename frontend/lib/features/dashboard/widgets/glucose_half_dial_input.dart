import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// Visual reference only, NOT the patient's prescribed glucose targets.
/// The five bands always show: red / amber / green / amber / red.
Color d22IllustrativeGlucoseArcColor(double mg) {
  if (mg < 70 || mg > 180) return const Color(0xFFCF475A);
  if (mg < 90 || mg > 160) return const Color(0xFFF0A447);
  return const Color(0xFF18A781);
}

/// Smooth ambient accent for the surrounding entry card, distinct from
/// medical safety classification. The five zones are illustrative only.
///
/// Use paired symmetric anchors so the background smoothly transitions
/// RED -> AMBER -> GREEN -> AMBER -> RED as the finger moves.
Color d22GlucoseDialAmbientColor(double? mgdl) {
  if (mgdl == null || !mgdl.isFinite) return const Color(0xFF198C78);
  const stops = <double>[40, 67, 82, 105, 145, 168, 187, 230];
  const accents = <Color>[
    Color(0xFFE36462),
    Color(0xFFE36462),
    Color(0xFFE9A348),
    Color(0xFF23A881),
    Color(0xFF23A881),
    Color(0xFFE9A348),
    Color(0xFFE36462),
    Color(0xFFE36462),
  ];
  final value = mgdl.clamp(stops.first, stops.last).toDouble();
  for (var i = 0; i < stops.length - 1; i++) {
    if (value <= stops[i + 1]) {
      final fraction =
          (value - stops[i]) / (stops[i + 1] - stops[i]);
      return Color.lerp(accents[i], accents[i + 1], fraction)!;
    }
  }
  return accents.last;
}

/// A visually descriptive zone; it NEVER substitutes for the separate
/// low-glucose safety warning or patient-specific glycemic targets.
enum D22GlucoseDialVisualZone {
  lowRed,
  lowAmber,
  centerGreen,
  highAmber,
  highRed,
}

D22GlucoseDialVisualZone? d22GlucoseDialVisualZone(double? mgdl) {
  if (mgdl == null || !mgdl.isFinite) return null;
  if (mgdl < 70) return D22GlucoseDialVisualZone.lowRed;
  if (mgdl < 90) return D22GlucoseDialVisualZone.lowAmber;
  if (mgdl <= 160) return D22GlucoseDialVisualZone.centerGreen;
  if (mgdl <= 180) return D22GlucoseDialVisualZone.highAmber;
  return D22GlucoseDialVisualZone.highRed;
}

/// A segmented dial deliberately gives more touch space to the central band.
/// Values remain physically expressed in mg/dL; this is presentation only.
/// Inverse and forward functions share the same breakpoints to avoid drift.
const _d22MgKnots = <double>[40, 70, 90, 160, 180, 320];
const _d22ArcKnots = <double>[0, .15, .29, .71, .85, 1];

double d22DialFractionForMgdl(double mg) {
  final value = mg.clamp(_d22MgKnots.first, _d22MgKnots.last).toDouble();
  for (var i = 0; i < _d22MgKnots.length - 1; i++) {
    if (value <= _d22MgKnots[i + 1]) {
      final t = (value - _d22MgKnots[i]) /
          (_d22MgKnots[i + 1] - _d22MgKnots[i]);
      return _d22ArcKnots[i] +
          t * (_d22ArcKnots[i + 1] - _d22ArcKnots[i]);
    }
  }
  return 1;
}

double d22DialMgdlForFraction(double fraction) {
  final value = fraction.clamp(0.0, 1.0).toDouble();
  for (var i = 0; i < _d22ArcKnots.length - 1; i++) {
    if (value <= _d22ArcKnots[i + 1]) {
      final t = (value - _d22ArcKnots[i]) /
          (_d22ArcKnots[i + 1] - _d22ArcKnots[i]);
      return _d22MgKnots[i] +
          t * (_d22MgKnots[i + 1] - _d22MgKnots[i]);
    }
  }
  return _d22MgKnots.last;
}

/// D22 fine adjustment uses integer mg/dL or tenths of mmol/L relative to the
/// displayed value, not raw finger position. It never seeds a missing reading,
/// imposes a new clinical range, or truncates a direct measurement to the dial.
double? d22FineAdjustedMgdl(double? currentMgdl, String unit, int direction) {
  if (currentMgdl == null ||
      !currentMgdl.isFinite ||
      currentMgdl <= 0 ||
      (direction != -1 && direction != 1)) {
    return null;
  }
  final double? next = switch (unit) {
    'mg/dL' => currentMgdl.roundToDouble() + direction,
    'mmol/L' => (((currentMgdl / 18.0 * 10).round() + direction) / 10.0) * 18.0,
    _ => null,
  };
  return next != null && next.isFinite && next > 0 ? next : null;
}

/// Progressive repeat cadence for a held fine adjustment, bounded so a
/// precision control does not become impossible to stop on touch devices.
Duration d221HoldRepeatDelay(int completedRepeats) {
  if (completedRepeats < 3) return const Duration(milliseconds: 270);
  if (completedRepeats < 9) return const Duration(milliseconds: 155);
  return const Duration(milliseconds: 85);
}

/// Actual reading input — keeps the existing journal save pipeline intact.
/// Drag the half-ring for fast selection; edit the number directly or use
/// localized fine-step controls for a precise measurement.
class GlucoseHalfDialInput extends StatefulWidget {
  const GlucoseHalfDialInput({
    super.key,
    required this.controller,
    required this.unit,
    required this.valueMgdl,
    required this.onTextChanged,
    required this.onValueSelected,
    required this.onToggleUnit,
  });

  final TextEditingController controller;
  final String unit;
  final double? valueMgdl;
  final ValueChanged<String> onTextChanged;
  final ValueChanged<double> onValueSelected;
  final VoidCallback? onToggleUnit;

  static const double minScale = 40;
  static const double maxScale = 320;

  @override
  State<GlucoseHalfDialInput> createState() => _GlucoseHalfDialInputState();
}

class _GlucoseHalfDialInputState extends State<GlucoseHalfDialInput> {
  Timer? _holdTimer;
  int? _holdDirection;
  int _completedRepeats = 0;
  int? _arcPointer;
  bool _arcDragging = false;

  @override
  void didUpdateWidget(covariant GlucoseHalfDialInput oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.unit != widget.unit || widget.valueMgdl == null) {
      _stopHold();
    }
  }

  @override
  void dispose() {
    _stopHold();
    super.dispose();
  }

  void _stopHold() {
    _holdTimer?.cancel();
    _holdTimer = null;
    _holdDirection = null;
    _completedRepeats = 0;
  }

  bool _applyFineStep(int direction) {
    final next = d22FineAdjustedMgdl(widget.valueMgdl, widget.unit, direction);
    if (next == null) return false;
    widget.onValueSelected(next);
    return true;
  }

  void _scheduleHeldStep() {
    if (!mounted || _holdDirection == null) return;
    final direction = _holdDirection!;
    _holdTimer = Timer(d221HoldRepeatDelay(_completedRepeats), () {
      if (!mounted || _holdDirection != direction) return;
      if (!_applyFineStep(direction)) {
        _stopHold();
        return;
      }
      _completedRepeats++;
      _scheduleHeldStep();
    });
  }

  void _startHold(int direction) {
    _stopHold();
    if (!_applyFineStep(direction)) return;
    _holdDirection = direction;
    _scheduleHeldStep();
  }

  void _beginArcPointer(PointerDownEvent event, Size size) {
    if (_arcPointer != null) return;
    if (!_selectArc(event.localPosition, size)) return;
    _arcPointer = event.pointer;
    setState(() => _arcDragging = true);
  }

  void _moveArcPointer(PointerMoveEvent event, Size size) {
    if (event.pointer == _arcPointer) _selectArc(event.localPosition, size);
  }

  void _endArcPointer(int pointer) {
    if (pointer != _arcPointer) return;
    _arcPointer = null;
    if (mounted) setState(() => _arcDragging = false);
  }

  String _copy(BuildContext context, String fr, String en, String ar) =>
      switch (Localizations.localeOf(context).languageCode) {
        'fr' => fr,
        'ar' => ar,
        _ => en,
      };

  String _display(double mg) =>
      widget.unit == 'mmol/L'
          ? (mg / 18.0).toStringAsFixed(1)
          : mg.round().toString();

  bool _selectArc(Offset localPoint, Size size) {
    final center = Offset(size.width / 2, size.height - 18);
    final rel = localPoint - center;
    final radius = math.min(size.width / 2 - 30, size.height - 35);
    // Larger ~60px touch target around the track. Project a finger placed
    // slightly inside/outside the ring onto the real semicircle, so fast
    // drags remain responsive and never jump to the opposite end.
    if (rel.dy > 25 || rel.distance < radius * 0.38 ||
        rel.distance > radius + 76) return false;
    final projectedY = math.min(rel.dy, 0.0);
    var radians = math.atan2(projectedY, rel.dx);
    if (radians <= 0) radians += math.pi * 2;
    final fraction = ((radians - math.pi) / math.pi).clamp(0.0, 1.0);
    final mg = d22DialMgdlForFraction(fraction).roundToDouble();
    // Update just the reading. Firing a platform haptic on *every* pixel
    // move slows iOS Safari down and can break finger tracking.
    if (mg != widget.valueMgdl) widget.onValueSelected(mg);
    return true;
  }

  @override
  Widget build(BuildContext context) {
    final controller = widget.controller;
    final unit = widget.unit;
    final valueMgdl = widget.valueMgdl;
    final onTextChanged = widget.onTextChanged;
    final onValueSelected = widget.onValueSelected;
    final onToggleUnit = widget.onToggleUnit;
    const minScale = GlucoseHalfDialInput.minScale;
    const maxScale = GlucoseHalfDialInput.maxScale;
    final theme = Theme.of(context);
    final colors = theme.colorScheme;
    final selected = valueMgdl?.clamp(minScale, maxScale).toDouble();
    final displayed = selected ?? 140.0;
    // Fine adjustment follows the entered reading even outside the visual
    // dial scale; unlike the arc, it must never clamp a valid direct value.
    final fineMinus = d22FineAdjustedMgdl(valueMgdl, unit, -1);
    final finePlus = d22FineAdjustedMgdl(valueMgdl, unit, 1);

    return Column(
      key: const Key('glucose-half-dial-input'),
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            Expanded(
              child: SizedBox(
                height: 46,
                child: Align(
                  alignment: AlignmentDirectional.centerStart,
                  child: _arcDragging && valueMgdl != null
                      ? Column(
                          key: const Key('glucose-drag-reading'),
                          crossAxisAlignment: CrossAxisAlignment.start,
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Text(
                              _copy(context, 'VALEUR', 'READING', 'القراءة'),
                              maxLines: 1,
                              style: theme.textTheme.labelSmall?.copyWith(
                                color: colors.onSurfaceVariant,
                                fontSize: 10,
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                            Text(
                              '${_display(valueMgdl)} $unit',
                              key: const Key('glucose-drag-reading-value'),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: theme.textTheme.titleMedium?.copyWith(
                                fontWeight: FontWeight.w900,
                                fontSize: 21,
                                color: colors.onSurface,
                              ),
                            ),
                          ],
                        )
                      : Text(
                          _copy(context, 'SAISIE DIRECTE', 'DIRECT INPUT',
                              'إدخال مباشر'),
                          style: theme.textTheme.labelSmall?.copyWith(
                            color: colors.onSurfaceVariant,
                            fontWeight: FontWeight.w800,
                            letterSpacing: 1,
                          ),
                        ),
                ),
              ),
            ),
            OutlinedButton(
              key: const Key('glucose-half-dial-unit-toggle'),
              onPressed: onToggleUnit,
              style: OutlinedButton.styleFrom(
                minimumSize: const Size(0, 46),
                padding: const EdgeInsets.symmetric(horizontal: 12),
                side: BorderSide(color: colors.outlineVariant),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(13),
                ),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(unit, style: const TextStyle(
                    fontWeight: FontWeight.w800, fontSize: 13,
                  )),
                  const SizedBox(width: 7),
                  const Icon(Icons.swap_horiz_rounded, size: 19),
                  Text(unit == 'mg/dL' ? 'mmol/L' : 'mg/dL',
                      style: const TextStyle(fontSize: 12)),
                ],
              ),
            ),
          ],
        ),
        const SizedBox(height: 14),
        LayoutBuilder(builder: (context, limits) {
          final width = math.min(limits.maxWidth, 354.0);
          final size = Size(width, width * .59);
          return Center(
            child: SizedBox(
              key: const Key('glucose-half-dial-gesture'),
              width: size.width,
              height: size.height,
              child: Stack(
                alignment: Alignment.center,
                children: [
                  Positioned.fill(
                    // iOS Safari: the parent SingleChildScrollView previously
                    // won the vertical-drag gesture arena, so the whole page
                    // moved instead of the dial. Claim this hit-tested dial
                    // surface immediately. The number editor is a separate
                    // Stack sibling ABOVE it and retains keyboard focus.
                    child: RawGestureDetector(
                      key: const Key('glucose-half-dial-touch-surface'),
                      behavior: HitTestBehavior.opaque,
                      gestures: <Type, GestureRecognizerFactory>{
                        EagerGestureRecognizer:
                            GestureRecognizerFactoryWithHandlers<
                                EagerGestureRecognizer>(
                          () => EagerGestureRecognizer(),
                          (recognizer) {},
                        ),
                      },
                      child: Listener(
                        behavior: HitTestBehavior.opaque,
                        onPointerDown: (event) => _beginArcPointer(event, size),
                        onPointerMove: (event) => _moveArcPointer(event, size),
                        onPointerUp: (event) => _endArcPointer(event.pointer),
                        onPointerCancel: (event) => _endArcPointer(event.pointer),
                        child: Semantics(
                        label: _copy(context,
                          'Sélecteur de glycémie par demi-cercle',
                          'Semicircle glucose input',
                          'محدد الغلوكوز نصف الدائري',
                        ),
                        value: valueMgdl == null
                            ? _copy(context, 'Aucune valeur', 'No value', 'لا قيمة')
                            : _display(valueMgdl) + ' ' + unit,
                        increasedValue: finePlus == null
                            ? null
                            : '${_display(finePlus)} $unit',
                        decreasedValue: fineMinus == null
                            ? null
                            : '${_display(fineMinus)} $unit',
                        onIncrease: finePlus == null
                            ? null
                            : () => onValueSelected(finePlus),
                        onDecrease: fineMinus == null
                            ? null
                            : () => onValueSelected(fineMinus),
                        child: CustomPaint(
                          key: const Key('glucose-half-dial-arc'),
                          painter: _PremiumGlucoseArcPainter(
                            fraction: d22DialFractionForMgdl(displayed),
                            hasValue: selected != null,
                            outline: colors.outlineVariant,
                            accent: d22GlucoseDialAmbientColor(valueMgdl),
                            dark: theme.brightness == Brightness.dark,
                          ),
                        ),
                      ),
                      ),
                    ),
                  ),
                  // The number sits INSIDE the semicircle. Its own
                  // hit target opens the numeric keyboard without moving
                  // the dial. No wide blocking plate and no +/- buttons.
                  Positioned(
                    bottom: 9,
                    child: Container(
                      key: const Key('glucose-half-dial-edit-center'),
                      width: 174,
                      padding: const EdgeInsets.fromLTRB(14, 7, 14, 10),
                      decoration: BoxDecoration(
                        color: colors.surface.withValues(alpha: .92),
                        borderRadius: BorderRadius.circular(19),
                        border: Border.all(
                          color: colors.outlineVariant.withValues(alpha: .55),
                        ),
                      ),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          TextField(
                            key: const Key('glucose-input'),
                            controller: controller,
                            textAlign: TextAlign.center,
                            keyboardType: const TextInputType.numberWithOptions(
                              decimal: true,
                            ),
                            inputFormatters: [
                              FilteringTextInputFormatter.allow(RegExp(r'[0-9,.]')),
                            ],
                            style: TextStyle(
                              fontSize: 39,
                              height: 1.05,
                              letterSpacing: -1.5,
                              fontWeight: FontWeight.w800,
                              color: colors.onSurface,
                            ),
                            decoration: InputDecoration(
                              hintText: '—',
                              isDense: true,
                              contentPadding: EdgeInsets.zero,
                              border: InputBorder.none,
                              hintStyle: TextStyle(color: colors.onSurfaceVariant),
                            ),
                            onChanged: onTextChanged,
                          ),
                          const SizedBox(height: 5),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Text(
                                unit,
                                style: theme.textTheme.labelSmall?.copyWith(
                                  color: colors.onSurfaceVariant,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                              const SizedBox(width: 6),
                              Icon(Icons.edit_rounded,
                                  color: colors.onSurfaceVariant, size: 13),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          );
        }),
        const SizedBox(height: 10),
        Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 354),
            child: Row(
              children: [
                Listener(
                  behavior: HitTestBehavior.opaque,
                  // Let IconButton's own InkResponse win the long-press
                  // gesture over its Tooltip; raw pointer up/cancel stops
                  // the repeating timer without competing recognizers.
                  onPointerUp: (_) => _stopHold(),
                  onPointerCancel: (_) => _stopHold(),
                  onPointerMove: (event) {
                    if (_holdDirection == -1 &&
                        !Rect.fromLTWH(0, 0, 48, 48)
                            .inflate(16)
                            .contains(event.localPosition)) {
                      _stopHold();
                    }
                  },
                  child: IconButton.outlined(
                  key: const Key('glucose-fine-minus'),
                  tooltip: _copy(context,
                    'Diminuer de ${unit == 'mmol/L' ? '0,1 mmol/L' : '1 mg/dL'}',
                    'Decrease by ${unit == 'mmol/L' ? '0.1 mmol/L' : '1 mg/dL'}',
                    'إنقاص ${unit == 'mmol/L' ? '0.1 mmol/L' : '1 mg/dL'}',
                  ),
                  onPressed: fineMinus == null
                      ? null
                      : () => onValueSelected(fineMinus),
                  onLongPress: fineMinus == null
                      ? null
                      : () => _startHold(-1),
                  icon: const Icon(Icons.remove_rounded),
                  style: IconButton.styleFrom(
                    minimumSize: const Size(48, 48),
                  ),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        _copy(context, 'RÉGLAGE PRÉCIS', 'FINE ADJUSTMENT',
                          'ضبط دقيق'),
                        textAlign: TextAlign.center,
                        style: theme.textTheme.labelSmall?.copyWith(
                          fontWeight: FontWeight.w800,
                          color: colors.onSurface,
                          fontSize: 10.5,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        unit == 'mmol/L' ? '0,1 mmol/L' : '1 mg/dL',
                        textAlign: TextAlign.center,
                        style: theme.textTheme.labelSmall?.copyWith(
                          color: colors.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 10),
                Listener(
                  behavior: HitTestBehavior.opaque,
                  // Let IconButton's own InkResponse win the long-press
                  // gesture over its Tooltip; raw pointer up/cancel stops
                  // the repeating timer without competing recognizers.
                  onPointerUp: (_) => _stopHold(),
                  onPointerCancel: (_) => _stopHold(),
                  onPointerMove: (event) {
                    if (_holdDirection == 1 &&
                        !Rect.fromLTWH(0, 0, 48, 48)
                            .inflate(16)
                            .contains(event.localPosition)) {
                      _stopHold();
                    }
                  },
                  child: IconButton.outlined(
                  key: const Key('glucose-fine-plus'),
                  tooltip: _copy(context,
                    'Augmenter de ${unit == 'mmol/L' ? '0,1 mmol/L' : '1 mg/dL'}',
                    'Increase by ${unit == 'mmol/L' ? '0.1 mmol/L' : '1 mg/dL'}',
                    'زيادة ${unit == 'mmol/L' ? '0.1 mmol/L' : '1 mg/dL'}',
                  ),
                  onPressed: finePlus == null
                      ? null
                      : () => onValueSelected(finePlus),
                  onLongPress: finePlus == null
                      ? null
                      : () => _startHold(1),
                  icon: const Icon(Icons.add_rounded),
                  style: IconButton.styleFrom(
                    minimumSize: const Size(48, 48),
                  ),
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(
              child: _boundaryLabel(
                context, colors,
                _copy(context, 'Repère bas', 'Lower guide', 'الحد المرجعي الأدنى'),
                _display(70),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Align(
                alignment: AlignmentDirectional.centerEnd,
                child: _boundaryLabel(
                  context, colors,
                  _copy(context, 'Repère haut', 'Upper guide', 'الحد المرجعي الأعلى'),
                  _display(180),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 13),
        Text(
          _copy(context,
            'Glisse : valeur visible en haut. Maintiens − / + pour accélérer.',
            'Drag: reading stays visible above. Hold − / + to accelerate.',
            'اسحب لترى القراءة بالأعلى. اضغط مطولاً − / + للتسريع.',
          ),
          key: const Key('glucose-half-dial-instruction'),
          textAlign: TextAlign.center,
          style: theme.textTheme.bodySmall?.copyWith(
            fontWeight: FontWeight.w600,
            color: colors.onSurface,
          ),
        ),
        const SizedBox(height: 6),
        Text(
          _copy(context,
            'Rouge hors repères · orange aux limites · vert au centre. Repères généraux, pas ta cible personnelle.',
            'Red outside guides · amber at boundaries · green between. General guides, not your personal target.',
            'الأحمر خارج الحدود والبرتقالي قربها والأخضر بينهما. مؤشرات عامة وليست هدفك الشخصي.',
          ),
          key: const Key('glucose-half-dial-guide-note'),
          textAlign: TextAlign.center,
          style: theme.textTheme.bodySmall?.copyWith(
            fontSize: 11,
            height: 1.4,
            color: colors.onSurfaceVariant,
          ),
        ),
      ],
    );
  }

  Widget _boundaryLabel(BuildContext context, ColorScheme colors,
      String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: Theme.of(context).textTheme.labelSmall?.copyWith(
          color: colors.onSurfaceVariant, fontSize: 10,
        )),
        Text(value + ' ' + widget.unit,
          style: Theme.of(context).textTheme.labelMedium?.copyWith(
            color: colors.onSurface,
            fontWeight: FontWeight.w800,
          ),
        ),
      ],
    );
  }

}

class _PremiumGlucoseArcPainter extends CustomPainter {
  const _PremiumGlucoseArcPainter({
    required this.fraction,
    required this.hasValue,
    required this.outline,
    required this.accent,
    required this.dark,
  });

  final double fraction;
  final bool hasValue;
  final Color outline;
  final Color accent;
  final bool dark;

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height - 18);
    final radius = math.min(size.width / 2 - 30, size.height - 35);
    final rect = Rect.fromCircle(center: center, radius: radius);
    const segments = 210;

    // A subtle shadow + continuous arc. Round only the TWO outside ends;
    // overlapping rounded caps on every segment would create color bumps.
    canvas.drawArc(rect, math.pi, math.pi, false, Paint()
      ..color = Colors.black.withValues(alpha: dark ? .15 : .07)
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round
      ..strokeWidth = 31
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 7));

    final band = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 26
      ..strokeCap = StrokeCap.butt;
    for (var i = 0; i < segments; i++) {
      final f = (i + .5) / segments;
      band.color = d22IllustrativeGlucoseArcColor(
        d22DialMgdlForFraction(f),
      );
      canvas.drawArc(
        rect,
        math.pi + i * math.pi / segments,
        math.pi / segments + .004,
        false,
        band,
      );
    }

    for (final endValue in [40.0, 320.0]) {
      final theta = math.pi + d22DialFractionForMgdl(endValue) * math.pi;
      final pos = Offset(
        center.dx + radius * math.cos(theta),
        center.dy + radius * math.sin(theta),
      );
      canvas.drawCircle(
        pos, 13, Paint()..color = d22IllustrativeGlucoseArcColor(endValue),
      );
    }

    // Fine radial separators, aligned to real reference boundaries.
    final separator = Paint()
      ..color = Colors.white.withValues(alpha: .75)
      ..strokeWidth = 2.4
      ..strokeCap = StrokeCap.round;
    for (final mg in [70.0, 90.0, 160.0, 180.0]) {
      final angle = math.pi + d22DialFractionForMgdl(mg) * math.pi;
      canvas.drawLine(
        Offset(
          center.dx + (radius - 11) * math.cos(angle),
          center.dy + (radius - 11) * math.sin(angle),
        ),
        Offset(
          center.dx + (radius + 11) * math.cos(angle),
          center.dy + (radius + 11) * math.sin(angle),
        ),
        separator,
      );
    }

    if (!hasValue) return;
    final theta = math.pi + fraction * math.pi;
    final cursor = Offset(
      center.dx + radius * math.cos(theta),
      center.dy + radius * math.sin(theta),
    );
    final haloColor = Color.lerp(
      accent, Colors.black, dark ? 0.23 : 0.30,
    )!;
    canvas.drawCircle(cursor, 23, Paint()
      ..color = haloColor.withValues(alpha: .17)
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 8));
    canvas.drawCircle(cursor, 17, Paint()..color = Colors.white);
    canvas.drawCircle(cursor, 13, Paint()..color = haloColor);
    canvas.drawCircle(cursor, 4.4, Paint()..color = Colors.white);
  }

  @override
  bool shouldRepaint(covariant _PremiumGlucoseArcPainter old) =>
      fraction != old.fraction || hasValue != old.hasValue ||
      outline != old.outline || accent != old.accent || dark != old.dark;
}
