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
    page_title="The Orb",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "The Orb — Powered by JoAI"}
)

# ═══════════════════════════════════════════════
# CSS — Light Amber Theme
# ═══════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@400;600;700;800&display=swap');

/* Base */
html, body { font-family: 'Syne', sans-serif !important; }
[class*="css"] { font-family: 'Syne', sans-serif; }
.stApp { background: #fdfaf4 !important; color: #1a1509 !important; }

/* Sidebar — targeted selectors, no wildcard * */
section[data-testid="stSidebar"] { background: #fff8e8 !important; border-right: 1px solid #f0d88a; }
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div { color: #3a2e0a !important; }

/* Input */
.stTextInput > div > div > input {
    background: #fff !important; border: 1.5px solid #f0c842 !important; border-radius: 8px !important;
    color: #1a1509 !important; font-family:'DM Mono',monospace !important; font-size:0.9rem; padding:12px 16px;
}
.stTextInput > div > div > input:focus { border-color: #F9A602 !important; box-shadow: 0 0 0 3px rgba(249,166,2,.18) !important; }
.stTextInput > div > div > input::placeholder { color: #b89040 !important; }

/* Button */
.stButton > button {
    background: #F9A602 !important; color: #1a1509 !important; border: none !important; border-radius: 8px !important;
    font-family:'Syne',sans-serif !important; font-weight:700 !important; padding:8px 20px; transition:all .2s;
}
.stButton > button:hover { background: #e09500 !important; box-shadow:0 4px 12px rgba(249,166,2,.3); }

/* Metric cards */
.metric-card {
    background: #fff; border: 1.5px solid #f0d88a; border-radius: 12px;
    padding: 18px 22px; margin: 4px 0; box-shadow: 0 2px 8px rgba(249,166,2,.15);
}
.metric-value { font-family:'DM Mono',monospace; font-size:1.8rem; font-weight:500; color:#c97f00; line-height:1.1; }
.metric-label { font-size:0.72rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; color:#6b5010; margin-top:4px; }

/* AI box — solid bg, no transparency issues on mobile */
.ai-box {
    background: #fffbef;
    border: 1.5px solid #f0d07a; border-left: 4px solid #F9A602;
    border-radius: 10px; padding: 20px 24px;
    font-size: 0.92rem; line-height: 1.75; color: #3a2e0a !important;
    margin-top: 8px;
}

/* Section header */
.section-header {
    font-size:0.7rem; font-weight:700; letter-spacing:.15em; text-transform:uppercase;
    color:#c97f00 !important; margin-bottom:12px; margin-top:24px; display:flex; align-items:center; gap:8px;
}
.section-header::after { content:''; flex:1; height:1px; background:#f0d88a; }

/* Misc */
div[data-testid="stDataFrame"] { border:1.5px solid #f0d88a; border-radius:10px; overflow:hidden; }
h1 { font-size:1.6rem !important; font-weight:800 !important; letter-spacing:-.02em !important; color:#1a1509 !important; }
h2 { color:#3a2e0a !important; }
h3 { color:#5a4510 !important; font-size:1rem !important; margin-top:20px !important; }
p  { color:#1a1509 !important; }
.stSpinner > div { border-top-color:#F9A602 !important; }
.stSelectbox > div > div { background:#fff !important; border:1.5px solid #f0c842 !important; border-radius:8px !important; }

/* ══ MOBILE (≤ 768px) ══ */
@media (max-width: 768px) {

    html, body { font-size: 14px !important; }
    h1 { font-size: 1.25rem !important; }
    h3 { font-size: 0.9rem !important; }

    /* Metric cards — 2 per row */
    .metric-value { font-size: 1.3rem !important; }
    .metric-label { font-size: 0.65rem !important; letter-spacing: 0.05em !important; }
    .metric-card  { padding: 12px 14px !important; }

    /* AI box — force visible text */
    .ai-box {
        background: #fffbef !important;
        color: #1a1509 !important;
        font-size: 0.85rem !important;
        padding: 14px 16px !important;
    }

    /* Section header */
    .section-header { font-size: 0.62rem !important; letter-spacing: 0.08em !important; }

    /* Input */
    .stTextInput > div > div > input { font-size: 0.85rem !important; padding: 10px 12px !important; }

    /* Sidebar text */
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div { color: #3a2e0a !important; font-size: 0.85rem !important; }

    /* Charts — allow horizontal scroll */
    .js-plotly-plot { overflow-x: auto !important; }

    /* Tabs — horizontal scroll instead of wrapping */
    .stTabs [data-baseweb="tab-list"] {
        overflow-x: auto !important;
        flex-wrap: nowrap !important;
        -webkit-overflow-scrolling: touch;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 0.75rem !important;
        padding: 6px 10px !important;
        white-space: nowrap !important;
    }

    /* Dataframe */
    div[data-testid="stDataFrame"] { font-size: 0.78rem !important; }
}
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
ai_provider = st.sidebar.radio("AI Provider", ["DeepSeek", "Claude"], index=0, horizontal=True)
if ai_provider == "DeepSeek":
    ai_model = st.sidebar.selectbox("DeepSeek Model", [
        "deepseek-chat",       # V3 — fast, cost-efficient
        "deepseek-reasoner",   # R1 — analytical, slower
    ])
    ai_model_label = "DeepSeek V3 (deepseek-chat)" if ai_model == "deepseek-chat" else "DeepSeek R1 (deepseek-reasoner)"
else:
    ai_model = "claude-sonnet-4-20250514"
    ai_model_label = "Claude Sonnet"
st.sidebar.caption(f"Model: {ai_model_label}")
ai_depth = st.sidebar.selectbox("Response depth", ["Concise","Detailed","Strategic"])


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
    import re as _re
    # Convert **word**: to <strong>word</strong>: so markdown bold renders in HTML
    text = _re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Convert newlines to <br> for HTML rendering
    text = text.replace("\n", "<br>")
    st.markdown(f'<div class="ai-box">{text}</div>', unsafe_allow_html=True)

def ai_button(context, data_str, question="", key=None):
    """Renders a button; only calls AI and renders insight when clicked."""
    if st.button("🧠 Get AI Insight", key=key, use_container_width=False):
        with st.spinner("Generating insight..."):
            ai_box(insight(context, data_str, question))

def call_ai(system: str, user: str) -> str:
    depth = {"Concise":"Be concise — max 4 bullet points total.",
             "Detailed":"Give thorough analysis referencing specific numbers.",
             "Strategic":"Focus on board-level strategic implications and risks."}[ai_depth]
    full_system = system + "\n\n" + depth

    if ai_provider == "DeepSeek":
        key = st.secrets.get("DEEPSEEK_API_KEY", None)
        if not key:
            return "⚠ Add `DEEPSEEK_API_KEY` to Streamlit secrets to enable DeepSeek insights."
        r = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": ai_model,
                "max_tokens": 1000,
                "messages": [
                    {"role": "system", "content": full_system},
                    {"role": "user",   "content": user}
                ]
            }
        )
        res = r.json()
        if "choices" in res and res["choices"]:
            return res["choices"][0]["message"]["content"]
        return f"⚠ DeepSeek error: {res.get('error',{}).get('message','Unknown')}"

    else:  # Claude
        key = st.secrets.get("ANTHROPIC_API_KEY", None)
        if not key:
            return "⚠ Add `ANTHROPIC_API_KEY` to Streamlit secrets to enable Claude insights."
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key":key,"anthropic-version":"2023-06-01","content-type":"application/json"},
            json={"model":"claude-sonnet-4-20250514","max_tokens":1000,
                  "system": full_system,
                  "messages":[{"role":"user","content":user}]}
        )
        res = r.json()
        if "content" in res and res["content"]:
            return res["content"][0]["text"]
        return f"⚠ Claude error: {res.get('error',{}).get('message','Unknown')}"

# keep old name as alias so all call sites work unchanged
call_claude = call_ai

def insight(context, data_str, question=""):
    sys_p = f"You are a COO workforce analytics advisor. Context: {context}. Format with **Observation**, **Risk**, **Action** headers. Use bullet points."
    usr_p = f"{question}\n\nData:\n{data_str}" if question else f"Analyse:\n{data_str}"
    return call_claude(sys_p, usr_p)

# ═══════════════════════════════════════════════
# HEADER + KPI CARDS
# ═══════════════════════════════════════════════
st.markdown("# 🔮 The Orb")
st.markdown('<p style="color:#9a7d30;font-size:0.85rem;margin-top:-8px;">Workforce & Project Intelligence · Powered by JoAI</p>', unsafe_allow_html=True)

try:
    es_h = filter_emp(emp_summary())
    ps_h = proj_summary()

    def card_html(val, label, good):
        color = "#16a34a" if good else "#dc2626"
        return f'''<div class="metric-card">
            <div class="metric-value" style="color:{color}">{val}</div>
            <div class="metric-label">{label}</div>
        </div>'''

    cards = [
        card_html(f"{es_h['avg_util'].mean():.0%}",           "Avg Utilisation", es_h["avg_util"].mean() >= util_thr),
        card_html(f"{es_h['avg_kpi'].mean():.0%}",            "Avg KPI",         es_h["avg_kpi"].mean()  >= kpi_thr),
        card_html(f"${es_h['avg_total_cost'].mean():,.0f}",   "Avg Mo. Cost",    es_h["avg_total_cost"].mean() <= cost_thr),
        card_html(f"${ps_h['total_revenue'].sum()/1e6:.1f}M", "Total Revenue",   True),
        card_html(f"${ps_h['total_penalty'].sum():,.0f}",     "Total Penalties", ps_h["total_penalty"].sum() == 0),
        card_html(f"{(es_h['avg_util'] < util_thr).sum()}",   "Low Util Flags",  (es_h["avg_util"] < util_thr).sum() == 0),
        card_html(f"{(es_h['avg_kpi']  < kpi_thr).sum()}",    "Low KPI Flags",   (es_h["avg_kpi"]  < kpi_thr).sum() == 0),
    ]
    # Responsive grid: 4 cols on mobile via CSS, 7 on desktop
    st.markdown(
        '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin-bottom:16px;">' + "".join(cards) + '</div>',
        unsafe_allow_html=True
    )
except Exception as e:
    st.warning(f"Cards unavailable: {e}")

# ═══════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════
tabs = st.tabs(["💬 Ask","💰 Revenue & Cost","⚡ Productivity","👥 Redundancy","🏆 Performance","🎯 Strategic","🏗 Projects","🌿 Leaves","🚨 Issues"])

# ═══════════════════════════════════════════════
# SHARED QUERY RENDERER — used by both RAG and AI Ask
# ═══════════════════════════════════════════════
def parse_and_render(q, key_prefix="rag"):
    """
    Improved structured parser. Handles directionality, top/bottom N,
    ROI (top + bottom), overtime, attrition, manager, tenure, redundancy,
    department compare, project & department inline filters, and all core metrics.
    Returns True if a match was found, False otherwise.
    """
    ql = q.lower()

    # ── Inline project filter ─────────────────────
    # Matches: "in Project Apollo", "for Project Beacon", "Project Apollo"
    detected_project = None
    all_proj_names = D["dim_project"]["project_name"].tolist()
    all_proj_ids   = D["dim_project"]["project_id"].tolist()
    for pname in all_proj_names:
        if pname.lower() in ql:
            detected_project = pname
            break
    # Also match short name e.g. "apollo" -> "Project Apollo"
    if not detected_project:
        for pname in all_proj_names:
            short = pname.lower().replace("project ","").strip()
            if short in ql:
                detected_project = pname
                break

    # ── Inline department filter ──────────────────
    # Matches: "in Engineering", "for Sales team", "Engineering department"
    detected_dept = None
    all_depts = D["dim_employee"]["department"].dropna().unique().tolist()
    for dept in all_depts:
        if dept.lower() in ql:
            detected_dept = dept
            break

    # ── Apply inline filters on top of sidebar filters ──
    es_base = filter_emp(emp_summary())
    if detected_project:
        pid = D["dim_project"].loc[D["dim_project"]["project_name"]==detected_project, "project_id"].values
        if len(pid):
            es_base = es_base[es_base["project_id"].isin(pid)]
    if detected_dept:
        es_base = es_base[es_base["department"] == detected_dept]

    # Show active filter badge
    filters_applied = []
    if detected_project: filters_applied.append(f"📁 {detected_project}")
    if detected_dept:    filters_applied.append(f"🏢 {detected_dept}")
    if filters_applied:
        st.info(f"Filtered by: {' · '.join(filters_applied)}")

    es_f = es_base
    ps   = proj_summary()

    # Filter project summary if project mentioned
    if detected_project:
        pid = D["dim_project"].loc[D["dim_project"]["project_name"]==detected_project,"project_id"].values
        if len(pid):
            ps = ps[ps["project_id"].isin(pid)]

    # ── helpers ──────────────────────────────────
    def top_n():
        m = re.search(r"(top|bottom)\s*(\d+)", ql)
        return int(m.group(2)) if m else None

    def pct_n():
        m = re.search(r"(top|bottom)\s*(\d+)\s*%", ql)
        return int(m.group(2)) if m else None

    is_top    = any(x in ql for x in ["top","best","highest","most","above","exceed","high","who are top","who has highest"])
    is_bottom = any(x in ql for x in ["bottom","worst","lowest","least","below","under","poor","low","who are bottom","who has lowest"])
    n         = top_n() or 10
    pct       = pct_n()

    def topbot_df(df, col, ascending):
        if pct:
            thr = df[col].quantile(1 - pct/100) if not ascending else df[col].quantile(pct/100)
            return df[df[col] >= thr] if not ascending else df[df[col] <= thr]
        return df.sort_values(col, ascending=ascending).head(n)

    # ── CORRELATION ──────────────────────────────
    if any(x in ql for x in ["correlation","relationship","correlate","linked"]):
        sec("↗ Correlation Matrix")
        cols_c = ["avg_util","avg_kpi","avg_total_cost","net_contribution","avg_rev_per_hr"]
        corr = es_f[cols_c].corr()
        c1, c2 = st.columns(2)
        with c1:
            fig = go.Figure(go.Heatmap(z=corr.values, x=corr.columns, y=corr.index,
                colorscale=[[0,C_BAD],[0.5,"#fff8e1"],[1,C_AMBER]],
                zmid=0, text=corr.round(2).values, texttemplate="%{text}"))
            fig.update_layout(**CT, title="Workforce Correlation"); st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig = px.scatter(es_f, x="avg_util", y="avg_kpi", trendline="ols",
                             color="avg_total_cost", color_continuous_scale=["#fff8e1",C_AMBER],
                             title="Util vs KPI")
            fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)
        ai_button("workforce correlation", corr.round(3).to_string(), key=f"{key_prefix}_corr")
        return True

    # ── PENALTIES ────────────────────────────────
    if any(x in ql for x in ["penalty","penalties"]):
        sec("⚠ Project Penalties")
        ps_p = ps.sort_values("total_penalty", ascending=False)
        fig = px.bar(ps_p, x="project_name", y="total_penalty", color_discrete_sequence=[C_WARN])
        fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)
        st.dataframe(ps_p[["project_name","total_revenue","total_penalty","margin","avg_kpi"]].round(2), use_container_width=True)
        ai_button("project penalties", ps_p[["project_name","total_penalty","avg_kpi"]].to_string(), key=f"{key_prefix}_pen")
        return True

    # ── LEAVES ───────────────────────────────────
    if any(x in ql for x in ["sick","leave","leaves","unplanned","planned","absent","absentee"]):
        sec("🌿 Leave Analysis")
        lv = es_f[["employee_id","name","department","planned","unplanned","sick","total_leaves"]].copy()
        lv["absenteeism"] = lv["unplanned"] + lv["sick"]
        if is_top or "most" in ql or "high" in ql:
            lv = lv.sort_values("absenteeism", ascending=False).head(n)
            sec_label = f"Top {n} by Absenteeism"
        elif "sick" in ql:
            lv = lv.sort_values("sick", ascending=False).head(n)
            sec_label = f"Top {n} Sick Leave"
        elif "unplanned" in ql:
            lv = lv.sort_values("unplanned", ascending=False).head(n)
            sec_label = f"Top {n} Unplanned Leave"
        else:
            lv = lv.sort_values("total_leaves", ascending=False).head(20)
            sec_label = "All Leave"
        c1, c2 = st.columns([1.5,1])
        with c1: st.dataframe(lv, use_container_width=True)
        with c2:
            fig = px.bar(lv.head(15), x="employee_id", y=["planned","unplanned","sick"],
                         barmode="stack", color_discrete_sequence=[C_AMBER, C_WARN, C_BAD])
            fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)
        return True

    # ── ROI ──────────────────────────────────────
    if any(x in ql for x in ["roi","return on investment","net contribution per"]):
        if is_top and not is_bottom:
            sec(f"🌟 Top {pct or n}{'%' if pct else ''} ROI Employees")
            df = topbot_df(es_f, "roi", ascending=False)
            color = C_GOOD
        else:
            sec(f"📉 Bottom {pct or n}{'%' if pct else ''} ROI Employees")
            df = topbot_df(es_f, "roi", ascending=True)
            color = C_WARN
        fig = px.bar(df, x="employee_id", y="roi", color_discrete_sequence=[color])
        fig.add_hline(y=0, line_dash="dash", line_color=C_BAD)
        fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df[["employee_id","name","role","department","avg_total_cost","net_contribution","roi"]].round(3), use_container_width=True)
        ai_button("employee ROI", df[["employee_id","avg_total_cost","net_contribution","roi"]].round(3).to_string(), q, key=f"{key_prefix}_roi")
        return True

    # ── BELOW COST / NEGATIVE CONTRIBUTION ───────
    if any(x in ql for x in ["below cost","contribute below","negative contribution","neg contribution","not contributing"]):
        sec("📉 Employees Contributing Below Cost")
        df = es_f[es_f["net_contribution"] < 0].sort_values("net_contribution")
        fig = px.bar(df.head(15), x="employee_id", y="net_contribution", color_discrete_sequence=[C_BAD])
        fig.add_hline(y=0, line_dash="dash"); fig.update_layout(**CT); fmt_axes(fig)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df[["employee_id","name","role","avg_total_cost","net_contribution","avg_kpi"]].round(2), use_container_width=True)
        ai_button("negative contribution", df[["employee_id","avg_total_cost","net_contribution"]].round(2).to_string(), q, key=f"{key_prefix}_negcont")
        return True

    # ── REVENUE PER HOUR ─────────────────────────
    if any(x in ql for x in ["revenue per hour","rev per hour","rev/hr","output per hour","revenue efficiency"]):
        asc = is_bottom and not is_top
        sec(f"💹 {'Lowest' if asc else 'Highest'} Revenue per Hour")
        df = es_f.sort_values("avg_rev_per_hr", ascending=asc).head(n)
        fig = px.bar(df, x="employee_id", y="avg_rev_per_hr",
                     color="avg_rev_per_hr", color_continuous_scale=["#fff8e1", C_AMBER if not asc else C_WARN])
        fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df[["employee_id","name","role","avg_rev_per_hr","avg_util","avg_kpi"]].round(2), use_container_width=True)
        return True

    # ── OVERTIME ─────────────────────────────────
    if any(x in ql for x in ["overtime","over time","overworked","working extra"]):
        sec("⏱ Overtime Analysis")
        df = es_f.sort_values("avg_overtime", ascending=False).head(n)
        c1, c2 = st.columns(2)
        with c1:
            fig = px.bar(df, x="employee_id", y="avg_overtime", color_discrete_sequence=[C_WARN],
                         title=f"Top {n} Overtime Hours/Month")
            fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig = px.scatter(es_f, x="avg_overtime", y="avg_rev_per_hr",
                             color="avg_kpi", color_continuous_scale=["#fff8e1",C_AMBER],
                             title="Overtime vs Revenue per Hour")
            fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df[["employee_id","name","department","avg_overtime","avg_util","avg_kpi","avg_rev_per_hr"]].round(2), use_container_width=True)
        ai_button("overtime analysis", df[["employee_id","avg_overtime","avg_rev_per_hr","avg_kpi"]].round(2).to_string(), q, key=f"{key_prefix}_ot")
        return True

    # ── MANAGER PERFORMANCE ──────────────────────
    if any(x in ql for x in ["manager","management","team lead","which manager"]):
        sec("👔 Manager Effectiveness")
        mgr = es_f.groupby("manager_id").agg(
            team_kpi=("avg_kpi","mean"), team_util=("avg_util","mean"),
            headcount=("employee_id","count"), team_cost=("avg_total_cost","mean")).reset_index()
        if is_top:
            mgr = mgr.sort_values("team_kpi", ascending=False)
        else:
            mgr = mgr.sort_values("team_kpi", ascending=True)
        fig = px.bar(mgr, x="manager_id", y="team_kpi",
                     color="team_kpi", color_continuous_scale=["#fff8e1",C_GOOD],
                     title="Team Avg KPI by Manager")
        fig.add_hline(y=kpi_thr, line_dash="dash", line_color=C_BAD)
        fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)
        st.dataframe(mgr.round(3), use_container_width=True)
        ai_button("manager effectiveness", mgr.round(3).to_string(), q, key=f"{key_prefix}_mgr")
        return True

    # ── ATTRITION ────────────────────────────────
    if any(x in ql for x in ["attrition","resign","turnover","exit","replacement cost","breakeven","break even"]):
        sec("🚪 Attrition & Replacement Cost")
        if "dim_attrition" in D:
            atr = D["dim_attrition"].merge(D["dim_employee"][["employee_id","name","role","department"]], on="employee_id", how="left")
            c1, c2 = st.columns([1,2])
            with c1:
                st.metric("Total Attrition Cost", f"${atr['replacement_cost'].sum():,.0f}")
                st.metric("Avg Break-even",        f"{atr['months_to_breakeven'].mean():.1f} mo")
            with c2:
                fig = px.bar(atr.sort_values("replacement_cost", ascending=False),
                             x="employee_id", y="replacement_cost", color="exit_reason",
                             color_discrete_sequence=PALETTE, title="Replacement Cost by Employee")
                fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)
            st.dataframe(atr[["name","role","department","exit_reason","replacement_cost","months_to_breakeven"]].round(1), use_container_width=True)
        return True

    # ── TENURE ───────────────────────────────────
    if any(x in ql for x in ["tenure","experience","years","new hire","new employee","onboard"]):
        sec("📅 Performance by Tenure")
        es_f["tenure_band"] = pd.cut(es_f["tenure_years"], bins=[0,1,2,3,5,99],
                                      labels=["<1yr","1-2yr","2-3yr","3-5yr","5+yr"])
        ten = es_f.groupby("tenure_band", observed=True).agg(
            avg_kpi=("avg_kpi","mean"), avg_util=("avg_util","mean"),
            avg_cost=("avg_total_cost","mean"), count=("employee_id","count")).reset_index()
        c1, c2 = st.columns(2)
        with c1:
            fig = px.bar(ten, x="tenure_band", y="avg_kpi",
                         color="avg_kpi", color_continuous_scale=["#fff8e1",C_AMBER], title="KPI by Tenure")
            fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig = px.bar(ten, x="tenure_band", y="avg_util",
                         color="avg_util", color_continuous_scale=["#fff8e1",C_AMBER], title="Utilisation by Tenure")
            fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)
        st.dataframe(ten.round(3), use_container_width=True)
        return True

    # ── DEPARTMENT COMPARE ───────────────────────
    if any(x in ql for x in ["department","dept","by team","by group","compare","breakdown"]):
        sec("🏢 Department Comparison")
        dept = es_f.groupby("department").agg(
            avg_kpi=("avg_kpi","mean"), avg_util=("avg_util","mean"),
            avg_cost=("avg_total_cost","mean"), headcount=("employee_id","count"),
            avg_rev=("total_revenue","mean")).reset_index()
        col_y = ("avg_kpi" if "kpi" in ql or "performance" in ql
                 else "avg_util" if "util" in ql
                 else "avg_cost" if "cost" in ql
                 else "avg_kpi")
        fig = px.bar(dept.sort_values(col_y, ascending=False), x="department", y=col_y,
                     color=col_y, color_continuous_scale=["#fff8e1",C_AMBER])
        fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)
        st.dataframe(dept.round(3), use_container_width=True)
        return True

    # ── HIGH COST LOW KPI ────────────────────────
    if ("cost" in ql and "kpi" in ql) or ("expensive" in ql and "perform" in ql) or "cost but" in ql:
        sec("💸 High Cost, Low KPI Employees")
        df = es_f[(es_f["avg_total_cost"] > es_f["avg_total_cost"].quantile(0.6)) &
                  (es_f["avg_kpi"] < es_f["avg_kpi"].quantile(0.4))].sort_values("avg_total_cost", ascending=False)
        fig = px.scatter(es_f, x="avg_total_cost", y="avg_kpi",
                         color="net_contribution", color_continuous_scale=[[0,C_BAD],[0.5,"#fff8e1"],[1,C_GOOD]],
                         hover_data=["name","role"], title="Cost vs KPI — flagged in orange-red")
        # Highlight the flagged employees
        fig.add_scatter(x=df["avg_total_cost"], y=df["avg_kpi"],
                        mode="markers", marker=dict(color=C_WARN, size=12, symbol="circle-open", line=dict(width=2)),
                        name="High Cost Low KPI")
        fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df[["employee_id","name","role","department","avg_total_cost","avg_kpi","net_contribution"]].round(2), use_container_width=True)
        ai_button("high cost low KPI", df[["employee_id","avg_total_cost","avg_kpi","net_contribution"]].round(2).to_string(), q, key=f"{key_prefix}_hclk")
        return True

    # ── UNDERPERFORMING ──────────────────────────
    if any(x in ql for x in ["underperform","under perform","poor perform","low perform","struggling"]):
        sec("⚠ Underperforming Employees")
        df = es_f[(es_f["avg_kpi"] < kpi_thr) & (es_f["avg_util"] < util_thr)].sort_values("avg_kpi")
        fig = px.scatter(df, x="avg_util", y="avg_kpi", text="employee_id",
                         color="avg_total_cost", color_continuous_scale=["#fff8e1",C_WARN],
                         title="Low KPI + Low Utilisation")
        fig.add_hline(y=kpi_thr, line_dash="dash", line_color=C_BAD)
        fig.add_vline(x=util_thr, line_dash="dash", line_color=C_BAD)
        fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df[["employee_id","name","role","avg_kpi","avg_util","avg_total_cost"]].round(3), use_container_width=True)
        return True

    # ── TOP PERFORMERS ───────────────────────────
    if any(x in ql for x in ["top perform","best perform","star","high perform","excel","outstanding"]):
        sec(f"🌟 Top {n} Performers")
        es_f["perf_score"] = (es_f["avg_kpi"] * 0.4 + es_f["avg_util"] * 0.3 + es_f["avg_rev_per_hr"].rank(pct=True) * 0.3)
        df = es_f.sort_values("perf_score", ascending=False).head(n)
        fig = px.bar(df, x="employee_id", y="perf_score", color_discrete_sequence=[C_GOOD],
                     title=f"Top {n} Performance Score")
        fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df[["employee_id","name","role","department","avg_kpi","avg_util","avg_rev_per_hr","perf_score"]].round(3), use_container_width=True)
        return True

    # ── UNDER-RECOGNISED ─────────────────────────
    if any(x in ql for x in ["under-recogni","underrecogni","unrecogni","hidden gem","overlooked","low rating high"]):
        sec("💎 Under-Recognised High Performers")
        df = es_f[(es_f["avg_kpi"] >= kpi_thr) & (es_f["avg_rating"] < 3.5)].sort_values("avg_kpi", ascending=False)
        fig = px.bar(df.head(15), x="employee_id", y="avg_kpi",
                     color_discrete_sequence=[C_GOOD], title="High KPI, Low Manager Rating")
        fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df[["employee_id","name","role","avg_kpi","avg_rating","avg_total_cost"]].round(2), use_container_width=True)
        ai_button("under-recognised performers", df[["employee_id","avg_kpi","avg_rating"]].round(2).to_string(), q, key=f"{key_prefix}_ur")
        return True

    # ── INCENTIVE ────────────────────────────────
    if any(x in ql for x in ["incentive","bonus","reward","pay rise","increment"]):
        sec("💰 Incentive vs Performance")
        fig = px.scatter(es_f, x="avg_incentive", y="avg_kpi", trendline="ols",
                         color="avg_util", color_continuous_scale=["#fff8e1",C_AMBER],
                         hover_data=["name","role"], title="Incentive Spend vs KPI")
        fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)
        top_inc = es_f.sort_values("avg_incentive", ascending=False).head(n)
        st.dataframe(top_inc[["employee_id","name","role","avg_incentive","avg_kpi","avg_util"]].round(2), use_container_width=True)
        ai_button("incentive ROI", top_inc[["employee_id","avg_incentive","avg_kpi"]].round(2).to_string(), q, key=f"{key_prefix}_inc")
        return True

    # ── PROJECT REVENUE / MARGIN ──────────────────
    if any(x in ql for x in ["project revenue","project margin","project profit","project performance","which project"]):
        sec("🏗 Project Revenue & Margin")
        fig = px.bar(ps.sort_values("margin", ascending=False), x="project_name", y=["total_revenue","total_cost"],
                     barmode="group", color_discrete_sequence=[C_AMBER, C_WARN])
        fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)
        st.dataframe(ps[["project_name","status","total_revenue","total_cost","total_penalty","margin","avg_kpi"]].round(2), use_container_width=True)
        return True

    # ── GENERIC METRIC FILTER (fallback) ─────────
    if any(x in ql for x in ["util","kpi","performance","cost","salary","productive","hour"]):
        col   = ("avg_util"       if any(x in ql for x in ["util","productive","hours"]) else
                 "avg_kpi"        if any(x in ql for x in ["kpi","performance","score"]) else
                 "avg_total_cost" if any(x in ql for x in ["cost","salary","pay"])       else "avg_kpi")
        label = ("Utilisation" if "util" in ql or "productive" in ql else
                 "KPI"         if "kpi" in ql or "performance" in ql else
                 "Cost"        if "cost" in ql or "salary" in ql     else "KPI")
        asc   = is_bottom and not is_top
        df    = es_f.sort_values(col, ascending=asc).head(n)
        sec(f"📋 {'Lowest' if asc else 'Highest'} {label} · Top {n} employees")
        c1, c2 = st.columns([1.5,1])
        with c1: st.dataframe(df[["employee_id","name","department","role",col]].round(3), use_container_width=True)
        with c2:
            fig = px.histogram(es_f, x=col, nbins=20, color_discrete_sequence=[C_AMBER])
            fig.update_layout(**CT); fmt_axes(fig); st.plotly_chart(fig, use_container_width=True)
        ai_button(f"{label} analysis", df[["employee_id",col]].round(3).to_string(), q, key=f"{key_prefix}_gen")
        return True

    return False  # no match


# ═══════════════════════════════════════════════
# NLP INTENT PARSER — for Ask Anything (AI)
# ═══════════════════════════════════════════════
def ai_parse_intent(question: str) -> dict:
    """Send question to AI, get back structured intent JSON."""
    system = """You are a workforce analytics query parser.
Given a natural language question, return ONLY a valid JSON object with these fields:
{
  "intent": one of [correlation, penalties, leaves, roi_top, roi_bottom, below_cost, revenue_per_hour,
                    overtime, manager, attrition, tenure, department, high_cost_low_kpi,
                    underperform, top_performers, under_recognised, incentive, project_revenue, metric_filter, unknown],
  "metric": one of [avg_util, avg_kpi, avg_total_cost, avg_rev_per_hr, null],
  "direction": one of [top, bottom, null],
  "n": integer or null,
  "pct": integer (if percentage mentioned) or null,
  "department": string or null
}
Return ONLY the JSON. No explanation. No markdown."""

    raw = call_ai(system, question)
    try:
        import json
        raw = raw.strip().replace("```json","").replace("```","")
        return json.loads(raw)
    except Exception:
        return {"intent": "unknown"}

def intent_to_query(parsed: dict) -> str:
    """Convert parsed intent back to a keyword query the parser understands."""
    intent = parsed.get("intent", "unknown")
    n      = parsed.get("n") or 10
    pct    = parsed.get("pct")
    dept   = parsed.get("department")
    metric = parsed.get("metric","")
    direction = parsed.get("direction","top")

    mapping = {
        "correlation":        "correlation",
        "penalties":          "penalties",
        "leaves":             "leaves",
        "roi_top":            f"top {pct}% roi" if pct else f"top {n} roi",
        "roi_bottom":         f"bottom {pct}% roi" if pct else f"bottom {n} roi",
        "below_cost":         "contribute below cost",
        "revenue_per_hour":   f"{'bottom' if direction=='bottom' else 'top'} {n} revenue per hour",
        "overtime":           "overtime",
        "manager":            f"{'top' if direction=='top' else 'worst'} manager",
        "attrition":          "attrition",
        "tenure":             "tenure",
        "department":         f"compare by department {metric or 'kpi'}",
        "high_cost_low_kpi":  "high cost low kpi",
        "underperform":       "underperforming employees",
        "top_performers":     f"top {n} performers",
        "under_recognised":   "under-recognised",
        "incentive":          "incentive",
        "project_revenue":    "project revenue margin",
        "metric_filter":      f"{'bottom' if direction=='bottom' else 'top'} {n} {metric or 'kpi'}",
    }
    q = mapping.get(intent, "")
    if dept and q:
        q += f" department {dept}"
    return q


# ─── TAB 0: ASK ───────────────────────────────
with tabs[0]:

    # ── Option A: Indexed Search ──────────────
    sec("🗂 Indexed Search (RAG Query)")
    RAG_EXAMPLES = [
        "",
        # Utilisation
        "Which employees have low utilisation?",
        "Top 10 highest utilisation employees",
        # KPI / Performance
        "Show high cost low KPI employees",
        "Who are the top 10 performers?",
        "Who are underperforming employees?",
        "Who are under-recognised high performers?",
        # ROI
        "Who are top 10% ROI employees?",
        "Who are bottom 10% ROI employees?",
        "Which employees contribute below cost?",
        # Revenue
        "Revenue per hour by employee",
        "Bottom 10 revenue per hour employees",
        "Which project has the best margin?",
        "Project revenue and cost breakdown",
        # Cost & Incentives
        "Show high cost employees",
        "Do incentives improve performance?",
        # Overtime
        "Which employees work the most overtime?",
        "Overtime vs output analysis",
        # Leaves
        "Who has the most sick leave?",
        "Unplanned leave analysis",
        "Top 10 absentees",
        # Managers
        "Which managers have the best performing teams?",
        "Which managers have the worst performing teams?",
        # Attrition
        "What is the cost of attrition?",
        "Employee turnover and replacement cost",
        # Tenure
        "Performance by tenure",
        "How do new hires perform?",
        # Department
        "Compare KPI by department",
        "Utilisation breakdown by department",
        # Correlation
        "Correlation between cost and performance",
        # Penalties
        "Which projects have penalties?",
        # Project-specific
        "Low utilisation in Project Apollo",
        "Top performers in Project Beacon",
        "High cost employees in Project Catalyst",
        "Who are bottom ROI in Project Delta?",
        # Department-specific
        "Low KPI in Engineering",
        "Top 5 performers in Sales",
        "Overtime analysis for Operations",
        "Absentees in Finance",
        "High cost employees in HR",
    ]
    # ── Mode toggle ──────────────────────────
    input_mode = st.radio("Input mode", ["📋 Dropdown", "✏️ Custom Query"],
                          horizontal=True, label_visibility="collapsed")

    # Reset stored query when mode switches
    if "rag_mode" not in st.session_state:
        st.session_state["rag_mode"] = input_mode
    if input_mode != st.session_state["rag_mode"]:
        st.session_state["rag_mode"]     = input_mode
        st.session_state["rag_active_q"] = ""

    if "rag_active_q" not in st.session_state:
        st.session_state["rag_active_q"] = ""

    # ── Show only the active field ────────────
    if input_mode == "📋 Dropdown":
        sel_rag = st.selectbox("Select a query →", RAG_EXAMPLES,
                               label_visibility="collapsed", key="rag_selectbox")
        if sel_rag and sel_rag != st.session_state["rag_active_q"]:
            st.session_state["rag_active_q"] = sel_rag
        active_q = st.session_state["rag_active_q"]

    else:  # Custom Query
        rag_q = st.text_input("Type your query:", value="",
                               placeholder="e.g. 'top 10% ROI employees' or 'low utilisation'",
                               key="rag_input")
        if rag_q.strip() and rag_q.strip() != st.session_state["rag_active_q"]:
            st.session_state["rag_active_q"] = rag_q.strip()
        active_q = st.session_state["rag_active_q"]

    # ── Render results ────────────────────────
    if active_q:
        found = parse_and_render(active_q, key_prefix="rag")
        if not found:
            st.warning("No match found. Try rephrasing or use **Ask Anything (AI)** below for complex questions.")

    st.markdown("---")

    # ── Option B: Ask Anything (AI) ──────────
    sec("🤖 Ask Anything (AI)")
    st.caption("⚠️ AI-powered: may misunderstand intent and produce inaccuracies.")
    ai_q = st.text_input("Ask in plain language:",
                          placeholder="e.g. 'Who are the top 10% ROI employees?' or 'Which managers consistently underdeliver?'",
                          key="ai_ask_input")

    # When user types in AI box → clear RAG custom box and reset dropdown
    if ai_q.strip() and ai_q.strip() != st.session_state.get("last_ai_q", ""):
        st.session_state["last_ai_q"]    = ai_q.strip()
        st.session_state["rag_input"]    = ""   # clear custom query box
        st.session_state["last_sel_rag"] = ""   # will cause dropdown to show blank next cycle

    if ai_q:
        with st.spinner("Parsing intent..."):
            parsed = ai_parse_intent(ai_q)
        routed_q = intent_to_query(parsed)
        if routed_q:
            st.caption(f"Interpreted as: *{routed_q}*")
            found = parse_and_render(routed_q, key_prefix="ai")
            if not found:
                st.warning("Could not match intent to a known analysis. Try rephrasing or use Indexed Search.")
        else:
            st.warning("Could not interpret question. Try Indexed Search for structured queries.")

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

    sec("🧠 Claude Insight")
    if st.button("🧠 Get AI Insight", key="btn_rev", use_container_width=False):
        with st.spinner("Generating insight..."):
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

    sec("🧠 Claude Insight")
    if st.button("🧠 Get AI Insight", key="btn_prod", use_container_width=False):
        with st.spinner("Generating insight..."):
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

    sec("🧠 Claude Insight")
    if st.button("🧠 Get AI Insight", key="btn_red", use_container_width=False):
        with st.spinner("Generating insight..."):
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

    sec("🧠 Claude Insight")
    if st.button("🧠 Get AI Insight", key="btn_perf", use_container_width=False):
        with st.spinner("Generating insight..."):
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

    sec("🧠 Claude Insight")
    if st.button("🧠 Get AI Insight", key="btn_strat", use_container_width=False):
        with st.spinner("Generating insight..."):
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

    sec("🧠 Claude Insight")
    if st.button("🧠 Get AI Insight", key="btn_proj", use_container_width=False):
        with st.spinner("Generating insight..."):
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

    sec("🧠 Claude Insight")
    if st.button("🧠 Get AI Insight", key="btn_leave", use_container_width=False):
        with st.spinner("Generating insight..."):
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
    cols_show = ["employee_id","name","department","issue","avg_util","avg_kpi","avg_total_cost","net_contribution"]

    # Summary counts
    counts = issues["issue"].value_counts().reset_index(); counts.columns = ["Issue","Count"]
    c1, c2, c3, c4 = st.columns(4)
    for col_m, (_, row) in zip([c1,c2,c3,c4], counts.iterrows()):
        col_m.metric(row["Issue"], f"{row['Count']} employees")

    # Pie chart
    c1, c2 = st.columns([1,1])
    with c1:
        fig = go.Figure(go.Pie(labels=counts["Issue"], values=counts["Count"], hole=0.55,
                               marker_colors=[C_AMBER, C_WARN, C_BAD, "#7c3aed"]))
        fig.update_layout(**CT, title="Issues by Type")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig2 = px.bar(counts, x="Issue", y="Count",
                      color="Issue", color_discrete_sequence=[C_AMBER, C_WARN, C_BAD, "#7c3aed"],
                      title="Issue Counts")
        fig2.update_layout(**CT); fmt_axes(fig2)
        st.plotly_chart(fig2, use_container_width=True)

    # Per-issue expandable tables — fully untruncated, sorted by worst first
    issue_order = [
        ("Low KPI",           low_kpi_df,   "avg_kpi",          True),
        ("Low Utilisation",   low_util_df,  "avg_util",         True),
        ("High Cost",         high_cost_df, "avg_total_cost",   False),
        ("Neg. Contribution", neg_cont_df,  "net_contribution", True),
    ]
    for label, df, sort_col, asc in issue_order:
        if len(df) == 0:
            continue
        icon = "🔴" if label == "Neg. Contribution" else "🟠"
        with st.expander(f"{icon} {label} — {len(df)} employees", expanded=True):
            st.dataframe(
                df[cols_show].sort_values(sort_col, ascending=asc).round(3),
                use_container_width=True
            )

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
