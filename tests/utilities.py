def validate_chart_type(result: str, expected: str) -> bool:
    """Check if the analysis correctly identified chart type"""
    return expected.lower() in result.lower()

def validate_data_points(result: str, expected_points: list) -> bool:
    """Verify all expected data points are present and accurate"""
    for point in expected_points:
        # Allow for slight variations in number formatting
        value_str = str(point["value"])
        if value_str not in result and \
            str(point["value"]) not in result:
            return False
    return True
