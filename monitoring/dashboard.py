"""
Monitoring Dashboard for Streamlit Chatbot
Visualizes metrics from request logs: cost, latency, errors, token usage
"""

import json
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Configure page
st.set_page_config(
    page_title="Chatbot Monitoring Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Paths
METRICS_FILE = Path("../metrics/requests.jsonl")
FEEDBACK_FILE = Path("../metrics/feedback.jsonl")


def load_metrics():
    """Load metrics from JSONL file."""
    if not METRICS_FILE.exists():
        return pd.DataFrame()

    metrics = []
    try:
        with open(METRICS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    metrics.append(json.loads(line))

        if metrics:
            df = pd.DataFrame(metrics)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            return df
    except Exception as e:
        st.error(f"Error loading metrics: {e}")
        return pd.DataFrame()

    return pd.DataFrame()


def load_feedback():
    """Load feedback from JSONL file."""
    if not FEEDBACK_FILE.exists():
        return pd.DataFrame()

    feedback = []
    try:
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    feedback.append(json.loads(line))

        if feedback:
            df = pd.DataFrame(feedback)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            return df
    except Exception as e:
        st.error(f"Error loading feedback: {e}")
        return pd.DataFrame()

    return pd.DataFrame()


def calculate_percentile(data, percentile):
    """Calculate percentile value."""
    if len(data) == 0:
        return 0
    return data.quantile(percentile / 100)


# Header
st.title("📊 Chatbot Monitoring Dashboard")
st.caption("Real-time metrics and analytics for your LiteLLM-powered chatbot")

# Sidebar filters
with st.sidebar:
    st.header("⚙️ Filters")

    time_range = st.selectbox(
        "Time Range",
        ["Last Hour", "Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time"],
        index=1,
    )

    st.divider()

    if st.button("🔄 Refresh Data"):
        st.rerun()

    st.caption("Dashboard auto-refreshes on page reload")

# Load data
df = load_metrics()
feedback_df = load_feedback()

if df.empty:
    st.warning("No metrics data found. Start using the chatbot to generate metrics!")
    st.info(f"Metrics will be stored in: {METRICS_FILE.absolute()}")
    st.stop()

# Apply time filter
now = datetime.now()
time_filters = {
    "Last Hour": now - timedelta(hours=1),
    "Last 24 Hours": now - timedelta(days=1),
    "Last 7 Days": now - timedelta(days=7),
    "Last 30 Days": now - timedelta(days=30),
    "All Time": df["timestamp"].min(),
}

start_time = time_filters[time_range]
df_filtered = df[df["timestamp"] >= start_time].copy()

if df_filtered.empty:
    st.warning(f"No data in selected time range: {time_range}")
    st.stop()

# Key Metrics (Top Row)
st.header("📈 Key Metrics")

col1, col2, col3, col4, col5 = st.columns(5)

total_requests = len(df_filtered)
successful_requests = len(df_filtered[df_filtered["success"] == True])
failed_requests = len(df_filtered[df_filtered["success"] == False])
success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
total_cost = df_filtered["cost_usd"].sum()

with col1:
    st.metric("Total Requests", f"{total_requests:,}")

with col2:
    st.metric("Success Rate", f"{success_rate:.1f}%")

with col3:
    st.metric("Failed Requests", failed_requests)

with col4:
    st.metric("Total Cost", f"${total_cost:.4f}")

with col5:
    avg_duration = df_filtered["duration_seconds"].mean()
    st.metric("Avg Duration", f"{avg_duration:.2f}s")

st.divider()

# Latency Analysis
st.header("⚡ Latency Analysis")

col1, col2 = st.columns(2)

with col1:
    # Latency percentiles
    success_df = df_filtered[df_filtered["success"] == True]

    if not success_df.empty:
        p50 = calculate_percentile(success_df["duration_seconds"], 50)
        p95 = calculate_percentile(success_df["duration_seconds"], 95)
        p99 = calculate_percentile(success_df["duration_seconds"], 99)

        percentile_data = pd.DataFrame(
            {
                "Percentile": ["p50 (median)", "p95", "p99"],
                "Duration (seconds)": [p50, p95, p99],
            }
        )

        fig = px.bar(
            percentile_data,
            x="Percentile",
            y="Duration (seconds)",
            title="Response Time Percentiles",
            color="Duration (seconds)",
            color_continuous_scale="Viridis",
        )
        st.plotly_chart(fig, use_container_width=True)

with col2:
    # Latency over time
    if not success_df.empty:
        fig = px.scatter(
            success_df,
            x="timestamp",
            y="duration_seconds",
            title="Response Time Over Time",
            labels={"duration_seconds": "Duration (seconds)", "timestamp": "Time"},
            trendline="lowess",
            opacity=0.6,
        )
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# Cost Analysis
st.header("💰 Cost Analysis")

col1, col2 = st.columns(2)

with col1:
    # Cost over time (cumulative)
    df_filtered_sorted = df_filtered.sort_values("timestamp")
    df_filtered_sorted["cumulative_cost"] = df_filtered_sorted["cost_usd"].cumsum()

    fig = px.line(
        df_filtered_sorted,
        x="timestamp",
        y="cumulative_cost",
        title="Cumulative Cost Over Time",
        labels={"cumulative_cost": "Total Cost (USD)", "timestamp": "Time"},
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Cost per request
    fig = px.histogram(
        df_filtered[df_filtered["cost_usd"] > 0],
        x="cost_usd",
        title="Cost Distribution per Request",
        labels={"cost_usd": "Cost (USD)"},
        nbins=30,
    )
    st.plotly_chart(fig, use_container_width=True)

# Token usage metrics
col1, col2, col3 = st.columns(3)

with col1:
    total_tokens = df_filtered["total_tokens"].sum()
    st.metric("Total Tokens", f"{total_tokens:,}")

with col2:
    avg_prompt_tokens = df_filtered[df_filtered["success"] == True][
        "prompt_tokens"
    ].mean()
    st.metric("Avg Input Tokens", f"{avg_prompt_tokens:.0f}")

with col3:
    avg_completion_tokens = df_filtered[df_filtered["success"] == True][
        "completion_tokens"
    ].mean()
    st.metric("Avg Output Tokens", f"{avg_completion_tokens:.0f}")

st.divider()

# Error Analysis
st.header("🚨 Error Analysis")

if failed_requests > 0:
    col1, col2 = st.columns(2)

    with col1:
        # Error types distribution
        error_df = df_filtered[df_filtered["success"] == False]
        error_counts = error_df["error_type"].value_counts()

        fig = px.pie(
            values=error_counts.values,
            names=error_counts.index,
            title="Error Types Distribution",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Error rate over time
        df_filtered_sorted["hour"] = df_filtered_sorted["timestamp"].dt.floor("H")
        hourly_stats = (
            df_filtered_sorted.groupby("hour")
            .agg({"success": ["count", "sum"]})
            .reset_index()
        )
        hourly_stats.columns = ["hour", "total", "successful"]
        hourly_stats["error_rate"] = (
            1 - hourly_stats["successful"] / hourly_stats["total"]
        ) * 100

        fig = px.line(
            hourly_stats,
            x="hour",
            y="error_rate",
            title="Error Rate Over Time (Hourly)",
            labels={"error_rate": "Error Rate (%)", "hour": "Time"},
        )
        st.plotly_chart(fig, use_container_width=True)

    # Recent errors table
    st.subheader("Recent Errors")
    recent_errors = error_df.nlargest(10, "timestamp")[
        ["timestamp", "error_type", "error_message", "model", "temperature"]
    ]
    st.dataframe(recent_errors, use_container_width=True)
else:
    st.success("✅ No errors in selected time range!")

st.divider()

# Feedback Analysis
st.header("💬 User Feedback")

if not feedback_df.empty:
    feedback_filtered = feedback_df[feedback_df["timestamp"] >= start_time]

    if not feedback_filtered.empty:
        col1, col2, col3 = st.columns(3)

        positive_count = len(
            feedback_filtered[feedback_filtered["rating"] == "positive"]
        )
        negative_count = len(
            feedback_filtered[feedback_filtered["rating"] == "negative"]
        )
        total_feedback = positive_count + negative_count

        with col1:
            st.metric("Total Feedback", total_feedback)

        with col2:
            st.metric("👍 Positive", positive_count)

        with col3:
            st.metric("👎 Negative", negative_count)

        # Feedback ratio
        if total_feedback > 0:
            satisfaction_rate = (positive_count / total_feedback) * 100
            st.progress(satisfaction_rate / 100)
            st.caption(f"Satisfaction Rate: {satisfaction_rate:.1f}%")
    else:
        st.info("No feedback in selected time range.")
else:
    st.info(
        "No user feedback collected yet. Users can rate responses with 👍/👎 buttons."
    )

st.divider()

# Model Performance
st.header("🤖 Model Performance")

# Group by model
if "model" in df_filtered.columns:
    model_stats = (
        df_filtered.groupby("model")
        .agg(
            {
                "request_id": "count",
                "duration_seconds": "mean",
                "cost_usd": "sum",
                "total_tokens": "sum",
                "success": lambda x: (x == True).sum() / len(x) * 100,
            }
        )
        .reset_index()
    )

    model_stats.columns = [
        "Model",
        "Requests",
        "Avg Duration (s)",
        "Total Cost ($)",
        "Total Tokens",
        "Success Rate (%)",
    ]

    st.dataframe(
        model_stats.style.format(
            {
                "Avg Duration (s)": "{:.2f}",
                "Total Cost ($)": "${:.6f}",
                "Total Tokens": "{:,.0f}",
                "Success Rate (%)": "{:.1f}%",
            }
        ),
        use_container_width=True,
    )

# Footer
st.divider()
st.caption(
    f"Dashboard generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data range: {time_range}"
)
st.caption(f"Monitoring {len(df)} total requests across all time")
