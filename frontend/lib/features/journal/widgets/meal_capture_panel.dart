import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';

import '../../../core/data/meal_food_catalog.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/drift/database.dart';
import '../../../data/models/ai_models.dart';
import '../../../l10n/app_localizations.dart';
import '../../../services/api_client.dart';

typedef MealPhotoRecognition = Future<MealAnalysisResult?> Function();

class MealCapturePanel extends StatefulWidget {
  final List<String> selectedIds;
  final ValueChanged<List<String>> onChanged;
  final bool canUsePhotoRecognition;
  final MealPhotoRecognition? photoRecognition;

  const MealCapturePanel({
    super.key,
    required this.selectedIds,
    required this.onChanged,
    required this.canUsePhotoRecognition,
    this.photoRecognition,
  });

  @override
  State<MealCapturePanel> createState() => _MealCapturePanelState();
}

class _MealCapturePanelState extends State<MealCapturePanel> {
  final _searchController = TextEditingController();
  String _query = '';
  bool _recognizing = false;
  List<MealFoodItem> _photoCandidates = const <MealFoodItem>[];
  final Set<String> _proposalSelection = <String>{};
  Future<List<LogEntryData>>? _historyFuture;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _historyFuture ??= context.read<AppDatabase>().getRecentLogs(limit: 100);
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _toggleItem(String id) {
    final next = widget.selectedIds.toSet();
    if (!next.add(id)) next.remove(id);
    widget.onChanged(next.toList(growable: false));
  }

  Future<MealAnalysisResult?> _pickAndRecognize() async {
    final file = await ImagePicker().pickImage(
      source: ImageSource.gallery,
      imageQuality: 85,
      maxWidth: 1600,
    );
    if (file == null) return null;
    final bytes = await file.readAsBytes();
    final lower = file.name.toLowerCase();
    final mime = lower.endsWith('.png')
        ? 'image/png'
        : lower.endsWith('.webp')
        ? 'image/webp'
        : 'image/jpeg';
    return ApiClient().analyzeMealImage(bytes, mimeType: mime);
  }

  Future<void> _recognizePhoto(AppLocalizations l10n) async {
    if (!widget.canUsePhotoRecognition) {
      _message(l10n.journalMealPhotoConsent);
      return;
    }
    setState(() => _recognizing = true);
    try {
      final result = await (widget.photoRecognition ?? _pickAndRecognize)();
      if (!mounted) return;
      if (result == null || result.fallback || result.foods.isEmpty) {
        setState(() {
          _photoCandidates = const <MealFoodItem>[];
          _proposalSelection.clear();
        });
        _message(l10n.journalMealPhotoUnavailable);
        return;
      }
      final matches = matchRecognizedMealFoods(result.foods);
      setState(() {
        _photoCandidates = matches;
        _proposalSelection.clear();
      });
      if (matches.isEmpty) _message(l10n.journalMealPhotoUnavailable);
    } finally {
      if (mounted) setState(() => _recognizing = false);
    }
  }

  void _confirmProposal() {
    if (_proposalSelection.isEmpty) return;
    final next = <String>{...widget.selectedIds, ..._proposalSelection};
    widget.onChanged(next.toList(growable: false));
    setState(() {
      _photoCandidates = const <MealFoodItem>[];
      _proposalSelection.clear();
    });
  }

  void _message(String text) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(text), behavior: SnackBarBehavior.floating),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final locale = Localizations.localeOf(context);
    final selected = widget.selectedIds
        .map(mealFoodById)
        .whereType<MealFoodItem>()
        .toList(growable: false);
    final results = searchMealFoods(_query);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        Text(
          l10n.journalMealCaptureTitle,
          style: TextStyle(
            color: AminaTheme.textSecondary(context),
            fontSize: 11,
            fontWeight: FontWeight.w800,
            letterSpacing: .55,
          ),
        ),
        const SizedBox(height: 5),
        Text(
          l10n.journalMealCaptureHint,
          style: TextStyle(
            color: AminaTheme.textSecondary(context),
            fontSize: 12,
            height: 1.4,
          ),
        ),
        if (selected.isNotEmpty) ...<Widget>[
          const SizedBox(height: 12),
          _subhead(l10n.journalMealSelected),
          const SizedBox(height: 7),
          Wrap(
            spacing: 7,
            runSpacing: 7,
            children: selected
                .map(
                  (item) => InputChip(
                    key: Key('meal-selected-${item.id}'),
                    label: Text(item.labelFor(locale)),
                    onDeleted: () => _toggleItem(item.id),
                  ),
                )
                .toList(),
          ),
        ],
        const SizedBox(height: 14),
        FutureBuilder<List<LogEntryData>>(
          future: _historyFuture,
          builder: (context, snapshot) {
            final logs = snapshot.data ?? const <LogEntryData>[];
            final recent = _recentItems(logs);
            final habitual = _habitualItems(logs);
            if (recent.isEmpty && habitual.isEmpty) {
              return const SizedBox.shrink();
            }
            return Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                if (recent.isNotEmpty)
                  _historySection(
                    title: l10n.journalMealRecent,
                    empty: l10n.journalMealNoRecent,
                    items: recent,
                    locale: locale,
                  ),
                if (recent.isNotEmpty && habitual.isNotEmpty)
                  const SizedBox(height: 12),
                if (habitual.isNotEmpty)
                  _historySection(
                    title: l10n.journalMealHabitual,
                    empty: l10n.journalMealNoHabitual,
                    items: habitual,
                    locale: locale,
                  ),
              ],
            );
          },
        ),
        const SizedBox(height: 14),
        TextField(
          key: const Key('meal-food-search'),
          controller: _searchController,
          onChanged: (value) => setState(() => _query = value),
          decoration: InputDecoration(
            labelText: l10n.journalMealSearch,
            hintText: l10n.journalMealSearchHint,
            prefixIcon: const Icon(Icons.search_rounded),
            border: const OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 8),
        if (foldMealText(_query).length < 2)
          Text(
            l10n.journalMealSearchEmpty,
            style: TextStyle(
              color: AminaTheme.textSecondary(context),
              fontSize: 11,
            ),
          )
        else
          Wrap(
            spacing: 7,
            runSpacing: 7,
            children: results
                .map(
                  (item) => FilterChip(
                    key: Key('meal-search-${item.id}'),
                    label: Text(item.labelFor(locale)),
                    selected: widget.selectedIds.contains(item.id),
                    onSelected: (_) => _toggleItem(item.id),
                  ),
                )
                .toList(),
          ),
        const SizedBox(height: 16),
        OutlinedButton.icon(
          key: const Key('meal-photo-button'),
          onPressed: _recognizing ? null : () => _recognizePhoto(l10n),
          icon: _recognizing
              ? const SizedBox.square(
                  dimension: 18,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.add_a_photo_outlined, size: 18),
          label: Text(l10n.journalMealPhoto),
          style: OutlinedButton.styleFrom(
            minimumSize: const Size.fromHeight(48),
            alignment: AlignmentDirectional.centerStart,
          ),
        ),
        const SizedBox(height: 6),
        Text(
          l10n.journalMealPhotoHint,
          style: TextStyle(
            color: AminaTheme.textSecondary(context),
            fontSize: 11,
            height: 1.35,
          ),
        ),
        if (_photoCandidates.isNotEmpty) ...<Widget>[
          const SizedBox(height: 14),
          Container(
            key: const Key('meal-photo-proposal'),
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AminaTheme.bg(context),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: AminaTheme.divider(context)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                _subhead(l10n.journalMealPhotoProposal),
                const SizedBox(height: 4),
                Text(
                  l10n.journalMealPhotoProposalHint,
                  style: TextStyle(
                    color: AminaTheme.textSecondary(context),
                    fontSize: 11,
                    height: 1.35,
                  ),
                ),
                const SizedBox(height: 10),
                Wrap(
                  spacing: 7,
                  runSpacing: 7,
                  children: _photoCandidates
                      .map(
                        (item) => FilterChip(
                          key: Key('meal-photo-candidate-${item.id}'),
                          label: Text(item.labelFor(locale)),
                          selected: _proposalSelection.contains(item.id),
                          onSelected: (value) => setState(() {
                            if (value) {
                              _proposalSelection.add(item.id);
                            } else {
                              _proposalSelection.remove(item.id);
                            }
                          }),
                        ),
                      )
                      .toList(),
                ),
                const SizedBox(height: 10),
                FilledButton(
                  key: const Key('meal-photo-confirm'),
                  onPressed: _proposalSelection.isEmpty
                      ? null
                      : _confirmProposal,
                  child: Text(l10n.journalMealPhotoConfirm),
                ),
              ],
            ),
          ),
        ],
      ],
    );
  }

  Widget _subhead(String text) => Text(
    text,
    style: TextStyle(
      color: AminaTheme.textPrimary(context),
      fontSize: 12,
      fontWeight: FontWeight.w700,
    ),
  );

  Widget _historySection({
    required String title,
    required String empty,
    required List<MealFoodItem> items,
    required Locale locale,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        _subhead(title),
        const SizedBox(height: 6),
        if (items.isEmpty)
          Text(
            empty,
            style: TextStyle(
              color: AminaTheme.textSecondary(context),
              fontSize: 11,
            ),
          )
        else
          Wrap(
            spacing: 7,
            runSpacing: 7,
            children: items
                .map(
                  (item) => FilterChip(
                    key: Key('meal-history-${item.id}'),
                    label: Text(item.labelFor(locale)),
                    selected: widget.selectedIds.contains(item.id),
                    onSelected: (_) => _toggleItem(item.id),
                  ),
                )
                .toList(),
          ),
      ],
    );
  }

  List<MealFoodItem> _recentItems(List<LogEntryData> logs) {
    final ids = <String>[];
    for (final log in logs) {
      for (final id in decodeMealItemIds(log.mealItemsJson)) {
        if (!ids.contains(id)) ids.add(id);
        if (ids.length >= 6) break;
      }
      if (ids.length >= 6) break;
    }
    return ids.map(mealFoodById).whereType<MealFoodItem>().toList();
  }

  List<MealFoodItem> _habitualItems(List<LogEntryData> logs) {
    final counts = <String, int>{};
    final recency = <String, int>{};
    for (var index = 0; index < logs.length; index++) {
      for (final id in decodeMealItemIds(logs[index].mealItemsJson)) {
        counts[id] = (counts[id] ?? 0) + 1;
        recency.putIfAbsent(id, () => index);
      }
    }
    final ids = counts.keys.where((id) => counts[id]! >= 2).toList()
      ..sort((a, b) {
        final count = counts[b]!.compareTo(counts[a]!);
        if (count != 0) return count;
        return recency[a]!.compareTo(recency[b]!);
      });
    return ids.take(6).map(mealFoodById).whereType<MealFoodItem>().toList();
  }
}
