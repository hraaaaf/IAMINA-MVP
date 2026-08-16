import 'package:flutter/material.dart';
import 'package:amina/l10n/app_localizations.dart';

import '../../core/localization/import_localized_copy.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/clinical_card.dart';
import '../../services/cgm_service.dart';

class CgmConnectionsSection extends StatefulWidget {
  final CgmService? service;

  const CgmConnectionsSection({super.key, this.service});

  @override
  State<CgmConnectionsSection> createState() => _CgmConnectionsSectionState();
}

class _CgmConnectionsSectionState extends State<CgmConnectionsSection> {
  late final CgmService _service = widget.service ?? CgmService();
  CgmConnectionState _connection = const CgmConnectionState(connected: false);
  List<CgmReadingView> _readings = const [];
  bool _loading = true;
  bool _syncing = false;
  String? _error;

  static const _sources = <_CgmSourcePresentation>[
    _CgmSourcePresentation(id: 'dexcom', title: 'Dexcom G6/G7', icon: Icons.bluetooth),
    _CgmSourcePresentation(id: 'libre', title: 'FreeStyle Libre', icon: Icons.sensors),
    _CgmSourcePresentation(
      id: 'linx',
      title: 'LinX / AiDEX X',
      icon: Icons.monitor_heart_outlined,
    ),
  ];

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    if (widget.service == null) _service.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    if (mounted) {
      setState(() {
        _loading = true;
        _error = null;
      });
    }
    try {
      final connection = await _service.getConnection();
      List<CgmReadingView> readings = const [];
      String? readError;
      if (connection.connected) {
        try {
          readings = await _service.getReadings(hours: 24);
        } catch (_) {
          readError = AppLocalizations.of(context)!.cgmUnavailable;
        }
      }
      if (!mounted) return;
      setState(() {
        _connection = connection;
        _readings = readings;
        _error = readError;
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = AppLocalizations.of(context)!.cgmUnavailable;
      });
    }
  }

  Future<void> _sync() async {
    if (_syncing) return;
    setState(() {
      _syncing = true;
      _error = null;
    });
    try {
      await _service.sync();
      await _load();
      if (!mounted) return;
      setState(() => _syncing = false);
      _showMessage(AppLocalizations.of(context)!.cgmSyncComplete);
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _syncing = false;
        _error = AppLocalizations.of(context)!.cgmUnavailable;
      });
    }
  }

  Future<void> _disconnect() async {
    final l10n = AppLocalizations.of(context)!;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(l10n.cgmDisconnect),
        content: Text(l10n.cgmDisconnectConfirm),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text(l10n.cgmCancel),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text(l10n.cgmDisconnect),
          ),
        ],
      ),
    );
    if (confirmed != true) return;

    try {
      await _service.disconnect();
      if (!mounted) return;
      setState(() {
        _connection = const CgmConnectionState(connected: false);
        _readings = const [];
        _error = null;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _error = l10n.cgmUnavailable);
    }
  }

  Future<void> _configure(_CgmSourcePresentation source) async {
    final result = await showDialog<_CgmConfiguration>(
      context: context,
      builder: (context) => _CgmConfigurationDialog(source: source),
    );
    if (result == null) return;

    setState(() {
      _loading = true;
      _error = null;
    });

    CgmConnectionState saved;
    try {
      saved = await _service.configure(
        source: source.id,
        nightscoutUrl: result.url,
        authType: result.authType,
        credential: result.credential,
      );
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = AppLocalizations.of(context)!.cgmUnavailable;
      });
      return;
    }

    if (!mounted) return;
    setState(() {
      _connection = saved;
      _readings = const [];
      _loading = false;
    });
    _showMessage(AppLocalizations.of(context)!.cgmSaved);

    try {
      await _service.sync();
      await _load();
    } catch (_) {
      if (!mounted) return;
      setState(() => _error = AppLocalizations.of(context)!.cgmUnavailable);
    }
  }

  void _showMessage(String message) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
  }

  String _relative(DateTime value, AppLocalizations l10n) {
    final diff = DateTime.now().difference(value);
    if (diff.inMinutes < 1) return l10n.justNowRelative;
    if (diff.inMinutes < 60) return l10n.minutesAgoRelative(diff.inMinutes);
    if (diff.inHours < 24) return l10n.hoursAgoRelative(diff.inHours);
    return l10n.daysAgoRelative(diff.inDays);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    if (_loading) {
      return Semantics(
        liveRegion: true,
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 16),
          child: Row(
            children: [
              const SizedBox(
                width: 18,
                height: 18,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
              const SizedBox(width: 10),
              Text(l10n.cgmLoading),
            ],
          ),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          l10n.cgmOneConnectionNote,
          style: const TextStyle(fontSize: 12, height: 1.4, color: AminaTheme.ink500),
        ),
        if (_error != null) ...[
          const SizedBox(height: 10),
          Semantics(
            liveRegion: true,
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AminaTheme.ink50,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AminaTheme.ink200),
              ),
              child: Text(
                _error!,
                style: const TextStyle(fontSize: 12, color: AminaTheme.ink700),
              ),
            ),
          ),
        ],
        const SizedBox(height: 12),
        LayoutBuilder(
          builder: (context, constraints) {
            final cards = _sources
                .map((source) => _buildSourceCard(source, l10n))
                .toList(growable: false);
            if (constraints.maxWidth >= 900) {
              return Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  for (var i = 0; i < cards.length; i++) ...[
                    if (i > 0) const SizedBox(width: 16),
                    Expanded(child: cards[i]),
                  ],
                ],
              );
            }
            return Column(
              children: [
                for (var i = 0; i < cards.length; i++) ...[
                  if (i > 0) const SizedBox(height: 12),
                  cards[i],
                ],
              ],
            );
          },
        ),
      ],
    );
  }

  Widget _buildSourceCard(_CgmSourcePresentation source, AppLocalizations l10n) {
    final connected = _connection.connected && _connection.source == source.id;
    final latest = connected && _readings.isNotEmpty ? _readings.last : null;
    final subtitle = source.id == 'linx' ? l10n.cgmLinxBridge : l10n.cgmCompatibleBridge;

    return ClinicalCard(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  color: AminaTheme.teal50,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(source.icon, size: 18, color: AminaTheme.teal600),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      source.title,
                      style: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                        color: AminaTheme.ink900,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      subtitle,
                      style: const TextStyle(fontSize: 11, height: 1.35, color: AminaTheme.ink500),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              _CgmBadge(
                label: connected ? l10n.cgmConnected : l10n.cgmViaNightscout,
                connected: connected,
              ),
            ],
          ),
          const SizedBox(height: 14),
          if (connected) ...[
            if (latest != null)
              Semantics(
                label: '${l10n.cgmLatestReading}: ${latest.glucoseMgDl} mg/dL ${latest.trend}',
                child: Row(
                  children: [
                    Text(
                      '${latest.glucoseMgDl}',
                      style: const TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.w800,
                        color: AminaTheme.ink900,
                      ),
                    ),
                    const SizedBox(width: 5),
                    const Text('mg/dL', style: TextStyle(fontSize: 11, color: AminaTheme.ink500)),
                    if (latest.trend.isNotEmpty) ...[
                      const SizedBox(width: 10),
                      Flexible(
                        child: Text(
                          latest.trend,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                            color: AminaTheme.teal700,
                          ),
                        ),
                      ),
                    ],
                    const Spacer(),
                    Text(
                      _relative(latest.recordedAt, l10n),
                      style: const TextStyle(fontSize: 11, color: AminaTheme.ink500),
                    ),
                  ],
                ),
              )
            else
              Text(l10n.cgmNoReading, style: const TextStyle(fontSize: 12, color: AminaTheme.ink500)),
            const SizedBox(height: 8),
            Text(
              '${l10n.cgmLastSync}: ${_connection.lastSuccessAt != null ? _relative(_connection.lastSuccessAt!, l10n) : l10n.cgmNeverSynced}',
              style: const TextStyle(fontSize: 11, color: AminaTheme.ink500),
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                FilledButton.icon(
                  onPressed: _syncing ? null : _sync,
                  icon: _syncing
                      ? const SizedBox(
                          width: 14,
                          height: 14,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.sync, size: 16),
                  label: Text(l10n.cgmSync),
                ),
                TextButton(onPressed: _disconnect, child: Text(l10n.cgmDisconnect)),
              ],
            ),
          ] else ...[
            Text(l10n.cgmNoConnection, style: const TextStyle(fontSize: 12, color: AminaTheme.ink500)),
            const SizedBox(height: 10),
            OutlinedButton(
              onPressed: () => _configure(source),
              child: Text(l10n.cgmConfigure),
            ),
          ],
        ],
      ),
    );
  }
}

class _CgmBadge extends StatelessWidget {
  final String label;
  final bool connected;

  const _CgmBadge({required this.label, required this.connected});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: connected ? AminaTheme.teal50 : AminaTheme.ink50,
        borderRadius: BorderRadius.circular(99),
        border: Border.all(color: connected ? AminaTheme.teal100 : AminaTheme.ink200),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 9,
          fontWeight: FontWeight.w800,
          color: connected ? AminaTheme.teal700 : AminaTheme.ink500,
        ),
      ),
    );
  }
}

class _CgmConfigurationDialog extends StatefulWidget {
  final _CgmSourcePresentation source;

  const _CgmConfigurationDialog({required this.source});

  @override
  State<_CgmConfigurationDialog> createState() => _CgmConfigurationDialogState();
}

class _CgmConfigurationDialogState extends State<_CgmConfigurationDialog> {
  final _url = TextEditingController();
  final _credential = TextEditingController();
  String _authType = 'bearer';
  bool _obscure = true;

  @override
  void dispose() {
    _url.dispose();
    _credential.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final canSave = _url.text.trim().isNotEmpty && _credential.text.trim().isNotEmpty;
    return AlertDialog(
      title: Text('${l10n.cgmConfigTitle} — ${widget.source.title}'),
      content: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 480),
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextField(
                controller: _url,
                keyboardType: TextInputType.url,
                autocorrect: false,
                decoration: InputDecoration(labelText: l10n.cgmNightscoutUrl, hintText: 'https://…'),
                onChanged: (_) => setState(() {}),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                value: _authType,
                decoration: InputDecoration(labelText: l10n.cgmAuthentication),
                items: [
                  DropdownMenuItem(value: 'bearer', child: Text(l10n.cgmBearerToken)),
                  DropdownMenuItem(value: 'api_secret', child: Text(l10n.cgmApiSecret)),
                ],
                onChanged: (value) {
                  if (value != null) setState(() => _authType = value);
                },
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _credential,
                obscureText: _obscure,
                autocorrect: false,
                enableSuggestions: false,
                decoration: InputDecoration(
                  labelText: l10n.cgmSecret,
                  suffixIcon: IconButton(
                    onPressed: () => setState(() => _obscure = !_obscure),
                    icon: Icon(_obscure ? Icons.visibility : Icons.visibility_off),
                  ),
                ),
                onChanged: (_) => setState(() {}),
              ),
              const SizedBox(height: 14),
              Text(
                l10n.cgmBridgeDisclosure,
                style: const TextStyle(fontSize: 12, height: 1.4, color: AminaTheme.ink500),
              ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: Text(l10n.cgmCancel)),
        FilledButton(
          onPressed: canSave
              ? () => Navigator.pop(
                    context,
                    _CgmConfiguration(
                      url: _url.text.trim(),
                      authType: _authType,
                      credential: _credential.text,
                    ),
                  )
              : null,
          child: Text(l10n.cgmSave),
        ),
      ],
    );
  }
}

class _CgmSourcePresentation {
  final String id;
  final String title;
  final IconData icon;

  const _CgmSourcePresentation({required this.id, required this.title, required this.icon});
}

class _CgmConfiguration {
  final String url;
  final String authType;
  final String credential;

  const _CgmConfiguration({
    required this.url,
    required this.authType,
    required this.credential,
  });
}
