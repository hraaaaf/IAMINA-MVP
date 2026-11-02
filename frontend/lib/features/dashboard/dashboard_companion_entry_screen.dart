import 'package:flutter/material.dart';
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
/// Dragging does not activate the chat, and the 104px bottom dock stays uncovered.
class DashboardCompanionAvatarAction extends StatefulWidget {
  const DashboardCompanionAvatarAction({super.key});

  @override
  State<DashboardCompanionAvatarAction> createState() =>
      _DashboardCompanionAvatarActionState();
}

class _DashboardCompanionAvatarActionState
    extends State<DashboardCompanionAvatarAction> {
  static const double _diameter = 40;
  static const double _edge = 12;
  static const double _dockClearance = 104;
  Offset? _normalized;
  bool _dragging = false;

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
      final maxY = (constraints.maxHeight - _diameter - _dockClearance)
          .clamp(_edge, double.infinity).toDouble();
      final xSpan = maxX - _edge;
      final ySpan = maxY - _edge;
      final start = Offset(
        (Directionality.of(context) == TextDirection.rtl
                ? 20.0
                : constraints.maxWidth - _diameter - 20)
            .clamp(_edge, maxX)
            .toDouble(),
        maxY,
      );
      final location = _normalized == null
          ? start
          : Offset(
              _edge + (_normalized!.dx * xSpan),
              _edge + (_normalized!.dy * ySpan),
            );
      return Stack(children: [
        Positioned(
          left: location.dx,
          top: location.dy,
          child: GestureDetector(
            onPanStart: (_) => setState(() => _dragging = true),
            onPanUpdate: (details) {
              final nx = (location.dx + details.delta.dx)
                  .clamp(_edge, maxX).toDouble();
              final ny = (location.dy + details.delta.dy)
                  .clamp(_edge, maxY).toDouble();
              setState(() => _normalized = Offset(
                xSpan == 0 ? 0 : (nx - _edge) / xSpan,
                ySpan == 0 ? 0 : (ny - _edge) / ySpan,
              ));
            },
            onPanEnd: (_) {
              setState(() => _dragging = false);
              _savePosition();
            },
            onPanCancel: () {
              setState(() => _dragging = false);
              _savePosition();
            },
            child: AnimatedScale(
              duration: const Duration(milliseconds: 160),
              curve: Curves.easeOutCubic,
              scale: _dragging ? 1.10 : 1,
              child: Semantics(
                button: true,
                label: label,
                hint: switch (Localizations.localeOf(context).languageCode) {
                  'ar' => 'اسحب الزر لتغيير مكانه',
                  'en' => 'Drag to reposition',
                  _ => 'Faire glisser pour déplacer',
                },
                child: FloatingActionButton.small(
                  key: const ValueKey('dashboard-companion-chat-action'),
                  heroTag: 'dashboard-companion-chat-action',
                  tooltip: label,
                  onPressed: () => context.push('/companion/chat'),
                  elevation: _dragging ? 9 : 5,
                  backgroundColor: AminaVisualLanguage.forestDeep,
                  foregroundColor: Colors.white,
                  child: ClipOval(
                    child: SizedBox.square(
                      dimension: 34,
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
      ]);
    });
  }
}
