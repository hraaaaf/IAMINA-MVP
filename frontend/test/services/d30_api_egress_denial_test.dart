import 'package:amina/services/api_client.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('D30 default local-only clinical transports reject synthetic writes', () async {
    // If any method reaches the network this invalid hostname will fail; the
    // explicit assertions below must pass before even trying a transport.
    final api = ApiClient(baseUrl: 'https://d30-never-contact.invalid');
    expect(api.canSyncClinicalData, isFalse);
    expect(
      await api.syncLogEntry({'client_uuid': 'd30-synthetic', 'blood_sugar': 112}),
      isFalse,
    );
    expect(
      await api.batchSyncLogs([
        {'client_uuid': 'd30-synthetic', 'blood_sugar': 112}
      ]),
      isEmpty,
    );
    expect(await api.patchProfile({'diabetes_type': 'synthetic'}), isFalse);
    expect(await api.chatStream('D30 synthetic message').toList(), isEmpty);
  });
}
