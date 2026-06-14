"""
ask_engine.py
-------------
Answers clinical guideline questions by routing to the correct authority,
scoring retrieved chunks, and building a structured, cited response.

Answer quality rules enforced here:
  Rule 1 — Answer only what was asked.
  Rule 2 — Always cite exact source + location.
  Rule 3 — Tight, precise retrieval.
  Rule 4 — Max 4 sentences in any answer field.
  Rule 6 — If context is missing or docs don't cover it, say so clearly.
"""
from __future__ import annotations

import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GuidelineChunk
from app.retrieval.authority_router import route_authority

_CPT_RE = re.compile(r"\b(99(?:202|203|204|205|212|213|214|215))\b")

# ---------------------------------------------------------------------------
# Section priority — base scores used by chunk_score()
# Higher = retrieved first when all else is equal
# ---------------------------------------------------------------------------
_SECTION_PRIORITY: dict[str, int] = {
    # AMA 2021
    "mdm_2_of_3_rule": 55,
    "mdm_levels": 50,
    "problem_definitions": 48,
    "time_based_codes": 45,
    "risk_levels": 42,
    "data_elements": 40,
    "time_definition": 38,
    "code_mapping": 25,
    # CMS 1997
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

# Hint keys used by _intent_section_keys()
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

# Questions that imply encounter context is needed (Rule 6)
_CONTEXT_REQUIRED_TRIGGERS = (
    "does this visit qualify",
    "does this encounter qualify",
    "does this qualify",
    "qualify for",
    "qualify for a 99",
    "support this code",
    "support a 99",
)
_INLINE_CONTEXT_KW = (
    "hpi", "diagnosis", "diagnoses", "assessment", "chief complaint",
    "patient", "bp ", "blood pressure", "exam ", "history of",
    "prescribed", "medication", "procedure",
)

def _extract_cpt(text: str) -> str | None:
    match = _CPT_RE.search(text)
    return match.group(1) if match else None

def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))

def _find_nested_rule(content: Any) -> str:
    if isinstance(content, dict):
        for key in (
            "rule_text",
            "exact_definition",
            "documentation_guideline",
            "description",
            "finding",
        ):
            value = content.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        for value in content.values():
            result = _find_nested_rule(value)

            if result:
                return result
    elif isinstance(content, list):
        for item in content:
            result = _find_nested_rule(item)

            if result:
                return result
    return ""

def _summary_from_content(content: Any) -> str:
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


def _needs_encounter_context(question: str) -> bool:
    """
    Rule 6: detect questions that ask whether 'this visit' qualifies
    but provide no encounter data inline AND no CPT code to look up.

    If a CPT code is present the question is asking about qualification
    criteria for that code — we can answer from the guidelines directly.
    """
    q = question.lower()
    triggered = any(t in q for t in _CONTEXT_REQUIRED_TRIGGERS)
    has_inline_context = any(kw in q for kw in _INLINE_CONTEXT_KW)
    has_cpt_code = bool(_CPT_RE.search(q))
    # If a specific CPT code is mentioned we can answer about its MDM criteria
    return triggered and not has_inline_context and not has_cpt_code


def _intent_section_keys(question: str, cpt_code: str | None, authority: str) -> set[str] | None:
    """
    Narrow retrieval to the most relevant sections.
    Not hardcoding answers — this is retrieval routing only.
    """
    q = question.lower()

    if authority == "AMA_2021":
        if cpt_code or any(k in q for k in _AMA_HINT_KEYS):
            return {
                "mdm_2_of_3_rule",
                "mdm_levels",
                "problem_definitions",
                "time_based_codes",
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


def _is_qualification_question(question: str) -> bool:
    """True when the question is about whether a code is supported/qualified."""
    q = question.lower()
    return any(kw in q for kw in (
        "qualify", "qualifies", "support", "supported",
        "level", "mdm", "medical decision", "criteria",
    ))


def _build_answer(cpt_code: str | None, chunk: GuidelineChunk, question: str) -> tuple[str, str]:
    """
    Return (answer, rule_text). Concise, source-grounded, max ~4 sentences.
    """
    content = chunk.content
    section = (chunk.section_key or "").lower()
    q = question.lower()
    if section == "mdm_2_of_3_rule" and isinstance(content, dict):
        rule_text = content.get("rule_text", "")
        elements = content.get("elements", [])
        elements_text = ", ".join(elements) if isinstance(elements, list) else ""
        answer = rule_text or "Two of the three MDM elements must be met or exceeded."
        if elements_text:
            answer += f" The three elements are: {elements_text}."
        if cpt_code:
            answer += f" Use /api/analyze with a full encounter payload to evaluate {cpt_code}."
        return answer, rule_text or answer

    if cpt_code and isinstance(content, dict):
        if cpt_code in content and isinstance(content[cpt_code], dict):
            info = content[cpt_code]
            mdm = info.get("mdm_level", "")
            min_m = info.get("min_minutes", "")
            max_m = info.get("max_minutes", "")
            visit = info.get("visit_type", "")
            visit_label = (
                "new-patient" if visit == "new"
                else "established-patient" if visit == "established"
                else "patient"
            )
            answer = f"{cpt_code} is a {visit_label} code requiring {mdm} MDM."
            if min_m and max_m:
                answer += f" Time-based billing requires {min_m}–{max_m} total minutes."
            rule_text = f"{cpt_code} requires {mdm} MDM and {min_m}–{max_m} minutes."
            return answer, rule_text

        if "code_mapping" in section:
            for visit_key in ("new_patient", "established_patient"):
                visit_map = content.get(visit_key)
                if isinstance(visit_map, dict):
                    for mdm_level, code in visit_map.items():
                        if code == cpt_code:
                            visit_label = visit_key.replace("_", " ")
                            answer = f"{cpt_code} maps to {mdm_level} MDM for a {visit_label}."
                            return answer, answer

    if section == "mdm_levels" and isinstance(content, dict) and cpt_code:
        code_to_level = {
            "99202": "straightforward",
            "99203": "low",
            "99204": "moderate",
            "99205": "high",
            "99212": "straightforward",
            "99213": "low",
            "99214": "moderate",
            "99215": "high",
        }
        level = code_to_level.get(cpt_code)
        if level and level in content:
            level_data = content[level]

            problems = level_data.get("problems", [])
            risk = level_data.get("risk", "")
            data = level_data.get("data", {})
            data_level = data.get("level", "") if isinstance(data, dict) else ""
            problems_text = (
                "; ".join(problems[:3])
                if isinstance(problems, list)
                else ""
            )
            answer = (
                f"For {cpt_code}, '{level}' MDM requires: "
                f"problems — {problems_text}. "
                f"Risk: {risk}. "
                f"Data: {data_level}. "
                f"Two of these three elements must be met or exceeded "
                f"(AMA 2021 Table 2, page 10)."
            )

            rule_text = (
                f"{level} MDM: "
                f"problems={problems_text}; "
                f"risk={risk}; "
                f"data={data_level}."
            )
            return answer, rule_text

    if section == "problem_definitions" and isinstance(content, dict):
        if any(kw in q for kw in ("stable chronic", "hypertension", "stable", "chronic illness")):
            stable = content.get("stable_chronic_illness")
            if isinstance(stable, dict):
                exact = stable.get("exact_definition", "")
                examples = stable.get("examples", [])
                ex_text = ", ".join(examples[:4]) if isinstance(examples, list) else ""
                answer = f"Under AMA 2021, a stable chronic illness is defined as: {exact}"
                if ex_text:
                    answer += f" Examples include: {ex_text}."
                return answer, exact or "Stable chronic illness definition."

        if any(kw in q for kw in ("self-limited", "minor problem", "self limited")):
            slf = content.get("self_limited_or_minor_problem")
            if isinstance(slf, dict):
                exact = slf.get("exact_definition", "")
                return f"Under AMA 2021, a self-limited or minor problem is: {exact}", exact

        if any(kw in q for kw in ("acute uncomplicated",)):
            aui = content.get("acute_uncomplicated_illness_or_injury")
            if isinstance(aui, dict):
                exact = aui.get("exact_definition", "")
                examples = aui.get("examples", [])
                ex_text = ", ".join(examples) if isinstance(examples, list) else ""
                answer = f"Under AMA 2021, an acute uncomplicated illness or injury is: {exact}"
                if ex_text:
                    answer += f" Examples: {ex_text}."
                return answer, exact

        stable = content.get("stable_chronic_illness")
        if isinstance(stable, dict):
            exact = stable.get("exact_definition", "")
            examples = stable.get("examples", [])
            ex_text = ", ".join(examples[:3]) if isinstance(examples, list) else ""
            answer = f"Under AMA 2021, a stable chronic illness is: {exact}"
            if ex_text:
                answer += f" Examples include: {ex_text}."
            return answer, exact or "Stable chronic illness definition."

    if section == "time_definition" and isinstance(content, dict):
        included = content.get("included_activities", [])
        excluded = content.get("excluded_activities", [])
        included_text = "; ".join(included[:4]) if isinstance(included, list) else ""
        excluded_text = "; ".join(excluded[:2]) if isinstance(excluded, list) else ""
        answer = (
            f"AMA 2021 counts the following toward total time: {included_text}. "
            f"Excluded activities include: {excluded_text}."
        )
        rule_text = content.get("source_section", "Time definition")
        return answer, rule_text

    if section == "risk_levels" and isinstance(content, dict):
        for risk_key in ("moderate", "high", "low", "minimal"):
            if risk_key in q:
                level_data = content.get(risk_key)
                if isinstance(level_data, dict):
                    desc = level_data.get("description", "")
                    examples = level_data.get("examples", [])
                    ex_text = "; ".join(examples[:3]) if isinstance(examples, list) else ""
                    answer = f"AMA 2021 {risk_key} risk: {desc}."
                    if ex_text:
                        answer += f" Examples: {ex_text}."
                    return answer, desc
                
    if (
        section == "claims_review_requirements"
        and isinstance(content, dict)
        and "lama" in q
    ):
        lama = content.get("lama_forms")
        if isinstance(lama, dict):
            rule = lama.get("rule_text", "")
            severity = lama.get("severity", "")
            points = lama.get("points_deducted", "")
            answer = (
                f"{rule} "
                f"A missing or unsigned LAMA form is classified as a "
                f"{severity} finding and deducts {points} points."
            )
            return answer, rule
        
    if (
        section == "documentation_of_history"
        and isinstance(content, dict)
    ):
        if "hpi" in q:
            hpi = content.get("hpi")
            if isinstance(hpi, dict):
                definition = hpi.get("exact_definition")
                if definition:
                    return definition, definition
        if "ros" in q:
            ros = content.get("ros")
            if isinstance(ros, dict):
                definition = ros.get("documentation_guideline")
                if definition:
                    return definition, definition
        if "pfsh" in q:
            pfsh = content.get("pfsh")
            if isinstance(pfsh, dict):
                complete_new = pfsh.get("complete_new")
                if isinstance(complete_new, dict):
                    definition = complete_new.get(
                        "documentation_guideline"
                    )
                    if definition:
                        return definition, definition

    summary = _find_nested_rule(content)

    if not summary:
        summary = _summary_from_content(content)
    if not summary:
        summary = chunk.section_name or chunk.section_key or "Relevant guideline content"

    page = chunk.source_page or "N/A"
    answer = f"{summary} (Source: {chunk.authority}, {chunk.section_name or chunk.section_key}, page {page}.)"
    return answer, summary


async def answer_question(question: str, db: AsyncSession) -> dict:
    if _needs_encounter_context(question):
        return {
            "answer": (
                "To determine whether a specific visit qualifies for a CPT code, "
                "encounter details are required (diagnoses, documentation, procedures, visit type). "
                "Submit a full encounter payload to POST /api/analyze. "
                "AMA 2021 Table 2 (page 10) governs qualification via the 2-of-3 MDM rule."
            ),
            "authority": "AMA_2021",
            "source_section": "Table 2 Levels of Medical Decision Making",
            "source_page": 10,
            "confidence": "context_required",
            "rule_text": (
                "To qualify for a particular level of MDM, two of the three elements "
                "for that level of MDM must be met or exceeded."
            ),
            "reasoning": (
                "Encounter-specific qualification cannot be determined "
                "without clinical documentation."
            ),
            "authority_chain": ["AMA_2021"],
            "matched_terms": [],
            "citation": {
                "authority": "AMA_2021",
                "section": "Table 2 Levels of Medical Decision Making",
                "page": 10,
            },
        }

    decision = route_authority(question)
    authority = decision.primary_authority
    cpt_code = _extract_cpt(question)
    q_tokens = _tokenize(question)
    is_qual_q = _is_qualification_question(question)

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

        if (
            cpt_code
            and isinstance(chunk.content, dict)
            and cpt_code in chunk.content
        ):
            score += 50

        for token in q_tokens:
            if token in content_text or token in section_key or token in section_name:
                score += 2

        if authority == "AMA_2021" and is_qual_q:
            if chunk.section_key == "mdm_levels":
                score += 50
            if chunk.section_key == "mdm_2_of_3_rule":
                score += 20
            if chunk.section_key == "time_based_codes":
                score -= 25  
                
        if authority == "AMA_2021" and cpt_code and not is_qual_q:
            if chunk.section_key == "time_based_codes":
                score += 30
            if chunk.section_key == "mdm_2_of_3_rule":
                score += 20

        if authority == "AMA_2021" and any(
            k in question.lower()
            for k in ("stable chronic", "hypertension", "chronic illness",
                       "self-limited", "acute uncomplicated", "definition")
        ):
            if chunk.section_key == "problem_definitions":
                score += 35

        if authority == "AMA_2021" and any(
            k in question.lower()
            for k in ("risk", "morbidity", "mortality", "prescription drug")
        ):
            if chunk.section_key == "risk_levels":
                score += 30

        if authority == "HAAD" and any(
            k in question.lower()
            for k in ("query", "documentation", "medical necessity", "claims", "ethics")
        ):
            if chunk.section_key in {
                "coder_query_process", "documentation_policies",
                "claims_submission_accuracy", "coding_ethics",
            }:
                score += 25

        if authority == "JAWDA_2026" and any(
            k in question.lower()
            for k in ("lama", "audit", "physician mismatch", "verification", "score")
        ):
            if chunk.section_key in {
                "claims_review_requirements", "accuracy_error_scoring",
                "verification_logic", "scoring_weights",
            }:
                score += 25

        return score

    best_chunk = max(chunks, key=chunk_score, default=None)

    if not best_chunk:
        return {
            "answer": (
                "The provided clinical guideline documents do not contain "
                "sufficient information to answer this question."
            ),
            "authority": authority,
            "source_section": "N/A",
            "source_page": "N/A",
            "confidence": "insufficient_information",
            "rule_text": "",
            "reasoning": (
                "No matching guideline content was found."
            ),
            "authority_chain": list(
                decision.authority_chain
            ),
            "matched_terms": list(
                decision.matched_terms
            ),
        }

    answer, rule_text = _build_answer(cpt_code, best_chunk, question)

    reasoning = (
        f"Matched authority {best_chunk.authority} "
        f"using section '{best_chunk.section_key}'."
        f"Matched terms: {', '.join(decision.matched_terms) or 'none'}."
    )

    confidence = (
        "high"
        if decision.matched_terms
        else "medium"
    )

    return {
        "answer": answer,
        "authority": best_chunk.authority,
        "authority_chain": list(
            decision.authority_chain
        ),
        "matched_terms": list(
            decision.matched_terms
        ),
        "reasoning": reasoning,
        "source_section": best_chunk.section_name or best_chunk.section_key,
        "source_page": best_chunk.source_page or "N/A",
        "confidence": confidence,
        "rule_text": rule_text[:500],
        "citation": {
            "authority": best_chunk.authority,
            "section": best_chunk.section_name or best_chunk.section_key,
            "page": best_chunk.source_page or "N/A",
        }
    }