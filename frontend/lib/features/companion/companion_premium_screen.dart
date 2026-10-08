import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/amina_visual_language.dart';
import '../../core/theme/app_theme.dart';
import '../../data/models/companion_models.dart';
import '../../services/companion_service.dart';
import 'companion_uncertainty_copy.dart';

part 'companion_premium_screen_presentation.dart';

String _t(BuildContext context, String fr, String en, String ar) {
  final code = Localizations.localeOf(context).languageCode;
  if (code == 'ar') return ar;
  if (code == 'en') return en;
  return fr;
}

class CompanionPremiumScreen extends StatefulWidget {
  final CompanionService? service;

  const CompanionPremiumScreen({super.key, this.service});

  @override
  State<CompanionPremiumScreen> createState() => _CompanionPremiumScreenState();
}

class _CompanionPremiumScreenState extends State<CompanionPremiumScreen> {
  late final CompanionService _service = widget.service ?? CompanionService();
  late Future<CompanionOverview?> _future = _service.fetchOverview();

  @override
  void dispose() {
    if (widget.service == null) _service.dispose();
    super.dispose();
  }

  void _reload() {
    setState(() {
      _future = _service.fetchOverview();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AminaTheme.isDark(context)
          ? AminaTheme.bg(context)
          : const Color(0xFFF4FBF9),
      body: Stack(
        children: [
          const Positioned.fill(child: _AmbientBackground()),
          SafeArea(
            bottom: false,
            child: FutureBuilder<CompanionOverview?>(
              future: _future,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return _Shell(
                    child: _StateCard(
                      loading: true,
                      title: _t(context, 'Préparation', 'Preparing', 'جارٍ التحضير'),
                      body: _t(
                        context,
                        'IAmina prépare votre compagnon à partir de vos données gouvernées.',
                        'IAmina is preparing your companion from governed data.',
                        'تقوم IAmina بإعداد رفيقك من بياناتك المحكومة.',
                      ),
                    ),
                  );
                }

                final overview = snapshot.data;
                if (overview == null) {
                  return _Shell(
                    child: _StateCard(
                      icon: Icons.cloud_off_outlined,
                      title: _t(context, 'Données indisponibles', 'Data unavailable', 'البيانات غير متاحة'),
                      body: _t(
                        context,
                        'La synthèse n’est pas disponible pour le moment. Aucune interprétation n’est inventée. Vous pouvez ouvrir la conversation IAmina, dont les réponses peuvent rester limitées.',
                        'The summary is unavailable right now. No interpretation is invented. You can open IAmina chat, where replies may remain limited.',
                        'الملخص غير متاح حالياً. لا يتم اختراع أي تفسير. يمكنك فتح محادثة IAmina، وقد تبقى الردود محدودة.',
                      ),
                      onChat: () => context.push('/companion/chat'),
                      actionLabel: _t(context, 'Réessayer', 'Retry', 'إعادة المحاولة'),
                      onAction: _reload,
                    ),
                  );
                }

                return Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 1080),
                    child: _Overview(overview: overview),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
