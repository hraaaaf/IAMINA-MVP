from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
EXPECTED = "ffdb101edbf75ef0805e6247951f61ee23217468"

head = subprocess.check_output(
    ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
).strip()
if head != EXPECTED:
    raise SystemExit(f"stale product head: {head}")

api = ROOT / "frontend/lib/services/api_client.dart"
text = api.read_text()
old_import = "import '../data/models/document_models.dart';"
new_import = old_import + "\nimport '../data/models/personal_response_models.dart';"
if new_import not in text:
    if text.count(old_import) != 1:
        raise SystemExit("api_client import anchor mismatch")
    text = text.replace(old_import, new_import, 1)

anchor = "  /// Envoie un log unique au backend."
method = """  Future<PersonalResponseResult?> getPersonalResponse({int days = 90}) async {
    try {
      final response = await _client.get(
        Uri.parse('/api/v1/personal-response/?days=$days'),
      );
      final body = response.body;
      if (response.isSuccessful && body is Map) {
        return PersonalResponseResult.fromJson(
          Map<String, dynamic>.from(body),
        );
      }
      return null;
    } catch (_) {
      return null;
    }
  }

"""
if method not in text:
    if text.count(anchor) != 1:
        raise SystemExit("api_client method anchor mismatch")
    text = text.replace(anchor, method + anchor, 1)
api.write_text(text)

journal = ROOT / "frontend/lib/features/journal/journal_screen.dart"
text = journal.read_text()
old_import = "import 'widgets/insulin_logging.dart';"
new_import = old_import + "\nimport 'widgets/personal_response_section.dart';"
if new_import not in text:
    if text.count(old_import) != 1:
        raise SystemExit("journal import anchor mismatch")
    text = text.replace(old_import, new_import, 1)

anchor = "          _buildSliverAppBar(context),\n          StreamBuilder<List<LogEntryData>>("
insertion = """          _buildSliverAppBar(context),
          SliverPadding(
            padding: EdgeInsetsDirectional.fromSTEB(
              horizontalPadding,
              20,
              horizontalPadding,
              0,
            ),
            sliver: SliverToBoxAdapter(
              child: PersonalResponseSection(unit: unit),
            ),
          ),
          StreamBuilder<List<LogEntryData>>("""
if insertion not in text:
    if text.count(anchor) != 1:
        raise SystemExit("journal sliver anchor mismatch")
    text = text.replace(anchor, insertion, 1)
journal.write_text(text)

translations = {
    "fr": {
        "personalResponseTitle": "Réponses personnelles",
        "personalResponseSubtitle": "Répétitions observées dans vos données synchronisées.",
        "personalResponseUnavailable": "Analyse indisponible pour le moment",
        "personalResponseUnavailableBody": "Le journal reste utilisable. Les motifs réapparaîtront quand les données synchronisées seront accessibles.",
        "personalResponseInsufficient": "Pas encore assez de répétitions",
        "personalResponseMinimumBasis": "Seuil produit : au moins {observations} observations sur {days} jours différents.",
        "@personalResponseMinimumBasis": {"placeholders": {"observations": {"type": "int"}, "days": {"type": "int"}}},
        "personalResponseEvidenceBasis": "Observations : {observations} · Jours : {days}",
        "@personalResponseEvidenceBasis": {"placeholders": {"observations": {"type": "int"}, "days": {"type": "int"}}},
        "personalResponsePatternMedian": "Médiane de ces observations",
        "personalResponseWindowMedian": "Médiane de tous les relevés synchronisés ({days} j)",
        "@personalResponseWindowMedian": {"placeholders": {"days": {"type": "int"}}},
        "personalResponseCausalityNotice": "Association observée dans votre journal. Elle ne prouve pas une cause et ne doit pas guider un traitement ou une dose.",
        "personalResponseConfidenceNotice": "Le niveau de répétition décrit seulement la quantité et la répartition de vos données ; ce n’est ni une probabilité ni une confiance clinique.",
        "personalResponseSyncedScope": "Basé uniquement sur vos glycémies synchronisées avec votre compte ; les données de démonstration sont exclues.",
        "personalResponseEvidenceLimited": "Répétition limitée",
        "personalResponseEvidenceModerate": "Répétition modérée",
        "personalResponseEvidenceStrong": "Répétition forte",
        "personalResponseStress": "Stress signalé",
        "personalResponseActivity": "Activité physique signalée",
        "personalResponseIllness": "Maladie signalée",
        "personalResponsePoorSleep": "Mauvais sommeil signalé",
        "personalResponseFatigue": "Fatigue signalée",
        "personalResponseBreakfast": "Après petit-déjeuner",
        "personalResponseLunch": "Après déjeuner",
        "personalResponseDinner": "Après dîner",
        "personalResponseSnack": "Après collation",
        "personalResponseSuhoor": "Après Suhoor",
        "personalResponseIftar": "Après Iftar",
        "personalResponseObservedPattern": "Motif observé",
    },
    "en": {
        "personalResponseTitle": "Personal responses",
        "personalResponseSubtitle": "Repeated observations in your synced data.",
        "personalResponseUnavailable": "Analysis is unavailable for now",
        "personalResponseUnavailableBody": "Your journal remains usable. Patterns will return when synced data is available.",
        "personalResponseInsufficient": "Not enough repetition yet",
        "personalResponseMinimumBasis": "Product threshold: at least {observations} observations across {days} different days.",
        "@personalResponseMinimumBasis": {"placeholders": {"observations": {"type": "int"}, "days": {"type": "int"}}},
        "personalResponseEvidenceBasis": "Observations: {observations} · Days: {days}",
        "@personalResponseEvidenceBasis": {"placeholders": {"observations": {"type": "int"}, "days": {"type": "int"}}},
        "personalResponsePatternMedian": "Median for these observations",
        "personalResponseWindowMedian": "Median of all synced readings ({days} d)",
        "@personalResponseWindowMedian": {"placeholders": {"days": {"type": "int"}}},
        "personalResponseCausalityNotice": "Association observed in your journal. It does not prove a cause and must not guide treatment or dosing.",
        "personalResponseConfidenceNotice": "The repetition level describes only the amount and spread of your data; it is not a probability or clinical confidence score.",
        "personalResponseSyncedScope": "Based only on glucose readings synced to your account; demo data is excluded.",
        "personalResponseEvidenceLimited": "Limited repetition",
        "personalResponseEvidenceModerate": "Moderate repetition",
        "personalResponseEvidenceStrong": "Strong repetition",
        "personalResponseStress": "Reported stress",
        "personalResponseActivity": "Reported physical activity",
        "personalResponseIllness": "Reported illness",
        "personalResponsePoorSleep": "Reported poor sleep",
        "personalResponseFatigue": "Reported fatigue",
        "personalResponseBreakfast": "After breakfast",
        "personalResponseLunch": "After lunch",
        "personalResponseDinner": "After dinner",
        "personalResponseSnack": "After snack",
        "personalResponseSuhoor": "After Suhoor",
        "personalResponseIftar": "After Iftar",
        "personalResponseObservedPattern": "Observed pattern",
    },
    "ar": {
        "personalResponseTitle": "استجابتك الشخصية",
        "personalResponseSubtitle": "تكرارات لوحظت في بياناتك المتزامنة.",
        "personalResponseUnavailable": "التحليل غير متاح حالياً",
        "personalResponseUnavailableBody": "يبقى السجل قابلاً للاستخدام. ستظهر الأنماط مجدداً عندما تتوفر البيانات المتزامنة.",
        "personalResponseInsufficient": "لا توجد تكرارات كافية بعد",
        "personalResponseMinimumBasis": "حد العرض في المنتج: {observations} ملاحظات على الأقل موزعة على {days} أيام مختلفة.",
        "@personalResponseMinimumBasis": {"placeholders": {"observations": {"type": "int"}, "days": {"type": "int"}}},
        "personalResponseEvidenceBasis": "الملاحظات: {observations} · الأيام: {days}",
        "@personalResponseEvidenceBasis": {"placeholders": {"observations": {"type": "int"}, "days": {"type": "int"}}},
        "personalResponsePatternMedian": "وسيط هذه الملاحظات",
        "personalResponseWindowMedian": "وسيط كل القياسات المتزامنة ({days} يومًا)",
        "@personalResponseWindowMedian": {"placeholders": {"days": {"type": "int"}}},
        "personalResponseCausalityNotice": "ارتباط لوحظ في سجلك فقط. لا يثبت سببًا ولا ينبغي استخدامه لتوجيه علاج أو جرعة.",
        "personalResponseConfidenceNotice": "مستوى التكرار يصف فقط كمية بياناتك وتوزعها؛ وليس احتمالًا أو درجة ثقة سريرية.",
        "personalResponseSyncedScope": "يعتمد فقط على قياسات السكر المتزامنة مع حسابك؛ وتُستبعد بيانات العرض التجريبي.",
        "personalResponseEvidenceLimited": "تكرار محدود",
        "personalResponseEvidenceModerate": "تكرار متوسط",
        "personalResponseEvidenceStrong": "تكرار قوي",
        "personalResponseStress": "الضغط النفسي المسجل",
        "personalResponseActivity": "النشاط البدني المسجل",
        "personalResponseIllness": "المرض المسجل",
        "personalResponsePoorSleep": "سوء النوم المسجل",
        "personalResponseFatigue": "التعب المسجل",
        "personalResponseBreakfast": "بعد الإفطار الصباحي",
        "personalResponseLunch": "بعد الغداء",
        "personalResponseDinner": "بعد العشاء",
        "personalResponseSnack": "بعد وجبة خفيفة",
        "personalResponseSuhoor": "بعد السحور",
        "personalResponseIftar": "بعد الإفطار",
        "personalResponseObservedPattern": "نمط ملحوظ",
    },
}

for locale, values in translations.items():
    path = ROOT / f"frontend/lib/l10n/app_{locale}.arb"
    data = json.loads(path.read_text())
    for key in values:
        if key in data:
            raise SystemExit(f"duplicate localization key {key} in {path}")
    data.update(values)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
