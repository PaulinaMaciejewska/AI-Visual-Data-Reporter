"""
Test suite for ChartsAssistant - validates chart type detection and answer similarity.

Run from project root:
    .venv\Scripts\Activate.ps1
    python tests/run_chart_analysis_tests.py
"""
import sys
import json
import asyncio
from pathlib import Path
from difflib import SequenceMatcher

# Add project root and tests directory to path so modules like chart_assistant can be imported
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))
# Also add the current tests directory to support local test utilities
sys.path.insert(0, str(Path(__file__).resolve().parent))

from load_advanced_test_cases import load_advanced_test_cases
from chart_assistant import ChartsAssistant
from tests.simple_tests.utilities import validate_chart_type


class ChartAnalysisValidator:
    """Validates chart analysis results against expected values."""
    
    def __init__(self):
        self.results = []
        self.assistant = ChartsAssistant()
    
    def contains_keywords(self, text: str, keywords: list) -> tuple[bool, list]:
        """
        Check if text contains any of the keywords.
        Returns (all_found: bool, found_keywords: list).
        """
        text_lower = text.lower()
        found = [kw for kw in keywords if kw.lower() in text_lower]
        return len(found) == len(keywords), found
    
    def extract_chart_type(self, response: str) -> str:
        """
        Extract chart type from GPT response.
        Looks for patterns like "bar chart", "pie chart", "line chart", etc.
        """
        response_lower = response.lower()
        chart_types = [
            "bar chart", "pie chart", "line chart", "scatter plot", 
            "heatmap", "heat map", "diagram", "flow diagram",
            "multi-plot", "combined plot", "dual line", "doughnut",
            "hype cycle", "concept map"
        ]
        
        for chart_type in chart_types:
            if chart_type in response_lower:
                return chart_type
        
        return "unknown"
    
    def test_chart_analysis(self, test_case: dict) -> dict:
        """
        Test a single chart analysis.
        
        Args:
            test_case: dict with 'image_path' and 'expected' keys
            
        Returns:
            dict with test results
        """
        image_path = test_case["image_path"]
        expected = test_case["expected"]
        
        result = {
            "image_path": image_path,
            "expected_type": expected.get("chart_type", "unknown"),
            "detected_type": "unknown",
            "type_match": False,
            "response": None,
            "error": None,
            "data_point_mentions": [],
        }
        
        try:
            # Read image
            full_path = Path(__file__).parent.parent / image_path
            if not full_path.exists():
                result["error"] = f"File not found: {full_path}"
                return result
            
            with open(full_path, "rb") as f:
                image_data = f.read()
            
            # Analyze chart (handle both sync and async)
            try:
                # Try async first (newer version)
                response = asyncio.run(self.assistant.analyze_chart([(Path(image_path).name, image_data)]))
            except TypeError:
                # Fall back to sync (older version)
                response = self.assistant.analyze_chart(image_data)
            
            result["response"] = response
            result["detected_type"] = self.extract_chart_type(response)
            result["type_match"] = validate_chart_type(response, expected.get("chart_type", ""))
            
            # Check for data points
            data_points = expected.get("data_points", [])
            if isinstance(data_points, list) and data_points:
                for dp in data_points:
                    if isinstance(dp, dict):
                        label = dp.get("label", "")
                        if label and label.lower() in response.lower():
                            result["data_point_mentions"].append(label)
            
            # Calculate similarity to expected summary if available
            expected_summary = expected.get("summary", "")
        
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def run_all_tests(self):
        """Run tests for all advanced test cases."""
        test_cases = load_advanced_test_cases()
        
        print(f"\n{'='*80}")
        print(f"Running {len(test_cases)} chart analysis tests...")
        print(f"{'='*80}\n")
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"[{i}/{len(test_cases)}] Testing: {test_case['image_path']}")
            result = self.test_chart_analysis(test_case)
            self.results.append(result)
            
            # Print immediate feedback
            if result["error"]:
                print(f"  ❌ ERROR: {result['error']}\n")
            else:
                type_status = "✓" if result["type_match"] else "✗"
                print(f"  {type_status} Expected: {result['expected_type']}")
                print(f"  {type_status} Detected: {result['detected_type']}")
                print(f"  📊 Data points found: {len(result['data_point_mentions'])}/{len(test_case['expected'].get('data_points', []))}")
                print()
        
        return self.results
    
    def generate_report(self):
        """Generate a summary report of test results."""
        if not self.results:
            print("No test results to report.")
            return
        
        # Calculate metrics
        total_tests = len(self.results)
        passed_type_detection = sum(1 for r in self.results if r["type_match"])
        failed_tests = sum(1 for r in self.results if r["error"])
        
        print(f"\n{'='*80}")
        print("TEST REPORT SUMMARY")
        print(f"{'='*80}\n")
        
        print(f"Total Tests: {total_tests}")
        print(f"Chart Type Detection Passed: {passed_type_detection}/{total_tests} ({passed_type_detection/total_tests*100:.1f}%)")
        print(f"Test Errors: {failed_tests}")
        
        # Detailed results
        print(f"{'='*80}")
        print("DETAILED RESULTS")
        print(f"{'='*80}\n")
        
        for i, result in enumerate(self.results, 1):
            status = "PASS" if result["type_match"] else "FAIL"
            print(f"[{i}] {result['image_path']}")
            print(f"    Status: {status}")
            
            if result["error"]:
                print(f"    Error: {result['error']}")
            else:
                print(f"    Expected Type: {result['expected_type']}")
                print(f"    Detected Type: {result['detected_type']}")
                print(f"    Data Points Matched: {len(result['data_point_mentions'])}")
            print()
    
    def export_results(self, output_file: str = "test_results.json"):
        """Export test results to JSON file."""
        output_path = Path(__file__).parent / output_file
        
        # Convert results to JSON-serializable format
        json_results = []
        for r in self.results:
            json_results.append({
                "image_path": r["image_path"],
                "expected_type": r["expected_type"],
                "detected_type": r["detected_type"],
                "type_match": r["type_match"],
                "error": r["error"],
                "data_point_mentions": r["data_point_mentions"],
                "response_preview": r["response"][:200] + "..." if r["response"] else None
            })
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_results, f, indent=2)
        
        print(f"Results exported to: {output_path}\n")


if __name__ == "__main__":
    validator = ChartAnalysisValidator()
    
    # Run all tests
    validator.run_all_tests()
    
    # Generate report
    validator.generate_report()
    
    # Export results
    validator.export_results("test_results.json")
