import 'dart:convert';
import 'dart:io';

import 'package:amina/services/app_lock_authenticator.dart';
import 'package:amina/services/app_lock_service.dart';
import 'package:amina/services/auth_service.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/testing.dart';

const _credentialKey = 'iamina_app_lock_credential_v1';
const _requiredKey = 'iamina_app_lock_required_v1';
const _localSessionKey = 'iamina_local_session_v1';
const _localSessionValue = 'enrolled';

const _credential = AppLockCredential(
  credentialId: 'credential-id',
  publicKeySpki: 'public-key-spki',
  rpId: 'patient.example',
  origin: 'https://patient.example',
  signCount: 4,
);

class _FakeAuthenticator implements AppLockAuthenticator {
  AppLockCapability capabilityValue;
  AppLockCredential enrollmentCredential = _credential;
  AppLockAssertion assertion;
  Object? enrollError;
  Object? unlockError;
  int enrollCalls = 0;
  int unlockCalls = 0;

  _FakeAuthenticator({
    this.capabilityValue = AppLockCapability.supported,
    this.assertion = const AppLockAssertion(signCount: 5),
  });

  @override
  Future<AppLockCapability> capability() async => capabilityValue;

  @override
  Future<AppLockCredential> enroll() async {
    enrollCalls += 1;
    final error = enrollError;
    if (error != null) throw error;
    return enrollmentCredential;
  }

  @override
  Future<AppLockAssertion> unlock(AppLockCredent¶»§q«^