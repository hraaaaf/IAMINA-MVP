// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element_parameter

import 'package:json_annotation/json_annotation.dart';
import 'package:json_annotation/json_annotation.dart' as json;
import 'package:collection/collection.dart';
import 'dart:convert';

import 'schema.models.swagger.dart';
import 'package:chopper/chopper.dart';

import 'client_mapping.dart';
import 'dart:async';
import 'package:http/http.dart' as http;
import 'package:http/http.dart' show MultipartFile;
import 'package:chopper/chopper.dart' as chopper;
import 'schema.metadata.swagger.dart';
export 'schema.models.swagger.dart';

part 'schema.swagger.chopper.dart';

// **************************************************************************
// SwaggerChopperGenerator
// **************************************************************************

@ChopperApi()
abstract class Schema extends ChopperService {
  static Schema create({
    ChopperClient? client,
    http.Client? httpClient,
    Authenticator? authenticator,
    ErrorConverter? errorConverter,
    Converter? converter,
    Uri? baseUrl,
    List<Interceptor>? interceptors,
  }) {
    if (client != null) {
      return _$Schema(client);
    }

    final newClient = ChopperClient(
      services: [_$Schema()],
      converter: converter ?? $JsonSerializableConverter(),
      interceptors: interceptors ?? [],
      client: httpClient,
      authenticator: authenticator,
      errorConverter: errorConverter,
      baseUrl: baseUrl ?? Uri.parse('http://'),
    );
    return _$Schema(newClient);
  }

  ///List Logs
  Future<chopper.Response<List<LogEntrySchema>>> apiV1LogsGet() {
    generatedMapping.putIfAbsent(
      LogEntrySchema,
      () => LogEntrySchema.fromJsonFactory,
    );

    return _apiV1LogsGet();
  }

  ///List Logs
  @GET(path: '/api/v1/logs')
  Future<chopper.Response<List<LogEntrySchema>>> _apiV1LogsGet({
    @chopper.Tag()
    SwaggerMetaData swaggerMetaData = const SwaggerMetaData(
      description: '',
      summary: 'List Logs',
      operationId: 'tracking_api_v1_logs_list_logs',
      consumes: [],
      produces: [],
      security: ["SessionAuth"],
      tags: ["logs"],
      deprecated: false,
    ),
  });

  ///Create Log
  Future<chopper.Response<LogEntrySchema>> apiV1LogsPost({
    required LogEntryCreateSchema? body,
  }) {
    generatedMapping.putIfAbsent(
      LogEntrySchema,
      () => LogEntrySchema.fromJsonFactory,
    );

    return _apiV1LogsPost(body: body);
  }

  ///Create Log
  @POST(path: '/api/v1/logs', optionalBody: true)
  Future<chopper.Response<LogEntrySchema>> _apiV1LogsPost({
    @Body() required LogEntryCreateSchema? body,
    @chopper.Tag()
    SwaggerMetaData swaggerMetaData = const SwaggerMetaData(
      description: '',
      summary: 'Create Log',
      operationId: 'tracking_api_v1_logs_create_log',
      consumes: [],
      produces: [],
      security: ["SessionAuth"],
      tags: ["logs"],
      deprecated: false,
    ),
  });

  ///Get Log
  ///@param log_id
  Future<chopper.Response<LogEntrySchema>> apiV1LogsLogIdGet({
    required int? logId,
  }) {
    generatedMapping.putIfAbsent(
      LogEntrySchema,
      () => LogEntrySchema.fromJsonFactory,
    );

    return _apiV1LogsLogIdGet(logId: logId);
  }

  ///Get Log
  ///@param log_id
  @GET(path: '/api/v1/logs/{log_id}')
  Future<chopper.Response<LogEntrySchema>> _apiV1LogsLogIdGet({
    @Path('log_id') required int? logId,
    @chopper.Tag()
    SwaggerMetaData swaggerMetaData = const SwaggerMetaData(
      description: '',
      summary: 'Get Log',
      operationId: 'tracking_api_v1_logs_get_log',
      consumes: [],
      produces: [],
      security: ["SessionAuth"],
      tags: ["logs"],
      deprecated: false,
    ),
  });

  ///Delete Log
  ///@param log_id
  Future<chopper.Response> apiV1LogsLogIdDelete({required int? logId}) {
    return _apiV1LogsLogIdDelete(logId: logId);
  }

  ///Delete Log
  ///@param log_id
  @DELETE(path: '/api/v1/logs/{log_id}')
  Future<chopper.Response> _apiV1LogsLogIdDelete({
    @Path('log_id') required int? logId,
    @chopper.Tag()
    SwaggerMetaData swaggerMetaData = const SwaggerMetaData(
      description: '',
      summary: 'Delete Log',
      operationId: 'tracking_api_v1_logs_delete_log',
      consumes: [],
      produces: [],
      security: ["SessionAuth"],
      tags: ["logs"],
      deprecated: false,
    ),
  });

  ///Get Profile
  Future<chopper.Response<PatientProfileSchema>> apiV1ProfileGet() {
    generatedMapping.putIfAbsent(
      PatientProfileSchema,
      () => PatientProfileSchema.fromJsonFactory,
    );

    return _apiV1ProfileGet();
  }

  ///Get Profile
  @GET(path: '/api/v1/profile')
  Future<chopper.Response<PatientProfileSchema>> _apiV1ProfileGet({
    @chopper.Tag()
    SwaggerMetaData swaggerMetaData = const SwaggerMetaData(
      description: '',
      summary: 'Get Profile',
      operationId: 'tracking_api_v1_profile_get_profile',
      consumes: [],
      produces: [],
      security: ["SessionAuth"],
      tags: ["profile"],
      deprecated: false,
    ),
  });

  ///Get Summary
  Future<chopper.Response<SummaryResponse>> apiV1AiSummaryPost({
    required SummaryRequest? body,
  }) {
    generatedMapping.putIfAbsent(
      SummaryResponse,
      () => SummaryResponse.fromJsonFactory,
    );

    return _apiV1AiSummaryPost(body: body);
  }

  ///Get Summary
  @POST(path: '/api/v1/ai/summary', optionalBody: true)
  Future<chopper.Response<SummaryResponse>> _apiV1AiSummaryPost({
    @Body() required SummaryRequest? body,
    @chopper.Tag()
    SwaggerMetaData swaggerMetaData = const SwaggerMetaData(
      description: '''Generate IAmina summary for a patient\'s recent logs.

Phase 2 MVP: Returns template response based on log patterns.
Phase 6: Integrates clinical_engine + LLM reformulation.''',
      summary: 'Get Summary',
      operationId: 'tracking_api_v1_ai_get_summary',
      consumes: [],
      produces: [],
      security: ["SessionAuth"],
      tags: ["ai"],
      deprecated: false,
    ),
  });

  ///Chat With Amina
  Future<chopper.Response<ChatResponse>> apiV1AiChatPost({
    required ChatRequest? body,
  }) {
    generatedMapping.putIfAbsent(
      ChatResponse,
      () => ChatResponse.fromJsonFactory,
    );

    return _apiV1AiChatPost(body: body);
  }

  ///Chat With Amina
  @POST(path: '/api/v1/ai/chat', optionalBody: true)
  Future<chopper.Response<ChatResponse>> _apiV1AiChatPost({
    @Body() required ChatRequest? body,
    @chopper.Tag()
    SwaggerMetaData swaggerMetaData = const SwaggerMetaData(
      description: '''Chat endpoint for persistent conversation with IAmina.

Phase 2 MVP: Returns template response.
Phase 6: Integrates LLM + conversation history.''',
      summary: 'Chat With Amina',
      operationId: 'tracking_api_v1_ai_chat_with_amina',
      consumes: [],
      produces: [],
      security: ["SessionAuth"],
      tags: ["ai"],
      deprecated: false,
    ),
  });
}

typedef $JsonFactory<T> = T Function(Map<String, dynamic> json);

class $CustomJsonDecoder {
  $CustomJsonDecoder(this.factories);

  final Map<Type, $JsonFactory> factories;

  dynamic decode<T>(dynamic entity) {
    if (entity is Iterable) {
      return _decodeList<T>(entity);
    }

    if (entity is T) {
      return entity;
    }

    if (isTypeOf<T, Map>()) {
      return entity;
    }

    if (isTypeOf<T, Iterable>()) {
      return entity;
    }

    if (entity is Map<String, dynamic>) {
      return _decodeMap<T>(entity);
    }

    return entity;
  }

  T _decodeMap<T>(Map<String, dynamic> values) {
    final jsonFactory = factories[T];
    if (jsonFactory == null || jsonFactory is! $JsonFactory<T>) {
      return throw "Could not find factory for type $T. Is '$T: $T.fromJsonFactory' included in the CustomJsonDecoder instance creation in bootstrapper.dart?";
    }

    return jsonFactory(values);
  }

  List<T> _decodeList<T>(Iterable values) =>
      values.where((v) => v != null).map<T>((v) => decode<T>(v) as T).toList();
}

class $JsonSerializableConverter extends chopper.JsonConverter {
  @override
  FutureOr<chopper.Response<ResultType>> convertResponse<ResultType, Item>(
    chopper.Response response,
  ) async {
    if (response.bodyString.isEmpty) {
      // In rare cases, when let's say 204 (no content) is returned -
      // we cannot decode the missing json with the result type specified
      return chopper.Response(response.base, null, error: response.error);
    }

    if (ResultType == String) {
      return response.copyWith();
    }

    if (ResultType == DateTime) {
      return response.copyWith(
        body:
            DateTime.parse((response.body as String).replaceAll('"', ''))
                as ResultType,
      );
    }

    final jsonRes = await super.convertResponse(response);
    return jsonRes.copyWith<ResultType>(
      body: $jsonDecoder.decode<Item>(jsonRes.body) as ResultType,
    );
  }
}

final $jsonDecoder = $CustomJsonDecoder(generatedMapping);
