import 'package:flutter/material.dart';
import 'package:flutter/semantics.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/amina_visual_language.dart';
import '../../services/companion_service.dart';
import 'companion_fab_position_stub.dart'
    if (dart.library.html) 'companion_fab_position_web.dart'
    as fab_position;
import 'dashboard_premium_screen.dart';

class DashboardCompanionEntryScreen extends StatelessWidget {
  final CompanionService? companionService;
  final ScrollController? scrollController;

  const DashboardCompanionEntryScreen({
    super.key,
    this.companionService,
    this.scrollController,
  });

  @override
  Widget build(BuildContext context) => KeyedSubtree(
    key: const ValueKey('dashboard-companion-primary-entry'),
    child: Stack(
      children: [
        DashboardPremiumScreen(
          companionService: companionService,
          scrollController: scrollController,
        ),
        const Positioned.fill(child: DashboardCompanionAvatarAction()),
      ],
    ),
  );
}

/// D27: move the Home-only IAmina launcher without moving any clinical content.
/// The normalized position is a browser-local UI preference (never a patient fact).
/// Dragging does not activate the chat. The outer MainShell Scaffold already
/// reserves bottom-navigation height; keep only an in-body edge margin.
class DashboardCompanionAvatarAction extends StatefulWidget {
  const DashboardCompanionAvatarAction({super.key});

  @override
  State<DashboardCompanionAvatarAction> createState() =>
      _DashboardCompanionAvatarActionState();
}

class _DashboardCompanionAvatarActionState
    extends State<DashboardCompanionAvatarAction> {
  static const double _diameter = 56;
  static const double _edge = 12;
  // MainShell.bottomNavigationBar sits OUTSIDE this widget's layout bounds.
  // Reserving its height again stopped the avatar ~100px too high on iPhone.
  static const double _bottomEdge = 12;
  Offset? _normalized;
  bool _dragging = false;
  // Capture the initial pointer and button position once per gesture.
  // Global pointer displacement avoids dropped deltas during widget rebuilds.
  Offset? _dragPointerOrigin;
  Offset? _dragAvatarOrigin;

  @override
  void initState() {
    super.initState();
    final saved = fab_position.loadFabPosition();
    if (saved == null) return;
    final coordinates = saved.split(',');
    if (coordinates.length != 2) return;
    final x = double.tryParse(coordinates[0]);
    final y = double.tryParse(coordinates[1]);
    if (x != null && y != null && x.isFinite && y.isFinite &&
        x >= 0 && x <= 1 && y >= 0 && y <= 1) {
      _normalized = Offset(x, y);
    }
  }

  void _savePosition() {
    final value = _normalized;
    if (value != null) {
      fab_position.saveFabPosition('${value.dx},${value.dy}');
    }
  }

  // WCAG 2.2 2.5.7: a click/tap on a 2D picker can set any position,
  // without the precision or sustained movement required by dragging.
  void _showPositionPicker() {
    final width =
        (MediaQuery.sizeOf(context).width - 48).clamp(200.0, 300.0).toDouble();
    const height = 180.0;
    final start = _normalized ?? Offset(
      Directionality.of(context) == TextDirection.rtl ? 0 : 1,
      1,
    );
    showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (sheetContext) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(22, 10, 22, 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                switch (Localizations.localeOf(context).languageCode) {
                  'ar' => 'اختيار مكان IAmina',
                  'en' => 'Choose where IAmina sits',
                  _ => 'Choisir la position d’IAmina',
                },
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 8),
              Text(
                switch (Localizations.localeOf(context).languageCode) {
                  'ar' => 'اضغط على أي مكان في المنطقة لنقل الزر',
                  'en' => 'Tap anywhere in the area to move the button',
                  _ => 'Touchez un endroit dans la zone pour déplacer le bouton',
                },
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: width,
                height: height,
                child: GestureDetector(
                  key: const Key('dashboard-companion-position-grid'),
                  behavior: HitTestBehavior.opaque,
                  onTapDown: (details) {
                    setState(() {
                      _normalized = Offset(
                        (details.localPosition.dx / width).clamp(0.0, 1.0),
                        (details.localPosition.dy / height).clamp(0.0, 1.0),
                      );
                    });
                    _savePosition();
                    Navigator.of(sheetContext).pop();
                  },
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                      color: AminaVisualLanguage.controlSurface(context),
                      borderRadius: BorderRadius.circular(18),
                      border: Border.all(
                        color: AminaVisualLanguage.controlBorder(context),
                      ),
                    ),
                    child: Stack(
                      children: [
                        Positioned(
                          left: (width - 28) * start.dx,
                          top: (height - 28) * start.dy,
                          child: const CircleAvatar(
                            radius: 14,
                            backgroundColor: AminaVisualLanguage.forestDeep,
                            child: Icon(Icons.chat_bubble_outline_rounded,
                                size: 16, color: Colors.white),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final label = switch (Localizations.localeOf(context).languageCode) {
      'ar' => 'تحدث مع IAmina',
      'en' => 'Talk with IAmina',
      _ => 'Parler avec IAmina',
    };
    return LayoutBuilder(builder: (context, constraints) {
      final maxX = (constraints.maxWidth - _diameter - _edge)
          .clamp(_edge, double.infinity).toDouble();
      final maxY = (constraints.maxHeight - _diameter - _bottomEdge)
          .clamp(_edge, double.infinity).toDouble();
      final xSpan = maxX - _edge;
      final ySpan = maxY - _edge;
      final start = Offset(
        (Directionality.of(context) == TextDirection.rtl
                ? 20.0
                : constraints.maxWidth - _diameter - 20)
            .clamp(_edge, maxX)
            .toDouble(),
        (maxY - 72).clamp(_edge, maxY).toDouble(),
      );
      final location = _normalized == null
          ? start
          : Offset(
              _edge + (_normalized!.dx * xSpan),
              _edge + (_normalized!.dy * ySpan),
            );
      // Use the original pointer-to-button offset, not successive local deltas.
      // This keeps horizontal, vertical and circular finger motions 1:1.
      void followFinger(Offset globalPosition) {
        final pointerOrigin = _dragPointerOrigin;
        final avatarOrigin = _dragAvatarOrigin;
        if (pointerOrigin == null || avatarOrigin == null) return;
        final desired = avatarOrigin + (globalPosition - pointerOrigin);
        final nx = desired.dx.clamp(_edge, maxX).toDouble();
        final ny = desired.dy.clamp(_edge, maxY).toDouble();
        setState(() => _normalized = Offset(
          xSpan == 0 ? 0 : (nx - _edge) / xSpan,
          ySpan == 0 ? 0 : (ny - _edge) / ySpan,
        ));
      }

      void finishDrag() {
        _dragPointerOrigin = null;
        _dragAvatarOrigin = null;
        setState(() => _dragging = false);
        _savePosition();
      }

      void nudge(double dx, double dy) {
        final nx = (location.dx + dx).clamp(_edge, maxX).toDouble();
        final ny = (location.dy + dy).clamp(_edge, maxY).toDouble();
        setState(() => _normalized = Offset(
          xSpan == 0 ? 0 : (nx - _edge) / xSpan,
          ySpan == 0 ? 0 : (ny - _edge) / ySpan,
        ));
        _savePosition();
      }

      return Stack(children: [
        Positioned(
          left: location.dx,
          top: location.dy,
          child: CallbackShortcuts(
            bindings: {
              const SingleActivator(LogicalKeyboardKey.arrowLeft):
                  () => nudge(-24, 0),
              const SingleActivator(LogicalKeyboardKey.arrowRight):
                  () => nudge(24, 0),
              const SingleActivator(LogicalKeyboardKey.arrowUp):
                  () => nudge(0, -24),
              const SingleActivator(LogicalKeyboardKey.arrowDown):
                  () => nudge(0, 24),
              const SingleActivator(LogicalKeyboardKey.enter, shift: true):
                  _showPositionPicker,
            },
            child: GestureDetector(
            onLongPress: _showPositionPicker,
            onPanDown: (details) {
              _dragPointerOrigin = details.globalPosition;
              _dragAvatarOrigin = location;
            },
            onPanStart: (details) {
              _dragPointerOrigin ??= details.globalPosition;
              _dragAvatarOrigin ??= location;
              setState(() => _dragging = true);
              followFinger(details.globalPosition);
            },
            onPanUpdate: (details) => followFinger(details.globalPosition),
            onPanEnd: (_) => finishDrag(),
            onPanCancel: finishDrag,
            child: AnimatedScale(
              duration: const Duration(milliseconds: 160),
              curve: Curves.easeOutCubic,
              scale: MediaQuery.disableAnimationsOf(context)
                  ? 1
                  : (_dragging ? 1.04 : 1),
              child: Semantics(
                button: true,
                label: label,
                hint: switch (Localizations.localeOf(context).languageCode) {
                  'ar' => 'اسحب أو اضغط مطولاً لتغيير المكان',
                  'en' => 'Drag or hold to reposition',
                  _ => 'Glisser ou maintenir pour déplacer',
                },
                customSemanticsActions: {
                  CustomSemanticsAction(
                    label: switch (Localizations.localeOf(context).languageCode) {
                      'ar' => 'نقل IAmina',
                      'en' => 'Reposition IAmina',
                      _ => 'Déplacer IAmina',
                    },
                  ): _showPositionPicker,
                },
                child: FloatingActionButton(
                  key: const ValueKey('dashboard-companion-chat-action'),
                  heroTag: 'dashboard-companion-chat-action',
                  // The built-in FAB Tooltip consumes long presses before the
                  // outer reposition gesture. Semantics supplies the label.
                  onPressed: () => context.push('/companion/chat'),
                  elevation: _dragging ? 9 : 5,
                  backgroundColor: AminaVisualLanguage.forestDeep,
                  foregroundColor: Colors.white,
                  child: ClipOval(
                    child: SizedBox.square(
                      dimension: 44,
                      child: ColoredBox(
                        color: Colors.white,
                        child: Image.asset(
                          'assets/images/logo_amina.png',
                          fit: BoxFit.cover,
                          alignment: Alignment.topCenter,
                          excludeFromSemantics: true,
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ),
            ),
          ),
        ),
      ]);
    });
  }
}
