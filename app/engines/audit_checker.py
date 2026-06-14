from app.engines.models import AuditFinding, Citation
TIME_BASED_CODES = {
    "99202", "99203", "99204", "99205",
    "99212", "99213", "99214", "99215",
}
def run_audit_checks(
    lama_required: bool,
    lama_signed: bool,
    billed_physician: str,
    actual_physician: str,
    billed_code: str = "",
    start_time: str | None = None,
    end_time: str | None = None,
):
    findings = []

    if lama_required and not lama_signed:
        findings.append(
            AuditFinding(
                finding_id="jawda_004",
                category="Major",
                points_deducted=20,
                description="Missing or unsigned LAMA form",
                citation=Citation(
                    authority="JAWDA_2026",
                    source_section="Appendix III",
                    source_page=16,
                ),
            )
        )

    if billed_physician != actual_physician:
        findings.append(
            AuditFinding(
                finding_id="jawda_002",
                category="Major",
                points_deducted=20,
                description="Physician mismatch",
                citation=Citation(
                    authority="JAWDA_2026",
                    source_section="Appendix III",
                    source_page=16,
                ),
            )
        )

    if (
        billed_code in TIME_BASED_CODES
        and (not start_time or not end_time)
    ):
        findings.append(
            AuditFinding(
                finding_id="jawda_005",
                category="Major",
                points_deducted=20,
                description="Missing start time or end time documentation for time-based billing",
                citation=Citation(
                    authority="JAWDA_2026",
                    source_section="Claims Review Requirements",
                    source_page=5,
                ),
            )
        )
    
    return findings