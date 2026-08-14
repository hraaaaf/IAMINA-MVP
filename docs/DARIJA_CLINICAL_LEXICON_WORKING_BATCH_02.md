# Darija Clinical Lexicon — Working Native Review Batch 02

Status: **WORKING / NON-RUNTIME / NOT CLINICALLY CERTIFIED**

Date: 2026-08-15
Locale target: Moroccan Darija (`ar-MA`)
Source: interactive native-speaker review session.

## Governance boundary

This document records native-language candidates accepted during an interactive review session. It is **not** a clinical approval, safety-corpus approval, release certification, or authorization to add these phrases to runtime triage/classification logic.

Before any runtime use, each candidate requires the applicable clinical-safety review, positive/negative/contextual tests, false-positive analysis, and the existing fail-closed release gates.

Naturalness acceptance below is linguistic only. It does not assign medical severity or clinical meaning beyond the recorded gloss and semantic boundaries.

## Batch 02

### 27 — Low glucose / hypoglycemia wording
French gloss: « Mon sucre a beaucoup baissé / j’ai une hypo. »

Accepted:
- `هبط ليا السكر بزاف`
- `السكر هابط ليا`

Not retained in this session:
- `عندي هبوط فالسكر`
- `جاني هبوط فالسكر`

### 28 — High glucose / hyperglycemia wording
French gloss: « Mon sucre est très haut / j’ai une hyperglycémie. »

Accepted:
- `طلع ليا السكر بزاف`
- `السكر طالع ليا`
- `عندي السكر طالع`

Not retained in this session:
- `السكر زايد عندي`

### 29 — Seizure / convulsion language
French gloss: « Je fais une crise / j’ai des convulsions. »

Accepted:
- `شداتني التشنجات`
- `كنتشجنج`
- `بديت كنتفض بزاف`
- `جاتني نوبة`

Semantic boundary:
- `جاتني نوبة` is broader than convulsion and must not be mapped automatically to seizure without context.

### 30 — Disorientation
French gloss: « Je ne sais plus où je suis / je suis désorienté. »

Accepted:
- `ما بقيتش عارف فين أنا`
- `ما عرفت فين راني`
- `تخلط ليا كلشي وما بقيتش عارف فين أنا`

Not retained:
- `حاس براسي ضايع`

### 31 — Speech disturbance
French gloss: « Je n’arrive plus à parler correctement / mes paroles sont confuses. »

Accepted:
- `ما بقيتش كنقدر نهضر مزيان`
- `الهضرة تخلطات ليا`
- `لساني تقل عليا`

Not retained:
- `كنهضر وما كيبانش كلامي مزيان`

### 32 — Sudden loss of vision
French gloss: « Je ne vois plus / j’ai perdu la vue soudainement. »

Accepted:
- `ما بقيتش كنشوف`
- `مشى ليا الشوف`
- `ما بقيت كنشوف والو`

Native correction:
- use `الشوف` in `مشى ليا الشوف`, not `الشوفة`.

Not retained:
- `ضرباتني العمى`

### 33 — Numbness / tingling
French gloss: « J’ai un engourdissement / des fourmillements. »

Accepted:
- `تنملات ليا يدي`
- `يدي ما بقيتش كنحس بيها مزيان`

Not retained:
- `يدي فيها التنميل`
- `كنحس بالنمل ف يدي`

### 34 — Severe sudden headache
French gloss: « J’ai une douleur très forte et soudaine à la tête. »

Native lexical correction:
- prefer `على غفلة` over `فجأة` for the reviewed sudden-onset formulations.

Accepted:
- `شدني وجع قوي فراسي على غفلة`
- `راسي كايدرني بزاف وبدا على غفلة`
- `جاني صداع قوي على غفلة`

Not retained:
- `تفرقع ليا راسي من الوجع`

### 35 — Chest tightness / pressure
French gloss: « J’ai la poitrine serrée / une oppression. »

Accepted:
- `صدري مشدود عليا`
- `حاس بصدري مضيق عليا`
- `حاس بضغط فصدري`
- `صدري مخنوق`

Semantic boundary:
- some formulations can overlap chest pressure with dyspnea/suffocation language. Do not collapse these meanings automatically without context.

### 36 — Vomiting
French gloss: « Je vomis / j’ai vomi plusieurs fois. »

Accepted:
- `كنرد بزاف`
- `تقييت بزاف`
- `رديت بزاف`

Not retained:
- `ما حبساتش عليا الردة`

### 37 — Unable to stand / walk normally
French gloss: « Je n’arrive plus à me tenir debout / marcher correctement. »

Accepted:
- `ما بقيتش قادر نوقف على رجليا`
- `ما قادرش نمشي مزيان`
- `ما بقيتش قادر نتحرك مزيان`

Not retained:
- `رجليا ما بقاوش حامليني`

### 38 — Facial asymmetry
French gloss: « Je sens que ma bouche/mon visage part d’un côté. »

Accepted:
- `فمي تعوج ليا`
- `وجهي تعوج ليا`

Not retained:
- `حاس بوجهي مايل لجهة وحدة`
- `نص وجهي ما بقيتش كنحس بيه`

### 39 — Unable to move an arm / leg
French gloss: « Je n’arrive plus à bouger un bras / une jambe. »

Accepted:
- `ما بقيتش قادر نحرك يدي`
- `ما بقيتش قادر نحرك رجلي`
- `يدي ما بقاتش كتتحرك مزيان`
- `رجلي ما بقاتش كتتحرك مزيان`

### 40 — Insulin / CGM language
French gloss: « Je prends de l’insuline / mon capteur CGM. »

Accepted:
- `كندير الإنسولين`
- `كنضرب الإنسولين`
- `عندي الكابتور ديال السكر`
- `الكابتور ديال السكر ما خدامش`

Semantic boundary:
- these are treatment/device vocabulary candidates only. They do not authorize dose advice, treatment optimization, diagnosis, or automated clinical action.

## Review rules carried forward

1. Preserve native lexical corrections exactly as reviewed.
2. Keep broad expressions distinct from specific clinical events when ambiguity exists.
3. Keep chest tightness, dyspnea, pain, weakness, sensory loss, and motor deficit semantically separable.
4. Record rejected candidates because false-positive control matters as much as positive recall.
5. Add Arabizi/code-switch variants only after separate native review; do not transliterate mechanically.
6. Do not promote any item into runtime triage from this working document alone.
7. Before runtime promotion, build positive, negative, contextual, hyperbole, and ambiguity regression cases for each promoted concept.
