import 'package:mocktail/mocktail.dart';
import 'package:amina/data/drift/database.dart';
import 'package:amina/services/api_client.dart';
import 'package:amina/services/auth_service.dart';
import 'package:amina/services/sync_service.dart';

class MockAppDatabase extends Mock implements AppDatabase {}
class MockApiClient extends Mock implements ApiClient {}
class MockAuthService extends Mock implements AuthService {}
class MockSyncService extends Mock implements SyncService {}

void registerMocks() {
  // Add any common mock registration here
}
