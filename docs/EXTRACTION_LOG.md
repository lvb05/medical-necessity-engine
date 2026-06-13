# Rule Extraction Log

**Extracted**: 2024-01-13  
**Status**: Complete  
**Files Created**: 5 JSON files  

---

## Document-to-File Mapping

| Source PDF | Output JSON | Authority Rank | Purpose |
|---|---|---|---|
| AMA_Guidelines.txt | `ama_2021.json` | 2 | MDM Table, time thresholds, problem definitions |
| 97_Doc_guidelines.txt | `cms_1997.json` | 3 | History types, ROS, PFSH, documentation framework |
| JAWDA Part IX | `jawda_part_ix.json` | Local (Audit) | Audit findings, time-based code requirement, LAMA forms |
| CodingManual.txt + Clinical Process Review | `haad_process.json` | 1 | Authority hierarchy, coder requirements, query triggers |
| clinical_coding_process_review.txt | `clinical_coding_process.json` | Local (Process) | Coding process review, documentation policies, training |

---

## Extraction Details

### 1. AMA 2021 (`rules/ama_2021.json`)
- **Sections Extracted**:
  - MDM 2-of-3 rule
  - Code descriptors (99202-99215)
  - Problem definitions (stable chronic illness, acute uncomplicated, etc.)
  - Time definition and included/excluded activities
  - Data elements (analyzed, combination, etc.)

- **Source Pages**: CPT code descriptors, MDM definitions section

- **Key Rules**:
  - Straightforward (99202/99212): 15-29 min (new), 10-19 min (est)
  - Low (99203/99213): 30-44 min (new), 20-29 min (est)
  - Moderate (99204/99214): 45-59 min (new), 30-39 min (est)
  - High (99205/99215): 60-74 min (new), 40-54 min (est)

### 2. CMS 1997 (`rules/cms_1997.json`)
- **Sections Extracted**:
  - History types table (Problem Focused, Expanded, Detailed, Comprehensive)
  - Chief Complaint definition
  - HPI definition (Brief: 1-3 elements, Extended: ≥4 elements or ≥3 chronic conditions)
  - ROS systems (14 recognized systems)
  - PFSH components (Past, Family, Social)
  - General principles of medical record documentation

- **Source Pages**: History, Examination, and MDM sections

- **Key Rules**:
  - Brief HPI: 1-3 elements
  - Extended HPI: ≥4 elements OR status of ≥3 chronic conditions
  - Complete ROS: ≥10 systems documented
  - Complete PFSH (New): ≥1 item from each of 3 areas
  - Complete PFSH (Established): ≥1 item from 2 of 3 areas

### 3. JAWDA Part IX (`rules/jawda_part_ix.json`)
- **Sections Extracted**:
  - Time-based code requirements (start AND end times required, not total time alone)
  - LAMA form requirements (duly signed)
  - Audit findings table (Major/Moderate/Minor categories)
  - Error scoring (100 pts for signature mismatch, 20 pts for various violations)
  - Verification logic for audit checks

- **Source Pages**: Sections 8.2.2, 4.2.1, and APPENDIX-III

- **Key Findings**:
  - Major (100 pts): Signature/detail mismatch
  - Major (20 pts each): Physician mismatch, DRG incorrect, LAMA missing
  - Moderate (10 pts): Encounter type error, billing errors
  - Minor (5 pts): Date errors, demographic issues

### 4. HAAD + Process (`rules/haad_process.json`)
- **Sections Extracted**:
  - Authority hierarchy (HAAD > AMA 2021 > CMS 1997)
  - Coding ethics standards
  - Coder requirements (reference access, ethics, query process, pre-auth)
  - Coder query triggers (4 main triggers)
  - Documentation policies (timeliness, completeness, medical necessity)
  - Claims review checkpoints

- **Source Pages**: Section 1 (Coding Guidelines), Coding Practice Policies

- **Key Triggers**:
  - Documentation unclear/insufficient
  - Diagnosis not supported
  - Reason for visit unclear
  - Services without documentation

### 5. Clinical Coding Process (`rules/clinical_coding_process.json`)
- **Sections Extracted**:
  - Document purpose (JAWDA audit domain)
  - Audit assessment areas (process, policies, documentation)
  - Documentation recommendations (timeliness, completeness, necessity)
  - Training recommendations
  - Key interview areas
  - Claims submission accuracy checks
  - Risk areas (violations, insufficient docs, non-compliance)
  - Quality measurement criteria (accuracy, completeness)

- **Source Pages**: Clinical Coding Process Review sections

- **Key Risk Areas**:
  - HAAD guideline violation
  - Insufficient documentation for code level
  - Place of service error
  - Medical necessity not documented

---

## Extraction Standards Applied

**Exact Text Only**: Every rule includes exact quotes from source documents  
**Source Tracking**: All rules tagged with source section and page  
**No Paraphrasing**: Original document language preserved  
**Complete Citations**: Every finding includes source location  
**Authority Hierarchy**: HAAD > AMA 2021 > CMS 1997 maintained  

---

## Validation Checklist

- [x] All 5 JSON files created
- [x] Every rule has source document reference
- [x] Authority hierarchy documented
- [x] Time thresholds extracted (AMA 2021)
- [x] Audit findings extracted (JAWDA Part IX)
- [x] Coder query triggers extracted (HAAD + Process)
- [x] Documentation policies extracted (CMS 1997)
- [x] No invented or paraphrased content
- [x] EXTRACTION_LOG.md completed

---

## Next Steps

**Phase 1**: Project skeleton (30 min)  
**Phase 2**: Database schema (45 min)  
**Phase 3**: Document ingestion (1 hour)  
**Phase 4**: Rule engines (3-4 hours)  

Estimated Total: **15-18 hours**

---

## Files Ready for Phase 1
