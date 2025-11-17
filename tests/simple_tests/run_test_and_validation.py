'''
Varification:
- OCR correctly extracts text from chart images
- GPT-4 Vision accurately interprets chart data and associations
- Structured data output matches expected format and content
'''
import sys
import os
import asyncio
from pathlib import Path

# Add parent directory to path so we can import modules from project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from test_cases import test_cases
from chart_assistant import ChartsAssistant
from tests.simple_tests.utilities import validate_chart_type, validate_data_points

class TestResultOfAnalysis:
    def __init__(self, image_path, assistant: ChartsAssistant):
        self.image_path = image_path
        self.assistant = assistant
        self.image_data = None

    def _read_image(self):
        with open(self.image_path, "rb") as img_file:
            self.image_data = img_file.read()

    def _test_chart_analysis(self):
        if self.image_data is None:
            self._read_image()
        
        # analyze_chart is async and expects list of (filename, data) tuples
        filename = Path(self.image_path).name
        analysis_result = asyncio.run(self.assistant.analyze_chart([(filename, self.image_data)]))
        
        assert "chart type" in analysis_result.lower()
        assert "market share" in analysis_result.lower()
        assert any(str(i) + "%" for i in range(101) if str(i) in analysis_result)

    def _test_full_workflow(self, spec_test_case):
        if self.image_data is None:
            self._read_image()
        
        # analyze_chart is async and expects list of (filename, data) tuples
        filename = Path(self.image_path).name
        analysis_result = asyncio.run(self.assistant.analyze_chart([(filename, self.image_data)]))
        validate_chart_type(analysis_result, spec_test_case["expected"]["chart_type"])
        validate_data_points(analysis_result, spec_test_case["expected"]["data_points"])


if __name__ == "__main__":
    assistant = ChartsAssistant()
    print("Starting tests for chart analysis and validation...")
    for case in test_cases:
        tester = TestResultOfAnalysis(case["image_path"], assistant)
        try:
            print(80 * "=")
            print(f"Running tests for {case['image_path']}...")
            tester._test_chart_analysis()
            print(f"✅ Test chart analysis passed for {case['image_path']}")

            tester._test_full_workflow(case)
            print(f"✅ Full workflow test passed for {case['image_path']}")
        except AssertionError as e:
            print(f"❌ Test failed for {case['image_path']}: {str(e)}")
        