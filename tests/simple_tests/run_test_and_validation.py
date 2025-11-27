'''
Varification:
- OCR correctly extracts text from chart images
- GPT-4 Vision accurately interprets chart data and associations
- Structured data output matches expected format and content
'''
import sys
import pytest
import asyncio
from pathlib import Path

# Add parent directory to path so we can import modules from project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from test_cases import test_cases
from chart_assistant import ChartsAssistant
from tests.simple_tests.utilities import validate_chart_type, validate_data_points

@pytest.fixture(params=test_cases)
def chart_case(request):
    case = request.param
    image_path = case["image_path"]
    filename = Path(image_path).name

    with open(image_path, "rb") as img_file:
        image_data = img_file.read()

    return filename, image_data, case["expected"]

@pytest.fixture
def assistant():
    return ChartsAssistant()


class TestChartAnalysis:

    @pytest.mark.asyncio
    async def test_chart_analysis(self, assistant, chart_case):
        filename, image_data, expected = chart_case
        analysis_result = await assistant.analyze_chart([(filename, image_data)])
        
        assert expected["chart_type"].lower() in analysis_result.lower()
        assert any(str(i) + "%" for i in range(101) if str(i) in analysis_result)

    @pytest.mark.asyncio
    async def test_full_workflow(self, assistant, chart_case):
        filename, image_data, expected = chart_case
        analysis_result = await assistant.analyze_chart([(filename, image_data)])  

        validate_chart_type(analysis_result, expected["chart_type"])
        validate_data_points(analysis_result, expected["data_points"])
