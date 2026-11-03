import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../core/localization/ai_summary_localized_copy.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/clinical_card.dart';
import '../../core/widgets/mobile_page_header.dart';
import '../../core/widgets/first_use_panel.dart';
import '../../data/drift/database.dart';
import '../../data/models/ai_models.dart';
import '../../l10n/app_localizations.dart';
import '../../l10n/audited_page_copy.dart';
import './widgets/amina_chat_view.dart';
import '../dashboard/widgets/tweaks_panel.dart';
import '../dashboard/widgets/agp_chart.dart';

part 'ai_summary_screen_presentation.dart';

// ─────────────────────────────────────────────────────────────────────────────
// IAmina Summary Screen — Redesign
// ─────────────────────────────────────────────────────────────────────────────

class AISummaryScreen extends StatefulWidget {
  const AISummaryScreen({super.key});
  @override
  State<AISummaryScreen> createState() => _AISummaryScreenState();
}

class _AISummaryScreenState extends State<AISummaryScreen> {
  bool _isLoading = true;
  SummaryResponse? _summary;
  KpisResponse? _kpis;
  String? _errorMessage;
  bool? _hasLocalLogs;
  bool _showTweaks = false;
  int _periodDays = 21;
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _initialize());
  }

  Future<void> _initialize() async {
    final db = context.read<AppDatabase>();
    final count = await db.countLogs();
    if (!mounted) return;
    setState(() => _hasLocalLogs = count > 0);
    await _fetchData();
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToInsights() {
    _scrollController.animateTo(
      _scrollController.position.maxScrollExtent * 0.45,
      duration: const Duration(milliseconds: 500),
      curve: Curves.easeInOut,
    );
  }

  /// D22 Gate A: personalized analysis needs a verified target and source.
  /// No KPI or personalized AI request is made by this UI until Gate B.
  Future<void> _fetchData() async {
    if (!mounted) return;
    setState(() {
      _isLoading = false;
      _errorMessage = null;
      _summary = null;
      _kpis = null;
    });
  }

  Widget _buildD22SafetyNotice() {
    final copy = switch (Localizations.localeOf(context).languageCode) {
      'fr' => 'Analyse personnalisée temporairement indisponible : les objectifs glycémiques historiques ne sont pas vérifiés.',
      'ar' => 'التحليل الشخصي غير متاح مؤقتًا: لم يتم التحقق من أهداف سكر الدم القديمة.',
      _ => 'Personalized analysis is temporarily unavailable: historical glucose targets are unverified.',
    };
    // D22 Gate A: show the safety notice near the header, not in the
    // middle of a blank mobile/desktop viewport.
    return Align(
      alignment: AlignmentDirectional.topCenter,
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 640),
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.info_outline_rounded, size: 26),
                  const SizedBox(height: 12),
                  Text(
                    copy,
                    key: const Key('d22-ai-summary-target-unverified'),
                    style: Theme.of(context).textTheme.bodyLarge,
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  void _setPeriod(int days) {
    if (_periodDays == days) return;
    setState(() => _periodDays = days);
    _fetchData();
  }

  void _openChat() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => DraggableScrollableSheet(
        initialChildSize: 0.9,
        minChildSize: 0.5,
        maxChildSize: 0.95,
        builder: (ctx, _) => AminaChatView(onClose: () => Navigator.pop(ctx)),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AminaTheme.bg(context),
      body: Stack(
        children: [
          Positioned.fill(
            child: Column(
              children: [
                _SummaryTopBar(
                  periodDays: _periodDays,
                  onPeriodChange: _setPeriod,
                  onTweaksTap: () => setState(() => _showTweaks = !_showTweaks),
                ),
                Expanded(
                  child: _isLoading
                      ? _buildLoader()
                      : _errorMessage != null
                      ? (_hasLocalLogs == false
                            ? _buildFirstUse()
                            : _buildError())
                      : _summary == null && _kpis == null
                      ? (_hasLocalLogs == false
                            ? _buildFirstUse()
                            : _buildD22SafetyNotice())
                      : _buildContent(),
                ),
              ],
            ),
          ),
          if (_showTweaks)
            Positioned.fill(
              child: TweaksPanel(
                onClose: () => setState(() => _showTweaks = false),
              ),
            ),
        ],
      ),
    );
  }


}
