class AuthEpoch {
  AuthEpoch._();

  static int _value = 0;

  static int get value => _value;

  static void advance() {
    _value++;
  }
}
