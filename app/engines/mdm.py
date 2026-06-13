from app.engines.models import Citation, MDMResult


LEVELS = [
    "straightforward",
    "low",
    "moderate",
    "high"
]


NEW_PATIENT = {
    "straightforward": "99202",
    "low": "99203",
    "moderate": "99204",
    "high": "99205",
}


ESTABLISHED = {
    "straightforward": "99212",
    "low": "99213",
    "moderate": "99214",
    "high": "99215",
}


def calculate_mdm(
    problems_level: str,
    data_level: str,
    risk_level: str,
    visit_type: str,
) -> MDMResult:

    values = [
        problems_level,
        data_level,
        risk_level
    ]

    final_level = "straightforward"

    for level in reversed(LEVELS):
        count = sum(1 for v in values if LEVELS.index(v) >= LEVELS.index(level))

        if count >= 2:
            final_level = level
            break

    if visit_type == "new":
        code = NEW_PATIENT[final_level]
    else:
        code = ESTABLISHED[final_level]

    return MDMResult(
        mdm_level=final_level,
        recommended_code=code,
        citation=Citation(
            authority="AMA_2021",
            source_section="Table 2 Levels of Medical Decision Making",
            source_page=10,
        ),
    )