import 'package:firebase_auth/firebase_auth.dart';

class AuthService {
  final FirebaseAuth? _auth;

  AuthService({FirebaseAuth? auth}) : _auth = _getAuthInstance(auth);

  static FirebaseAuth? _getAuthInstance(FirebaseAuth? provided) {
    try {
      return provided ?? FirebaseAuth.instance;
    } catch (_) {
      return null;
    }
  }

  Stream<User?> get authStateChanges => _auth?.authStateChanges() ?? const Stream.empty();

  Future<String?> getIdToken() async {
    return await _auth?.currentUser?.getIdToken();
  }

  Future<String?> refreshToken() async {
    return await _auth?.currentUser?.getIdToken(true);
  }

  Future<UserCredential> signInWithEmail(String email, String password) async {
    if (_auth == null) throw Exception('Firebase non initialisé');
    return await _auth.signInWithEmailAndPassword(email: email, password: password);
  }

  Future<UserCredential> registerWithEmail(String email, String password) async {
    if (_auth == null) throw Exception('Firebase non initialisé');
    return await _auth.createUserWithEmailAndPassword(email: email, password: password);
  }

  Future<void> signOut() async {
    await _auth?.signOut();
  }

  Future<UserCredential> signInAnonymously() async {
    if (_auth == null) throw Exception('Firebase non initialisé');
    return await _auth.signInAnonymously();
  }

  User? get currentUser => _auth?.currentUser;

  /// Envoie un email de réinitialisation de mot de passe.
  /// Lève une exception si Firebase n'est pas initialisé ou si l'email est invalide.
  Future<void> sendPasswordResetEmail(String email) async {
    if (_auth == null) throw Exception('Firebase non initialisé');
    await _auth.sendPasswordResetEmail(email: email.trim());
  }
}
