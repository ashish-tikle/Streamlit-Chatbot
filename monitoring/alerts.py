"""
Alerting System for Chatbot Monitoring
Monitors metrics and sends alerts via email or Slack when thresholds are exceeded
"""

import json
import os
import logging
import smtplib
import requests
from pathlib import Path
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Configuration
METRICS_FILE = Path("metrics/requests.jsonl")

# Alert thresholds (configurable via environment variables)
ERROR_RATE_THRESHOLD = float(os.getenv("ALERT_ERROR_RATE_THRESHOLD", "10.0"))  # %
LATENCY_P95_THRESHOLD = float(
    os.getenv("ALERT_LATENCY_P95_THRESHOLD", "5.0")
)  # seconds
COST_PER_HOUR_THRESHOLD = float(os.getenv("ALERT_COST_THRESHOLD", "1.0"))  # USD
MIN_REQUESTS_FOR_ALERT = int(
    os.getenv("ALERT_MIN_REQUESTS", "10")
)  # Minimum requests before alerting

# Alert delivery configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO")
ALERT_EMAIL_FROM = os.getenv("ALERT_EMAIL_FROM", SMTP_USER)

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# Alert cooldown (prevent alert spam)
ALERT_COOLDOWN_HOURS = int(os.getenv("ALERT_COOLDOWN_HOURS", "1"))
last_alert_times: Dict[str, datetime] = {}


class MetricsAnalyzer:
    """Analyze metrics and detect issues."""

    def __init__(self, lookback_hours: int = 1):
        self.lookback_hours = lookback_hours
        self.metrics = self._load_recent_metrics()

    def _load_recent_metrics(self) -> List[Dict]:
        """Load metrics from the last N hours."""
        if not METRICS_FILE.exists():
            return []

        cutoff_time = datetime.utcnow() - timedelta(hours=self.lookback_hours)
        metrics = []

        try:
            with open(METRICS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        record = json.loads(line)
                        timestamp = datetime.fromisoformat(record["timestamp"])
                        if timestamp >= cutoff_time:
                            metrics.append(record)
        except Exception as e:
            logger.error(f"Error loading metrics: {e}")

        return metrics

    def calculate_error_rate(self) -> Optional[float]:
        """Calculate error rate as percentage."""
        if len(self.metrics) < MIN_REQUESTS_FOR_ALERT:
            return None

        total = len(self.metrics)
        failures = sum(1 for m in self.metrics if not m.get("success", True))

        return (failures / total) * 100 if total > 0 else 0.0

    def calculate_p95_latency(self) -> Optional[float]:
        """Calculate 95th percentile latency for successful requests."""
        successful = [
            m["duration_seconds"]
            for m in self.metrics
            if m.get("success", True) and "duration_seconds" in m
        ]

        if len(successful) < MIN_REQUESTS_FOR_ALERT:
            return None

        successful.sort()
        idx = int(len(successful) * 0.95)
        return successful[idx] if successful else None

    def calculate_hourly_cost(self) -> Optional[float]:
        """Calculate cost per hour."""
        if not self.metrics:
            return None

        total_cost = sum(m.get("cost_usd", 0) for m in self.metrics)
        hours = self.lookback_hours if self.lookback_hours > 0 else 1

        return total_cost / hours

    def get_recent_errors(self, limit: int = 5) -> List[Dict]:
        """Get recent error details."""
        errors = [m for m in self.metrics if not m.get("success", True)]
        errors.sort(key=lambda x: x["timestamp"], reverse=True)
        return errors[:limit]


class AlertSender:
    """Send alerts via email or Slack."""

    @staticmethod
    def can_send_alert(alert_type: str) -> bool:
        """Check if enough time has passed since last alert of this type."""
        if alert_type not in last_alert_times:
            return True

        time_since_last = datetime.utcnow() - last_alert_times[alert_type]
        return time_since_last.total_seconds() >= (ALERT_COOLDOWN_HOURS * 3600)

    @staticmethod
    def send_email(subject: str, body: str) -> bool:
        """Send email alert."""
        if not all([SMTP_USER, SMTP_PASSWORD, ALERT_EMAIL_TO]):
            logger.warning("Email alerting not configured (missing SMTP credentials)")
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = ALERT_EMAIL_FROM
            msg["To"] = ALERT_EMAIL_TO
            msg["Subject"] = f"🚨 Chatbot Alert: {subject}"

            msg.attach(MIMEText(body, "html"))

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)

            logger.info(f"Email alert sent: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False

    @staticmethod
    def send_slack(message: str) -> bool:
        """Send Slack alert via webhook."""
        if not SLACK_WEBHOOK_URL:
            logger.warning("Slack alerting not configured (missing webhook URL)")
            return False

        try:
            payload = {
                "text": f"🚨 *Chatbot Alert*\n\n{message}",
                "username": "Chatbot Monitor",
                "icon_emoji": ":robot_face:",
            }

            response = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
            response.raise_for_status()

            logger.info("Slack alert sent")
            return True

        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False


def check_and_alert():
    """Main monitoring loop: check metrics and send alerts if needed."""
    logger.info("Starting monitoring check...")

    analyzer = MetricsAnalyzer(lookback_hours=1)
    sender = AlertSender()
    alerts_sent = []

    # Check error rate
    error_rate = analyzer.calculate_error_rate()
    if error_rate is not None and error_rate > ERROR_RATE_THRESHOLD:
        alert_type = "high_error_rate"
        if sender.can_send_alert(alert_type):
            recent_errors = analyzer.get_recent_errors()
            error_details = "\n".join(
                [
                    f"- {e['timestamp']}: {e.get('error_type', 'Unknown')} - {e.get('error_message', '')[:100]}"
                    for e in recent_errors
                ]
            )

            subject = f"High Error Rate: {error_rate:.1f}%"
            body = f"""
            <h2>⚠️ High Error Rate Detected</h2>
            <p><strong>Current Error Rate:</strong> {error_rate:.1f}% (threshold: {ERROR_RATE_THRESHOLD}%)</p>
            <p><strong>Time Window:</strong> Last 1 hour</p>
            <p><strong>Total Requests:</strong> {len(analyzer.metrics)}</p>
            
            <h3>Recent Errors:</h3>
            <pre>{error_details}</pre>
            
            <p>Check the dashboard for more details.</p>
            """

            slack_msg = (
                f"⚠️ *High Error Rate: {error_rate:.1f}%* (threshold: {ERROR_RATE_THRESHOLD}%)\n"
                f"Time window: Last 1 hour\n"
                f"Total requests: {len(analyzer.metrics)}\n\n"
                f"Recent errors:\n{error_details}"
            )

            if sender.send_email(subject, body) or sender.send_slack(slack_msg):
                last_alert_times[alert_type] = datetime.utcnow()
                alerts_sent.append(alert_type)

    # Check latency
    p95_latency = analyzer.calculate_p95_latency()
    if p95_latency is not None and p95_latency > LATENCY_P95_THRESHOLD:
        alert_type = "high_latency"
        if sender.can_send_alert(alert_type):
            subject = f"High Latency: p95={p95_latency:.2f}s"
            body = f"""
            <h2>🐌 High Latency Detected</h2>
            <p><strong>P95 Latency:</strong> {p95_latency:.2f}s (threshold: {LATENCY_P95_THRESHOLD}s)</p>
            <p><strong>Time Window:</strong> Last 1 hour</p>
            <p><strong>Successful Requests:</strong> {len([m for m in analyzer.metrics if m.get('success', True)])}</p>
            
            <p>Response times are slower than expected. Check for:</p>
            <ul>
                <li>API performance issues</li>
                <li>Network latency</li>
                <li>Complex prompts requiring more processing</li>
            </ul>
            """

            slack_msg = (
                f"🐌 *High Latency: p95={p95_latency:.2f}s* (threshold: {LATENCY_P95_THRESHOLD}s)\n"
                f"Time window: Last 1 hour\n"
                f"Check dashboard for details."
            )

            if sender.send_email(subject, body) or sender.send_slack(slack_msg):
                last_alert_times[alert_type] = datetime.utcnow()
                alerts_sent.append(alert_type)

    # Check cost
    hourly_cost = analyzer.calculate_hourly_cost()
    if hourly_cost is not None and hourly_cost > COST_PER_HOUR_THRESHOLD:
        alert_type = "high_cost"
        if sender.can_send_alert(alert_type):
            subject = f"High Cost: ${hourly_cost:.4f}/hour"
            body = f"""
            <h2>💰 High Cost Detected</h2>
            <p><strong>Hourly Cost:</strong> ${hourly_cost:.4f} (threshold: ${COST_PER_HOUR_THRESHOLD})</p>
            <p><strong>Projected Daily:</strong> ${hourly_cost * 24:.2f}</p>
            <p><strong>Projected Monthly:</strong> ${hourly_cost * 24 * 30:.2f}</p>
            
            <p>Consider:</p>
            <ul>
                <li>Reviewing usage patterns</li>
                <li>Optimizing prompts to reduce tokens</li>
                <li>Implementing rate limiting</li>
            </ul>
            """

            slack_msg = (
                f"💰 *High Cost: ${hourly_cost:.4f}/hour* (threshold: ${COST_PER_HOUR_THRESHOLD})\n"
                f"Projected monthly: ${hourly_cost * 24 * 30:.2f}\n"
                f"Review usage patterns in dashboard."
            )

            if sender.send_email(subject, body) or sender.send_slack(slack_msg):
                last_alert_times[alert_type] = datetime.utcnow()
                alerts_sent.append(alert_type)

    # Log summary
    if alerts_sent:
        logger.warning(f"Alerts sent: {', '.join(alerts_sent)}")
    else:
        logger.info("All metrics within normal ranges")

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "alerts_sent": alerts_sent,
        "metrics": {
            "error_rate": error_rate,
            "p95_latency": p95_latency,
            "hourly_cost": hourly_cost,
            "total_requests": len(analyzer.metrics),
        },
    }


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    print("🔍 Chatbot Alert Monitor")
    print("=" * 50)
    print(f"Error rate threshold: {ERROR_RATE_THRESHOLD}%")
    print(f"Latency (p95) threshold: {LATENCY_P95_THRESHOLD}s")
    print(f"Cost per hour threshold: ${COST_PER_HOUR_THRESHOLD}")
    print(f"Alert cooldown: {ALERT_COOLDOWN_HOURS} hour(s)")
    print("=" * 50)

    result = check_and_alert()

    print("\n📊 Monitoring Results:")
    print(json.dumps(result, indent=2))

    if result["alerts_sent"]:
        print(f"\n⚠️  {len(result['alerts_sent'])} alert(s) sent!")
    else:
        print("\n✅ All systems nominal")
