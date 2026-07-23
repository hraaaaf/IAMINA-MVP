from typing import Any, Dict


def normalize_to_pivot(clinical_data: Dict[str, Any]) -> str:
    """
    Translates clinical metrics and patterns into an English Pivot Language.

    IAmina uses English as a pivot language for its internal clinical reasoning
    to ensure maximum model performance and consistency, regardless of the
    user's target language (FR/AR/Darija).
    """
    pivot_lines = ["[CLINICAL_PIVOT_CONTEXT]"]

    # 1. Core KPIs
    if 'avg_glucose' in clinical_data and clinical_data['avg_glucose']:
        pivot_lines.append(f"AVG_GLUCOSE: {clinical_data['avg_glucose']:.1f} mg/dL")
    if 'tir_pct' in clinical_data:
        pivot_lines.append(f"TIR: {clinical_data['tir_pct']:.1f}%")
    if 'gmi' in clinical_data and clinical_data['gmi']:
        pivot_lines.append(f"GMI_EST_HBA1C: {clinical_data['gmi']:.1f}%")
    if 'std_dev' in clinical_data and clinical_data['std_dev']:
        pivot_lines.append(f"GLYCEMIC_VARIABILITY_SD: {clinical_data['std_dev']:.1f} mg/dL")

    # 2. Detected Patterns
    patterns = clinical_data.get('patterns', [])
    if patterns:
        pivot_lines.append("\n[DETECTED_PATTERNS]")
        for p in patterns:
            # Safely handle both objects (dataclasses) and dictionaries
            if hasattr(p, 'get'):
                code = p.get('code', 'UNKNOWN')
                priority = p.get('priority', 3)
                evidence = p.get('evidence', 'No evidence provided')
            else:
                code = getattr(p, 'code', 'UNKNOWN')
                priority = getattr(p, 'priority', 3)
                evidence = getattr(p, 'evidence', 'No evidence provided')

            pivot_lines.append(f"- {code} (PRIORITY_{priority}): {evidence}")

    return "\n".join(pivot_lines)
