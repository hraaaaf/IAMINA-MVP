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
  late Future<CompanionOverview?> _future = _service.fetchOverview();

  @override
  void dispose() {
    if (widget.service == null) _service.dispose();
    super.dispose();
  }

  void _reload() => setState(() => _future = _service.fetchOverview());

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
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          final overview = snapshot.data;
          if (overview == null) {
            return _Unavailable(onRetry: _reload);
          }
          return _Overview(overview: overview);
        },
      ),
    );
  }
}

class _Overview extends StatelessWidget {
  final CompanionOverview overview;

  const _Overview({required this.overview});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsetsDirectional.fromSTEB(18, 8, 18, 32),
      children: [
        const _SafetyCard(),
        const SizedBox(height: 18),
        _SectionTitle(
          eyebrow: _t(context, 'COMPRENDRE', 'UNDERSTAND', 'افهم'),
          title: _t(
            context,
            'Ce que vos données montrent',
            'What your data shows',
            'ما الذي تظهره بياناتك',
          ),
        ),
        const SizedBox(height: 9),
        if (overview.patterns.isEmpty)
          _MessageCard(
            text: _t(
              context,
              'Pas encore assez de données répétées pour afficher un schéma personnel gouverné.',
              'Not enough repeated data yet to show a governed personal pattern.',
              'لا توجد بيانات متكررة كافية بعد لإظهار نمط شخصي موثوق.',
            ),
          )
        else
          ...overview.patterns.map((pattern) => _PatternCard(pattern: pattern)),
        const SizedBox(height: 20),
        _SectionTitle(
          eyebrow: _t(context, 'SUIVRE', 'FOLLOW', 'تابع'),
          title: _t(
            context,
            'Depuis votre dernière revue',
            'Since your last review',
            'منذ آخر مراجعة لك',
          ),
        ),
        const SizedBox(height: 9),
        if (overview.reviewStatus != 'ready')
          _MessageCard(
            text: _t(
              context,
              'Aucune revue précédente fiable à comparer. IAmina ne fabrique pas d’historique.',
              'No reliable previous review to compare. IAmina does not invent history.',
              'لا توجد مراجعة سابقة موثوقة للمقارنة. IAmina لا تنشئ تاريخاً غير موجود.',
            ),
          )
        else if (overview.changesSinceReview.isEmpty)
          _MessageCard(
            text: _t(
              context,
              'Aucun changement gouverné à afficher depuis la dernière revue.',
              'No governed change to show since the last review.',
              'لا يوجد تغير موثوق لعرضه منذ آخر مراجعة.',
            ),
          )
        else
          ...overview.changesSinceReview.map((change) => _ChangeCard(change: change)),
        const SizedBox(height: 20),
        _SectionTitle(
          eyebrow: _t(context, 'PRÉPARER', 'PREPARE', 'استعد'),
          title: _t(
            context,
            'Continuité après consultation',
            'After-visit continuity',
            'المتابعة بعد الاستشارة',
          ),
        ),
        const SizedBox(height: 9),
        _AfterVisitCard(afterVisit: overview.afterVisit),
      ],
    );
  }
}

class _SafetyCard extends StatelessWidget {
  const _SafetyCard();

  @override
  Widget build(BuildContext context) {
    return _SurfaceCard(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.shield_outlined, size: 20, color: Color(0xFF0B6B70)),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              _t(
                context,
                'IAmina vous aide à comprendre et suivre vos données. Les décisions médicales restent avec votre professionnel de santé.',
                'IAmina helps you understand and follow your data. Medical decisions remain with your clinician.',
                'تساعدك IAmina على فهم بياناتك ومتابعتها. تبقى القرارات الطبية مع طبيبك.',
              ),
              style: TextStyle(
                fontSize: 12.5,
                height: 1.4,
                color: AminaTheme.textSecondary(context),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  final String eyebrow;
  final String title;

  const _SectionTitle({required this.eyebrow, required this.title});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          eyebrow,
          style: const TextStyle(
            color: Color(0xFF0B6B70),
            fontSize: 10.5,
            fontWeight: FontWeight.w800,
            letterSpacing: 1.1,
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
    return _SurfaceCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  _friendlyKey(context, pattern.observationKey),
                  style: TextStyle(
                    fontWeight: FontWeight.w800,
                    color: AminaTheme.textPrimary(context),
                  ),
                ),
              ),
              _RepeatabilityPill(density: pattern.evidenceDensity),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            _movement(context, pattern.baselineMovement),
            style: TextStyle(
              fontSize: 12.5,
              height: 1.4,
              color: AminaTheme.textSecondary(context),
            ),
          ),
          const SizedBox(height: 7),
          Text(
            _t(
              context,
              '${pattern.recurrenceCount} occurrence(s) dans votre historique gouverné.',
              '${pattern.recurrenceCount} occurrence(s) in your governed history.',
              '${pattern.recurrenceCount} حالة في سجلك الموثوق.',
            ),
            style: TextStyle(
              fontSize: 11.5,
              color: AminaTheme.textSecondary(context),
            ),
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
    return _SurfaceCard(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(_changeIcon(change.changeKind), size: 20, color: const Color(0xFF0B6B70)),
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
                  style: TextStyle(
                    fontSize: 12.5,
                    height: 1.35,
                    color: AminaTheme.textSecondary(context),
                  ),
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
                    style: TextStyle(
                      fontSize: 11.5,
                      color: AminaTheme.textSecondary(context),
                    ),
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(width: 8),
          _RepeatabilityPill(density: change.evidenceStrength),
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
      return _MessageCard(
        text: _t(
          context,
          'Aucune consultation n’a été explicitement enregistrée. IAmina ne la déduit pas de votre activité.',
          'No consultation has been explicitly recorded. IAmina does not infer one from your activity.',
          'لم يتم تسجيل أي استشارة بشكل صريح. لا تستنتج IAmina ذلك من نشاطك.',
        ),
      );
    }
    return _SurfaceCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            _t(context, 'Consultation enregistrée', 'Recorded consultation', 'استشارة مسجلة'),
            style: TextStyle(
              fontWeight: FontWeight.w800,
              color: AminaTheme.textPrimary(context),
            ),
          ),
          const SizedBox(height: 6),
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
              'Un changement après la consultation ne prouve pas que le traitement en est la cause.',
              'A change after the visit does not prove that treatment caused it.',
              'حدوث تغير بعد الاستشارة لا يثبت أن العلاج هو السبب.',
            ),
            style: TextStyle(
              fontSize: 11.5,
              height: 1.4,
              color: AminaTheme.textSecondary(context),
            ),
          ),
        ],
      ),
    );
  }
}

class _RepeatabilityPill extends StatelessWidget {
  final String density;

  const _RepeatabilityPill({required this.density});

  @override
  Widget build(BuildContext context) {
    final label = switch (density) {
      'strong' => _t(context, 'Répétabilité forte', 'Strong repeatability', 'تكرار قوي'),
      'moderate' => _t(context, 'Répétabilité modérée', 'Moderate repeatability', 'تكرار متوسط'),
      _ => _t(context, 'Répétabilité limitée', 'Limited repeatability', 'تكرار محدود'),
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: const Color(0xFF0B6B70).withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(18),
      ),
      child: Text(
        label,
        style: const TextStyle(
          color: Color(0xFF0B6B70),
          fontSize: 10.5,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}

class _SurfaceCard extends StatelessWidget {
  final Widget child;

  const _SurfaceCard({required this.child});

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

class _MessageCard extends StatelessWidget {
  final String text;

  const _MessageCard({required this.text});

  @override
  Widget build(BuildContext context) {
    return _SurfaceCard(
      child: Text(
        text,
        style: TextStyle(
          fontSize: 12.5,
          height: 1.4,
          color: AminaTheme.textSecondary(context),
        ),
      ),
    );
  }
}

class _Unavailable extends StatelessWidget {
  final VoidCallback onRetry;

  const _Unavailable({required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(28),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.cloud_off_outlined, size: 34, color: AminaTheme.textSecondary(context)),
            const SizedBox(height: 12),
            Text(
              _t(context, 'Données indisponibles', 'Data unavailable', 'البيانات غير متاحة'),
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w800,
                color: AminaTheme.textPrimary(context),
              ),
            ),
            const SizedBox(height: 7),
            Text(
              _t(
                context,
                'IAmina ne peut pas charger votre suivi pour le moment.',
                'IAmina cannot load your companion view right now.',
                'يتعذر على IAmina تحميل المتابعة حالياً.',
              ),
              textAlign: TextAlign.center,
              style: TextStyle(color: AminaTheme.textSecondary(context)),
            ),
            const SizedBox(height: 14),
            OutlinedButton(
              onPressed: onRetry,
              child: Text(_t(context, 'Réessayer', 'Retry', 'إعادة المحاولة')),
            ),
          ],
        ),
      ),
    );
  }
}

String _friendlyKey(BuildContext context, String key) {
  const values = <String, List<String>>{
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
  final value = values[key];
  if (value == null) return key;
  final code = Localizations.localeOf(context).languageCode;
  return code == 'ar' ? value[2] : code == 'en' ? value[1] : value[0];
}

String _movement(BuildContext context, String value) => switch (value) {
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
  'improving' => _t(
      context,
      'Mouvement descriptif vers votre référence personnelle, sans conclure à un effet du traitement.',
      'Descriptive movement toward your personal baseline, without inferring a treatment effect.',
      'تحرك وصفي نحو مرجعك الشخصي دون استنتاج تأثير للعلاج.',
    ),
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
