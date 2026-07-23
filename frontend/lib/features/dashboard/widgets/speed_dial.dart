part of '../dashboard_screen.dart';

// ── Add FAB — direct single-tap navigation ────────────────────────────────────

class _AddFab extends StatefulWidget {
  final VoidCallback onTap;
  const _AddFab({required this.onTap});
  @override
  State<_AddFab> createState() => _AddFabState();
}

class _AddFabState extends State<_AddFab> with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<double> _pulse;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 2600))..repeat();
    _pulse = Tween<double>(begin: 0.0, end: 1.0).animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeOut));
  }

  @override
  void dispose() { _ctrl.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: widget.onTap,
      child: SizedBox(
        width: 76, height: 76,
        child: AnimatedBuilder(
          animation: _pulse,
          builder: (_, __) {
            final ripple = _pulse.value;
            return Stack(alignment: Alignment.center, children: [
              IgnorePointer(
                child: Container(
                  width: 56 + ripple * 20,
                  height: 56 + ripple * 20,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: AminaTheme.teal500.withValues(alpha: (1.0 - ripple) * 0.3),
                  ),
                ),
              ),
              Container(
                width: 56, height: 56,
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [AminaTheme.teal500, AminaTheme.teal700],
                    begin: Alignment.topLeft, end: Alignment.bottomRight,
                  ),
                  shape: BoxShape.circle,
                  boxShadow: AminaTheme.shadowFab,
                ),
                child: const Icon(Icons.add, color: Colors.white, size: 26),
              ),
            ]);
          },
        ),
      ),
    );
  }
}
