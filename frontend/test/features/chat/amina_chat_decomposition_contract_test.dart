import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('IAmina chat keeps API DB voice orchestration out of presentation part', () {
    final state = File(
      'lib/features/journal/widgets/amina_chat_view.dart',
    ).readAsStringSync();
    final presentation = File(
      'lib/features/journal/widgets/amina_chat_view_presentation.dart',
    ).readAsStringSync();

    expect(state, contains("part 'amina_chat_view_presentation.dart';"));
    expect(state, contains('class _AminaChatViewState'));
    expect(state, contains('context.read<ApiClient>()'));
    expect(state, contains('context.read<AppDatabase>()'));
    expect(state, contains('chatStream(msg)'));
    expect(state, contains('sendVoiceMessage(audioBytes, mimeType)'));
    expect(state, contains('AudioRecorder'));
    expect(state, contains('FlutterTts'));
    expect(state, isNot(contains('class _ChatHeader')));
    expect(state, isNot(contains('class _MessageBubble')));
    expect(state, isNot(contains('class _ChatInput')));

    expect(
      presentation,
      contains('extension _AminaChatViewPresentation on _AminaChatViewState'),
    );
    expect(presentation, contains('Widget _buildPresentation('));
    expect(presentation, contains('class _ChatHeader'));
    expect(presentation, contains('class _SuggestedPrompts'));
    expect(presentation, contains('class _MessageBubble'));
    expect(presentation, contains('class _TypingBubble'));
    expect(presentation, contains('class _ChatInput'));
    expect(presentation, isNot(contains('context.read<ApiClient>()')));
    expect(presentation, isNot(contains('context.read<AppDatabase>()')));
    expect(presentation, isNot(contains('chatStream(')));
    expect(presentation, isNot(contains('sendVoiceMessage(')));
    expect(presentation, isNot(contains('AudioRecorder')));
    expect(presentation, isNot(contains('FlutterTts')));
    expect(presentation, isNot(contains("import 'package:")));
  });
}
