from app.engines.documentation_checker import (
    evaluate_history_level,
)

def test_problem_focused():
    result = evaluate_history_level(
        chief_complaint="cough",
        hpi_count=2,
        ros_count=0,
        pfsh_count=0
    )
    assert result["level"] == "Problem Focused"

def test_detailed():
    result = evaluate_history_level(
        chief_complaint="cough",
        hpi_count=4,
        ros_count=3,
        pfsh_count=1
    )
    assert result["level"] == "Detailed"

def test_comprehensive():
    result = evaluate_history_level(
        chief_complaint="cough",
        hpi_count=4,
        ros_count=10,
        pfsh_count=2
    )
    assert result["level"] == "Comprehensive"