import streamlit as st
import pandas as pd
import os
import re
import requests

# =========================
# CONFIG
# =========================
DATA_PATH = "data/"
st.set_page_config(page_title="COO AI Analytics Bot", layout="wide")

st.title("🤖COO AI Analytics Bot")

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
            st.warning(f"Missing file: {file}")

    return data

data = load_data()

# =========================
# SIDEBAR CONTROLS
# =========================
st.sidebar.header("⚙️ Controls")

util_threshold = st.sidebar.slider("Utilisation Threshold", 0.0, 1.0, 0.6, 0.05)
kpi_threshold = st.sidebar.slider("KPI Threshold", 0.0, 1.0, 0.8, 0.05)
cost_threshold = st.sidebar.number_input("Cost Threshold", value=4000)

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

# =========================
# BUILD DATASET (FOR CORRELATION)
# =========================
def build_analysis_dataset():
    util = calculate_utilisation()
    kpi = calculate_kpi()
    cost = calculate_cost()

    df = util.merge(kpi, on="employee_id")
    df = df.merge(cost, on="employee_id")

    return df[["employee_id", "utilisation", "kpi", "total_cost"]]

# =========================
# CORRELATION
# =========================
def compute_correlation(df):
    return df.corr(numeric_only=True)

# =========================
# AI EXPLANATION
# =========================
def explain_with_ai(corr_df):
    api_key = st.secrets.get("OPENAI_API_KEY", None)

    if not api_key:
        return "⚠️ No AI key found. Add OPENAI_API_KEY in Streamlit secrets."

    prompt = f"""
You are a COO analytics assistant.

Explain this correlation matrix in business terms.

Focus on:
- Key relationships
- Risks
- Opportunities
- Actions

Correlation Matrix:
{corr_df.to_string()}
"""

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a COO advisor."},
                {"role": "user", "content": prompt}
            ]
        }
    )

    result = response.json()
    return result["choices"][0]["message"]["content"]

# =========================
# NLP PARSER
# =========================
def parse_question(q):
    q = q.lower()

    # correlation
    if "correlation" in q or "relationship" in q:
        return "correlation", None, None, None

    # metric
    if "util" in q:
        metric = "utilisation"
    elif "kpi" in q or "performance" in q:
        metric = "kpi"
    elif "cost" in q:
        metric = "cost"
    else:
        metric = None

    # direction
    if any(x in q for x in ["low", "below", "under", "worst", "bottom"]):
        direction = "below"
    elif any(x in q for x in ["high", "above", "over", "top", "best"]):
        direction = "above"
    else:
        direction = "above"

    # threshold
    match = re.search(r"(\d*\.?\d+)", q)
    value = float(match.group(1)) if match else None

    # top N
    match_n = re.search(r"(top|bottom)\s*(\d+)", q)
    top_n = int(match_n.group(2)) if match_n else None

    return metric, direction, value, top_n

# =========================
# METRIC ENGINE
# =========================
def get_metric_df(metric):
    if metric == "utilisation":
        return calculate_utilisation(), "utilisation"
    elif metric == "kpi":
        return calculate_kpi(), "kpi"
    elif metric == "cost":
        return calculate_cost(), "total_cost"
    return pd.DataFrame(), None

def apply_condition(df, column, direction, value):
    if value is None:
        return df

    if direction == "below":
        return df[df[column] < value]
    else:
        return df[df[column] > value]

def apply_top_n(df, column, direction, n):
    if n is None:
        return df

    return df.sort_values(column, ascending=(direction == "below")).head(n)

# =========================
# SIMPLE INSIGHT ENGINE
# =========================
def generate_insight(df, metric, direction):
    if df.empty:
        return "No significant findings."

    if direction == "above":
        return f"These are high {metric} cases. Review for strong performance or cost concentration."
    else:
        return f"These are low {metric} cases. Indicates potential underperformance or inefficiency."

# =========================
# UI INPUT
# =========================
question = st.text_input("💬 Ask a question")

if question:
    metric, direction, value, top_n = parse_question(question)

    # ===== CORRELATION =====
    if metric == "correlation":
        df = build_analysis_dataset()
        corr = compute_correlation(df)

        st.subheader("↗️Correlation Matrix")
        st.dataframe(corr)

        st.subheader("🧠 AI Insight")
        st.write(explain_with_ai(corr))

    # ===== METRIC ANALYSIS =====
    elif metric:
        df, column = get_metric_df(metric)

        # fallback thresholds
        if value is None:
            if metric == "utilisation":
                value = util_threshold
            elif metric == "kpi":
                value = kpi_threshold
            elif metric == "cost":
                value = cost_threshold

        result = apply_condition(df, column, direction, value)
        result = apply_top_n(result, column, direction, top_n)

        st.subheader("📌 Results")
        st.dataframe(result)

        st.subheader("🧠 Insight")
        st.write(generate_insight(result, metric, direction))

    else:
        st.warning("Try: utilisation, KPI, cost, or correlation")

# =========================
# TOP ISSUES (NO HIGHLIGHT)
# =========================
st.subheader("🚨 Top Issues")

low_util = calculate_utilisation()
low_util = low_util[low_util["utilisation"] < util_threshold]

low_kpi = calculate_kpi()
low_kpi = low_kpi[low_kpi["kpi"] < kpi_threshold]

high_cost = calculate_cost()
high_cost = high_cost[high_cost["total_cost"] > cost_threshold]

issues = pd.concat([
    low_util.assign(issue="Low Utilisation"),
    low_kpi.assign(issue="Low KPI"),
    high_cost.assign(issue="High Cost")
])

st.dataframe(issues.head(10))
