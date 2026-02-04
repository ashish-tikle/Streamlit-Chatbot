"""
Installation verification and health check script
Run this after installation to verify monitoring setup
"""

import sys
import os
from pathlib import Path


def check_python_version():
    """Verify Python version is 3.9+"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(
            f"❌ Python version: {version.major}.{version.minor}.{version.micro} (need 3.9+)"
        )
        return False


def check_dependencies():
    """Check if all required packages are installed"""
    required = {
        "streamlit": "1.30.0",
        "litellm": "1.25.3",
        "langfuse": "2.12.0",
        "tenacity": "8.2.3",
        "pandas": "2.1.4",
        "plotly": "5.18.0",
    }

    all_good = True
    for package, expected_version in required.items():
        try:
            if package == "streamlit":
                import streamlit as pkg
            elif package == "litellm":
                import litellm as pkg
            elif package == "langfuse":
                import langfuse as pkg
            elif package == "tenacity":
                import tenacity as pkg
            elif package == "pandas":
                import pandas as pkg
            elif package == "plotly":
                import plotly as pkg

            version = getattr(pkg, "__version__", "unknown")
            print(f"✅ {package}: {version}")
        except ImportError:
            print(f"❌ {package}: NOT INSTALLED")
            all_good = False

    return all_good


def check_phase1_dependencies():
    """Check Phase 1 enhancement packages (Prometheus, circuit breaker, rate limiting)"""
    phase1_packages = {
        "prometheus_client": "Prometheus metrics exporter",
        "pybreaker": "Circuit breaker pattern",
        "ratelimit": "Rate limiting",
    }

    print("\n📦 Phase 1 Enhancement Packages (optional):")
    all_installed = True
    for package, description in phase1_packages.items():
        try:
            pkg = __import__(package)
            version = getattr(pkg, "__version__", "unknown")
            print(f"✅ {package}: {version} ({description})")
        except ImportError:
            print(f"⚠️  {package}: NOT INSTALLED - {description} will be disabled")
            all_installed = False

    if not all_installed:
        print("\nℹ️  Phase 1 packages are optional. Install with:")
        print("   pip install prometheus-client pybreaker ratelimit")

    return True  # Don't fail for optional packages


def check_file_structure():
    """Verify all required files exist"""
    required_files = [
        "app.py",
        "backend.py",
        "requirements.txt",
        "README.md",
        "MONITORING.md",
        "prompts/system_prompt.txt",
        "monitoring/dashboard.py",
        "monitoring/alerts.py",
        "tests/test_monitoring.py",
    ]

    all_good = True
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}: MISSING")
            all_good = False

    return all_good


def check_env_file():
    """Check if .env file exists and has required variables"""
    env_file = Path(".env")

    if not env_file.exists():
        print("⚠️  .env file not found")
        print("   Create one from .env.example:")
        print("   cp .env.example .env")
        return False

    print("✅ .env file exists")

    # Check for required variables
    required_vars = ["GEMINI_API_KEY", "GOOGLE_GEMINI_BASE_URL"]

    with open(env_file, "r") as f:
        content = f.read()

    all_good = True
    for var in required_vars:
        if var in content and not content.startswith(f"{var}="):
            print(f"✅ {var} is configured")
        else:
            print(f"⚠️  {var} not configured")
            all_good = False

    return all_good


def check_metrics_directory():
    """Verify metrics and logs directories can be created"""
    metrics_dir = Path("metrics")
    logs_dir = Path("logs")

    all_good = True

    try:
        metrics_dir.mkdir(exist_ok=True)
        print(f"✅ Metrics directory: {metrics_dir.absolute()}")

        # Check if writable
        test_file = metrics_dir / ".test"
        test_file.touch()
        test_file.unlink()
        print("✅ Metrics directory is writable")
    except Exception as e:
        print(f"❌ Metrics directory error: {e}")
        all_good = False

    try:
        logs_dir.mkdir(exist_ok=True)
        print(f"✅ Logs directory: {logs_dir.absolute()}")

        # Check if writable
        test_file = logs_dir / ".test"
        test_file.touch()
        test_file.unlink()
        print("✅ Logs directory is writable")
    except Exception as e:
        print(f"❌ Logs directory error: {e}")
        all_good = False

    return all_good


def check_imports():
    """Test critical imports"""
    try:
        from backend import generate_response, _calculate_cost, log_feedback

        print("✅ Backend imports successful")

        # Test cost calculation
        usage = {"prompt_tokens": 100, "completion_tokens": 50}
        cost = _calculate_cost(usage)
        print(f"✅ Cost calculation works: ${cost:.8f}")

        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False


def check_prometheus_config():
    """Check Prometheus configuration and availability"""
    print("\n🔍 Prometheus Configuration:")

    try:
        import prometheus_client

        print("✅ prometheus-client installed")

        port = os.getenv("PROMETHEUS_PORT", "9090")
        print(f"✅ Prometheus port configured: {port}")
        print(f"   Metrics endpoint: http://localhost:{port}/metrics")

        return True
    except ImportError:
        print("⚠️  prometheus-client not installed - Prometheus metrics disabled")
        print("   Install with: pip install prometheus-client")
        return True  # Don't fail, just warn


def check_resilience_config():
    """Check resilience configuration (circuit breaker, rate limiting)"""
    print("\n🛡️  Resilience Configuration:")

    # Circuit breaker
    threshold = os.getenv("CIRCUIT_BREAKER_THRESHOLD", "5")
    timeout = os.getenv("CIRCUIT_BREAKER_TIMEOUT", "30")
    print(f"   Circuit breaker threshold: {threshold} failures")
    print(f"   Circuit breaker timeout: {timeout} seconds")

    # Rate limiting
    rate_calls = os.getenv("RATE_LIMIT_CALLS", "60")
    rate_period = os.getenv("RATE_LIMIT_PERIOD", "60")
    print(f"   Rate limit: {rate_calls} requests per {rate_period} seconds")

    # Request timeout
    req_timeout = os.getenv("REQUEST_TIMEOUT", "30")
    print(f"   Request timeout: {req_timeout} seconds")

    print("✅ Resilience settings configured")
    return True


def main():
    print("=" * 60)
    print("🔍 STREAMLIT CHATBOT MONITORING - INSTALLATION CHECK")
    print("=" * 60)
    print()

    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Phase 1 Enhancements", check_phase1_dependencies),
        ("File Structure", check_file_structure),
        ("Environment Configuration", check_env_file),
        ("Metrics & Logs Directories", check_metrics_directory),
        ("Code Imports", check_imports),
        ("Prometheus Configuration", check_prometheus_config),
        ("Resilience Configuration", check_resilience_config),
    ]

    results = []
    for name, check_func in checks:
        print(f"\n--- {name} ---")
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Check failed with error: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10} - {name}")
        if not result:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n🎉 All checks passed! You're ready to go.")
        print("\nNext steps:")
        print("1. Configure .env with your API keys")
        print("2. Run: streamlit run app.py")
        print("3. View Prometheus metrics: curl http://localhost:9090/metrics")
        print("4. Open dashboard: cd monitoring && streamlit run dashboard.py")
        print("5. Run tests: pytest tests/ -v")
        print("\n📚 Documentation:")
        print("   - README.md - Full documentation")
        print("   - MONITORING.md - Quick reference commands")
        print("   - ADVANCED_OBSERVABILITY.md - Prometheus, circuit breaker, etc.")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("- Install dependencies: pip install -r requirements.txt")
        print("- Create .env file: cp .env.example .env")
        print("- Ensure all files are present")
        return 1


if __name__ == "__main__":
    sys.exit(main())
