from app.engines.models import AuditFinding, Citation
def run_audit_checks(
    lama_required: bool,
    lama_signed: bool,
    billed_physician: str,
    actual_physician: str,
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
    return findings