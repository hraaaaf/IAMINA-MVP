// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'database.dart';

// ignore_for_file: type=lint
class $LogEntriesTable extends LogEntries
    with TableInfo<$LogEntriesTable, LogEntryData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $LogEntriesTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
    'id',
    aliasedName,
    false,
    hasAutoIncrement: true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'PRIMARY KEY AUTOINCREMENT',
    ),
  );
  static const VerificationMeta _createdAtMeta = const VerificationMeta(
    'createdAt',
  );
  @override
  late final GeneratedColumn<DateTime> createdAt = GeneratedColumn<DateTime>(
    'created_at',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _bloodSugarMeta = const VerificationMeta(
    'bloodSugar',
  );
  @override
  late final GeneratedColumn<double> bloodSugar = GeneratedColumn<double>(
    'blood_sugar',
    aliasedName,
    false,
    type: DriftSqlType.double,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _insulinUnitsMeta = const VerificationMeta(
    'insulinUnits',
  );
  @override
  late final GeneratedColumn<double> insulinUnits = GeneratedColumn<double>(
    'insulin_units',
    aliasedName,
    true,
    type: DriftSqlType.double,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _glycemicContextMeta = const VerificationMeta(
    'glycemicContext',
  );
  @override
  late final GeneratedColumn<String> glycemicContext = GeneratedColumn<String>(
    'glycemic_context',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _mealTypeMeta = const VerificationMeta(
    'mealType',
  );
  @override
  late final GeneratedColumn<String> mealType = GeneratedColumn<String>(
    'meal_type',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _mealDescriptionMeta = const VerificationMeta(
    'mealDescription',
  );
  @override
  late final GeneratedColumn<String> mealDescription = GeneratedColumn<String>(
    'meal_description',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _mealItemsJsonMeta = const VerificationMeta(
    'mealItemsJson',
  );
  @override
  late final GeneratedColumn<String> mealItemsJson = GeneratedColumn<String>(
    'meal_items_json',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _mealPortionsJsonMeta = const VerificationMeta(
    'mealPortionsJson',
  );
  @override
  late final GeneratedColumn<String> mealPortionsJson = GeneratedColumn<String>(
    'meal_portions_json',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _sourceMeta = const VerificationMeta('source');
  @override
  late final GeneratedColumn<String> source = GeneratedColumn<String>(
    'source',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant('manual'),
  );
  static const VerificationMeta _syncStatusMeta = const VerificationMeta(
    'syncStatus',
  );
  @override
  late final GeneratedColumn<String> syncStatus = GeneratedColumn<String>(
    'sync_status',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant('pending'),
  );
  static const VerificationMeta _clientUuidMeta = const VerificationMeta(
    'clientUuid',
  );
  @override
  late final GeneratedColumn<String> clientUuid = GeneratedColumn<String>(
    'client_uuid',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
    defaultConstraints: GeneratedColumn.constraintIsAlways('UNIQUE'),
  );
  static const VerificationMeta _loggedAtMeta = const VerificationMeta(
    'loggedAt',
  );
  @override
  late final GeneratedColumn<DateTime> loggedAt = GeneratedColumn<DateTime>(
    'logged_at',
    aliasedName,
    true,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _fatigueLevelMeta = const VerificationMeta(
    'fatigueLevel',
  );
  @override
  late final GeneratedColumn<int> fatigueLevel = GeneratedColumn<int>(
    'fatigue_level',
    aliasedName,
    true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _isSickMeta = const VerificationMeta('isSick');
  @override
  late final GeneratedColumn<bool> isSick = GeneratedColumn<bool>(
    'is_sick',
    aliasedName,
    false,
    type: DriftSqlType.bool,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'CHECK ("is_sick" IN (0, 1))',
    ),
    defaultValue: const Constant(false),
  );
  static const VerificationMeta _isStressedMeta = const VerificationMeta(
    'isStressed',
  );
  @override
  late final GeneratedColumn<bool> isStressed = GeneratedColumn<bool>(
    'is_stressed',
    aliasedName,
    false,
    type: DriftSqlType.bool,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'CHECK ("is_stressed" IN (0, 1))',
    ),
    defaultValue: const Constant(false),
  );
  static const VerificationMeta _isTiredMeta = const VerificationMeta(
    'isTired',
  );
  @override
  late final GeneratedColumn<bool> isTired = GeneratedColumn<bool>(
    'is_tired',
    aliasedName,
    false,
    type: DriftSqlType.bool,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'CHECK ("is_tired" IN (0, 1))',
    ),
    defaultValue: const Constant(false),
  );
  static const VerificationMeta _isActiveMeta = const VerificationMeta(
    'isActive',
  );
  @override
  late final GeneratedColumn<bool> isActive = GeneratedColumn<bool>(
    'is_active',
    aliasedName,
    false,
    type: DriftSqlType.bool,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'CHECK ("is_active" IN (0, 1))',
    ),
    defaultValue: const Constant(false),
  );
  static const VerificationMeta _ramadanModeMeta = const VerificationMeta(
    'ramadanMode',
  );
  @override
  late final GeneratedColumn<bool> ramadanMode = GeneratedColumn<bool>(
    'ramadan_mode',
    aliasedName,
    false,
    type: DriftSqlType.bool,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'CHECK ("ramadan_mode" IN (0, 1))',
    ),
    defaultValue: const Constant(false),
  );
  static const VerificationMeta _sleepQualityMeta = const VerificationMeta(
    'sleepQuality',
  );
  @override
  late final GeneratedColumn<String> sleepQuality = GeneratedColumn<String>(
    'sleep_quality',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _syncAttemptsMeta = const VerificationMeta(
    'syncAttempts',
  );
  @override
  late final GeneratedColumn<int> syncAttempts = GeneratedColumn<int>(
    'sync_attempts',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultValue: const Constant(0),
  );
  static const VerificationMeta _errorSyncMeta = const VerificationMeta(
    'errorSync',
  );
  @override
  late final GeneratedColumn<bool> errorSync = GeneratedColumn<bool>(
    'error_sync',
    aliasedName,
    false,
    type: DriftSqlType.bool,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'CHECK ("error_sync" IN (0, 1))',
    ),
    defaultValue: const Constant(false),
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    createdAt,
    bloodSugar,
    insulinUnits,
    glycemicContext,
    mealType,
    mealDescription,
    mealItemsJson,
    mealPortionsJson,
    source,
    syncStatus,
    clientUuid,
    loggedAt,
    fatigueLevel,
    isSick,
    isStressed,
    isTired,
    isActive,
    ramadanMode,
    sleepQuality,
    syncAttempts,
    errorSync,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'log_entries';
  @override
  VerificationContext validateIntegrity(
    Insertable<LogEntryData> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('created_at')) {
      context.handle(
        _createdAtMeta,
        createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta),
      );
    } else if (isInserting) {
      context.missing(_createdAtMeta);
    }
    if (data.containsKey('blood_sugar')) {
      context.handle(
        _bloodSugarMeta,
        bloodSugar.isAcceptableOrUnknown(data['blood_sugar']!, _bloodSugarMeta),
      );
    } else if (isInserting) {
      context.missing(_bloodSugarMeta);
    }
    if (data.containsKey('insulin_units')) {
      context.handle(
        _insulinUnitsMeta,
        insulinUnits.isAcceptableOrUnknown(
          data['insulin_units']!,
          _insulinUnitsMeta,
        ),
      );
    }
    if (data.containsKey('glycemic_context')) {
      context.handle(
        _glycemicContextMeta,
        glycemicContext.isAcceptableOrUnknown(
          data['glycemic_context']!,
          _glycemicContextMeta,
        ),
      );
    }
    if (data.containsKey('meal_type')) {
      context.handle(
        _mealTypeMeta,
        mealType.isAcceptableOrUnknown(data['meal_type']!, _mealTypeMeta),
      );
    }
    if (data.containsKey('meal_description')) {
      context.handle(
        _mealDescriptionMeta,
        mealDescription.isAcceptableOrUnknown(
          data['meal_description']!,
          _mealDescriptionMeta,
        ),
      );
    }
    if (data.containsKey('meal_items_json')) {
      context.handle(
        _mealItemsJsonMeta,
        mealItemsJson.isAcceptableOrUnknown(
          data['meal_items_json']!,
          _mealItemsJsonMeta,
        ),
      );
    }
    if (data.containsKey('meal_portions_json')) {
      context.handle(
        _mealPortionsJsonMeta,
        mealPortionsJson.isAcceptableOrUnknown(
          data['meal_portions_json']!,
          _mealPortionsJsonMeta,
        ),
      );
    }
    if (data.containsKey('source')) {
      context.handle(
        _sourceMeta,
        source.isAcceptableOrUnknown(data['source']!, _sourceMeta),
      );
    }
    if (data.containsKey('sync_status')) {
      context.handle(
        _syncStatusMeta,
        syncStatus.isAcceptableOrUnknown(data['sync_status']!, _syncStatusMeta),
      );
    }
    if (data.containsKey('client_uuid')) {
      context.handle(
        _clientUuidMeta,
        clientUuid.isAcceptableOrUnknown(data['client_uuid']!, _clientUuidMeta),
      );
    } else if (isInserting) {
      context.missing(_clientUuidMeta);
    }
    if (data.containsKey('logged_at')) {
      context.handle(
        _loggedAtMeta,
        loggedAt.isAcceptableOrUnknown(data['logged_at']!, _loggedAtMeta),
      );
    }
    if (data.containsKey('fatigue_level')) {
      context.handle(
        _fatigueLevelMeta,
        fatigueLevel.isAcceptableOrUnknown(
          data['fatigue_level']!,
          _fatigueLevelMeta,
        ),
      );
    }
    if (data.containsKey('is_sick')) {
      context.handle(
        _isSickMeta,
        isSick.isAcceptableOrUnknown(data['is_sick']!, _isSickMeta),
      );
    }
    if (data.containsKey('is_stressed')) {
      context.handle(
        _isStressedMeta,
        isStressed.isAcceptableOrUnknown(data['is_stressed']!, _isStressedMeta),
      );
    }
    if (data.containsKey('is_tired')) {
      context.handle(
        _isTiredMeta,
        isTired.isAcceptableOrUnknown(data['is_tired']!, _isTiredMeta),
      );
    }
    if (data.containsKey('is_active')) {
      context.handle(
        _isActiveMeta,
        isActive.isAcceptableOrUnknown(data['is_active']!, _isActiveMeta),
      );
    }
    if (data.containsKey('ramadan_mode')) {
      context.handle(
        _ramadanModeMeta,
        ramadanMode.isAcceptableOrUnknown(
          data['ramadan_mode']!,
          _ramadanModeMeta,
        ),
      );
    }
    if (data.containsKey('sleep_quality')) {
      context.handle(
        _sleepQualityMeta,
        sleepQuality.isAcceptableOrUnknown(
          data['sleep_quality']!,
          _sleepQualityMeta,
        ),
      );
    }
    if (data.containsKey('sync_attempts')) {
      context.handle(
        _syncAttemptsMeta,
        syncAttempts.isAcceptableOrUnknown(
          data['sync_attempts']!,
          _syncAttemptsMeta,
        ),
      );
    }
    if (data.containsKey('error_sync')) {
      context.handle(
        _errorSyncMeta,
        errorSync.isAcceptableOrUnknown(data['error_sync']!, _errorSyncMeta),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  LogEntryData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return LogEntryData(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}id'],
      )!,
      createdAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}created_at'],
      )!,
      bloodSugar: attachedDatabase.typeMapping.read(
        DriftSqlType.double,
        data['${effectivePrefix}blood_sugar'],
      )!,
      insulinUnits: attachedDatabase.typeMapping.read(
        DriftSqlType.double,
        data['${effectivePrefix}insulin_units'],
      ),
      glycemicContext: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}glycemic_context'],
      ),
      mealType: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}meal_type'],
      ),
      mealDescription: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}meal_description'],
      ),
      mealItemsJson: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}meal_items_json'],
      ),
      mealPortionsJson: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}meal_portions_json'],
      ),
      source: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}source'],
      )!,
      syncStatus: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}sync_status'],
      )!,
      clientUuid: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}client_uuid'],
      )!,
      loggedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}logged_at'],
      ),
      fatigueLevel: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}fatigue_level'],
      ),
      isSick: attachedDatabase.typeMapping.read(
        DriftSqlType.bool,
        data['${effectivePrefix}is_sick'],
      )!,
      isStressed: attachedDatabase.typeMapping.read(
        DriftSqlType.bool,
        data['${effectivePrefix}is_stressed'],
      )!,
      isTired: attachedDatabase.typeMapping.read(
        DriftSqlType.bool,
        data['${effectivePrefix}is_tired'],
      )!,
      isActive: attachedDatabase.typeMapping.read(
        DriftSqlType.bool,
        data['${effectivePrefix}is_active'],
      )!,
      ramadanMode: attachedDatabase.typeMapping.read(
        DriftSqlType.bool,
        data['${effectivePrefix}ramadan_mode'],
      )!,
      sleepQuality: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}sleep_quality'],
      ),
      syncAttempts: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}sync_attempts'],
      )!,
      errorSync: attachedDatabase.typeMapping.read(
        DriftSqlType.bool,
        data['${effectivePrefix}error_sync'],
      )!,
    );
  }

  @override
  $LogEntriesTable createAlias(String alias) {
    return $LogEntriesTable(attachedDatabase, alias);
  }
}

class LogEntryData extends DataClass implements Insertable<LogEntryData> {
  final int id;
  final DateTime createdAt;
  final double bloodSugar;
  final double? insulinUnits;
  final String? glycemicContext;
  final String? mealType;
  final String? mealDescription;
  final String? mealItemsJson;
  final String? mealPortionsJson;
  final String source;
  final String syncStatus;
  final String clientUuid;
  final DateTime? loggedAt;
  final int? fatigueLevel;
  final bool isSick;
  final bool isStressed;
  final bool isTired;
  final bool isActive;
  final bool ramadanMode;
  final String? sleepQuality;
  final int syncAttempts;
  final bool errorSync;
  const LogEntryData({
    required this.id,
    required this.createdAt,
    required this.bloodSugar,
    this.insulinUnits,
    this.glycemicContext,
    this.mealType,
    this.mealDescription,
    this.mealItemsJson,
    this.mealPortionsJson,
    required this.source,
    required this.syncStatus,
    required this.clientUuid,
    this.loggedAt,
    this.fatigueLevel,
    required this.isSick,
    required this.isStressed,
    required this.isTired,
    required this.isActive,
    required this.ramadanMode,
    this.sleepQuality,
    required this.syncAttempts,
    required this.errorSync,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['created_at'] = Variable<DateTime>(createdAt);
    map['blood_sugar'] = Variable<double>(bloodSugar);
    if (!nullToAbsent || insulinUnits != null) {
      map['insulin_units'] = Variable<double>(insulinUnits);
    }
    if (!nullToAbsent || glycemicContext != null) {
      map['glycemic_context'] = Variable<String>(glycemicContext);
    }
    if (!nullToAbsent || mealType != null) {
      map['meal_type'] = Variable<String>(mealType);
    }
    if (!nullToAbsent || mealDescription != null) {
      map['meal_description'] = Variable<String>(mealDescription);
    }
    if (!nullToAbsent || mealItemsJson != null) {
      map['meal_items_json'] = Variable<String>(mealItemsJson);
    }
    if (!nullToAbsent || mealPortionsJson != null) {
      map['meal_portions_json'] = Variable<String>(mealPortionsJson);
    }
    map['source'] = Variable<String>(source);
    map['sync_status'] = Variable<String>(syncStatus);
    map['client_uuid'] = Variable<String>(clientUuid);
    if (!nullToAbsent || loggedAt != null) {
      map['logged_at'] = Variable<DateTime>(loggedAt);
    }
    if (!nullToAbsent || fatigueLevel != null) {
      map['fatigue_level'] = Variable<int>(fatigueLevel);
    }
    map['is_sick'] = Variable<bool>(isSick);
    map['is_stressed'] = Variable<bool>(isStressed);
    map['is_tired'] = Variable<bool>(isTired);
    map['is_active'] = Variable<bool>(isActive);
    map['ramadan_mode'] = Variable<bool>(ramadanMode);
    if (!nullToAbsent || sleepQuality != null) {
      map['sleep_quality'] = Variable<String>(sleepQuality);
    }
    map['sync_attempts'] = Variable<int>(syncAttempts);
    map['error_sync'] = Variable<bool>(errorSync);
    return map;
  }

  LogEntriesCompanion toCompanion(bool nullToAbsent) {
    return LogEntriesCompanion(
      id: Value(id),
      createdAt: Value(createdAt),
      bloodSugar: Value(bloodSugar),
      insulinUnits: insulinUnits == null && nullToAbsent
          ? const Value.absent()
          : Value(insulinUnits),
      glycemicContext: glycemicContext == null && nullToAbsent
          ? const Value.absent()
          : Value(glycemicContext),
      mealType: mealType == null && nullToAbsent
          ? const Value.absent()
          : Value(mealType),
      mealDescription: mealDescription == null && nullToAbsent
          ? const Value.absent()
          : Value(mealDescription),
      mealItemsJson: mealItemsJson == null && nullToAbsent
          ? const Value.absent()
          : Value(mealItemsJson),
      mealPortionsJson: mealPortionsJson == null && nullToAbsent
          ? const Value.absent()
          : Value(mealPortionsJson),
      source: Value(source),
      syncStatus: Value(syncStatus),
      clientUuid: Value(clientUuid),
      loggedAt: loggedAt == null && nullToAbsent
          ? const Value.absent()
          : Value(loggedAt),
      fatigueLevel: fatigueLevel == null && nullToAbsent
          ? const Value.absent()
          : Value(fatigueLevel),
      isSick: Value(isSick),
      isStressed: Value(isStressed),
      isTired: Value(isTired),
      isActive: Value(isActive),
      ramadanMode: Value(ramadanMode),
      sleepQuality: sleepQuality == null && nullToAbsent
          ? const Value.absent()
          : Value(sleepQuality),
      syncAttempts: Value(syncAttempts),
      errorSync: Value(errorSync),
    );
  }

  factory LogEntryData.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return LogEntryData(
      id: serializer.fromJson<int>(json['id']),
      createdAt: serializer.fromJson<DateTime>(json['createdAt']),
      bloodSugar: serializer.fromJson<double>(json['bloodSugar']),
      insulinUnits: serializer.fromJson<double?>(json['insulinUnits']),
      glycemicContext: serializer.fromJson<String?>(json['glycemicContext']),
      mealType: serializer.fromJson<String?>(json['mealType']),
      mealDescription: serializer.fromJson<String?>(json['mealDescription']),
      mealItemsJson: serializer.fromJson<String?>(json['mealItemsJson']),
      mealPortionsJson: serializer.fromJson<String?>(json['mealPortionsJson']),
      source: serializer.fromJson<String>(json['source']),
      syncStatus: serializer.fromJson<String>(json['syncStatus']),
      clientUuid: serializer.fromJson<String>(json['clientUuid']),
      loggedAt: serializer.fromJson<DateTime?>(json['loggedAt']),
      fatigueLevel: serializer.fromJson<int?>(json['fatigueLevel']),
      isSick: serializer.fromJson<bool>(json['isSick']),
      isStressed: serializer.fromJson<bool>(json['isStressed']),
      isTired: serializer.fromJson<bool>(json['isTired']),
      isActive: serializer.fromJson<bool>(json['isActive']),
      ramadanMode: serializer.fromJson<bool>(json['ramadanMode']),
      sleepQuality: serializer.fromJson<String?>(json['sleepQuality']),
      syncAttempts: serializer.fromJson<int>(json['syncAttempts']),
      errorSync: serializer.fromJson<bool>(json['errorSync']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'createdAt': serializer.toJson<DateTime>(createdAt),
      'bloodSugar': serializer.toJson<double>(bloodSugar),
      'insulinUnits': serializer.toJson<double?>(insulinUnits),
      'glycemicContext': serializer.toJson<String?>(glycemicContext),
      'mealType': serializer.toJson<String?>(mealType),
      'mealDescription': serializer.toJson<String?>(mealDescription),
      'mealItemsJson': serializer.toJson<String?>(mealItemsJson),
      'mealPortionsJson': serializer.toJson<String?>(mealPortionsJson),
      'source': serializer.toJson<String>(source),
      'syncStatus': serializer.toJson<String>(syncStatus),
      'clientUuid': serializer.toJson<String>(clientUuid),
      'loggedAt': serializer.toJson<DateTime?>(loggedAt),
      'fatigueLevel': serializer.toJson<int?>(fatigueLevel),
      'isSick': serializer.toJson<bool>(isSick),
      'isStressed': serializer.toJson<bool>(isStressed),
      'isTired': serializer.toJson<bool>(isTired),
      'isActive': serializer.toJson<bool>(isActive),
      'ramadanMode': serializer.toJson<bool>(ramadanMode),
      'sleepQuality': serializer.toJson<String?>(sleepQuality),
      'syncAttempts': serializer.toJson<int>(syncAttempts),
      'errorSync': serializer.toJson<bool>(errorSync),
    };
  }

  LogEntryData copyWith({
    int? id,
    DateTime? createdAt,
    double? bloodSugar,
    Value<double?> insulinUnits = const Value.absent(),
    Value<String?> glycemicContext = const Value.absent(),
    Value<String?> mealType = const Value.absent(),
    Value<String?> mealDescription = const Value.absent(),
    Value<String?> mealItemsJson = const Value.absent(),
    Value<String?> mealPortionsJson = const Value.absent(),
    String? source,
    String? syncStatus,
    String? clientUuid,
    Value<DateTime?> loggedAt = const Value.absent(),
    Value<int?> fatigueLevel = const Value.absent(),
    bool? isSick,
    bool? isStressed,
    bool? isTired,
    bool? isActive,
    bool? ramadanMode,
    Value<String?> sleepQuality = const Value.absent(),
    int? syncAttempts,
    bool? errorSync,
  }) => LogEntryData(
    id: id ?? this.id,
    createdAt: createdAt ?? this.createdAt,
    bloodSugar: bloodSugar ?? this.bloodSugar,
    insulinUnits: insulinUnits.present ? insulinUnits.value : this.insulinUnits,
    glycemicContext: glycemicContext.present
        ? glycemicContext.value
        : this.glycemicContext,
    mealType: mealType.present ? mealType.value : this.mealType,
    mealDescription: mealDescription.present
        ? mealDescription.value
        : this.mealDescription,
    mealItemsJson: mealItemsJson.present
        ? mealItemsJson.value
        : this.mealItemsJson,
    mealPortionsJson: mealPortionsJson.present
        ? mealPortionsJson.value
        : this.mealPortionsJson,
    source: source ?? this.source,
    syncStatus: syncStatus ?? this.syncStatus,
    clientUuid: clientUuid ?? this.clientUuid,
    loggedAt: loggedAt.present ? loggedAt.value : this.loggedAt,
    fatigueLevel: fatigueLevel.present ? fatigueLevel.value : this.fatigueLevel,
    isSick: isSick ?? this.isSick,
    isStressed: isStressed ?? this.isStressed,
    isTired: isTired ?? this.isTired,
    isActive: isActive ?? this.isActive,
    ramadanMode: ramadanMode ?? this.ramadanMode,
    sleepQuality: sleepQuality.present ? sleepQuality.value : this.sleepQuality,
    syncAttempts: syncAttempts ?? this.syncAttempts,
    errorSync: errorSync ?? this.errorSync,
  );
  LogEntryData copyWithCompanion(LogEntriesCompanion data) {
    return LogEntryData(
      id: data.id.present ? data.id.value : this.id,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
      bloodSugar: data.bloodSugar.present
          ? data.bloodSugar.value
          : this.bloodSugar,
      insulinUnits: data.insulinUnits.present
          ? data.insulinUnits.value
          : this.insulinUnits,
      glycemicContext: data.glycemicContext.present
          ? data.glycemicContext.value
          : this.glycemicContext,
      mealType: data.mealType.present ? data.mealType.value : this.mealType,
      mealDescription: data.mealDescription.present
          ? data.mealDescription.value
          : this.mealDescription,
      mealItemsJson: data.mealItemsJson.present
          ? data.mealItemsJson.value
          : this.mealItemsJson,
      mealPortionsJson: data.mealPortionsJson.present
          ? data.mealPortionsJson.value
          : this.mealPortionsJson,
      source: data.source.present ? data.source.value : this.source,
      syncStatus: data.syncStatus.present
          ? data.syncStatus.value
          : this.syncStatus,
      clientUuid: data.clientUuid.present
          ? data.clientUuid.value
          : this.clientUuid,
      loggedAt: data.loggedAt.present ? data.loggedAt.value : this.loggedAt,
      fatigueLevel: data.fatigueLevel.present
          ? data.fatigueLevel.value
          : this.fatigueLevel,
      isSick: data.isSick.present ? data.isSick.value : this.isSick,
      isStressed: data.isStressed.present
          ? data.isStressed.value
          : this.isStressed,
      isTired: data.isTired.present ? data.isTired.value : this.isTired,
      isActive: data.isActive.present ? data.isActive.value : this.isActive,
      ramadanMode: data.ramadanMode.present
          ? data.ramadanMode.value
          : this.ramadanMode,
      sleepQuality: data.sleepQuality.present
          ? data.sleepQuality.value
          : this.sleepQuality,
      syncAttempts: data.syncAttempts.present
          ? data.syncAttempts.value
          : this.syncAttempts,
      errorSync: data.errorSync.present ? data.errorSync.value : this.errorSync,
    );
  }

  @override
  String toString() {
    return (StringBuffer('LogEntryData(')
          ..write('id: $id, ')
          ..write('createdAt: $createdAt, ')
          ..write('bloodSugar: $bloodSugar, ')
          ..write('insulinUnits: $insulinUnits, ')
          ..write('glycemicContext: $glycemicContext, ')
          ..write('mealType: $mealType, ')
          ..write('mealDescription: $mealDescription, ')
          ..write('mealItemsJson: $mealItemsJson, ')
          ..write('mealPortionsJson: $mealPortionsJson, ')
          ..write('source: $source, ')
          ..write('syncStatus: $syncStatus, ')
          ..write('clientUuid: $clientUuid, ')
          ..write('loggedAt: $loggedAt, ')
          ..write('fatigueLevel: $fatigueLevel, ')
          ..write('isSick: $isSick, ')
          ..write('isStressed: $isStressed, ')
          ..write('isTired: $isTired, ')
          ..write('isActive: $isActive, ')
          ..write('ramadanMode: $ramadanMode, ')
          ..write('sleepQuality: $sleepQuality, ')
          ..write('syncAttempts: $syncAttempts, ')
          ..write('errorSync: $errorSync')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hashAll([
    id,
    createdAt,
    bloodSugar,
    insulinUnits,
    glycemicContext,
    mealType,
    mealDescription,
    mealItemsJson,
    mealPortionsJson,
    source,
    syncStatus,
    clientUuid,
    loggedAt,
    fatigueLevel,
    isSick,
    isStressed,
    isTired,
    isActive,
    ramadanMode,
    sleepQuality,
    syncAttempts,
    errorSync,
  ]);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is LogEntryData &&
          other.id == this.id &&
          other.createdAt == this.createdAt &&
          other.bloodSugar == this.bloodSugar &&
          other.insulinUnits == this.insulinUnits &&
          other.glycemicContext == this.glycemicContext &&
          other.mealType == this.mealType &&
          other.mealDescription == this.mealDescription &&
          other.mealItemsJson == this.mealItemsJson &&
          other.mealPortionsJson == this.mealPortionsJson &&
          other.source == this.source &&
          other.syncStatus == this.syncStatus &&
          other.clientUuid == this.clientUuid &&
          other.loggedAt == this.loggedAt &&
          other.fatigueLevel == this.fatigueLevel &&
          other.isSick == this.isSick &&
          other.isStressed == this.isStressed &&
          other.isTired == this.isTired &&
          other.isActive == this.isActive &&
          other.ramadanMode == this.ramadanMode &&
          other.sleepQuality == this.sleepQuality &&
          other.syncAttempts == this.syncAttempts &&
          other.errorSync == this.errorSync);
}

class LogEntriesCompanion extends UpdateCompanion<LogEntryData> {
  final Value<int> id;
  final Value<DateTime> createdAt;
  final Value<double> bloodSugar;
  final Value<double?> insulinUnits;
  final Value<String?> glycemicContext;
  final Value<String?> mealType;
  final Value<String?> mealDescription;
  final Value<String?> mealItemsJson;
  final Value<String?> mealPortionsJson;
  final Value<String> source;
  final Value<String> syncStatus;
  final Value<String> clientUuid;
  final Value<DateTime?> loggedAt;
  final Value<int?> fatigueLevel;
  final Value<bool> isSick;
  final Value<bool> isStressed;
  final Value<bool> isTired;
  final Value<bool> isActive;
  final Value<bool> ramadanMode;
  final Value<String?> sleepQuality;
  final Value<int> syncAttempts;
  final Value<bool> errorSync;
  const LogEntriesCompanion({
    this.id = const Value.absent(),
    this.createdAt = const Value.absent(),
    this.bloodSugar = const Value.absent(),
    this.insulinUnits = const Value.absent(),
    this.glycemicContext = const Value.absent(),
    this.mealType = const Value.absent(),
    this.mealDescription = const Value.absent(),
    this.mealItemsJson = const Value.absent(),
    this.mealPortionsJson = const Value.absent(),
    this.source = const Value.absent(),
    this.syncStatus = const Value.absent(),
    this.clientUuid = const Value.absent(),
    this.loggedAt = const Value.absent(),
    this.fatigueLevel = const Value.absent(),
    this.isSick = const Value.absent(),
    this.isStressed = const Value.absent(),
    this.isTired = const Value.absent(),
    this.isActive = const Value.absent(),
    this.ramadanMode = const Value.absent(),
    this.sleepQuality = const Value.absent(),
    this.syncAttempts = const Value.absent(),
    this.errorSync = const Value.absent(),
  });
  LogEntriesCompanion.insert({
    this.id = const Value.absent(),
    required DateTime createdAt,
    required double bloodSugar,
    this.insulinUnits = const Value.absent(),
    this.glycemicContext = const Value.absent(),
    this.mealType = const Value.absent(),
    this.mealDescription = const Value.absent(),
    this.mealItemsJson = const Value.absent(),
    this.mealPortionsJson = const Value.absent(),
    this.source = const Value.absent(),
    this.syncStatus = const Value.absent(),
    required String clientUuid,
    this.loggedAt = const Value.absent(),
    this.fatigueLevel = const Value.absent(),
    this.isSick = const Value.absent(),
    this.isStressed = const Value.absent(),
    this.isTired = const Value.absent(),
    this.isActive = const Value.absent(),
    this.ramadanMode = const Value.absent(),
    this.sleepQuality = const Value.absent(),
    this.syncAttempts = const Value.absent(),
    this.errorSync = const Value.absent(),
  }) : createdAt = Value(createdAt),
       bloodSugar = Value(bloodSugar),
       clientUuid = Value(clientUuid);
  static Insertable<LogEntryData> custom({
    Expression<int>? id,
    Expression<DateTime>? createdAt,
    Expression<double>? bloodSugar,
    Expression<double>? insulinUnits,
    Expression<String>? glycemicContext,
    Expression<String>? mealType,
    Expression<String>? mealDescription,
    Expression<String>? mealItemsJson,
    Expression<String>? mealPortionsJson,
    Expression<String>? source,
    Expression<String>? syncStatus,
    Expression<String>? clientUuid,
    Expression<DateTime>? loggedAt,
    Expression<int>? fatigueLevel,
    Expression<bool>? isSick,
    Expression<bool>? isStressed,
    Expression<bool>? isTired,
    Expression<bool>? isActive,
    Expression<bool>? ramadanMode,
    Expression<String>? sleepQuality,
    Expression<int>? syncAttempts,
    Expression<bool>? errorSync,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (createdAt != null) 'created_at': createdAt,
      if (bloodSugar != null) 'blood_sugar': bloodSugar,
      if (insulinUnits != null) 'insulin_units': insulinUnits,
      if (glycemicContext != null) 'glycemic_context': glycemicContext,
      if (mealType != null) 'meal_type': mealType,
      if (mealDescription != null) 'meal_description': mealDescription,
      if (mealItemsJson != null) 'meal_items_json': mealItemsJson,
      if (mealPortionsJson != null) 'meal_portions_json': mealPortionsJson,
      if (source != null) 'source': source,
      if (syncStatus != null) 'sync_status': syncStatus,
      if (clientUuid != null) 'client_uuid': clientUuid,
      if (loggedAt != null) 'logged_at': loggedAt,
      if (fatigueLevel != null) 'fatigue_level': fatigueLevel,
      if (isSick != null) 'is_sick': isSick,
      if (isStressed != null) 'is_stressed': isStressed,
      if (isTired != null) 'is_tired': isTired,
      if (isActive != null) 'is_active': isActive,
      if (ramadanMode != null) 'ramadan_mode': ramadanMode,
      if (sleepQuality != null) 'sleep_quality': sleepQuality,
      if (syncAttempts != null) 'sync_attempts': syncAttempts,
      if (errorSync != null) 'error_sync': errorSync,
    });
  }

  LogEntriesCompanion copyWith({
    Value<int>? id,
    Value<DateTime>? createdAt,
    Value<double>? bloodSugar,
    Value<double?>? insulinUnits,
    Value<String?>? glycemicContext,
    Value<String?>? mealType,
    Value<String?>? mealDescription,
    Value<String?>? mealItemsJson,
    Value<String?>? mealPortionsJson,
    Value<String>? source,
    Value<String>? syncStatus,
    Value<String>? clientUuid,
    Value<DateTime?>? loggedAt,
    Value<int?>? fatigueLevel,
    Value<bool>? isSick,
    Value<bool>? isStressed,
    Value<bool>? isTired,
    Value<bool>? isActive,
    Value<bool>? ramadanMode,
    Value<String?>? sleepQuality,
    Value<int>? syncAttempts,
    Value<bool>? errorSync,
  }) {
    return LogEntriesCompanion(
      id: id ?? this.id,
      createdAt: createdAt ?? this.createdAt,
      bloodSugar: bloodSugar ?? this.bloodSugar,
      insulinUnits: insulinUnits ?? this.insulinUnits,
      glycemicContext: glycemicContext ?? this.glycemicContext,
      mealType: mealType ?? this.mealType,
      mealDescription: mealDescription ?? this.mealDescription,
      mealItemsJson: mealItemsJson ?? this.mealItemsJson,
      mealPortionsJson: mealPortionsJson ?? this.mealPortionsJson,
      source: source ?? this.source,
      syncStatus: syncStatus ?? this.syncStatus,
      clientUuid: clientUuid ?? this.clientUuid,
      loggedAt: loggedAt ?? this.loggedAt,
      fatigueLevel: fatigueLevel ?? this.fatigueLevel,
      isSick: isSick ?? this.isSick,
      isStressed: isStressed ?? this.isStressed,
      isTired: isTired ?? this.isTired,
      isActive: isActive ?? this.isActive,
      ramadanMode: ramadanMode ?? this.ramadanMode,
      sleepQuality: sleepQuality ?? this.sleepQuality,
      syncAttempts: syncAttempts ?? this.syncAttempts,
      errorSync: errorSync ?? this.errorSync,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<DateTime>(createdAt.value);
    }
    if (bloodSugar.present) {
      map['blood_sugar'] = Variable<double>(bloodSugar.value);
    }
    if (insulinUnits.present) {
      map['insulin_units'] = Variable<double>(insulinUnits.value);
    }
    if (glycemicContext.present) {
      map['glycemic_context'] = Variable<String>(glycemicContext.value);
    }
    if (mealType.present) {
      map['meal_type'] = Variable<String>(mealType.value);
    }
    if (mealDescription.present) {
      map['meal_description'] = Variable<String>(mealDescription.value);
    }
    if (mealItemsJson.present) {
      map['meal_items_json'] = Variable<String>(mealItemsJson.value);
    }
    if (mealPortionsJson.present) {
      map['meal_portions_json'] = Variable<String>(mealPortionsJson.value);
    }
    if (source.present) {
      map['source'] = Variable<String>(source.value);
    }
    if (syncStatus.present) {
      map['sync_status'] = Variable<String>(syncStatus.value);
    }
    if (clientUuid.present) {
      map['client_uuid'] = Variable<String>(clientUuid.value);
    }
    if (loggedAt.present) {
      map['logged_at'] = Variable<DateTime>(loggedAt.value);
    }
    if (fatigueLevel.present) {
      map['fatigue_level'] = Variable<int>(fatigueLevel.value);
    }
    if (isSick.present) {
      map['is_sick'] = Variable<bool>(isSick.value);
    }
    if (isStressed.present) {
      map['is_stressed'] = Variable<bool>(isStressed.value);
    }
    if (isTired.present) {
      map['is_tired'] = Variable<bool>(isTired.value);
    }
    if (isActive.present) {
      map['is_active'] = Variable<bool>(isActive.value);
    }
    if (ramadanMode.present) {
      map['ramadan_mode'] = Variable<bool>(ramadanMode.value);
    }
    if (sleepQuality.present) {
      map['sleep_quality'] = Variable<String>(sleepQuality.value);
    }
    if (syncAttempts.present) {
      map['sync_attempts'] = Variable<int>(syncAttempts.value);
    }
    if (errorSync.present) {
      map['error_sync'] = Variable<bool>(errorSync.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('LogEntriesCompanion(')
          ..write('id: $id, ')
          ..write('createdAt: $createdAt, ')
          ..write('bloodSugar: $bloodSugar, ')
          ..write('insulinUnits: $insulinUnits, ')
          ..write('glycemicContext: $glycemicContext, ')
          ..write('mealType: $mealType, ')
          ..write('mealDescription: $mealDescription, ')
          ..write('mealItemsJson: $mealItemsJson, ')
          ..write('mealPortionsJson: $mealPortionsJson, ')
          ..write('source: $source, ')
          ..write('syncStatus: $syncStatus, ')
          ..write('clientUuid: $clientUuid, ')
          ..write('loggedAt: $loggedAt, ')
          ..write('fatigueLevel: $fatigueLevel, ')
          ..write('isSick: $isSick, ')
          ..write('isStressed: $isStressed, ')
          ..write('isTired: $isTired, ')
          ..write('isActive: $isActive, ')
          ..write('ramadanMode: $ramadanMode, ')
          ..write('sleepQuality: $sleepQuality, ')
          ..write('syncAttempts: $syncAttempts, ')
          ..write('errorSync: $errorSync')
          ..write(')'))
        .toString();
  }
}

class $PatientProfilesTable extends PatientProfiles
    with TableInfo<$PatientProfilesTable, PatientProfileData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $PatientProfilesTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _userIdMeta = const VerificationMeta('userId');
  @override
  late final GeneratedColumn<int> userId = GeneratedColumn<int>(
    'user_id',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _preferredLanguageMeta = const VerificationMeta(
    'preferredLanguage',
  );
  @override
  late final GeneratedColumn<String> preferredLanguage =
      GeneratedColumn<String>(
        'preferred_language',
        aliasedName,
        false,
        type: DriftSqlType.string,
        requiredDuringInsert: false,
        defaultValue: const Constant('fr'),
      );
  static const VerificationMeta _updatedAtMeta = const VerificationMeta(
    'updatedAt',
  );
  @override
  late final GeneratedColumn<DateTime> updatedAt = GeneratedColumn<DateTime>(
    'updated_at',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _diabetesTypeMeta = const VerificationMeta(
    'diabetesType',
  );
  @override
  late final GeneratedColumn<String> diabetesType = GeneratedColumn<String>(
    'diabetes_type',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _targetRangeLowMeta = const VerificationMeta(
    'targetRangeLow',
  );
  @override
  late final GeneratedColumn<double> targetRangeLow = GeneratedColumn<double>(
    'target_range_low',
    aliasedName,
    false,
    type: DriftSqlType.double,
    requiredDuringInsert: false,
    defaultValue: const Constant(70.0),
  );
  static const VerificationMeta _targetRangeHighMeta = const VerificationMeta(
    'targetRangeHigh',
  );
  @override
  late final GeneratedColumn<double> targetRangeHigh = GeneratedColumn<double>(
    'target_range_high',
    aliasedName,
    false,
    type: DriftSqlType.double,
    requiredDuringInsert: false,
    defaultValue: const Constant(180.0),
  );
  static const VerificationMeta _unitPreferenceMeta = const VerificationMeta(
    'unitPreference',
  );
  @override
  late final GeneratedColumn<String> unitPreference = GeneratedColumn<String>(
    'unit_preference',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant('mg/dL'),
  );
  static const VerificationMeta _treatmentMeta = const VerificationMeta(
    'treatment',
  );
  @override
  late final GeneratedColumn<String> treatment = GeneratedColumn<String>(
    'treatment',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _ramadanStartDateMeta = const VerificationMeta(
    'ramadanStartDate',
  );
  @override
  late final GeneratedColumn<DateTime> ramadanStartDate =
      GeneratedColumn<DateTime>(
        'ramadan_start_date',
        aliasedName,
        true,
        type: DriftSqlType.dateTime,
        requiredDuringInsert: false,
      );
  static const VerificationMeta _ramadanEndDateMeta = const VerificationMeta(
    'ramadanEndDate',
  );
  @override
  late final GeneratedColumn<DateTime> ramadanEndDate =
      GeneratedColumn<DateTime>(
        'ramadan_end_date',
        aliasedName,
        true,
        type: DriftSqlType.dateTime,
        requiredDuringInsert: false,
      );
  static const VerificationMeta _aiConsentGivenAtMeta = const VerificationMeta(
    'aiConsentGivenAt',
  );
  @override
  late final GeneratedColumn<DateTime> aiConsentGivenAt =
      GeneratedColumn<DateTime>(
        'ai_consent_given_at',
        aliasedName,
        true,
        type: DriftSqlType.dateTime,
        requiredDuringInsert: false,
      );
  @override
  List<GeneratedColumn> get $columns => [
    userId,
    preferredLanguage,
    updatedAt,
    diabetesType,
    targetRangeLow,
    targetRangeHigh,
    unitPreference,
    treatment,
    ramadanStartDate,
    ramadanEndDate,
    aiConsentGivenAt,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'patient_profiles';
  @override
  VerificationContext validateIntegrity(
    Insertable<PatientProfileData> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('user_id')) {
      context.handle(
        _userIdMeta,
        userId.isAcceptableOrUnknown(data['user_id']!, _userIdMeta),
      );
    }
    if (data.containsKey('preferred_language')) {
      context.handle(
        _preferredLanguageMeta,
        preferredLanguage.isAcceptableOrUnknown(
          data['preferred_language']!,
          _preferredLanguageMeta,
        ),
      );
    }
    if (data.containsKey('updated_at')) {
      context.handle(
        _updatedAtMeta,
        updatedAt.isAcceptableOrUnknown(data['updated_at']!, _updatedAtMeta),
      );
    } else if (isInserting) {
      context.missing(_updatedAtMeta);
    }
    if (data.containsKey('diabetes_type')) {
      context.handle(
        _diabetesTypeMeta,
        diabetesType.isAcceptableOrUnknown(
          data['diabetes_type']!,
          _diabetesTypeMeta,
        ),
      );
    }
    if (data.containsKey('target_range_low')) {
      context.handle(
        _targetRangeLowMeta,
        targetRangeLow.isAcceptableOrUnknown(
          data['target_range_low']!,
          _targetRangeLowMeta,
        ),
      );
    }
    if (data.containsKey('target_range_high')) {
      context.handle(
        _targetRangeHighMeta,
        targetRangeHigh.isAcceptableOrUnknown(
          data['target_range_high']!,
          _targetRangeHighMeta,
        ),
      );
    }
    if (data.containsKey('unit_preference')) {
      context.handle(
        _unitPreferenceMeta,
        unitPreference.isAcceptableOrUnknown(
          data['unit_preference']!,
          _unitPreferenceMeta,
        ),
      );
    }
    if (data.containsKey('treatment')) {
      context.handle(
        _treatmentMeta,
        treatment.isAcceptableOrUnknown(data['treatment']!, _treatmentMeta),
      );
    }
    if (data.containsKey('ramadan_start_date')) {
      context.handle(
        _ramadanStartDateMeta,
        ramadanStartDate.isAcceptableOrUnknown(
          data['ramadan_start_date']!,
          _ramadanStartDateMeta,
        ),
      );
    }
    if (data.containsKey('ramadan_end_date')) {
      context.handle(
        _ramadanEndDateMeta,
        ramadanEndDate.isAcceptableOrUnknown(
          data['ramadan_end_date']!,
          _ramadanEndDateMeta,
        ),
      );
    }
    if (data.containsKey('ai_consent_given_at')) {
      context.handle(
        _aiConsentGivenAtMeta,
        aiConsentGivenAt.isAcceptableOrUnknown(
          data['ai_consent_given_at']!,
          _aiConsentGivenAtMeta,
        ),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {userId};
  @override
  PatientProfileData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return PatientProfileData(
      userId: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}user_id'],
      )!,
      preferredLanguage: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}preferred_language'],
      )!,
      updatedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}updated_at'],
      )!,
      diabetesType: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}diabetes_type'],
      ),
      targetRangeLow: attachedDatabase.typeMapping.read(
        DriftSqlType.double,
        data['${effectivePrefix}target_range_low'],
      )!,
      targetRangeHigh: attachedDatabase.typeMapping.read(
        DriftSqlType.double,
        data['${effectivePrefix}target_range_high'],
      )!,
      unitPreference: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}unit_preference'],
      )!,
      treatment: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}treatment'],
      ),
      ramadanStartDate: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}ramadan_start_date'],
      ),
      ramadanEndDate: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}ramadan_end_date'],
      ),
      aiConsentGivenAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}ai_consent_given_at'],
      ),
    );
  }

  @override
  $PatientProfilesTable createAlias(String alias) {
    return $PatientProfilesTable(attachedDatabase, alias);
  }
}

class PatientProfileData extends DataClass
    implements Insertable<PatientProfileData> {
  final int userId;
  final String preferredLanguage;
  final DateTime updatedAt;
  final String? diabetesType;
  final double targetRangeLow;
  final double targetRangeHigh;
  final String unitPreference;

  /// Treatment modality: 'insulin' | 'tablets' | 'lifestyle'
  final String? treatment;
  final DateTime? ramadanStartDate;
  final DateTime? ramadanEndDate;

  /// RGPD Art. 7 — explicit AI processing consent timestamp.
  /// null = no consent given or withdrawn.
  final DateTime? aiConsentGivenAt;
  const PatientProfileData({
    required this.userId,
    required this.preferredLanguage,
    required this.updatedAt,
    this.diabetesType,
    required this.targetRangeLow,
    required this.targetRangeHigh,
    required this.unitPreference,
    this.treatment,
    this.ramadanStartDate,
    this.ramadanEndDate,
    this.aiConsentGivenAt,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['user_id'] = Variable<int>(userId);
    map['preferred_language'] = Variable<String>(preferredLanguage);
    map['updated_at'] = Variable<DateTime>(updatedAt);
    if (!nullToAbsent || diabetesType != null) {
      map['diabetes_type'] = Variable<String>(diabetesType);
    }
    map['target_range_low'] = Variable<double>(targetRangeLow);
    map['target_range_high'] = Variable<double>(targetRangeHigh);
    map['unit_preference'] = Variable<String>(unitPreference);
    if (!nullToAbsent || treatment != null) {
      map['treatment'] = Variable<String>(treatment);
    }
    if (!nullToAbsent || ramadanStartDate != null) {
      map['ramadan_start_date'] = Variable<DateTime>(ramadanStartDate);
    }
    if (!nullToAbsent || ramadanEndDate != null) {
      map['ramadan_end_date'] = Variable<DateTime>(ramadanEndDate);
    }
    if (!nullToAbsent || aiConsentGivenAt != null) {
      map['ai_consent_given_at'] = Variable<DateTime>(aiConsentGivenAt);
    }
    return map;
  }

  PatientProfilesCompanion toCompanion(bool nullToAbsent) {
    return PatientProfilesCompanion(
      userId: Value(userId),
      preferredLanguage: Value(preferredLanguage),
      updatedAt: Value(updatedAt),
      diabetesType: diabetesType == null && nullToAbsent
          ? const Value.absent()
          : Value(diabetesType),
      targetRangeLow: Value(targetRangeLow),
      targetRangeHigh: Value(targetRangeHigh),
      unitPreference: Value(unitPreference),
      treatment: treatment == null && nullToAbsent
          ? const Value.absent()
          : Value(treatment),
      ramadanStartDate: ramadanStartDate == null && nullToAbsent
          ? const Value.absent()
          : Value(ramadanStartDate),
      ramadanEndDate: ramadanEndDate == null && nullToAbsent
          ? const Value.absent()
          : Value(ramadanEndDate),
      aiConsentGivenAt: aiConsentGivenAt == null && nullToAbsent
          ? const Value.absent()
          : Value(aiConsentGivenAt),
    );
  }

  factory PatientProfileData.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return PatientProfileData(
      userId: serializer.fromJson<int>(json['userId']),
      preferredLanguage: serializer.fromJson<String>(json['preferredLanguage']),
      updatedAt: serializer.fromJson<DateTime>(json['updatedAt']),
      diabetesType: serializer.fromJson<String?>(json['diabetesType']),
      targetRangeLow: serializer.fromJson<double>(json['targetRangeLow']),
      targetRangeHigh: serializer.fromJson<double>(json['targetRangeHigh']),
      unitPreference: serializer.fromJson<String>(json['unitPreference']),
      treatment: serializer.fromJson<String?>(json['treatment']),
      ramadanStartDate: serializer.fromJson<DateTime?>(
        json['ramadanStartDate'],
      ),
      ramadanEndDate: serializer.fromJson<DateTime?>(json['ramadanEndDate']),
      aiConsentGivenAt: serializer.fromJson<DateTime?>(
        json['aiConsentGivenAt'],
      ),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'userId': serializer.toJson<int>(userId),
      'preferredLanguage': serializer.toJson<String>(preferredLanguage),
      'updatedAt': serializer.toJson<DateTime>(updatedAt),
      'diabetesType': serializer.toJson<String?>(diabetesType),
      'targetRangeLow': serializer.toJson<double>(targetRangeLow),
      'targetRangeHigh': serializer.toJson<double>(targetRangeHigh),
      'unitPreference': serializer.toJson<String>(unitPreference),
      'treatment': serializer.toJson<String?>(treatment),
      'ramadanStartDate': serializer.toJson<DateTime?>(ramadanStartDate),
      'ramadanEndDate': serializer.toJson<DateTime?>(ramadanEndDate),
      'aiConsentGivenAt': serializer.toJson<DateTime?>(aiConsentGivenAt),
    };
  }

  PatientProfileData copyWith({
    int? userId,
    String? preferredLanguage,
    DateTime? updatedAt,
    Value<String?> diabetesType = const Value.absent(),
    double? targetRangeLow,
    double? targetRangeHigh,
    String? unitPreference,
    Value<String?> treatment = const Value.absent(),
    Value<DateTime?> ramadanStartDate = const Value.absent(),
    Value<DateTime?> ramadanEndDate = const Value.absent(),
    Value<DateTime?> aiConsentGivenAt = const Value.absent(),
  }) => PatientProfileData(
    userId: userId ?? this.userId,
    preferredLanguage: preferredLanguage ?? this.preferredLanguage,
    updatedAt: updatedAt ?? this.updatedAt,
    diabetesType: diabetesType.present ? diabetesType.value : this.diabetesType,
    targetRangeLow: targetRangeLow ?? this.targetRangeLow,
    targetRangeHigh: targetRangeHigh ?? this.targetRangeHigh,
    unitPreference: unitPreference ?? this.unitPreference,
    treatment: treatment.present ? treatment.value : this.treatment,
    ramadanStartDate: ramadanStartDate.present
        ? ramadanStartDate.value
        : this.ramadanStartDate,
    ramadanEndDate: ramadanEndDate.present
        ? ramadanEndDate.value
        : this.ramadanEndDate,
    aiConsentGivenAt: aiConsentGivenAt.present
        ? aiConsentGivenAt.value
        : this.aiConsentGivenAt,
  );
  PatientProfileData copyWithCompanion(PatientProfilesCompanion data) {
    return PatientProfileData(
      userId: data.userId.present ? data.userId.value : this.userId,
      preferredLanguage: data.preferredLanguage.present
          ? data.preferredLanguage.value
          : this.preferredLanguage,
      updatedAt: data.updatedAt.present ? data.updatedAt.value : this.updatedAt,
      diabetesType: data.diabetesType.present
          ? data.diabetesType.value
          : this.diabetesType,
      targetRangeLow: data.targetRangeLow.present
          ? data.targetRangeLow.value
          : this.targetRangeLow,
      targetRangeHigh: data.targetRangeHigh.present
          ? data.targetRangeHigh.value
          : this.targetRangeHigh,
      unitPreference: data.unitPreference.present
          ? data.unitPreference.value
          : this.unitPreference,
      treatment: data.treatment.present ? data.treatment.value : this.treatment,
      ramadanStartDate: data.ramadanStartDate.present
          ? data.ramadanStartDate.value
          : this.ramadanStartDate,
      ramadanEndDate: data.ramadanEndDate.present
          ? data.ramadanEndDate.value
          : this.ramadanEndDate,
      aiConsentGivenAt: data.aiConsentGivenAt.present
          ? data.aiConsentGivenAt.value
          : this.aiConsentGivenAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('PatientProfileData(')
          ..write('userId: $userId, ')
          ..write('preferredLanguage: $preferredLanguage, ')
          ..write('updatedAt: $updatedAt, ')
          ..write('diabetesType: $diabetesType, ')
          ..write('targetRangeLow: $targetRangeLow, ')
          ..write('targetRangeHigh: $targetRangeHigh, ')
          ..write('unitPreference: $unitPreference, ')
          ..write('treatment: $treatment, ')
          ..write('ramadanStartDate: $ramadanStartDate, ')
          ..write('ramadanEndDate: $ramadanEndDate, ')
          ..write('aiConsentGivenAt: $aiConsentGivenAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    userId,
    preferredLanguage,
    updatedAt,
    diabetesType,
    targetRangeLow,
    targetRangeHigh,
    unitPreference,
    treatment,
    ramadanStartDate,
    ramadanEndDate,
    aiConsentGivenAt,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is PatientProfileData &&
          other.userId == this.userId &&
          other.preferredLanguage == this.preferredLanguage &&
          other.updatedAt == this.updatedAt &&
          other.diabetesType == this.diabetesType &&
          other.targetRangeLow == this.targetRangeLow &&
          other.targetRangeHigh == this.targetRangeHigh &&
          other.unitPreference == this.unitPreference &&
          other.treatment == this.treatment &&
          other.ramadanStartDate == this.ramadanStartDate &&
          other.ramadanEndDate == this.ramadanEndDate &&
          other.aiConsentGivenAt == this.aiConsentGivenAt);
}

class PatientProfilesCompanion extends UpdateCompanion<PatientProfileData> {
  final Value<int> userId;
  final Value<String> preferredLanguage;
  final Value<DateTime> updatedAt;
  final Value<String?> diabetesType;
  final Value<double> targetRangeLow;
  final Value<double> targetRangeHigh;
  final Value<String> unitPreference;
  final Value<String?> treatment;
  final Value<DateTime?> ramadanStartDate;
  final Value<DateTime?> ramadanEndDate;
  final Value<DateTime?> aiConsentGivenAt;
  const PatientProfilesCompanion({
    this.userId = const Value.absent(),
    this.preferredLanguage = const Value.absent(),
    this.updatedAt = const Value.absent(),
    this.diabetesType = const Value.absent(),
    this.targetRangeLow = const Value.absent(),
    this.targetRangeHigh = const Value.absent(),
    this.unitPreference = const Value.absent(),
    this.treatment = const Value.absent(),
    this.ramadanStartDate = const Value.absent(),
    this.ramadanEndDate = const Value.absent(),
    this.aiConsentGivenAt = const Value.absent(),
  });
  PatientProfilesCompanion.insert({
    this.userId = const Value.absent(),
    this.preferredLanguage = const Value.absent(),
    required DateTime updatedAt,
    this.diabetesType = const Value.absent(),
    this.targetRangeLow = const Value.absent(),
    this.targetRangeHigh = const Value.absent(),
    this.unitPreference = const Value.absent(),
    this.treatment = const Value.absent(),
    this.ramadanStartDate = const Value.absent(),
    this.ramadanEndDate = const Value.absent(),
    this.aiConsentGivenAt = const Value.absent(),
  }) : updatedAt = Value(updatedAt);
  static Insertable<PatientProfileData> custom({
    Expression<int>? userId,
    Expression<String>? preferredLanguage,
    Expression<DateTime>? updatedAt,
    Expression<String>? diabetesType,
    Expression<double>? targetRangeLow,
    Expression<double>? targetRangeHigh,
    Expression<String>? unitPreference,
    Expression<String>? treatment,
    Expression<DateTime>? ramadanStartDate,
    Expression<DateTime>? ramadanEndDate,
    Expression<DateTime>? aiConsentGivenAt,
  }) {
    return RawValuesInsertable({
      if (userId != null) 'user_id': userId,
      if (preferredLanguage != null) 'preferred_language': preferredLanguage,
      if (updatedAt != null) 'updated_at': updatedAt,
      if (diabetesType != null) 'diabetes_type': diabetesType,
      if (targetRangeLow != null) 'target_range_low': targetRangeLow,
      if (targetRangeHigh != null) 'target_range_high': targetRangeHigh,
      if (unitPreference != null) 'unit_preference': unitPreference,
      if (treatment != null) 'treatment': treatment,
      if (ramadanStartDate != null) 'ramadan_start_date': ramadanStartDate,
      if (ramadanEndDate != null) 'ramadan_end_date': ramadanEndDate,
      if (aiConsentGivenAt != null) 'ai_consent_given_at': aiConsentGivenAt,
    });
  }

  PatientProfilesCompanion copyWith({
    Value<int>? userId,
    Value<String>? preferredLanguage,
    Value<DateTime>? updatedAt,
    Value<String?>? diabetesType,
    Value<double>? targetRangeLow,
    Value<double>? targetRangeHigh,
    Value<String>? unitPreference,
    Value<String?>? treatment,
    Value<DateTime?>? ramadanStartDate,
    Value<DateTime?>? ramadanEndDate,
    Value<DateTime?>? aiConsentGivenAt,
  }) {
    return PatientProfilesCompanion(
      userId: userId ?? this.userId,
      preferredLanguage: preferredLanguage ?? this.preferredLanguage,
      updatedAt: updatedAt ?? this.updatedAt,
      diabetesType: diabetesType ?? this.diabetesType,
      targetRangeLow: targetRangeLow ?? this.targetRangeLow,
      targetRangeHigh: targetRangeHigh ?? this.targetRangeHigh,
      unitPreference: unitPreference ?? this.unitPreference,
      treatment: treatment ?? this.treatment,
      ramadanStartDate: ramadanStartDate ?? this.ramadanStartDate,
      ramadanEndDate: ramadanEndDate ?? this.ramadanEndDate,
      aiConsentGivenAt: aiConsentGivenAt ?? this.aiConsentGivenAt,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (userId.present) {
      map['user_id'] = Variable<int>(userId.value);
    }
    if (preferredLanguage.present) {
      map['preferred_language'] = Variable<String>(preferredLanguage.value);
    }
    if (updatedAt.present) {
      map['updated_at'] = Variable<DateTime>(updatedAt.value);
    }
    if (diabetesType.present) {
      map['diabetes_type'] = Variable<String>(diabetesType.value);
    }
    if (targetRangeLow.present) {
      map['target_range_low'] = Variable<double>(targetRangeLow.value);
    }
    if (targetRangeHigh.present) {
      map['target_range_high'] = Variable<double>(targetRangeHigh.value);
    }
    if (unitPreference.present) {
      map['unit_preference'] = Variable<String>(unitPreference.value);
    }
    if (treatment.present) {
      map['treatment'] = Variable<String>(treatment.value);
    }
    if (ramadanStartDate.present) {
      map['ramadan_start_date'] = Variable<DateTime>(ramadanStartDate.value);
    }
    if (ramadanEndDate.present) {
      map['ramadan_end_date'] = Variable<DateTime>(ramadanEndDate.value);
    }
    if (aiConsentGivenAt.present) {
      map['ai_consent_given_at'] = Variable<DateTime>(aiConsentGivenAt.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('PatientProfilesCompanion(')
          ..write('userId: $userId, ')
          ..write('preferredLanguage: $preferredLanguage, ')
          ..write('updatedAt: $updatedAt, ')
          ..write('diabetesType: $diabetesType, ')
          ..write('targetRangeLow: $targetRangeLow, ')
          ..write('targetRangeHigh: $targetRangeHigh, ')
          ..write('unitPreference: $unitPreference, ')
          ..write('treatment: $treatment, ')
          ..write('ramadanStartDate: $ramadanStartDate, ')
          ..write('ramadanEndDate: $ramadanEndDate, ')
          ..write('aiConsentGivenAt: $aiConsentGivenAt')
          ..write(')'))
        .toString();
  }
}

class $ChatMessagesTable extends ChatMessages
    with TableInfo<$ChatMessagesTable, ChatMessageData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $ChatMessagesTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
    'id',
    aliasedName,
    false,
    hasAutoIncrement: true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'PRIMARY KEY AUTOINCREMENT',
    ),
  );
  static const VerificationMeta _conversationIdMeta = const VerificationMeta(
    'conversationId',
  );
  @override
  late final GeneratedColumn<String> conversationId = GeneratedColumn<String>(
    'conversation_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _roleMeta = const VerificationMeta('role');
  @override
  late final GeneratedColumn<String> role = GeneratedColumn<String>(
    'role',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _messageMeta = const VerificationMeta(
    'message',
  );
  @override
  late final GeneratedColumn<String> message = GeneratedColumn<String>(
    'message',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _createdAtMeta = const VerificationMeta(
    'createdAt',
  );
  @override
  late final GeneratedColumn<DateTime> createdAt = GeneratedColumn<DateTime>(
    'created_at',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    conversationId,
    role,
    message,
    createdAt,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'chat_messages';
  @override
  VerificationContext validateIntegrity(
    Insertable<ChatMessageData> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('conversation_id')) {
      context.handle(
        _conversationIdMeta,
        conversationId.isAcceptableOrUnknown(
          data['conversation_id']!,
          _conversationIdMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_conversationIdMeta);
    }
    if (data.containsKey('role')) {
      context.handle(
        _roleMeta,
        role.isAcceptableOrUnknown(data['role']!, _roleMeta),
      );
    } else if (isInserting) {
      context.missing(_roleMeta);
    }
    if (data.containsKey('message')) {
      context.handle(
        _messageMeta,
        message.isAcceptableOrUnknown(data['message']!, _messageMeta),
      );
    } else if (isInserting) {
      context.missing(_messageMeta);
    }
    if (data.containsKey('created_at')) {
      context.handle(
        _createdAtMeta,
        createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta),
      );
    } else if (isInserting) {
      context.missing(_createdAtMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  ChatMessageData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return ChatMessageData(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}id'],
      )!,
      conversationId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}conversation_id'],
      )!,
      role: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}role'],
      )!,
      message: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}message'],
      )!,
      createdAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}created_at'],
      )!,
    );
  }

  @override
  $ChatMessagesTable createAlias(String alias) {
    return $ChatMessagesTable(attachedDatabase, alias);
  }
}

class ChatMessageData extends DataClass implements Insertable<ChatMessageData> {
  final int id;
  final String conversationId;
  final String role;
  final String message;
  final DateTime createdAt;
  const ChatMessageData({
    required this.id,
    required this.conversationId,
    required this.role,
    required this.message,
    required this.createdAt,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['conversation_id'] = Variable<String>(conversationId);
    map['role'] = Variable<String>(role);
    map['message'] = Variable<String>(message);
    map['created_at'] = Variable<DateTime>(createdAt);
    return map;
  }

  ChatMessagesCompanion toCompanion(bool nullToAbsent) {
    return ChatMessagesCompanion(
      id: Value(id),
      conversationId: Value(conversationId),
      role: Value(role),
      message: Value(message),
      createdAt: Value(createdAt),
    );
  }

  factory ChatMessageData.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return ChatMessageData(
      id: serializer.fromJson<int>(json['id']),
      conversationId: serializer.fromJson<String>(json['conversationId']),
      role: serializer.fromJson<String>(json['role']),
      message: serializer.fromJson<String>(json['message']),
      createdAt: serializer.fromJson<DateTime>(json['createdAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'conversationId': serializer.toJson<String>(conversationId),
      'role': serializer.toJson<String>(role),
      'message': serializer.toJson<String>(message),
      'createdAt': serializer.toJson<DateTime>(createdAt),
    };
  }

  ChatMessageData copyWith({
    int? id,
    String? conversationId,
    String? role,
    String? message,
    DateTime? createdAt,
  }) => ChatMessageData(
    id: id ?? this.id,
    conversationId: conversationId ?? this.conversationId,
    role: role ?? this.role,
    message: message ?? this.message,
    createdAt: createdAt ?? this.createdAt,
  );
  ChatMessageData copyWithCompanion(ChatMessagesCompanion data) {
    return ChatMessageData(
      id: data.id.present ? data.id.value : this.id,
      conversationId: data.conversationId.present
          ? data.conversationId.value
          : this.conversationId,
      role: data.role.present ? data.role.value : this.role,
      message: data.message.present ? data.message.value : this.message,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('ChatMessageData(')
          ..write('id: $id, ')
          ..write('conversationId: $conversationId, ')
          ..write('role: $role, ')
          ..write('message: $message, ')
          ..write('createdAt: $createdAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(id, conversationId, role, message, createdAt);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is ChatMessageData &&
          other.id == this.id &&
          other.conversationId == this.conversationId &&
          other.role == this.role &&
          other.message == this.message &&
          other.createdAt == this.createdAt);
}

class ChatMessagesCompanion extends UpdateCompanion<ChatMessageData> {
  final Value<int> id;
  final Value<String> conversationId;
  final Value<String> role;
  final Value<String> message;
  final Value<DateTime> createdAt;
  const ChatMessagesCompanion({
    this.id = const Value.absent(),
    this.conversationId = const Value.absent(),
    this.role = const Value.absent(),
    this.message = const Value.absent(),
    this.createdAt = const Value.absent(),
  });
  ChatMessagesCompanion.insert({
    this.id = const Value.absent(),
    required String conversationId,
    required String role,
    required String message,
    required DateTime createdAt,
  }) : conversationId = Value(conversationId),
       role = Value(role),
       message = Value(message),
       createdAt = Value(createdAt);
  static Insertable<ChatMessageData> custom({
    Expression<int>? id,
    Expression<String>? conversationId,
    Expression<String>? role,
    Expression<String>? message,
    Expression<DateTime>? createdAt,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (conversationId != null) 'conversation_id': conversationId,
      if (role != null) 'role': role,
      if (message != null) 'message': message,
      if (createdAt != null) 'created_at': createdAt,
    });
  }

  ChatMessagesCompanion copyWith({
    Value<int>? id,
    Value<String>? conversationId,
    Value<String>? role,
    Value<String>? message,
    Value<DateTime>? createdAt,
  }) {
    return ChatMessagesCompanion(
      id: id ?? this.id,
      conversationId: conversationId ?? this.conversationId,
      role: role ?? this.role,
      message: message ?? this.message,
      createdAt: createdAt ?? this.createdAt,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (conversationId.present) {
      map['conversation_id'] = Variable<String>(conversationId.value);
    }
    if (role.present) {
      map['role'] = Variable<String>(role.value);
    }
    if (message.present) {
      map['message'] = Variable<String>(message.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<DateTime>(createdAt.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('ChatMessagesCompanion(')
          ..write('id: $id, ')
          ..write('conversationId: $conversationId, ')
          ..write('role: $role, ')
          ..write('message: $message, ')
          ..write('createdAt: $createdAt')
          ..write(')'))
        .toString();
  }
}

class $MedicationEventsTable extends MedicationEvents
    with TableInfo<$MedicationEventsTable, MedicationEventData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $MedicationEventsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
    'id',
    aliasedName,
    false,
    hasAutoIncrement: true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'PRIMARY KEY AUTOINCREMENT',
    ),
  );
  static const VerificationMeta _labelMeta = const VerificationMeta('label');
  @override
  late final GeneratedColumn<String> label = GeneratedColumn<String>(
    'label',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _doseMeta = const VerificationMeta('dose');
  @override
  late final GeneratedColumn<double> dose = GeneratedColumn<double>(
    'dose',
    aliasedName,
    true,
    type: DriftSqlType.double,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _unitMeta = const VerificationMeta('unit');
  @override
  late final GeneratedColumn<String> unit = GeneratedColumn<String>(
    'unit',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _takenAtMeta = const VerificationMeta(
    'takenAt',
  );
  @override
  late final GeneratedColumn<DateTime> takenAt = GeneratedColumn<DateTime>(
    'taken_at',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _createdAtMeta = const VerificationMeta(
    'createdAt',
  );
  @override
  late final GeneratedColumn<DateTime> createdAt = GeneratedColumn<DateTime>(
    'created_at',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    label,
    dose,
    unit,
    takenAt,
    createdAt,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'medication_events';
  @override
  VerificationContext validateIntegrity(
    Insertable<MedicationEventData> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('label')) {
      context.handle(
        _labelMeta,
        label.isAcceptableOrUnknown(data['label']!, _labelMeta),
      );
    } else if (isInserting) {
      context.missing(_labelMeta);
    }
    if (data.containsKey('dose')) {
      context.handle(
        _doseMeta,
        dose.isAcceptableOrUnknown(data['dose']!, _doseMeta),
      );
    }
    if (data.containsKey('unit')) {
      context.handle(
        _unitMeta,
        unit.isAcceptableOrUnknown(data['unit']!, _unitMeta),
      );
    }
    if (data.containsKey('taken_at')) {
      context.handle(
        _takenAtMeta,
        takenAt.isAcceptableOrUnknown(data['taken_at']!, _takenAtMeta),
      );
    } else if (isInserting) {
      context.missing(_takenAtMeta);
    }
    if (data.containsKey('created_at')) {
      context.handle(
        _createdAtMeta,
        createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta),
      );
    } else if (isInserting) {
      context.missing(_createdAtMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  MedicationEventData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return MedicationEventData(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}id'],
      )!,
      label: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}label'],
      )!,
      dose: attachedDatabase.typeMapping.read(
        DriftSqlType.double,
        data['${effectivePrefix}dose'],
      ),
      unit: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}unit'],
      ),
      takenAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}taken_at'],
      )!,
      createdAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}created_at'],
      )!,
    );
  }

  @override
  $MedicationEventsTable createAlias(String alias) {
    return $MedicationEventsTable(attachedDatabase, alias);
  }
}

class MedicationEventData extends DataClass
    implements Insertable<MedicationEventData> {
  final int id;
  final String label;
  final double? dose;
  final String? unit;
  final DateTime takenAt;
  final DateTime createdAt;
  const MedicationEventData({
    required this.id,
    required this.label,
    this.dose,
    this.unit,
    required this.takenAt,
    required this.createdAt,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['label'] = Variable<String>(label);
    if (!nullToAbsent || dose != null) {
      map['dose'] = Variable<double>(dose);
    }
    if (!nullToAbsent || unit != null) {
      map['unit'] = Variable<String>(unit);
    }
    map['taken_at'] = Variable<DateTime>(takenAt);
    map['created_at'] = Variable<DateTime>(createdAt);
    return map;
  }

  MedicationEventsCompanion toCompanion(bool nullToAbsent) {
    return MedicationEventsCompanion(
      id: Value(id),
      label: Value(label),
      dose: dose == null && nullToAbsent ? const Value.absent() : Value(dose),
      unit: unit == null && nullToAbsent ? const Value.absent() : Value(unit),
      takenAt: Value(takenAt),
      createdAt: Value(createdAt),
    );
  }

  factory MedicationEventData.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return MedicationEventData(
      id: serializer.fromJson<int>(json['id']),
      label: serializer.fromJson<String>(json['label']),
      dose: serializer.fromJson<double?>(json['dose']),
      unit: serializer.fromJson<String?>(json['unit']),
      takenAt: serializer.fromJson<DateTime>(json['takenAt']),
      createdAt: serializer.fromJson<DateTime>(json['createdAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'label': serializer.toJson<String>(label),
      'dose': serializer.toJson<double?>(dose),
      'unit': serializer.toJson<String?>(unit),
      'takenAt': serializer.toJson<DateTime>(takenAt),
      'createdAt': serializer.toJson<DateTime>(createdAt),
    };
  }

  MedicationEventData copyWith({
    int? id,
    String? label,
    Value<double?> dose = const Value.absent(),
    Value<String?> unit = const Value.absent(),
    DateTime? takenAt,
    DateTime? createdAt,
  }) => MedicationEventData(
    id: id ?? this.id,
    label: label ?? this.label,
    dose: dose.present ? dose.value : this.dose,
    unit: unit.present ? unit.value : this.unit,
    takenAt: takenAt ?? this.takenAt,
    createdAt: createdAt ?? this.createdAt,
  );
  MedicationEventData copyWithCompanion(MedicationEventsCompanion data) {
    return MedicationEventData(
      id: data.id.present ? data.id.value : this.id,
      label: data.label.present ? data.label.value : this.label,
      dose: data.dose.present ? data.dose.value : this.dose,
      unit: data.unit.present ? data.unit.value : this.unit,
      takenAt: data.takenAt.present ? data.takenAt.value : this.takenAt,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('MedicationEventData(')
          ..write('id: $id, ')
          ..write('label: $label, ')
          ..write('dose: $dose, ')
          ..write('unit: $unit, ')
          ..write('takenAt: $takenAt, ')
          ..write('createdAt: $createdAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(id, label, dose, unit, takenAt, createdAt);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is MedicationEventData &&
          other.id == this.id &&
          other.label == this.label &&
          other.dose == this.dose &&
          other.unit == this.unit &&
          other.takenAt == this.takenAt &&
          other.createdAt == this.createdAt);
}

class MedicationEventsCompanion extends UpdateCompanion<MedicationEventData> {
  final Value<int> id;
  final Value<String> label;
  final Value<double?> dose;
  final Value<String?> unit;
  final Value<DateTime> takenAt;
  final Value<DateTime> createdAt;
  const MedicationEventsCompanion({
    this.id = const Value.absent(),
    this.label = const Value.absent(),
    this.dose = const Value.absent(),
    this.unit = const Value.absent(),
    this.takenAt = const Value.absent(),
    this.createdAt = const Value.absent(),
  });
  MedicationEventsCompanion.insert({
    this.id = const Value.absent(),
    required String label,
    this.dose = const Value.absent(),
    this.unit = const Value.absent(),
    required DateTime takenAt,
    required DateTime createdAt,
  }) : label = Value(label),
       takenAt = Value(takenAt),
       createdAt = Value(createdAt);
  static Insertable<MedicationEventData> custom({
    Expression<int>? id,
    Expression<String>? label,
    Expression<double>? dose,
    Expression<String>? unit,
    Expression<DateTime>? takenAt,
    Expression<DateTime>? createdAt,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (label != null) 'label': label,
      if (dose != null) 'dose': dose,
      if (unit != null) 'unit': unit,
      if (takenAt != null) 'taken_at': takenAt,
      if (createdAt != null) 'created_at': createdAt,
    });
  }

  MedicationEventsCompanion copyWith({
    Value<int>? id,
    Value<String>? label,
    Value<double?>? dose,
    Value<String?>? unit,
    Value<DateTime>? takenAt,
    Value<DateTime>? createdAt,
  }) {
    return MedicationEventsCompanion(
      id: id ?? this.id,
      label: label ?? this.label,
      dose: dose ?? this.dose,
      unit: unit ?? this.unit,
      takenAt: takenAt ?? this.takenAt,
      createdAt: createdAt ?? this.createdAt,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (label.present) {
      map['label'] = Variable<String>(label.value);
    }
    if (dose.present) {
      map['dose'] = Variable<double>(dose.value);
    }
    if (unit.present) {
      map['unit'] = Variable<String>(unit.value);
    }
    if (takenAt.present) {
      map['taken_at'] = Variable<DateTime>(takenAt.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<DateTime>(createdAt.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('MedicationEventsCompanion(')
          ..write('id: $id, ')
          ..write('label: $label, ')
          ..write('dose: $dose, ')
          ..write('unit: $unit, ')
          ..write('takenAt: $takenAt, ')
          ..write('createdAt: $createdAt')
          ..write(')'))
        .toString();
  }
}

class $RemindersTable extends Reminders
    with TableInfo<$RemindersTable, ReminderData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $RemindersTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
    'id',
    aliasedName,
    false,
    hasAutoIncrement: true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'PRIMARY KEY AUTOINCREMENT',
    ),
  );
  static const VerificationMeta _titleMeta = const VerificationMeta('title');
  @override
  late final GeneratedColumn<String> title = GeneratedColumn<String>(
    'title',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _dueAtMeta = const VerificationMeta('dueAt');
  @override
  late final GeneratedColumn<DateTime> dueAt = GeneratedColumn<DateTime>(
    'due_at',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _enabledMeta = const VerificationMeta(
    'enabled',
  );
  @override
  late final GeneratedColumn<bool> enabled = GeneratedColumn<bool>(
    'enabled',
    aliasedName,
    false,
    type: DriftSqlType.bool,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'CHECK ("enabled" IN (0, 1))',
    ),
    defaultValue: const Constant(true),
  );
  static const VerificationMeta _createdAtMeta = const VerificationMeta(
    'createdAt',
  );
  @override
  late final GeneratedColumn<DateTime> createdAt = GeneratedColumn<DateTime>(
    'created_at',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [id, title, dueAt, enabled, createdAt];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'reminders';
  @override
  VerificationContext validateIntegrity(
    Insertable<ReminderData> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('title')) {
      context.handle(
        _titleMeta,
        title.isAcceptableOrUnknown(data['title']!, _titleMeta),
      );
    } else if (isInserting) {
      context.missing(_titleMeta);
    }
    if (data.containsKey('due_at')) {
      context.handle(
        _dueAtMeta,
        dueAt.isAcceptableOrUnknown(data['due_at']!, _dueAtMeta),
      );
    } else if (isInserting) {
      context.missing(_dueAtMeta);
    }
    if (data.containsKey('enabled')) {
      context.handle(
        _enabledMeta,
        enabled.isAcceptableOrUnknown(data['enabled']!, _enabledMeta),
      );
    }
    if (data.containsKey('created_at')) {
      context.handle(
        _createdAtMeta,
        createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta),
      );
    } else if (isInserting) {
      context.missing(_createdAtMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  ReminderData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return ReminderData(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}id'],
      )!,
      title: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}title'],
      )!,
      dueAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}due_at'],
      )!,
      enabled: attachedDatabase.typeMapping.read(
        DriftSqlType.bool,
        data['${effectivePrefix}enabled'],
      )!,
      createdAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}created_at'],
      )!,
    );
  }

  @override
  $RemindersTable createAlias(String alias) {
    return $RemindersTable(attachedDatabase, alias);
  }
}

class ReminderData extends DataClass implements Insertable<ReminderData> {
  final int id;
  final String title;
  final DateTime dueAt;
  final bool enabled;
  final DateTime createdAt;
  const ReminderData({
    required this.id,
    required this.title,
    required this.dueAt,
    required this.enabled,
    required this.createdAt,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['title'] = Variable<String>(title);
    map['due_at'] = Variable<DateTime>(dueAt);
    map['enabled'] = Variable<bool>(enabled);
    map['created_at'] = Variable<DateTime>(createdAt);
    return map;
  }

  RemindersCompanion toCompanion(bool nullToAbsent) {
    return RemindersCompanion(
      id: Value(id),
      title: Value(title),
      dueAt: Value(dueAt),
      enabled: Value(enabled),
      createdAt: Value(createdAt),
    );
  }

  factory ReminderData.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return ReminderData(
      id: serializer.fromJson<int>(json['id']),
      title: serializer.fromJson<String>(json['title']),
      dueAt: serializer.fromJson<DateTime>(json['dueAt']),
      enabled: serializer.fromJson<bool>(json['enabled']),
      createdAt: serializer.fromJson<DateTime>(json['createdAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'title': serializer.toJson<String>(title),
      'dueAt': serializer.toJson<DateTime>(dueAt),
      'enabled': serializer.toJson<bool>(enabled),
      'createdAt': serializer.toJson<DateTime>(createdAt),
    };
  }

  ReminderData copyWith({
    int? id,
    String? title,
    DateTime? dueAt,
    bool? enabled,
    DateTime? createdAt,
  }) => ReminderData(
    id: id ?? this.id,
    title: title ?? this.title,
    dueAt: dueAt ?? this.dueAt,
    enabled: enabled ?? this.enabled,
    createdAt: createdAt ?? this.createdAt,
  );
  ReminderData copyWithCompanion(RemindersCompanion data) {
    return ReminderData(
      id: data.id.present ? data.id.value : this.id,
      title: data.title.present ? data.title.value : this.title,
      dueAt: data.dueAt.present ? data.dueAt.value : this.dueAt,
      enabled: data.enabled.present ? data.enabled.value : this.enabled,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('ReminderData(')
          ..write('id: $id, ')
          ..write('title: $title, ')
          ..write('dueAt: $dueAt, ')
          ..write('enabled: $enabled, ')
          ..write('createdAt: $createdAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(id, title, dueAt, enabled, createdAt);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is ReminderData &&
          other.id == this.id &&
          other.title == this.title &&
          other.dueAt == this.dueAt &&
          other.enabled == this.enabled &&
          other.createdAt == this.createdAt);
}

class RemindersCompanion extends UpdateCompanion<ReminderData> {
  final Value<int> id;
  final Value<String> title;
  final Value<DateTime> dueAt;
  final Value<bool> enabled;
  final Value<DateTime> createdAt;
  const RemindersCompanion({
    this.id = const Value.absent(),
    this.title = const Value.absent(),
    this.dueAt = const Value.absent(),
    this.enabled = const Value.absent(),
    this.createdAt = const Value.absent(),
  });
  RemindersCompanion.insert({
    this.id = const Value.absent(),
    required String title,
    required DateTime dueAt,
    this.enabled = const Value.absent(),
    required DateTime createdAt,
  }) : title = Value(title),
       dueAt = Value(dueAt),
       createdAt = Value(createdAt);
  static Insertable<ReminderData> custom({
    Expression<int>? id,
    Expression<String>? title,
    Expression<DateTime>? dueAt,
    Expression<bool>? enabled,
    Expression<DateTime>? createdAt,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (title != null) 'title': title,
      if (dueAt != null) 'due_at': dueAt,
      if (enabled != null) 'enabled': enabled,
      if (createdAt != null) 'created_at': createdAt,
    });
  }

  RemindersCompanion copyWith({
    Value<int>? id,
    Value<String>? title,
    Value<DateTime>? dueAt,
    Value<bool>? enabled,
    Value<DateTime>? createdAt,
  }) {
    return RemindersCompanion(
      id: id ?? this.id,
      title: title ?? this.title,
      dueAt: dueAt ?? this.dueAt,
      enabled: enabled ?? this.enabled,
      createdAt: createdAt ?? this.createdAt,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (title.present) {
      map['title'] = Variable<String>(title.value);
    }
    if (dueAt.present) {
      map['due_at'] = Variable<DateTime>(dueAt.value);
    }
    if (enabled.present) {
      map['enabled'] = Variable<bool>(enabled.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<DateTime>(createdAt.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('RemindersCompanion(')
          ..write('id: $id, ')
          ..write('title: $title, ')
          ..write('dueAt: $dueAt, ')
          ..write('enabled: $enabled, ')
          ..write('createdAt: $createdAt')
          ..write(')'))
        .toString();
  }
}

abstract class _$AppDatabase extends GeneratedDatabase {
  _$AppDatabase(QueryExecutor e) : super(e);
  $AppDatabaseManager get managers => $AppDatabaseManager(this);
  late final $LogEntriesTable logEntries = $LogEntriesTable(this);
  late final $PatientProfilesTable patientProfiles = $PatientProfilesTable(
    this,
  );
  late final $ChatMessagesTable chatMessages = $ChatMessagesTable(this);
  late final $MedicationEventsTable medicationEvents = $MedicationEventsTable(
    this,
  );
  late final $RemindersTable reminders = $RemindersTable(this);
  @override
  Iterable<TableInfo<Table, Object?>> get allTables =>
      allSchemaEntities.whereType<TableInfo<Table, Object?>>();
  @override
  List<DatabaseSchemaEntity> get allSchemaEntities => [
    logEntries,
    patientProfiles,
    chatMessages,
    medicationEvents,
    reminders,
  ];
}

typedef $$LogEntriesTableCreateCompanionBuilder =
    LogEntriesCompanion Function({
      Value<int> id,
      required DateTime createdAt,
      required double bloodSugar,
      Value<double?> insulinUnits,
      Value<String?> glycemicContext,
      Value<String?> mealType,
      Value<String?> mealDescription,
      Value<String?> mealItemsJson,
      Value<String?> mealPortionsJson,
      Value<String> source,
      Value<String> syncStatus,
      required String clientUuid,
      Value<DateTime?> loggedAt,
      Value<int?> fatigueLevel,
      Value<bool> isSick,
      Value<bool> isStressed,
      Value<bool> isTired,
      Value<bool> isActive,
      Value<bool> ramadanMode,
      Value<String?> sleepQuality,
      Value<int> syncAttempts,
      Value<bool> errorSync,
    });
typedef $$LogEntriesTableUpdateCompanionBuilder =
    LogEntriesCompanion Function({
      Value<int> id,
      Value<DateTime> createdAt,
      Value<double> bloodSugar,
      Value<double?> insulinUnits,
      Value<String?> glycemicContext,
      Value<String?> mealType,
      Value<String?> mealDescription,
      Value<String?> mealItemsJson,
      Value<String?> mealPortionsJson,
      Value<String> source,
      Value<String> syncStatus,
      Value<String> clientUuid,
      Value<DateTime?> loggedAt,
      Value<int?> fatigueLevel,
      Value<bool> isSick,
      Value<bool> isStressed,
      Value<bool> isTired,
      Value<bool> isActive,
      Value<bool> ramadanMode,
      Value<String?> sleepQuality,
      Value<int> syncAttempts,
      Value<bool> errorSync,
    });

class $$LogEntriesTableFilterComposer
    extends Composer<_$AppDatabase, $LogEntriesTable> {
  $$LogEntriesTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<double> get bloodSugar => $composableBuilder(
    column: $table.bloodSugar,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<double> get insulinUnits => $composableBuilder(
    column: $table.insulinUnits,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get glycemicContext => $composableBuilder(
    column: $table.glycemicContext,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get mealType => $composableBuilder(
    column: $table.mealType,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get mealDescription => $composableBuilder(
    column: $table.mealDescription,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get mealItemsJson => $composableBuilder(
    column: $table.mealItemsJson,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get mealPortionsJson => $composableBuilder(
    column: $table.mealPortionsJson,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get source => $composableBuilder(
    column: $table.source,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get syncStatus => $composableBuilder(
    column: $table.syncStatus,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get clientUuid => $composableBuilder(
    column: $table.clientUuid,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get loggedAt => $composableBuilder(
    column: $table.loggedAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get fatigueLevel => $composableBuilder(
    column: $table.fatigueLevel,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<bool> get isSick => $composableBuilder(
    column: $table.isSick,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<bool> get isStressed => $composableBuilder(
    column: $table.isStressed,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<bool> get isTired => $composableBuilder(
    column: $table.isTired,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<bool> get isActive => $composableBuilder(
    column: $table.isActive,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<bool> get ramadanMode => $composableBuilder(
    column: $table.ramadanMode,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get sleepQuality => $composableBuilder(
    column: $table.sleepQuality,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get syncAttempts => $composableBuilder(
    column: $table.syncAttempts,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<bool> get errorSync => $composableBuilder(
    column: $table.errorSync,
    builder: (column) => ColumnFilters(column),
  );
}

class $$LogEntriesTableOrderingComposer
    extends Composer<_$AppDatabase, $LogEntriesTable> {
  $$LogEntriesTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<double> get bloodSugar => $composableBuilder(
    column: $table.bloodSugar,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<double> get insulinUnits => $composableBuilder(
    column: $table.insulinUnits,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get glycemicContext => $composableBuilder(
    column: $table.glycemicContext,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get mealType => $composableBuilder(
    column: $table.mealType,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get mealDescription => $composableBuilder(
    column: $table.mealDescription,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get mealItemsJson => $composableBuilder(
    column: $table.mealItemsJson,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get mealPortionsJson => $composableBuilder(
    column: $table.mealPortionsJson,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get source => $composableBuilder(
    column: $table.source,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get syncStatus => $composableBuilder(
    column: $table.syncStatus,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get clientUuid => $composableBuilder(
    column: $table.clientUuid,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get loggedAt => $composableBuilder(
    column: $table.loggedAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get fatigueLevel => $composableBuilder(
    column: $table.fatigueLevel,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<bool> get isSick => $composableBuilder(
    column: $table.isSick,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<bool> get isStressed => $composableBuilder(
    column: $table.isStressed,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<bool> get isTired => $composableBuilder(
    column: $table.isTired,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<bool> get isActive => $composableBuilder(
    column: $table.isActive,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<bool> get ramadanMode => $composableBuilder(
    column: $table.ramadanMode,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get sleepQuality => $composableBuilder(
    column: $table.sleepQuality,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get syncAttempts => $composableBuilder(
    column: $table.syncAttempts,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<bool> get errorSync => $composableBuilder(
    column: $table.errorSync,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$LogEntriesTableAnnotationComposer
    extends Composer<_$AppDatabase, $LogEntriesTable> {
  $$LogEntriesTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<DateTime> get createdAt =>
      $composableBuilder(column: $table.createdAt, builder: (column) => column);

  GeneratedColumn<double> get bloodSugar => $composableBuilder(
    column: $table.bloodSugar,
    builder: (column) => column,
  );

  GeneratedColumn<double> get insulinUnits => $composableBuilder(
    column: $table.insulinUnits,
    builder: (column) => column,
  );

  GeneratedColumn<String> get glycemicContext => $composableBuilder(
    column: $table.glycemicContext,
    builder: (column) => column,
  );

  GeneratedColumn<String> get mealType =>
      $composableBuilder(column: $table.mealType, builder: (column) => column);

  GeneratedColumn<String> get mealDescription => $composableBuilder(
    column: $table.mealDescription,
    builder: (column) => column,
  );

  GeneratedColumn<String> get mealItemsJson => $composableBuilder(
    column: $table.mealItemsJson,
    builder: (column) => column,
  );

  GeneratedColumn<String> get mealPortionsJson => $composableBuilder(
    column: $table.mealPortionsJson,
    builder: (column) => column,
  );

  GeneratedColumn<String> get source =>
      $composableBuilder(column: $table.source, builder: (column) => column);

  GeneratedColumn<String> get syncStatus => $composableBuilder(
    column: $table.syncStatus,
    builder: (column) => column,
  );

  GeneratedColumn<String> get clientUuid => $composableBuilder(
    column: $table.clientUuid,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get loggedAt =>
      $composableBuilder(column: $table.loggedAt, builder: (column) => column);

  GeneratedColumn<int> get fatigueLevel => $composableBuilder(
    column: $table.fatigueLevel,
    builder: (column) => column,
  );

  GeneratedColumn<bool> get isSick =>
      $composableBuilder(column: $table.isSick, builder: (column) => column);

  GeneratedColumn<bool> get isStressed => $composableBuilder(
    column: $table.isStressed,
    builder: (column) => column,
  );

  GeneratedColumn<bool> get isTired =>
      $composableBuilder(column: $table.isTired, builder: (column) => column);

  GeneratedColumn<bool> get isActive =>
      $composableBuilder(column: $table.isActive, builder: (column) => column);

  GeneratedColumn<bool> get ramadanMode => $composableBuilder(
    column: $table.ramadanMode,
    builder: (column) => column,
  );

  GeneratedColumn<String> get sleepQuality => $composableBuilder(
    column: $table.sleepQuality,
    builder: (column) => column,
  );

  GeneratedColumn<int> get syncAttempts => $composableBuilder(
    column: $table.syncAttempts,
    builder: (column) => column,
  );

  GeneratedColumn<bool> get errorSync =>
      $composableBuilder(column: $table.errorSync, builder: (column) => column);
}

class $$LogEntriesTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $LogEntriesTable,
          LogEntryData,
          $$LogEntriesTableFilterComposer,
          $$LogEntriesTableOrderingComposer,
          $$LogEntriesTableAnnotationComposer,
          $$LogEntriesTableCreateCompanionBuilder,
          $$LogEntriesTableUpdateCompanionBuilder,
          (
            LogEntryData,
            BaseReferences<_$AppDatabase, $LogEntriesTable, LogEntryData>,
          ),
          LogEntryData,
          PrefetchHooks Function()
        > {
  $$LogEntriesTableTableManager(_$AppDatabase db, $LogEntriesTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$LogEntriesTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$LogEntriesTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$LogEntriesTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<DateTime> createdAt = const Value.absent(),
                Value<double> bloodSugar = const Value.absent(),
                Value<double?> insulinUnits = const Value.absent(),
                Value<String?> glycemicContext = const Value.absent(),
                Value<String?> mealType = const Value.absent(),
                Value<String?> mealDescription = const Value.absent(),
                Value<String?> mealItemsJson = const Value.absent(),
                Value<String?> mealPortionsJson = const Value.absent(),
                Value<String> source = const Value.absent(),
                Value<String> syncStatus = const Value.absent(),
                Value<String> clientUuid = const Value.absent(),
                Value<DateTime?> loggedAt = const Value.absent(),
                Value<int?> fatigueLevel = const Value.absent(),
                Value<bool> isSick = const Value.absent(),
                Value<bool> isStressed = const Value.absent(),
                Value<bool> isTired = const Value.absent(),
                Value<bool> isActive = const Value.absent(),
                Value<bool> ramadanMode = const Value.absent(),
                Value<String?> sleepQuality = const Value.absent(),
                Value<int> syncAttempts = const Value.absent(),
                Value<bool> errorSync = const Value.absent(),
              }) => LogEntriesCompanion(
                id: id,
                createdAt: createdAt,
                bloodSugar: bloodSugar,
                insulinUnits: insulinUnits,
                glycemicContext: glycemicContext,
                mealType: mealType,
                mealDescription: mealDescription,
                mealItemsJson: mealItemsJson,
                mealPortionsJson: mealPortionsJson,
                source: source,
                syncStatus: syncStatus,
                clientUuid: clientUuid,
                loggedAt: loggedAt,
                fatigueLevel: fatigueLevel,
                isSick: isSick,
                isStressed: isStressed,
                isTired: isTired,
                isActive: isActive,
                ramadanMode: ramadanMode,
                sleepQuality: sleepQuality,
                syncAttempts: syncAttempts,
                errorSync: errorSync,
              ),
          createCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                required DateTime createdAt,
                required double bloodSugar,
                Value<double?> insulinUnits = const Value.absent(),
                Value<String?> glycemicContext = const Value.absent(),
                Value<String?> mealType = const Value.absent(),
                Value<String?> mealDescription = const Value.absent(),
                Value<String?> mealItemsJson = const Value.absent(),
                Value<String?> mealPortionsJson = const Value.absent(),
                Value<String> source = const Value.absent(),
                Value<String> syncStatus = const Value.absent(),
                required String clientUuid,
                Value<DateTime?> loggedAt = const Value.absent(),
                Value<int?> fatigueLevel = const Value.absent(),
                Value<bool> isSick = const Value.absent(),
                Value<bool> isStressed = const Value.absent(),
                Value<bool> isTired = const Value.absent(),
                Value<bool> isActive = const Value.absent(),
                Value<bool> ramadanMode = const Value.absent(),
                Value<String?> sleepQuality = const Value.absent(),
                Value<int> syncAttempts = const Value.absent(),
                Value<bool> errorSync = const Value.absent(),
              }) => LogEntriesCompanion.insert(
                id: id,
                createdAt: createdAt,
                bloodSugar: bloodSugar,
                insulinUnits: insulinUnits,
                glycemicContext: glycemicContext,
                mealType: mealType,
                mealDescription: mealDescription,
                mealItemsJson: mealItemsJson,
                mealPortionsJson: mealPortionsJson,
                source: source,
                syncStatus: syncStatus,
                clientUuid: clientUuid,
                loggedAt: loggedAt,
                fatigueLevel: fatigueLevel,
                isSick: isSick,
                isStressed: isStressed,
                isTired: isTired,
                isActive: isActive,
                ramadanMode: ramadanMode,
                sleepQuality: sleepQuality,
                syncAttempts: syncAttempts,
                errorSync: errorSync,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$LogEntriesTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $LogEntriesTable,
      LogEntryData,
      $$LogEntriesTableFilterComposer,
      $$LogEntriesTableOrderingComposer,
      $$LogEntriesTableAnnotationComposer,
      $$LogEntriesTableCreateCompanionBuilder,
      $$LogEntriesTableUpdateCompanionBuilder,
      (
        LogEntryData,
        BaseReferences<_$AppDatabase, $LogEntriesTable, LogEntryData>,
      ),
      LogEntryData,
      PrefetchHooks Function()
    >;
typedef $$PatientProfilesTableCreateCompanionBuilder =
    PatientProfilesCompanion Function({
      Value<int> userId,
      Value<String> preferredLanguage,
      required DateTime updatedAt,
      Value<String?> diabetesType,
      Value<double> targetRangeLow,
      Value<double> targetRangeHigh,
      Value<String> unitPreference,
      Value<String?> treatment,
      Value<DateTime?> ramadanStartDate,
      Value<DateTime?> ramadanEndDate,
      Value<DateTime?> aiConsentGivenAt,
    });
typedef $$PatientProfilesTableUpdateCompanionBuilder =
    PatientProfilesCompanion Function({
      Value<int> userId,
      Value<String> preferredLanguage,
      Value<DateTime> updatedAt,
      Value<String?> diabetesType,
      Value<double> targetRangeLow,
      Value<double> targetRangeHigh,
      Value<String> unitPreference,
      Value<String?> treatment,
      Value<DateTime?> ramadanStartDate,
      Value<DateTime?> ramadanEndDate,
      Value<DateTime?> aiConsentGivenAt,
    });

class $$PatientProfilesTableFilterComposer
    extends Composer<_$AppDatabase, $PatientProfilesTable> {
  $$PatientProfilesTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get userId => $composableBuilder(
    column: $table.userId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get preferredLanguage => $composableBuilder(
    column: $table.preferredLanguage,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get updatedAt => $composableBuilder(
    column: $table.updatedAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get diabetesType => $composableBuilder(
    column: $table.diabetesType,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<double> get targetRangeLow => $composableBuilder(
    column: $table.targetRangeLow,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<double> get targetRangeHigh => $composableBuilder(
    column: $table.targetRangeHigh,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get unitPreference => $composableBuilder(
    column: $table.unitPreference,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get treatment => $composableBuilder(
    column: $table.treatment,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get ramadanStartDate => $composableBuilder(
    column: $table.ramadanStartDate,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get ramadanEndDate => $composableBuilder(
    column: $table.ramadanEndDate,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get aiConsentGivenAt => $composableBuilder(
    column: $table.aiConsentGivenAt,
    builder: (column) => ColumnFilters(column),
  );
}

class $$PatientProfilesTableOrderingComposer
    extends Composer<_$AppDatabase, $PatientProfilesTable> {
  $$PatientProfilesTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get userId => $composableBuilder(
    column: $table.userId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get preferredLanguage => $composableBuilder(
    column: $table.preferredLanguage,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get updatedAt => $composableBuilder(
    column: $table.updatedAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get diabetesType => $composableBuilder(
    column: $table.diabetesType,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<double> get targetRangeLow => $composableBuilder(
    column: $table.targetRangeLow,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<double> get targetRangeHigh => $composableBuilder(
    column: $table.targetRangeHigh,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get unitPreference => $composableBuilder(
    column: $table.unitPreference,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get treatment => $composableBuilder(
    column: $table.treatment,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get ramadanStartDate => $composableBuilder(
    column: $table.ramadanStartDate,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get ramadanEndDate => $composableBuilder(
    column: $table.ramadanEndDate,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get aiConsentGivenAt => $composableBuilder(
    column: $table.aiConsentGivenAt,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$PatientProfilesTableAnnotationComposer
    extends Composer<_$AppDatabase, $PatientProfilesTable> {
  $$PatientProfilesTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get userId =>
      $composableBuilder(column: $table.userId, builder: (column) => column);

  GeneratedColumn<String> get preferredLanguage => $composableBuilder(
    column: $table.preferredLanguage,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get updatedAt =>
      $composableBuilder(column: $table.updatedAt, builder: (column) => column);

  GeneratedColumn<String> get diabetesType => $composableBuilder(
    column: $table.diabetesType,
    builder: (column) => column,
  );

  GeneratedColumn<double> get targetRangeLow => $composableBuilder(
    column: $table.targetRangeLow,
    builder: (column) => column,
  );

  GeneratedColumn<double> get targetRangeHigh => $composableBuilder(
    column: $table.targetRangeHigh,
    builder: (column) => column,
  );

  GeneratedColumn<String> get unitPreference => $composableBuilder(
    column: $table.unitPreference,
    builder: (column) => column,
  );

  GeneratedColumn<String> get treatment =>
      $composableBuilder(column: $table.treatment, builder: (column) => column);

  GeneratedColumn<DateTime> get ramadanStartDate => $composableBuilder(
    column: $table.ramadanStartDate,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get ramadanEndDate => $composableBuilder(
    column: $table.ramadanEndDate,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get aiConsentGivenAt => $composableBuilder(
    column: $table.aiConsentGivenAt,
    builder: (column) => column,
  );
}

class $$PatientProfilesTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $PatientProfilesTable,
          PatientProfileData,
          $$PatientProfilesTableFilterComposer,
          $$PatientProfilesTableOrderingComposer,
          $$PatientProfilesTableAnnotationComposer,
          $$PatientProfilesTableCreateCompanionBuilder,
          $$PatientProfilesTableUpdateCompanionBuilder,
          (
            PatientProfileData,
            BaseReferences<
              _$AppDatabase,
              $PatientProfilesTable,
              PatientProfileData
            >,
          ),
          PatientProfileData,
          PrefetchHooks Function()
        > {
  $$PatientProfilesTableTableManager(
    _$AppDatabase db,
    $PatientProfilesTable table,
  ) : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$PatientProfilesTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$PatientProfilesTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$PatientProfilesTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<int> userId = const Value.absent(),
                Value<String> preferredLanguage = const Value.absent(),
                Value<DateTime> updatedAt = const Value.absent(),
                Value<String?> diabetesType = const Value.absent(),
                Value<double> targetRangeLow = const Value.absent(),
                Value<double> targetRangeHigh = const Value.absent(),
                Value<String> unitPreference = const Value.absent(),
                Value<String?> treatment = const Value.absent(),
                Value<DateTime?> ramadanStartDate = const Value.absent(),
                Value<DateTime?> ramadanEndDate = const Value.absent(),
                Value<DateTime?> aiConsentGivenAt = const Value.absent(),
              }) => PatientProfilesCompanion(
                userId: userId,
                preferredLanguage: preferredLanguage,
                updatedAt: updatedAt,
                diabetesType: diabetesType,
                targetRangeLow: targetRangeLow,
                targetRangeHigh: targetRangeHigh,
                unitPreference: unitPreference,
                treatment: treatment,
                ramadanStartDate: ramadanStartDate,
                ramadanEndDate: ramadanEndDate,
                aiConsentGivenAt: aiConsentGivenAt,
              ),
          createCompanionCallback:
              ({
                Value<int> userId = const Value.absent(),
                Value<String> preferredLanguage = const Value.absent(),
                required DateTime updatedAt,
                Value<String?> diabetesType = const Value.absent(),
                Value<double> targetRangeLow = const Value.absent(),
                Value<double> targetRangeHigh = const Value.absent(),
                Value<String> unitPreference = const Value.absent(),
                Value<String?> treatment = const Value.absent(),
                Value<DateTime?> ramadanStartDate = const Value.absent(),
                Value<DateTime?> ramadanEndDate = const Value.absent(),
                Value<DateTime?> aiConsentGivenAt = const Value.absent(),
              }) => PatientProfilesCompanion.insert(
                userId: userId,
                preferredLanguage: preferredLanguage,
                updatedAt: updatedAt,
                diabetesType: diabetesType,
                targetRangeLow: targetRangeLow,
                targetRangeHigh: targetRangeHigh,
                unitPreference: unitPreference,
                treatment: treatment,
                ramadanStartDate: ramadanStartDate,
                ramadanEndDate: ramadanEndDate,
                aiConsentGivenAt: aiConsentGivenAt,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$PatientProfilesTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $PatientProfilesTable,
      PatientProfileData,
      $$PatientProfilesTableFilterComposer,
      $$PatientProfilesTableOrderingComposer,
      $$PatientProfilesTableAnnotationComposer,
      $$PatientProfilesTableCreateCompanionBuilder,
      $$PatientProfilesTableUpdateCompanionBuilder,
      (
        PatientProfileData,
        BaseReferences<
          _$AppDatabase,
          $PatientProfilesTable,
          PatientProfileData
        >,
      ),
      PatientProfileData,
      PrefetchHooks Function()
    >;
typedef $$ChatMessagesTableCreateCompanionBuilder =
    ChatMessagesCompanion Function({
      Value<int> id,
      required String conversationId,
      required String role,
      required String message,
      required DateTime createdAt,
    });
typedef $$ChatMessagesTableUpdateCompanionBuilder =
    ChatMessagesCompanion Function({
      Value<int> id,
      Value<String> conversationId,
      Value<String> role,
      Value<String> message,
      Value<DateTime> createdAt,
    });

class $$ChatMessagesTableFilterComposer
    extends Composer<_$AppDatabase, $ChatMessagesTable> {
  $$ChatMessagesTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get conversationId => $composableBuilder(
    column: $table.conversationId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get role => $composableBuilder(
    column: $table.role,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get message => $composableBuilder(
    column: $table.message,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnFilters(column),
  );
}

class $$ChatMessagesTableOrderingComposer
    extends Composer<_$AppDatabase, $ChatMessagesTable> {
  $$ChatMessagesTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get conversationId => $composableBuilder(
    column: $table.conversationId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get role => $composableBuilder(
    column: $table.role,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get message => $composableBuilder(
    column: $table.message,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$ChatMessagesTableAnnotationComposer
    extends Composer<_$AppDatabase, $ChatMessagesTable> {
  $$ChatMessagesTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get conversationId => $composableBuilder(
    column: $table.conversationId,
    builder: (column) => column,
  );

  GeneratedColumn<String> get role =>
      $composableBuilder(column: $table.role, builder: (column) => column);

  GeneratedColumn<String> get message =>
      $composableBuilder(column: $table.message, builder: (column) => column);

  GeneratedColumn<DateTime> get createdAt =>
      $composableBuilder(column: $table.createdAt, builder: (column) => column);
}

class $$ChatMessagesTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $ChatMessagesTable,
          ChatMessageData,
          $$ChatMessagesTableFilterComposer,
          $$ChatMessagesTableOrderingComposer,
          $$ChatMessagesTableAnnotationComposer,
          $$ChatMessagesTableCreateCompanionBuilder,
          $$ChatMessagesTableUpdateCompanionBuilder,
          (
            ChatMessageData,
            BaseReferences<_$AppDatabase, $ChatMessagesTable, ChatMessageData>,
          ),
          ChatMessageData,
          PrefetchHooks Function()
        > {
  $$ChatMessagesTableTableManager(_$AppDatabase db, $ChatMessagesTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$ChatMessagesTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$ChatMessagesTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$ChatMessagesTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<String> conversationId = const Value.absent(),
                Value<String> role = const Value.absent(),
                Value<String> message = const Value.absent(),
                Value<DateTime> createdAt = const Value.absent(),
              }) => ChatMessagesCompanion(
                id: id,
                conversationId: conversationId,
                role: role,
                message: message,
                createdAt: createdAt,
              ),
          createCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                required String conversationId,
                required String role,
                required String message,
                required DateTime createdAt,
              }) => ChatMessagesCompanion.insert(
                id: id,
                conversationId: conversationId,
                role: role,
                message: message,
                createdAt: createdAt,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$ChatMessagesTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $ChatMessagesTable,
      ChatMessageData,
      $$ChatMessagesTableFilterComposer,
      $$ChatMessagesTableOrderingComposer,
      $$ChatMessagesTableAnnotationComposer,
      $$ChatMessagesTableCreateCompanionBuilder,
      $$ChatMessagesTableUpdateCompanionBuilder,
      (
        ChatMessageData,
        BaseReferences<_$AppDatabase, $ChatMessagesTable, ChatMessageData>,
      ),
      ChatMessageData,
      PrefetchHooks Function()
    >;
typedef $$MedicationEventsTableCreateCompanionBuilder =
    MedicationEventsCompanion Function({
      Value<int> id,
      required String label,
      Value<double?> dose,
      Value<String?> unit,
      required DateTime takenAt,
      required DateTime createdAt,
    });
typedef $$MedicationEventsTableUpdateCompanionBuilder =
    MedicationEventsCompanion Function({
      Value<int> id,
      Value<String> label,
      Value<double?> dose,
      Value<String?> unit,
      Value<DateTime> takenAt,
      Value<DateTime> createdAt,
    });

class $$MedicationEventsTableFilterComposer
    extends Composer<_$AppDatabase, $MedicationEventsTable> {
  $$MedicationEventsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get label => $composableBuilder(
    column: $table.label,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<double> get dose => $composableBuilder(
    column: $table.dose,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get unit => $composableBuilder(
    column: $table.unit,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get takenAt => $composableBuilder(
    column: $table.takenAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnFilters(column),
  );
}

class $$MedicationEventsTableOrderingComposer
    extends Composer<_$AppDatabase, $MedicationEventsTable> {
  $$MedicationEventsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get label => $composableBuilder(
    column: $table.label,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<double> get dose => $composableBuilder(
    column: $table.dose,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get unit => $composableBuilder(
    column: $table.unit,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get takenAt => $composableBuilder(
    column: $table.takenAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$MedicationEventsTableAnnotationComposer
    extends Composer<_$AppDatabase, $MedicationEventsTable> {
  $$MedicationEventsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get label =>
      $composableBuilder(column: $table.label, builder: (column) => column);

  GeneratedColumn<double> get dose =>
      $composableBuilder(column: $table.dose, builder: (column) => column);

  GeneratedColumn<String> get unit =>
      $composableBuilder(column: $table.unit, builder: (column) => column);

  GeneratedColumn<DateTime> get takenAt =>
      $composableBuilder(column: $table.takenAt, builder: (column) => column);

  GeneratedColumn<DateTime> get createdAt =>
      $composableBuilder(column: $table.createdAt, builder: (column) => column);
}

class $$MedicationEventsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $MedicationEventsTable,
          MedicationEventData,
          $$MedicationEventsTableFilterComposer,
          $$MedicationEventsTableOrderingComposer,
          $$MedicationEventsTableAnnotationComposer,
          $$MedicationEventsTableCreateCompanionBuilder,
          $$MedicationEventsTableUpdateCompanionBuilder,
          (
            MedicationEventData,
            BaseReferences<
              _$AppDatabase,
              $MedicationEventsTable,
              MedicationEventData
            >,
          ),
          MedicationEventData,
          PrefetchHooks Function()
        > {
  $$MedicationEventsTableTableManager(
    _$AppDatabase db,
    $MedicationEventsTable table,
  ) : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$MedicationEventsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$MedicationEventsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$MedicationEventsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<String> label = const Value.absent(),
                Value<double?> dose = const Value.absent(),
                Value<String?> unit = const Value.absent(),
                Value<DateTime> takenAt = const Value.absent(),
                Value<DateTime> createdAt = const Value.absent(),
              }) => MedicationEventsCompanion(
                id: id,
                label: label,
                dose: dose,
                unit: unit,
                takenAt: takenAt,
                createdAt: createdAt,
              ),
          createCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                required String label,
                Value<double?> dose = const Value.absent(),
                Value<String?> unit = const Value.absent(),
                required DateTime takenAt,
                required DateTime createdAt,
              }) => MedicationEventsCompanion.insert(
                id: id,
                label: label,
                dose: dose,
                unit: unit,
                takenAt: takenAt,
                createdAt: createdAt,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$MedicationEventsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $MedicationEventsTable,
      MedicationEventData,
      $$MedicationEventsTableFilterComposer,
      $$MedicationEventsTableOrderingComposer,
      $$MedicationEventsTableAnnotationComposer,
      $$MedicationEventsTableCreateCompanionBuilder,
      $$MedicationEventsTableUpdateCompanionBuilder,
      (
        MedicationEventData,
        BaseReferences<
          _$AppDatabase,
          $MedicationEventsTable,
          MedicationEventData
        >,
      ),
      MedicationEventData,
      PrefetchHooks Function()
    >;
typedef $$RemindersTableCreateCompanionBuilder =
    RemindersCompanion Function({
      Value<int> id,
      required String title,
      required DateTime dueAt,
      Value<bool> enabled,
      required DateTime createdAt,
    });
typedef $$RemindersTableUpdateCompanionBuilder =
    RemindersCompanion Function({
      Value<int> id,
      Value<String> title,
      Value<DateTime> dueAt,
      Value<bool> enabled,
      Value<DateTime> createdAt,
    });

class $$RemindersTableFilterComposer
    extends Composer<_$AppDatabase, $RemindersTable> {
  $$RemindersTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get title => $composableBuilder(
    column: $table.title,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get dueAt => $composableBuilder(
    column: $table.dueAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<bool> get enabled => $composableBuilder(
    column: $table.enabled,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnFilters(column),
  );
}

class $$RemindersTableOrderingComposer
    extends Composer<_$AppDatabase, $RemindersTable> {
  $$RemindersTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get title => $composableBuilder(
    column: $table.title,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get dueAt => $composableBuilder(
    column: $table.dueAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<bool> get enabled => $composableBuilder(
    column: $table.enabled,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$RemindersTableAnnotationComposer
    extends Composer<_$AppDatabase, $RemindersTable> {
  $$RemindersTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get title =>
      $composableBuilder(column: $table.title, builder: (column) => column);

  GeneratedColumn<DateTime> get dueAt =>
      $composableBuilder(column: $table.dueAt, builder: (column) => column);

  GeneratedColumn<bool> get enabled =>
      $composableBuilder(column: $table.enabled, builder: (column) => column);

  GeneratedColumn<DateTime> get createdAt =>
      $composableBuilder(column: $table.createdAt, builder: (column) => column);
}

class $$RemindersTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $RemindersTable,
          ReminderData,
          $$RemindersTableFilterComposer,
          $$RemindersTableOrderingComposer,
          $$RemindersTableAnnotationComposer,
          $$RemindersTableCreateCompanionBuilder,
          $$RemindersTableUpdateCompanionBuilder,
          (
            ReminderData,
            BaseReferences<_$AppDatabase, $RemindersTable, ReminderData>,
          ),
          ReminderData,
          PrefetchHooks Function()
        > {
  $$RemindersTableTableManager(_$AppDatabase db, $RemindersTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$RemindersTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$RemindersTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$RemindersTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<String> title = const Value.absent(),
                Value<DateTime> dueAt = const Value.absent(),
                Value<bool> enabled = const Value.absent(),
                Value<DateTime> createdAt = const Value.absent(),
              }) => RemindersCompanion(
                id: id,
                title: title,
                dueAt: dueAt,
                enabled: enabled,
                createdAt: createdAt,
              ),
          createCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                required String title,
                required DateTime dueAt,
                Value<bool> enabled = const Value.absent(),
                required DateTime createdAt,
              }) => RemindersCompanion.insert(
                id: id,
                title: title,
                dueAt: dueAt,
                enabled: enabled,
                createdAt: createdAt,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$RemindersTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $RemindersTable,
      ReminderData,
      $$RemindersTableFilterComposer,
      $$RemindersTableOrderingComposer,
      $$RemindersTableAnnotationComposer,
      $$RemindersTableCreateCompanionBuilder,
      $$RemindersTableUpdateCompanionBuilder,
      (
        ReminderData,
        BaseReferences<_$AppDatabase, $RemindersTable, ReminderData>,
      ),
      ReminderData,
      PrefetchHooks Function()
    >;

class $AppDatabaseManager {
  final _$AppDatabase _db;
  $AppDatabaseManager(this._db);
  $$LogEntriesTableTableManager get logEntries =>
      $$LogEntriesTableTableManager(_db, _db.logEntries);
  $$PatientProfilesTableTableManager get patientProfiles =>
      $$PatientProfilesTableTableManager(_db, _db.patientProfiles);
  $$ChatMessagesTableTableManager get chatMessages =>
      $$ChatMessagesTableTableManager(_db, _db.chatMessages);
  $$MedicationEventsTableTableManager get medicationEvents =>
      $$MedicationEventsTableTableManager(_db, _db.medicationEvents);
  $$RemindersTableTableManager get reminders =>
      $$RemindersTableTableManager(_db, _db.reminders);
}
