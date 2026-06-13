from dataclasses import dataclass

@dataclass
class Citation:
    authority: str
    source_section: str
    source_page: int | str

@dataclass
class MDMResult:
    mdm_level: str
    recommended_code: str
    citation: Citation

@dataclass
class TimeValidationResult:
    valid: bool
    findings: list
    citation: Citation

@dataclass
class AuditFinding:
    finding_id: str
    category: str
    points_deducted: int
    description: str
    citation: Citation