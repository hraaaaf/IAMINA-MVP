part of 'amina_chat_view.dart';

extension _AminaChatViewPresentation on _AminaChatViewState {
  bool get _hasUserMessage => _messages.any((m) => m['isAi'] == false);

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

  Widget _buildPresentation(BuildContext context) {
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

