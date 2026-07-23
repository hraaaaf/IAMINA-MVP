// GENERATED CODE - DO NOT MODIFY BY HAND
// dart format width=80

part of 'schema.swagger.dart';

// **************************************************************************
// ChopperGenerator
// **************************************************************************

// coverage:ignore-file
// ignore_for_file: type=lint
final class _$Schema extends Schema {
  _$Schema([ChopperClient? client]) {
    if (client == null) return;
    this.client = client;
  }

  @override
  final Type definitionType = Schema;

  @override
  Future<Response<List<LogEntrySchema>>> _apiV1LogsGet({
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
  }) {
    final Uri $url = Uri.parse('/api/v1/logs');
    final Request $request = Request(
      'GET',
      $url,
      client.baseUrl,
      tag: swaggerMetaData,
    );
    return client.send<List<LogEntrySchema>, LogEntrySchema>($request);
  }

  @override
  Future<Response<LogEntrySchema>> _apiV1LogsPost({
    required LogEntryCreateSchema? body,
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
  }) {
    final Uri $url = Uri.parse('/api/v1/logs');
    final $body = body;
    final Request $request = Request(
      'POST',
      $url,
      client.baseUrl,
      body: $body,
      tag: swaggerMetaData,
    );
    return client.send<LogEntrySchema, LogEntrySchema>($request);
  }

  @override
  Future<Response<LogEntrySchema>> _apiV1LogsLogIdGet({
    required int? logId,
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
  }) {
    final Uri $url = Uri.parse('/api/v1/logs/${logId}');
    final Request $request = Request(
      'GET',
      $url,
      client.baseUrl,
      tag: swaggerMetaData,
    );
    return client.send<LogEntrySchema, LogEntrySchema>($request);
  }

  @override
  Future<Response<dynamic>> _apiV1LogsLogIdDelete({
    required int? logId,
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
  }) {
    final Uri $url = Uri.parse('/api/v1/logs/${logId}');
    final Request $request = Request(
      'DELETE',
      $url,
      client.baseUrl,
      tag: swaggerMetaData,
    );
    return client.send<dynamic, dynamic>($request);
  }

  @override
  Future<Response<PatientProfileSchema>> _apiV1ProfileGet({
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
  }) {
    final Uri $url = Uri.parse('/api/v1/profile');
    final Request $request = Request(
      'GET',
      $url,
      client.baseUrl,
      tag: swaggerMetaData,
    );
    return client.send<PatientProfileSchema, PatientProfileSchema>($request);
  }

  @override
  Future<Response<SummaryResponse>> _apiV1AiSummaryPost({
    required SummaryRequest? body,
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
  }) {
    final Uri $url = Uri.parse('/api/v1/ai/summary');
    final $body = body;
    final Request $request = Request(
      'POST',
      $url,
      client.baseUrl,
      body: $body,
      tag: swaggerMetaData,
    );
    return client.send<SummaryResponse, SummaryResponse>($request);
  }

  @override
  Future<Response<ChatResponse>> _apiV1AiChatPost({
    required ChatRequest? body,
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
  }) {
    final Uri $url = Uri.parse('/api/v1/ai/chat');
    final $body = body;
    final Request $request = Request(
      'POST',
      $url,
      client.baseUrl,
      body: $body,
      tag: swaggerMetaData,
    );
    return client.send<ChatResponse, ChatResponse>($request);
  }
}
