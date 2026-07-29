import 'dart:async';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:drift/drift.dart' hide Column;
import 'package:record/record.dart';
import 'package:flutter_tts/flutter_tts.dart';
import '../../../core/theme/app_theme.dart';
import '../../../services/api_client.dart';
import '../../../data/drift/database.dart';

class AminaChatView extends StatefulWidget {
  final VoidCallback onClose;
  final String? initialMessage;
  const AminaChatView({super.key, required this.onClose, this.initialMessage});

  @override
  State<AminaChatView> createState() => _AminaChatViewState();
}

enum _VoiceState { idle, recording, processing }

class _AminaChatViewState extends State<AminaChatView> {
  final TextEditingController _ctrl       = TextEditingController();
  final ScrollController      _scrollCtrl = ScrollController();
  final List<Map<String, dynamic>> _messages = [];
  bool _isTyping = false;
  bool _showScrollDown = false;
  StreamSubscription<String>? _streamSub;

  // Voice
  final AudioRecorder _recorder = AudioRecorder();
  final FlutterTts    _tts      = FlutterTts();
  _VoiceState _voiceState = _VoiceState.idle;

  // Suggested prompts — generated dynamically in _buildSuggestions()
  // Fallback static set used when no log data is available
  static const _fallbackSuggestions = [
    'Comment se passe ma semaine ?',
    'Ai-je eu des hypos ?',
    'Éviter les pics',
    'Mon meilleur jour',
  ];

  bool get _hasUserMessage => _messages.any((m) => m['isAi'] == false);

  @override
  void initState() {
    super.initState();
    _initTts();
    _loadHistory();
    if (widget.initialMessage != null) {
      _ctrl.text = widget.initialMessage!;
    }
    _scrollCtrl.addListener(_onScroll);
  }

  void _onScroll() {
    if (!_scrollCtrl.hasClients) return;
    final atBottom = _scrollCtrl.position.maxScrollExtent - _scrollCtrl.offset < 80;
    if (atBottom != !_showScrollDown) {
      setState(() => _showScrollDown = !atBottom);
    }
  }

  /// Configure flutter_tts for Darija / French / Arabic playback.
  ///
  /// Language mapping:
  ///   ar-MA → "ar"  (Darija — nearest TTS locale; Moroccan not available natively)
  ///   ar    → "ar"  (Fusha / MSA)
  ///   fr    → "fr-FR"
  ///   *     → "fr-FR" (safe default — IAmina always speaks at least French)
  Future<void> _initTts() async {
    // Slightly slower rate — easier for medical context + dialect comprehension
    await _tts.setSpeechRate(0.85);
    await _tts.setVolume(1.0);
    await _tts.setPitch(1.0);
    // Don't let a second speak() fire before the first finishes
    await _tts.awaitSpeakCompletion(true);

    // Try to read language from profile; fall back to French
    final lang = await _resolveTtsLanguage();
    await _tts.setLanguage(lang);
  }

  /// Returns the flutter_tts locale string for the patient's preferred language.
  ///
  /// We check available TTS languages on this device and pick the best match,
  /// so we never try to set a locale the engine doesn't support.
  Future<String> _resolveTtsLanguage() async {
    // Derive language from device locale (set when the user registered the app).
    // PatientProfile preferred_language: "fr" → "fr-FR", "ar-MA" / "ar" → "ar".
    final locale    = WidgetsBinding.instance.platformDispatcher.locale.toString();
    final preferred = locale.startsWith('ar') ? 'ar' : 'fr-FR';

    // Verify the locale is actually installed on this device/browser.
    try {
      final available = await _tts.getLanguages as List<dynamic>? ?? [];
      final locales   = available.map((l) => l.toString().toLowerCase()).toList();
      final prefix    = preferred.toLowerCase().split('-').first;
      if (locales.any((l) => l.startsWith(prefix))) return preferred;
    } catch (_) {}

    return 'fr-FR'; // guaranteed fallback
  }

  /// If the LLM accidentally returned JSON in the stream, extract the reply field.
  /// Otherwise return the text unchanged.
  String _stripJsonIfNeeded(String raw) {
    if (raw.isEmpty) return 'Je n\'ai pas pu générer de réponse.';
    final trimmed = raw.trim();
    // Detect JSON leak: starts with { or ```
    if (!trimmed.startsWith('{') && !trimmed.startsWith('`')) return trimmed;
    try {
      // Strip markdown fences if present
      final jsonStr = trimmed
          .replaceAll(RegExp(r'^```json\s*', multiLine: true), '')
          .replaceAll(RegExp(r'^```\s*', multiLine: true), '')
          .trim();
      final decoded = jsonStr.isNotEmpty ? (
        jsonStr.startsWith('{')
            ? (jsonStr) // attempt parse below
            : jsonStr
      ) : jsonStr;
      // Simple regex extract of "reply" value — avoids dart:convert dependency issues
      final match = RegExp(r'"reply"\s*:\s*"((?:[^"\\]|\\.)*)"').firstMatch(decoded);
      if (match != null) return match.group(1)!.replaceAll(r'\"', '"');
    } catch (_) {}
    return trimmed;
  }

  /// Re-configure TTS language just before speaking.
  /// [replyLanguage] comes from the backend (backend knows after detect_language).
  /// "ar-MA" and "ar" → Arabic TTS locale; anything else → French.
  Future<void> _speakReply(String text, {String replyLanguage = 'fr'}) async {
    if (text.isEmpty) return;
    final lang = (replyLanguage == 'ar-MA' || replyLanguage == 'ar') ? 'ar' : 'fr-FR';
    await _tts.setLanguage(lang);
    await _tts.speak(text);
  }

  @override
  void dispose() {
    _streamSub?.cancel();
    _recorder.dispose();
    _tts.stop();
    _ctrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadHistory() async {
    final db = context.read<AppDatabase>();
    final history = await (db.select(db.chatMessages)
          ..orderBy([(t) => OrderingTerm(expression: t.createdAt, mode: OrderingMode.asc)]))
        .get();

    if (mounted) {
      setState(() {
        if (history.isEmpty) {
          _messages.add({
            'isAi':        true,
            'text':        'Bonjour 👋 Je peux analyser vos tendances, expliquer un pic glycémique, ou suggérer un ajustement. Par quoi on commence ?',
            'isEmergency': false,
          });
        } else {
          for (final msg in history) {
            _messages.add({
              'isAi':        msg.role == 'assistant',
              'text':        msg.message,
              'isEmergency': false,
            });
          }
        }
      });
      _scrollToBottom();
    }
  }

  Future<void> _send(String text) async {
    if (text.trim().isEmpty || _isTyping) return;
    final msg       = text.trim();
    final db        = context.read<AppDatabase>();
    final apiClient = context.read<ApiClient>();

    setState(() {
      _messages.add({'isAi': false, 'text': msg, 'isEmergency': false});
      // Placeholder for streaming AI reply
      _messages.add({'isAi': true, 'text': '', 'isEmergency': false});
      _ctrl.clear();
      _isTyping = true;
    });
    _scrollToBottom();

    await db.into(db.chatMessages).insert(
      ChatMessagesCompanion.insert(
        conversationId: 'default',
        role:           'user',
        message:        msg,
        createdAt:      DateTime.now(),
      ),
    );

    final aiMsgIndex = _messages.length - 1;
    final buffer = StringBuffer();

    _streamSub = apiClient.chatStream(msg).listen(
      (token) {
        if (!mounted) return;
        buffer.write(token);
        setState(() {
          _messages[aiMsgIndex] = {'isAi': true, 'text': buffer.toString(), 'isEmergency': false};
        });
        _scrollToBottom();
      },
      onDone: () async {
        if (!mounted) return;
        final raw = buffer.toString();
        // Guard: if the LLM leaked JSON despite the plain-text instruction,
        // extract the "reply" field rather than showing raw JSON.
        final reply = _stripJsonIfNeeded(raw);
        setState(() {
          _messages[aiMsgIndex] = {'isAi': true, 'text': reply, 'isEmergency': false};
          _isTyping = false;
        });
        await db.into(db.chatMessages).insert(
          ChatMessagesCompanion.insert(
            conversationId: 'default',
            role:           'assistant',
            message:        reply,
            createdAt:      DateTime.now(),
          ),
        );
      },
      onError: (error) {
        if (!mounted) return;
        final message = error is ProviderApiException
            ? error.userMessage
            : 'La demande n’a pas pu être traitée en toute sécurité.';
        setState(() {
          _messages[aiMsgIndex] = {
            'isAi': true,
            'text': message,
            'isEmergency': false,
            'retryable': error is ProviderApiException && error.retryable,
          };
          _isTyping = false;
        });
      },
      cancelOnError: true,
    );
  }

  // ── Voice ─────────────────────────────────────────────────────────────────

  // Bytes accumulator for stream-based recording (web + mobile)
  final List<Uint8List> _audioChunks = [];
  StreamSubscription<Uint8List>? _recordSub;

  Future<void> _toggleVoice() async {
    if (_isTyping || _voiceState == _VoiceState.processing) return;

    if (_voiceState == _VoiceState.recording) {
      await _stopAndSend();
    } else {
      await _startRecording();
    }
  }

  Future<void> _startRecording() async {
    // On web, hasPermission() uses enumerateDevices() which doesn't trigger
    // the browser's mic permission dialog. We attempt startStream directly
    // and catch the NotAllowedError instead.
    if (!kIsWeb) {
      final hasPermission = await _recorder.hasPermission();
      if (!hasPermission) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Accès au micro refusé. Vérifie les permissions.')),
          );
        }
        return;
      }
    }

    _audioChunks.clear();

    // Web supports Opus/WebM only — AAC is not available in browser MediaRecorder.
    // Mobile (iOS/Android) uses AAC (m4a). Both are accepted by Gemini Audio STT.
    const config = RecordConfig(
      encoder:    kIsWeb ? AudioEncoder.opus : AudioEncoder.aacLc,
      sampleRate: 16000,
      numChannels: 1,
    );

    try {
      final stream = await _recorder.startStream(config);
      _recordSub = stream.listen(
        (chunk) => _audioChunks.add(chunk),
        onError: (e) {
          if (mounted) {
            setState(() => _voiceState = _VoiceState.idle);
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text('Erreur micro : $e')),
            );
          }
        },
      );
      if (mounted) setState(() => _voiceState = _VoiceState.recording);
    } catch (e) {
      if (mounted) {
        setState(() => _voiceState = _VoiceState.idle);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(
            e.toString().contains('NotAllowed')
                ? 'Accès au micro refusé. Autorise le micro dans le navigateur.'
                : 'Impossible de démarrer l\'enregistrement : $e',
          )),
        );
      }
    }
  }

  Future<void> _stopAndSend() async {
    await _recordSub?.cancel();
    _recordSub = null;
    await _recorder.stop();

    if (!mounted) return;
    setState(() => _voiceState = _VoiceState.processing);

    // Combine all chunks into one Uint8List
    final totalLength = _audioChunks.fold<int>(0, (sum, c) => sum + c.length);
    final audioBytes  = Uint8List(totalLength);
    var offset = 0;
    for (final chunk in _audioChunks) {
      audioBytes.setRange(offset, offset + chunk.length, chunk);
      offset += chunk.length;
    }
    _audioChunks.clear();

    if (audioBytes.isEmpty) {
      if (mounted) setState(() => _voiceState = _VoiceState.idle);
      return;
    }

    // Web records WebM, mobile records AAC — both supported by Gemini Audio
    const mimeType  = kIsWeb ? 'audio/webm' : 'audio/mp4';
    final apiClient = context.read<ApiClient>();
    final db        = context.read<AppDatabase>();

    final response = await apiClient.sendVoiceMessage(audioBytes, mimeType);

    if (!mounted) return;
    setState(() => _voiceState = _VoiceState.idle);

    if (response == null) {
      setState(() {
        _messages.add({
          'isAi':        true,
          'text':        'Impossible d\'envoyer le message vocal. Réessaie.',
          'isEmergency': false,
        });
      });
      _scrollToBottom();
      return;
    }

    // User bubble — transcript prefixed with mic icon
    final userText = response.transcript.isNotEmpty
        ? '🎤 ${response.transcript}'
        : '🎤 [message vocal]';

    setState(() {
      _messages.add({'isAi': false, 'text': userText,        'isEmergency': false});
      _messages.add({'isAi': true,  'text': response.reply,  'isEmergency': response.isEmergency});
    });
    _scrollToBottom();

    // Persist to local DB
    await db.into(db.chatMessages).insert(ChatMessagesCompanion.insert(
      conversationId: 'default', role: 'user',
      message: response.transcript.isNotEmpty ? response.transcript : '[voice]',
      createdAt: DateTime.now(),
    ));
    await db.into(db.chatMessages).insert(ChatMessagesCompanion.insert(
      conversationId: 'default', role: 'assistant',
      message:   response.reply,
      createdAt: DateTime.now(),
    ));

    // TTS — IAmina reads her reply aloud (skip emergency: user needs to call SAMU)
    if (!response.isEmergency) {
      await _speakReply(response.reply, replyLanguage: response.replyLanguage);
    }
  }

  /// Build contextual suggestions based on the patient's recent logs.
  ///
  /// Rules:
  ///  - High last reading (>160)     → ask about the spike
  ///  - Low last reading (<70)        → ask about hypoglycaemia
  ///  - No recent data               → generic onboarding chips
  ///  - Data present + in range       → positive / coaching chips
  List<String> _buildSuggestions(BuildContext context) {
    // Derive from conversation history — no async needed.
    // After IAmina's first response, we can read the clinical context from its text.
    final lastAi = _messages.lastWhere((m) => m['isAi'] == true, orElse: () => {});
    final aiText = (lastAi['text'] as String? ?? '').toLowerCase();

    if (aiText.contains('hypo') || aiText.contains('glycémie basse') || aiText.contains('< 70') || aiText.contains('tbr')) {
      return ['Que faire en cas d\'hypo ?', 'Quels aliments éviter ?', 'C\'est souvent la nuit ?', 'Résumé 7 jours'];
    }
    if (aiText.contains('élevé') || aiText.contains('pic') || aiText.contains('hyperglycé') || aiText.contains('180')) {
      return ['Pourquoi ce pic ?', 'C\'est lié au repas ?', 'Éviter les hausses', 'Mon meilleur jour'];
    }
    if (aiText.contains('cible') || aiText.contains('tir') || aiText.contains('excellent') || aiText.contains('bravo')) {
      return ['Garder ce rythme ?', 'Ce qui a bien marché', 'Résumé 30 jours', 'Objectif prochain mois'];
    }
    return _fallbackSuggestions;
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollCtrl.hasClients) {
        _scrollCtrl.animateTo(
          _scrollCtrl.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AminaTheme.surface(context),
        borderRadius: const BorderRadius.vertical(top: Radius.circular(AminaTheme.radius3XL)),
      ),
      child: Column(
        children: [
          _ChatHeader(onClose: widget.onClose),
          Expanded(
            child: Stack(
              children: [
                _messages.isEmpty
                    ? const Center(child: CircularProgressIndicator(strokeWidth: 2))
                    : ListView.builder(
                        controller: _scrollCtrl,
                        padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
                        itemCount: _messages.length + (_isTyping ? 1 : 0),
                        itemBuilder: (ctx, i) {
                          if (i == _messages.length) return const _TypingBubble();
                          final m = _messages[i];
                          return _MessageBubble(
                            text:        m['text'] as String,
                            isAi:        m['isAi'] as bool,
                            isEmergency: m['isEmergency'] as bool? ?? false,
                          );
                        },
                      ),
                // Scroll-to-bottom indicator
                AnimatedPositioned(
                  duration: const Duration(milliseconds: 200),
                  curve: Curves.easeOut,
                  bottom: _showScrollDown ? 12 : -48,
                  right: 16,
                  child: AnimatedOpacity(
                    duration: const Duration(milliseconds: 200),
                    opacity: _showScrollDown ? 1.0 : 0.0,
                    child: GestureDetector(
                      onTap: _scrollToBottom,
                      child: Container(
                        width: 36, height: 36,
                        decoration: BoxDecoration(
                          color: AminaTheme.surface(context),
                          shape: BoxShape.circle,
                          border: Border.all(color: AminaTheme.divider(context)),
                          boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.08), blurRadius: 8, offset: const Offset(0, 2))],
                        ),
                        child: const Icon(Icons.keyboard_arrow_down_rounded, size: 20, color: AminaTheme.teal500),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
          // Suggested prompts (shown until first user message)
          if (!_hasUserMessage)
            _SuggestedPrompts(
              suggestions: _buildSuggestions(context),
              onTap: _send,
            ),
          _ChatInput(
            controller: _ctrl,
            isTyping:   _isTyping,
            onSend:     () => _send(_ctrl.text),
            voiceState: _voiceState,
            onVoice:    _toggleVoice,
          ),
        ],
      ),
    );
  }
}

// ── Chat Header ───────────────────────────────────────────────────────────────

class _ChatHeader extends StatelessWidget {
  final VoidCallback onClose;
  const _ChatHeader({required this.onClose});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 16, 12, 14),
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: AminaTheme.divider(context))),
      ),
      child: Row(
        children: [
          // Drag handle
          Expanded(
            child: Row(
              children: [
                Container(
                  width: 36, height: 36,
                  decoration: BoxDecoration(
                    gradient: AminaTheme.heroGradient,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Icon(Icons.auto_awesome, color: Colors.white, size: 18),
                ),
                const SizedBox(width: 10),
                const Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text('IAmina', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: AminaTheme.ink900)),
                    Text('Assistant clinique · Gemini Flash', style: TextStyle(fontSize: 11, color: AminaTheme.ink400)),
                  ],
                ),
              ],
            ),
          ),
          IconButton(
            onPressed: onClose,
            icon: const Icon(Icons.close, size: 20, color: AminaTheme.ink400),
            padding: EdgeInsets.zero,
            constraints: const BoxConstraints(minWidth: 36, minHeight: 36),
          ),
        ],
      ),
    );
  }
}

// ── Suggested Prompts ─────────────────────────────────────────────────────────

class _SuggestedPrompts extends StatelessWidget {
  final List<String> suggestions;
  final void Function(String) onTap;

  const _SuggestedPrompts({required this.suggestions, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 10, 16, 4),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          children: suggestions.map((s) => Padding(
            padding: const EdgeInsets.only(right: 8),
            child: GestureDetector(
              onTap: () => onTap(s),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
                decoration: BoxDecoration(
                  color: AminaTheme.subtleBg(context),
                  border: Border.all(color: AminaTheme.divider(context)),
                  borderRadius: BorderRadius.circular(100),
                ),
                child: Text(
                  s,
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: AminaTheme.isDark(context) ? AminaTheme.dark200 : AminaTheme.ink700),
                ),
              ),
            ),
          )).toList(),
        ),
      ),
    );
  }
}

// ── Message Bubble ────────────────────────────────────────────────────────────

class _MessageBubble extends StatelessWidget {
  final String text;
  final bool   isAi;
  final bool   isEmergency;

  const _MessageBubble({required this.text, required this.isAi, required this.isEmergency});

  // Returns true when the majority of letters are Arabic/Hebrew/Darija script.
  static bool _isRtl(String text) {
    if (text.isEmpty) return false;
    final rtl = RegExp(r'[؀-ۿݐ-ݿ֐-׿ﭐ-﷿ﹰ-﻿]');
    final rtlCount = rtl.allMatches(text).length;
    return rtlCount > text.length * 0.25;
  }

  @override
  Widget build(BuildContext context) {
    if (isEmergency) {
      return Container(
        margin: const EdgeInsets.symmetric(vertical: 6),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AminaTheme.dangerBg,
          borderRadius: BorderRadius.circular(AminaTheme.radiusXL),
          border: Border.all(color: AminaTheme.dangerFg.withValues(alpha: 0.3)),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Icon(Icons.warning_amber_rounded, color: AminaTheme.dangerFg, size: 18),
            const SizedBox(width: 10),
            Expanded(
              child: Text(text, style: const TextStyle(fontSize: 13, color: AminaTheme.dangerFg, fontWeight: FontWeight.w600, height: 1.5)),
            ),
          ],
        ),
      );
    }

    if (isAi) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 6),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // AI avatar
            Container(
              width: 28, height: 28,
              margin: const EdgeInsets.only(right: 10, top: 2),
              decoration: BoxDecoration(
                gradient: AminaTheme.heroGradient,
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.auto_awesome, color: Colors.white, size: 14),
            ),
            Flexible(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
                decoration: BoxDecoration(
                  color: AminaTheme.subtleBg(context),
                  borderRadius: const BorderRadius.only(
                    topLeft:     Radius.circular(4),
                    topRight:    Radius.circular(AminaTheme.radiusXL),
                    bottomLeft:  Radius.circular(AminaTheme.radiusXL),
                    bottomRight: Radius.circular(AminaTheme.radiusXL),
                  ),
                  border: Border.all(color: AminaTheme.divider(context)),
                ),
                child: Text(
                  text,
                  textDirection: _isRtl(text) ? TextDirection.rtl : TextDirection.ltr,
                  style: TextStyle(fontSize: 13, color: AminaTheme.isDark(context) ? AminaTheme.dark100 : AminaTheme.ink800, height: 1.55),
                ),
              ),
            ),
            const SizedBox(width: 32),
          ],
        ),
      );
    }

    // User bubble
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          const SizedBox(width: 32),
          Flexible(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
              decoration: const BoxDecoration(
                color: AminaTheme.teal500,
                borderRadius: BorderRadius.only(
                  topLeft:     Radius.circular(AminaTheme.radiusXL),
                  topRight:    Radius.circular(4),
                  bottomLeft:  Radius.circular(AminaTheme.radiusXL),
                  bottomRight: Radius.circular(AminaTheme.radiusXL),
                ),
              ),
              child: Text(
                text,
                style: const TextStyle(fontSize: 13, color: Colors.white, height: 1.5),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Typing Indicator ──────────────────────────────────────────────────────────

class _TypingBubble extends StatefulWidget {
  const _TypingBubble();

  @override
  State<_TypingBubble> createState() => _TypingBubbleState();
}

class _TypingBubbleState extends State<_TypingBubble> with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 1200))..repeat();
  }

  @override
  void dispose() { _ctrl.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 28, height: 28,
            margin: const EdgeInsets.only(right: 10, top: 2),
            decoration: BoxDecoration(
              gradient: AminaTheme.heroGradient,
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(Icons.auto_awesome, color: Colors.white, size: 14),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
            decoration: BoxDecoration(
              color: AminaTheme.subtleBg(context),
              borderRadius: const BorderRadius.only(
                topLeft:     Radius.circular(4),
                topRight:    Radius.circular(AminaTheme.radiusXL),
                bottomLeft:  Radius.circular(AminaTheme.radiusXL),
                bottomRight: Radius.circular(AminaTheme.radiusXL),
              ),
              border: Border.all(color: AminaTheme.divider(context)),
            ),
            child: AnimatedBuilder(
              animation: _ctrl,
              builder: (_, __) {
                return Row(
                  mainAxisSize: MainAxisSize.min,
                  children: List.generate(3, (i) {
                    final delay  = i / 3;
                    final phase  = ((_ctrl.value - delay) % 1.0 + 1.0) % 1.0;
                    final scale  = 0.6 + 0.4 * (phase < 0.5 ? phase * 2 : (1 - phase) * 2);
                    final opacity = 0.3 + 0.7 * scale;
                    return Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 2),
                      child: Opacity(
                        opacity: opacity,
                        child: Transform.scale(
                          scale: scale,
                          child: Container(
                            width: 7, height: 7,
                            decoration: const BoxDecoration(color: AminaTheme.teal500, shape: BoxShape.circle),
                          ),
                        ),
                      ),
                    );
                  }),
                );
              },
            ),
          ),
          // IAmina réfléchit label
          Padding(
            padding: const EdgeInsets.only(left: 8, top: 16),
            child: Text(
              'IAmina réfléchit…',
              style: TextStyle(fontSize: 11, color: AminaTheme.ink400.withValues(alpha: 0.7), fontStyle: FontStyle.italic),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Chat Input ────────────────────────────────────────────────────────────────

class _ChatInput extends StatefulWidget {
  final TextEditingController controller;
  final bool         isTyping;
  final VoidCallback onSend;
  final _VoiceState  voiceState;
  final VoidCallback onVoice;

  const _ChatInput({
    required this.controller,
    required this.isTyping,
    required this.onSend,
    required this.voiceState,
    required this.onVoice,
  });

  @override
  State<_ChatInput> createState() => _ChatInputState();
}

class _ChatInputState extends State<_ChatInput> with SingleTickerProviderStateMixin {
  late AnimationController _pulseCtrl;

  @override
  void initState() {
    super.initState();
    _pulseCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _pulseCtrl.dispose();
    super.dispose();
  }

  Widget _buildMicButton() {
    switch (widget.voiceState) {
      case _VoiceState.processing:
        return const SizedBox(
          width: 40, height: 40,
          child: Center(
            child: SizedBox(
              width: 20, height: 20,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                valueColor: AlwaysStoppedAnimation<Color>(AminaTheme.teal500),
              ),
            ),
          ),
        );

      case _VoiceState.recording:
        return AnimatedBuilder(
          animation: _pulseCtrl,
          builder: (_, __) {
            final scale = 1.0 + 0.12 * _pulseCtrl.value;
            return GestureDetector(
              onTap: widget.onVoice,
              child: Transform.scale(
                scale: scale,
                child: Container(
                  width: 40, height: 40,
                  decoration: BoxDecoration(
                    color: const Color(0xFFEF4444),
                    borderRadius: BorderRadius.circular(12),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFFEF4444).withValues(alpha: 0.35 + 0.25 * _pulseCtrl.value),
                        blurRadius: 10,
                        spreadRadius: 2,
                      ),
                    ],
                  ),
                  child: const Icon(Icons.stop_rounded, color: Colors.white, size: 20),
                ),
              ),
            );
          },
        );

      case _VoiceState.idle:
        return GestureDetector(
          onTap: widget.onVoice,
          child: Container(
            width: 40, height: 40,
            decoration: BoxDecoration(
              color: AminaTheme.subtleBg(context),
              border: Border.all(color: AminaTheme.divider(context)),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(Icons.mic_rounded, color: AminaTheme.teal500, size: 20),
          ),
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    final bottom = MediaQuery.of(context).viewInsets.bottom;

    return Container(
      padding: EdgeInsets.fromLTRB(16, 10, 12, 10 + bottom),
      decoration: BoxDecoration(
        color: AminaTheme.surface(context),
        border: Border(top: BorderSide(color: AminaTheme.divider(context))),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          // Mic button (idle → teal border, recording → pulsing red, processing → spinner)
          _buildMicButton(),
          const SizedBox(width: 8),
          Expanded(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxHeight: 120),
              child: TextField(
                controller: widget.controller,
                maxLines: null,
                textInputAction: TextInputAction.send,
                onSubmitted: (_) => widget.onSend(),
                style: TextStyle(fontSize: 14, color: AminaTheme.isDark(context) ? AminaTheme.dark100 : AminaTheme.ink900),
                decoration: InputDecoration(
                  hintText: 'Posez une question à IAmina…',
                  hintStyle: TextStyle(fontSize: 13, color: AminaTheme.textSecondary(context)),
                  filled: true,
                  fillColor: AminaTheme.subtleBg(context),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(AminaTheme.radiusXL),
                    borderSide: BorderSide(color: AminaTheme.divider(context)),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(AminaTheme.radiusXL),
                    borderSide: BorderSide(color: AminaTheme.divider(context)),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(AminaTheme.radiusXL),
                    borderSide: const BorderSide(color: AminaTheme.teal500),
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(width: 8),
          // Send button
          AnimatedOpacity(
            opacity: widget.isTyping ? 0.5 : 1.0,
            duration: const Duration(milliseconds: 150),
            child: GestureDetector(
              onTap: widget.isTyping ? null : widget.onSend,
              child: Container(
                width: 40, height: 40,
                decoration: BoxDecoration(
                  gradient: AminaTheme.heroGradient,
                  borderRadius: BorderRadius.circular(12),
                  boxShadow: widget.isTyping ? null : AminaTheme.shadowPrimary,
                ),
                child: widget.isTyping
                    ? const Center(child: SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)))
                    : const Icon(Icons.send_rounded, color: Colors.white, size: 18),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
