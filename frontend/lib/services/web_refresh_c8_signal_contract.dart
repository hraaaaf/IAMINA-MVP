/// W02-C8 test-only browser revocation bus. No token, owner or family ID.
abstract class WebRefreshC8SignalBus {
  void listen(void Function() onRevoke);
  void broadcastRevocation();
  void dispose();
}
