from app.engines.audit_checker import run_audit_checks

def test_lama_missing():
    findings = run_audit_checks(
        lama_required=True,
        lama_signed=False,
        billed_physician="Dr A",
        actual_physician="Dr A"
    )
    assert len(findings) == 1
    assert findings[0].points_deducted == 20

def test_physician_mismatch():
    findings = run_audit_checks(
        lama_required=False,
        lama_signed=True,
        billed_physician="Dr A",
        actual_physician="Dr B"
    )
    assert len(findings) == 1
    assert findings[0].finding_id == "jawda_002"

def test_clean_claim():
    findings = run_audit_checks(
        lama_required=False,
        lama_signed=True,
        billed_physician="Dr A",
        actual_physician="Dr A"
    )
    assert len(findings) == 0