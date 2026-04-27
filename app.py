import streamlit as st
import pandas as pd
import numpy as np
import os, re, requests
import plotly.express as px
import plotly.graph_objects as go

# ═══════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════
DATA_PATH = "data2/"

st.set_page_config(
    page_title="COO AI Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "COO AI Analytics — Powered by Claude"}
)

# ═══════════════════════════════════════════════
# CSS — Light Amber Theme
# ═══════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Syne', sans-serif; }
.stApp { background: #fdfaf4; color: #1a1509; }
section[data-testid="stSidebar"] { background: #fff8e8; border-right: 1px solid #f0d88a; }
section[data-testid="stSidebar"] * { color: #3a2e0a !important; }
.stTextInput > div > div > input {
    background: #fff; border: 1.5px solid #f0c842; border-radius: 8px;
    color: #1a1509; font-family:'DM Mono',monospace; font-size:0.9rem; padding:12px 16px;
}
.stTextInput > div > div > input:focus { border-color: #F9A602; box-shadow: 0 0 0 3px rgba(249,166,2,.18); }
.stTextInput > div > div > input::placeholder { color: #b89040; }
.stButton > button {
    background: #F9A602; color: #1a1509; border: none; border-radius: 8px;
    font-family:'Syne',sans-serif; font-weight:700; padding:8px 20px; transition:all .2s;
}
.stButton > button:hover { background: #e09500; transform:translateY(-1px); box-shadow:0 4px 12px rgba(249,166,2,.3); }
.metric-card {
    background: #fff; border: 1.5px solid #f0d88a; border-radius: 12px;
    padding: 18px 22px; margin: 4px 0; box-shadow: 0 2px 8px rgba(249,166,2,.08);
}
.metric-value { font-family:'DM Mono',monospace; font-size:1.8rem; font-weight:500; color:#c97f00; line-height:1.1; }
.metric-label { font-size:0.72rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; color:#9a7d30; margin-top:4px; }
.ai-box {
    background: linear-gradient(135deg,#fffbef 0%,#fff8e1 100%);
    border: 1.5px solid #f0d07a; border-left: 4px solid #F9A602;
    border-radius: 10px; padding: 20px 24px;
    font-size: 0.92rem; line-height: 1.75; color: #3a2e0a;
    margin-top: 8px; box-shadow: 0 2px 10px rgba(249,166,2,.07);
}
.section-header {
    font-size:0.7rem; font-weight:700; letter-spacing:.15em; text-transform:uppercase;
    color:#c97f00; margin-bottom:12px; margin-top:24px; display:flex; align-items:center; gap:8px;
}
.section-header::after { content:''; flex:1; height:1px; background:#f0d88a; }
div[data-testid="stDataFrame"] { border:1.5px solid #f0d88a; border-radius:10px; overflow:hidden; }
h1 { font-size:1.6rem!important; font-weight:800!important; letter-spacing:-.02em!important; color:#1a1509!important; }
h3 { color:#5a4510!important; font-size:1rem!important; margin-top:20px!important; }
.stSpinner > div { border-top-color:#F9A602!important; }
.stSelectbox > div > div { background:#fff; border:1.5px solid #f0c842; border-radius:8px; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════
# COLOUR PALETTE — semantic
# ═══════════════════════════════════════════════
C_AMBER   = "#F9A602"
C_GOOD    = "#16a34a"    # green = good only
C_WARN    = "#ea580c"    # orange-red = issues/warnings
C_BAD     = "#dc2626"    # red = critical
C_NEUTRAL = "#94a3b8"
C_GRID    = "#f0d88a"
C_AXIS    = "#9a7d30"
PALETTE   = [C_AMBER, C_WARN, C_GOOD, "#7c3aed", "#0ea5e9", "#ec4899"]

CT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Mono", color="#6b5a1e", size=11),
    margin=dict(l=0, r=0, t=30, b=0),
)
def fmt_axes(fig):
    fig.update_xaxes(showgrid=False, color=C_AXIS, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor=C_GRID, color=C_AXIS, zeroline=False)
    return fig

# ═══════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════
@st.cache_data
def load_data():
    files = {
        "dim_employee":         "dim_employee.xlsx",
        "dim_project":          "dim_project.xlsx",
        "bridge_ep":            "bridge_employee_project.xlsx",
        "fact_payroll":         "fact_payroll.xlsx",
        "fact_attendance":      "fact_attendance.xlsx",
        "fact_kpi":             "fact_employee_kpi.xlsx",
        "fact_leaves":          "fact_leaves.xlsx",
        "fact_project_revenue": "fact_project_revenue.xlsx",
        "fact_emp_revenue":     "fact_employee_revenue.xlsx",
        "dim_attrition":        "dim_attrition.xlsx",
    }
    d = {}
    for key, fname in files.items():
        path = os.path.join(DATA_PATH, fname)
        if os.path.exists(path):
            d[key] = pd.read_excel(path)
        else:
            st.sidebar.warning(f"⚠ Missing: {fname}")
    return d

D = load_data()

# ═══════════════════════════════════════════════
# SEMANTIC AGGREGATIONS
# ═══════════════════════════════════════════════
@st.cache_data
def emp_summary():
    pay = D["fact_payroll"].groupby("employee_id").agg(
        avg_salary=("salary","mean"), avg_incentive=("incentive","mean"),
        avg_bonus=("bonus","mean"), avg_total_cost=("total_cost","mean")).reset_index()
    att = D["fact_attendance"].groupby("employee_id").agg(
        avg_util=("utilisation","mean"), avg_productive=("productive_hours","mean"),
        avg_overtime=("overtime_hours","mean")).reset_index()
    kpi = D["fact_kpi"].groupby("employee_id").agg(
        avg_kpi=("kpi","mean"), avg_rating=("manager_rating","mean")).reset_index()
    lv  = D["fact_leaves"].groupby("employee_id").agg(
        planned=("planned_leaves","sum"), unplanned=("unplanned_leaves","sum"),
        sick=("sick_leaves","sum"), total_leaves=("total_leaves","sum")).reset_index()
    rev = D["fact_emp_revenue"].groupby("employee_id").agg(
        total_revenue=("revenue_contribution","sum"),
        net_contribution=("net_contribution","sum"),
        avg_rev_per_hr=("revenue_per_hour","mean")).reset_index()
    df = (D["dim_employee"]
          .merge(pay, on="employee_id", how="left")
          .merge(att, on="employee_id", how="left")
          .merge(kpi, on="employee_id", how="left")
          .merge(lv,  on="employee_id", how="left")
          .merge(rev, on="employee_id", how="left"))
    df["roi"] = (df["net_contribution"] / (df["avg_total_cost"] * 12).replace(0, np.nan)).round(3)
    return df

@st.cache_data
def proj_summary():
    rev = D["fact_project_revenue"].groupby("project_id").agg(
        total_revenue=("revenue","sum"), total_cost=("project_cost","sum"),
        total_penalty=("penalty","sum"), total_net=("net_revenue","sum"),
        trend_type=("trend_type","first")).reset_index()
    kpi_p = D["fact_kpi"].groupby("project_id").agg(avg_kpi=("kpi","mean")).reset_index()
    att_p = D["fact_attendance"].groupby("project_id").agg(avg_util=("utilisation","mean")).reset_index()
    emp_cnt = D["dim_employee"].groupby("project_id").size().reset_index(name="emp_count")
    df = (D["dim_project"]
          .merge(rev,    on="project_id", how="left")
          .merge(kpi_p,  on="project_id", how="left")
          .merge(att_p,  on="project_id", how="left")
          .merge(emp_cnt,on="project_id", how="left"))
    df["cost_per_emp"] = (df["total_cost"] / df["emp_count"]).round(0)
    df["rev_per_emp"]  = (df["total_revenue"] / df["emp_count"]).round(0)
    df["margin"]       = ((df["total_net"] / df["total_revenue"].replace(0, np.nan)) * 100).round(1)
    return df

@st.cache_data
def monthly_trends():
    rev = D["fact_project_revenue"][["project_id","month","revenue","project_cost","penalty","net_revenue"]]
    pay = D["fact_payroll"].groupby(["project_id","month"]).agg(total_emp_cost=("total_cost","sum")).reset_index()
    df  = rev.merge(pay, on=["project_id","month"], how="left")
    df  = df.merge(D["dim_project"][["project_id","project_name"]], on="project_id", how="left")
    return df

# ═══════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════
st.sidebar.markdown("### ⚙ Thresholds")
util_thr   = st.sidebar.slider("Utilisation",         0.0, 1.0, 0.60, 0.05, format="%.2f")
kpi_thr    = st.sidebar.slider("KPI Score",            0.0, 1.0, 0.75, 0.05, format="%.2f")
cost_thr   = st.sidebar.number_input("Emp Cost Ceiling ($/mo)", value=8000, step=500)
margin_thr = st.sidebar.number_input("Project Margin Floor (%)", value=10, step=5)
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Filters")
all_projs = ["All"] + sorted(D["dim_project"]["project_name"].tolist())
sel_proj  = st.sidebar.selectbox("Project", all_projs)
all_depts = ["All"] + sorted(D["dim_employee"]["department"].dropna().unique().tolist())
sel_dept  = st.sidebar.selectbox("Department", all_depts)
st.sidebar.markdown("---")
st.sidebar.markdown("### 🤖 AI")
ai_depth = st.sidebar.selectbox("Response depth", ["Concise","Detailed","Strategic"])
auto_ai  = st.sidebar.toggle("Auto AI insight", value=True)

# ═══════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════
def filter_emp(df):
    if sel_proj != "All":
        pid = D["dim_project"].loc[D["dim_project"]["project_name"]==sel_proj,"project_id"].values
        if "project_id" in df.columns and len(pid):
            df = df[df["project_id"].isin(pid)]
    if sel_dept != "All" and "department" in df.columns:
        df = df[df["department"] == sel_dept]
    return df

def sec(label):
    st.markdown(f'<div class="section-header">{label}</div>', unsafe_allow_html=True)

def ai_box(text):
    st.markdown(f'<div class="ai-box">{text}</div>', unsafe_allow_html=True)

def call_claude(system: str, user: str) -> str:
    key = st.secrets.get("ANTHROPIC_API_KEY", None)
    if not key:
        return "⚠ Add `ANTHROPIC_API_KEY` to Streamlit secrets to enable AI insights."
    depth = {"Concise":"Be concise — max 4 bullet points total.",
             "Detailed":"Give thorough analysis referencing specific numbers.",
             "Strategic":"Focus on board-level strategic implications and risks."}[ai_depth]
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key":key,"anthropic-version":"2023-06-01","content-type":"application/json"},
        json={"model":"claude-sonnet-4-20250514","max_tokens":1000,
              "system": system + "\n\n" + depth,
              "messages":[{"role":"user","content":user}]}
    )
    res = r.json()
    if "content" in res and res["content"]:
        return res["content"][0]["text"]
    return f"⚠ API error: {res.get('error',{}).get('message','Unknown')}"

def insight(context, data_str, question=""):
    sys_p = f"You are a COO workforce analytics advisor. Context: {context}. Format with **Observation**, **Risk**, **Action** headers. Use bullet points."
    usr_p = f"{question}\n\nData:\n{data_str}" if question else f"Analyse:\n{data_str}"
    return call_claude(sys_p, usr_p)

# ═══════════════════════════════════════════════
# HEADER + KPI CARDS
# ═══════════════════════════════════════════════
st.markdown("# 🧠 COO AI Analytics")
st.markdown('<p style="color:#9a7d30;font-size:0.85rem;margin-top:-8px;">Workforce & Project Intelligence · Powered by Claude</p>', unsafe_allow_html=True)

try:
    es_h = filter_emp(emp_summary())
    ps_h = proj_summary()
    cols = st.columns(7)
    def card(col, val, label, good):
        color = "#16a34a" if good else "#dc2626"
        col.markdown(f"""<div class="metric-card">
            <div class="metric-value" style="color:{color}">{val}</div>
            <div class="metric-label">{label}</div></div>""", unsafe_allow_html=True)
    card(cols[0], f"{es_h['avg_util'].mean():.0%}",          "Avg Utilisation",  es_h["avg_util"].mean() >= util_thr)
    card(cols[1], f"{es_h['avg_kpi'].mean():.0%}",           "Avg KPI",          es_h["avg_kpi"].mean()  >= kpi_thr)
    card(cols[2], f"${es_h['avg_total_cost'].mean():,.0f}",  "Avg Mo. Cost",     es_h["avg_total_cost"].mean() <= cost_thr)
    card(cols[3], f"${ps_h['total_revenue'].sum()/1e6:.1f}M","Total Revenue",    True)
    card(cols[4], f"${ps_h['total_penalty'].sum():,.0f}",    "Total Penalties",  ps_h["total_penalty"].sum() == 0)
    card(cols[5], f"{(es_h['avg_util'] < util_thr).sum()}",  "Low Util Flags",   (es_h["avg_util"] < util_thr).sum() == 0)
    card(cols[6], f"{(es_h['avg_kpi']  < kpi_thr).sum()}",   "Low KPI Flags",    (es_h["avg_kpi"]  < kpi_thr).sum() == 0)
except Exception as e:
    st.warning(f"Cards unavailable: {e}")

# ═══════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════
tabs = st.tabs(["💬 Ask","💰 Revenue & Cost","⚡ Productivity","👥 Redundancy","🏆 Performance","🎯 Strategic","🏗 Projects","🌿 Leaves","🚨 Issues"])

# ─── TAB 0: ASK ───────────────────────────────
with tabs[0]:
    sec("💬 Natural Language Query")
    examples = ["","Which employees have low utilisation?","Show high cost low KPI employees",
                "Revenue per hour by employee","Which projects have penalties?",
                "Who are bottom 10% ROI employees?","Correlation between cost and performance",
                "Sick leave outliers","Compare utilisation by department",
                "Which employees contribute below cost?"]
    sel_ex = st.selectbox("Quick examples →", examples, label_visibility="collapsed")
    q = st.text_input("Ask anything:", value=sel_ex, placeholder="e.g. 'high cost low KPI' or 'project penalties'")

    if q:
        ql = q.lower()
        es_f = filter_emp(emp_summary())

        if any(x in ql for x in ["correlation","relationship","correlate"]):
            sec("↗ Correlation Matrix")
            cols_c = ["avg_util","avg_kpi","avg_total_cost","net_contribution","avg_rev_per_hr"]
            corr = es_f[cols_c].corr()
            fig = go.Figure(go.Heatmap(z=corr.values, x=corr.columns, y=corr.index,
                colorscale=[[0,C_BAD],[0.5,"#fff8e1"],[1,C_AMBER]],
                zmid=0, text=corr.round(2).values, texttemplate="%{text}"))
            fig.update_layout(**CT, title="Workforce Correlation")
            st.plotly_chart(fig, use_container_width=True)
            if auto_ai:
                with st.spinner(): ai_box(insight("workforce correlation", corr.round(3).to_string()))

        elif any(x in ql for x in ["penalty","penalties"]):
            sec("⚠ Project Penalties")
            ps_p = proj_summary().sort_values("total_penalty", ascending=False)
            fig = px.bar(ps_p, x="project_name", y="total_penalty", color_discrete_sequence=[C_WARN])
            fig.update_layout(**CT); fmt_axes(fig)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(ps_p[["project_name","total_revenue","total_penalty","margin","avg_kpi"]].round(2), use_container_width=True)

        elif any(x in ql for x in ["sick","leave","leaves","unplanned"]):
            sec("🌿 Leave Analysis")
            lv = filter_emp(emp_summary())[["employee_id","name","department","planned","unplanned","sick","total_leaves"]].sort_values("total_leaves", ascending=False)
            st.dataframe(lv.head(20), use_container_width=True)
            fig = px.bar(lv.head(15), x="employee_id", y=["planned","unplanned","sick"],
                         barmode="stack", color_discrete_sequence=[C_AMBER, C_WARN, C_BAD])
            fig.update_layout(**CT); fmt_axes(fig)
            st.plotly_chart(fig, use_container_width=True)

        elif any(x in ql for x in ["roi","bottom 10","contribute below","below cost"]):
            sec("📉 Low ROI Employees")
            df = es_f.sort_values("roi").head(20)
            fig = px.bar(df, x="employee_id", y="roi", color_discrete_sequence=[C_WARN])
            fig.add_hline(y=0, line_dash="dash", line_color=C_BAD)
            fig.update_layout(**CT); fmt_axes(fig)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df[["employee_id","name","role","avg_total_cost","net_contribution","roi"]].round(2), use_container_width=True)
            if auto_ai:
                with st.spinner(): ai_box(insight("employee ROI", df[["employee_id","avg_total_cost","net_contribution","roi"]].head(10).to_string(), q))

        elif any(x in ql for x in ["revenue per hour","rev per hr"]):
            sec("💹 Revenue per Hour")
            df = es_f.sort_values("avg_rev_per_hr", ascending=False)
            fig = px.bar(df.head(20), x="employee_id", y="avg_rev_per_hr",
                         color="avg_rev_per_hr", color_continuous_scale=["#fff8e1", C_AMBER])
            fig.update_layout(**CT); fmt_axes(fig)
            st.plotly_chart(fig, use_container_width=True)

        else:
            col  = "avg_util" if "util" in ql else "avg_kpi" if "kpi" in ql else "avg_total_cost" if "cost" in ql else "avg_kpi"
            label= "Utilisation" if "util" in ql else "KPI" if "kpi" in ql else "Cost" if "cost" in ql else "KPI"
            dire = "below" if any(x in ql for x in ["low","below","under","worst","bottom","poor"]) else "above"
            mn   = re.search(r"(top|bottom)\s*(\d+)", ql)
            n    = int(mn.group(2)) if mn else 15
            df   = es_f.sort_values(col, ascending=(dire=="below")).head(n)
            sec(f"📋 {label} · {dire} threshold · {len(df)} employees")
            c1, c2 = st.columns([1.5,1])
            with c1: st.dataframe(df[["employee_id","name","department","role",col]].round(3), use_container_width=True)
            with c2:
                fig = px.histogram(es_f, x=col, nbins=20, color_discrete_sequence=[C_AMBER])
                fig.update_layout(**CT); fmt_axes(fig)
                st.plotly_chart(fig, use_container_width=True)
            if auto_ai:
                with st.spinner(): ai_box(insight(f"{label} analysis", df[["employee_id",col]].round(3).to_string(), q))

# ─── TAB 1: REVENUE & COST ────────────────────
with tabs[1]:
    sec("💰 Revenue & Cost Intelligence")
    es_f = filter_emp(emp_summary())
    ps   = proj_summary()

    st.markdown("### Highest Cost, Lowest Contribution")
    es_f["cost_gap"] = es_f["avg_total_cost"] - (es_f["net_contribution"] / 12)
    c1, c2 = st.columns(2)
    with c1:
        fig = px.scatter(es_f, x="avg_total_cost", y="net_contribution",
                         hover_data=["name","role"], color="avg_kpi",
                         color_continuous_scale=["#fff8e1",C_AMBER], title="Cost vs Net Contribution")
        fig.add_hline(y=0, line_dash="dash", line_color=C_BAD, annotation_text="Break-even")
        fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)
    with c2:
        top_gap = es_f.sort_values("cost_gap", ascending=False).head(12)
        fig = px.bar(top_gap, x="employee_id", y="cost_gap", color_discrete_sequence=[C_WARN], title="Cost–Contribution Gap")
        fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Cost per Employee vs Revenue Generated by Project")
    fig = px.bar(ps, x="project_name", y=["cost_per_emp","rev_per_emp"],
                 barmode="group", color_discrete_sequence=[C_WARN, C_AMBER])
    fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Projects Becoming More Expensive Without Revenue Growth")
    mt = monthly_trends()
    at_risk_projs = ps[ps["trend_type"].isin(["declining","volatile"])]["project_name"].tolist()
    if at_risk_projs:
        fig = px.line(mt[mt["project_name"].isin(at_risk_projs)],
                      x="month", y=["revenue","total_emp_cost"],
                      facet_col="project_name", facet_col_wrap=3,
                      color_discrete_sequence=[C_AMBER, C_WARN])
        fig.update_layout(**CT, height=450); fig.update_xaxes(showgrid=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### % Non-Productive Cost")
    es_f["non_prod_pct"] = ((1 - es_f["avg_util"]) * 100)
    avg_np = es_f["non_prod_pct"].mean()
    c1, c2 = st.columns(2)
    with c1:
        fig = px.histogram(es_f, x="non_prod_pct", nbins=20, color_discrete_sequence=[C_WARN])
        fig.add_vline(x=avg_np, line_dash="dash", line_color=C_BAD, annotation_text=f"Avg {avg_np:.1f}%")
        fig.update_layout(**CT, title="Non-Productive Time % Distribution"); fmt_axes(fig)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.dataframe(es_f.sort_values("non_prod_pct", ascending=False)[["name","role","non_prod_pct","avg_util"]].head(10).round(2), use_container_width=True)

    st.markdown("### Incentive Spend vs Performance + Penalties")
    es_f["inc_ratio"] = es_f["avg_incentive"] / es_f["avg_salary"].replace(0, np.nan)
    proj_inc = es_f.groupby("project_id").agg(avg_inc_ratio=("inc_ratio","mean")).reset_index()
    ps2 = ps.merge(proj_inc, on="project_id", how="left")
    fig = px.scatter(ps2, x="avg_inc_ratio", y="avg_kpi", size="total_penalty",
                     color="total_penalty", color_continuous_scale=["#fff8e1", C_BAD],
                     hover_data=["project_name","total_penalty"],
                     title="Incentive Ratio vs KPI (bubble = penalty)")
    fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)

    if auto_ai:
        sec("🧠 Claude Insight")
        with st.spinner():
            ai_box(insight("revenue and cost", ps[["project_name","total_revenue","total_cost","total_penalty","margin","avg_kpi"]].round(2).to_string(),
                           "Highest cost lowest contribution? Overspending on incentives?"))

# ─── TAB 2: PRODUCTIVITY ──────────────────────
with tabs[2]:
    sec("⚡ Productivity & Utilisation")
    es_f = filter_emp(emp_summary())

    st.markdown("### Low Utilisation Employees")
    low_u = es_f[es_f["avg_util"] < util_thr].sort_values("avg_util")
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(low_u.head(15), x="employee_id", y="avg_util", color_discrete_sequence=[C_WARN])
        fig.add_hline(y=util_thr, line_dash="dash", line_color=C_BAD)
        fig.update_layout(**CT, title=f"Utilisation < {util_thr:.0%}"); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.box(es_f, y="avg_util", points="all", color_discrete_sequence=[C_AMBER], title="Utilisation Distribution")
        fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Revenue per Hour by Employee (Top 20)")
    top_rph = es_f.sort_values("avg_rev_per_hr", ascending=False).head(20)
    fig = px.bar(top_rph, x="employee_id", y="avg_rev_per_hr",
                 color="avg_util", color_continuous_scale=["#fff8e1", C_AMBER], title="Revenue per Productive Hour")
    fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Overtime vs Output (Working Overtime Without Extra Revenue)")
    es_f["overtime_flag"] = es_f["avg_overtime"] > 8
    fig = px.scatter(es_f, x="avg_overtime", y="avg_rev_per_hr",
                     color="overtime_flag",
                     color_discrete_map={True: C_WARN, False: C_GOOD},
                     hover_data=["name","department"], title="Overtime Hours vs Revenue per Hour")
    fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Top Performers — Productivity Score")
    es_f["prod_score"] = (es_f["avg_util"] * 0.4 + es_f["avg_kpi"] * 0.4 + es_f["avg_rev_per_hr"].rank(pct=True) * 0.2)
    top_prod = es_f.sort_values("prod_score", ascending=False).head(15)
    fig = px.bar(top_prod, x="employee_id", y="prod_score", color_discrete_sequence=[C_GOOD], title="Top Productivity Score")
    fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Productivity Trend by Site")
    att_site = (D["fact_attendance"]
                .merge(D["dim_employee"][["employee_id","site"]], on="employee_id")
                .groupby(["site","month"])["utilisation"].mean().reset_index())
    fig = px.line(att_site, x="month", y="utilisation", color="site",
                  color_discrete_sequence=PALETTE, title="Utilisation Trend by Site")
    fig.add_hline(y=util_thr, line_dash="dash", line_color=C_BAD, annotation_text="Threshold")
    fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)

    if auto_ai:
        sec("🧠 Claude Insight")
        with st.spinner():
            ai_box(insight("productivity", es_f[["employee_id","avg_util","avg_kpi","avg_rev_per_hr","avg_overtime"]].describe().round(3).to_string(),
                           "Which teams work overtime without more output? Who are top performers?"))

# ─── TAB 3: REDUNDANCY ────────────────────────
with tabs[3]:
    sec("👥 Redundancy Identification")
    es_f = filter_emp(emp_summary())

    st.markdown("### Employees Contributing Below Cost")
    neg = es_f[es_f["net_contribution"] < 0].sort_values("net_contribution")
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(neg.head(15), x="employee_id", y="net_contribution", color_discrete_sequence=[C_BAD])
        fig.add_hline(y=0, line_dash="dash"); fig.update_layout(**CT, title="Negative Net Contribution"); fmt_axes(fig)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.dataframe(neg[["employee_id","name","role","avg_total_cost","net_contribution","avg_kpi"]].round(2).head(15), use_container_width=True)

    st.markdown("### Overlapping Roles — Cost vs Output")
    role_stats = es_f.groupby("role").agg(count=("employee_id","count"), avg_cost=("avg_total_cost","mean"),
        avg_kpi=("avg_kpi","mean"), avg_util=("avg_util","mean")).reset_index()
    fig = px.scatter(role_stats, x="avg_cost", y="avg_kpi", size="count", text="role",
                     color="avg_util", color_continuous_scale=["#fff8e1", C_AMBER],
                     title="Role: Cost vs KPI (size = headcount)")
    fig.update_traces(textposition="top center", textfont_size=9)
    fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Teams with Excess Capacity")
    dept_util = es_f.groupby("department").agg(avg_util=("avg_util","mean"),
        headcount=("employee_id","count"), avg_kpi=("avg_kpi","mean")).reset_index()
    dept_util["excess"] = dept_util["avg_util"] < util_thr
    fig = px.scatter(dept_util, x="avg_util", y="headcount",
                     color="excess", color_discrete_map={True: C_WARN, False: C_GOOD},
                     text="department", size="headcount", title="Dept Utilisation vs Headcount")
    fig.add_vline(x=util_thr, line_dash="dash", line_color=C_BAD)
    fig.update_traces(textposition="top center"); fig.update_layout(**CT); fmt_axes(fig)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Projects: Headcount vs Revenue Output")
    ps2 = proj_summary()
    fig = px.scatter(ps2, x="emp_count", y="total_revenue", color="avg_kpi", size="total_penalty",
                     text="project_name", color_continuous_scale=["#fff8e1", C_AMBER],
                     title="Project Headcount vs Revenue (bubble = penalty)")
    fig.update_traces(textposition="top center", textfont_size=9)
    fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)

    if auto_ai:
        sec("🧠 Claude Insight")
        with st.spinner():
            ai_box(insight("redundancy", neg[["employee_id","role","avg_total_cost","net_contribution"]].head(10).round(2).to_string(),
                           "Where can we reduce headcount? Which roles have overlapping output?"))

# ─── TAB 4: PERFORMANCE ───────────────────────
with tabs[4]:
    sec("🏆 Performance Insights")
    es_f = filter_emp(emp_summary())

    st.markdown("### Rating vs KPI — Bias Detection")
    c1, c2 = st.columns(2)
    with c1:
        fig = px.scatter(es_f, x="avg_rating", y="avg_kpi",
                         color="avg_total_cost", color_continuous_scale=["#fff8e1", C_AMBER],
                         hover_data=["name","role"], title="Manager Rating vs KPI Score")
        fig.add_hline(y=kpi_thr, line_dash="dash", line_color=C_BAD, annotation_text="KPI threshold")
        fig.add_vline(x=3.5, line_dash="dash", line_color=C_WARN, annotation_text="High rating")
        fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)
    with c2:
        high_rated_low = es_f[(es_f["avg_rating"] >= 3.5) & (es_f["avg_kpi"] < kpi_thr)]
        st.markdown("**High-rated, Low-KPI (potential bias)**")
        st.dataframe(high_rated_low[["name","role","avg_rating","avg_kpi","avg_total_cost"]].round(2).head(10), use_container_width=True)

    st.markdown("### Under-Recognised High Performers")
    under_rec = es_f[(es_f["avg_kpi"] >= kpi_thr) & (es_f["avg_rating"] < 3.5)].sort_values("avg_kpi", ascending=False)
    fig = px.bar(under_rec.head(15), x="employee_id", y="avg_kpi",
                 color_discrete_sequence=[C_GOOD], title="High KPI, Low Manager Rating")
    fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Does Higher Pay Correlate with Better Performance?")
    fig = px.scatter(es_f, x="avg_salary", y="avg_kpi", trendline="ols",
                     hover_data=["name","role"], color_discrete_sequence=[C_AMBER],
                     title="Salary vs KPI")
    fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Manager Effectiveness")
    mgr_p = es_f.groupby("manager_id").agg(team_avg_kpi=("avg_kpi","mean"),
        team_avg_util=("avg_util","mean"), headcount=("employee_id","count")).reset_index()
    fig = px.bar(mgr_p.sort_values("team_avg_kpi", ascending=False),
                 x="manager_id", y="team_avg_kpi",
                 color="team_avg_kpi", color_continuous_scale=["#fff8e1", C_GOOD],
                 title="Team Avg KPI by Manager")
    fig.add_hline(y=kpi_thr, line_dash="dash", line_color=C_BAD)
    fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Performance by Tenure Band")
    es_f["tenure_band"] = pd.cut(es_f["tenure_years"], bins=[0,1,2,3,5,99],
                                  labels=["<1yr","1-2yr","2-3yr","3-5yr","5+yr"])
    ten_p = es_f.groupby("tenure_band", observed=True).agg(avg_kpi=("avg_kpi","mean")).reset_index()
    fig = px.bar(ten_p, x="tenure_band", y="avg_kpi",
                 color="avg_kpi", color_continuous_scale=["#fff8e1", C_AMBER], title="Avg KPI by Tenure")
    fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)

    if auto_ai:
        sec("🧠 Claude Insight")
        with st.spinner():
            ai_box(insight("performance", mgr_p.round(3).to_string(),
                           "Who are high-rated but low-performing? Which managers produce high-performing teams?"))

# ─── TAB 5: STRATEGIC ─────────────────────────
with tabs[5]:
    sec("🎯 Strategic Insights")
    es_f = filter_emp(emp_summary())

    st.markdown("### Net Contribution per Employee")
    es_s = es_f.sort_values("net_contribution", ascending=False)
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(es_s.head(20), x="employee_id", y="net_contribution",
                     color="net_contribution", color_continuous_scale=[[0,C_BAD],[0.5,"#fff8e1"],[1,C_GOOD]])
        fig.add_hline(y=0, line_dash="dash"); fig.update_layout(**CT, title="Top 20 Net Contributors"); fmt_axes(fig)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.bar(es_s.tail(10), x="employee_id", y="net_contribution",
                     color_discrete_sequence=[C_BAD], title="Bottom 10 Net Contributors")
        fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Bottom 10% ROI Employees")
    bot_roi = es_f[es_f["roi"] <= es_f["roi"].quantile(0.10)].sort_values("roi")
    fig = px.scatter(bot_roi, x="avg_total_cost", y="net_contribution", text="employee_id",
                     color="avg_kpi", color_continuous_scale=["#fff8e1", C_AMBER],
                     title="Bottom 10% ROI: Cost vs Contribution")
    fig.add_hline(y=0, line_dash="dash", line_color=C_BAD)
    fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Cost of Attrition")
    if "dim_attrition" in D:
        atr = D["dim_attrition"].merge(D["dim_employee"][["employee_id","name","role","department"]], on="employee_id", how="left")
        c1, c2 = st.columns([1,2])
        with c1:
            st.metric("Total Attrition Cost",  f"${atr['replacement_cost'].sum():,.0f}")
            st.metric("Avg Replacement Cost",  f"${atr['replacement_cost'].mean():,.0f}")
            st.metric("Avg Months to Break-even", f"{atr['months_to_breakeven'].mean():.1f} mo")
        with c2:
            fig = px.bar(atr.sort_values("replacement_cost", ascending=False),
                         x="employee_id", y="replacement_cost", color="exit_reason",
                         color_discrete_sequence=PALETTE, title="Attrition Cost by Employee")
            fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Do Incentives Drive Performance?")
    fig = px.scatter(es_f, x="avg_incentive", y="avg_kpi", trendline="ols",
                     color="avg_incentive", color_continuous_scale=["#fff8e1", C_WARN],
                     hover_data=["name","role"], title="Incentive Spend vs KPI")
    fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)

    if auto_ai:
        sec("🧠 Claude Insight")
        with st.spinner():
            ai_box(insight("strategic ROI", es_f[["employee_id","roi","net_contribution","avg_incentive","avg_kpi"]].describe().round(3).to_string(),
                           "Net contribution per employee? Cost of attrition? Which incentives drive performance?"))

# ─── TAB 6: PROJECTS ──────────────────────────
with tabs[6]:
    sec("🏗 Project Analytics")
    ps = proj_summary()
    mt = monthly_trends()

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Projects",   len(ps))
    c2.metric("Total Revenue",    f"${ps['total_revenue'].sum()/1e6:.2f}M")
    c3.metric("Total Penalties",  f"${ps['total_penalty'].sum():,.0f}")

    st.markdown("### Revenue vs Cost vs Penalties")
    fig = go.Figure([
        go.Bar(x=ps["project_name"], y=ps["total_revenue"],  name="Revenue",  marker_color=C_AMBER),
        go.Bar(x=ps["project_name"], y=ps["total_cost"],     name="Cost",     marker_color=C_WARN),
        go.Bar(x=ps["project_name"], y=ps["total_penalty"],  name="Penalties",marker_color=C_BAD),
    ])
    fig.update_layout(barmode="group", **CT); fmt_axes(fig)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Project Margin vs KPI")
    fig = px.scatter(ps, x="margin", y="avg_kpi", size="total_revenue",
                     color="total_penalty", color_continuous_scale=["#fff8e1", C_BAD],
                     text="project_name", title="Margin vs KPI (bubble=revenue, colour=penalty)")
    fig.add_vline(x=margin_thr, line_dash="dash", line_color=C_WARN, annotation_text="Margin floor")
    fig.update_traces(textposition="top center", textfont_size=9)
    fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Monthly Revenue Trend by Project")
    fig = px.line(mt, x="month", y="revenue", color="project_name",
                  color_discrete_sequence=PALETTE, title="Revenue Trend")
    fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Project Summary Table")
    st.dataframe(ps[["project_name","status","total_revenue","total_cost","total_penalty","margin","avg_kpi","avg_util","emp_count"]].round(2), use_container_width=True)

    if auto_ai:
        sec("🧠 Claude Insight")
        with st.spinner():
            ai_box(insight("project portfolio", ps[["project_name","total_revenue","total_penalty","margin","avg_kpi","status"]].round(2).to_string(),
                           "Which projects are at risk? Where are penalties coming from?"))

# ─── TAB 7: LEAVES ────────────────────────────
with tabs[7]:
    sec("🌿 Leave Analysis")
    lv = D["fact_leaves"].merge(D["dim_employee"][["employee_id","name","department","project_id","site"]], on="employee_id", how="left")
    if sel_dept != "All":
        lv = lv[lv["department"] == sel_dept]

    lv_emp = lv.groupby(["employee_id","name","department","site"]).agg(
        planned=("planned_leaves","sum"), unplanned=("unplanned_leaves","sum"),
        sick=("sick_leaves","sum"), total=("total_leaves","sum")).reset_index()

    c1, c2, c3 = st.columns(3)
    c1.metric("Avg Total Leaves/yr",   f"{lv_emp['total'].mean():.1f}")
    c2.metric("Avg Unplanned/yr",      f"{lv_emp['unplanned'].mean():.1f}")
    c3.metric("Avg Sick/yr",           f"{lv_emp['sick'].mean():.1f}")

    c1, c2 = st.columns(2)
    with c1:
        totals = {"Planned": lv["planned_leaves"].sum(), "Unplanned": lv["unplanned_leaves"].sum(), "Sick": lv["sick_leaves"].sum()}
        fig = go.Figure(go.Pie(labels=list(totals.keys()), values=list(totals.values()),
                               hole=0.55, marker_colors=[C_AMBER, C_WARN, C_BAD]))
        fig.update_layout(**CT, title="Leave Type Mix"); st.plotly_chart(fig, use_container_width=True)
    with c2:
        lv_emp["absenteeism"] = lv_emp["unplanned"] + lv_emp["sick"]
        top_abs = lv_emp.sort_values("absenteeism", ascending=False).head(20)
        fig = px.bar(top_abs, x="employee_id", y=["unplanned","sick"], barmode="stack",
                     color_discrete_sequence=[C_WARN, C_BAD], title="Top Absentees")
        fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Monthly Leave Trend")
    lv_month = lv.groupby("month")[["planned_leaves","unplanned_leaves","sick_leaves"]].sum().reset_index()
    fig = px.line(lv_month, x="month", y=["planned_leaves","unplanned_leaves","sick_leaves"],
                  color_discrete_sequence=[C_AMBER, C_WARN, C_BAD], title="Leave Trend by Month")
    fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Absenteeism vs KPI Correlation")
    lv_kpi = lv_emp.merge(filter_emp(emp_summary())[["employee_id","avg_kpi","avg_util"]], on="employee_id", how="left")
    fig = px.scatter(lv_kpi, x="absenteeism", y="avg_kpi", trendline="ols",
                     color="avg_util", color_continuous_scale=["#fff8e1", C_AMBER],
                     hover_data=["name","department"], title="Absenteeism vs KPI")
    fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)

    st.dataframe(lv_emp.sort_values("absenteeism", ascending=False), use_container_width=True)

    if auto_ai:
        sec("🧠 Claude Insight")
        with st.spinner():
            ai_box(insight("leave patterns", lv_emp.describe().round(2).to_string(),
                           "What are the absenteeism risks? Is sick/unplanned leave concentrated in specific teams?"))

# ─── TAB 8: ISSUES ────────────────────────────
with tabs[8]:
    sec("🚨 Active Issue Flags")
    es_all = emp_summary()

    low_util_df  = es_all[es_all["avg_util"]        < util_thr].assign(issue="Low Utilisation")
    low_kpi_df   = es_all[es_all["avg_kpi"]         < kpi_thr].assign(issue="Low KPI")
    high_cost_df = es_all[es_all["avg_total_cost"]  > cost_thr].assign(issue="High Cost")
    neg_cont_df  = es_all[es_all["net_contribution"]< 0       ].assign(issue="Neg. Contribution")

    issues = pd.concat([low_util_df, low_kpi_df, high_cost_df, neg_cont_df])

    c1, c2 = st.columns([2,1])
    with c1:
        st.dataframe(issues[["employee_id","name","department","issue","avg_util","avg_kpi","avg_total_cost","net_contribution"]].round(3).head(25), use_container_width=True)
    with c2:
        counts = issues["issue"].value_counts().reset_index(); counts.columns = ["Issue","Count"]
        # orange-red for issues — no green in issue pie
        fig = go.Figure(go.Pie(labels=counts["Issue"], values=counts["Count"], hole=0.55,
                               marker_colors=[C_AMBER, C_WARN, C_BAD, "#7c3aed"]))
        fig.update_layout(**CT, title="Issues by Type"); st.plotly_chart(fig, use_container_width=True)

    sec("🏗 Project Flags")
    ps = proj_summary()
    at_risk = ps[(ps["margin"] < margin_thr) | (ps["total_penalty"] > 0) | (ps["status"] == "At Risk")]
    c1, c2 = st.columns(2)
    with c1:
        st.dataframe(at_risk[["project_name","status","margin","total_penalty","avg_kpi"]].round(2), use_container_width=True)
    with c2:
        fig = px.bar(at_risk.sort_values("total_penalty", ascending=False),
                     x="project_name", y="total_penalty", color_discrete_sequence=[C_WARN], title="Penalties by Project")
        fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)
