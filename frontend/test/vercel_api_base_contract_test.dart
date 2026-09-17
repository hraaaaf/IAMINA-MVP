import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Vercel review build injects backend origin without duplicating /api/v1', () {
    final source = File('vercel_build.sh').readAsStringSync();

    expect(
      source,
      contains(
        'IAMINA_CERTIFIED_API_BASE_URL="https://iamina-certified.vercel.app"',
      ),
    );
    expect(
      source,
      isNot(
        contains(
          'IAMINA_CERTIFIED_API_BASE_URL="https://iamina-certified.vercel.app/api/v1"',
        ),
      ),
    );
  });
}
