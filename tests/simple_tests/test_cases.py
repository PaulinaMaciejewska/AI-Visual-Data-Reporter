test_cases = [
    {
        "image_path": "tests\simple_tests\simple_charts/bar_chart_sales.png", 
        "expected": {
            "chart_type": "bar chart",
            "data_points": [
                {"label": "Q1 2024", "value": 150000},
                {"label": "Q2 2024", "value": 175000},
                {"label": "Q3 2024", "value": 215000},
                {"label": "Q4 2024", "value": 204000}
            ],
            "trends": ["15% increase from Q1 to Q2, 23% increase from Q2 to Q3, 5% decrease from Q3 to Q4"]
        }
    },

    {
        "image_path": "tests\simple_tests\simple_charts\pie_chart_market_share.png",
        "expected": {
            "chart_type": "pie chart",
            "data_points": [
                {"label": "Company A", "value": 40},
                {"label": "Company B", "value": 35},
                {"label": "Company C", "value": 25}
            ],
            "trends": ["Company A has the largest market share"]
        }
    },
    {
        "image_path": "tests\simple_tests\simple_charts\line_chart_growth.png",
        "expected": {
            "chart_type": "line chart",
            "data_points": [
                {"label": "Jan 2024", "value": 1000},
                {"label": "Feb 2024", "value": 1200},
                {"label": "Mar 2024", "value": 1500}
            ],
            "trends": ["20% growth from Jan to Feb", "25% growth from Feb to Mar"]
        }
    }
]