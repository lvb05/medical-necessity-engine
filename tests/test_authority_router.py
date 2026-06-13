from app.retrieval.authority_router import route_authority
from app.retrieval.rule_loader import (
    AUTHORITY_AMA,
    AUTHORITY_CMS,
    AUTHORITY_HAAD,
    AUTHORITY_JAWDA,
)

def test_99214_routes_to_ama():
    decision = route_authority("Does this visit qualify for 99214?", "99214")
    assert decision.primary_authority == AUTHORITY_AMA
    assert decision.fallback_authority == AUTHORITY_CMS

def test_lama_question_routes_to_jawda():
    decision = route_authority("What happens if the LAMA form is missing?")
    assert decision.primary_authority == AUTHORITY_JAWDA

def test_haad_process_question_routes_to_haad():
    decision = route_authority("What are the HAAD documentation policy rules?")
    assert decision.primary_authority == AUTHORITY_HAAD

def test_history_question_routes_to_cms():
    decision = route_authority("What history type is required?")
    assert decision.primary_authority == AUTHORITY_CMS