from app.engines.time_validator import validate_time

def test_valid_99214():
    result = validate_time(
        cpt_code="99214",
        documented_minutes=35,
        start_time="10:00",
        end_time="10:35"
    )

    assert result["valid"] is True

def test_missing_start_end_time():
    result = validate_time(
        cpt_code="99214",
        documented_minutes=35,
        start_time=None,
        end_time=None
    )

    assert result["valid"] is False
    assert any(
        "Missing start/end time" in finding
        for finding in result["findings"]
    )

def test_time_below_range():
    result = validate_time(
        cpt_code="99214",
        documented_minutes=10,
        start_time="10:00",
        end_time="10:10"
    )
    assert result["valid"] is False