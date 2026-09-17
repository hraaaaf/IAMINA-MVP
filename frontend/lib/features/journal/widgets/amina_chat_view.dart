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

part 'amina_chat_view_presentation.dart';

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
  Widget build(BuildContext context) => _buildPresentation(context);
}
