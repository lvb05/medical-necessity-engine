from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_ask_99214():
    response = client.post("/api/ask", json={"question": "Does this visit qualify for a 99214?"})
    assert response.status_code == 200
    body = response.json()
    assert body["authority"] == "AMA_2021"
    assert "99214" in body["answer"]

def test_analyze_clean_case():
    payload = {
        "visit_type": "outpatient",
        "chief_complaint": "Cough",
        "diagnoses": ["J06.9"],
        "procedures": [],
        "documentation": {
            "HPI": "Cough for 5 days",
            "exam": "Lungs clear",
            "assessment": "Upper respiratory infection"
        },
        "billed_code": "99214",
        "total_time_minutes": 35,
        "start_time": "10:00",
        "end_time": "10:35",
        "billed_physician": "Dr Smith",
        "actual_physician": "Dr Smith",
        "lama_required": False,
        "lama_signed": True
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["recommended_code"] == "99214"
    assert body["code_supported"] is True