// IAMINA D18 P0-D — experimental bounded-memory ciphertext archive codec.
// PRE-CUTOVER ONLY; never imported by patient-facing app or clinical providers.
// Input MUST already be physically encrypted sqlite3mc bytes from a verified
// consistent worker snapshot, NOT a plaintext SQLite database. This class
// neither opens sqlite3mc nor manages browser storage or recovery markers.
import 'dart:convert';
import 'dart:math';
import 'dart:typed_data';
import 'package:crypto/crypto.dart' as hash;
import 'package:cryptography/cryptography.dart';
import 'patient_vault_scope.dart';

final class D18StreamingArchiveManifest {
  final String vaultName;
  final String publicKeyEnvelopeJson;
  final String sha256;
  final int bytes;
  final int chunks;
  final int schemaVersion;
  const D18StreamingArchiveManifest({
    required this.vaultName, required this.publicKeyEnvelopeJson,
    required this.sha256, required this.bytes, required this.chunks,
    required this.schemaVersion,
  });
}

final class _DigestSink implements Sink<hash.Digest> {
  hash.Digest? value;
  @override
  void add(hash.Digest digest) => value = digest;
  @override
  void close() {}
}

/// V2 NDJSON: random PBKDF2 salt, 8-byte nonce prefix, 32-bit frame sequence.
/// AES-256-GCM AAD authenticates exact vault scope, frame type and sequence.
/// An authenticated final frame binds SHA-256, length and public DEK envelope.
/// Scope and envelope are never exposed in the public header.
/// Validity of this archive is NOT sqlite3mc restoration or clinical proof.
abstract final class D18StreamingCipherArchive {
  static const format = 'iamina-d18-stream-v1';
  static const schemaVersion = 12;
  static const blockSize = 64 * 1024;
  static const maxRecordBytes = 150000;
  static const maxArchiveBytes = 512 * 1024 * 1024;
  static const kdfIterations = 600000;
  static final _name = RegExp(
    r'^amina_vault_v1_(native_[1-9][0-9]*|device_[0-9a-f]{32})$');

  static String _scope(PatientVaultScope scope) {
    final name = scope.databaseName;
    if (!_name.hasMatch(name) ||
        name == PatientVaultScope.auditOnly().databaseName) {
      throw StateError('D18_STREAM_SCOPE_INVALID');
    }
    return name;
  }

  static void _password(String value) {
    if (value.runes.length < 12 || value.runes.length > 1024) {
      throw ArgumentError('D18_STREAM_PASSPHRASE_INVALID');
    }
  }

  static List<int> _random(int n) {
    final r = Random.secure();
    return List<int>.generate(n, (_) => r.nextInt(256));
  }

  static void _envelope(String input) {
    if (input.isEmpty || input.length > 4096) {
      throw const FormatException('D18_STREAM_ENVELOPE_SIZE');
    }
    final decoded = jsonDecode(input);
    const fields = {
      'format','version','kdf','iterations','salt','cipher',
      'passwordWrappedKey','recoveryWrappedKey',
    };
    if (decoded is! Map<String,dynamic> ||
        decoded.keys.toSet().difference(fields).isNotEmpty ||
        fields.difference(decoded.keys.toSet()).isNotEmpty ||
        decoded['format'] != 'iamina-d18-vault-key-envelope' ||
        decoded['version'] != 1 ||
        decoded['kdf'] != 'pbkdf2-hmac-sha256' ||
        decoded['iterations'] != kdfIterations ||
        decoded['cipher'] != 'aes-256-gcm' ||
        decoded['salt'] is! String ||
        decoded['passwordWrappedKey'] is! String ||
        decoded['recoveryWrappedKey'] is! String ||
        base64Decode(decoded['salt'] as String).length != 16 ||
        base64Decode(decoded['passwordWrappedKey'] as String).length != 60 ||
        base64Decode(decoded['recoveryWrappedKey'] as String).length != 60) {
      throw const FormatException('D18_STREAM_ENVELOPE_INVALID');
    }
  }

  static Future<SecretKey> _key(String pass, List<int> salt) =>
    Pbkdf2(macAlgorithm:Hmac.sha256(),iterations:kdfIterations,bits:256)
      .deriveKeyFromPassword(password:pass,nonce:salt);

  static List<int> _nonce(List<int> prefix,int seq) {
    if (prefix.length!=8 || seq<0 || seq>0xffffffff) {
      throw const FormatException('D18_STREAM_NONCE_SEQUENCE');
    }
    final out=Uint8List(12)..setRange(0,8,prefix);
    ByteData.view(out.buffer).setUint32(8,seq,Endian.big);
    return out;
  }
  static List<int> _aad(String scope,String kind,int seq) =>
    utf8.encode('IAMINA-D18-STREAM-V1|$kind|$seq|$scope');

  static Future<String> _seal(SecretKey key,List<int> prefix,String scope,
      String kind,int seq,List<int> bytes) async {
    final box=await AesGcm.with256bits().encrypt(bytes,secretKey:key,
      nonce:_nonce(prefix,seq),aad:_aad(scope,kind,seq));
    return base64Encode([...box.cipherText,...box.mac.bytes]);
  }

  static Future<List<int>> _open(SecretKey key,List<int> prefix,String scope,
      String kind,int seq,Object? encoded) async {
    if (encoded is! String || encoded.length>maxRecordBytes) {
      throw const FormatException('D18_STREAM_FRAME_INVALID');
    }
    final raw=base64Decode(encoded);
    if (raw.length<16 || raw.length>blockSize+4096) {
      throw const FormatException('D18_STREAM_FRAME_SIZE');
    }
    return AesGcm.with256bits().decrypt(
      SecretBox(raw.sublist(0,raw.length-16),nonce:_nonce(prefix,seq),
        mac:Mac(raw.sublist(raw.length-16))),
      secretKey:key,aad:_aad(scope,kind,seq));
  }

  /// Reject enormous or unterminated records BEFORE JSON parsing.
  static Stream<String> _lines(Stream<List<int>> source) async* {
    final pending=BytesBuilder(copy:false);
    await for (final chunk in source) {
      var from=0;
      while (from<chunk.length) {
        final sep=chunk.indexOf(10,from);
        final end=sep<0?chunk.length:sep;
        final part=chunk.sublist(from,end);
        if(pending.length+part.length>maxRecordBytes) {
          throw const FormatException('D18_STREAM_LINE_TOO_BIG');
        }
        pending.add(part);
        if(sep<0)break;
        yield utf8.decode(pending.takeBytes());
        from=sep+1;
      }
    }
    if(pending.length!=0) {
      throw const FormatException('D18_STREAM_UNTERMINATED');
    }
  }

  /// Streaming-only output: caller is responsible for writing chunks into a
  /// separately controlled archive file. Never concatenate for production.
  static Stream<List<int>> seal({
    required PatientVaultScope scope,
    required String publicKeyEnvelopeJson,
    required String backupPassphrase,
    required Stream<List<int>> encryptedSqliteChunks,
  }) async* {
    final vault=_scope(scope);
    _password(backupPassphrase);
    _envelope(publicKeyEnvelopeJson);
    final salt=_random(16),prefix=_random(8);
    final key=await _key(backupPassphrase,salt);
    final digest=_DigestSink();
    final hasher=hash.sha256.startChunkedConversion(digest);
    final pending=BytesBuilder(copy:false);
    var count=0,total=0;
    try {
      yield utf8.encode(jsonEncode({
        'format':format,'version':1,'kdf':'pbkdf2-sha256',
        'iterations':kdfIterations,'chunkSize':blockSize,
        'salt':base64Encode(salt),'noncePrefix':base64Encode(prefix),
      })+'\n');
      await for(final input in encryptedSqliteChunks) {
        for(var offset=0;offset<input.length;) {
          final len=min(blockSize-pending.length,input.length-offset);
          pending.add(input.sublist(offset,offset+len));
          offset+=len;
          if(pending.length==blockSize) {
            final bytes=pending.takeBytes();
            if(count>=0xffffffff || total+bytes.length>maxArchiveBytes) {
              throw StateError('D18_STREAM_EXPORT_LIMIT');
            }
            if(total==0 &&
               String.fromCharCodes(bytes.take(16))=='SQLite format 3\u0000') {
              throw const FormatException('D18_STREAM_PLAINTEXT_SQLITE');
            }
            hasher.add(bytes);
            total+=bytes.length;
            final sealed=await _seal(key,prefix,vault,'chunk',count,bytes);
            yield utf8.encode(jsonEncode({
              'kind':'chunk','seq':count++,'sealed':sealed,
            })+'\n');
          }
        }
      }
      if(pending.length>0) {
        final bytes=pending.takeBytes();
        if(count>=0xffffffff || total+bytes.length>maxArchiveBytes) {
          throw StateError('D18_STREAM_EXPORT_LIMIT');
        }
        if(total==0 && bytes.length>=16 &&
           String.fromCharCodes(bytes.take(16))=='SQLite format 3\u0000') {
          throw const FormatException('D18_STREAM_PLAINTEXT_SQLITE');
        }
        hasher.add(bytes);
        total+=bytes.length;
        final sealed=await _seal(key,prefix,vault,'chunk',count,bytes);
        yield utf8.encode(jsonEncode({
          'kind':'chunk','seq':count++,'sealed':sealed,
        })+'\n');
      }
      if(total<1024)throw const FormatException('D18_STREAM_TOO_SHORT');
      hasher.close();
      final payload=utf8.encode(jsonEncode({
        'scope':vault,'bytes':total,'chunks':count,
        'sha256':digest.value.toString(),
        'publicKeyEnvelopeJson':publicKeyEnvelopeJson,
        'schemaVersion':schemaVersion,
      }));
      final finalTag=await _seal(key,prefix,vault,'final',count,payload);
      yield utf8.encode(jsonEncode({
        'kind':'final','seq':count,'sealed':finalTag,
      })+'\n');
    } finally {
      key.destroy();
    }
  }

  /// Only writes physically encrypted SQLite BYTES into a separate QUARANTINE.
  /// A completed digest still requires sqlite3mc+schema+FK+durability proof.
  /// A callback MUST NEVER publish, overwrite or execute bytes directly.
  static Future<D18StreamingArchiveManifest> restoreIntoQuarantine({
    required PatientVaultScope expectedScope,
    required String backupPassphrase,
    required Stream<List<int>> archiveChunks,
    required Future<void> Function(List<int>) stageEncryptedChunk,
  }) async {
    final vault=_scope(expectedScope);
    _password(backupPassphrase);
    final sink=_DigestSink();
    final hasher=hash.sha256.startChunkedConversion(sink);
    SecretKey? key;
    List<int>? prefix;
    var header=false,finalSeen=false,count=0,total=0;
    D18StreamingArchiveManifest? result;
    try {
      await for(final line in _lines(archiveChunks)) {
        final record=jsonDecode(line);
        if(record is! Map<String,dynamic>) {
          throw const FormatException('D18_STREAM_NON_OBJECT');
        }
        if(!header) {
          header=true;
          const fields={'format','version','kdf','iterations',
            'chunkSize','salt','noncePrefix'};
          if(record.keys.toSet().difference(fields).isNotEmpty ||
             fields.difference(record.keys.toSet()).isNotEmpty ||
             record['format']!=format || record['version']!=1 ||
             record['kdf']!='pbkdf2-sha256' ||
             record['iterations']!=kdfIterations ||
             record['chunkSize']!=blockSize ||
             record['salt'] is! String ||
             record['noncePrefix'] is! String) {
            throw const FormatException('D18_STREAM_BAD_HEADER');
          }
          final salt=base64Decode(record['salt'] as String);
          prefix=base64Decode(record['noncePrefix'] as String);
          if(salt.length!=16||prefix.length!=8) {
            throw const FormatException('D18_STREAM_BAD_SALT_NONCE');
          }
          key=await _key(backupPassphrase,salt);
          continue;
        }
        if(finalSeen || record['seq']!=count) {
          throw const FormatException('D18_STREAM_OUT_OF_ORDER');
        }
        const fields={'kind','seq','sealed'};
        if(record.keys.toSet().difference(fields).isNotEmpty ||
           fields.difference(record.keys.toSet()).isNotEmpty) {
          throw const FormatException('D18_STREAM_BAD_FRAME');
        }
        if(record['kind']=='chunk') {
          final bytes=await _open(key!,prefix!,vault,'chunk',count,
            record['sealed']);
          if(bytes.isEmpty||bytes.length>blockSize ||
             total+bytes.length>maxArchiveBytes || count>=0xffffffff) {
            throw const FormatException('D18_STREAM_BAD_CHUNK');
          }
          if(total==0 && bytes.length>=16 &&
             String.fromCharCodes(bytes.take(16))=='SQLite format 3\u0000') {
            throw const FormatException('D18_STREAM_PLAINTEXT_SQLITE');
          }
          await stageEncryptedChunk(bytes);
          hasher.add(bytes);
          total+=bytes.length;
          count++;
        } else if(record['kind']=='final') {
          final payload=await _open(key!,prefix!,vault,'final',count,
            record['sealed']);
          final proof=jsonDecode(utf8.decode(payload));
          const fields={'scope','bytes','chunks','sha256',
            'publicKeyEnvelopeJson','schemaVersion'};
          if(proof is! Map<String,dynamic> ||
             proof.keys.toSet().difference(fields).isNotEmpty ||
             fields.difference(proof.keys.toSet()).isNotEmpty ||
             proof['scope']!=vault || proof['bytes']!=total ||
             proof['chunks']!=count || proof['schemaVersion']!=schemaVersion ||
             proof['sha256'] is! String ||
             proof['publicKeyEnvelopeJson'] is! String || total<1024) {
            throw const FormatException('D18_STREAM_BAD_MANIFEST');
          }
          hasher.close();
          if(sink.value.toString()!=proof['sha256']) {
            throw const FormatException('D18_STREAM_DIGEST_INVALID');
          }
          _envelope(proof['publicKeyEnvelopeJson'] as String);
          finalSeen=true;
          result=D18StreamingArchiveManifest(
            vaultName:vault,
            publicKeyEnvelopeJson:proof['publicKeyEnvelopeJson'] as String,
            sha256:sink.value.toString(),bytes:total,chunks:count,
            schemaVersion:schemaVersion,
          );
        } else {
          throw const FormatException('D18_STREAM_UNKNOWN_FRAME');
        }
      }
      if(!header||!finalSeen||result==null) {
        throw const FormatException('D18_STREAM_MISSING_FINAL');
      }
      return result;
    } finally {
      key?.destroy();
    }
  }
}
