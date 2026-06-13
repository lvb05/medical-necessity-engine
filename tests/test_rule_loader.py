from app.retrieval.rule_loader import (
    AUTHORITY_AMA,
    AUTHORITY_CMS,
    AUTHORITY_HAAD,
    AUTHORITY_JAWDA,
    AUTHORITY_CLINICAL,
    get_documents_by_authority,
    get_loaded_authorities,
    load_rules,
    reset,
)

def test_load_rules_loads_all_authorities():
    reset()
    load_rules(force_reload=True)
    authorities = get_loaded_authorities()

    assert AUTHORITY_AMA in authorities
    assert AUTHORITY_CMS in authorities
    assert AUTHORITY_HAAD in authorities
    assert AUTHORITY_JAWDA in authorities
    assert AUTHORITY_CLINICAL in authorities


def test_haad_authority_returns_supporting_documents():
    reset()
    load_rules(force_reload=True)
    docs = get_documents_by_authority("HAAD")
    assert len(docs) >= 2