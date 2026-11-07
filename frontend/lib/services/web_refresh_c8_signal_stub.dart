import 'web_refresh_c8_signal_contract.dart';

/// VM/mobile: no cross-tab signal. Candidate is not wired to live AuthService.
class WebRefreshC8NoopBus implements WebRefreshC8SignalBus {
  @override
  void listen(void Function() onRevoke) {}

  @override
  void broadcastRevocation() {}

  @override
  void dispose() {}
}

WebRefreshC8SignalBus createC8SignalBus() => WebRefreshC8NoopBus();
