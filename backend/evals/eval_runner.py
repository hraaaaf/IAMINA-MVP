import json
import logging
import os
import sys

# 1. Path configuration to allow importing from the backend
# Assumes this script is in backend/evals/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# Mock Django settings if needed for imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'amina_backend.settings')

try:
    from diabetes.services.clinical.shield import ClinicalShield
except ImportError as e:
    print(f"Error importing shield: {e}")
    sys.exit(1)

def run_eval(cases_file: str):
    """
    IAmina Evaluation Runner (Phase 6)
    ==================================
    Runs a suite of golden cases against the Clinical Shield and Triage logic.
    """
    if not os.path.exists(cases_file):
        print(f"Golden cases file not found: {cases_file}")
        return

    with open(cases_file, 'r', encoding='utf-8') as f:
        cases = json.load(f)

    print("\n--- IAmina Clinical Evaluation Runner ---")
    print(f"Testing {len(cases)} cases from {os.path.basename(cases_file)}\n")

    passed_count = 0

    for case in cases:
        cid = case.get('id', '???')
        name = case.get('name', 'Unnamed Case')
        msg = case['input']['message']
        glucose = case['input']['glucose']
        expected = case['expected']

        # 1. Run Triage Vital
        actual_triage = ClinicalShield.triage_vital(glucose)

        # 2. Run Clinical Shield (Safety Check)
        # Note: check_safety returns True if SAFE, False if VIOLATION.
        # We invert it for the "is_violation" check.
        is_violation = not ClinicalShield.check_safety(msg)

        # 3. Validate results
        triage_ok = True
        if 'triage' in expected:
            triage_ok = actual_triage == expected['triage']

        safety_ok = True
        if 'safety_violation' in expected:
            safety_ok = is_violation == expected['safety_violation']

        case_passed = triage_ok and safety_ok
        if case_passed:
            passed_count += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"

        print(f"{status} [{cid}] {name}")
        if not case_passed:
            if not triage_ok:
                print(f"   - Triage mismatch: Got {actual_triage}, Expected {expected['triage']}")
            if not safety_ok:
                print(f"   - Safety mismatch: Got violation={is_violation}, Expected {expected['safety_violation']}")

    print(f"\nSummary: {passed_count}/{len(cases)} passed ({ (passed_count/len(cases))*100:.1f}% )")

if __name__ == "__main__":
    # Default to v1 if no args provided
    target = sys.argv[1] if len(sys.argv) > 1 else "evals/golden_cases/v1.json"
    run_eval(os.path.join(BASE_DIR, target))
