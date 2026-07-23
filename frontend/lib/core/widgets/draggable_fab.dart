import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class DraggableFab extends StatefulWidget {
  final VoidCallback onTap;
  final IconData icon;
  final String heroTag;
  final Offset? initialOffset;

  const DraggableFab({
    super.key,
    required this.onTap,
    required this.icon,
    this.heroTag = 'draggable_fab',
    this.initialOffset,
  });

  @override
  State<DraggableFab> createState() => _DraggableFabState();
}

class _DraggableFabState extends State<DraggableFab> with SingleTickerProviderStateMixin {
  late Offset _offset;
  bool _isDragging = false;
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _offset = widget.initialOffset ?? const Offset(-24, -100);
    
    // Breathing/Pulse animation (Phase 2 UI)
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);
    
    _pulseAnimation = Tween<double>(begin: 1.0, end: 1.08).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOutSine),
    );
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        Positioned(
          right: _offset.dx < 0 ? -_offset.dx : null,
          left: _offset.dx > 0 ? _offset.dx : null,
          bottom: _offset.dy < 0 ? -_offset.dy : null,
          top: _offset.dy > 0 ? _offset.dy : null,
          child: GestureDetector(
            onPanStart: (_) {
              setState(() => _isDragging = true);
              _pulseController.stop(); // Stop pulsing while dragging
            },
            onPanUpdate: (details) {
              setState(() {
                _offset += details.delta;
              });
            },
            onPanEnd: (_) {
              setState(() => _isDragging = false);
              _pulseController.repeat(reverse: true); // Resume pulse
            },
            child: AnimatedBuilder(
              animation: _pulseAnimation,
              builder: (context, child) {
                // Combine drag scale (1.15) with pulse scale
                final scale = _isDragging ? 1.15 : _pulseAnimation.value;
                
                return AnimatedScale(
                  scale: scale,
                  duration: _isDragging ? const Duration(milliseconds: 200) : Duration.zero,
                  curve: Curves.easeOutBack,
                  child: AnimatedRotation(
                    turns: _isDragging ? 0.125 : 0.0,
                    duration: const Duration(milliseconds: 400),
                    curve: Curves.elasticOut,
                    child: FloatingActionButton(
                      heroTag: widget.heroTag,
                      onPressed: _isDragging ? null : widget.onTap,
                      backgroundColor: Colors.transparent,
                      elevation: 0,
                      child: Container(
                        width: 64,
                        height: 64,
                        decoration: BoxDecoration(
                          gradient: AminaTheme.heroGradient,
                          shape: BoxShape.circle,
                          boxShadow: [
                            BoxShadow(
                              color: AminaTheme.primaryTeal.withValues(
                                alpha: _isDragging ? 0.6 : (0.4 * _pulseAnimation.value)
                              ),
                              blurRadius: _isDragging ? 24 : (18 * _pulseAnimation.value),
                              spreadRadius: _isDragging ? 4 : (2 * (_pulseAnimation.value - 1.0) * 10),
                              offset: const Offset(0, 4),
                            ),
                          ],
                        ),
                        child: Icon(widget.icon, color: Colors.white, size: 32),
                      ),
                    ),
                  ),
                );
              }
            ),
          ),
        ),
      ],
    );
  }
}
