part of '../dashboard_screen.dart';

// ── Add FAB — direct single-tap navigation ────────────────────────────────────

class _AddFab extends StatefulWidget {
  final VoidCallback onTap;

  const _AddFab({required this.onTap});

  @override
  State<_AddFab> createState() => _AddFabState();
}

class _AddFabState extends State<_AddFab>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _pulse;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2600),
    )..repeat();
    _pulse = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final label = AuditedPageCopy.of(context).l10n.addEntry;
    return Tooltip(
      message: label,
      child: Semantics(
        button: true,
        label: label,
        child: InkResponse(
          onTap: widget.onTap,
          radius: 30,
          child: SizedBox(
            width: 60,
            height: 60,
            child: AnimatedBuilder(
              animation: _pulse,
              builder: (_, __) {
                final ripple = _pulse.value;
                return Stack(
                  alignment: Alignment.center,
                  children: [
                    IgnorePointer(
                      child: Container(
                        width: 48 + ripple * 12,
                        height: 48 + ripple * 12,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: AminaTheme.teal500.withValues(
                            alpha: (1 - ripple) * 0.22,
                          ),
                        ),
                      ),
                    ),
                    Container(
                      width: 48,
                      height: 48,
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [AminaTheme.teal500, AminaTheme.teal700],
                          begin: AlignmentDirectional.topStart,
                          end: AlignmentDirectional.bottomEnd,
                        ),
                        shape: BoxShape.circle,
                        boxShadow: AminaTheme.shadowFab,
                      ),
                      child: const Icon(
                        Icons.add,
                        color: Colors.white,
                        size: 24,
                      ),
                    ),
                  ],
                );
              },
            ),
          ),
        ),
      ),
    );
  }
}
