from __future__ import annotations

import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GuidelineChunk
from app.retrieval.authority_router import route_authority

_CPT_RE = re.compile(r"\b(99(?:202|203|204|205|212|213|214|215))\b")

_SECTION_PRIORITY: dict[str, int] = {
    # AMA
    "time_based_codes": 50,
    "mdm_2_of_3_rule": 45,
    "mdm_levels": 40,
    "problem_definitions": 40,
    "risk_levels": 35,
    "data_elements": 30,
    "time_definition": 35,
    "code_mapping": 25,
    # CMS
    "documentation_of_history": 45,
    "documentation_of_examination": 40,
    "general_principles": 35,
    "mdm_framework": 30,
    # HAAD / Clinical coding process
    "coder_query_process": 45,
    "documentation_policies": 40,
    "coding_ethics": 35,
    "claims_submission_accuracy": 40,
    "outpatient_coding_rules": 35,
    "diagnosis_rules": 30,
    # JAWDA
    "claims_review_requirements": 45,
    "accuracy_error_scoring": 45,
    "verification_logic": 40,
    "clinical_coding_process_review": 35,
    "scoring_weights": 30,
}

_AMA_HINT_KEYS = (
    "99202", "99203", "99204", "99205",
    "99212", "99213", "99214", "99215",
    "cpt", "code", "em", "mdm", "medical decision making",
    "stable chronic", "chronic illness", "hypertension",
    "time", "minutes", "total time", "2 of 3", "two of three",
    "risk", "data", "problem",
)

_HAAD_HINT_KEYS = (
    "query", "coder", "physician", "documentation", "medical necessity",
    "claims", "policy", "ethics", "upcoding", "downcoding",
)

_JAWDA_HINT_KEYS = (
    "jawda", "audit", "lama", "left ama", "finding", "score",
    "verification", "physician mismatch", "missing signature",
    "start time", "end time", "time-based",
)

_CMS_HINT_KEYS = (
    "hpi", "ros", "pfsh", "history", "exam", "review of systems",
    "past family social", "chief complaint", "documentation framework",
)

def _extract_cpt(text: str) -> str | None:
    match = _CPT_RE.search(text)
    return match.group(1) if match else None


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _summary_from_content(content: Any) -> str:
    """
    Extract a concise, human-readable summary from nested JSON content.
    Avoid dumping raw dicts into the API response.
    """
    preferred_keys = (
        "rule_text",
        "exact_definition",
        "description",
        "definition",
        "documentation_guideline",
        "note",
    )

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, dict):
        for key in preferred_keys:
            value = content.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        for value in content.values():
            summary = _summary_from_content(value)
            if summary:
                return summary

    if isinstance(content, list):
        for item in content:
            summary = _summary_from_content(item)
            if summary:
                return summary

    return ""


def _intent_section_keys(question: str, cpt_code: str | None, authority: str) -> set[str] | None:
    """
    Narrow the search to the most relevant sections first.
    This is not hardcoding answers; it is retrieval routing.
    """
    q = question.lower()

    if authority == "AMA_2021":
        if cpt_code or any(k in q for k in _AMA_HINT_KEYS):
            return {
                "time_based_codes",
                "mdm_2_of_3_rule",
                "mdm_levels",
                "problem_definitions",
                "risk_levels",
                "data_elements",
                "time_definition",
                "code_mapping",
            }

    if authority == "CMS_1997":
        if any(k in q for k in _CMS_HINT_KEYS):
            return {
                "documentation_of_history",
                "documentation_of_examination",
                "general_principles",
                "mdm_framework",
            }

    if authority in {"HAAD", "CLINICAL_CODING_PROCESS"}:
        if any(k in q for k in _HAAD_HINT_KEYS):
            return {
                "coder_query_process",
                "documentation_policies",
                "coding_ethics",
                "claims_submission_accuracy",
                "outpatient_coding_rules",
                "diagnosis_rules",
            }

    if authority == "JAWDA_2026":
        if any(k in q for k in _JAWDA_HINT_KEYS):
            return {
                "claims_review_requirements",
                "accuracy_error_scoring",
                "verification_logic",
                "clinical_coding_process_review",
                "scoring_weights",
            }

    return None


def _build_answer(cpt_code: str | None, chunk: GuidelineChunk) -> tuple[str, str]:
    """
    Return (answer, rule_text). Both should be concise and source-grounded.
    """
    content = chunk.content
    section = (chunk.section_key or "").lower()

    # AMA CPT-specific answers
    if cpt_code and isinstance(content, dict):
        if cpt_code in content and isinstance(content[cpt_code], dict):
            info = content[cpt_code]
            mdm = info.get("mdm_level", "")
            min_m = info.get("min_minutes", "")
            max_m = info.get("max_minutes", "")
            visit = info.get("visit_type", "")

            visit_label = "new-patient" if visit == "new" else "established-patient" if visit == "established" else "patient"
            answer_parts = [f"{cpt_code} is a {visit_label} code requiring {mdm} MDM."]

            if min_m and max_m:
                answer_parts.append(
                    f"Time-based billing requires {min_m}–{max_m} total minutes."
                )

            answer = " ".join(answer_parts)
            rule_text = f"{cpt_code} requires {mdm} MDM and {min_m}–{max_m} minutes."
            return answer, rule_text

        # code_mapping lookup
        if "code_mapping" in section:
            for visit_key in ("new_patient", "established_patient"):
                visit_map = content.get(visit_key)
                if isinstance(visit_map, dict):
                    for mdm_level, code in visit_map.items():
                        if code == cpt_code:
                            visit_label = visit_key.replace("_", " ")
                            answer = f"{cpt_code} maps to {mdm_level} MDM for a {visit_label}."
                            rule_text = answer
                            return answer, rule_text

    # AMA stable chronic / hypertension / definition-style questions
    if section == "problem_definitions" and isinstance(content, dict):
        stable = content.get("stable_chronic_illness")
        if isinstance(stable, dict):
            exact = stable.get("exact_definition", "")
            examples = stable.get("examples", [])
            ex_text = ", ".join(examples[:3]) if isinstance(examples, list) else ""
            answer = (
                f"Under AMA 2021, a stable chronic illness is {exact}. "
                f"Examples include {ex_text}."
            ).strip()
            rule_text = exact or "Stable chronic illness definition."
            return answer, rule_text

    if section == "mdm_2_of_3_rule" and isinstance(content, dict):
        rule_text = content.get("rule_text", "")
        answer = rule_text or "Two of the three MDM elements must be met or exceeded."
        return answer, rule_text or answer

    if section == "time_definition" and isinstance(content, dict):
        included = content.get("included_activities", [])
        excluded = content.get("excluded_activities", [])
        included_text = "; ".join(included[:4]) if isinstance(included, list) else ""
        excluded_text = "; ".join(excluded[:3]) if isinstance(excluded, list) else ""
        answer = (
            f"AMA 2021 counts activities such as {included_text} toward total time. "
            f"Excluded activities include {excluded_text}."
        ).strip()
        rule_text = content.get("source_section", "Time definition")
        return answer, rule_text

    # CMS / HAAD / JAWDA generic summary from the best matching section
    summary = _summary_from_content(content)
    if not summary:
        summary = chunk.section_name or chunk.section_key or "Relevant guideline content"

    answer = f"{summary} Source: {chunk.authority}, page {chunk.source_page or 'N/A'}."
    rule_text = summary
    return answer, rule_text


async def answer_question(question: str, db: AsyncSession) -> dict:
    decision = route_authority(question)
    authority = decision.primary_authority
    cpt_code = _extract_cpt(question)
    q_tokens = _tokenize(question)

    result = await db.execute(
        select(GuidelineChunk).where(GuidelineChunk.authority == authority)
    )
    chunks = result.scalars().all()

    preferred_keys = _intent_section_keys(question, cpt_code, authority)

    def chunk_score(chunk: GuidelineChunk) -> int:
        score = 0
        content_text = str(chunk.content).lower()
        section_key = (chunk.section_key or "").lower()
        section_name = (chunk.section_name or "").lower()

        score += _SECTION_PRIORITY.get(section_key, 0)

        if preferred_keys and chunk.section_key in preferred_keys:
            score += 40

        if cpt_code and cpt_code in content_text:
            score += 30

        for token in q_tokens:
            if token in content_text or token in section_key or token in section_name:
                score += 2

        # Give strong preference to exact-topic sections instead of random match
        if authority == "AMA_2021" and cpt_code:
            if chunk.section_key == "time_based_codes":
                score += 30
            if chunk.section_key == "mdm_2_of_3_rule":
                score += 20

        if authority == "AMA_2021" and any(k in question.lower() for k in ("stable chronic", "hypertension", "chronic illness")):
            if chunk.section_key == "problem_definitions":
                score += 30

        if authority == "HAAD" and any(k in question.lower() for k in ("query", "documentation", "medical necessity", "claims", "ethics")):
            if chunk.section_key in {"coder_query_process", "documentation_policies", "claims_submission_accuracy", "coding_ethics"}:
                score += 25

        if authority == "JAWDA_2026" and any(k in question.lower() for k in ("lama", "audit", "physician mismatch", "verification", "score")):
            if chunk.section_key in {"claims_review_requirements", "accuracy_error_scoring", "verification_logic", "scoring_weights"}:
                score += 25

        return score

    best_chunk = max(chunks, key=chunk_score, default=None)

    if not best_chunk:
        return {
            "answer": (
                "The provided documents do not contain enough information "
                "to answer this question."
            ),
            "authority": authority,
            "source_section": "Fallback",
            "source_page": "N/A",
            "confidence": "insufficient_information",
            "rule_text": "",
        }

    answer, rule_text = _build_answer(cpt_code, best_chunk)

    return {
        "answer": answer,
        "authority": best_chunk.authority,
        "source_section": best_chunk.section_name or best_chunk.section_key,
        "source_page": best_chunk.source_page or "N/A",
        "confidence": "direct_rule_match",
        "rule_text": rule_text[:500],
    }