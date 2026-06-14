from app.engines.audit_checker import run_audit_checks
from app.engines.documentation_checker import evaluate_history_level
from app.engines.mdm import calculate_mdm
from app.engines.time_validator import validate_time


_HIGH_PROBLEM_KW = frozenset({
    "severe exacerbation", "severe progression", "threat to life",
    "threat to bodily function", "life-threatening", "critical",
    "sepsis", "stroke", "mi ", "myocardial infarction", "respiratory failure",
})
_MODERATE_PROBLEM_KW = frozenset({
    "exacerbation", "poorly controlled", "uncontrolled", "progressing",
    "progression", "undiagnosed", "uncertain prognosis", "systemic symptoms",
    "systemic", "complicated injury", "acute complicated",
    "pyelonephritis", "pneumonitis", "colitis",
})
_LOW_PROBLEM_KW = frozenset({
    "stable", "well-controlled", "well controlled", "routine",
    "follow-up", "follow up", "uncomplicated", "controlled",
    "benign", "cataract", "bph",
})

_HIGH_RISK_KW = frozenset({
    "hospitalization", "hospital admission", "admit", "icu",
    "emergency surgery", "major surgery with identified",
    "intensive monitoring for toxicity", "dnr",
    "do not resuscitate", "de-escalate care",
})
_MODERATE_RISK_KW = frozenset({
    "prescribed", "prescription", "new medication", "medication change",
    "dose adjustment", "increased dose", "added medication", "started medication",
    "drug management", "prescription drug",
    "metformin", "lisinopril", "amlodipine", "atorvastatin", "insulin",
    "losartan", "metoprolol", "omeprazole", "levothyroxine",
    "minor surgery with identified",
    "elective major surgery without",
    "social determinants of health",
})
_LOW_RISK_KW = frozenset({
    "otc", "over the counter", "rest", "ice", "compression", "elevation",
    "labs ordered", "blood test", "urinalysis", "x-ray ordered",
    "superficial needle biopsy",
})

_DATA_TO_MDM: dict[str, str] = {
    "none": "straightforward",
    "limited": "low",
    "moderate": "moderate",
    "extensive": "high",
}

_RISK_TO_MDM: dict[str, str] = {
    "minimal": "straightforward",
    "low": "low",
    "moderate": "moderate",
    "high": "high",
}
_CODE_TO_MDM: dict[str, str] = {
    "99202": "straightforward", "99203": "low",
    "99204": "moderate",        "99205": "high",
    "99212": "straightforward", "99213": "low",
    "99214": "moderate",        "99215": "high",
}

def _infer_problems_level(diagnoses: list[str], documentation: dict) -> str:
    assessment = (documentation.get("assessment") or "").lower()
    hpi = (documentation.get("HPI") or documentation.get("hpi") or "").lower()
    all_text = assessment + " " + hpi + " " + " ".join(d.lower() for d in diagnoses)

    if any(kw in all_text for kw in _HIGH_PROBLEM_KW):
        return "high"

    if any(kw in all_text for kw in _MODERATE_PROBLEM_KW):
        return "moderate"

    if len(diagnoses) >= 2:
        return "low"
    if any(kw in all_text for kw in _LOW_PROBLEM_KW):
        return "low"
    if len(diagnoses) == 1:
        return "low"

    return "straightforward"


def _infer_data_level_raw(encounter: dict) -> str:
    score = 0
    documentation = encounter.get("documentation", {})
    hpi = (documentation.get("HPI") or documentation.get("hpi") or "").lower()
    assessment = (documentation.get("assessment") or "").lower()
    combined = hpi + " " + assessment

    procedures = encounter.get("procedures", [])
    score += len(procedures)  # each unique order/test = 1 element

    if any(kw in combined for kw in (
        "prior records", "external note", "previous records",
        "old records", "outside records", "prior lab",
    )):
        score += 1

    if any(kw in combined for kw in (
        "ecg", "ekg", "x-ray", "ct scan", "mri", "ultrasound",
        "echo", "interpreted", "read the",
    )):
        score += 1

    if any(kw in combined for kw in (
        "discussed with", "consulted", "spoke with dr", "referred to",
        "coordination with", "care coordination",
    )):
        score += 1

    if score == 0:
        return "none"
    if score == 1:
        return "limited"
    if score <= 3:
        return "moderate"
    return "extensive"


def _infer_risk_level(encounter: dict) -> str:
    documentation = encounter.get("documentation", {})
    assessment = (documentation.get("assessment") or "").lower()
    hpi = (documentation.get("HPI") or documentation.get("hpi") or "").lower()
    procedures = [p.lower() for p in encounter.get("procedures", [])]
    combined = assessment + " " + hpi + " " + " ".join(procedures)

    if any(kw in combined for kw in _HIGH_RISK_KW):
        return "high"

    if any(kw in combined for kw in _MODERATE_RISK_KW):
        return "moderate"

    if any(kw in combined for kw in _LOW_RISK_KW):
        return "low"

    return "minimal"

def _build_mdm_gaps(
    billed_code: str,
    problems_level: str,
    data_level_raw: str,
    risk_level: str,
    diagnoses: list[str],
    procedures: list[str],
) -> list[dict]:
    """
    Produces up to 3 gap entries (one per MDM element) with exact AMA 2021 citations.
    Only called when recommended_code != billed_code.
    """
    billed_mdm = _CODE_TO_MDM.get(billed_code, "unknown")
    gaps = []

    gaps.append({
        "gap": (
            f"Documentation supports '{problems_level}' problem complexity "
            f"(diagnoses: {', '.join(diagnoses) if diagnoses else 'none documented'}). "
            f"Billed code {billed_code} requires '{billed_mdm}' MDM. "
            f"AMA 2021 Table 2 (page 10): 2 of 3 MDM elements must meet or exceed the billed level."
        ),
        "authority": "AMA_2021",
        "source_section": "Table 2 Levels of Medical Decision Making",
        "source_page": 10,
    })

    gaps.append({
        "gap": (
            f"Data element supports '{data_level_raw}' complexity "
            f"(procedures/orders found: {len(procedures)}; "
            f"external records, independent test interpretation, or care coordination not documented). "
            f"'{billed_mdm}' MDM requires '{billed_mdm}' data per AMA 2021 Table 2 (page 9-10)."
        ),
        "authority": "AMA_2021",
        "source_section": "Amount and/or Complexity of Data to be Reviewed and Analyzed",
        "source_page": 9,
    })

    gaps.append({
        "gap": (
            f"Risk element: inferred '{risk_level}' risk from documented management. "
            f"'{billed_mdm}' MDM requires '{billed_mdm}' risk "
            f"(e.g., prescription drug management = moderate per AMA 2021 page 13; "
            f"drug therapy requiring intensive monitoring = high per AMA 2021 page 14)."
        ),
        "authority": "AMA_2021",
        "source_section": "Risk of Complications and/or Morbidity or Mortality of Patient Management",
        "source_page": 13,
    })

    return gaps

def analyze_encounter(encounter: dict) -> dict:
    audit_findings = run_audit_checks(
        lama_required=encounter.get("lama_required", False),
        lama_signed=encounter.get("lama_signed", True),
        billed_physician=encounter.get("billed_physician", ""),
        actual_physician=encounter.get("actual_physician", ""),
        billed_code=encounter.get("billed_code", ""),
        start_time=encounter.get("start_time"),
        end_time=encounter.get("end_time"),
    )

    history = evaluate_history_level(
        chief_complaint=encounter.get("chief_complaint"),
        hpi_count=encounter.get("hpi_count", 0),
        ros_count=encounter.get("ros_count", 0),
        pfsh_count=encounter.get("pfsh_count", 0),
    )

    documentation = encounter.get("documentation", {})
    diagnoses = encounter.get("diagnoses", [])
    procedures = encounter.get("procedures", [])

    problems_level = _infer_problems_level(diagnoses, documentation)
    data_level_raw = _infer_data_level_raw(encounter)
    data_level = _DATA_TO_MDM[data_level_raw]
    risk_level = _infer_risk_level(encounter)          # 'minimal'|'low'|'moderate'|'high'
    risk_mdm = _RISK_TO_MDM[risk_level]               # mapped to LEVELS list in mdm.py

    mdm = calculate_mdm(
        problems_level=problems_level,
        data_level=data_level,
        risk_level=risk_mdm,
        visit_type=encounter.get("visit_type", "outpatient"),
    )

    time_result = validate_time(
        cpt_code=encounter.get("billed_code", ""),
        documented_minutes=encounter.get("total_time_minutes") or 0,
        start_time=encounter.get("start_time"),
        end_time=encounter.get("end_time"),
    )

    uses_time_coding = (
        (encounter.get("total_time_minutes") or 0) > 0
        or encounter.get("start_time")
        or encounter.get("end_time")
    )

    recommended_code = mdm.recommended_code
    billed_code = encounter.get("billed_code", "")
    if uses_time_coding and time_result["valid"] and billed_code in {
        "99202", "99203", "99204", "99205",
        "99212", "99213", "99214", "99215",
    }:
        recommended_code = billed_code

    documentation_gaps: list[dict] = []

    if not encounter.get("chief_complaint"):
        documentation_gaps.append({
            "gap": "Chief complaint missing — required at all history levels.",
            "authority": "CMS_1997",
            "source_section": "Documentation of History - Chief Complaint (CC)",
            "source_page": 6,
        })

    if not documentation.get("assessment"):
        documentation_gaps.append({
            "gap": "Assessment/clinical impression missing — must document diagnosis or reason for management decision.",
            "authority": "CMS_1997",
            "source_section": "General Principles of Medical Record Documentation",
            "source_page": 4,
        })

    if not documentation.get("exam"):
        documentation_gaps.append({
            "gap": "Physical examination findings missing.",
            "authority": "CMS_1997",
            "source_section": "Documentation of Examination",
            "source_page": 10,
        })

    if not (documentation.get("HPI") or documentation.get("hpi")):
        documentation_gaps.append({
            "gap": "History of Present Illness (HPI) missing.",
            "authority": "CMS_1997",
            "source_section": "Documentation of History - History of Present Illness (HPI)",
            "source_page": 7,
        })

    billed_code = encounter.get("billed_code", "")
    if billed_code and recommended_code != billed_code:
        documentation_gaps.extend(
            _build_mdm_gaps(
                billed_code=billed_code,
                problems_level=problems_level,
                data_level_raw=data_level_raw,
                risk_level=risk_level,
                diagnoses=diagnoses,
                procedures=procedures,
            )
        )

    mdm_mismatch = billed_code and recommended_code != billed_code

    audit_points = sum(
        finding.points_deducted
        for finding in audit_findings
    )

    if audit_points >= 20 or len(documentation_gaps) >= 4:
        denial_risk = "high"
    elif (
        len(audit_findings) == 1
        or mdm_mismatch
        or len(documentation_gaps) >= 2
        or (uses_time_coding and not time_result["valid"])
    ):
        denial_risk = "moderate"
    else:
        denial_risk = "low"

    if uses_time_coding:
        code_supported = (
            billed_code == recommended_code
            and time_result["valid"]
            and len(documentation_gaps) == 0
            and len(audit_findings) == 0
        )
    else:
        code_supported = (
            billed_code == recommended_code
            and len(documentation_gaps) == 0
            and len(audit_findings) == 0
        )

    citations = [{
        "authority": mdm.citation.authority,
        "source_section": mdm.citation.source_section,
        "source_page": mdm.citation.source_page,
    }]
    for finding in audit_findings:
        citations.append({
            "authority": finding.citation.authority,
            "source_section": finding.citation.source_section,
            "source_page": finding.citation.source_page,
        })

    if time_result["citation"] and uses_time_coding:
        citations.append({
            "authority": time_result["citation"].authority,
            "source_section": time_result["citation"].source_section,
            "source_page": time_result["citation"].source_page,
        })

    if documentation_gaps:
        citations.append({
            "authority": "CMS_1997",
            "source_section": "General Principles of Medical Record Documentation",
            "source_page": 4,
        })

    return {
        "recommended_code": recommended_code,
        "code_supported": code_supported,
        "history_level": history,
        "documentation_gaps": documentation_gaps,
        "audit_findings": audit_findings,
        "total_findings": len(audit_findings),
        "denial_risk": denial_risk,
        "citations": citations,
        "_mdm_debug": {
            "problems_level": problems_level,
            "data_level": data_level_raw,
            "risk_level": risk_level,
            "mdm_level": mdm.mdm_level,
        },
    }