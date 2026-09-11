import 'package:flutter/material.dart';

import '../../core/theme/amina_visual_language.dart';
import '../../core/theme/app_theme.dart';
import '../../services/companion_service.dart';

String _chatText(BuildContext context, String fr, String en, String ar) {
  final code = Localizations.localeOf(context).languageCode;
  if (code == 'ar') return ar;
  if (code == 'en') return en;
  return fr;
}

class CompanionConversationScreen extends StatefulWidget {
  final CompanionService? service;

  const CompanionConversationScreen({super.key, this.service});

  @override
  State<CompanionConversationScreen> createState() =>
      _CompanionConversationScreenState();
}

class _CompanionConversationScreenState
    extends State<CompanionConversationScreen> {
  late final CompanionService _service = widget.service ?? CompanionService();
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<_ConversationMessage> _messages = [];
  bool _sending = false;
  bool _failed = false;

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    if (widget.service == null) _service.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.isEmpty || _sending) return;

    setState(() {
      _messages.add(_ConversationMessage.user(text));
      _sending = true;
      _failed = false;
      _controller.clear();
    });
    _scrollToBottom();

    final result = await _service.sendChatMessage(text);
    if (!mounted) return;

    setState(() {
      _sending = false;
      if (result == null) {
        _failed = true;
      } else {
        _messages.add(_ConversationMessage.assistant(result.reply));
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
                          itemCount: _messages.length + (_sending ? 1 : 0),
                          separatorBuilder: (_, __) =>
                              const SizedBox(height: 12),
                          itemBuilder: (context, index) {
                            if (_sending && index == _messages.length) {
                              return const _TypingBubble();
                            }
                            return _MessageBubble(message: _messages[index]);
                          },
                        ),
                ),
                if (_failed)
                  Padding(
                    padding: const EdgeInsetsDirectional.fromSTEB(24, 0, 24, 8),
                    child: Text(
                      _chatText(
                        context,
                        'La réponse n’a pas pu être chargée. Réessaie sans modifier ton message.',
                        'The reply could not be loaded. Try again without changing your message.',
                        'تعذر تحميل الرد. حاول مجددًا بدون تغيير رسالتك.',
                      ),
                      style: const TextStyle(
                        color: Color(0xFF9B3C35),
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                _Composer(
                  controller: _controller,
                  sending: _sending,
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
          IconButton(
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
  final Future<void> Function() onSend;

  const _Composer({
    required this.controller,
    required this.sending,
    required this.onSend,
  });

  @override
  Widget build(BuildContext context) {
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
          Expanded(
            child: TextField(
              key: const Key('companion-chat-input'),
              controller: controller,
              enabled: !sending,
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
          IconButton.filled(
            key: const Key('companion-chat-send'),
            onPressed: sending ? null : onSend,
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
        ],
      ),
    );
  }
}

class _MessageBubble extends StatelessWidget {
  final _ConversationMessage message;

  const _MessageBubble({required this.message});

  @override
  Widget build(BuildContext context) {
    final isUser = message.role == _ConversationRole.user;
    final desktop = MediaQuery.sizeOf(context).width >= 900;
    return Align(
      alignment: isUser
          ? AlignmentDirectional.centerEnd
          : AlignmentDirectional.centerStart,
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: desktop ? 520 : 310),
        child: Container(
          key: Key(
            isUser ? 'companion-user-bubble' : 'companion-assistant-bubble',
          ),
          padding: const EdgeInsetsDirectional.fromSTEB(15, 12, 15, 12),
          decoration: BoxDecoration(
            color: isUser
                ? AminaVisualLanguage.forestDeep
                : AminaVisualLanguage.controlSurface(context),
            borderRadius: BorderRadiusDirectional.only(
              topStart: const Radius.circular(19),
              topEnd: const Radius.circular(19),
              bottomStart: Radius.circular(isUser ? 19 : 6),
              bottomEnd: Radius.circular(isUser ? 6 : 19),
            ),
            border: isUser
                ? null
                : Border.all(color: AminaVisualLanguage.controlBorder(context)),
            boxShadow: isUser ? null : AminaVisualLanguage.cardShadowLight,
          ),
          child: Text(
            message.text,
            style: TextStyle(
              height: 1.42,
              fontSize: 14,
              color: isUser
                  ? Colors.white
                  : AminaVisualLanguage.primaryText(context),
            ),
          ),
        ),
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

  const _ConversationMessage._(this.role, this.text);

  factory _ConversationMessage.user(String text) =>
      _ConversationMessage._(_ConversationRole.user, text);

  factory _ConversationMessage.assistant(String text) =>
      _ConversationMessage._(_ConversationRole.assistant, text);
}
