"""
Streamlit Monitoring Dashboard - /monitor page
Shows real-time metrics from Langfuse and local JSONL files
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import hashlib
import requests
from typing import Optional, Dict, List, Any
import os
import base64

# ====== Configuration ======
METRICS_DIR = Path("metrics")
LOGS_DIR = Path("logs")
DEMO_DATA_DIR = Path("demo_data")

# Langfuse configuration
LANGFUSE_ENABLED = os.getenv("ENABLE_LANGFUSE", "true").lower() == "true"
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")

# Performance limits
MAX_LOG_LINES = int(os.getenv("MONITOR_MAX_LOG_LINES", "1000"))
MAX_CHART_POINTS = int(os.getenv("MONITOR_MAX_CHART_POINTS", "500"))
LOG_PAGE_SIZE = 100

# Dark mode friendly color palette
COLORS = {
    "primary": "#3B82F6",  # Blue
    "success": "#10B981",  # Green
    "warning": "#F59E0B",  # Amber
    "danger": "#EF4444",  # Red
    "info": "#06B6D4",  # Cyan
    "secondary": "#8B5CF6",  # Purple
    "accent": "#EC4899",  # Pink
}

# Chart color scheme (dark mode friendly)
CHART_COLORS = [
    "#3B82F6",
    "#10B981",
    "#F59E0B",
    "#EF4444",
    "#8B5CF6",
    "#EC4899",
    "#06B6D4",
    "#14B8A6",
]

# Localized labels
LABELS = {
    "en": {
        "title": "📊 Real-Time Monitoring Dashboard",
        "time_range": "Time Range",
        "refresh": "Refresh Data",
        "last_updated": "Last Updated",
        "request_count": "Request Count",
        "latency": "Latency",
        "tokens": "Token Usage",
        "errors": "Error Rate",
        "cost": "Estimated Cost",
        "feedback": "User Feedback",
        "logs": "Live Logs",
        "p50": "P50 (Median)",
        "p95": "P95",
        "p99": "P99",
        "total": "Total",
        "avg": "Average",
        "prompt": "Prompt Tokens",
        "completion": "Completion Tokens",
        "thumbs_up": "Thumbs Up",
        "thumbs_down": "Thumbs Down",
        "log_level": "Log Level",
        "module": "Module",
        "session": "Session ID",
        "filter": "Filter",
        "show_more": "Load More",
    }
}

# Model cost map (USD per 1M tokens)
MODEL_COSTS = {
    "openai/gemini-3-flash": {"input": 0.075, "output": 0.30},
    "openai/gemini-2-pro": {"input": 0.50, "output": 1.50},
    "gemini/gemini-3-flash": {"input": 0.075, "output": 0.30},
    "gemini/gemini-2-pro": {"input": 0.50, "output": 1.50},
}

# ====== Page Configuration ======
st.set_page_config(
    page_title="Monitor | Chatbot",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for dark mode friendly design
st.markdown(
    """
<style>
    /* Dark mode friendly metrics */
    .metric-card {
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 8px;
        padding: 16px;
        margin: 8px 0;
    }
    
    /* Log viewer styling */
    .log-entry {
        font-family: 'Courier New', monospace;
        font-size: 12px;
        padding: 4px 8px;
        margin: 2px 0;
        border-left: 3px solid rgba(59, 130, 246, 0.5);
        background: rgba(0, 0, 0, 0.1);
    }
    
    .log-error { border-left-color: #EF4444; }
    .log-warning { border-left-color: #F59E0B; }
    .log-info { border-left-color: #10B981; }
    .log-debug { border-left-color: #8B5CF6; }
    
    /* Responsive charts */
    .plotly-chart {
        width: 100%;
        height: auto;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ====== Helper Functions ======


def get_labels(lang: str = "en") -> Dict[str, str]:
    """Get localized labels"""
    return LABELS.get(lang, LABELS["en"])


def hash_query(query: str) -> str:
    """Hash query for anonymization"""
    return hashlib.sha256(query.encode()).hexdigest()[:12]


def get_langfuse_stats(hours: int = 24) -> Optional[Dict[str, Any]]:
    """
    Fetch statistics from Langfuse API
    Returns aggregated metrics for the specified time range
    """
    if not LANGFUSE_ENABLED or not LANGFUSE_PUBLIC_KEY or not LANGFUSE_SECRET_KEY:
        return None

    try:
        # Create basic auth header
        auth_string = f"{LANGFUSE_PUBLIC_KEY}:{LANGFUSE_SECRET_KEY}"
        auth_bytes = auth_string.encode("ascii")
        auth_b64 = base64.b64encode(auth_bytes).decode("ascii")

        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/json",
        }

        # Calculate time range
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)

        # Fetch traces with observations
        traces_url = f"{LANGFUSE_HOST}/api/public/traces"
        params = {
            "fromTimestamp": start_time.isoformat(),
            "toTimestamp": end_time.isoformat(),
            "page": 1,
            "limit": 50,  # Fetch 50 most recent traces
        }

        response = requests.get(traces_url, headers=headers, params=params, timeout=10)

        if response.status_code == 401:
            return {"error": "Authentication failed. Check your Langfuse API keys."}
        elif response.status_code == 403:
            return {"error": "Access denied. Verify your Langfuse permissions."}
        elif response.status_code != 200:
            return {"error": f"Langfuse API returned status {response.status_code}"}

        data = response.json()
        traces = data.get("data", [])

        if not traces:
            return {
                "total_traces": 0,
                "total_observations": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "avg_latency": 0.0,
                "traces": [],
                "has_data": False,
            }

        # Aggregate statistics from traces (trace-level data)
        total_traces = len(traces)
        total_observations = 0
        total_input_tokens = 0
        total_output_tokens = 0
        total_cost = 0.0
        latencies = []

        for trace in traces:
            if not isinstance(trace, dict):
                continue

            # Get trace-level cost and latency (already calculated by Langfuse)
            trace_cost = trace.get("totalCost")
            if trace_cost:
                total_cost += float(trace_cost)

            trace_latency = trace.get("latency")
            if trace_latency:
                latencies.append(float(trace_latency))

            # Count observations
            obs_ids = trace.get("observations", [])
            if isinstance(obs_ids, list):
                total_observations += len(obs_ids)

        # Estimate tokens from cost (approximate)
        # Gemini pricing: $0.075/1M input tokens, $0.30/1M output tokens
        # Rough estimate: assume 3:1 ratio of output to input cost
        if total_cost > 0:
            estimated_output_tokens = int((total_cost * 0.75) / 0.30 * 1_000_000)
            estimated_input_tokens = int((total_cost * 0.25) / 0.075 * 1_000_000)
            total_input_tokens = estimated_input_tokens
            total_output_tokens = estimated_output_tokens

        return {
            "total_traces": total_traces,
            "total_observations": total_observations,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_tokens": total_input_tokens + total_output_tokens,
            "total_cost": total_cost,
            "avg_latency": sum(latencies) / len(latencies) if latencies else 0.0,
            "median_latency": (
                sorted(latencies)[len(latencies) // 2] if latencies else 0.0
            ),
            "p95_latency": (
                sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0.0
            ),
            "traces": traces,
            "has_data": True,
        }

    except requests.exceptions.Timeout:
        return {"error": "Langfuse API request timed out. Try again later."}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to Langfuse. Check your network connection."}
    except requests.exceptions.RequestException as e:
        return {"error": f"Error fetching Langfuse data: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def load_jsonl_metrics(time_range_hours: int = 24) -> pd.DataFrame:
    """Load metrics from JSONL files"""
    metrics_file = METRICS_DIR / "requests.jsonl"
    demo_file = DEMO_DATA_DIR / "demo_metrics.jsonl"

    # Try demo data first if main file doesn't exist
    if not metrics_file.exists() and demo_file.exists():
        metrics_file = demo_file
        st.info("📦 Using demo data (no real requests yet)")

    if not metrics_file.exists():
        return pd.DataFrame()

    try:
        data = []
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_range_hours)

        with open(metrics_file, "r") as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    timestamp = pd.to_datetime(record["timestamp"])

                    # Filter by time range
                    if timestamp >= cutoff_time:
                        data.append(record)

                    # Performance limit
                    if len(data) >= MAX_CHART_POINTS * 2:
                        break
                except:
                    continue

        df = pd.DataFrame(data)
        if not df.empty:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp")

        return df
    except Exception as e:
        st.error(f"Failed to load metrics: {e}")
        return pd.DataFrame()


def load_feedback_data() -> pd.DataFrame:
    """Load user feedback from JSONL"""
    feedback_file = METRICS_DIR / "feedback.jsonl"
    demo_file = DEMO_DATA_DIR / "demo_feedback.jsonl"

    if not feedback_file.exists() and demo_file.exists():
        feedback_file = demo_file

    if not feedback_file.exists():
        return pd.DataFrame()

    try:
        data = []
        with open(feedback_file, "r") as f:
            for line in f:
                try:
                    data.append(json.loads(line.strip()))
                except:
                    continue

        df = pd.DataFrame(data)
        if not df.empty:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    except:
        return pd.DataFrame()


def load_logs(
    level_filter: Optional[str] = None,
    module_filter: Optional[str] = None,
    session_filter: Optional[str] = None,
    limit: int = MAX_LOG_LINES,
) -> List[Dict]:
    """Load and filter structured logs"""
    log_file = LOGS_DIR / "chatbot.log"
    demo_file = DEMO_DATA_DIR / "demo_logs.log"

    if not log_file.exists() and demo_file.exists():
        log_file = demo_file

    if not log_file.exists():
        return []

    try:
        logs = []
        with open(log_file, "r", encoding="utf-8") as f:
            # Read from end of file for recent logs
            lines = f.readlines()

        # Reverse to get newest first
        for line in reversed(lines[-limit * 2 :]):  # Read 2x limit for filtering
            try:
                # Parse log line format: "timestamp - module - level - message"
                parts = line.strip().split(" - ", 3)
                if len(parts) >= 4:
                    log_entry = {
                        "timestamp": parts[0],
                        "module": parts[1],
                        "level": parts[2],
                        "message": parts[3],
                    }

                    # Apply filters
                    if level_filter and log_entry["level"] != level_filter:
                        continue
                    if module_filter and module_filter not in log_entry["module"]:
                        continue
                    if session_filter and session_filter not in log_entry["message"]:
                        continue

                    logs.append(log_entry)

                    if len(logs) >= limit:
                        break
            except:
                continue

        return logs
    except Exception as e:
        st.error(f"Failed to load logs: {e}")
        return []


def calculate_latency_percentiles(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate latency percentiles from DataFrame"""
    if df.empty or "duration_seconds" not in df.columns:
        return {"p50": 0, "p95": 0, "p99": 0}

    return {
        "p50": df["duration_seconds"].quantile(0.50),
        "p95": df["duration_seconds"].quantile(0.95),
        "p99": df["duration_seconds"].quantile(0.99),
    }


def calculate_cost(df: pd.DataFrame) -> float:
    """Calculate total cost from metrics"""
    if df.empty:
        return 0.0

    if "cost_usd" in df.columns:
        return df["cost_usd"].sum()

    # Calculate from tokens if cost not available
    total_cost = 0.0
    for _, row in df.iterrows():
        model = row.get("model", "openai/gemini-3-flash")
        costs = MODEL_COSTS.get(model, MODEL_COSTS["openai/gemini-3-flash"])

        prompt_tokens = row.get("prompt_tokens", 0)
        completion_tokens = row.get("completion_tokens", 0)

        total_cost += prompt_tokens / 1_000_000 * costs["input"]
        total_cost += completion_tokens / 1_000_000 * costs["output"]

    return total_cost


# ====== Main Dashboard ======


def main():
    labels = get_labels()

    # Header
    st.title(labels["title"])

    # Sidebar controls
    with st.sidebar:
        st.header("⚙️ Controls")

        # Time range
        time_range = st.selectbox(
            labels["time_range"],
            ["Last Hour", "Last 6 Hours", "Last 24 Hours", "Last 7 Days"],
            index=2,
        )

        time_range_map = {
            "Last Hour": 1,
            "Last 6 Hours": 6,
            "Last 24 Hours": 24,
            "Last 7 Days": 168,
        }
        hours = time_range_map[time_range]

        # Refresh button
        if st.button(labels["refresh"], use_container_width=True):
            st.rerun()

        st.divider()

        # Status
        st.caption(f"{labels['last_updated']}: {datetime.now().strftime('%H:%M:%S')}")

        # Demo data info
        if (DEMO_DATA_DIR / "demo_metrics.jsonl").exists():
            st.info("💡 Demo data available for testing")

    # Load data from local files
    with st.spinner("Loading local metrics..."):
        df_metrics = load_jsonl_metrics(hours)

    if not df_metrics.empty:
        st.info("📁 Using local JSONL data")

    if df_metrics is None or df_metrics.empty:
        st.warning("No data available. Generate some requests or check data sources.")
        # Don't stop - still show Langfuse stats if available
        df_metrics = pd.DataFrame()  # Empty dataframe for compatibility

    # ====== Langfuse Statistics Section ======
    if LANGFUSE_ENABLED and LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY:
        st.divider()
        st.header("🔍 Langfuse Tracing Statistics")

        with st.spinner("Fetching Langfuse statistics..."):
            langfuse_stats = get_langfuse_stats(hours)

        if langfuse_stats and "error" in langfuse_stats:
            st.error(f"⚠️ {langfuse_stats['error']}")
        elif langfuse_stats and langfuse_stats.get("has_data", False):
            # Langfuse metrics row
            lf_col1, lf_col2, lf_col3, lf_col4, lf_col5 = st.columns(5)

            with lf_col1:
                st.metric(
                    "Total Traces",
                    f"{langfuse_stats['total_traces']:,}",
                    help="Number of traces captured by Langfuse",
                )

            with lf_col2:
                st.metric(
                    "Total Tokens",
                    f"{langfuse_stats['total_tokens']:,}",
                    help=f"Input: {langfuse_stats['total_input_tokens']:,} | Output: {langfuse_stats['total_output_tokens']:,}",
                )

            with lf_col3:
                st.metric(
                    "Avg Latency",
                    f"{langfuse_stats['avg_latency']:.2f}s",
                    help=f"Median: {langfuse_stats['median_latency']:.2f}s | P95: {langfuse_stats['p95_latency']:.2f}s",
                )

            with lf_col4:
                st.metric(
                    "Total Cost",
                    f"${langfuse_stats['total_cost']:.4f}",
                    help="Calculated cost from Langfuse traces",
                )

            with lf_col5:
                avg_tokens_per_trace = (
                    langfuse_stats["total_tokens"] / langfuse_stats["total_traces"]
                    if langfuse_stats["total_traces"] > 0
                    else 0
                )
                st.metric(
                    "Avg Tokens/Trace",
                    f"{avg_tokens_per_trace:.0f}",
                    help="Average tokens per conversation trace",
                )

            # Recent traces table
            if langfuse_stats["traces"]:
                st.subheader("📋 Recent Traces")

                # Create expandable section for trace details
                with st.expander("View Trace Details", expanded=True):
                    traces_data = []
                    for trace in langfuse_stats["traces"][:20]:  # Show latest 20
                        # Get latency directly from trace (already calculated by Langfuse)
                        latency_str = "N/A"
                        trace_latency = trace.get("latency")
                        if trace_latency:
                            latency_str = f"{float(trace_latency):.2f}s"

                        # Get cost directly from trace
                        trace_cost = trace.get("totalCost", 0)

                        # Estimate tokens from cost if available
                        total_tokens = 0
                        if trace_cost and trace_cost > 0:
                            # Rough estimate based on Gemini pricing
                            estimated_output = int(
                                (trace_cost * 0.75) / 0.30 * 1_000_000
                            )
                            estimated_input = int(
                                (trace_cost * 0.25) / 0.075 * 1_000_000
                            )
                            total_tokens = estimated_input + estimated_output

                        traces_data.append(
                            {
                                "Timestamp": trace.get("timestamp", "")[:19].replace(
                                    "T", " "
                                ),
                                "Name": trace.get("name", "N/A"),
                                "Latency": latency_str,
                                "Tokens": total_tokens,
                                "Cost": f"${float(trace_cost):.5f}",
                                "Status": (
                                    "✅"
                                    if not trace.get("level")
                                    or trace.get("level") == "DEFAULT"
                                    else "⚠️"
                                ),
                                "Trace ID": trace.get("id", "")[:8] + "e",
                            }
                        )

                    df_traces = pd.DataFrame(traces_data)
                    st.dataframe(
                        df_traces,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Timestamp": st.column_config.TextColumn(
                                "Timestamp", width="medium"
                            ),
                            "Name": st.column_config.TextColumn("Name", width="medium"),
                            "Latency": st.column_config.TextColumn(
                                "Latency", width="small"
                            ),
                            "Tokens": st.column_config.NumberColumn(
                                "Tokens", width="small"
                            ),
                            "Cost": st.column_config.TextColumn("Cost", width="small"),
                            "Status": st.column_config.TextColumn(
                                "Status", width="small"
                            ),
                            "Trace ID": st.column_config.TextColumn(
                                "Trace ID", width="small"
                            ),
                        },
                    )

                # Link to Langfuse dashboard
                st.markdown(
                    f"""
                    <a href="{LANGFUSE_HOST}" target="_blank" style="
                        display: inline-block;
                        padding: 8px 16px;
                        background-color: {COLORS['primary']};
                        color: white;
                        text-decoration: none;
                        border-radius: 4px;
                        margin-top: 8px;
                    ">
                        🔗 View Full Dashboard in Langfuse
                    </a>
                """,
                    unsafe_allow_html=True,
                )
        else:
            st.info(
                f"📊 Langfuse tracing is enabled but no data available for the last {hours} hours. Start chatting to generate traces!"
            )

    if df_metrics.empty:
        st.stop()  # Stop here if no local metrics available

    # ====== Local Metrics Row ======
    st.divider()
    st.header("📊 Local Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_requests = len(df_metrics)
        st.metric(labels["request_count"], f"{total_requests:,}")

    with col2:
        success_rate = (
            (df_metrics["success"].sum() / len(df_metrics) * 100)
            if "success" in df_metrics.columns
            else 100
        )
        st.metric("Success Rate", f"{success_rate:.1f}%")

    with col3:
        percentiles = calculate_latency_percentiles(df_metrics)
        st.metric(f"{labels['latency']} (P95)", f"{percentiles['p95']:.2f}s")

    with col4:
        total_cost = calculate_cost(df_metrics)
        st.metric(labels["cost"], f"${total_cost:.4f}")

    # ====== Charts Section ======

    # Request Count Over Time
    st.subheader(f"📈 {labels['request_count']} Over Time")

    if not df_metrics.empty:
        # Resample to handle large datasets
        df_resampled = (
            df_metrics.set_index("timestamp")
            .resample("5T")
            .size()
            .reset_index(name="count")
        )

        # Limit points for performance
        if len(df_resampled) > MAX_CHART_POINTS:
            sample_rate = len(df_resampled) // MAX_CHART_POINTS
            df_resampled = df_resampled.iloc[::sample_rate]

        fig_requests = px.area(
            df_resampled,
            x="timestamp",
            y="count",
            title=f'{labels["request_count"]} (5-minute buckets)',
            color_discrete_sequence=[COLORS["primary"]],
        )
        fig_requests.update_layout(
            xaxis_title="Time",
            yaxis_title="Requests",
            hovermode="x unified",
            template="plotly_dark",
        )
        st.plotly_chart(fig_requests, use_container_width=True)

    # Latency Distribution
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"⏱️ {labels['latency']} Distribution")

        if "duration_seconds" in df_metrics.columns:
            fig_latency = go.Figure()

            # P50, P95, P99 over time
            df_latency = (
                df_metrics.set_index("timestamp")
                .resample("10T")["duration_seconds"]
                .quantile([0.5, 0.95, 0.99])
                .unstack()
            )

            if len(df_latency) > MAX_CHART_POINTS:
                sample_rate = len(df_latency) // MAX_CHART_POINTS
                df_latency = df_latency.iloc[::sample_rate]

            df_latency = df_latency.reset_index()

            fig_latency.add_trace(
                go.Scatter(
                    x=df_latency["timestamp"],
                    y=df_latency[0.5],
                    name=labels["p50"],
                    line=dict(color=COLORS["success"]),
                )
            )
            fig_latency.add_trace(
                go.Scatter(
                    x=df_latency["timestamp"],
                    y=df_latency[0.95],
                    name=labels["p95"],
                    line=dict(color=COLORS["warning"]),
                )
            )
            fig_latency.add_trace(
                go.Scatter(
                    x=df_latency["timestamp"],
                    y=df_latency[0.99],
                    name=labels["p99"],
                    line=dict(color=COLORS["danger"]),
                )
            )

            fig_latency.update_layout(
                xaxis_title="Time",
                yaxis_title="Latency (seconds)",
                hovermode="x unified",
                template="plotly_dark",
            )
            st.plotly_chart(fig_latency, use_container_width=True)
        else:
            st.info("No latency data available")

    with col2:
        st.subheader(f"🔢 {labels['tokens']}")

        if "total_tokens" in df_metrics.columns:
            # Rolling total
            df_tokens = (
                df_metrics.set_index("timestamp")[
                    ["prompt_tokens", "completion_tokens"]
                ]
                .resample("10T")
                .sum()
            )

            if len(df_tokens) > MAX_CHART_POINTS:
                sample_rate = len(df_tokens) // MAX_CHART_POINTS
                df_tokens = df_tokens.iloc[::sample_rate]

            df_tokens = df_tokens.reset_index()

            fig_tokens = go.Figure()
            fig_tokens.add_trace(
                go.Bar(
                    x=df_tokens["timestamp"],
                    y=df_tokens["prompt_tokens"],
                    name=labels["prompt"],
                    marker_color=COLORS["info"],
                )
            )
            fig_tokens.add_trace(
                go.Bar(
                    x=df_tokens["timestamp"],
                    y=df_tokens["completion_tokens"],
                    name=labels["completion"],
                    marker_color=COLORS["secondary"],
                )
            )

            fig_tokens.update_layout(
                barmode="stack",
                xaxis_title="Time",
                yaxis_title="Tokens",
                hovermode="x unified",
                template="plotly_dark",
            )
            st.plotly_chart(fig_tokens, use_container_width=True)

            # Token statistics
            st.metric(
                f"{labels['total']} Tokens", f"{df_metrics['total_tokens'].sum():,}"
            )
        else:
            st.info("No token data available")

    # Error Rate
    st.subheader(f"⚠️ {labels['errors']} (Last 24h)")

    col1, col2 = st.columns([2, 1])

    with col1:
        if "success" in df_metrics.columns:
            # Error rate over time
            df_errors = (
                df_metrics.set_index("timestamp")
                .resample("10T")
                .agg({"success": lambda x: (1 - x.mean()) * 100})
                .reset_index()
            )
            df_errors.columns = ["timestamp", "error_rate"]

            if len(df_errors) > MAX_CHART_POINTS:
                sample_rate = len(df_errors) // MAX_CHART_POINTS
                df_errors = df_errors.iloc[::sample_rate]

            fig_errors = px.line(
                df_errors,
                x="timestamp",
                y="error_rate",
                title="Error Rate (%)",
                color_discrete_sequence=[COLORS["danger"]],
            )
            fig_errors.update_layout(
                xaxis_title="Time", yaxis_title="Error Rate (%)", template="plotly_dark"
            )
            st.plotly_chart(fig_errors, use_container_width=True)

    with col2:
        # Error breakdown by type
        if "error_type" in df_metrics.columns:
            error_df = df_metrics[df_metrics["success"] == False]
            if not error_df.empty:
                error_counts = error_df["error_type"].value_counts()

                fig_error_pie = px.pie(
                    values=error_counts.values,
                    names=error_counts.index,
                    title="Error Types",
                    color_discrete_sequence=CHART_COLORS,
                )
                fig_error_pie.update_layout(template="plotly_dark")
                st.plotly_chart(fig_error_pie, use_container_width=True)
            else:
                st.success("✅ No errors in this period!")
        else:
            st.info("No error data")

    # Top Queries (Anonymized)
    st.subheader("🔍 Top Queries (Anonymized)")

    col1, col2 = st.columns([2, 1])

    with col1:
        if "user_message_length" in df_metrics.columns:
            # Group by message length buckets
            df_metrics["length_bucket"] = pd.cut(
                df_metrics["user_message_length"],
                bins=[0, 50, 100, 200, 500, 1000, 10000],
                labels=["<50", "50-100", "100-200", "200-500", "500-1000", "1000+"],
            )

            query_dist = df_metrics["length_bucket"].value_counts().sort_index()

            fig_queries = px.bar(
                x=query_dist.index,
                y=query_dist.values,
                title="Query Length Distribution",
                labels={"x": "Message Length (chars)", "y": "Count"},
                color_discrete_sequence=[COLORS["info"]],
            )
            fig_queries.update_layout(template="plotly_dark")
            st.plotly_chart(fig_queries, use_container_width=True)
        else:
            st.info("No query data available")

    with col2:
        # User feedback
        st.subheader(f"👍 {labels['feedback']}")

        df_feedback = load_feedback_data()
        if not df_feedback.empty:
            feedback_counts = df_feedback["rating"].value_counts()

            positive = feedback_counts.get("positive", 0)
            negative = feedback_counts.get("negative", 0)
            total_feedback = positive + negative

            if total_feedback > 0:
                satisfaction = (positive / total_feedback) * 100

                st.metric("Satisfaction Rate", f"{satisfaction:.1f}%")
                st.metric(labels["thumbs_up"], positive)
                st.metric(labels["thumbs_down"], negative)
            else:
                st.info("No feedback yet")
        else:
            st.info("No feedback data")

    # Live Logs
    st.subheader(f"📜 {labels['logs']}")

    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

    with col1:
        level_filter = st.selectbox(
            labels["log_level"],
            ["All", "INFO", "WARNING", "ERROR", "DEBUG"],
            key="log_level_filter",
        )

    with col2:
        module_filter = st.text_input(
            labels["module"], placeholder="e.g. backend", key="module_filter"
        )

    with col3:
        session_filter = st.text_input(
            labels["session"], placeholder="e.g. session_id", key="session_filter"
        )

    with col4:
        st.write("")  # Spacer
        st.write("")
        if st.button("🔄", help="Refresh logs"):
            st.rerun()

    # Load and display logs
    logs = load_logs(
        level_filter if level_filter != "All" else None,
        module_filter if module_filter else None,
        session_filter if session_filter else None,
        limit=LOG_PAGE_SIZE,
    )

    if logs:
        # Create paginated log viewer
        if "log_page" not in st.session_state:
            st.session_state.log_page = 0

        start_idx = st.session_state.log_page * LOG_PAGE_SIZE
        end_idx = start_idx + LOG_PAGE_SIZE
        page_logs = logs[start_idx:end_idx]

        # Display logs
        for log in page_logs:
            level_class = f"log-{log['level'].lower()}"
            st.markdown(
                f"""<div class="log-entry {level_class}">
                <strong>{log['timestamp']}</strong> | 
                <span style="color: {COLORS.get(log['level'].lower(), COLORS['info'])}">{log['level']}</span> | 
                {log['module']} | {log['message'][:200]}
                </div>""",
                unsafe_allow_html=True,
            )

        # Pagination controls
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.session_state.log_page > 0:
                if st.button("⬅️ Previous"):
                    st.session_state.log_page -= 1
                    st.rerun()
        with col2:
            st.caption(
                f"Showing {start_idx+1}-{min(end_idx, len(logs))} of {len(logs)} logs"
            )
        with col3:
            if end_idx < len(logs):
                if st.button("Next ➡️"):
                    st.session_state.log_page += 1
                    st.rerun()
    else:
        st.info("No logs match the current filters")

    # Footer
    st.divider()
    st.caption(
        f"Dashboard refreshed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"
    )


if __name__ == "__main__":
    main()
