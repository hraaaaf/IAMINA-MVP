import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';
import '../../data/models/companion_models.dart';
import '../../services/companion_service.dart';

String _t(BuildContext context, String fr, String en, String ar) {
  final code = Localizations.localeOf(context).languageCode;
  if (code == 'ar') return ar;
  if (code == 'en') return en;
  return fr;
}

class CompanionScreen extends StatefulWidget {
  final CompanionService? service;

  const CompanionScreen({super.key, this.service});

  @override
  State<CompanionScreen> createState() => _CompanionScreenState();
}

class _CompanionScreenState extends State<CompanionScreen> {
  late final CompanionService _service = widget.service ?? CompanionService();
  late Future<CompanionOverview?> _overview = _service.fetchOverview();

  @override
  void dispose() {
    if (widget.service == null) _service.dispose();
    super.dispose();
  }

  void _reload() {
    setState(() => _overview = _service.fetchOverview());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AminaTheme.bg(context),
      appBar: AppBar(
        backgroundColor: AminaTheme.bg(context),
        surfaceTintColor: Colors.transparent,
        title: Text(
          _t(context, 'Mon compagnon', 'My companion', 'رفيقي الصحي'),
          style: TextStyle(
            fontWeight: FontWeight.w800,
            color: AminaTheme.textPrimary(context),
          ),
        ),
      ),
      body: FutureBuilder<CompanionOverview?>(
        future: _overview,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          final overview = snapshot.data;
          if (overview == null) {
            return _StateMessage(
              icon: Icons.cloud_off_outlined,
              title: _t(
                context,
                'Données indisponibles',
                'Data unavailable',
                'البيانات غير متاحة',
              ),
              body: _t(
                context,
                'IAmina ne peut pas charger votre suivi pour le moment.',
                'IAmina cannot load your companion view right now.',
                'يتعذر على IAmina تحميل المتابعة حالياً.',
              ),
              onRetry: _reload,
            );
          }
          return _OverviewBody(overview: overview);
        },
      ),
    );
  }
}

class _OverviewBody extends StatelessWidget {
  final CompanionOverview overview;

  const _OverviewBody({required this.overview});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsetsDirectional.fromSTEB(18, 8, 18, 32),
      children: [
        _SafetyBanner(notice: overview.safetyNotice),
        const SizedBox(height: 16),
        _SectionHeader(
          eyebrow: _t(context, 'COMPRENDRE', 'UNDERSTAND', 'افهم'),
          title: _t(
            context,
            'Ce que vos données montrent',
            'What your data shows',
            'ما الذي تظهره بياناتك',
          ),
        ),
        const SizedBox(height: 10),
        if (overview.patterns.isEmpty)
          _EmptyCard(
            text: _t(
              context,
              'Pas encore assez de données répétées pour afficher un schéma personnel gouverné.',
              'Not enough repeated data yet to show a governed personal pattern.',
              'لا توجد بيانات متكررة كافية بعد لإظهار نمط شخصي موثوق.',
            ),
          )
        else
          ...overview.patterns.map((item) => _PatternCard(pattern: item)),
        const SizedBox(height: 22),
        _SectionHeader(
          eyebrow: _t(context, 'SUIVRE', 'FOLLOW', 'تابع'),
          title: _t(
            context,
            'Depuis votre dernière revue',
            'Since your last review',
            'منذ آخر مراجعة لك',
          ),
        ),
        const SizedBox(height: 10),
        if (overview.reviewStatus != 'ready')
          _EmptyCard(
            text: _t(
              context,
              'Aucune revue précédente fiable à comparer. IAmina ne fabrique pas d’historique.',
              'No reliable previous review to compare. IAmina does not invent history.',
              'لا توجد مراجعة سابقة موثوقة للمقارنة. IAmina لا تنشئ تاريخاً غير موجود.',
            ),
          )
        else if (overview.changesSinceReview.isEmpty)
          _EmptyCard(
            text: _t(
              context,
              'Aucun changement gouverné à afficher depuis la dernière revue.',
              'No governed change to show since the last review.',
              'لا يوجد تغير موثوق لعرضه منذ آخر مراجعة.',
            ),
          )
        else
          ...overview.changesSinceReview.map((item) => _ChangeCard(change: item)),
        const SizedBox(height: 22),
        _SectionHeader(
          eyebrow: _t(context, 'PRÉPARER', 'PREPARE', 'استعد'),
          title: _t(
            context,
            'Continuité après consultation',
            'After-visit continuity',
            'المتابعة بعد الاستشارة',
          ),
        ),
        const SizedBox(height: 10),
        _AfterVisitCard(afterVisit: overview.afterVisit),
      ],
    );
  }
}

class _SafetyBanner extends StatelessWidget {
  final String notice;

  const _SafetyBanner({required this.notice});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AminaTheme.surface(context),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AminaTheme.divider(context)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.shield_outlined, size: 20, color: Color(0xFF0B6B70)),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              notice.isEmpty
                  ? _t(
                      context,
                      'IAmina vous aide à comprendre et suivre vos données. Les décisions médicales restent avec votre professionnel de santé.',
                      'IAmina helps you understand and follow your data. Medical decisions remain with your clinician.',
                      'تساعدك IAmina على فهم بياناتك ومتابعتها. تبقى القرارات الطبية مع طبيبك.',
                    )
                  : notice,
              style: TextStyle(
                height: 1.35,
                fontSize: 12.5,
                color: AminaTheme.textSecondary(context),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final String eyebrow;
  final String title;

  const _SectionHeader({required this.eyebrow, required this.title});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          eyebrow,
          style: const TextStyle(
            fontSize: 10.5,
            fontWeight: FontWeight.w800,
            letterSpacing: 1.2,
            color: Color(0xFF0B6B70),
          ),
        ),
        const SizedBox(height: 4),
        Text(
          title,
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.w800,
            color: AminaTheme.textPrimary(context),
          ),
        ),
      ],
    );
  }
}

class _PatternCard extends StatelessWidget {
  final CompanionPattern pattern;

  const _PatternCard({required this.pattern});

  @override
  Widget build(BuildContext context) {
    return _Card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  _friendlyKey(context, pattern.observationKey),
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w800,
                    color: AminaTheme.textPrimary(context),
                  ),
                ),
              ),
              _EvidencePill(density: pattern.evidenceDensity),
            ],
          ),
          const SizedBox(height: 9),
          Text(
            _movement(context, pattern.baselineMovement),
            style: TextStyle(
              fontSize: 13,
              height: 1.35,
              color: AminaTheme.textSecondary(context),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            _t(
              context,
              '${pattern.recurrenceCount} occurrence(s) observée(s) dans votre historique gouverné.',
              '${pattern.recurrenceCount} occurrence(s) observed in your governed history.',
              'تمت ملاحظة ${pattern.recurrenceCount} حالة في سجلك الموثوق.',
            ),
            style: TextStyle(fontSize: 11.5, color: AminaTheme.textSecondary(context)),
          ),
        ],
      ),
    );
  }
}

class _ChangeCard extends StatelessWidget {
  final CompanionChange change;

  const _ChangeCard({required this.change});

  @override
  Widget build(BuildContext context) {
    return _Card(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(_changeIcon(change.changeKind), color: const Color(0xFF0B6B70), size: 20),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _friendlyKey(context, change.observationKey),
                  style: TextStyle(
                    fontWeight: FontWeight.w800,
                    color: AminaTheme.textPrimary(context),
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  _changeLabel(context, change.changeKind),
                  style: TextStyle(fontSize: 12.5, color: AminaTheme.textSecondary(context)),
                ),
                if (change.missingData.isNotEmpty) ...[
                  const SizedBox(height: 6),
                  Text(
                    _t(
                      context,
                      'Données manquantes : ${change.missingData.join(', ')}',
                      'Missing data: ${change.missingData.join(', ')}',
                      'بيانات ناقصة: ${change.missingData.join(', ')}',
                    ),
                    style: TextStyle(fontSize: 11.5, color: AminaTheme.textSecondary(context)),
                  ),
                ],
              ],
            ),
          ),
          _EvidencePill(density: change.evidenceStrength),
        ],
      ),
    );
  }
}

class _AfterVisitCard extends StatelessWidget {
  final CompanionAfterVisit afterVisit;

  const _AfterVisitCard({required this.afterVisit});

  @override
  Widget build(BuildContext context) {
    if (afterVisit.status != 'recorded') {
      return _EmptyCard(
        text: _t(
          context,
          'Aucune consultation n’a été explicitement enregistrée. IAmina ne la déduit pas de votre activité.',
          'No consultation has been explicitly recorded. IAmina does not infer one from your activity.',
          'لم يتم تسجيل أي استشارة بشكل صريح. لا تستنتج IAmina ذلك من نشاطك.',
        ),
      );
    }
    return _Card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            _t(context, 'Consultation enregistrée', 'Recorded consultation', 'استشارة مسجلة'),
            style: TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w800,
              color: AminaTheme.textPrimary(context),
            ),
          ),
          const SizedBox(height: 7),
          Text(
            _t(
              context,
              '${afterVisit.factCount} élément(s) de suivi structuré(s) enregistré(s).',
              '${afterVisit.factCount} structured follow-up item(s) recorded.',
              'تم تسجيل ${afterVisit.factCount} عنصر متابعة منظم.',
            ),
            style: TextStyle(fontSize: 12.5, color: AminaTheme.textSecondary(context)),
          ),
          const SizedBox(height: 8),
          Text(
            _t(
              context,
              'Le fait qu’une mesure change après la consultation ne signifie pas que le traitement en est la cause.',
              'A change after the visit does not mean the treatment caused it.',
              'حدوث تغير بعد الاستشارة لا يعني أن العلاج هو السبب.',
            ),
            style: TextStyle(fontSize: 11.5, height: 1.35, color: AminaTheme.textSecondary(context)),
          ),
        ],
      ),
    );
  }
}

class _EvidencePill extends StatelessWidget {
  final String density;

  const _EvidencePill({required this.density});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: const Color(0xFF0B6B70).withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        _evidenceLabel(context, density),
        style: const TextStyle(fontSize: 10.5, fontWeight: FontWeight.w700, color: Color(0xFF0B6B70)),
      ),
    );
  }
}

class _Card extends StatelessWidget {
  final Widget child;

  const _Card({required this.child});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 9),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AminaTheme.surface(context),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AminaTheme.divider(context)),
      ),
      child: child,
    );
  }
}

class _EmptyCard extends StatelessWidget {
  final String text;

  const _EmptyCard({required this.text});

  @override
  Widget build(BuildContext context) {
    return _Card(
      child: Text(
        text,
        style: TextStyle(fontSize: 13, height: 1.4, color: AminaTheme.textSecondary(context)),
      ),
    );
  }
}

class _StateMessage extends StatelessWidget {
  final IconData icon;
  final String title;
  final String body;
  final VoidCallback onRetry;

  const _StateMessage({
    required this.icon,
    required this.title,
    required this.body,
    required this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(28),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 34, color: AminaTheme.textSecondary(context)),
            const SizedBox(height: 12),
            Text(title, style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: AminaTheme.textPrimary(context))),
            const SizedBox(height: 7),
            Text(body, textAlign: TextAlign.center, style: TextStyle(height: 1.4, color: AminaTheme.textSecondary(context))),
            const SizedBox(height: 14),
            OutlinedButton(onPressed: onRetry, child: Text(_t(context, 'Réessayer', 'Retry', 'إعادة المحاولة'))),
          ],
        ),
      ),
    );
  }
}

String _friendlyKey(BuildContext context, String key) {
  final labels = <String, List<String>>{
    'context:stress': ['Stress', 'Stress', 'التوتر'],
    'context:activity': ['Activité', 'Activity', 'النشاط'],
    'context:illness': ['Maladie déclarée', 'Recorded illness', 'مرض مسجل'],
    'context:poor_sleep': ['Sommeil difficile', 'Poor sleep', 'نوم غير جيد'],
    'context:fatigue': ['Fatigue', 'Fatigue', 'التعب'],
    'meal:breakfast': ['Petit-déjeuner', 'Breakfast', 'الفطور'],
    'meal:lunch': ['Déjeuner', 'Lunch', 'الغداء'],
    'meal:dinner': ['Dîner', 'Dinner', 'العشاء'],
    'meal:snack': ['Collation', 'Snack', 'وجبة خفيفة'],
    'meal:suhoor': ['Suhoor', 'Suhoor', 'السحور'],
    'meal:iftar': ['Iftar', 'Iftar', 'الإفطار'],
  };
  final item = labels[key];
  if (item == null) return key;
  final code = Localizations.localeOf(context).languageCode;
  return code == 'ar' ? item[2] : code == 'en' ? item[1] : item[0];
}

String _evidenceLabel(BuildContext context, String density) => switch (density) {
  'strong' => _t(context, 'Preuve répétée forte', 'Strong repeatability', 'تكرار قوي'),
  'moderate' => _t(context, 'Preuve répétée modérée', 'Moderate repeatability', 'تكرار متوسط'),
  _ => _t(context, 'Preuve répétée limitée', 'Limited repeatability', 'تكرار محدود'),
};

String _movement(BuildContext context, String movement) => switch (movement) {
  'toward_personal_window_baseline' => _t(
      context,
      'Le signal descriptif s’est rapproché de votre référence personnelle sur la fenêtre observée.',
      'The descriptive signal moved toward your personal window baseline.',
      'اقتربت الإشارة الوصفية من مرجعك الشخصي خلال الفترة المرصودة.',
    ),
  'away_from_personal_window_baseline' => _t(
      context,
      'Le signal descriptif s’est éloigné de votre référence personnelle sur la fenêtre observée.',
      'The descriptive signal moved away from your personal window baseline.',
      'ابتعدت الإشارة الوصفية عن مرجعك الشخصي خلال الفترة المرصودة.',
    ),
  'stable_relative_to_personal_window_baseline' => _t(
      context,
      'Le signal descriptif est resté globalement stable par rapport à votre référence personnelle.',
      'The descriptive signal stayed broadly stable relative to your personal baseline.',
      'بقيت الإشارة الوصفية مستقرة عموماً مقارنة بمرجعك الشخصي.',
    ),
  _ => _t(
      context,
      'Première comparaison disponible ou historique encore insuffisant.',
      'First available comparison or history is still insufficient.',
      'هذه أول مقارنة متاحة أو أن السجل ما زال غير كافٍ.',
    ),
};

String _changeLabel(BuildContext context, String kind) => switch (kind) {
  'new' => _t(context, 'Nouveau depuis votre dernière revue.', 'New since your last review.', 'جديد منذ آخر مراجعة.'),
  'persisting' => _t(context, 'Toujours observé depuis votre dernière revue.', 'Still observed since your last review.', 'ما زال ملاحظاً منذ آخر مراجعة.'),
  'improving' => _t(context, 'Mouvement descriptif vers votre référence personnelle.', 'Descriptive movement toward your personal baseline.', 'تحرك وصفي نحو مرجعك الشخصي.'),
  'resolved' => _t(context, 'Non retrouvé dans les données gouvernées actuelles.', 'Not present in current governed data.', 'لم يعد موجوداً في البيانات الموثوقة الحالية.'),
  _ => _t(context, 'Changement non déterminable avec les données disponibles.', 'Change cannot be determined from available data.', 'لا يمكن تحديد التغير من البيانات المتاحة.'),
};

IconData _changeIcon(String kind) => switch (kind) {
  'new' => Icons.fiber_new_rounded,
  'persisting' => Icons.repeat_rounded,
  'improving' => Icons.trending_flat_rounded,
  'resolved' => Icons.check_circle_outline_rounded,
  _ => Icons.help_outline_rounded,
};
