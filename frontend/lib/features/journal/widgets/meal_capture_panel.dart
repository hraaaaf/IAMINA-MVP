import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';

import '../../../core/data/meal_food_catalog.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/drift/database.dart';
import '../../../data/models/ai_models.dart';
import '../../../l10n/app_localizations.dart';
import '../../../services/api_client.dart';
import '../../../services/meal_food_favorites_repository.dart';

typedef MealPhotoRecognition = Future<MealAnalysisResult?> Function();

class MealCapturePanel extends StatefulWidget {
  final List<String> selectedIds;
  final ValueChanged<List<String>> onChanged;
  final bool canUsePhotoRecognition;
  final MealPhotoRecognition? photoRecognition;
  final MealFoodFavoritesRepository? favoritesRepository;

  const MealCapturePanel({
    super.key,
    required this.selectedIds,
    required this.onChanged,
    required this.canUsePhotoRecognition,
    this.photoRecognition,
    this.favoritesRepository,
  });

  @override
  State<MealCapturePanel> createState() => _MealCapturePanelState();
}

class _MealCapturePanelState extends State<MealCapturePanel> {
  final _searchController = TextEditingController();
  late final MealFoodFavoritesRepository _favoritesRepository;
  String _query = '';
  bool _recognizing = false;
  List<MealFoodItem> _photoCandidates = const <MealFoodItem>[];
  final Set<String> _proposalSelection = <String>{};
  Set<String> _favoriteIds = <String>{};
  Future<List<LogEntryData>>? _historyFuture;

  @override
  void initState() {
    super.initState();
    _favoritesRepository =
        widget.favoritesRepository ??
        const SecureMealFoodFavoritesRepository();
    _loadFavorites();
  }

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

  Future<void> _loadFavorites() async {
    try {
      final ids = await _favoritesRepository.load();
      if (!mounted) return;
      setState(() => _favoriteIds = ids);
    } catch (_) {
      // Favorites are a convenience layer. Capture must remain usable if local
      // preference storage is temporarily unavailable.
    }
  }

  Future<void> _toggleFavorite(String id) async {
    final previous = Set<String>.from(_favoriteIds);
    final next = Set<String>.from(_favoriteIds);
    if (!next.add(id)) next.remove(id);
    setState(() => _favoriteIds = next);
    try {
      await _favoritesRepository.save(next);
    } catch (_) {
      if (mounted) setState(() => _favoriteIds = previous);
    }
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

  void _clearSearch() {
    _searchController.clear();
    setState(() => _query = '');
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final locale = Localizations.localeOf(context);
    final selected = widget.selectedIds
        .map(mealFoodById)
        .whereType<MealFoodItem>()
        .toList(growable: false);
    final queryReady = foldMealText(_query).length >= 2;
    final results = queryReady ? searchMealFoods(_query) : const <MealFoodItem>[];

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
        TextField(
          key: const Key('meal-food-search'),
          controller: _searchController,
          onChanged: (value) => setState(() => _query = value),
          textInputAction: TextInputAction.search,
          decoration: InputDecoration(
            labelText: l10n.journalMealSearch,
            hintText: l10n.journalMealSearchHint,
            prefixIcon: const Icon(Icons.search_rounded),
            suffixIcon: _query.isEmpty
                ? null
                : IconButton(
                    key: const Key('meal-food-search-clear'),
                    tooltip: l10n.cancel,
                    onPressed: _clearSearch,
                    icon: const Icon(Icons.close_rounded),
                  ),
            filled: true,
            fillColor: AminaTheme.subtleBg(context),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(AminaTheme.radiusXL),
              borderSide: BorderSide(color: AminaTheme.divider(context)),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(AminaTheme.radiusXL),
              borderSide: BorderSide(color: AminaTheme.divider(context)),
            ),
          ),
        ),
        const SizedBox(height: 10),
        if (_query.isNotEmpty && !queryReady)
          Text(
            l10n.journalMealSearchEmpty,
            style: TextStyle(
              color: AminaTheme.textSecondary(context),
              fontSize: 11,
            ),
          )
        else if (queryReady)
          _searchResults(results: results, locale: locale, l10n: l10n)
        else
          FutureBuilder<List<LogEntryData>>(
            future: _historyFuture,
            builder: (context, snapshot) {
              final logs = snapshot.data ?? const <LogEntryData>[];
              final favorites = _favoriteItems();
              final favoriteIds = favorites.map((item) => item.id).toSet();
              final recent = _recentItems(logs)
                  .where((item) => !favoriteIds.contains(item.id))
                  .take(5)
                  .toList(growable: false);
              final hidden = <String>{
                ...favoriteIds,
                ...recent.map((item) => item.id),
              };
              final habitual = _habitualItems(logs)
                  .where((item) => !hidden.contains(item.id))
                  .take(5)
                  .toList(growable: false);

              if (favorites.isEmpty && recent.isEmpty && habitual.isEmpty) {
                return const SizedBox.shrink();
              }

              return Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  if (favorites.isNotEmpty)
                    _foodListSection(
                      key: const Key('meal-favorites-section'),
                      title: _favoritesLabel(locale),
                      icon: Icons.star_rounded,
                      items: favorites,
                      locale: locale,
                      rowKeyPrefix: 'meal-favorite-row',
                    ),
                  if (favorites.isNotEmpty && recent.isNotEmpty)
                    const SizedBox(height: 14),
                  if (recent.isNotEmpty)
                    _foodListSection(
                      title: l10n.journalMealRecent,
                      icon: Icons.history_rounded,
                      items: recent,
                      locale: locale,
                      rowKeyPrefix: 'meal-history',
                    ),
                  if ((favorites.isNotEmpty || recent.isNotEmpty) &&
                      habitual.isNotEmpty)
                    const SizedBox(height: 14),
                  if (habitual.isNotEmpty)
                    _foodListSection(
                      title: l10n.journalMealHabitual,
                      icon: Icons.repeat_rounded,
                      items: habitual,
                      locale: locale,
                      rowKeyPrefix: 'meal-habitual',
                    ),
                ],
              );
            },
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

  Widget _searchResults({
    required List<MealFoodItem> results,
    required Locale locale,
    required AppLocalizations l10n,
  }) {
    if (results.isEmpty) {
      return Container(
        key: const Key('meal-search-empty'),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 16),
        decoration: BoxDecoration(
          color: AminaTheme.subtleBg(context),
          borderRadius: BorderRadius.circular(AminaTheme.radiusXL),
        ),
        child: Text(
          l10n.noData,
          style: TextStyle(
            color: AminaTheme.textSecondary(context),
            fontSize: 12,
          ),
        ),
      );
    }

    return _responsiveFoodList(
      items: results,
      locale: locale,
      rowKeyPrefix: 'meal-search',
    );
  }

  Widget _foodListSection({
    Key? key,
    required String title,
    required IconData icon,
    required List<MealFoodItem> items,
    required Locale locale,
    required String rowKeyPrefix,
  }) {
    return Column(
      key: key,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Row(
          children: <Widget>[
            Icon(icon, size: 16, color: AminaTheme.accent(context)),
            const SizedBox(width: 6),
            _subhead(title),
          ],
        ),
        const SizedBox(height: 7),
        _responsiveFoodList(
          items: items,
          locale: locale,
          rowKeyPrefix: rowKeyPrefix,
        ),
      ],
    );
  }

  Widget _responsiveFoodList({
    required List<MealFoodItem> items,
    required Locale locale,
    required String rowKeyPrefix,
  }) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final twoColumns = constraints.maxWidth >= 720 && items.length > 1;
        if (!twoColumns) {
          return Column(
            children: <Widget>[
              for (var index = 0; index < items.length; index++) ...<Widget>[
                _foodRow(
                  item: items[index],
                  locale: locale,
                  key: Key('$rowKeyPrefix-${items[index].id}'),
                ),
                if (index != items.length - 1) const SizedBox(height: 7),
              ],
            ],
          );
        }

        const gap = 8.0;
        final width = (constraints.maxWidth - gap) / 2;
        return Wrap(
          spacing: gap,
          runSpacing: gap,
          children: items
              .map(
                (item) => SizedBox(
                  width: width,
                  child: _foodRow(
                    item: item,
                    locale: locale,
                    key: Key('$rowKeyPrefix-${item.id}'),
                  ),
                ),
              )
              .toList(growable: false),
        );
      },
    );
  }

  Widget _foodRow({
    required MealFoodItem item,
    required Locale locale,
    required Key key,
  }) {
    final selected = widget.selectedIds.contains(item.id);
    final favorite = _favoriteIds.contains(item.id);
    final accent = AminaTheme.accent(context);

    return Material(
      key: key,
      color: selected
          ? accent.withValues(alpha: AminaTheme.isDark(context) ? .16 : .08)
          : AminaTheme.surface(context),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AminaTheme.radiusXL),
        side: BorderSide(
          color: selected ? accent : AminaTheme.divider(context),
        ),
      ),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: () => _toggleItem(item.id),
        child: ConstrainedBox(
          constraints: const BoxConstraints(minHeight: 58),
          child: Padding(
            padding: const EdgeInsetsDirectional.only(
              start: 12,
              end: 6,
              top: 7,
              bottom: 7,
            ),
            child: Row(
              children: <Widget>[
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    color: AminaTheme.subtleBg(context),
                    shape: BoxShape.circle,
                  ),
                  alignment: Alignment.center,
                  child: Icon(
                    Icons.restaurant_rounded,
                    size: 18,
                    color: selected ? accent : AminaTheme.textSecondary(context),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    item.labelFor(locale),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      color: AminaTheme.textPrimary(context),
                      fontSize: 13,
                      fontWeight: selected ? FontWeight.w700 : FontWeight.w600,
                      height: 1.25,
                    ),
                  ),
                ),
                IconButton(
                  key: Key('meal-favorite-${item.id}'),
                  tooltip: _favoriteTooltip(locale, favorite),
                  onPressed: () => _toggleFavorite(item.id),
                  visualDensity: VisualDensity.compact,
                  icon: Icon(
                    favorite ? Icons.star_rounded : Icons.star_border_rounded,
                    color: favorite
                        ? AminaTheme.accentAmber
                        : AminaTheme.textSecondary(context),
                    size: 21,
                  ),
                ),
                AnimatedContainer(
                  duration: const Duration(milliseconds: 160),
                  width: 30,
                  height: 30,
                  decoration: BoxDecoration(
                    color: selected ? accent : Colors.transparent,
                    shape: BoxShape.circle,
                    border: Border.all(
                      color: selected ? accent : AminaTheme.divider(context),
                    ),
                  ),
                  alignment: Alignment.center,
                  child: Icon(
                    selected ? Icons.check_rounded : Icons.add_rounded,
                    size: 17,
                    color: selected
                        ? Colors.white
                        : AminaTheme.textSecondary(context),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
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

  List<MealFoodItem> _favoriteItems() => _favoriteIds
      .map(mealFoodById)
      .whereType<MealFoodItem>()
      .toList(growable: false)
    ..sort((a, b) => a.fr.compareTo(b.fr));

  String _favoritesLabel(Locale locale) {
    return switch (locale.languageCode) {
      'ar' => 'المفضلة',
      'en' => 'Favorites',
      _ => 'Favoris',
    };
  }

  String _favoriteTooltip(Locale locale, bool favorite) {
    return switch (locale.languageCode) {
      'ar' => favorite ? 'إزالة من المفضلة' : 'إضافة إلى المفضلة',
      'en' => favorite ? 'Remove from favorites' : 'Add to favorites',
      _ => favorite ? 'Retirer des favoris' : 'Ajouter aux favoris',
    };
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
