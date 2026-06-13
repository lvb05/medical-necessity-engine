from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Final
from app.retrieval.rule_loader import (
    AMA_CPT_CODES,
    AUTHORITY_AMA,
    AUTHORITY_CMS,
    AUTHORITY_HAAD,
    AUTHORITY_JAWDA,
)

_CPT_RE = re.compile(r"\b99(?:202|203|204|205|212|213|214|215)\b")
_JAWDA_KEYWORDS: Final[tuple[str, ...]] = (
    "jawda",
    "audit",
    "kpi",
    "lama",
    "left ama",
    "time-based",
    "time based",
    "signature",
    "physician match",
    "drg",
    "compliance",
    "score",
    "finding",
    "verification",
)

_HAAD_KEYWORDS: Final[tuple[str, ...]] = (
    "haad",
    "abu dhabi",
    "doh",
    "coder query",
    "query process",
    "pre-auth",
    "preauthorization",
    "pre authorization",
    "documentation policy",
    "documentation policies",
    "training",
    "ethics",
    "medical necessity",
    "claims submission",
    "facility policy",
    "coding practice",
    "outpatient visit coding",
    "narrative diagnosis",
    "copy-paste",
    "copy paste",
    "claims accuracy",
    "denial",
    "denials",
)

_AMA_KEYWORDS: Final[tuple[str, ...]] = (
    "ama",
    "em code",
    "e/m",
    "mdm",
    "medical decision making",
    "stable chronic illness",
    "chronic illness",
    "acute uncomplicated",
    "risk of complications",
    "data reviewed",
    "time-based",
    "99202",
    "99203",
    "99204",
    "99205",
    "99212",
    "99213",
    "99214",
    "99215",
)

_CMS_KEYWORDS: Final[tuple[str, ...]] = (
    "history",
    "chief complaint",
    "hpi",
    "ros",
    "review of systems",
    "pfsh",
    "past family social",
    "physical examination",
    "physical exam",
    "exam",
    "bullet elements",
    "documentation framework",
    "comprehensive history",
    "problem focused",
    "expanded problem focused",
    "detailed",
    "comprehensive",
)

@dataclass(frozen=True, slots=True)
class RouteDecision:
    primary_authority: str
    fallback_authority: str | None
    context: str
    reason: str
    authority_chain: tuple[str, ...]
    matched_terms: tuple[str, ...]

def _detect_cpt_code(question: str) -> str | None:
    match = _CPT_RE.search(question)
    return match.group(0) if match else None


def _contains_any(text: str, keywords: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted({kw for kw in keywords if kw in text}))


def _is_ama_outpatient_code(code: str | None) -> bool:
    if not code:
        return False
    code = code.strip()
    return code in AMA_CPT_CODES

def route_authority(question: str, code: str | None = None) -> RouteDecision:
    """
    Decide which authority should answer the query.
    Priority:
    1) JAWDA audit/compliance
    2) HAAD local process rules
    3) AMA 2021 E/M code selection
    4) CMS 1997 fallback documentation
    """
    text = (question or "").lower().strip()
    detected_code = (code or "").strip() or _detect_cpt_code(text)

    jawda_hits = _contains_any(text, _JAWDA_KEYWORDS)
    haad_hits = _contains_any(text, _HAAD_KEYWORDS)
    ama_hits = _contains_any(text, _AMA_KEYWORDS)
    cms_hits = _contains_any(text, _CMS_KEYWORDS)

    ama_code_match = _is_ama_outpatient_code(detected_code)

    if jawda_hits:
        chain = [AUTHORITY_JAWDA]
        if ama_code_match or ama_hits:
            chain.append(AUTHORITY_AMA)
        chain.append(AUTHORITY_HAAD)
        chain.append(AUTHORITY_CMS)

        return RouteDecision(
            primary_authority=AUTHORITY_JAWDA,
            fallback_authority=chain[1] if len(chain) > 1 else None,
            context="audit_review",
            reason=(
                "Query matches JAWDA audit/compliance terms "
                f"({', '.join(jawda_hits)})."
            ),
            authority_chain=tuple(chain),
            matched_terms=jawda_hits,
        )

    if haad_hits:
        chain = [AUTHORITY_HAAD]
        if ama_code_match or ama_hits:
            chain.append(AUTHORITY_AMA)
        chain.append(AUTHORITY_CMS)

        return RouteDecision(
            primary_authority=AUTHORITY_HAAD,
            fallback_authority=chain[1] if len(chain) > 1 else None,
            context="local_process_rules",
            reason=(
                "Query matches HAAD/local process terms "
                f"({', '.join(haad_hits)})."
            ),
            authority_chain=tuple(chain),
            matched_terms=haad_hits,
        )

    if ama_code_match or ama_hits:
        chain = [AUTHORITY_AMA, AUTHORITY_CMS]
        return RouteDecision(
            primary_authority=AUTHORITY_AMA,
            fallback_authority=AUTHORITY_CMS,
            context="em_code_selection",
            reason=(
                "Query matches AMA 2021 E/M selection terms "
                f"(code={detected_code or 'none'}, terms={', '.join(ama_hits)})."
            ),
            authority_chain=tuple(chain),
            matched_terms=ama_hits,
        )

    if cms_hits:
        return RouteDecision(
            primary_authority=AUTHORITY_CMS,
            fallback_authority=None,
            context="documentation_framework",
            reason=(
                "Query matches CMS 1997 documentation framework terms "
                f"({', '.join(cms_hits)})."
            ),
            authority_chain=(AUTHORITY_CMS,),
            matched_terms=cms_hits,
        )

    return RouteDecision(
        primary_authority=AUTHORITY_CMS,
        fallback_authority=None,
        context="general_fallback",
        reason="No higher-specificity rule matched; using CMS 1997 fallback.",
        authority_chain=(AUTHORITY_CMS,),
        matched_terms=(),
    )

route_for_code_selection = route_authority