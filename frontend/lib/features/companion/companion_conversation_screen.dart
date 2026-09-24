import 'dart:async';
import 'dart:typed_data';

import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:record/record.dart';
import 'package:provider/provider.dart';

import '../../core/theme/amina_visual_language.dart';
import '../../core/theme/app_theme.dart';
import '../../services/api_client.dart';
import '../../services/companion_service.dart';
import '../../services/auth_service.dart';

String _chatText(BuildContext context, String fr, String en, String ar) {
  final code = Localizations.localeOf(context).languageCode;
  if (code == 'ar') return ar;
  if (code == 'en') return en;
  return fr;
}

String _failureText(BuildContext context, ProviderApiException failure) {
  return switch (failure.code) {
    'provider_timeout' => _chatText(
      context,
      'IAmina met trop de temps à répondre. Réessaie dans un instant.',
      'IAmina is taking too long to respond. Try again in a moment.',
      'تستغرق IAmina وقتًا أطول من المعتاد للرد. حاول مجددًا بعد لحظة.',
    ),
    'provider_unavailable' => _chatText(
      context,
      'Le service IAmina est temporairement indisponible. Réessaie dans un instant.',
      'IAmina is temporarily unavailable. Try again in a moment.',
      'خدمة IAmina غير متاحة مؤقتًا. حاول مجددًا بعد لحظة.',
    ),
    'provider_quota_exceeded' => _chatText(
      context,
      'IAmina a atteint sa limite temporaire. Réessaie plus tard.',
      'IAmina has reached its temporary limit. Try again later.',
      'بلغت IAmina الحد المؤقت للخدمة. حاول مجددًا لاحقًا.',
    ),
    'authentication_required' => _chatText(
      context,
      'Votre session n’est plus valide. Reconnectez-vous avant de réessayer.',
      'Your session is no longer valid. Sign in again before retrying.',
      'لم تعد جلستك صالحة. سجّل الدخول مجددًا قبل المحاولة.',
    ),
    _ => _chatText(
      context,
      'La réponse n’a pas pu être chargée. Réessaie sans modifier ton message.',
      'The reply could not be loaded. Try again without changing your message.',
      'تعذر تحميل الرد. حاول مجددًا بدون تغيير رسالتك.',
    ),
  };
}

enum _VoiceState { idle, recording, processing }

class CompanionConversationScreen extends StatefulWidget {
  final CompanionService? service;

  const CompanionConversationScreen({super.key, this.service});

  @override
  State<CompanionConversationScreen> createState() =>
      _CompanionConversationScreenState();
}

class _CompanionConversationScreenState
    extends State<CompanionConversationScreen>
    with SingleTickerProviderStateMixin {
  late CompanionService _service;
  bool _serviceInitialized = false;
  bool _ownsService = false;
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<_ConversationMessage> _messages = [];
  bool _sending = false;
  ProviderApiException? _failure;

  final AudioRecorder _recorder = AudioRecorder();
  final FlutterTts _tts = FlutterTts();
  final List<Uint8List> _audioChunks = <Uint8List>[];
  StreamSubscription<Uint8List>? _recordSubscription;
  late final AnimationController _voicePulseController;
  _VoiceState _voiceState = _VoiceState.idle;

  @override
  void initState() {
    super.initState();
    _voicePulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );
    unawaited(_initializeTts());
  }


  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_serviceInitialized) return;
    final injected = widget.service;
    if (injected != null) {
      _service = injected;
    } else {
      _service = CompanionService(
        authService: context.read<AuthService>(),
        demoLanguage: Localizations.localeOf(context).languageCode,
      );
      _ownsService = true;
    }
    _serviceInitialized = true;
  }

  @override
  void dispose() {
    unawaited(_recordSubscription?.cancel() ?? Future<void>.value());
    unawaited(_recorder.dispose());
    unawaited(_tts.stop().then<void>((_) {}));
    _voicePulseController.dispose();
    _controller.dispose();
    _scrollController.dispose();
    if (_ownsService) _service.dispose();
    super.dispose();
  }

  Future<void> _initializeTts() async {
    try {
      await _tts.setSpeechRate(0.85);
      await _tts.setVolume(1.0);
      await _tts.setPitch(1.0);
      await _tts.awaitSpeakCompletion(true);
    } catch (_) {
      // TTS is an optional local playback enhancement. Voice input stays usable.
    }
  }

  Future<void> _speakVoiceReply(
    String text, {
    required String replyLanguage,
  }) async {
    if (text.trim().isEmpty) return;
    try {
      final language = replyLanguage == 'ar-MA' || replyLanguage == 'ar'
          ? 'ar'
          : replyLanguage == 'en'
          ? 'en-US'
          : 'fr-FR';
      await _tts.setLanguage(language);
      await _tts.speak(text);
    } catch (_) {
      // A missing local TTS engine must not fail the governed chat response.
    }
  }

  Future<void> _toggleVoice() async {
    if (_sending || _voiceState == _VoiceState.processing) return;
    if (_voiceState == _VoiceState.recording) {
      await _stopAndSendVoice();
      return;
    }
    await _startVoiceRecording();
  }

  Future<void> _startVoiceRecording() async {
    if (!kIsWeb) {
      final granted = await _recorder.hasPermission();
      if (!granted) {
        if (mounted) {
          _showVoiceMessage(
            _chatText(
              context,
              'Accès au micro refusé. Vérifie les permissions.',
              'Microphone access was denied. Check your permissions.',
              'تم رفض الوصول إلى الميكروفون. تحقّق من الأذونات.',
            ),
          );
        }
        return;
      }
    }

    _audioChunks.clear();
    const config = RecordConfig(
      encoder: kIsWeb ? AudioEncoder.opus : AudioEncoder.aacLc,
      sampleRate: 16000,
      numChannels: 1,
    );

    try {
      final stream = await _recorder.startStream(config);
      await _recordSubscription?.cancel();
      _recordSubscription = stream.listen(
        _audioChunks.add,
        onError: (_) {
          if (!mounted) return;
          _voicePulseController
            ..stop()
            ..reset();
          setState(() => _voiceState = _VoiceState.idle);
          _showVoiceMessage(
            _chatText(
              context,
              'Le micro a rencontré une erreur. Réessaie.',
              'The microphone encountered an error. Try again.',
              'حدث خطأ في الميكروفون. حاول مجددًا.',
            ),
          );
        },
      );
      if (mounted) {
        setState(() {
          _failure = null;
          _voiceState = _VoiceState.recording;
        });
        _voicePulseController.repeat(reverse: true);
      }
    } catch (_) {
      if (!mounted) return;
      _voicePulseController
        ..stop()
        ..reset();
      setState(() => _voiceState = _VoiceState.idle);
      _showVoiceMessage(
        _chatText(
          context,
          'Impossible de démarrer le micro. Vérifie les permissions.',
          'Unable to start the microphone. Check your permissions.',
          'تعذر تشغيل الميكروفون. تحقّق من الأذونات.',
        ),
      );
    }
  }

  Future<void> _stopAndSendVoice() async {
    await _recordSubscription?.cancel();
    _recordSubscription = null;
    await _recorder.stop();

    if (!mounted) return;
    _voicePulseController
      ..stop()
      ..reset();
    setState(() {
      _voiceState = _VoiceState.processing;
      _failure = null;
    });

    final totalLength = _audioChunks.fold<int>(
      0,
      (total, chunk) => total + chunk.length,
    );
    final audioBytes = Uint8List(totalLength);
    var offset = 0;
    for (final chunk in _audioChunks) {
      audioBytes.setRange(offset, offset + chunk.length, chunk);
      offset += chunk.length;
    }
    _audioChunks.clear();

    if (audioBytes.isEmpty) {
      if (mounted) {
        setState(() => _voiceState = _VoiceState.idle);
        _showVoiceMessage(
          _chatText(
            context,
            'Aucun son détecté. Réessaie.',
            'No audio was detected. Try again.',
            'لم يتم اكتشاف صوت. حاول مجددًا.',
          ),
        );
      }
      return;
    }

    try {
      final result = await _service.sendVoiceMessage(
        audioBytes,
        kIsWeb ? 'audio/webm' : 'audio/mp4',
      );
      if (!mounted) return;

      setState(() {
        _voiceState = _VoiceState.idle;
        if (result == null) {
          _failure = const ProviderApiException(
            code: 'provider_unknown_failure',
            message: 'The AI request could not be completed safely.',
            retryable: false,
            statusCode: 500,
          );
          return;
        }
        if (result.transcript.trim().isNotEmpty) {
          _messages.add(
            _ConversationMessage.user('🎤 ${result.transcript.trim()}'),
          );
        }
        _messages.add(
          _ConversationMessage.assistant(
            result.reply,
            isEmergency: result.isEmergency,
          ),
        );
      });
      _scrollToBottom();

      if (result != null && !result.isEmergency) {
        unawaited(
          _speakVoiceReply(
            result.reply,
            replyLanguage: result.replyLanguage,
          ),
        );
      }
    } on ProviderApiException catch (error) {
      if (!mounted) return;
      setState(() {
        _voiceState = _VoiceState.idle;
        _failure = error;
      });
    }
  }

  void _showVoiceMessage(String message) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message)));
  }

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.isEmpty || _sending) return;

    setState(() {
      _messages.add(_ConversationMessage.user(text));
      _sending = true;
      _failure = null;
      _controller.clear();
    });
    _scrollToBottom();

    CompanionChatReply? result;
    ProviderApiException? failure;
    try {
      result = await _service.sendChatMessage(text);
    } on ProviderApiException catch (error) {
      failure = error;
    }
    if (!mounted) return;

    setState(() {
      _sending = false;
      if (failure != null) {
        _failure = failure;
      } else if (result == null) {
        _failure = const ProviderApiException(
          code: 'provider_unknown_failure',
          message: 'The AI request could not be completed safely.',
          retryable: false,
          statusCode: 500,
        );
      } else {
        _messages.add(
          _ConversationMessage.assistant(
            result.reply,
            isEmergency: result.isEmergency,
          ),
        );
      }
    });
    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) return;
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 220),
        curve: Curves.easeOut,
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    final dark = AminaTheme.isDark(context);
    return Scaffold(
      backgroundColor: dark ? AminaTheme.bg(context) : const Color(0xFFF4FBF9),
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            final desktop = constraints.maxWidth >= 900;
            final waitingForReply =
                _sending || _voiceState == _VoiceState.processing;
            final conversation = Column(
              children: [
                _ConversationHeader(
                  onClose: () => Navigator.of(context).maybePop(),
                ),
                Expanded(
                  child: _messages.isEmpty
                      ? const _EmptyConversation()
                      : ListView.separated(
                          key: const Key('companion-chat-message-list'),
                          controller: _scrollController,
                          padding: const EdgeInsetsDirectional.fromSTEB(
                            24,
                            22,
                            24,
                            24,
                          ),
                          itemCount: _messages.length + (waitingForReply ? 1 : 0),
                          separatorBuilder: (_, __) =>
                              const SizedBox(height: 12),
                          itemBuilder: (context, index) {
                            if (waitingForReply && index == _messages.length) {
                              return const _TypingBubble();
                            }
                            return _MessageBubble(message: _messages[index]);
                          },
                        ),
                ),
                if (_failure != null)
                  Padding(
                    padding: const EdgeInsetsDirectional.fromSTEB(24, 0, 24, 8),
                    child: Semantics(
                      liveRegion: true,
                      label: _failureText(context, _failure!),
                      child: ExcludeSemantics(
                        child: Text(
                          _failureText(context, _failure!),
                          key: const Key('companion-chat-failure'),
                          style: const TextStyle(
                            color: Color(0xFF9B3C35),
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ),
                  ),
                _Composer(
                  controller: _controller,
                  sending: _sending,
                  voiceState: _voiceState,
                  voicePulse: _voicePulseController,
                  onVoice: _toggleVoice,
                  onSend: _send,
                ),
              ],
            );

            if (!desktop) {
              return Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 960),
                  child: conversation,
                ),
              );
            }

            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 960),
                  child: SizedBox(
                    height: constraints.maxHeight > 48
                        ? constraints.maxHeight - 48
                        : constraints.maxHeight,
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(24),
                      child: DecoratedBox(
                        decoration: BoxDecoration(
                          color: AminaVisualLanguage.controlSurface(context),
                          border: Border.all(
                            color: AminaVisualLanguage.controlBorder(context),
                          ),
                          boxShadow: AminaVisualLanguage.cardShadowLight,
                        ),
                        child: conversation,
                      ),
                    ),
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}

class _ConversationHeader extends StatelessWidget {
  final VoidCallback onClose;

  const _ConversationHeader({required this.onClose});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsetsDirectional.fromSTEB(18, 12, 12, 12),
      decoration: BoxDecoration(
        color: AminaVisualLanguage.controlSurface(
          context,
        ).withValues(alpha: .94),
        border: Border(
          bottom: BorderSide(color: AminaVisualLanguage.controlBorder(context)),
        ),
      ),
      child: Row(
        children: [
          Container(
            width: 46,
            height: 46,
            padding: const EdgeInsets.all(5),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: .9),
              borderRadius: BorderRadius.circular(15),
              boxShadow: AminaVisualLanguage.cardShadowLight,
            ),
            child: Image.asset(
              'assets/images/logo_amina.png',
              fit: BoxFit.contain,
            ),
          ),
          const SizedBox(width: 11),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'IAmina',
                  style: TextStyle(
                    color: AminaVisualLanguage.primaryText(context),
                    fontSize: 18,
                    fontWeight: FontWeight.w800,
                    letterSpacing: -.35,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  _chatText(
                    context,
                    'Conversation gouvernée',
                    'Governed conversation',
                    'محادثة محكومة',
                  ),
                  style: TextStyle(
                    color: AminaVisualLanguage.secondary(context),
                    fontSize: 11.5,
                  ),
                ),
              ],
            ),
          ),
          Semantics(
            label: _chatText(
              context,
              'Fermer la conversation',
              'Close conversation',
              'إغلاق المحادثة',
            ),
            button: true,
            excludeSemantics: true,
            child: IconButton(
              key: const Key('companion-chat-close'),
              onPressed: onClose,
              icon: const Icon(Icons.close_rounded),
              style: IconButton.styleFrom(
                minimumSize: const Size(44, 44),
                backgroundColor: AminaVisualLanguage.controlSurface(context),
                foregroundColor: AminaVisualLanguage.forestDeep,
                side: BorderSide(
                  color: AminaVisualLanguage.controlBorder(context),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _EmptyConversation extends StatelessWidget {
  const _EmptyConversation();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(26),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 620),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 68,
                height: 68,
                decoration: AminaVisualLanguage.mintIconDecoration(context),
                child: const Icon(
                  Icons.forum_outlined,
                  color: AminaVisualLanguage.actionGreen,
                  size: 30,
                ),
              ),
              const SizedBox(height: 18),
              Text(
                _chatText(
                  context,
                  'Parler avec IAmina',
                  'Talk with IAmina',
                  'تحدث مع IAmina',
                ),
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
                _chatText(
                  context,
                  'Pose une question avec tes mots. IAmina peut organiser et reformuler, mais ne remplace pas ton professionnel de santé.',
                  'Ask in your own words. IAmina can organize and rephrase, but does not replace your clinician.',
                  'اكتب سؤالك بطريقتك. يمكن لـ IAmina التنظيم وإعادة الصياغة، لكنها لا تستبدل طبيبك.',
                ),
                textAlign: TextAlign.center,
                style: TextStyle(
                  height: 1.45,
                  fontSize: 13,
                  color: AminaVisualLanguage.secondary(context),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Composer extends StatelessWidget {
  final TextEditingController controller;
  final bool sending;
  final _VoiceState voiceState;
  final Animation<double> voicePulse;
  final Future<void> Function() onVoice;
  final Future<void> Function() onSend;

  const _Composer({
    required this.controller,
    required this.sending,
    required this.voiceState,
    required this.voicePulse,
    required this.onVoice,
    required this.onSend,
  });

  @override
  Widget build(BuildContext context) {
    final voiceBusy = voiceState != _VoiceState.idle;
    return Container(
      padding: const EdgeInsetsDirectional.fromSTEB(14, 10, 12, 14),
      decoration: BoxDecoration(
        color: AminaVisualLanguage.controlSurface(
          context,
        ).withValues(alpha: .96),
        border: Border(
          top: BorderSide(color: AminaVisualLanguage.controlBorder(context)),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          _VoiceButton(
            state: voiceState,
            pulse: voicePulse,
            disabled: sending,
            onPressed: onVoice,
          ),
          const SizedBox(width: 9),
          Expanded(
            child: TextField(
              key: const Key('companion-chat-input'),
              controller: controller,
              enabled: !sending && !voiceBusy,
              minLines: 1,
              maxLines: 4,
              textInputAction: TextInputAction.send,
              onSubmitted: (_) => onSend(),
              decoration: InputDecoration(
                hintText: _chatText(
                  context,
                  'Écrire à IAmina…',
                  'Write to IAmina…',
                  'اكتب إلى IAmina…',
                ),
                filled: true,
                fillColor: AminaVisualLanguage.controlSurface(context),
                contentPadding: const EdgeInsetsDirectional.fromSTEB(
                  15,
                  13,
                  15,
                  13,
                ),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(18),
                  borderSide: BorderSide(
                    color: AminaVisualLanguage.controlBorder(context),
                  ),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(18),
                  borderSide: BorderSide(
                    color: AminaVisualLanguage.controlBorder(context),
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(width: 9),
          Semantics(
            label: _chatText(
              context,
              'Envoyer le message',
              'Send message',
              'إرسال الرسالة',
            ),
            button: true,
            excludeSemantics: true,
            child: IconButton.filled(
              key: const Key('companion-chat-send'),
              onPressed: sending || voiceBusy ? null : onSend,
              icon: sending
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.arrow_upward_rounded),
              style: IconButton.styleFrom(
                minimumSize: const Size(48, 48),
                backgroundColor: AminaVisualLanguage.actionGreen,
                foregroundColor: Colors.white,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _VoiceButton extends StatelessWidget {
  final _VoiceState state;
  final Animation<double> pulse;
  final bool disabled;
  final Future<void> Function() onPressed;

  const _VoiceButton({
    required this.state,
    required this.pulse,
    required this.disabled,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    final label = switch (state) {
      _VoiceState.idle => _chatText(
        context,
        'Envoyer un message vocal',
        'Send a voice message',
        'إرسال رسالة صوتية',
      ),
      _VoiceState.recording => _chatText(
        context,
        'Arrêter l’enregistrement',
        'Stop recording',
        'إيقاف التسجيل',
      ),
      _VoiceState.processing => _chatText(
        context,
        'Traitement du message vocal',
        'Processing voice message',
        'جارٍ معالجة الرسالة الصوتية',
      ),
    };

    Widget child;
    switch (state) {
      case _VoiceState.processing:
        child = SizedBox(
          width: 48,
          height: 48,
          child: Center(
            child: SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                color: AminaVisualLanguage.actionGreen,
              ),
            ),
          ),
        );
        break;
      case _VoiceState.recording:
        child = AnimatedBuilder(
          animation: pulse,
          builder: (context, _) => Transform.scale(
            scale: 1 + (0.08 * pulse.value),
            child: IconButton.filled(
              key: const Key('companion-chat-voice-stop'),
              onPressed: disabled ? null : onPressed,
              icon: const Icon(Icons.stop_rounded),
              style: IconButton.styleFrom(
                minimumSize: const Size(48, 48),
                backgroundColor: const Color(0xFFC94B45),
                foregroundColor: Colors.white,
              ),
            ),
          ),
        );
        break;
      case _VoiceState.idle:
        child = IconButton(
          key: const Key('companion-chat-voice'),
          onPressed: disabled ? null : onPressed,
          icon: const Icon(Icons.mic_rounded),
          style: IconButton.styleFrom(
            minimumSize: const Size(48, 48),
            backgroundColor: AminaVisualLanguage.controlSurface(context),
            foregroundColor: AminaVisualLanguage.actionGreen,
            side: BorderSide(
              color: AminaVisualLanguage.controlBorder(context),
            ),
          ),
        );
        break;
    }

    return Semantics(
      label: label,
      button: true,
      enabled: state != _VoiceState.processing && !disabled,
      excludeSemantics: true,
      child: child,
    );
  }
}

class _MessageBubble extends StatelessWidget {
  final _ConversationMessage message;

  const _MessageBubble({required this.message});

  @override
  Widget build(BuildContext context) {
    final isUser = message.role == _ConversationRole.user;
    final emergency = message.isEmergency;
    final desktop = MediaQuery.sizeOf(context).width >= 900;

    final bubble = Container(
      key: Key(
        emergency
            ? 'companion-emergency-bubble'
            : isUser
            ? 'companion-user-bubble'
            : 'companion-assistant-bubble',
      ),
      padding: const EdgeInsetsDirectional.fromSTEB(15, 12, 15, 12),
      decoration: BoxDecoration(
        color: emergency
            ? const Color(0xFFFFF0ED)
            : isUser
            ? AminaVisualLanguage.forestDeep
            : AminaVisualLanguage.controlSurface(context),
        borderRadius: BorderRadiusDirectional.only(
          topStart: const Radius.circular(19),
          topEnd: const Radius.circular(19),
          bottomStart: Radius.circular(isUser ? 19 : 6),
          bottomEnd: Radius.circular(isUser ? 6 : 19),
        ),
        border: emergency
            ? Border.all(color: const Color(0xFFC94B45), width: 1.5)
            : isUser
            ? null
            : Border.all(color: AminaVisualLanguage.controlBorder(context)),
        boxShadow: isUser ? null : AminaVisualLanguage.cardShadowLight,
      ),
      child: Text(
        message.text,
        style: TextStyle(
          height: 1.42,
          fontSize: 14,
          fontWeight: emergency ? FontWeight.w700 : FontWeight.w400,
          color: emergency
              ? const Color(0xFF8B2E28)
              : isUser
              ? Colors.white
              : AminaVisualLanguage.primaryText(context),
        ),
      ),
    );

    return Align(
      alignment: isUser
          ? AlignmentDirectional.centerEnd
          : AlignmentDirectional.centerStart,
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: desktop ? 520 : 310),
        child: emergency
            ? Semantics(
                liveRegion: true,
                label: _chatText(
                  context,
                  'Alerte urgente IAmina. ${message.text}',
                  'Urgent IAmina alert. ${message.text}',
                  'تنبيه عاجل من IAmina. ${message.text}',
                ),
                child: ExcludeSemantics(child: bubble),
              )
            : bubble,
      ),
    );
  }
}

class _TypingBubble extends StatelessWidget {
  const _TypingBubble();

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: AlignmentDirectional.centerStart,
      child: Container(
        key: const Key('companion-typing-bubble'),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 13),
        decoration: BoxDecoration(
          color: AminaVisualLanguage.controlSurface(context),
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: AminaVisualLanguage.controlBorder(context)),
        ),
        child: const SizedBox(
          width: 42,
          child: LinearProgressIndicator(minHeight: 3),
        ),
      ),
    );
  }
}

enum _ConversationRole { user, assistant }

class _ConversationMessage {
  final _ConversationRole role;
  final String text;
  final bool isEmergency;

  const _ConversationMessage._(
    this.role,
    this.text, {
    this.isEmergency = false,
  });

  factory _ConversationMessage.user(String text) =>
      _ConversationMessage._(_ConversationRole.user, text);

  factory _ConversationMessage.assistant(
    String text, {
    bool isEmergency = false,
  }) => _ConversationMessage._(
    _ConversationRole.assistant,
    text,
    isEmergency: isEmergency,
  );
}
