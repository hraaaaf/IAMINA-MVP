import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_theme.dart';
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
                borderRadius: BorderRadius.circular(28),
                child: Container(
                  height: 52,
                  padding: const EdgeInsetsDirectional.fromSTEB(14, 0, 16, 0),
                  decoration: BoxDecoration(
                    gradient: AminaTheme.heroGradient,
                    borderRadius: BorderRadius.circular(28),
                  ),
                  child: const Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.auto_awesome_rounded, color: Colors.white, size: 20),
                      SizedBox(width: 8),
                      Text(
                        'IAmina',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 14,
                          fontWeight: FontWeight.w800,
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
