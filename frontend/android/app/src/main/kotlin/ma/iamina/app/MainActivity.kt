package ma.iamina.app

import android.hardware.biometrics.BiometricManager
import android.hardware.biometrics.BiometricPrompt
import android.os.Build
import android.os.CancellationSignal
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel
import java.security.KeyPairGenerator
import java.security.KeyStore
import java.security.SecureRandom
import java.security.Signature
import java.security.spec.ECGenParameterSpec
import java.util.Base64
import java.util.UUID
import java.util.concurrent.Executor

/**
 * IAMINA native D18 gate: no success from a biometric boolean.
 *
 * Strong biometric authorizes a Keystore EC signature for THIS invocation
 * (auth duration 0) through BiometricPrompt.CryptoObject. The signed fresh
 * random challenge is verified with the stored public key before Flutter is
 * told the device lock opened. The private key never leaves Android Keystore.
 *
 * API < 30, absent BIOMETRIC_STRONG, enrollment change, missing key, cancelled
 * prompt, absent channel or verification error always fail closed.
 */
class MainActivity : FlutterActivity() {
    private val channelName = "ma.iamina.app/native_app_lock_v1"
    private val keyAliasPrefix = "native-bio-v1-"
    private val keyHandlePattern = Regex("^native-bio-v1-[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
    private var pending: MethodChannel.Result? = null
    private var pendingCancel: CancellationSignal? = null
    private val callbackExecutor = Executor { command -> runOnUiThread(command) }

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, channelName)
            .setMethodCallHandler { call, reply -> handleAppLock(call, reply) }
    }

    private fun strongBiometricsAvailable(): Boolean {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.R) return false
        val manager = getSystemService(BIOMETRIC_SERVICE) as? BiometricManager
            ?: return false
        return manager.canAuthenticate(BiometricManager.Authenticators.BIOMETRIC_STRONG) ==
            BiometricManager.BIOMETRIC_SUCCESS
    }

    private fun handleAppLock(call: MethodCall, reply: MethodChannel.Result) {
        when (call.method) {
            "capability" -> reply.success(mapOf("capability" to
                if (strongBiometricsAvailable()) "supported" else "unavailable"))
            "enroll" -> {
                if (!strongBiometricsAvailable()) {
                    reply.error("strong_auth_unavailable", null, null)
                    return
                }
                if (pending != null) {
                    reply.error("auth_busy", null, null)
                    return
                }
                val alias = keyAliasPrefix + UUID.randomUUID().toString()
                try {
                    val generator = KeyPairGenerator.getInstance(
                        KeyProperties.KEY_ALGORITHM_EC, "AndroidKeyStore"
                    )
                    val parameters = KeyGenParameterSpec.Builder(
                        alias, KeyProperties.PURPOSE_SIGN
                    )
                        .setAlgorithmParameterSpec(ECGenParameterSpec("secp256r1"))
                        .setDigests(KeyProperties.DIGEST_SHA256)
                        .setUserAuthenticationRequired(true)
                        .setUserAuthenticationParameters(
                            0, KeyProperties.AUTH_BIOMETRIC_STRONG
                        )
                        .setInvalidatedByBiometricEnrollment(true)
                        .build()
                    generator.initialize(parameters)
                    generator.generateKeyPair()
                    signChallenge(alias, null, true, reply)
                } catch (_: Exception) {
                    deleteKey(alias)
                    reply.error("native_enroll_failed", null, null)
                }
            }
            "unlock" -> {
                val args = call.arguments as? Map<*, *>
                val alias = args?.get("credentialId") as? String
                val expected = args?.get("publicKeySpki") as? String
                if (pending != null) {
                    reply.error("auth_busy", null, null)
                } else if (!strongBiometricsAvailable()) {
                    reply.error("strong_auth_unavailable", null, null)
                } else if (alias == null || !keyHandlePattern.matches(alias) ||
                    expected.isNullOrEmpty() ||
                    args["origin"] != "https://native.iamina.invalid" ||
                    args["rpId"] != "ma.iamina.app") {
                    reply.error("invalid_native_credential", null, null)
                } else {
                    signChallenge(alias, expected, false, reply)
                }
            }
            else -> reply.notImplemented()
        }
    }

    private fun deleteKey(alias: String) {
        try {
            KeyStore.getInstance("AndroidKeyStore").apply { load(null) }.deleteEntry(alias)
        } catch (_: Exception) { /* no patient data or key material logged */ }
    }

    private fun signChallenge(
        alias: String,
        expectedSpki: String?,
        enrollment: Boolean,
        reply: MethodChannel.Result
    ) {
        if (pending != null) {
            reply.error("auth_busy", null, null)
            return
        }
        var accepted = false
        val keyStore = try {
            KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        } catch (_: Exception) {
            reply.error("key_unavailable", null, null)
            return
        }
        val key = try { keyStore.getKey(alias, null) as? java.security.PrivateKey }
            catch (_: Exception) { null }
        val publicKey = try { keyStore.getCertificate(alias)?.publicKey }
            catch (_: Exception) { null }
        if (key == null || publicKey == null) {
            if (enrollment) deleteKey(alias)
            reply.error("key_unavailable", null, null)
            return
        }
        val spki = Base64.getEncoder().encodeToString(publicKey.encoded)
        if (!enrollment && (expectedSpki == null ||
                !java.security.MessageDigest.isEqual(
                    spki.toByteArray(Charsets.UTF_8),
                    expectedSpki.toByteArray(Charsets.UTF_8)))) {
            reply.error("native_public_key_mismatch", null, null)
            return
        }
        val signature = try {
            Signature.getInstance("SHA256withECDSA").apply { initSign(key) }
        } catch (_: Exception) {
            if (enrollment) deleteKey(alias)
            reply.error("key_invalidated_or_unavailable", null, null)
            return
        }
        val challenge = ByteArray(32).also { SecureRandom().nextBytes(it) }
        val cancellation = CancellationSignal()
        pending = reply
        pendingCancel = cancellation
        fun complete(error: String?, result: Map<String, Any>? = null) {
            if (pending !== reply) return
            pending = null
            pendingCancel = null
            if (error != null) {
                if (enrollment) deleteKey(alias)
                reply.error(error, null, null)
            } else reply.success(result)
        }
        try {
            val prompt = BiometricPrompt.Builder(this)
                .setTitle("Déverrouiller IAMINA")
                .setSubtitle("Vérification biométrique forte")
                .setAllowedAuthenticators(
                    BiometricManager.Authenticators.BIOMETRIC_STRONG
                )
                .setNegativeButton("Annuler", callbackExecutor) { _, _ ->
                    cancellation.cancel()
                    complete("user_cancelled")
                }
                .build()
            prompt.authenticate(
                BiometricPrompt.CryptoObject(signature),
                cancellation, callbackExecutor,
                object : BiometricPrompt.AuthenticationCallback() {
                    override fun onAuthenticationError(
                        errorCode: Int, errString: CharSequence
                    ) { complete("biometric_cancelled_or_unavailable") }

                    override fun onAuthenticationSucceeded(
                        result: BiometricPrompt.AuthenticationResult
                    ) {
                        if (pending !== reply) return
                        try {
                            val authenticated = result.cryptoObject?.signature
                                ?: throw IllegalStateException("Missing signed operation")
                            authenticated.update(challenge)
                            val signed = authenticated.sign()
                            val valid = Signature.getInstance("SHA256withECDSA")
                                .apply { initVerify(publicKey); update(challenge) }
                                .verify(signed)
                            if (!valid) throw IllegalStateException("Signature mismatch")
                            accepted = true
                            if (enrollment) {
                                complete(null, mapOf(
                                    "credentialId" to alias,
                                    "publicKeySpki" to spki,
                                    "verified" to true
                                ))
                            } else complete(null, mapOf("verified" to true))
                        } catch (_: Exception) {
                            complete("signature_not_verified")
                        }
                    }
                }
            )
        } catch (_: Exception) {
            if (!accepted) complete("strong_auth_unavailable")
        }
    }

    override fun onDestroy() {
        pendingCancel?.cancel()
        pending?.error("auth_interrupted", null, null)
        pending = null
        pendingCancel = null
        super.onDestroy()
    }
}
