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

st.title("📊 COO AI Analytics Bot")

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
# BUILD DATASET
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
# AI EXPLANATION (OpenAI)
# =========================
def explain_with_ai(corr_df):
    api_key = st.secrets.get("OPENAI_API_KEY", None)

    if not api_key:
        return "⚠️ No AI key found. Add OPENAI_API_KEY in Streamlit secrets."

    prompt = f"""
You are a COO analytics assistant.

Explain the following correlation matrix in business terms.

Focus on:
- Key relationships
- Risks
- Opportunities
- Actionable recommendations

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

    if "correlation" in q or "relationship" in q:
        return "correlation"

    if "util" in q:
        return "utilisation"
    elif "kpi" in q or "performance" in q:
        return "kpi"
    elif "cost" in q:
        return "cost"

    return None

# =========================
# HIGHLIGHT FUNCTION
# =========================
def highlight_issues(row):
    color = ""

    if row["issue"] == "Low Utilisation":
        color = "background-color: #ffcccc"
    elif row["issue"] == "Low KPI":
        color = "background-color: #fff3cd"
    elif row["issue"] == "High Cost":
        color = "background-color: #f8d7da"

    return [color]*len(row)

# =========================
# TOP ISSUES
# =========================
def get_top_issues():
    util = calculate_utilisation()
    util = util[util["utilisation"] < util_threshold]

    kpi = calculate_kpi()
    kpi = kpi[kpi["kpi"] < kpi_threshold]

    cost = calculate_cost()
    cost = cost[cost["total_cost"] > cost_threshold]

    issues = pd.concat([
        util.assign(issue="Low Utilisation"),
        kpi.assign(issue="Low KPI"),
        cost.assign(issue="High Cost")
    ])

    return issues.head(10)

# =========================
# UI INPUT
# =========================
question = st.text_input("💬 Ask a question")

if question:
    intent = parse_question(question)

    if intent == "correlation":
        df = build_analysis_dataset()
        corr = compute_correlation(df)

        st.subheader("📊 Correlation Matrix")
        st.dataframe(corr)

        st.subheader("🧠 AI Insight")
        st.write(explain_with_ai(corr))

    else:
        st.info("Try asking about correlation, utilisation, KPI or cost.")

# =========================
# TOP ISSUES DISPLAY
# =========================
#st.subheader("🚨 Top Issues")

#issues_df = get_top_issues()

#st.write(
#    issues_df.style.apply(highlight_issues, axis=1)
#)
