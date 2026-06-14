# Medical Necessity Assistant

> A clinical AI platform for healthcare providers in the UAE to understand E/M coding levels, manage claim denials, and stay compliant with JAWDA audit requirements.

**Live Deployment:** https://medical-necessity-engine.onrender.com/  
**Repository:** https://github.com/lvb05/medical-necessity-engine

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Authorities & Compliance](#authorities--compliance)
5. [API Endpoints](#api-endpoints)
6. [Sample Requests & Responses](#sample-requests--responses)
7. [Local Setup](#local-setup)
8. [Docker Setup](#docker-setup)
9. [Deployment](#deployment)
10. [Test Results](#test-results)
11. [Document Processing Approach](#document-processing-approach)
12. [AMA 2021 vs CMS 1997 Supersession](#ama-2021-vs-cms-1997-supersession)
13. [Future Improvements](#future-improvements)

---

## Project Overview

The **Medical Necessity Assistant** answers critical clinical coding questions for healthcare providers:

- *"Does this visit qualify for a 99214?"* → Powered by AMA 2021 E/M guidelines
- *"My claim was denied for lack of medical necessity — what's missing?"* → Gap detection engine
- *"What score will we get in JAWDA audit if the LAMA form is missing?"* → Audit compliance checker
- *"Is hypertension a stable chronic illness under AMA 2021?"* → Evidence-based definitions

### Key Differentiators

| Feature | How It Works |
|---------|-------------|
| **No Hallucination** | Every answer cites exact source + page number |
| **Multi-Authority Routing** | Questions routed to HAAD → JAWDA → AMA → CMS intelligently |
| **Encounter Analysis** | Analyzes actual visit documentation against MDM table |
| **Denial Risk Prediction** | Quantifies risk: `low` \| `moderate` \| `high` |
| **JAWDA Compliance** | Validates LAMA forms, physician matches, start/end times |

---

## Architecture

### System Components

┌─────────────────────────────────────────────────────────────────┐ │ FastAPI Web Application │ │ ┌─────────────────────────────────────────────────────────┐ │ │ │ API Layer (routes/) │ │ │ │ ├─ POST /api/ask → Answer guideline questions │ │ │ │ └─ POST /api/analyze → Analyze patient encounters │ │ │ └─────────────────────────────────────────────────────────┘ │ │ ↓ │ │ ┌─────────────────────────────────────────────────────────┐ │ │ │ Business Logic (engines/) │ │ │ │ ├─ ask_engine.py → Question answering + routing │ │ │ │ ├─ gap_detector.py → Documentation gap analysis │ │ │ │ ├─ mdm.py → MDM calculation (2-of-3 rule) │ │ │ │ ├─ audit_checker.py → JAWDA compliance checks │ │ │ │ ├─ time_validator.py → Time-based code validation │ │ │ │ └─ documentation_checker.py → History level eval │ │ │ └─────────────────────────────────────────────────────────┘ │ │ ↓ │ │ ┌─────────────────────────────────────────────────────────┐ │ │ │ Retrieval Layer (retrieval/) │ │ │ │ ├─ authority_router.py → Route to correct authority │ │ │ │ └─ rule_loader.py → Load and validate rules │ │ │ └─────────────────────────────────────────────────────────┘ │ │ ↓ │ │ ┌─────────────────────────────────────────────────────────┐ │ │ │ Data Layer │ │ │ │ ├─ PostgreSQL Database (async via SQLAlchemy) │ │ │ │ │ ├─ QueryLog (audit trail) │ │ │ │ │ ├─ GuidelineDocument (metadata) │ │ │ │ │ └─ GuidelineChunk (searchable content) │ │ │ │ └─ JSON Rules Files (rules/ directory) │ │ │ │ ├─ ama_2021.json │ │ │ │ ├─ cms_1997.json │ │ │ │ ├─ haad_process.json │ │ │ │ ├─ jawda_part_ix.json │ │ │ │ └─ clinical_coding_process.json │ │ │ └─────────────────────────────────────────────────────────┘ │ └─────────────────────────────────────────────────────────────────┘