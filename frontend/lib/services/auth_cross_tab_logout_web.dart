// Same-origin, cross-JS-isolate logout signal. No identity or bearer bytes
// ever transit the channel. A browser-storage failure must not suppress this.
// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;

const _logoutChannelName = 'iamina-auth-logout-v1';
const _logoutMessage = 'revoke-all-v1';
html.BroadcastChannel? _channel;

void registerCrossTabLogout(void Function() onLogout) {
  if (_channel != null) return;
  final channel = html.BroadcastChannel(_logoutChannelName);
  channel.onMessage.listen((event) {
    if (event.data == _logoutMessage) {
      onLogout();
    }
  });
  _channel = channel;
}

void publishCrossTabLogout() {
  _channel?.postMessage(_logoutMessage);
}
