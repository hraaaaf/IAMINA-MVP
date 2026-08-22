from django.contrib.auth.models import User
from django.db import models


class LabReport(models.Model):
    """
    Structured lab / medical report extracted by the Document Pulper (Phase 12).

    One row = one imported document (PDF, image, Excel, DOCX).
    Glucose readings from the same document are stored as LogEntry rows
    (source='import') and linked via import_batch_id.
    """

    SOURCE_CHOICES = [
        ('pdf',          'PDF'),
        ('pdf_scanned',  'PDF scanné'),
        ('image',        'Image / Photo'),
        ('excel',        'Excel / CSV'),
        ('docx',         'Document Word'),
        ('unknown',      'Inconnu'),
    ]

    DOC_TYPE_CHOICES = [
        ('lab_report',    'Bilan biologique'),
        ('cgm_export',    'Export CGM'),
        ('glucose_log',   'Carnet glycémique'),
        ('prescription',  'Ordonnance'),
        ('medical_report','Compte-rendu médical'),
        ('unknown',       'Inconnu'),
    ]

    patient         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lab_reports')
    document_type   = models.CharField(max_length=32, choices=DOC_TYPE_CHOICES, default='unknown')
    source_format   = models.CharField(max_length=32, choices=SOURCE_CHOICES, default='unknown')

    # ── Lab values ──────────────────────────────────────────────────────────────
    report_date            = models.DateField(null=True, blank=True)
    hba1c_pct              = models.FloatField(null=True, blank=True, help_text='HbA1c %')
    fasting_glucose_mgdl   = models.FloatField(null=True, blank=True, help_text='Glucose à jeun mg/dL')
    total_cholesterol_mgdl = models.FloatField(null=True, blank=True)
    hdl_mgdl               = models.FloatField(null=True, blank=True)
    ldl_mgdl               = models.FloatField(null=True, blank=True)
    triglycerides_mgdl     = models.FloatField(null=True, blank=True)
    creatinine_umol        = models.FloatField(null=True, blank=True)

    # ── Metadata ─────────────────────────────────────────────────────────────
    glucose_readings_imported = models.IntegerField(default=0, help_text='LogEntry rows created from this document')
    import_batch_id  = models.CharField(max_length=64, blank=True, default='', help_text='Links LogEntry rows to this report')
    confidence       = models.FloatField(default=0.0, help_text='0.0–1.0 extraction confidence')
    clinical_notes   = models.TextField(blank=True, default='')
    raw_text         = models.TextField(blank=True, default='', help_text='Full extracted text for audit trail')
    extraction_provenance = models.JSONField(
        default=dict,
        blank=True,
        help_text='Structured field-level extraction evidence; excludes the full source text.',
    )
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"LabReport({self.document_type}, {self.report_date}, confidence={self.confidence:.0%})"
