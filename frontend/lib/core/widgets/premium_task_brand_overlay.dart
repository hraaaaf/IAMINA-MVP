import 'package:flutter/material.dart';

import '../theme/amina_visual_language.dart';

/// Non-interactive brand accent for focused full-screen patient tasks.
/// Keeps the underlying workflow and navigation semantics untouched.
class PremiumTaskBrandOverlay extends StatelessWidget {
  const PremiumTaskBrandOverlay({super.key});

  @override
  Widget build(BuildContext context) {
    final top = MediaQuery.paddingOf(context).top;
    return IgnorePointer(
      child: Stack(
        children: [
          PositionedDirectional(
            top: top - 18,
            end: -34,
            child: Container(
              width: 150,
              height: 120,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AminaVisualLanguage.mintWaveLight.withValues(alpha: .42),
              ),
            ),
          ),
          PositionedDirectional(
            top: top + 8,
            end: 18,
            child: Container(
              width: 48,
              height: 54,
              padding: const EdgeInsets.all(4),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: .94),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.white),
                boxShadow: AminaVisualLanguage.cardShadowLight,
              ),
              child: Image.asset(
                'assets/images/logo_amina.png',
                fit: BoxFit.contain,
                filterQuality: FilterQuality.high,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
