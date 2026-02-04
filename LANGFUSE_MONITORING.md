# Langfuse Monitoring Integration - Summary

## What's New

✅ **Integrated Langfuse statistics into the Monitoring tab**

The Streamlit chatbot monitoring page now displays real-time Langfuse tracing data alongside local metrics!

## Features Added

### 1. Real-Time Langfuse Statistics

**Location:** Monitor tab → "🔍 Langfuse Tracing Statistics" section

**Metrics Displayed:**
- **Total Traces**: Number of conversation traces captured
- **Total Tokens**: Input + Output tokens across all traces
- **Avg Latency**: Mean response time (with P50, P95 in tooltip)
- **Total Cost**: Calculated cost from Langfuse data
- **Avg Tokens/Trace**: Average tokens per conversation

### 2. Recent Traces Table

Shows the **latest 20 traces** with:
- Timestamp
- Trace name
- Latency (calculated from start/end times)
- Token count
- Cost per trace
- Status (✅ success, ⚠️ warning)
- Trace ID (first 8 chars)

### 3. Direct Langfuse Link

Button to open the full Langfuse dashboard in a new tab for detailed analysis.

## How It Works

1. **API Integration**: Calls Langfuse Public API (`GET /api/public/traces`)
2. **Authentication**: Uses Basic Auth with your configured keys
3. **Time Range**: Respects the selected time range (Last Hour, 6 Hours, 24 Hours, 7 Days)
4. **Auto-Refresh**: Click "Refresh Data" in sidebar to update statistics
5. **Error Handling**: Gracefully handles API errors with helpful messages

## Configuration

Already configured in your `.env` file:

```env
ENABLE_LANGFUSE=true
LANGFUSE_PUBLIC_KEY=pk-lf-664c8f80...
LANGFUSE_SECRET_KEY=sk-lf-de6a9015...
LANGFUSE_HOST=https://cloud.langfuse.com
```

**No additional setup required!** The integration is ready to use.

## Usage

1. Start the Streamlit app:
   ```bash
   .\venv\Scripts\python.exe -m streamlit run app.py
   ```

2. Navigate to the **Monitor** tab in the sidebar

3. You'll see two main sections:
   - **🔍 Langfuse Tracing Statistics** (at the top)
   - **📊 Local Metrics** (below)

4. Select time range in the sidebar (defaults to Last 24 Hours)

5. Click "Refresh Data" to update statistics

## What You'll See

### If you have Langfuse data:
- 5 metric cards showing key statistics
- Expandable table with recent traces
- Link to full Langfuse dashboard

### If no data yet:
- Info message: "Langfuse tracing is enabled but no data available for the last X hours. Start chatting to generate traces!"

### If there's an error:
- Error message with specific issue (auth failed, timeout, etc.)

## Benefits

✅ **Single Dashboard**: View both Langfuse and local metrics in one place
✅ **Real-Time**: See up-to-date statistics without leaving the app
✅ **Cost Tracking**: Monitor costs directly from Langfuse calculations
✅ **Performance Analysis**: View latency percentiles and token usage
✅ **Trace Debugging**: Quick access to recent traces with status indicators
✅ **Deep Dive**: One-click access to full Langfuse dashboard

## File Changes

**Modified:**
- `pages/2_Monitor.py` - Added Langfuse API integration and UI components
- `MONITORING.md` - Updated documentation with Langfuse integration info

**New Function:**
- `get_langfuse_stats(hours)` - Fetches and aggregates Langfuse trace data

## Performance

- Fetches **50 most recent traces** per request
- Displays **20 traces** in the table
- Timeout: **10 seconds** (configurable)
- Automatic error handling and retry logic

## Error Messages

**401 Unauthorized:**
> "Authentication failed. Check your Langfuse API keys."

**403 Forbidden:**
> "Access denied. Verify your Langfuse permissions."

**Timeout:**
> "Langfuse API request timed out. Try again later."

**Connection Error:**
> "Cannot connect to Langfuse. Check your network connection."

## Next Steps

1. ✅ **Test the integration**: Open the Monitor tab and verify statistics display
2. ✅ **Generate some traces**: Chat with the bot to create trace data
3. ✅ **Monitor costs**: Keep an eye on token usage and costs
4. ✅ **Set up alerts** (optional): Configure email/Slack alerts based on metrics

## Screenshots Preview

```
🔍 Langfuse Tracing Statistics
┌─────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│ Total       │ Total       │ Avg         │ Total       │ Avg Tokens/ │
│ Traces      │ Tokens      │ Latency     │ Cost        │ Trace       │
│ 42          │ 5,678       │ 3.45s       │ $0.0234     │ 135         │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────┘

📋 Recent Traces
┌────────────────────┬─────────┬─────────┬────────┬──────────┬────────┬──────────┐
│ Timestamp          │ Name    │ Latency │ Tokens │ Cost     │ Status │ ID       │
├────────────────────┼─────────┼─────────┼────────┼──────────┼────────┼──────────┤
│ 2026-02-04 15:30   │ chat    │ 3.45s   │ 135    │ $0.00011 │ ✅     │ a1b2c3d4 │
│ 2026-02-04 15:25   │ chat    │ 2.89s   │ 142    │ $0.00012 │ ✅     │ e5f6g7h8 │
└────────────────────┴─────────┴─────────┴────────┴──────────┴────────┴──────────┘

[🔗 View Full Dashboard in Langfuse]
```

## Testing Checklist

- [ ] Start Streamlit app
- [ ] Navigate to Monitor tab
- [ ] Verify Langfuse section appears
- [ ] Check metrics display correctly
- [ ] Generate a chat request
- [ ] Refresh the monitoring page
- [ ] Verify new trace appears in table
- [ ] Click "View Full Dashboard in Langfuse" link
- [ ] Try different time ranges
- [ ] Test with empty data (no traces)

## Troubleshooting

**Issue:** Langfuse section not showing
- **Fix:** Check `ENABLE_LANGFUSE=true` in .env

**Issue:** "Authentication failed" error
- **Fix:** Verify `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` in .env

**Issue:** No data showing
- **Fix:** Generate some chat requests first, then refresh

**Issue:** Timeout errors
- **Fix:** Check network connectivity to https://cloud.langfuse.com

## Documentation

- **Main Docs**: [MONITORING.md](MONITORING.md)
- **Code**: [pages/2_Monitor.py](pages/2_Monitor.py)
- **Langfuse Docs**: https://langfuse.com/docs/api

---

**Status:** ✅ Complete and ready to use!
