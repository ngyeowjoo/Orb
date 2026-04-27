import streamlit as st
import pandas as pd
import os

# =========================
# CONFIG
# =========================
DATA_PATH = "./data"  # folder where excel files are stored

# =========================
# LOAD DATA
# =========================
@st.cache_data



def load_data():
    data = {}
    files = [
        "dim_employee.xlsx",
        "dim_project.xlsx",
        "bridge_employee_project.xlsx",
        "fact_payroll.xlsx",
        "fact_attendance.xlsx",
        "fact_project_financials.xlsx",
        "fact_employee_kpi.xlsx",
        "fact_project_kpi.xlsx"
    ]

    for file in files:
        path = os.path.join(DATA_PATH, file)
        if os.path.exists(path):
            data[file] = pd.read_excel(path)
    return data

#data = load_data()
#st.write("Payroll columns:", data["fact_payroll.xlsx"].columns)
#st.write("KPI columns:", data["fact_employee_kpi.xlsx"].columns)

# =========================
# SEMANTIC LAYER (METRICS)
# =========================
def calculate_project_profit(df_project_fin):
    df = df_project_fin.copy()
    df["net_profit"] = df["revenue"] - df["penalties"]
    return df


def calculate_employee_cost(df_payroll):
    df = df_payroll.copy()
    df["total_cost"] = (
        df["salary"] + df["incentive"] + df["bonus"]
    )
    return df


def calculate_utilisation(df_attendance):
    df = df_attendance.copy()
    df["utilisation"] = df["productive_hours"] / df["total_hours"]
    return df

# =========================
# BUSINESS LOGIC
# =========================
def get_loss_making_projects(data):
    df = calculate_project_profit(data["fact_project_financials.xlsx"])
    return df[df["net_profit"] < 0]

def get_profit_making_projects(data):
    df = calculate_project_profit(data["fact_project_financials.xlsx"])
    return df[df["net_profit"] > 0]

def get_low_utilisation_employees(data):
    df = calculate_utilisation(data["fact_attendance.xlsx"])
    return df[df["utilisation"] < 0.6]

def get_high_utilisation_employees(data):
    df = calculate_utilisation(data["fact_attendance.xlsx"])
    return df[df["utilisation"] > 0.8]

def get_high_cost_low_performance(data):
    payroll = calculate_employee_cost(data["fact_payroll.xlsx"])
    kpi = data["fact_employee_kpi.xlsx"]

    df = payroll.merge(kpi, on="employee_id")
    df["achievement"] = df["actual"] / df["target"]

    return df[(df["total_cost"] > df["total_cost"].mean()) & (df["achievement"] < 0.8)]

# =========================
# SIMPLE AI (RULE-BASED EXPLANATION)
# =========================
def generate_explanation(question, df):
    if df.empty:
        return "No significant issues found based on current criteria."

    if "profit" in question:
        return "These projects are profit-making."

    if "loss" in question:
        return "These projects are loss-making due to low revenue and/or high penalties. Review cost structure and performance KPIs."

    if "low utilisation" in question:
        return "These employees have low utilisation. Consider workload redistribution or role alignment."

    if "cost" in question or "performance" in question:
        return "These employees have high cost but low KPI achievement. Consider performance management or reassignment."

    return "Analysis completed. Review the data for insights."

# =========================
# STREAMLIT UI
# =========================
st.set_page_config(page_title="COO AI Analytics Bot", layout="wide")

st.title("📊 COO AI Analytics Bot")
st.write("Ask business questions and get insights instantly.")

# Load data
data = load_data()

# Input
question = st.text_input("Ask a question (e.g. 'Which projects are loss-making?')")

# Processing
if question:
    question_lower = question.lower()

    if "loss" in question_lower:
        result = get_loss_making_projects(data)

    elif "profit" in question_lower:
        result = get_profit_making_projects(data)

    elif "low utilisation" in question_lower:
        result = get_low_utilisation_employees(data)

    elif "high utilisation" in question_lower:
        result = get_high_utilisation_employees(data)

    elif "cost" in question_lower or "performance" in question_lower:
        result = get_high_cost_low_performance(data)

    else:
        st.warning("Question not recognized yet. Try keywords: loss, profit, utilisation, cost, performance.")
        result = pd.DataFrame()

    # Output
    if not result.empty:
        st.subheader("📌 Results")
        st.dataframe(result)

        st.subheader("🧠 Insight")
        explanation = generate_explanation(question_lower, result)
        st.write(explanation)
    else:
        st.info("No results found.")

# Sidebar examples
st.sidebar.title("Example Questions")
st.sidebar.write("- Which projects are loss/profit making?")
st.sidebar.write("- Which employees have low utilisation?")
st.sidebar.write("- Who are high cost but low performance employees?")

# =========================
# RUN INSTRUCTIONS
# =========================
# 1. Install: pip install streamlit pandas openpyxl
# 2. Place all Excel files in same folder
# 3. Run: streamlit run app.py
