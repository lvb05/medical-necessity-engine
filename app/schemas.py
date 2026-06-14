from typing import Any, Optional
from pydantic import BaseModel, Field

class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)

class Citation(BaseModel):
    authority: str
    section: str
    page: int | str

class SimpleCitation(BaseModel):
    authority: str
    section: str
    page: int | str

class AskResponse(BaseModel):
    answer: str
    authority: str
    authority_chain: list[str] = []
    matched_terms: list[str] = []
    reasoning: str | None = None
    source_section: str
    source_page: int | str
    confidence: str
    rule_text: str | None = None
    citation: Citation | None = None

class DocumentationInput(BaseModel):
    HPI: str | None = None
    exam: str | None = None
    assessment: str | None = None

class AnalyzeRequest(BaseModel):
    visit_type: str
    chief_complaint: str
    diagnoses: list[str] = []
    procedures: list[str] = []
    documentation: DocumentationInput
    billed_code: str
    total_time_minutes: int | None = None
    start_time: str | None = None
    end_time: str | None = None
    billed_physician: str | None = None
    actual_physician: str | None = None
    lama_required: bool = False
    lama_signed: bool = True

class AuditFindingOut(BaseModel):
    finding_id: str
    category: str
    points_deducted: int
    description: str
    authority: str
    source_section: str
    source_page: int | str

class DocumentationGap(BaseModel):
    gap: str
    authority: str
    source_section: str
    source_page: int | str

class AnalyzeResponse(BaseModel):
    billed_code: str
    code_supported: bool
    recommended_code: str
    documentation_gaps: list[DocumentationGap]
    audit_findings: list[AuditFindingOut]
    denial_risk: str
    authority_chain: list[str]
    citations: list[Citation]

class HealthResponse(BaseModel):
    status: str