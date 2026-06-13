from app.engines.models import Citation

def evaluate_history_level(
    chief_complaint: str | None,
    hpi_count: int,
    ros_count: int,
    pfsh_count: int,
):
    if not chief_complaint:
        return {
            "level": "invalid",
            "citation": None,
        }

    if hpi_count <= 3 and ros_count == 0:
        level = "Problem Focused"

    elif hpi_count <= 3 and ros_count == 1:
        level = "Expanded Problem Focused"

    elif hpi_count >= 4 and ros_count >= 10 and pfsh_count >= 2:
        level = "Comprehensive"
    
    elif hpi_count >= 4 and ros_count >= 2 and pfsh_count >= 1:
        level = "Detailed"

    else:
        level = "Problem Focused"

    return {
        "level": level,
        "citation": Citation(
            authority="CMS_1997",
            source_section="History Types Table",
            source_page=6,
        ),
    }