"""Exact D2 preview-only notice. Not permission to deliver health notifications."""
from dataclasses import dataclass
import hashlib

from core.consent_notice import normalize_notice_locale

D2_NOTICE_VERSION = "2026-10-20.d2.1"
D2_NOTICE_TEXT = {
    "fr": (
        "Je choisis de voir, dans IAmina uniquement, des aperçus non urgents "
        "d'observations personnalisées issues de mes données déjà enregistrées. "
        "Ces aperçus ne prédisent pas mon état de santé, ne diagnostiquent pas "
        "et ne recommandent aucun traitement. Cette préférence ne déclenche "
        "aucune notification du navigateur, aucun e-mail et aucun SMS. "
        "Je peux retirer mon accord à tout moment."
    ),
    "en": (
        "I choose to view, inside IAmina only, non-urgent previews of personal "
        "observations drawn from my existing records. These previews do not "
        "predict my health, diagnose or recommend treatment. This preference "
        "does not enable browser notifications, email or SMS. I can withdraw "
        "my consent at any time."
    ),
    "ar": (
        "أختار الاطلاع داخل IAmina فقط على معاينات لملاحظات شخصية غير عاجلة "
        "مستمدة من بياناتي المسجلة. لا تتنبأ هذه المعاينات بحالتي الصحية، "
        "ولا تشخص الأمراض أو توصي بعلاج. لا يفعّل هذا الاختيار إشعارات "
        "المتصفح أو البريد الإلكتروني أو الرسائل النصية. يمكنني سحب "
        "موافقتي في أي وقت."
    ),
}


@dataclass(frozen=True)
class D2Notice:
    version: str
    notice_hash: str
    locale: str
    text: str


def expected_d2_notice(locale: str) -> D2Notice:
    language = normalize_notice_locale(locale)
    if language == "ar-MA":
        language = "ar"
    if language not in D2_NOTICE_TEXT:
        raise ValueError("unsupported D2 notice locale")
    wording = D2_NOTICE_TEXT[language]
    hashed = hashlib.sha256(
        (D2_NOTICE_VERSION + "\n" + language + "\n" + wording).encode("utf-8")
    ).hexdigest()
    return D2Notice(D2_NOTICE_VERSION, hashed, language, wording)


def validate_d2_notice(*, version: str, notice_hash: str, locale: str) -> D2Notice:
    expected = expected_d2_notice(locale)
    if version != expected.version or notice_hash != expected.notice_hash:
        raise ValueError("D2 notice mismatch")
    return expected
