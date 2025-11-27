"""
Load and aggregate all test cases from JSON ground-truth files in advanced_charts.

Usage:
    from load_advanced_test_cases import load_advanced_test_cases
    test_cases = load_advanced_test_cases()
"""
import json
from pathlib import Path


def load_advanced_test_cases():
    """
    Discover and load all test cases from JSON files in advanced_charts folder.
    
    Returns:
        list: List of test case dicts with keys: image_path, expected
    """
    test_cases = []
    advanced_charts_dir = Path(__file__).parent.parent / "advanced_charts"
    
    if not advanced_charts_dir.exists():
        print(f"Warning: {advanced_charts_dir} does not exist")
        return test_cases
    
    # Find all .json files recursively
    for json_file in sorted(advanced_charts_dir.rglob("*.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                expected = json.load(f)
            
            # Build image path by replacing .json with image extension (.png, .jpg, .pdf)
            # Try common image extensions
            image_base = json_file.with_suffix("")
            image_path = None
            
            for ext in [".png", ".jpg", ".jpeg", ".pdf"]:
                candidate = image_base.with_suffix(ext)
                if candidate.exists():
                    image_path = str(candidate.relative_to(Path(__file__).parent.parent))
                    break
            
            if image_path:
                test_cases.append({
                    "image_path": image_path,
                    "expected": expected
                })
            else:
                print(f"Warning: No corresponding image found for {json_file}")
        
        except json.JSONDecodeError as e:
            print(f"Error parsing {json_file}: {e}")
        except Exception as e:
            print(f"Error loading {json_file}: {e}")
    
    return test_cases


if __name__ == "__main__":
    # Quick test: print loaded test cases
    cases = load_advanced_test_cases()
    print(f"Loaded {len(cases)} test cases:\n")
    for i, case in enumerate(cases, 1):
        print(f"{i}. {case['image_path']}")
        print(f"   Type: {case['expected'].get('chart_type', 'unknown')}")
        print()
