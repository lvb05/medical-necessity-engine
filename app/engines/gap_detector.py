from app.engines.audit_checker import run_audit_checks
from app.engines.documentation_checker import evaluate_history_level

def analyze_encounter(encounter):

    audit_findings = run_audit_checks(
        lama_required=encounter.get("lama_required", False),
        lama_signed=encounter.get("lama_signed", True),
        billed_physician=encounter.get("billed_physician", ""),
        actual_physician=encounter.get("actual_physician", ""),
    )

    history = evaluate_history_level(
        chief_complaint=encounter.get("chief_complaint"),
        hpi_count=encounter.get("hpi_count", 0),
        ros_count=encounter.get("ros_count", 0),
        pfsh_count=encounter.get("pfsh_count", 0),
    )

    return {
        "history_level": history,
        "audit_findings": audit_findings,
        "total_findings": len(audit_findings),
    }