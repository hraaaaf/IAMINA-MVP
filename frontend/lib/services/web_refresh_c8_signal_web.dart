// Web-only same-origin revocation. No credentials or identifiers transmitted.
// ignore_for_file: avoid_web_libraries_in_flutter
import 'dart:async';
import 'dart:html' as html;

import 'web_refresh_c8_signal_contract.dart';

const _name = 'iamina-w02-c8-revoke-testonly-v1';
const _message = 'revoke-local-web-memory-v1';

class WebRefreshC8ChromeBus implements WebRefreshC8SignalBus {
  final html.BroadcastChannel _channel = html.BroadcastChannel(_name);
  StreamSubscription<html.MessageEvent>? _sub;

  @override
  void listen(void Function() onRevoke) {
    _sub ??= _channel.onMessage.listen((event) {
      if (event.data == _message) {
        onRevoke();
      }
    });
  }

  @override
  void broadcastRevocation() {
    _channel.postMessage(_message);
  }

  @override
  void dispose() {
    _sub?.cancel();
    _channel.close();
  }
}

WebRefreshC8SignalBus createC8SignalBus() => WebRefreshC8ChromeBus();
