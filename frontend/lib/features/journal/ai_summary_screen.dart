import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../core/localization/ai_summary_localized_copy.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/clinical_card.dart';
import '../../core/widgets/mobile_page_header.dart';
import '../../core/widgets/first_use_panel.dart';
import '../../services/api_client.dart';
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

  Future<void> _fetchData() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });
    final api = context.read<ApiClient>();
    final results = await Future.wait([
      api.getAiSummary(days: _periodDays),
      api.getKpis(days: _periodDays),
    ]);
    if (!mounted) return;
    final summary = results[0] as SummaryResponse?;
    final kpis = results[1] as KpisResponse?;
    setState(() {
      _summary = summary;
      _kpis = kpis;
      _isLoading = false;
      if (summary == null)
        _errorMessage = AppLocalizations.of(context)!.analysisLoadError;
    });
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
