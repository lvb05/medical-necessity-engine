# Medical Necessity Assistant

> A clinical AI platform for healthcare providers in the UAE to understand E/M coding levels, manage claim denials, and stay compliant with JAWDA audit requirements.

**Live Application:** https://medical-necessity-engine.vercel.app/  
**Backend API:** https://medical-necessity-engine.onrender.com/  
**API Documentation:** https://medical-necessity-engine.onrender.com/docs  
**Repository:** https://github.com/lvb05/medical-necessity-engine

---

## Project Overview

> The Medical Necessity Assistant answers clinical coding questions using the provided guideline documents as the source of truth.

It supports questions like:

- Does this visit qualify for a 99214?
- Is hypertension a stable chronic illness under AMA 2021?
- What happens if the LAMA form is missing in a JAWDA audit?
- What documentation gaps could cause a denial?

The system is designed to answer with exact guideline citations and avoid unsupported claims.

---

## Key Differentiators

| Feature | How It Works |
|---------|-------------|
| **Source-Cited Answers** | Responses include authority, section, and page references from guideline rules |
| **Multi-Authority Routing** | Questions are routed to AMA 2021, CMS 1997, HAAD, or JAWDA based on context |
| **Encounter Analysis** | Evaluates documentation, MDM level, audit findings, and CPT support |
| **Denial Risk Assessment** | Assigns low, moderate, or high denial risk using rule-based checks |
| **JAWDA Compliance Checks** | Validates LAMA forms, physician consistency, and time-based billing requirements |

---

## Architecture

### System Architecture
```
         ┌─────────────────────────────┐
         │         FastAPI API         │
         └──────────────┬──────────────┘
                        │
              ┌─────────┴─────────┐
              │                   │
              ▼                   ▼
         ┌─────────────┐   ┌─────────────┐
         │  /api/ask   │   │ /api/analyze│
         └──────┬──────┘   └──────┬──────┘
                │                 │
                ▼                 ▼
         ┌─────────────┐   ┌─────────────┐
         │ Ask Engine  │   │Gap Detector │
         └──────┬──────┘   └──────┬──────┘
                │                 │
                ▼                 ▼
         ┌─────────────┐   ┌─────────────┐
         │  Authority  │   │  MDM Engine │
         │   Router    │   │ Audit Checks│
         └──────┬──────┘   │ Time Rules  │
                │          └──────┬──────┘
                ▼                 ▼
           ┌─────────────────────────────┐
           │ Clinical Guideline Rules    │
           │ AMA • CMS • HAAD • JAWDA    │
           └─────────────────────────────┘
```

## Tech Stack

#### Backend

* **Python 3.11** — Core application language
* **FastAPI** — REST API framework
* **Pydantic** — Request and response validation
* **Uvicorn** — ASGI application server

#### Data Storage

* **PostgreSQL** — Persistent storage for guideline content and query logs
* **SQLAlchemy (Async)** — ORM and database access

#### Rule Engine

* **Rule-Based Retrieval** — Authority-specific guideline retrieval
* **AMA 2021 MDM Engine** — Medical Decision Making calculation using the 2-of-3 rule
* **Documentation Analysis Engine** — CMS 1997 documentation validation
* **JAWDA Audit Engine** — UAE audit compliance checks
* **Time validator** — Time-based code validation

#### Testing & Deployment

* **pytest** — Unit and integration testing
* **Docker** — Containerized application packaging
* **Render** — Production hosting



### Encounter Analysis Flow (internal logic of `/api/analyze`)
```
                 Patient Encounter
                         │
                         ▼
                Extract Documentation
            (HPI, Exam, Assessment)
                         │
                         ▼
                  MDM Inference Engine
             ┌───────────┼───────────┐
             ▼           ▼           ▼
      Problems      Data Level    Risk Level
      Complexity                 Complexity
             └───────────┼───────────┘
                         ▼
                  AMA 2021 MDM
                   2-of-3 Rule
                         │
                         ▼
               Recommended CPT Code
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
     Audit Check    Time Validation   Gap Detection
       (JAWDA)          (AMA)            (CMS)
          └──────────────┼──────────────┘
                         ▼
                    Denial Risk
               (Low / Moderate / High)
                         ▼
               Structured JSON Output
```

### Question Answering Flow (internal logic of `/api/ask`)
```
                      User Question
                           │
                           ▼
                   Authority Router
              (AMA / CMS / HAAD / JAWDA)
                           │
                           ▼
                Extract Keywords & CPT
                           │
                           ▼
                 Retrieve Relevant Rule
                    From JSON Rules
                           │
                           ▼
                   Ask Engine Logic
                           │
                           ▼
                 Build Structured Answer
                           │
                           ▼
                    Add Citation
               (Authority + Section + Page)
                           │
                           ▼
                     JSON Response
```
---


## Features

| Feature | Description |
|---------|-------------|
| **Question Answering** | Answers clinical coding questions with citations |
| **Multi-Authority Support** | Routes to AMA 2021, CMS 1997, HAAD, or JAWDA |
| **Encounter Analysis** | Evaluates MDM, documentation gaps, and CPT support |
| **Denial Risk Assessment** | Returns low, moderate, or high risk |
| **Source Citations** | Includes authority, section, and page |
| **JAWDA Checks** | Validates LAMA, physician match, and time documentation |

---
## Answer Quality Guarantees

| Rule | How It's Enforced |
|------|-------------------|
| Answer only what was asked | Retrieval is scoped to the question's authority and keywords |
| Always cite the source | Every response includes authority, section, and page |
| Tight, precise retrieval | Keyword matching with section priority ranking |
| Max 4 sentences per answer | Enforced in the Ask Engine response builder |
| AMA 2021 supersedes CMS 1997 | Authority router enforces this for codes 99202–99215 |
| Never invent rules | Returns a clear "not found" if no matching guideline exists |
---

## Authorities & Compliance

#### AMA 2021

Used for office and outpatient E/M code selection (99202–99215).

* Medical Decision Making (MDM)
* 2-of-3 rule
* Problem, data, and risk complexity
* Time-based code selection

#### CMS 1997

Used for documentation framework requirements.

* HPI
* ROS
* PFSH
* Examination documentation

#### HAAD

Used for UAE-specific coding and documentation guidance.

* Coding processes
* Documentation standards
* Medical necessity guidance

#### JAWDA 2026

Used for audit compliance and scoring requirements.

* LAMA validation
* Physician verification
* Time documentation checks
* Audit findings

#### Supersession Rule

For office and outpatient E/M codes **99202–99215**, AMA 2021 supersedes CMS 1997 and is used as the primary authority.

---

## API Endpoints

#### GET `/health`

Returns service status.

**Response**

```json
{
  "status": "ok"
}
```

#### POST `/api/ask`

Answers a clinical coding question using the appropriate guideline authority.

**Request**

```json
{
  "question": "Does this visit qualify for a 99214?"
}
```

**Response Fields**

* answer
* authority
* source_section
* source_page
* confidence
* citation

#### POST `/api/analyze`

Analyzes a patient encounter for CPT support, documentation gaps, audit findings, and denial risk.

**Key Response Fields**

* recommended_code
* code_supported
* documentation_gaps
* audit_findings
* denial_risk
* citations

---

## Sample Requests

#### Clinical Question

```bash
curl -X POST https://medical-necessity-engine.onrender.com/api/ask \
-H "Content-Type: application/json" \
-d '{"question":"Does this visit qualify for a 99214?"}'
```

**Example Response**

```json
{
  "authority": "AMA_2021",
  "source_section": "Levels of Medical Decision Making",
  "source_page": 10,
  "confidence": "high",
  "citation": "AMA 2021, Levels of Medical Decision Making, p.10"
}
```

#### Encounter Analysis

```bash
curl -X POST https://medical-necessity-engine.onrender.com/api/analyze \
-H "Content-Type: application/json" \
-d '{ ... }'
```

**Example Response**

```json
{
  "recommended_code": "99214",
  "code_supported": true,
  "denial_risk": "low"
}
```

---

## Local Setup

### Prerequisites

* Python 3.11+
* PostgreSQL
* pip

### Installation

```bash
git clone https://github.com/lvb05/medical-necessity-engine.git
cd medical-necessity-engine

python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

Create `.env`

```env
DATABASE_URL=postgresql+asyncpg://USERNAME:PASSWORD@localhost:5432/medical_necessity
ENV=development
LOG_LEVEL=INFO
```

Run the application:

```bash
python -c "from app.database import init_db; import asyncio; asyncio.run(init_db())"
uvicorn app.main:app --reload
```

Available at:

* http://localhost:8000
* http://localhost:8000/docs

---

## Docker

```bash
docker build -t medical-necessity-engine .
docker run -p 8000:8000 medical-necessity-engine
```

---

## Deployment

**Live URL**

https://medical-necessity-engine.onrender.com/

---

## Testing

Current Status:

```text
21 tests passed
0 failures
```

Coverage includes:

* MDM calculation
* Authority routing
* Rule loading
* Audit validation
* Time validation
* Documentation analysis
* API integration

Run tests:

```bash
pytest -v
```

---

## Document Processing Approach

> The provided guideline documents were converted into structured JSON rule files and stored as searchable records.

#### Storage Model

* GuidelineDocument → document metadata
* GuidelineChunk → section-level rule content
* QueryLog → request history and audit trail

#### Retrieval Flow

1. Route question to the appropriate authority.
2. Retrieve matching guideline sections.
3. Rank results using keyword matching and section priority.
4. Return the highest-ranked result with citation.

This approach keeps retrieval deterministic and supports exact source attribution.

---

## Project Structure

```text
medical-necessity-engine/
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── ask.py
│   │       └── analyze.py
│   ├── engines/
│   │   ├── ask_engine.py
│   │   ├── gap_detector.py
│   │   ├── mdm.py
│   │   ├── audit_checker.py
│   │   ├── documentation_checker.py
│   │   └── time_validator.py
│   ├── retrieval/
│   │   ├── authority_router.py
│   │   └── rule_loader.py
│   ├── config.py
│   ├── database.py
│   ├── database_seed.py
│   ├── models.py
│   ├── schemas.py
│   └── main.py
│
├── rules/
│   ├── ama_2021.json
│   ├── cms_1997.json
│   ├── haad_process.json
│   ├── jawda_part_ix.json
│   └── clinical_coding_process.json
│
├── tests/
│   ├── test_api_integration.py
│   ├── test_authority_router.py
│   ├── test_mdm.py
│   ├── test_audit_checker.py
│   ├── test_documentation_checker.py
│   ├── test_rule_loader.py
│   └── test_time_validator.py
│
├── docs/
│   └── EXTRACTION_LOG.md
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

---

## Future Improvements

* Expand JAWDA audit coverage
* Improve retrieval with semantic search
* Add frontend dashboard
* Support batch encounter analysis
* Increase edge-case test coverage
