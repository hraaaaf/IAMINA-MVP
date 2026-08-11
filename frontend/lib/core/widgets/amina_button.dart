import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class AminaButton extends StatefulWidget {
  final String label;
  final VoidCallback? onPressed;
  final bool isPrimary;
  final IconData? icon;
  final double? borderRadius;
  final bool isLoading;
  final bool pulse; // New property to enable the IA pulse effect

  const AminaButton({
    super.key,
    required this.label,
    this.onPressed,
    this.isPrimary = true,
    this.icon,
    this.borderRadius,
    this.isLoading = false,
    this.pulse = true,
  });

  @override
  State<AminaButton> createState() => _AminaButtonState();
}

class _AminaButtonState extends State<AminaButton> with SingleTickerProviderStateMixin {
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    );
    
    _pulseAnimation = Tween<double>(begin: 0.0, end: 12.0).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOutSine),
    );

    if (widget.isPrimary && widget.pulse) {
      _pulseController.repeat(reverse: true);
    }
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (widget.isPrimary) {
      return AnimatedBuilder(
        animation: _pulseAnimation,
        builder: (context, child) {
          return Container(
            height: 52,
            decoration: BoxDecoration(
              gradient: AminaTheme.heroGradient,
              borderRadius: BorderRadius.circular(widget.borderRadius ?? AminaTheme.radius2XL),
              boxShadow: widget.onPressed == null 
                ? null 
                : [
                    BoxShadow(
                      color: AminaTheme.primaryTeal.withValues(alpha: 0.4),
                      blurRadius: 12 + _pulseAnimation.value,
                      spreadRadius: _pulseAnimation.value / 4,
                    ),
                  ],
            ),
            child: ElevatedButton(
              onPressed: widget.isLoading ? null : widget.onPressed,
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.transparent,
                shadowColor: Colors.transparent,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(widget.borderRadius ?? AminaTheme.radius2XL)
                ),
                padding: const EdgeInsets.symmetric(horizontal: 24),
              ),
              child: _buildContent(Colors.white),
            ),
          );
        },
      );
    } else {
      return SizedBox(
        height: 52,
        child: OutlinedButton(
          onPressed: widget.isLoading ? null : widget.onPressed,
          style: OutlinedButton.styleFrom(
            side: const BorderSide(color: AminaTheme.borderLight, width: 2),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(widget.borderRadius ?? AminaTheme.radius2XL)
            ),
            padding: const EdgeInsets.symmetric(horizontal: 24),
            backgroundColor: AminaTheme.surfaceWhite,
          ),
          child: _buildContent(AminaTheme.textMuted),
        ),
      );
    }
  }

  Widget _buildContent(Color textColor) {
    if (widget.isLoading) {
      return SizedBox(
        width: 20,
        height: 20,
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
          Icon(widget.icon, size: 20, color: textColor),
          const SizedBox(width: 8),
        ],
        Text(
          widget.label,
          style: TextStyle(
            color: textColor,
            fontSize: 16,
            fontWeight: FontWeight.w700,
            letterSpacing: -0.2,
          ),
        ),
      ],
    );
  }
}
