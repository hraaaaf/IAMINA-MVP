from __future__ import annotations

from django.apps import apps
from django.test import SimpleTestCase

_PATIENT_APP_LABELS = frozenset({"core", "diabetes"})
_FORBIDDEN_STORAGE_TYPES = frozenset({"BinaryField", "FileField", "ImageField"})


class PatientRelationalStorageContractTest(SimpleTestCase):
    def test_patient_models_do_not_embed_file_binary_or_base64_storage(self):
        offenders: list[str] = []

        for model in apps.get_models():
            if model._meta.app_label not in _PATIENT_APP_LABELS:
                continue
            for field in model._meta.get_fields():
                field_name = str(getattr(field, "name", ""))
                get_internal_type = getattr(field, "get_internal_type", None)
                internal_type = get_internal_type() if callable(get_internal_type) else ""
                if (
                    internal_type in _FORBIDDEN_STORAGE_TYPES
                    or "base64" in field_name.lower()
                ):
                    offenders.append(
                        f"{model._meta.label}.{field_name}:{internal_type or 'unknown'}"
                    )

        self.assertEqual(
            offenders,
            [],
            "Patient relational models must not embed large binary/original media; "
            "use an explicitly governed storage boundary instead.",
        )
