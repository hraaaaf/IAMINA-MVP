import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/amina_visual_language.dart';
import 'dashboard_convergent_screen.dart';

class DashboardCompanionEntryScreen extends StatelessWidget {
  const DashboardCompanionEntryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        const DashboardConvergentScreen(),
        PositionedDirectional(
          end: 18,
          bottom: 104,
          child: SafeArea(
            top: false,
            child: Material(
              color: Colors.transparent,
              child: InkWell(
                key: const ValueKey('dashboard-companion-primary-entry'),
                onTap: () => GoRouter.of(context).go('/companion'),
                borderRadius: BorderRadius.circular(26),
                child: Container(
                  height: 52,
                  padding: const EdgeInsetsDirectional.fromSTEB(15, 0, 17, 0),
                  decoration: BoxDecoration(
                    gradient: AminaVisualLanguage.primaryGradient,
                    borderRadius: BorderRadius.circular(26),
                    boxShadow: AminaVisualLanguage.controlShadowLight,
                  ),
                  child: const Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        Icons.auto_awesome_rounded,
                        color: Colors.white,
                        size: 19,
                      ),
                      SizedBox(width: 9),
                      Text(
                        'IAmina',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 14,
                          fontWeight: FontWeight.w800,
                          letterSpacing: -.1,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}
