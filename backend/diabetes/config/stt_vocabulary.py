"""
Darija/Arabic medical vocabulary hints for Gemini STT transcription.

Extracted from engine.services.llm.stt._LANGUAGE_HINTS["ar-MA"].
Pass to media.voice.transcribe() as language_hints=AR_MA_STT_HINTS so the
full Moroccan Darija medical vocabulary is applied during transcription.

Usage:
    from diabetes.config.stt_vocabulary import AR_MA_STT_HINTS
    transcript = transcribe(audio_bytes, mime_type, language, language_hints=AR_MA_STT_HINTS)
"""
from __future__ import annotations

AR_MA_STT_HINTS: dict[str, str] = {
    "fr": "French",

    "ar-MA": (
        "Moroccan Darija — a spoken Arabic dialect that freely mixes Moroccan Arabic, French, and "
        "occasionally Amazigh (Tamazight). The speaker is a diabetes patient speaking to a medical "
        "assistant app.\n\n"

        "=== DISEASE & DIAGNOSIS ===\n"
        "sukkar / s-sukkar = diabetes OR blood glucose (same word used for both)\n"
        "3andi s-sukkar = I have diabetes\n"
        "mrid b-s-sukkar = I am sick with diabetes\n"
        "glycémie = blood glucose level (French loanword used as-is)\n"
        "HbA1c / l-hemoglobine / ta7lil 3 chwhar = HbA1c / 3-month blood test\n"
        "bilan = blood test results (French, used as-is)\n\n"

        "=== GLUCOSE READINGS ===\n"
        "qist s-sukkar / 3aref s-sukkar = measure / check blood glucose\n"
        "l-appareille / l-glucomètre = glucometer device\n"
        "tla3 s-sukkar = glucose went up (hyperglycemia)\n"
        "hbt s-sukkar / nqes s-sukkar = glucose dropped (hypoglycemia)\n"
        "s-sukkar 3ali = glucose is high\n"
        "s-sukkar wati = glucose is low\n\n"

        "=== INSULIN & TREATMENT ===\n"
        "insuline / l-insuline = insulin (French loanword)\n"
        "piqure / piqura = injection\n"
        "l-qalam = insulin pen\n"
        "dwa dyali = my medication\n"
        "contrôle = follow-up appointment (French, used as-is)\n"
        "tbeeb s-sukkar = diabetologist\n"
        "l-wrd9a / ordonnance = prescription\n\n"

        "=== BLOOD & VITALS ===\n"
        "dmem / ddem = blood\n"
        "tqes dmem = blood test\n"
        "tensio = blood pressure\n\n"

        "=== HYPOGLYCEMIA SYMPTOMS ===\n"
        "doukha = dizziness / vertigo\n"
        "rtach / idin kayrta7u = hand tremors\n"
        "3raq = sweating\n"
        "3yan / la3ya = tired / fatigued\n"
        "jou3 = hunger\n\n"

        "=== HYPERGLYCEMIA SYMPTOMS ===\n"
        "3tach = excessive thirst\n"
        "bzzaf pipi / baul bzzaf = frequent urination\n"
        "3ini kayt3awwaq = blurry vision\n"
        "rijliya machi 7asin = can't feel my feet (neuropathy)\n\n"

        "=== MEAL TIMING (critical for glucose log) ===\n"
        "f-sbah = in the morning\n"
        "f-lil = at night\n"
        "f-nhar = during the day\n"
        "qbel l-makla = before eating\n"
        "men b3d l-makla = after eating\n"
        "3la l-khwa / 3la l-9ila = fasting (before any food)\n"
        "ma klit wal = I haven't eaten anything\n\n"

        "=== FOOD (high glycemic impact in Moroccan diet) ===\n"
        "sukkariyat = sweets / sugary foods\n"
        "khbiz = bread\n"
        "tamar = dates (very common, high glycemic impact)\n"
        "atay = mint tea (often very sweet)\n\n"

        "=== NUMBERS (CRITICAL — these are medical values, transcribe exactly) ===\n"
        "Units used: mg/dL (e.g. 120, 250) OR mmol/L (e.g. 5.5, 8.3)\n"
        "Darija number words:\n"
        "  0=sifr  1=wahed  2=jouj/zouj  3=tlata  4=rb3a  5=khmsa\n"
        "  6=sta/stta  7=sb3a  8=tmnya  9=ts3ud  10=3achra\n"
        "  11=hd3ch  12=tn3ch  13=tlt3ch  14=rb3tch  15=khmst3ch\n"
        "  20=3ashrine  30=tlatine  40=rb3ine  50=khmsine\n"
        "  100=miya  200=miyatayn  300=tletmiya  400=rb3umiya\n"
        "Fractions: nus=half(0.5)  rbe3=quarter(0.25)\n"
        "  e.g. 'khmsa w nus' = 5.5 mmol/L\n"
        "  e.g. 'miya w 3ashrine' = 120 mg/dL\n"
        "  e.g. 'miyatayn w khmsa w 3ashrine' = 225 mg/dL\n\n"

        "IMPORTANT: numeric glucose values are medically critical. "
        "Transcribe numbers as spoken — do NOT convert to digits, do NOT round. "
        "The speaker may alternate freely between Darija and French in the same sentence."
    ),

    "ar": "Modern Standard Arabic (Fusha / MSA)",
}
