"""
Test script for the monitoring dashboard
Run this to verify the monitoring page loads correctly
"""

import sys
from pathlib import Path


def test_imports():
    """Test that all required packages are importable"""
    print("Testing imports...")

    try:
        import streamlit

        print("✅ streamlit")
    except ImportError as e:
        print(f"❌ streamlit: {e}")
        return False

    try:
        import pandas

        print("✅ pandas")
    except ImportError as e:
        print(f"❌ pandas: {e}")
        return False

    try:
        import plotly

        print("✅ plotly")
    except ImportError as e:
        print(f"❌ plotly: {e}")
        return False

    try:
        import requests

        print("✅ requests")
    except ImportError as e:
        print(f"❌ requests: {e}")
        return False

    return True


def test_demo_data():
    """Test that demo data files exist"""
    print("\nChecking demo data...")

    demo_dir = Path("demo_data")
    files = ["demo_metrics.jsonl", "demo_feedback.jsonl", "demo_logs.log"]

    all_exist = True
    for file in files:
        filepath = demo_dir / file
        if filepath.exists():
            print(f"✅ {filepath}")
        else:
            print(f"❌ {filepath} (missing)")
            all_exist = False

    return all_exist


def test_monitoring_page():
    """Test that monitoring page file exists"""
    print("\nChecking monitoring page...")

    page_file = Path("pages/2_Monitor.py")
    if page_file.exists():
        print(f"✅ {page_file}")
        return True
    else:
        print(f"❌ {page_file} (missing)")
        return False


def test_directories():
    """Ensure required directories exist"""
    print("\nChecking directories...")

    dirs = ["metrics", "logs", "demo_data", "pages"]
    all_exist = True

    for dir_name in dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"✅ {dir_path}/")
        else:
            print(f"⚠️  {dir_path}/ (will be created on first run)")

    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("Monitoring Dashboard Test Suite")
    print("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("Demo Data", test_demo_data),
        ("Monitoring Page", test_monitoring_page),
        ("Directories", test_directories),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} test failed with error: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)

    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name}: {status}")

    all_passed = all(result for _, result in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed!")
        print("\nNext steps:")
        print("1. Run: streamlit run app.py")
        print("2. Navigate to the Monitor page in the sidebar")
        print("3. You should see demo data immediately")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\nTo fix:")
        print("1. Install missing packages: pip install -r requirements.txt")
        print("2. Ensure demo data files exist in demo_data/")
        print("3. Ensure pages/2_Monitor.py exists")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
