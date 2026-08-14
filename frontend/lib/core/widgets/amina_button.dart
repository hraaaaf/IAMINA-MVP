import 'package:flutter/material.dart';

import '../theme/amina_visual_language.dart';
import '../theme/app_theme.dart';

class AminaButton extends StatefulWidget {
  final String label;
  final VoidCallback? onPressed;
  final bool isPrimary;
  final IconData? icon;
  final double? borderRadius;
  final bool isLoading;
  final bool pulse;

  const AminaButton({
    super.key,
    required this.label,
    this.onPressed,
    this.isPrimary = true,
    this.icon,
    this.borderRadius,
    this.isLoading = false,
    this.pulse = false,
  });

  @override
  State<AminaButton> createState() => _AminaButtonState();
}

class _AminaButtonState extends State<AminaButton>
    with SingleTickerProviderStateMixin {
  late final AnimationController _pulseController;
  late final Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    );
    _pulseAnimation = Tween<double>(begin: 0, end: 6).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOutSine),
    );
    _syncPulse();
  }

  @override
  void didUpdateWidget(covariant AminaButton oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.pulse != widget.pulse ||
        oldWidget.isPrimary != widget.isPrimary ||
        oldWidget.onPressed != widget.onPressed) {
      _syncPulse();
    }
  }

  void _syncPulse() {
    if (widget.isPrimary && widget.pulse && widget.onPressed != null) {
      _pulseController.repeat(reverse: true);
    } else {
      _pulseController.stop();
      _pulseController.value = 0;
    }
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final radius = widget.borderRadius ?? AminaVisualLanguage.controlRadius;
    if (widget.isPrimary) {
      return AnimatedBuilder(
        animation: _pulseAnimation,
        builder: (context, child) {
          return Container(
            height: 44,
            decoration: BoxDecoration(
              gradient: AminaVisualLanguage.primaryGradient,
              borderRadius: BorderRadius.circular(radius),
              boxShadow: widget.onPressed == null
                  ? null
                  : [
                      BoxShadow(
                        color: const Color(0xFF034A39).withValues(alpha: .28),
                        blurRadius: 18 + _pulseAnimation.value,
                        spreadRadius: -7 + (_pulseAnimation.value / 6),
                        offset: const Offset(0, 8),
                      ),
                    ],
            ),
            child: ElevatedButton(
              onPressed: widget.isLoading ? null : widget.onPressed,
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.transparent,
                disabledBackgroundColor: Colors.transparent,
                shadowColor: Colors.transparent,
                surfaceTintColor: Colors.transparent,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(radius),
                ),
                padding: const EdgeInsets.symmetric(horizontal: 20),
              ),
              child: _buildContent(Colors.white),
            ),
          );
        },
      );
    }

    final foreground = AminaTheme.isDark(context)
        ? AminaTheme.teal400
        : AminaVisualLanguage.actionGreen;
    return SizedBox(
      height: 42,
      child: OutlinedButton(
        onPressed: widget.isLoading ? null : widget.onPressed,
        style: OutlinedButton.styleFrom(
          foregroundColor: foreground,
          side: BorderSide(color: foreground, width: 1.15),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(radius),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 20),
          backgroundColor: AminaVisualLanguage.controlSurface(context),
          surfaceTintColor: Colors.transparent,
        ),
        child: _buildContent(foreground),
      ),
    );
  }

  Widget _buildContent(Color textColor) {
    if (widget.isLoading) {
      return SizedBox(
        width: 18,
        height: 18,
        child: CircularProgressIndicator(
          strokeWidth: 2,
          valueColor: AlwaysStoppedAnimation<Color>(textColor),
        ),
      );
    }

    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      mainAxisSize: MainAxisSize.min,
      children: [
        if (widget.icon != null) ...[
          Icon(widget.icon, size: 18, color: textColor),
          const SizedBox(width: 9),
        ],
        Text(
          widget.label,
          style: TextStyle(
            color: textColor,
            fontSize: 14.5,
            fontWeight: FontWeight.w700,
            letterSpacing: -0.1,
          ),
        ),
      ],
    );
  }
}
