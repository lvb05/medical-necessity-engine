from app.engines.audit_checker import run_audit_checks
from app.engines.documentation_checker import evaluate_history_level
from app.engines.mdm import calculate_mdm
from app.engines.time_validator import validate_time


def analyze_encounter(encounter: dict):
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

    mdm = calculate_mdm(
        problems_level="moderate",
        data_level="moderate",
        risk_level="moderate",
        visit_type=encounter.get("visit_type", "outpatient"),
    )

    time_result = validate_time(
        cpt_code=encounter.get("billed_code", ""),
        documented_minutes=encounter.get("total_time_minutes", 0),
        start_time=encounter.get("start_time"),
        end_time=encounter.get("end_time"),
    )

    documentation_gaps = []

    if not encounter.get("chief_complaint"):
        documentation_gaps.append("Chief complaint missing")

    documentation = encounter.get("documentation", {})
    if not documentation.get("assessment"):
        documentation_gaps.append("Assessment missing")
    if not documentation.get("exam"):
        documentation_gaps.append("Exam missing")
    if not documentation.get("HPI"):
        documentation_gaps.append("HPI missing")

    if len(audit_findings) >= 2:
        denial_risk = "high"
    elif len(audit_findings) == 1 or not time_result["valid"]:
        denial_risk = "moderate"
    else:
        denial_risk = "low"

    code_supported = encounter.get("billed_code") == mdm.recommended_code and time_result["valid"]

    return {
        "recommended_code": mdm.recommended_code,
        "code_supported": code_supported,
        "history_level": history,
        "documentation_gaps": documentation_gaps,
        "audit_findings": audit_findings,
        "total_findings": len(audit_findings),
        "denial_risk": denial_risk,
        "citations": [
            {
                "authority": mdm.citation.authority,
                "source_section": mdm.citation.source_section,
                "source_page": mdm.citation.source_page,
            },
            {
                "authority": time_result["citation"].authority,
                "source_section": time_result["citation"].source_section,
                "source_page": time_result["citation"].source_page,
            },
        ],
    }