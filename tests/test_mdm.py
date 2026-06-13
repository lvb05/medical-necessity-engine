from app.engines.mdm import calculate_mdm

def test_moderate_established():
    result = calculate_mdm(
        problems_level="moderate",
        data_level="low",
        risk_level="moderate",
        visit_type="established"
    )

    assert result.mdm_level == "moderate"
    assert result.recommended_code == "99214"


def test_high_new_patient():
    result = calculate_mdm(
        problems_level="high",
        data_level="moderate",
        risk_level="high",
        visit_type="new"
    )

    assert result.mdm_level == "high"
    assert result.recommended_code == "99205"


def test_low_established():
    result = calculate_mdm(
        problems_level="low",
        data_level="low",
        risk_level="straightforward",
        visit_type="established"
    )

    assert result.mdm_level == "low"
    assert result.recommended_code == "99213"