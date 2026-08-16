import 'package:flutter/material.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../../data/drift/database.dart';
import '../../core/data/meal_food_catalog.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/clinical_card.dart';
import '../../core/widgets/mobile_page_header.dart';
import '../../core/widgets/first_use_panel.dart';
import 'widgets/insulin_logging.dart';
import 'widgets/personal_response_section.dart';

class JournalScreen extends StatefulWidget {
  const JournalScreen({super.key});

  @override
  State<JournalScreen> createState() => _JournalScreenState();
}

class _JournalScreenState extends State<JournalScreen> {
  int _selectedFilterDays = 30;
  bool _showPersonalResponse = false;

  String _journalRangeLabel(AppLocalizations l10n) {
    switch (_selectedFilterDays) {
      case 7:
        return l10n.last7Days;
      case 0:
        return l10n.allHistory;
      default:
        return l10n.last30Days;
    }
  }

  @override
  Widget build(BuildContext context) {
    final db = Provider.of<AppDatabase>(context, listen: false);
    final profile = context.watch<PatientProfileData?>();
    final unit = profile?.unitPreference ?? 'mg/dL';
    final targetLow = profile?.targetRangeLow ?? 70.0;
    final targetHigh = profile?.targetRangeHigh ?? 180.0;
    final viewportWidth = MediaQuery.sizeOf(context).width;
    final horizontalPadding = viewportWidth >= 1100
        ? (viewportWidth - 980) / 2
        : viewportWidth >= 700
        ? 28.0
        : 20.0;

    final now = DateTime.now();
    final start = _selectedFilterDays == 0
        ? DateTime(2000)
        : now.subtract(Duration(days: _selectedFilterDays));

    return Scaffold(
      body: CustomScrollView(
        slivers: [
          _buildSliverAppBar(context),
          StreamBuilder<List<LogEntryData>>(
            stream: db.watchLogsInRange(start, now),
            builder: (context, snapshot) {
              if (snapshot.connectionState == ConnectionState.waiting) {
                return SliverPadding(
                  padding: EdgeInsetsDirectional.fromSTEB(
                    horizontalPadding,
                    16,
                    horizontalPadding,
                    20,
                  ),
                  sliver: const _JournalSkeletonSliver(),
                );
              }

              final logs = snapshot.data ?? [];
              if (logs.isEmpty) {
                return _buildEmptyJournalSliver(
                  context,
                  viewportWidth,
                  horizontalPadding,
                );
              }

              final groupedLogs = <String, List<LogEntryData>>{};
              for (final log in logs) {
                final date = log.loggedAt ?? log.createdAt;
                final dayKey = DateFormat('yyyy-MM-dd').format(date);
                groupedLogs.putIfAbsent(dayKey, () => []).add(log);
              }

              final sortedDays = groupedLogs.keys.toList()
                ..sort((a, b) => b.compareTo(a));

              return SliverMainAxisGroup(
                slivers: [
                  SliverPadding(
                    padding: EdgeInsetsDirectional.fromSTEB(
                      horizontalPadding,
                      0,
                      horizontalPadding,
                      20,
                    ),
                    sliver: SliverList(
                      delegate: SliverChildBuilderDelegate((context, index) {
                        final dayKey = sortedDays[index];
                        final dayLogs = groupedLogs[dayKey]!;
                        final date = DateTime.parse(dayKey);

                        return Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            _buildDayHeader(date),
                            ...dayLogs.map(
                              (log) => _buildEntryCapsule(
                                log,
                                unit,
                                targetLow,
                                targetHigh,
                              ),
                            ),
                          ],
                        );
                      }, childCount: sortedDays.length),
                    ),
                  ),
                  _buildPersonalResponseSliver(unit, horizontalPadding),
                ],
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _buildPersonalResponseSliver(
    String unit,
    double horizontalPadding,
  ) {
    final l10n = AppLocalizations.of(context)!;
    return SliverPadding(
      padding: EdgeInsetsDirectional.fromSTEB(
        horizontalPadding,
        0,
        horizontalPadding,
        100,
      ),
      sliver: SliverToBoxAdapter(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Align(
              alignment: AlignmentDirectional.centerStart,
              child: TextButton.icon(
                key: const Key('journal-personal-response-disclosure'),
                onPressed: () => setState(
                  () => _showPersonalResponse = !_showPersonalResponse,
                ),
                icon: Icon(
                  _showPersonalResponse
                      ? Icons.expand_less_rounded
                      : Icons.insights_outlined,
                ),
                label: Text(
                  _showPersonalResponse
                      ? l10n.personalResponseShowLess
                      : l10n.personalResponseTitle,
                ),
              ),
            ),
            if (_showPersonalResponse) ...[
              const SizedBox(height: 8),
              PersonalResponseSection(unit: unit),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildEmptyJournalSliver(
    BuildContext context,
    double viewportWidth,
    double horizontalPadding,
  ) {
    final l10n = AppLocalizations.of(context)!;
    return SliverPadding(
      padding: EdgeInsetsDirectional.fromSTEB(
        horizontalPadding,
        viewportWidth < 700 ? 12 : 24,
        horizontalPadding,
        100,
      ),
      sliver: SliverToBoxAdapter(
        child: Align(
          alignment: AlignmentDirectional.topCenter,
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 720),
            child: AminaFirstUsePanel(
              icon: Icons.timeline_rounded,
              title: l10n.journalEmpty,
              body: l10n.journalEmptySubtitle,
              primaryActionLabel: l10n.addMeasurement,
              onPrimaryAction: () => context.go('/ajouter'),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildSliverAppBar(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final isMobile = MediaQuery.sizeOf(context).width < 700;
    final rangeLabel = _journalRangeLabel(l10n);
    if (isMobile) {
      return SliverToBoxAdapter(
        child: AminaMobilePageHeader(
          title: l10n.navJournal,
          subtitle: rangeLabel,
          trailing: _buildFilterBadge(
            iconColor: AminaTheme.textSecondary(context),
          ),
        ),
      );
    }

    final topPad = MediaQuery.paddingOf(context).top + 16;
    return SliverAppBar(
      expandedHeight: 140,
      pinned: true,
      automaticallyImplyLeading: false,
      flexibleSpace: FlexibleSpaceBar(
        background: Container(
          decoration: BoxDecoration(
            gradient: AminaTheme.heroGradient,
            borderRadius: const BorderRadiusDirectional.only(
              bottomStart: Radius.circular(32),
              bottomEnd: Radius.circular(32),
            ),
          ),
          padding: EdgeInsetsDirectional.fromSTEB(24, topPad, 24, 0),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    l10n.navJournal,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 28,
                      fontWeight: FontWeight.w900,
                      letterSpacing: -0.5,
                    ),
                  ),
                  Text(
                    rangeLabel,
                    style: const TextStyle(
                      color: Colors.white70,
                      fontSize: 14,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
              _buildFilterBadge(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildFilterBadge({Color? iconColor}) {
    return Builder(
      builder: (context) {
        final l10n = AppLocalizations.of(context)!;
        return PopupMenuButton<int>(
          icon: Icon(Icons.tune, color: iconColor ?? Colors.white),
          onSelected: (days) => setState(() => _selectedFilterDays = days),
          itemBuilder: (_) => [
            PopupMenuItem(value: 7, child: Text(l10n.last7Days)),
            PopupMenuItem(value: 30, child: Text(l10n.last30Days)),
            PopupMenuItem(value: 0, child: Text(l10n.allHistory)),
          ],
        );
      },
    );
  }

  Widget _buildDayHeader(DateTime date) {
    final now = DateTime.now();
    final isToday =
        date.year == now.year && date.month == now.month && date.day == now.day;
    final l10n = AppLocalizations.of(context)!;
    final localeTag = Localizations.localeOf(context).toLanguageTag();
    final label = isToday
        ? l10n.today
        : DateFormat('EEEE d MMMM', localeTag).format(date).toUpperCase();

    return Padding(
      padding: const EdgeInsetsDirectional.fromSTEB(4, 32, 4, 12),
      child: Row(
        children: [
          Icon(
            Icons.calendar_today_outlined,
            size: 14,
            color: AminaTheme.primaryTeal.withValues(alpha: 0.5),
          ),
          const SizedBox(width: 8),
          Text(
            label,
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w700,
              color: AminaTheme.textSecondary(context),
              letterSpacing: 0.5,
            ),
          ),
        ],
      ),
    );
  }

  String _entryContextLabel(LogEntryData log, AppLocalizations l10n) {
    final meal = log.mealType;
    switch (meal) {
      case 'breakfast':
        return l10n.journalMealBreakfast;
      case 'lunch':
        return l10n.journalMealLunch;
      case 'dinner':
        return l10n.journalMealDinner;
      case 'snack':
        return l10n.journalMealSnack;
      case 'iftar':
        return l10n.journalMealIftar;
      case 'suhoor':
        return l10n.journalMealSuhoor;
      case 'other':
        return l10n.journalMealOther;
      case null:
      case '':
        break;
      default:
        return meal;
    }

    switch (log.glycemicContext) {
      case 'fasting':
        return l10n.journalContextFasting;
      case 'pre_meal':
        return l10n.journalContextPreMeal;
      case 'post_meal':
        return l10n.journalContextPostMeal;
      case 'other':
        return l10n.journalContextOther;
      default:
        return l10n.freeMeasurement;
    }
  }

  Widget _buildEntryCapsule(
    LogEntryData log,
    String unit,
    double low,
    double high,
  ) {
    final val = log.bloodSugar;
    final displayValue = unit == 'mmol/L'
        ? (val / 18.0).toStringAsFixed(1)
        : val.toStringAsFixed(0);
    Color color = AminaTheme.successEmerald;
    if (val < 70) {
      color = AminaTheme.dangerRed;
    } else if (val < low || val > high) {
      color = AminaTheme.accentAmber;
    }

    return Dismissible(
      key: ValueKey(log.id),
      direction: DismissDirection.endToStart,
      background: Container(
        margin: const EdgeInsets.only(bottom: 10),
        alignment: AlignmentDirectional.centerEnd,
        padding: const EdgeInsetsDirectional.only(end: 20),
        decoration: BoxDecoration(
          color: AminaTheme.dangerRed,
          borderRadius: BorderRadius.circular(16),
        ),
        child: const Icon(Icons.delete_outline, color: Colors.white, size: 24),
      ),
      confirmDismiss: (_) async {
        return await showDialog<bool>(
              context: context,
              builder: (ctx) {
                final dl10n = AppLocalizations.of(ctx)!;
                return AlertDialog(
                  title: Text(dl10n.deleteEntryTitle),
                  content: Text(dl10n.actionIrreversible),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.pop(ctx, false),
                      child: Text(dl10n.cancel),
                    ),
                    TextButton(
                      onPressed: () => Navigator.pop(ctx, true),
                      child: Text(
                        dl10n.delete,
                        style: const TextStyle(color: AminaTheme.dangerRed),
                      ),
                    ),
                  ],
                );
              },
            ) ??
            false;
      },
      onDismissed: (_) async {
        final l10n = AppLocalizations.of(context)!;
        final db = Provider.of<AppDatabase>(context, listen: false);
        final messenger = ScaffoldMessenger.of(
          context,
        ); // capture before async gap
        await db.deleteLog(log.id);
        messenger.showSnackBar(
          SnackBar(
            content: Text(l10n.entryDeleted),
            behavior: SnackBarBehavior.floating,
          ),
        );
      },
      child: GestureDetector(
        onTap: () => context.push('/journal/${log.id}/edit'),
        child: Container(
          margin: const EdgeInsets.only(bottom: 10),
          child: ClinicalCard(
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
            child: Row(
              children: [
                SizedBox(
                  width: 52,
                  child: Center(
                    child: Text(
                      displayValue,
                      style: TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.w900,
                        color: color,
                        letterSpacing: -1.0,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Text(
                            _entryContextLabel(
                              log,
                              AppLocalizations.of(context)!,
                            ),
                            style: const TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w700,
                              color: AminaTheme.textDark,
                            ),
                          ),
                          if (log.ramadanMode) ...[
                            const SizedBox(width: 6),
                            const Text('🌙', style: TextStyle(fontSize: 12)),
                          ],
                        ],
                      ),
                      const SizedBox(height: 2),
                      Text(
                        DateFormat.Hm().format(log.loggedAt ?? log.createdAt),
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: AminaTheme.textMuted.withValues(alpha: 0.7),
                        ),
                      ),
                      if (decodeMealItemIds(log.mealItemsJson).isNotEmpty) ...[
                        const SizedBox(height: 6),
                        Wrap(
                          spacing: 4,
                          runSpacing: 4,
                          children: decodeMealItemIds(log.mealItemsJson)
                              .map(mealFoodById)
                              .whereType<MealFoodItem>()
                              .map(
                                (food) => Container(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 6,
                                    vertical: 2,
                                  ),
                                  decoration: BoxDecoration(
                                    color: AminaTheme.textMuted.withValues(
                                      alpha: 0.05,
                                    ),
                                    borderRadius: BorderRadius.circular(4),
                                    border: Border.all(
                                      color: AminaTheme.textMuted.withValues(
                                        alpha: 0.1,
                                      ),
                                    ),
                                  ),
                                  child: Text(
                                    food.labelFor(
                                      Localizations.localeOf(context),
                                    ),
                                    style: TextStyle(
                                      fontSize: 10,
                                      fontWeight: FontWeight.w600,
                                      color: AminaTheme.textMuted.withValues(
                                        alpha: 0.8,
                                      ),
                                    ),
                                  ),
                                ),
                              )
                              .toList(),
                        ),
                      ],
                      if (log.mealDescription != null &&
                          log.mealDescription!.trim().isNotEmpty) ...[
                        const SizedBox(height: 5),
                        Text(
                          log.mealDescription!.trim(),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            fontSize: 11,
                            color: AminaTheme.textMuted.withValues(alpha: 0.8),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        if (log.insulinUnits != null &&
                            log.insulinUnits! > 0) ...[
                          Container(
                            margin: const EdgeInsetsDirectional.only(end: 8),
                            padding: const EdgeInsets.symmetric(
                              horizontal: 8,
                              vertical: 4,
                            ),
                            decoration: BoxDecoration(
                              color: AminaTheme.primaryTeal.withValues(
                                alpha: 0.05,
                              ),
                              borderRadius: BorderRadius.circular(
                                AminaTheme.radiusXL,
                              ),
                            ),
                            child: Text(
                              '${formatTakenInsulinUnits(log.insulinUnits!)} U',
                              style: const TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.w900,
                                color: AminaTheme.primaryTeal,
                              ),
                            ),
                          ),
                        ],
                        _buildSyncIcon(log.syncStatus),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        if (log.isSick) const _LifeIcon(icon: '🤒'),
                        if (log.isStressed) const _LifeIcon(icon: '⚡'),
                        if (log.isTired) const _LifeIcon(icon: '🥱'),
                        if (log.isActive) const _LifeIcon(icon: '🏃‍♂️'),
                        if (log.sleepQuality == 'bad')
                          const _LifeIcon(icon: '🌙'),
                      ],
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildSyncIcon(String status) {
    if (status == 'pending') {
      return Icon(
        Icons.cloud_sync_outlined,
        size: 16,
        color: AminaTheme.warningOrange.withValues(alpha: 0.4),
      );
    }
    if (status == 'error') {
      return Icon(
        Icons.error_outline,
        size: 16,
        color: AminaTheme.dangerRed.withValues(alpha: 0.4),
      );
    }
    return const SizedBox.shrink();
  }
}

class _LifeIcon extends StatelessWidget {
  final String icon;
  const _LifeIcon({required this.icon});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsetsDirectional.only(start: 4),
      child: Text(icon, style: const TextStyle(fontSize: 12)),
    );
  }
}

class _JournalSkeletonSliver extends StatelessWidget {
  const _JournalSkeletonSliver();

  @override
  Widget build(BuildContext context) {
    return SliverList(
      delegate: SliverChildBuilderDelegate(
        (context, index) => _SkeletonGroup(),
        childCount: 3,
      ),
    );
  }
}

class _SkeletonGroup extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return const Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: EdgeInsetsDirectional.fromSTEB(0, 20, 0, 10),
          child: _SkeletonBox(width: 100, height: 13, radius: 6),
        ),
        _SkeletonCapsule(),
        SizedBox(height: 8),
        _SkeletonCapsule(narrowRight: true),
        SizedBox(height: 8),
        _SkeletonCapsule(),
        SizedBox(height: 8),
      ],
    );
  }
}

class _SkeletonCapsule extends StatelessWidget {
  final bool narrowRight;
  const _SkeletonCapsule({this.narrowRight = false});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AminaTheme.surface(context),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AminaTheme.divider(context)),
      ),
      child: Row(
        children: [
          const _SkeletonBox(width: 42, height: 42, radius: 10),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _SkeletonBox(
                  width: narrowRight ? 100 : 140,
                  height: 13,
                  radius: 5,
                ),
                const SizedBox(height: 6),
                const _SkeletonBox(width: 80, height: 10, radius: 4),
              ],
            ),
          ),
          const _SkeletonBox(width: 48, height: 22, radius: 11),
        ],
      ),
    );
  }
}

class _SkeletonBox extends StatefulWidget {
  final double width, height, radius;
  const _SkeletonBox({
    required this.width,
    required this.height,
    required this.radius,
  });
  @override
  State<_SkeletonBox> createState() => _SkeletonBoxState();
}

class _SkeletonBoxState extends State<_SkeletonBox>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  late final Animation<double> _anim;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1000),
    )..repeat(reverse: true);
    _anim = Tween<double>(
      begin: 0.28,
      end: 0.65,
    ).animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeInOut));
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _anim,
      builder: (_, __) => Container(
        width: widget.width,
        height: widget.height,
        decoration: BoxDecoration(
          color: AminaTheme.divider(context).withValues(alpha: _anim.value),
          borderRadius: BorderRadius.circular(widget.radius),
        ),
      ),
    );
  }
}
