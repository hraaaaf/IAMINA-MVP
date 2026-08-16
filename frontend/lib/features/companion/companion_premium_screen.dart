import 'package:flutter/material.dart';

import '../../core/theme/amina_visual_language.dart';
import '../../core/theme/app_theme.dart';
import '../../data/models/companion_models.dart';
import '../../services/companion_service.dart';
import 'companion_uncertainty_copy.dart';

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

  void _reload() => setState(() => _future = _service.fetchOverview());

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
                        'Votre suivi ne peut pas être chargé pour le moment. Aucune interprétation n’est inventée.',
                        'Your companion view cannot be loaded right now. No interpretation is invented.',
                        'يتعذر تحميل المتابعة حالياً. لا يتم اختراع أي تفسير.',
                      ),
                      actionLabel: _t(context, 'Réessayer', 'Retry', 'إعادة المحاولة'),
                      onAction: _reload,
                    ),
                  );
                }

                return _Overview(overview: overview);
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _Shell extends StatelessWidget {
  final Widget child;
  const _Shell({required this.child});

  @override
  Widget build(BuildContext context) {
    return CustomScrollView(
      physics: const BouncingScrollPhysics(),
      slivers: [
        SliverPadding(
          padding: const EdgeInsetsDirectional.fromSTEB(20, 14, 20, 40),
          sliver: SliverList(
            delegate: SliverChildListDelegate([
              const _BrandHeader(),
              const SizedBox(height: 24),
              child,
            ]),
          ),
        ),
      ],
    );
  }
}

class _Overview extends StatelessWidget {
  final CompanionOverview overview;
  const _Overview({required this.overview});

  @override
  Widget build(BuildContext context) {
    return CustomScrollView(
      physics: const BouncingScrollPhysics(),
      slivers: [
        SliverPadding(
          padding: const EdgeInsetsDirectional.fromSTEB(20, 14, 20, 48),
          sliver: SliverList(
            delegate: SliverChildListDelegate([
              const _BrandHeader(),
              const SizedBox(height: 24),
              Text(
                _t(context, 'Mon compagnon', 'My companion', 'رفيقي الصحي'),
                style: TextStyle(
                  fontFamily: 'Georgia',
                  fontSize: 30,
                  height: 1.05,
                  fontWeight: FontWeight.w700,
                  letterSpacing: -.7,
                  color: AminaVisualLanguage.primaryText(context),
                ),
              ),
              const SizedBox(height: 7),
              Text(
                _t(
                  context,
                  'Comprendre ce qui se répète, ce qui change et ce qui reste incertain.',
                  'Understand what repeats, what changes, and what remains uncertain.',
                  'افهم ما يتكرر وما يتغير وما يبقى غير مؤكد.',
                ),
                style: TextStyle(
                  fontSize: 14,
                  height: 1.4,
                  color: AminaVisualLanguage.secondary(context),
                ),
              ),
              const SizedBox(height: 20),
              const _SafetyCard(),
              const SizedBox(height: 22),
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
                _MessageCard(
                  icon: Icons.auto_graph_rounded,
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
                _MessageCard(
                  icon: Icons.history_rounded,
                  text: _t(
                    context,
                    'Aucune revue précédente fiable à comparer. IAmina ne fabrique pas d’historique.',
                    'No reliable previous review to compare. IAmina does not invent history.',
                    'لا توجد مراجعة سابقة موثوقة للمقارنة. IAmina لا تنشئ تاريخاً غير موجود.',
                  ),
                )
              else if (overview.changesSinceReview.isEmpty)
                _MessageCard(
                  icon: Icons.check_circle_outline_rounded,
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
            ]),
          ),
        ),
      ],
    );
  }
}

class _BrandHeader extends StatelessWidget {
  const _BrandHeader();

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 58,
          height: 58,
          padding: const EdgeInsets.all(5),
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: .88),
            borderRadius: BorderRadius.circular(18),
            boxShadow: AminaVisualLanguage.cardShadowLight,
          ),
          child: Image.asset('assets/images/logo_amina.png', fit: BoxFit.contain),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'IAmina',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w800,
                  letterSpacing: -.45,
                  color: AminaVisualLanguage.primaryText(context),
                ),
              ),
              const SizedBox(height: 3),
              Text(
                _t(context, 'Compagnon gouverné', 'Governed companion', 'رفيق محكوم'),
                style: TextStyle(
                  fontSize: 12,
                  color: AminaVisualLanguage.secondary(context),
                ),
              ),
            ],
          ),
        ),
        IconButton(
          onPressed: () => Navigator.of(context).maybePop(),
          icon: const Icon(Icons.close_rounded),
          style: IconButton.styleFrom(
            minimumSize: const Size(46, 46),
            backgroundColor: AminaVisualLanguage.controlSurface(context),
            foregroundColor: AminaVisualLanguage.forestDeep,
            side: BorderSide(color: AminaVisualLanguage.controlBorder(context)),
          ),
        ),
      ],
    );
  }
}

class _SafetyCard extends StatelessWidget {
  const _SafetyCard();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: AminaVisualLanguage.cardDecoration(
        context,
        color: AminaVisualLanguage.mintSurface.withValues(alpha: .75),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 42,
            height: 42,
            decoration: AminaVisualLanguage.mintIconDecoration(context),
            child: const Icon(
              Icons.shield_outlined,
              color: AminaVisualLanguage.actionGreen,
              size: 21,
            ),
          ),
          const SizedBox(width: 12),
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
                height: 1.45,
                color: AminaVisualLanguage.secondary(context),
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
            color: AminaVisualLanguage.actionGreen,
            fontSize: 10.5,
            fontWeight: FontWeight.w800,
            letterSpacing: 1.15,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          title,
          style: TextStyle(
            fontFamily: 'Georgia',
            fontSize: 21,
            fontWeight: FontWeight.w700,
            color: AminaVisualLanguage.primaryText(context),
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
    final limitationLabels = pattern.limitations
        .map((code) => companionPatternLimitationLabel(context, code))
        .whereType<String>()
        .toList(growable: false);

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
                    fontSize: 15,
                    fontWeight: FontWeight.w800,
                    color: AminaVisualLanguage.primaryText(context),
                  ),
                ),
              ),
              _EvidencePill(value: pattern.evidenceDensity),
            ],
          ),
          const SizedBox(height: 9),
          Text(
            _movement(context, pattern.baselineMovement),
            style: TextStyle(
              fontSize: 12.5,
              height: 1.45,
              color: AminaVisualLanguage.secondary(context),
            ),
          ),
          const SizedBox(height: 9),
          Text(
            _t(
              context,
              '${pattern.recurrenceCount} occurrence(s) dans votre historique gouverné.',
              '${pattern.recurrenceCount} occurrence(s) in your governed history.',
              '${pattern.recurrenceCount} حالة في سجلك الموثوق.',
            ),
            style: TextStyle(
              fontSize: 11.5,
              fontWeight: FontWeight.w600,
              color: AminaVisualLanguage.secondary(context),
            ),
          ),
          if (limitationLabels.isNotEmpty) ...[
            const SizedBox(height: 10),
            ...limitationLabels.map((label) => _UncertaintyNote(text: label)),
          ],
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
    final missingDataLabels = change.missingData
        .map((code) => companionMissingDataLabel(context, code))
        .whereType<String>()
        .toList(growable: false);

    return _SurfaceCard(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: AminaVisualLanguage.mintIconDecoration(context),
            child: Icon(
              _changeIcon(change.changeKind),
              size: 20,
              color: AminaVisualLanguage.actionGreen,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _friendlyKey(context, change.observationKey),
                  style: TextStyle(
                    fontWeight: FontWeight.w800,
                    color: AminaVisualLanguage.primaryText(context),
                  ),
                ),
                const SizedBox(height: 5),
                Text(
                  _changeLabel(context, change.changeKind),
                  style: TextStyle(
                    fontSize: 12.5,
                    height: 1.4,
                    color: AminaVisualLanguage.secondary(context),
                  ),
                ),
                if (missingDataLabels.isNotEmpty) ...[
                  const SizedBox(height: 9),
                  ...missingDataLabels.map((label) => _UncertaintyNote(text: label)),
                ],
              ],
            ),
          ),
          const SizedBox(width: 8),
          _EvidencePill(value: change.evidenceStrength),
        ],
      ),
    );
  }
}

class _UncertaintyNote extends StatelessWidget {
  final String text;
  const _UncertaintyNote({required this.text});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 5),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            Icons.info_outline_rounded,
            size: 15,
            color: AminaVisualLanguage.secondary(context),
          ),
          const SizedBox(width: 6),
          Expanded(
            child: Text(
              text,
              style: TextStyle(
                fontSize: 11.5,
                height: 1.4,
                color: AminaVisualLanguage.secondary(context),
              ),
            ),
          ),
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
        icon: Icons.event_note_outlined,
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
              color: AminaVisualLanguage.primaryText(context),
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
            style: TextStyle(fontSize: 12.5, color: AminaVisualLanguage.secondary(context)),
          ),
          const SizedBox(height: 9),
          Text(
            _t(
              context,
              'Un changement après la consultation ne prouve pas que le traitement en est la cause.',
              'A change after the visit does not prove that treatment caused it.',
              'حدوث تغير بعد الاستشارة لا يثبت أن العلاج هو السبب.',
            ),
            style: TextStyle(
              fontSize: 11.5,
              height: 1.45,
              color: AminaVisualLanguage.secondary(context),
            ),
          ),
        ],
      ),
    );
  }
}

class _MessageCard extends StatelessWidget {
  final IconData icon;
  final String text;
  const _MessageCard({required this.icon, required this.text});

  @override
  Widget build(BuildContext context) {
    return _SurfaceCard(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: AminaVisualLanguage.mintIconDecoration(context),
            child: Icon(icon, color: AminaVisualLanguage.actionGreen, size: 20),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              text,
              style: TextStyle(
                fontSize: 12.5,
                height: 1.45,
                color: AminaVisualLanguage.secondary(context),
              ),
            ),
          ),
        ],
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
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(18),
      decoration: AminaVisualLanguage.cardDecoration(context),
      child: child,
    );
  }
}

class _EvidencePill extends StatelessWidget {
  final String value;
  const _EvidencePill({required this.value});

  @override
  Widget build(BuildContext context) {
    final label = switch (value) {
      'strong' => _t(context, 'Forte', 'Strong', 'قوية'),
      'moderate' => _t(context, 'Modérée', 'Moderate', 'متوسطة'),
      _ => _t(context, 'Limitée', 'Limited', 'محدودة'),
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: AminaVisualLanguage.mintSurface,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        label,
        style: const TextStyle(
          color: AminaVisualLanguage.actionGreen,
          fontSize: 10.5,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }
}

class _StateCard extends StatelessWidget {
  final bool loading;
  final IconData? icon;
  final String title;
  final String body;
  final String? actionLabel;
  final VoidCallback? onAction;

  const _StateCard({
    this.loading = false,
    this.icon,
    required this.title,
    required this.body,
    this.actionLabel,
    this.onAction,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 30),
      decoration: AminaVisualLanguage.cardDecoration(context),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (loading)
            const CircularProgressIndicator()
          else
            Container(
              width: 54,
              height: 54,
              decoration: AminaVisualLanguage.mintIconDecoration(context),
              child: Icon(
                icon ?? Icons.auto_awesome_rounded,
                color: AminaVisualLanguage.actionGreen,
                size: 25,
              ),
            ),
          const SizedBox(height: 18),
          Text(
            title,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontFamily: 'Georgia',
              fontSize: 24,
              fontWeight: FontWeight.w700,
              color: AminaVisualLanguage.primaryText(context),
            ),
          ),
          const SizedBox(height: 9),
          Text(
            body,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 13,
              height: 1.5,
              color: AminaVisualLanguage.secondary(context),
            ),
          ),
          if (actionLabel != null && onAction != null) ...[
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              height: 46,
              child: FilledButton.icon(
                onPressed: onAction,
                icon: const Icon(Icons.refresh_rounded, size: 18),
                label: Text(actionLabel!),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _AmbientBackground extends StatelessWidget {
  const _AmbientBackground();

  @override
  Widget build(BuildContext context) {
    if (AminaTheme.isDark(context)) return const SizedBox.shrink();
    return IgnorePointer(
      child: Stack(
        children: [
          PositionedDirectional(
            top: -110,
            end: -105,
            child: Container(
              width: 290,
              height: 290,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AminaVisualLanguage.mintWaveLight.withValues(alpha: .70),
              ),
            ),
          ),
          PositionedDirectional(
            bottom: -140,
            start: -90,
            child: Container(
              width: 320,
              height: 240,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(180),
                color: AminaVisualLanguage.mintWaveStrong.withValues(alpha: .38),
              ),
            ),
          ),
        ],
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