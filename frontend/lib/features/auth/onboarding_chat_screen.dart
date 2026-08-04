import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:drift/drift.dart' as drift;
import '../../core/theme/app_theme.dart';
import '../../data/drift/database.dart';

class OnboardingChatScreen extends StatefulWidget {
  const OnboardingChatScreen({super.key});

  @override
  State<OnboardingChatScreen> createState() => _OnboardingChatScreenState();
}

class _OnboardingChatScreenState extends State<OnboardingChatScreen> {
  final List<Map<String, dynamic>> _messages = [];
  bool _isTyping = false;
  double _progress = 0.2;
  final ScrollController _scrollController = ScrollController();

  final Map<String, dynamic> _userData = {
    'diabetes_type': '',
    'treatment': '',
    'target_low': 70.0,
    'target_high': 180.0,
    'unit': 'mg/dL',
  };

  @override
  void initState() {
    super.initState();
    _startConversation();
  }

  void _startConversation() async {
    await _addBotMessage(
      "Bonjour ! Je suis IAmina, ton compagnon pour une vie équilibrée avec le diabète. 😊",
    );
    await _addBotMessage(
      "Pour commencer, quel type de diabète gères-tu au quotidien ?",
    );
    _showOptions([
      {'id': 'type1', 'label': 'Diabète Type 1'},
      {'id': 'type2', 'label': 'Diabète Type 2'},
      {'id': 'gestational', 'label': 'Gestationnel'},
      {'id': 'pre', 'label': 'Pré-diabète'},
    ], _onTypeSelected);
  }

  Future<void> _addBotMessage(String text) async {
    setState(() => _isTyping = true);
    await Future.delayed(const Duration(milliseconds: 1500));
    if (!mounted) return;
    setState(() {
      _isTyping = false;
      _messages.add({'text': text, 'isBot': true});
    });
    _scrollToBottom();
  }

  void _addUserMessage(String text) {
    setState(() {
      _messages.add({'text': text, 'isBot': false});
    });
    _scrollToBottom();
  }

  void _showOptions(
    List<Map<String, String>> options,
    Function(String, String) onSelect,
  ) {
    setState(() {
      _messages.add({
        'isOptions': true,
        'options': options,
        'onSelect': onSelect,
      });
    });
    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _onTypeSelected(String id, String label) async {
    _addUserMessage(label);
    _userData['diabetes_type'] = id;
    setState(() => _progress = 0.4);

    await _addBotMessage(
      "D'accord. Et quel est ton mode de traitement principal ?",
    );
    _showOptions([
      {'id': 'insulin', 'label': 'Insuline (Injection/Pompe)'},
      {'id': 'tablets', 'label': 'Comprimés'},
      {'id': 'lifestyle', 'label': 'Hygiène de vie seule'},
    ], _onTreatmentSelected);
  }

  void _onTreatmentSelected(String id, String label) async {
    _addUserMessage(label);
    _userData['treatment'] = id;
    setState(() => _progress = 0.6);

    await _addBotMessage(
      "Très bien. Quels sont tes objectifs glycémiques (en mg/dL) ? On utilise classiquement 70–180.",
    );
    _showOptions([
      {'id': 'standard', 'label': 'Standards (70–180)'},
      {'id': 'custom', 'label': 'Personnalisés'},
    ], _onTargetSelected);
  }

  void _onTargetSelected(String id, String label) async {
    _addUserMessage(label);
    setState(() => _progress = 0.75);

    await _addBotMessage(
      "Dernière question : quelle unité préfères-tu pour les mesures ?",
    );
    _showOptions([
      {'id': 'mg/dL', 'label': 'mg/dL  (standard France/Maroc)'},
      {'id': 'mmol/L', 'label': 'mmol/L  (UK, Canada, international)'},
    ], _onUnitSelected);
  }

  void _onUnitSelected(String id, String label) async {
    _addUserMessage(label);
    _userData['unit'] = id;
    setState(() => _progress = 0.9);

    await _addBotMessage(
      "Parfait ! J'ai configuré ton espace personnel. Prêt à transformer ton suivi ?",
    );
    _showOptions([
      {'id': 'go', 'label': "C'est parti ! 🚀"},
    ], (id, label) => _finish());
  }

  void _finish() async {
    _addUserMessage("C'est parti ! 🚀");
    setState(() => _progress = 1.0);
    await _addBotMessage("Tout est prêt ! Redirection en cours…");

    if (!mounted) return;
    // Save to DB — derive a stable integer ID from Firebase UID hash
    final db = context.read<AppDatabase>();
    final firebaseUser = FirebaseAuth.instance.currentUser;
    final userId = firebaseUser?.uid.hashCode.abs() ?? 1;
    final profile = PatientProfilesCompanion.insert(
      userId: drift.Value(userId),
      preferredLanguage: const drift.Value('fr'),
      updatedAt: DateTime.now(),
      diabetesType: drift.Value(_userData['diabetes_type'] as String),
      treatment: drift.Value(_userData['treatment'] as String),
      unitPreference: drift.Value(_userData['unit'] as String),
      targetRangeLow: drift.Value(_userData['target_low'] as double),
      targetRangeHigh: drift.Value(_userData['target_high'] as double),
    );
    await db.into(db.patientProfiles).insertOnConflictUpdate(profile);

    if (mounted) context.go('/dashboard');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AminaTheme.surfaceMuted,
      body: SafeArea(
        child: Column(
          children: [
            LinearProgressIndicator(
              value: _progress,
              backgroundColor: Colors.transparent,
              valueColor: const AlwaysStoppedAnimation<Color>(
                AminaTheme.primaryTeal,
              ),
              minHeight: 4,
            ),
            _buildHeader(),
            Expanded(
              child: ListView.builder(
                controller: _scrollController,
                padding: const EdgeInsets.all(20),
                itemCount: _messages.length + (_isTyping ? 1 : 0),
                itemBuilder: (context, index) {
                  if (index == _messages.length) return _buildTypingIndicator();
                  final msg = _messages[index];
                  if (msg['isOptions'] == true) return _buildOptions(msg);
                  return _buildMessage(msg);
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        border: const Border(bottom: BorderSide(color: AminaTheme.borderLight)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.02),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              gradient: AminaTheme.heroGradient,
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(
              Icons.auto_awesome,
              color: Colors.white,
              size: 20,
            ),
          ),
          const SizedBox(width: 12),
          const Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'IAmina',
                style: TextStyle(
                  fontWeight: FontWeight.w900,
                  fontSize: 18,
                  letterSpacing: -0.5,
                ),
              ),
              Text(
                'Assistant Intelligent',
                style: TextStyle(
                  color: AminaTheme.successEmerald,
                  fontSize: 12,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 0.5,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildMessage(Map<String, dynamic> msg) {
    final isBot = msg['isBot'] as bool;
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      alignment: isBot
          ? AlignmentDirectional.centerStart
          : AlignmentDirectional.centerEnd,
      child: Container(
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.85,
        ),
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
        decoration: BoxDecoration(
          color: isBot ? const Color(0xFFF3F4F6) : AminaTheme.primaryTeal,
          borderRadius: BorderRadiusDirectional.only(
            topStart: const Radius.circular(18),
            topEnd: const Radius.circular(18),
            bottomStart: Radius.circular(isBot ? 4 : 18),
            bottomEnd: Radius.circular(isBot ? 18 : 4),
          ),
        ),
        child: Text(
          msg['text'] as String,
          style: TextStyle(
            color: isBot ? AminaTheme.textDark : Colors.white,
            fontSize: 15,
            fontWeight: isBot ? FontWeight.w500 : FontWeight.w700,
            height: 1.5,
          ),
        ),
      ),
    );
  }

  Widget _buildOptions(Map<String, dynamic> msg) {
    final options = msg['options'] as List<Map<String, String>>;
    final onSelect = msg['onSelect'] as Function(String, String);

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      child: Wrap(
        spacing: 10,
        runSpacing: 10,
        children: options.map((opt) {
          return InkWell(
            onTap: () => onSelect(opt['id']!, opt['label']!),
            borderRadius: BorderRadius.circular(14),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: AminaTheme.borderLight, width: 1.5),
              ),
              child: Text(
                opt['label']!,
                style: const TextStyle(
                  fontWeight: FontWeight.w700,
                  color: AminaTheme.textMuted,
                  fontSize: 14,
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildTypingIndicator() {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      alignment: AlignmentDirectional.centerStart,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
        decoration: BoxDecoration(
          color: Colors.grey.shade100,
          borderRadius: const BorderRadiusDirectional.only(
            topStart: Radius.circular(18),
            topEnd: Radius.circular(18),
            bottomStart: Radius.circular(4),
            bottomEnd: Radius.circular(18),
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: List.generate(3, (index) => _TypingDot(delay: index * 0.2)),
        ),
      ),
    );
  }
}

class _TypingDot extends StatefulWidget {
  final double delay;
  const _TypingDot({required this.delay});

  @override
  State<_TypingDot> createState() => _TypingDotState();
}

class _TypingDotState extends State<_TypingDot>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    Future.delayed(Duration(milliseconds: (widget.delay * 1000).toInt()), () {
      if (mounted) _controller.repeat(reverse: true);
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: Tween<double>(begin: 0.3, end: 1.0).animate(_controller),
      child: Container(
        width: 6,
        height: 6,
        margin: const EdgeInsets.symmetric(horizontal: 2),
        decoration: const BoxDecoration(
          color: Colors.grey,
          shape: BoxShape.circle,
        ),
      ),
    );
  }
}
