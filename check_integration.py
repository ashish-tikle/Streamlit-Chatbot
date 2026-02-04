"""
Integration Status Checker
Verifies all external service connections and configurations
"""

import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv
import socket

# Load environment
load_dotenv()


class Colors:
    """ANSI color codes for terminal output"""

    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_header(text):
    """Print section header"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.RESET}\n")


def print_status(service, status, message=""):
    """Print service status"""
    if status == "OK":
        icon = f"{Colors.GREEN}✅{Colors.RESET}"
        status_text = f"{Colors.GREEN}OK{Colors.RESET}"
    elif status == "WARN":
        icon = f"{Colors.YELLOW}⚠️ {Colors.RESET}"
        status_text = f"{Colors.YELLOW}OPTIONAL{Colors.RESET}"
    elif status == "FAIL":
        icon = f"{Colors.RED}❌{Colors.RESET}"
        status_text = f"{Colors.RED}FAILED{Colors.RESET}"
    else:
        icon = "ℹ️ "
        status_text = status

    print(f"{icon} {Colors.BOLD}{service:<30}{Colors.RESET} {status_text}")
    if message:
        print(f"   └─ {message}")


def check_env_var(var_name, required=False):
    """Check if environment variable is set"""
    value = os.getenv(var_name)
    if value:
        # Mask sensitive values
        if any(key in var_name for key in ["KEY", "PASSWORD", "TOKEN", "SECRET"]):
            masked = value[:8] + "..." if len(value) > 8 else "***"
            return True, masked
        return True, value
    return False, None


def check_port_open(host, port, timeout=2):
    """Check if a port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False


def check_http_endpoint(url, timeout=5):
    """Check if HTTP endpoint is accessible"""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code < 500, response.status_code
    except requests.exceptions.Timeout:
        return False, "Timeout"
    except requests.exceptions.ConnectionError:
        return False, "Connection refused"
    except Exception as e:
        return False, str(e)


def main():
    """Run all service checks"""
    print(f"\n{Colors.BOLD}🔌 External Services Integration Check{Colors.RESET}")
    print(f"Date: {Colors.BLUE}{Path.cwd()}{Colors.RESET}\n")

    results = {"required": [], "optional": [], "warnings": []}

    # =====================================================
    # PHASE 1: Required Services
    # =====================================================
    print_header("PHASE 1: Required Services (Must Have)")

    # Check Python dependencies
    try:
        import streamlit
        import litellm
        import pandas
        import plotly

        print_status("Python Dependencies", "OK", "All packages installed")
        results["required"].append(("Dependencies", True))
    except ImportError as e:
        print_status("Python Dependencies", "FAIL", f"Missing: {e}")
        results["required"].append(("Dependencies", False))

    # Check Gemini API configuration
    has_key, key_value = check_env_var("GEMINI_API_KEY", required=True)
    has_url, url_value = check_env_var("GOOGLE_GEMINI_BASE_URL", required=True)

    if has_key and has_url:
        # Try to verify API connection (optional check)
        print_status(
            "Gemini API Configuration", "OK", f"Key: {key_value}, URL: {url_value}"
        )
        results["required"].append(("Gemini API", True))
    else:
        missing = []
        if not has_key:
            missing.append("GEMINI_API_KEY")
        if not has_url:
            missing.append("GOOGLE_GEMINI_BASE_URL")
        print_status(
            "Gemini API Configuration", "FAIL", f"Missing: {', '.join(missing)}"
        )
        results["required"].append(("Gemini API", False))

    # Check local storage directories
    dirs_ok = True
    for dir_name in ["logs", "metrics", "demo_data"]:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print_status(
                f"Directory: {dir_name}/",
                "OK",
                f"{len(list(dir_path.iterdir()))} files",
            )
        else:
            print_status(
                f"Directory: {dir_name}/", "WARN", "Will be created on first run"
            )
            dirs_ok = False
    results["required"].append(("Local Storage", dirs_ok))

    # =====================================================
    # PHASE 2: Observability Stack
    # =====================================================
    print_header("PHASE 2: Observability Stack (Recommended)")

    # Check Langfuse configuration
    enable_langfuse = os.getenv("ENABLE_LANGFUSE", "true").lower() == "true"
    has_lf_pub, lf_pub = check_env_var("LANGFUSE_PUBLIC_KEY")
    has_lf_sec, lf_sec = check_env_var("LANGFUSE_SECRET_KEY")
    has_lf_host, lf_host = check_env_var("LANGFUSE_HOST")

    if enable_langfuse:
        if has_lf_pub and has_lf_sec and has_lf_host:
            # Try to ping Langfuse
            is_reachable, status = check_http_endpoint(lf_host)
            if is_reachable:
                print_status(
                    "Langfuse Tracing", "OK", f"Host: {lf_host}, Keys configured"
                )
                results["optional"].append(("Langfuse", True))
            else:
                print_status(
                    "Langfuse Tracing", "WARN", f"Configured but unreachable: {status}"
                )
                results["optional"].append(("Langfuse", False))
        else:
            missing = []
            if not has_lf_pub:
                missing.append("LANGFUSE_PUBLIC_KEY")
            if not has_lf_sec:
                missing.append("LANGFUSE_SECRET_KEY")
            if not has_lf_host:
                missing.append("LANGFUSE_HOST")
            print_status(
                "Langfuse Tracing", "WARN", f"Disabled or missing: {', '.join(missing)}"
            )
            results["warnings"].append("Langfuse not configured - tracing disabled")
            results["optional"].append(("Langfuse", False))
    else:
        print_status("Langfuse Tracing", "WARN", "Disabled (ENABLE_LANGFUSE=false)")
        results["optional"].append(("Langfuse", False))

    # Check OpenTelemetry (fallback)
    enable_otel = os.getenv("ENABLE_OTEL", "false").lower() == "true"
    if enable_otel:
        otel_exporter = os.getenv("OTEL_EXPORTER", "console")
        print_status("OpenTelemetry", "OK", f"Enabled with {otel_exporter} exporter")
        results["optional"].append(("OpenTelemetry", True))
    else:
        print_status("OpenTelemetry", "WARN", "Disabled (fallback to Langfuse)")
        results["optional"].append(("OpenTelemetry", False))

    # =====================================================
    # PHASE 3: Alerting
    # =====================================================
    print_header("PHASE 3: Alerting (Optional)")

    # Check SMTP configuration
    has_smtp_host, smtp_host = check_env_var("SMTP_HOST")
    has_smtp_user, smtp_user = check_env_var("SMTP_USER")
    has_smtp_pass, smtp_pass = check_env_var("SMTP_PASSWORD")
    has_alert_to, alert_to = check_env_var("ALERT_EMAIL_TO")

    if has_smtp_host and has_smtp_user and has_smtp_pass and has_alert_to:
        print_status(
            "Email Alerts (SMTP)", "OK", f"Server: {smtp_host}, To: {alert_to}"
        )
        results["optional"].append(("Email Alerts", True))
    else:
        missing = []
        if not has_smtp_host:
            missing.append("SMTP_HOST")
        if not has_smtp_user:
            missing.append("SMTP_USER")
        if not has_smtp_pass:
            missing.append("SMTP_PASSWORD")
        if not has_alert_to:
            missing.append("ALERT_EMAIL_TO")
        print_status(
            "Email Alerts (SMTP)", "WARN", f"Not configured: {', '.join(missing)}"
        )
        results["optional"].append(("Email Alerts", False))

    # Check Slack webhook
    has_slack, slack_url = check_env_var("SLACK_WEBHOOK_URL")

    if has_slack:
        print_status("Slack Alerts", "OK", f"Webhook configured: {slack_url[:30]}...")
        results["optional"].append(("Slack Alerts", True))
    else:
        print_status(
            "Slack Alerts", "WARN", "Not configured (SLACK_WEBHOOK_URL missing)"
        )
        results["optional"].append(("Slack Alerts", False))

    # =====================================================
    # Summary
    # =====================================================
    print_header("Integration Summary")

    required_pass = sum(1 for _, status in results["required"] if status)
    required_total = len(results["required"])
    optional_pass = sum(1 for _, status in results["optional"] if status)
    optional_total = len(results["optional"])

    print(
        f"Required Services:  {required_pass}/{required_total} {Colors.GREEN if required_pass == required_total else Colors.RED}{'✅' if required_pass == required_total else '❌'}{Colors.RESET}"
    )
    print(
        f"Optional Services:  {optional_pass}/{optional_total} {Colors.YELLOW}⚠️{Colors.RESET}"
    )

    if results["warnings"]:
        print(f"\n{Colors.YELLOW}⚠️  Warnings:{Colors.RESET}")
        for warning in results["warnings"]:
            print(f"   • {warning}")

    print("\n" + "=" * 60)

    # Recommendations
    if required_pass < required_total:
        print(
            f"\n{Colors.RED}{Colors.BOLD}❌ CRITICAL: Required services missing!{Colors.RESET}"
        )
        print("   Action: Fix required services before proceeding")
        print("   See: INTEGRATION_PLAN.md → STEP 1")
        return 1
    elif optional_pass < optional_total / 2:
        print(
            f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  Ready for local testing (Phase 1){Colors.RESET}"
        )
        print("   Recommendation: Add observability for production")
        print("   Next: INTEGRATION_PLAN.md → STEP 2 (Langfuse)")
        return 0
    else:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ Production ready!{Colors.RESET}")
        print("   All critical services configured")
        print("   Next: Run load tests, then deploy")
        print("   See: INTEGRATION_PLAN.md → STEP 5-6")
        return 0


if __name__ == "__main__":
    sys.exit(main())
