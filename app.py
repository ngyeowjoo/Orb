import streamlit as st
import pandas as pd
import os
import re
import requests
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# =========================
# CONFIG
# =========================
DATA_PATH = "data/"

st.set_page_config(
    page_title="COO AI Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "COO AI Analytics Bot — Powered by Claude"}
)

# =========================
# CUSTOM CSS — Dark Executive Theme
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@400;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
}

.stApp {
    background: #0a0c10;
    color: #e8eaf0;
}

section[data-testid="stSidebar"] {
    background: #0f1217;
    border-right: 1px solid #1e2330;
}

.stTextInput > div > div > input {
    background: #111520;
    border: 1px solid #2a3050;
    border-radius: 8px;
    color: #e8eaf0;
    font-family: 'DM Mono', monospace;
    font-size: 0.9rem;
    padding: 12px 16px;
}

.stTextInput > div > div > input:focus {
    border-color: #4f6fff;
    box-shadow: 0 0 0 2px rgba(79,111,255,0.15);
}

.stButton > button {
    background: #4f6fff;
    color: white;
    border: none;
    border-radius: 8px;
    font-family: 'Syne', sans-serif;
    font-weight: 600;
    padding: 8px 20px;
    transition: all 0.2s;
}

.stButton > button:hover {
    background: #6b85ff;
    transform: translateY(-1px);
}

.metric-card {
    background: #111520;
    border: 1px solid #1e2330;
    border-radius: 12px;
    padding: 20px 24px;
    margin: 4px 0;
}

.metric-value {
    font-family: 'DM Mono', monospace;
    font-size: 2rem;
    font-weight: 500;
    color: #4f6fff;
    line-height: 1.1;
}

.metric-label {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #6b7280;
    margin-top: 4px;
}

.metric-delta {
    font-family: 'DM Mono', monospace;
    font-size: 0.8rem;
    margin-top: 6px;
}

.delta-up { color: #34d399; }
.delta-down { color: #f87171; }

.issue-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

.badge-util { background: #1e3a5f; color: #60a5fa; }
.badge-kpi  { background: #1e3a2a; color: #4ade80; }
.badge-cost { background: #3a1e1e; color: #f87171; }

.ai-box {
    background: linear-gradient(135deg, #111a35 0%, #0f1520 100%);
    border: 1px solid #2a3a6a;
    border-left: 3px solid #4f6fff;
    border-radius: 10px;
    padding: 20px 24px;
    font-size: 0.92rem;
    line-height: 1.7;
    color: #c8d0e8;
    margin-top: 8px;
}

.section-header {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #4f6fff;
    margin-bottom: 12px;
    margin-top: 24px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.section-header::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #1e2330;
}

div[data-testid="stDataFrame"] {
    border: 1px solid #1e2330;
    border-radius: 10px;
    overflow: hidden;
}

.stSlider > div > div {
    color: #4f6fff;
}

h1 {
    font-size: 1.6rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.02em !important;
    color: #e8eaf0 !important;
}

.stSpinner > div {
    border-top-color: #4f6fff !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
col_title, col_status = st.columns([3, 1])
with col_title:
    st.markdown("# 🧠 COO AI Analytics")
    st.markdown('<p style="color:#6b7280;font-size:0.85rem;margin-top:-8px;">Workforce Intelligence · Powered by Claude</p>', unsafe_allow_html=True)

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data():
    data = {}
    files = [
        "dim_employee.xlsx",
        "fact_payroll.xlsx",
        "fact_attendance.xlsx",
        "fact_employee_kpi.xlsx"
    ]
    for file in files:
        path = os.path.join(DATA_PATH, file)
        if os.path.exists(path):
            data[file] = pd.read_excel(path)
        else:
            st.sidebar.warning(f"⚠ Missing: {file}")
    return data

data = load_data()

# =========================
# SIDEBAR
# =========================
st.sidebar.markdown("### ⚙ Thresholds")
util_threshold = st.sidebar.slider("Utilisation", 0.0, 1.0, 0.6, 0.05, format="%.2f")
kpi_threshold  = st.sidebar.slider("KPI Score",   0.0, 1.0, 0.8, 0.05, format="%.2f")
cost_threshold = st.sidebar.number_input("Cost Ceiling ($)", value=4000, step=100)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🤖 AI Settings")
ai_detail = st.sidebar.selectbox("Response depth", ["Concise", "Detailed", "Strategic"])
show_chart_insight = st.sidebar.toggle("Auto chart insights", value=True)

# =========================
# SEMANTIC LAYER
# =========================
def calculate_utilisation():
    df = data["fact_attendance.xlsx"].copy()
    df["utilisation"] = df["productive_hours"] / df["total_hours"]
    return df

def calculate_kpi():
    df = data["fact_employee_kpi.xlsx"].copy()
    df["kpi"] = df["actual"] / df["target"]
    return df

def calculate_cost():
    df = data["fact_payroll.xlsx"].copy()
    df["total_cost"] = df["salary"] + df["incentive"] + df["bonus"]
    return df

def build_analysis_dataset():
    util = calculate_utilisation()
    kpi  = calculate_kpi()
    cost = calculate_cost()
    df   = util.merge(kpi, on="employee_id").merge(cost, on="employee_id")

    # Enrich with employee dimension if available
    if "dim_employee.xlsx" in data:
        emp = data["dim_employee.xlsx"]
        df = df.merge(emp, on="employee_id", how="left")

    return df

# =========================
# SMARTER NLP PARSER
# =========================
def parse_question(q: str) -> dict:
    """
    Returns a structured intent dict:
      intent: correlation | trend | distribution | outliers | compare | metric_filter | unknown
      metric: utilisation | kpi | cost | None
      direction: above | below | None
      value: float | None
      top_n: int | None
      department: str | None
      compare_metrics: list | None
    """
    raw = q
    q = q.lower()

    intent = "metric_filter"

    # Intent detection
    if any(x in q for x in ["correlation", "relationship", "correlate", "linked"]):
        intent = "correlation"
    elif any(x in q for x in ["trend", "over time", "monthly", "week", "quarter", "history"]):
        intent = "trend"
    elif any(x in q for x in ["distribution", "spread", "histogram", "range", "variance"]):
        intent = "distribution"
    elif any(x in q for x in ["outlier", "anomaly", "unusual", "flag", "alert"]):
        intent = "outliers"
    elif any(x in q for x in ["compare", "vs", "versus", "difference between", "breakdown by", "by department"]):
        intent = "compare"

    # Metric extraction
    if any(x in q for x in ["util", "productive", "hours"]):
        metric = "utilisation"
    elif any(x in q for x in ["kpi", "performance", "target", "actual", "score"]):
        metric = "kpi"
    elif any(x in q for x in ["cost", "salary", "payroll", "spend", "pay", "bonus"]):
        metric = "cost"
    else:
        metric = None

    # Multiple metrics for comparison
    compare_metrics = []
    for m, keywords in [("utilisation", ["util"]), ("kpi", ["kpi", "performance"]), ("cost", ["cost", "salary"])]:
        if any(k in q for k in keywords):
            compare_metrics.append(m)

    # Direction
    if any(x in q for x in ["low", "below", "under", "worst", "bottom", "least", "poor"]):
        direction = "below"
    elif any(x in q for x in ["high", "above", "over", "top", "best", "most", "exceed"]):
        direction = "above"
    else:
        direction = "above"

    # Numeric threshold
    match = re.search(r"(\d*\.?\d+)", q)
    value = float(match.group(1)) if match else None

    # Top N
    match_n = re.search(r"(top|bottom)\s*(\d+)", q)
    top_n = int(match_n.group(2)) if match_n else None

    # Department filter (basic)
    dept_match = re.search(r"(?:department|dept|team)\s+['\"]?([a-z\s]+)['\"]?", q)
    department = dept_match.group(1).strip().title() if dept_match else None

    return {
        "intent": intent,
        "metric": metric,
        "direction": direction,
        "value": value,
        "top_n": top_n,
        "department": department,
        "compare_metrics": compare_metrics if len(compare_metrics) > 1 else None,
        "raw": raw
    }

# =========================
# METRIC ENGINE
# =========================
def get_metric_df(metric):
    if metric == "utilisation": return calculate_utilisation(), "utilisation"
    elif metric == "kpi":       return calculate_kpi(), "kpi"
    elif metric == "cost":      return calculate_cost(), "total_cost"
    return pd.DataFrame(), None

def apply_condition(df, column, direction, value):
    if value is None: return df
    return df[df[column] < value] if direction == "below" else df[df[column] > value]

def apply_top_n(df, column, direction, n):
    if n is None: return df
    return df.sort_values(column, ascending=(direction == "below")).head(n)

# =========================
# CHARTS
# =========================
CHART_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Mono", color="#9ca3af", size=11),
    margin=dict(l=0, r=0, t=30, b=0),
    colorway=["#4f6fff", "#34d399", "#f87171", "#fbbf24", "#a78bfa"],
)

def chart_distribution(df, column, title):
    fig = px.histogram(
        df, x=column, nbins=20,
        title=title,
        color_discrete_sequence=["#4f6fff"]
    )
    fig.update_layout(**CHART_THEME)
    fig.update_traces(marker_line_width=0, opacity=0.85)
    fig.update_xaxes(showgrid=False, zeroline=False, color="#6b7280")
    fig.update_yaxes(showgrid=True, gridcolor="#1e2330", zeroline=False, color="#6b7280")
    return fig

def chart_scatter(df, x, y, title, color=None):
    fig = px.scatter(
        df, x=x, y=y, title=title,
        color=color,
        trendline="ols",
        opacity=0.75,
        color_discrete_sequence=["#4f6fff"]
    )
    fig.update_layout(**CHART_THEME)
    fig.update_xaxes(showgrid=True, gridcolor="#1e2330", color="#6b7280")
    fig.update_yaxes(showgrid=True, gridcolor="#1e2330", color="#6b7280")
    return fig

def chart_bar(df, x, y, title, color_col=None, horizontal=False):
    if horizontal:
        fig = px.bar(df, x=y, y=x, orientation="h", title=title,
                     color=color_col, color_discrete_sequence=["#4f6fff", "#34d399", "#f87171"])
    else:
        fig = px.bar(df, x=x, y=y, title=title,
                     color=color_col, color_discrete_sequence=["#4f6fff", "#34d399", "#f87171"])
    fig.update_layout(**CHART_THEME)
    fig.update_xaxes(showgrid=False, color="#6b7280")
    fig.update_yaxes(showgrid=True, gridcolor="#1e2330", color="#6b7280")
    fig.update_traces(marker_line_width=0)
    return fig

def chart_heatmap(corr_df):
    fig = go.Figure(data=go.Heatmap(
        z=corr_df.values,
        x=corr_df.columns,
        y=corr_df.index,
        colorscale=[
            [0.0, "#f87171"], [0.5, "#111520"], [1.0, "#4f6fff"]
        ],
        zmid=0,
        text=corr_df.round(2).values,
        texttemplate="%{text}",
        hovertemplate="%{y} × %{x}: %{z:.3f}<extra></extra>"
    ))
    fig.update_layout(title="Correlation Heatmap", **CHART_THEME)
    return fig

def chart_outlier_box(df, column, title):
    fig = px.box(
        df, y=column, title=title,
        points="all",
        color_discrete_sequence=["#4f6fff"]
    )
    fig.update_layout(**CHART_THEME)
    fig.update_xaxes(showgrid=False, color="#6b7280")
    fig.update_yaxes(showgrid=True, gridcolor="#1e2330", color="#6b7280")
    return fig

# =========================
# CLAUDE AI ENGINE
# =========================
def call_claude(system_prompt: str, user_prompt: str) -> str:
    api_key = st.secrets.get("ANTHROPIC_API_KEY", None)
    if not api_key:
        return "⚠ Add `ANTHROPIC_API_KEY` to Streamlit secrets to enable AI insights."

    depth_map = {
        "Concise":   "Be concise. Max 3 bullet points per section.",
        "Detailed":  "Provide thorough analysis with specific data references.",
        "Strategic": "Focus on strategic implications, risks, and board-level recommendations."
    }
    depth_instruction = depth_map.get(ai_detail, "")

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1000,
            "system": system_prompt + f"\n\n{depth_instruction}",
            "messages": [{"role": "user", "content": user_prompt}]
        }
    )

    result = response.json()
    if "content" in result and result["content"]:
        return result["content"][0]["text"]
    elif "error" in result:
        return f"⚠ Claude API error: {result['error'].get('message', 'Unknown error')}"
    return "⚠ Unexpected API response."


def explain_correlation(corr_df):
    system = """You are a COO analytics advisor. Analyse workforce data correlations.
Format your response with these sections:
**Key Relationships** | **Risk Signals** | **Opportunities** | **Recommended Actions**
Use bullet points within each section."""

    user = f"""Explain this workforce correlation matrix in business terms:

{corr_df.round(3).to_string()}

Focus on actionable COO-level insights."""
    return call_claude(system, user)


def explain_metric_results(df, metric, direction, value, intent):
    system = """You are a COO workforce analytics advisor. Provide sharp, actionable insights.
Be specific. Reference numbers when available. Format with **Observation**, **Risk**, **Action** headers."""

    sample = df.head(10).to_string() if not df.empty else "No data matched the filter."
    user = f"""Workforce data analysis result:
- Metric: {metric}
- Filter: {direction} {value if value else 'threshold'}
- Intent: {intent}
- Records found: {len(df)}
- Sample data:
{sample}

Provide COO-level insight."""
    return call_claude(system, user)


def explain_outliers(df, column):
    system = "You are a COO analytics advisor. Identify and explain workforce anomalies concisely."
    stats = df[column].describe().to_string()
    user = f"""Outlier analysis for {column}:
Stats: {stats}
High outliers (>95th pct): {df[df[column] > df[column].quantile(0.95)]['employee_id'].tolist()[:5]}
Low outliers (<5th pct): {df[df[column] < df[column].quantile(0.05)]['employee_id'].tolist()[:5]}

What should the COO investigate?"""
    return call_claude(system, user)

# =========================
# KPI SUMMARY CARDS
# =========================
def render_kpi_cards():
    try:
        util_df  = calculate_utilisation()
        kpi_df   = calculate_kpi()
        cost_df  = calculate_cost()

        avg_util = util_df["utilisation"].mean()
        avg_kpi  = kpi_df["kpi"].mean()
        avg_cost = cost_df["total_cost"].mean()
        low_util_count = (util_df["utilisation"] < util_threshold).sum()
        low_kpi_count  = (kpi_df["kpi"] < kpi_threshold).sum()
        high_cost_count = (cost_df["total_cost"] > cost_threshold).sum()

        c1, c2, c3, c4, c5, c6 = st.columns(6)
        cards = [
            (c1, f"{avg_util:.0%}", "Avg Utilisation", avg_util >= util_threshold),
            (c2, f"{avg_kpi:.0%}", "Avg KPI Score",  avg_kpi >= kpi_threshold),
            (c3, f"${avg_cost:,.0f}", "Avg Total Cost", avg_cost <= cost_threshold),
            (c4, str(low_util_count),  "Low Util Flags",  low_util_count == 0),
            (c5, str(low_kpi_count),   "Low KPI Flags",   low_kpi_count == 0),
            (c6, str(high_cost_count), "High Cost Flags", high_cost_count == 0),
        ]
        for col, val, label, ok in cards:
            color = "#34d399" if ok else "#f87171"
            with col:
                st.markdown(f"""
                <div class="metric-card">
                  <div class="metric-value" style="color:{color}">{val}</div>
                  <div class="metric-label">{label}</div>
                </div>""", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Cards unavailable: {e}")

# =========================
# QUESTION HANDLER
# =========================
def handle_question(question: str):
    parsed = parse_question(question)
    intent = parsed["intent"]
    metric = parsed["metric"]
    direction = parsed["direction"]
    value = parsed["value"]
    top_n = parsed["top_n"]

    # ── CORRELATION ──────────────────────────────────────
    if intent == "correlation":
        df = build_analysis_dataset()
        numeric_cols = ["utilisation", "kpi", "total_cost"]
        corr = df[numeric_cols].corr()

        c1, c2 = st.columns([1.2, 1])
        with c1:
            st.markdown('<div class="section-header">↗ Correlation Heatmap</div>', unsafe_allow_html=True)
            st.plotly_chart(chart_heatmap(corr), use_container_width=True)

        with c2:
            st.markdown('<div class="section-header">🔗 Scatter: Utilisation vs KPI</div>', unsafe_allow_html=True)
            st.plotly_chart(chart_scatter(df, "utilisation", "kpi", ""), use_container_width=True)

        st.markdown('<div class="section-header">🧠 Claude Insight</div>', unsafe_allow_html=True)
        with st.spinner("Analysing correlations..."):
            insight = explain_correlation(corr)
        st.markdown(f'<div class="ai-box">{insight}</div>', unsafe_allow_html=True)

    # ── DISTRIBUTION ─────────────────────────────────────
    elif intent == "distribution":
        if not metric:
            metric = "utilisation"
        df, column = get_metric_df(metric)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="section-header">📊 {metric.title()} Distribution</div>', unsafe_allow_html=True)
            st.plotly_chart(chart_distribution(df, column, ""), use_container_width=True)
        with c2:
            st.markdown(f'<div class="section-header">📦 Box Plot</div>', unsafe_allow_html=True)
            st.plotly_chart(chart_outlier_box(df, column, ""), use_container_width=True)

        if show_chart_insight:
            with st.spinner("Generating insight..."):
                insight = explain_metric_results(df, metric, direction, value, intent)
            st.markdown(f'<div class="ai-box">{insight}</div>', unsafe_allow_html=True)

    # ── OUTLIERS ─────────────────────────────────────────
    elif intent == "outliers":
        if not metric:
            metric = "utilisation"
        df, column = get_metric_df(metric)

        q95 = df[column].quantile(0.95)
        q05 = df[column].quantile(0.05)
        outliers = df[(df[column] > q95) | (df[column] < q05)]

        st.markdown(f'<div class="section-header">⚠ {metric.title()} Outliers ({len(outliers)} flagged)</div>', unsafe_allow_html=True)

        c1, c2 = st.columns([1, 1.5])
        with c1:
            st.dataframe(outliers.head(20), use_container_width=True)
        with c2:
            st.plotly_chart(chart_outlier_box(df, column, f"{metric.title()} with outlier bounds"), use_container_width=True)

        with st.spinner("Analysing anomalies..."):
            insight = explain_outliers(df, column)
        st.markdown(f'<div class="ai-box">{insight}</div>', unsafe_allow_html=True)

    # ── COMPARE ──────────────────────────────────────────
    elif intent == "compare" or parsed["compare_metrics"]:
        df = build_analysis_dataset()

        if "department" in df.columns:
            grp = df.groupby("department")[["utilisation", "kpi", "total_cost"]].mean().reset_index()
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(chart_bar(grp, "department", "utilisation", "Utilisation by Dept"), use_container_width=True)
                st.plotly_chart(chart_bar(grp, "department", "total_cost", "Cost by Dept"), use_container_width=True)
            with c2:
                st.plotly_chart(chart_bar(grp, "department", "kpi", "KPI by Dept"), use_container_width=True)
                st.dataframe(grp.round(3), use_container_width=True)
        else:
            st.info("Department breakdown requires `dim_employee.xlsx` with a `department` column.")
            df2 = df[["employee_id", "utilisation", "kpi", "total_cost"]].head(20)
            st.dataframe(df2, use_container_width=True)

        if show_chart_insight:
            with st.spinner("Generating comparison insight..."):
                insight = explain_metric_results(df, "all metrics", "compare", None, intent)
            st.markdown(f'<div class="ai-box">{insight}</div>', unsafe_allow_html=True)

    # ── METRIC FILTER (default) ───────────────────────────
    elif metric:
        df, column = get_metric_df(metric)

        # Apply threshold fallback
        if value is None:
            value = {
                "utilisation": util_threshold,
                "kpi": kpi_threshold,
                "cost": cost_threshold
            }.get(metric)

        result = apply_condition(df, column, direction, value)
        result = apply_top_n(result, column, direction, top_n)

        label = f"{direction.upper()} {value} — {len(result)} records"
        st.markdown(f'<div class="section-header">📋 {metric.title()} Results · {label}</div>', unsafe_allow_html=True)

        c1, c2 = st.columns([1.5, 1])
        with c1:
            st.dataframe(result, use_container_width=True)
        with c2:
            st.plotly_chart(chart_distribution(result, column, f"{metric.title()} distribution"), use_container_width=True)

        if show_chart_insight:
            with st.spinner("Generating insight..."):
                insight = explain_metric_results(result, metric, direction, value, intent)
            st.markdown(f'<div class="ai-box">{insight}</div>', unsafe_allow_html=True)

    else:
        st.warning("🤔 Try: *utilisation below 0.6*, *KPI outliers*, *correlation*, *cost distribution*, *compare by department*")

# =========================
# TOP ISSUES PANEL
# =========================
def render_issues():
    try:
        low_util  = calculate_utilisation()
        low_util  = low_util[low_util["utilisation"] < util_threshold].assign(issue="Low Utilisation")
        low_kpi   = calculate_kpi()
        low_kpi   = low_kpi[low_kpi["kpi"] < kpi_threshold].assign(issue="Low KPI")
        high_cost = calculate_cost()
        high_cost = high_cost[high_cost["total_cost"] > cost_threshold].assign(issue="High Cost")

        issues = pd.concat([low_util, low_kpi, high_cost]).sort_values("employee_id")

        c1, c2 = st.columns([2, 1])
        with c1:
            st.dataframe(issues.head(15), use_container_width=True)
        with c2:
            counts = issues["issue"].value_counts().reset_index()
            counts.columns = ["Issue", "Count"]
            fig = px.pie(counts, names="Issue", values="Count",
                         color_discrete_sequence=["#4f6fff", "#34d399", "#f87171"],
                         hole=0.55)
            fig.update_layout(**CHART_THEME, showlegend=True)
            fig.update_traces(textfont_size=11)
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Issues panel unavailable: {e}")

# =========================
# MAIN LAYOUT
# =========================

# KPI Summary
st.markdown('<div class="section-header">📊 Workforce Summary</div>', unsafe_allow_html=True)
render_kpi_cards()

# Query Input
st.markdown('<div class="section-header">💬 Ask the Data</div>', unsafe_allow_html=True)

example_queries = [
    "Show utilisation below 0.6",
    "KPI outliers",
    "Correlation between all metrics",
    "Cost distribution",
    "Top 10 high cost employees",
    "Compare by department"
]
selected_example = st.selectbox("Quick queries →", [""] + example_queries, label_visibility="collapsed")
question = st.text_input("Or type your own question:", value=selected_example, placeholder="e.g. 'Show low KPI employees' or 'correlation'")

if question:
    handle_question(question)

# Top Issues
st.markdown('<div class="section-header">🚨 Active Issues</div>', unsafe_allow_html=True)
render_issues()
