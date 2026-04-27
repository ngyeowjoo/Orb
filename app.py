import streamlit as st
import pandas as pd
import os
import re

# =========================
# CONFIG
# =========================
DATA_PATH = "data/"
st.set_page_config(page_title="COO AI Analytics Bot", layout="wide")

st.title("📊 COO AI Analytics Bot")
st.write("Ask smart business questions (e.g. 'top performers', 'low utilisation below 0.5')")

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data():
    data = {}
    files = [
        "dim_employee.xlsx",
        "dim_project.xlsx",
        "fact_payroll.xlsx",
        "fact_attendance.xlsx",
        "fact_employee_kpi.xlsx",
        "fact_project_financials.xlsx"
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
cost_threshold = st.sidebar.number_input("High Cost Threshold", value=4000)

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
# NLP PARSER
# =========================
def parse_question(q):
    q = q.lower()

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
    if any(x in q for x in ["low", "below", "under", "worst"]):
        direction = "below"
    elif any(x in q for x in ["high", "above", "over", "top", "best"]):
        direction = "above"
    else:
        direction = "above"

    # number
    match = re.search(r"(\d*\.?\d+)", q)
    value = float(match.group(1)) if match else None

    # top/bottom N
    top_n = None
    match_n = re.search(r"(top|bottom)\s*(\d+)", q)
    if match_n:
        top_n = int(match_n.group(2))

    return metric, direction, value, top_n

# =========================
# FILTER ENGINE
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
# INSIGHT ENGINE
# =========================
def generate_insight(df, metric, direction):
    if df.empty:
        return "No significant findings."

    avg = df.mean(numeric_only=True).mean()

    if direction == "above":
        return f"These are high {metric} cases. Indicates strong performance or potential cost concentration."
    else:
        return f"These are low {metric} cases. Indicates underperformance or inefficiency."

# =========================
# UI INPUT
# =========================
question = st.text_input("💬 Ask a question")

if question:
    metric, direction, value, top_n = parse_question(question)

    if metric is None:
        st.warning("Try mentioning utilisation, KPI, or cost.")
    else:
        df, column = get_metric_df(metric)

        # fallback to slider
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

# =========================
# CHARTS
# =========================
st.subheader("📊 Utilisation Overview")
util_df = calculate_utilisation()
st.bar_chart(util_df.set_index("employee_id")["utilisation"])

st.subheader("📊 KPI Overview")
kpi_df = calculate_kpi()
st.bar_chart(kpi_df.set_index("employee_id")["kpi"])

# =========================
# TOP ISSUES
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
