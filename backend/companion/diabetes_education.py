"""Deterministic, non-personalized education for common CGM concepts.

This module is intentionally data-free: it explains standard CGM metrics but never
interprets a patient's values, diagnoses, prescribes, or changes treatment.
"""
from __future__ import annotations

import re

_ARABIC_RE = re.compile(r"[\u0600-\u06FF]")

_CONCEPTS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("tir", re.compile(r"\b(?:tir|time[ -]?in[ -]?range|temps dans (?:la )?cible)\b", re.I)),
    ("ranges", re.compile(r"\b(?:tar|tbr|time above range|time below range|temps au-dessus|temps en dessous)\b", re.I)),
    ("gmi", re.compile(r"\b(?:gmi|glucose management indicator)\b", re.I)),
    ("cv", re.compile(r"\b(?:cv|coefficient de variation|coefficient of variation|variabilit[ée] glyc[ée]mique|glycemic variability|glucose variability)\b", re.I)),
    ("mean", re.compile(r"\b(?:glyc[ée]mie moyenne|mean glucose|average glucose|glucose moyen)\b", re.I)),
)

_COPY = {
    "fr": {
        "tir": "Le TIR (Time in Range) est le pourcentage du temps où le glucose mesuré par CGM est dans la plage 70–180 mg/dL (3,9–10,0 mmol/L). Il complète l’HbA1c en montrant combien de temps la glycémie reste dans la cible. Il doit être interprété avec le temps sous et au-dessus de la plage, et avec suffisamment de données CGM.",
        "ranges": "Le TAR est le temps au-dessus de la plage et le TBR le temps en dessous. Les seuils CGM usuels distinguent notamment >180 et >250 mg/dL pour le TAR, puis <70 et <54 mg/dL pour le TBR. Ces métriques complètent le TIR et ne doivent pas être interprétées isolément.",
        "gmi": "Le GMI (Glucose Management Indicator) est une estimation calculée à partir de la glycémie moyenne du CGM. Il donne une valeur de type HbA1c, mais ce n’est pas une HbA1c mesurée au laboratoire et les deux valeurs peuvent différer.",
        "cv": "Le CV est le coefficient de variation du glucose : il décrit la variabilité glycémique par rapport à la moyenne. Plus il est élevé, plus les valeurs sont dispersées. Les recommandations CGM utilisent généralement ≤36 % comme repère pour la plupart des adultes, à interpréter avec le reste du profil.",
        "mean": "La glycémie moyenne est la moyenne des valeurs enregistrées par le CGM sur la période observée. Elle résume le niveau global de glucose, mais ne montre pas à elle seule les hypoglycémies, hyperglycémies ou la variabilité ; elle se lit avec TIR/TBR/TAR et CV.",
    },
    "en": {
        "tir": "TIR (Time in Range) is the percentage of CGM time between 70 and 180 mg/dL (3.9–10.0 mmol/L). It complements A1C by showing how much time glucose stays in range. It should be read together with time below and above range and with enough CGM data.",
        "ranges": "TAR is time above range and TBR is time below range. Common CGM thresholds include >180 and >250 mg/dL for TAR, and <70 and <54 mg/dL for TBR. They complement TIR and should not be interpreted in isolation.",
        "gmi": "GMI (Glucose Management Indicator) is calculated from mean CGM glucose. It gives an A1C-like estimate, but it is not a laboratory A1C and the two values can differ.",
        "cv": "CV is the glucose coefficient of variation: it describes glucose variability relative to the mean. A higher CV means more spread. CGM guidance commonly uses ≤36% as a reference for most adults, interpreted alongside the rest of the glucose profile.",
        "mean": "Mean glucose is the average of CGM glucose values over the observed period. It summarizes overall glucose level but cannot by itself show hypoglycemia, hyperglycemia, or variability; it is best read with TIR/TBR/TAR and CV.",
    },
    "ar": {
        "tir": "الوقت ضمن النطاق (TIR) هو نسبة الوقت التي تكون فيها قراءات جهاز المراقبة المستمرة للغلوكوز بين 70 و180 mg/dL (3.9–10.0 mmol/L). وهو يكمل HbA1c لأنه يوضح مقدار الوقت داخل النطاق، ويُقرأ مع الوقت تحت النطاق وفوقه ومع توفر بيانات كافية.",
        "ranges": "TAR هو الوقت فوق النطاق وTBR هو الوقت تحت النطاق. من الحدود الشائعة في بيانات CGM: أكثر من 180 و250 mg/dL للارتفاع، وأقل من 70 و54 mg/dL للانخفاض. هذه المقاييس تكمل TIR ولا تُفسَّر منفردة.",
        "gmi": "مؤشر إدارة الغلوكوز (GMI) قيمة محسوبة من متوسط الغلوكوز في بيانات CGM وتعطي تقديرًا شبيهًا بـ HbA1c، لكنها ليست HbA1c مقاسة في المختبر وقد تختلف عنها.",
        "cv": "معامل الاختلاف (CV) يصف تذبذب الغلوكوز نسبةً إلى المتوسط؛ كلما ارتفع كان التشتت أكبر. تستخدم إرشادات CGM عادةً ≤36% كمرجع لمعظم البالغين، مع تفسيره ضمن بقية ملف الغلوكوز.",
        "mean": "متوسط الغلوكوز هو متوسط قراءات CGM خلال الفترة المدروسة. يلخص المستوى العام للغلوكوز، لكنه لا يوضح وحده الانخفاضات أو الارتفاعات أو التذبذب، لذلك يُقرأ مع TIR وTBR وTAR وCV.",
    },
    "ar-MA": {
        "tir": "TIR هو النسبة ديال الوقت اللي كيكون فيه السكر فـ CGM بين 70 و180 mg/dL (3.9–10.0 mmol/L). كيكمل HbA1c حيث كيبين شحال من الوقت السكر بقى فالنطاق، وخصو يتقرا مع الوقت تحت وفوق النطاق ومع بيانات كافية.",
        "ranges": "TAR هو الوقت فوق النطاق وTBR هو الوقت تحت النطاق. فـ CGM كاينين حدود معروفة بحال فوق 180 و250 mg/dL، وتحت 70 و54 mg/dL. هاد المؤشرات كيكملو TIR وما خاصهمش يتفسرو بوحدهم.",
        "gmi": "GMI هو تقدير كيتحسب من متوسط السكر فـ CGM وكيعطي قيمة شبيهة بـ HbA1c، ولكن ماشي HbA1c ديال المختبر وقد يختلف عليها.",
        "cv": "CV هو معامل الاختلاف وكيشرح شحال السكر كيتبدل مقارنة مع المتوسط. كلما طلع، كتكون القيم متفرقة أكثر. إرشادات CGM كتستعمل غالباً ≤36% كمرجع لمعظم البالغين، وخصو يتقرا مع باقي المؤشرات.",
        "mean": "متوسط السكر هو المتوسط ديال قياسات CGM فالفترة اللي كنشوفوها. كيعطي فكرة على المستوى العام، ولكن بوحدو ما كيبينش الهبوط والطلوع ولا التذبذب؛ الأحسن يتقرا مع TIR/TBR/TAR وCV.",
    },
}

_LATIN_DARIJA = {
    "tir": "TIR howa nisb dyal lwa9t li kaykon fih sokkar f CGM bin 70 w 180 mg/dL (3.9–10.0 mmol/L). Kaykmmel HbA1c 7it kaybeyen ch7al mn lwa9t sokkar b9a f range. Khasso ytqra m3a lwa9t ta7t w fo9 range w m3a data CGM kafya.",
    "ranges": "TAR howa lwa9t fo9 range w TBR howa lwa9t ta7t range. F CGM kaynin thresholds b7al fo9 180 w 250 mg/dL, w ta7t 70 w 54 mg/dL. Had metrics kaykmmlo TIR w ma khas-homch ytqraw bo7dhom.",
    "gmi": "GMI howa ta9dir kayt7seb mn moyenne dyal sokkar f CGM. Kay3ti value qriba l-format dyal HbA1c, walakin ma howach HbA1c dyal laboratoire w y9dro ykhtalfo.",
    "cv": "CV howa coefficient de variation dyal sokkar: kaybeyen ch7al l-values kaytbeddlo 7da moyenne. Ila tla3 CV, kaykon t-taqallob kter. Guidance dyal CGM katst3mel ghaliban ≤36% k reference l-ktr mn lbalghin, m3a ba9i metrics.",
    "mean": "Moyenne dyal sokkar hiya moyenne dyal readings CGM f wa7d lmodda. Kat3ti fikra 3la niveau l3am, walakin bo7dha ma katbeyench l-hypo, l-hyper, wla variability; katqra m3a TIR/TBR/TAR w CV.",
}


def diabetes_education_reply(message: str, language: str) -> str | None:
    """Return a bounded educational reply for a recognized CGM concept."""
    text = (message or "").strip()
    concept = next((name for name, pattern in _CONCEPTS if pattern.search(text)), None)
    if concept is None:
        return None
    if language == "ar-MA" and not _ARABIC_RE.search(text):
        return _LATIN_DARIJA[concept]
    copy = _COPY.get(language, _COPY["fr"])
    return copy[concept]
