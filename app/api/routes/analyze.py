from fastapi import APIRouter

from app.schemas import AnalyzeRequest, AnalyzeResponse, AuditFindingOut, Citation, DocumentationGap
from app.engines.gap_detector import analyze_encounter
from app.retrieval.authority_router import route_authority
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import QueryLog
router = APIRouter(prefix="/api", tags=["Analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_encounter_api(
    payload: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
):
    route = route_authority(question=payload.billed_code, code=payload.billed_code)
    analysis = analyze_encounter(payload.model_dump())

    audit_findings = [
        AuditFindingOut(
            finding_id=finding.finding_id,
            category=finding.category,
            points_deducted=finding.points_deducted,
            description=finding.description,
            authority=finding.citation.authority,
            source_section=finding.citation.source_section,
            source_page=finding.citation.source_page,
        )
        for finding in analysis["audit_findings"]
    ]

    citations = [
        Citation(
            authority=item["authority"],
            source_section=item["source_section"],
            source_page=item["source_page"],
        )
        for item in analysis["citations"]
    ]

    if audit_findings:
        route_chain = list(route.authority_chain)
        if "JAWDA_2026" not in route_chain:
            route_chain.insert(0, "JAWDA_2026")
    else:
        route_chain = list(route.authority_chain)

    documentation_gaps = []
    for gap in analysis["documentation_gaps"]:
        documentation_gaps.append(
            DocumentationGap(
                gap=gap["gap"],
                authority=gap["authority"],
                source_section=gap["source_section"],
                source_page=gap["source_page"],
            )
        )
    
    db.add(
        QueryLog(
            endpoint="/api/analyze",
            billed_code=payload.billed_code,
            authority_used=" -> ".join(route_chain),
            answer=(
                f"Supported={analysis['code_supported']}, "
                f"Recommended={analysis['recommended_code']}"
            ),
            denial_risk=analysis["denial_risk"],
        )
    )
    try:
        await db.commit()
    except Exception:
        await db.rollback()

    return AnalyzeResponse(
        billed_code=payload.billed_code,
        code_supported=analysis["code_supported"],
        recommended_code=analysis["recommended_code"],
        documentation_gaps=documentation_gaps,
        audit_findings=audit_findings,
        denial_risk=analysis["denial_risk"],
        authority_chain=route_chain,
        citations=citations,
    )