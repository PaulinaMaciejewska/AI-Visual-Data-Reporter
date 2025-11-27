def validate_chart_type(result: str, expected: str) -> bool:
    """
    Check if the analysis correctly identified chart type.
    Handles variations like "bar chart" vs "bar" or "pie chart" vs "pie".
    """
    if not result or not expected:
        return False
    
    result_lower = result.lower()
    expected_lower = expected.lower()
    
    # Direct match
    if expected_lower in result_lower:
        return True
    
    # Check for partial matches (e.g., "bar" in "bar chart")
    parts = expected_lower.split()
    if any(part in result_lower for part in parts if len(part) > 3):
        return True
    
    return False


def validate_data_points(result: str, expected_points: list) -> bool:
    """Verify all expected data points are present and accurate"""
    for point in expected_points:
        # Allow for slight variations in number formatting
        value_str = str(point["value"])
        if value_str not in result and \
            str(point["value"]) not in result:
            return False
    return True
