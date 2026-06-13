from app.engines.models import Citation

TIME_RANGES = {
    "99202": (15, 29),
    "99203": (30, 44),
    "99204": (45, 59),
    "99205": (60, 74),
    "99212": (10, 19),
    "99213": (20, 29),
    "99214": (30, 39),
    "99215": (40, 54),
}

def validate_time(
    cpt_code: str,
    documented_minutes: int,
    start_time: str | None,
    end_time: str | None,
):

    findings = []
    uses_time_coding = (
        documented_minutes > 0
        or start_time is not None
        or end_time is not None
    )

    if not uses_time_coding:
        return {
            "valid": True,
            "findings": [],
            "citation": None,
        }

    if cpt_code not in TIME_RANGES:
        findings.append("Unknown CPT")

    else:
        min_time, max_time = TIME_RANGES[cpt_code]

        if documented_minutes < min_time:
            findings.append("Below AMA minimum time")

        if documented_minutes > max_time:
            findings.append("Above AMA maximum time")

    if start_time is None or end_time is None:
        findings.append(
            "JAWDA Major Finding: Missing start/end time (20 points)"
        )

    return {
        "valid": len(findings) == 0,
        "findings": findings,
        "citation": Citation(
            authority="JAWDA_2026",
            source_section="Time-Based Codes",
            source_page="5-9",
        ),
    }