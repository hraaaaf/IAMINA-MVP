from pathlib import Path

path = Path("backend/diabetes/services/clinical/proactive_attention.py")
text = path.read_text()

old = '''    result = refresh_personal_response_memory(patient_id=patient_id)
    dataset_eligible = _dataset_eligible(result)
    now = timezone.now()

    evidence = get_evidence(PERSONAL_RESPONSE_EVIDENCE_ID)
    if evidence.clinical_authority is not ClinicalAuthority.GOVERNED_RULE:
        return ProactiveDecision(candidate=None, suppression_reason="source_rule_not_governed")
    if evidence.supersession_state != "current":
        return ProactiveDecision(candidate=None, suppression_reason="source_rule_superseded")
'''

new = '''    evidence = get_evidence(PERSONAL_RESPONSE_EVIDENCE_ID)
    if evidence.clinical_authority is not ClinicalAuthority.GOVERNED_RULE:
        return ProactiveDecision(candidate=None, suppression_reason="source_rule_not_governed")
    if evidence.supersession_state != "current":
        return ProactiveDecision(candidate=None, suppression_reason="source_rule_superseded")

    result = refresh_personal_response_memory(patient_id=patient_id)
    dataset_eligible = _dataset_eligible(result)
    now = timezone.now()
'''

count = text.count(old)
if count != 1:
    raise SystemExit(f"expected exactly one evidence-order block, found {count}")

path.write_text(text.replace(old, new))
