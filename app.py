import sqlite3
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).with_name("projetos.db")
STATUSES = ["Planejamento", "Em andamento", "Atenção", "Pausado", "Concluído"]
RISK_STATUSES = ["Aberto", "Em tratamento", "Resolvido"]

st.set_page_config(
    page_title="Nexo | Gestão de Projetos",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Persistência local ----------
def connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                owner TEXT,
                start_date TEXT,
                end_date TEXT,
                status TEXT NOT NULL DEFAULT 'Planejamento',
                progress INTEGER NOT NULL DEFAULT 0,
                description TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS risks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                probability TEXT NOT NULL,
                impact TEXT NOT NULL,
                mitigation TEXT,
                status TEXT NOT NULL DEFAULT 'Aberto',
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """)


def query(sql, params=()):
    with connect() as conn:
        return pd.read_sql_query(sql, conn, params=params)


def execute(sql, params=()):
    with connect() as conn:
        conn.execute(sql, params)
        conn.commit()


def risk_level(probability, impact):
    score = {"Baixa": 1, "Média": 2, "Alta": 3}[probability] * {
        "Baixo": 1, "Médio": 2, "Alto": 3
    }[impact]
    if score >= 6:
        return "Alto"
    if score >= 3:
        return "Médio"
    return "Baixo"


def status_class(status):
    return {
        "Planejamento": "planning",
        "Em andamento": "active",
        "Atenção": "attention",
        "Pausado": "paused",
        "Concluído": "done",
    }.get(status, "planning")


def fmt_date(value):
    if not value:
        return "—"
    try:
        return date.fromisoformat(str(value)).strftime("%d/%m/%Y")
    except ValueError:
        return str(value)


def metric_card(label, value, note, accent="blue"):
    st.markdown(
        f"""
        <div class="metric-card {accent}">
          <div class="metric-label">{label}</div>
          <div class="metric-value">{value}</div>
          <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


init_db()

# ---------- Design system ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --ink:#172033; --muted:#758097; --line:#e8edf4; --blue:#4361ee; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.stApp { background:#f6f8fc; color:var(--ink); }
.block-container { max-width:1440px; padding-top:1.7rem; padding-bottom:3rem; }
[data-testid="stSidebar"] { background:#111a2e; border-right:1px solid #202b43; }
[data-testid="stSidebar"] * { color:#e8edf8; }
[data-testid="stSidebar"] .stRadio label { padding:7px 10px; border-radius:9px; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#9eabc4; }
.brand { display:flex; align-items:center; gap:12px; padding:8px 4px 28px; }
.brand-mark { display:flex; align-items:center; justify-content:center; width:42px; height:42px; border-radius:13px; background:linear-gradient(135deg,#6178ff,#8b5cf6); color:white; font-size:25px; font-weight:800; }
.brand-name { color:#fff; font-family:'Manrope',sans-serif; font-size:21px; font-weight:800; letter-spacing:-.7px; }
.brand-sub { color:#93a1bc; font-size:11px; letter-spacing:1.6px; text-transform:uppercase; margin-top:1px; }
.sidebar-label { color:#7f8da8; font-size:10px; letter-spacing:1.5px; font-weight:700; text-transform:uppercase; margin:12px 0 8px; }
.page-eyebrow { color:#6375d9; text-transform:uppercase; letter-spacing:1.8px; font-size:10px; font-weight:800; margin-bottom:7px; }
h1, h2, h3 { font-family:'Manrope',sans-serif !important; color:#172033 !important; letter-spacing:-.6px; }
h1 { font-size:30px !important; font-weight:800 !important; margin-bottom:2px !important; }
h2 { font-size:21px !important; font-weight:750 !important; }
h3 { font-size:16px !important; font-weight:700 !important; }
.page-subtitle { color:#7b8498; font-size:13px; margin:0 0 22px; }
.metric-card { background:#fff; border:1px solid #e9edf5; border-radius:16px; padding:19px 20px; min-height:132px; box-shadow:0 3px 14px rgba(22,34,66,.025); position:relative; overflow:hidden; }
.metric-card:before { content:''; position:absolute; top:0; left:0; height:3px; width:100%; background:#4361ee; }
.metric-card.purple:before { background:#8b5cf6; } .metric-card.orange:before { background:#f59e0b; } .metric-card.red:before { background:#ef4444; } .metric-card.green:before { background:#10b981; }
.metric-label { color:#7c879b; font-size:12px; font-weight:600; margin-bottom:13px; }
.metric-value { font-family:'Manrope',sans-serif; font-size:31px; font-weight:800; color:#172033; line-height:1.05; }
.metric-note { color:#9aa3b3; font-size:11px; margin-top:10px; }
.panel { background:#fff; border:1px solid #e9edf5; border-radius:16px; padding:20px 22px; box-shadow:0 3px 14px rgba(22,34,66,.025); }
.status-pill { display:inline-block; border-radius:20px; padding:5px 10px; font-size:11px; font-weight:700; white-space:nowrap; }
.planning { color:#596579; background:#eef1f6; } .active { color:#2563eb; background:#e8f0ff; }
.attention { color:#b45309; background:#fff1d6; } .paused { color:#6b7280; background:#f1f2f5; } .done { color:#047857; background:#dff8ed; }
.stButton > button { border-radius:9px; font-weight:650; min-height:40px; }
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] { background:#4361ee; border-color:#4361ee; }
div[data-testid="stForm"] { background:#fff; border:1px solid #e8edf4; border-radius:14px; padding:18px; }
div[data-testid="stExpander"] { background:#fff; border:1px solid #e8edf4; border-radius:12px; }
div[data-testid="stMetric"] { background:#fff; border:1px solid #e8edf4; padding:14px 16px; border-radius:12px; }
.stProgress > div > div > div > div { background:#536dfe; }
hr { border-color:#e8edf4; }
.small-muted { color:#8a94a8; font-size:12px; }
div[data-testid="stDataFrame"] { border:1px solid #e8edf4; border-radius:12px; overflow:hidden; }
@media (max-width: 768px) { .block-container { padding:1rem .8rem 2rem; } h1 { font-size:25px !important; } .metric-card { padding:15px; min-height:115px; } }
</style>
""", unsafe_allow_html=True)

# ---------- Navegação ----------
with st.sidebar:
    st.markdown("""
    <div class="brand">
      <div class="brand-mark">◈</div>
      <div><div class="brand-name">nexo</div><div class="brand-sub">project workspace</div></div>
    </div>
    <div class="sidebar-label">Workspace</div>
    """, unsafe_allow_html=True)
    page = st.radio(
        "Navegação",
        ["Visão geral", "Projetos", "Riscos"],
        label_visibility="collapsed",
        format_func=lambda x: {"Visão geral": "◫  Visão geral", "Projetos": "▦  Projetos", "Riscos": "◇  Riscos e impedimentos"}[x],
    )
    st.markdown("<br><div class='sidebar-label'>Sobre o workspace</div>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:12px;line-height:1.6'>Organize entregas, acompanhe prazos e dê visibilidade aos riscos do projeto.</p>", unsafe_allow_html=True)
    st.markdown("<br><div style='border-top:1px solid #29344b;padding-top:15px;color:#8492ad;font-size:11px'>NEXO · PORTFÓLIO DE PROJETOS<br>Versão demonstrativa</div>", unsafe_allow_html=True)

projects = query("SELECT * FROM projects ORDER BY id DESC")
risks = query("""
    SELECT r.*, p.name AS project_name
    FROM risks r JOIN projects p ON p.id = r.project_id
    ORDER BY r.id DESC
""") if not projects.empty else pd.DataFrame()

# ---------- Visão geral ----------
if page == "Visão geral":
    st.markdown("<div class='page-eyebrow'>Workspace / Dashboard</div>", unsafe_allow_html=True)
    st.title("Visão geral")
    st.markdown("<p class='page-subtitle'>Uma visão clara do portfólio, dos prazos e dos pontos que precisam de atenção.</p>", unsafe_allow_html=True)

    total = len(projects)
    active = int(projects["status"].isin(["Em andamento", "Atenção"]).sum()) if total else 0
    completed = int((projects["status"] == "Concluído").sum()) if total else 0
    high_risks = int(sum(
        risk_level(r["probability"], r["impact"]) == "Alto" and r["status"] != "Resolvido"
        for _, r in risks.iterrows()
    )) if not risks.empty else 0
    today = date.today().isoformat()
    overdue = int(sum(
        bool(row["end_date"]) and row["end_date"] < today and row["status"] != "Concluído"
        for _, row in projects.iterrows()
    )) if total else 0
    avg_progress = int(projects["progress"].mean()) if total else 0

    cols = st.columns(4)
    with cols[0]: metric_card("PROJETOS NO PORTFÓLIO", total, f"{completed} concluído(s)", "blue")
    with cols[1]: metric_card("EM EXECUÇÃO", active, "Em andamento ou atenção", "purple")
    with cols[2]: metric_card("PRAZOS VENCIDOS", overdue, "Projetos não concluídos", "orange")
    with cols[3]: metric_card("RISCOS ALTOS", high_risks, "Ainda não resolvidos", "red")

    st.write("")
    left, right = st.columns([1.55, 1], gap="large")
    with left:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("Portfólio de projetos")
        st.markdown("<p class='small-muted'>Acompanhe o status e o avanço das principais iniciativas.</p>", unsafe_allow_html=True)
        if projects.empty:
            st.info("Seu portfólio ainda está vazio. Acesse **Projetos** para cadastrar a primeira iniciativa.")
        else:
            for _, p in projects.head(7).iterrows():
                a, b = st.columns([3, 1])
                with a:
                    st.markdown(f"**{p['name']}**")
                    st.markdown(f"<span class='status-pill {status_class(p['status'])}'>{p['status']}</span> <span class='small-muted'>Prazo: {fmt_date(p['end_date'])}</span>", unsafe_allow_html=True)
                with b:
                    st.markdown(f"<div style='text-align:right;font-size:13px;font-weight:700;padding-top:3px'>{int(p['progress'])}%</div>", unsafe_allow_html=True)
                st.progress(int(p["progress"]) / 100)
                st.markdown("<div style='height:7px'></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("Saúde do portfólio")
        st.markdown("<p class='small-muted'>Distribuição atual dos projetos por status.</p>", unsafe_allow_html=True)
        if projects.empty:
            st.info("Os gráficos serão exibidos após o cadastro de projetos.")
        else:
            status_counts = projects["status"].value_counts().reindex(STATUSES, fill_value=0)
            chart_df = status_counts[status_counts > 0].rename_axis("Status").reset_index(name="Projetos")
            st.bar_chart(chart_df.set_index("Status"), use_container_width=True)
            st.markdown(f"<div class='small-muted'>Progresso médio do portfólio: <b>{avg_progress}%</b></div>", unsafe_allow_html=True)
            st.progress(avg_progress / 100)
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.subheader("Pontos de atenção")
    if overdue:
        st.warning(f"Há {overdue} projeto(s) com prazo vencido. Revise as datas e os próximos passos.")
    if high_risks:
        st.warning(f"Há {high_risks} risco(s) de nível alto ainda não resolvido(s).")
    if not overdue and not high_risks:
        st.success("Nenhum prazo vencido ou risco alto identificado com os dados atuais.")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- Projetos ----------
elif page == "Projetos":
    st.markdown("<div class='page-eyebrow'>Workspace / Gestão</div>", unsafe_allow_html=True)
    st.title("Projetos")
    st.markdown("<p class='page-subtitle'>Cadastre iniciativas, mantenha os dados atualizados e acompanhe a evolução das entregas.</p>", unsafe_allow_html=True)

    with st.expander("＋  Cadastrar novo projeto", expanded=projects.empty):
        with st.form("new_project", clear_on_submit=True):
            name = st.text_input("Nome do projeto *", placeholder="Ex.: Implantação de sistema CLM")
            c1, c2 = st.columns(2)
            owner = c1.text_input("Responsável", placeholder="Nome do responsável")
            status = c2.selectbox("Status", STATUSES)
            c3, c4 = st.columns(2)
            start = c3.date_input("Data de início", value=date.today())
            end = c4.date_input("Prazo previsto", value=date.today())
            progress = st.slider("Progresso (%)", 0, 100, 0, step=5)
            description = st.text_area("Objetivo e observações", placeholder="Descreva o objetivo, escopo ou contexto do projeto...")
            submitted = st.form_submit_button("Salvar projeto", type="primary", use_container_width=True)
            if submitted:
                if not name.strip():
                    st.error("Informe o nome do projeto.")
                elif end < start:
                    st.error("O prazo previsto não pode ser anterior à data de início.")
                else:
                    execute("""INSERT INTO projects (name, owner, start_date, end_date, status, progress, description, created_at)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                            (name.strip(), owner.strip(), start.isoformat(), end.isoformat(), status, progress, description.strip(), datetime.now().isoformat(timespec="seconds")))
                    st.success("Projeto cadastrado com sucesso.")
                    st.rerun()

    projects = query("SELECT * FROM projects ORDER BY id DESC")
    search = st.text_input("⌕  Buscar projeto", placeholder="Digite o nome ou responsável...")
    status_filter = st.selectbox("Filtrar por status", ["Todos os status"] + STATUSES, label_visibility="collapsed")
    filtered = projects.copy()
    if search.strip() and not filtered.empty:
        filtered = filtered[filtered["name"].str.contains(search, case=False, na=False) | filtered["owner"].str.contains(search, case=False, na=False)]
    if status_filter != "Todos os status" and not filtered.empty:
        filtered = filtered[filtered["status"] == status_filter]

    st.markdown(f"<p class='small-muted'>{len(filtered)} projeto(s) encontrado(s)</p>", unsafe_allow_html=True)
    if filtered.empty:
        st.info("Nenhum projeto encontrado. Cadastre um projeto ou ajuste os filtros.")
    else:
        for _, p in filtered.iterrows():
            with st.expander(f"{p['name']}   ·   {p['status']}   ·   {int(p['progress'])}%"):
                st.markdown(f"<span class='status-pill {status_class(p['status'])}'>{p['status']}</span>", unsafe_allow_html=True)
                st.write(p["description"] or "Sem descrição registrada.")
                m1, m2, m3 = st.columns(3)
                m1.caption(f"**Responsável**\n\n{p['owner'] or 'Não definido'}")
                m2.caption(f"**Início**\n\n{fmt_date(p['start_date'])}")
                m3.caption(f"**Prazo previsto**\n\n{fmt_date(p['end_date'])}")
                st.progress(int(p["progress"]) / 100, text=f"Progresso: {int(p['progress'])}%")
                with st.form(f"edit_project_{p['id']}"):
                    st.markdown("**Editar informações**")
                    e_name = st.text_input("Nome", value=p["name"])
                    e_owner = st.text_input("Responsável", value=p["owner"] or "")
                    e_status = st.selectbox("Status", STATUSES, index=STATUSES.index(p["status"]))
                    e1, e2 = st.columns(2)
                    e_start = e1.date_input("Início", value=date.fromisoformat(p["start_date"]) if p["start_date"] else date.today(), key=f"start_{p['id']}")
                    e_end = e2.date_input("Prazo", value=date.fromisoformat(p["end_date"]) if p["end_date"] else date.today(), key=f"end_{p['id']}")
                    e_progress = st.slider("Progresso (%)", 0, 100, int(p["progress"]), step=5, key=f"progress_{p['id']}")
                    e_desc = st.text_area("Objetivo e observações", value=p["description"] or "", key=f"desc_{p['id']}")
                    save = st.form_submit_button("Salvar alterações", type="primary")
                    if save:
                        if not e_name.strip() or e_end < e_start:
                            st.error("Confira o nome e as datas do projeto.")
                        else:
                            execute("""UPDATE projects SET name=?, owner=?, status=?, progress=?, start_date=?, end_date=?, description=? WHERE id=?""",
                                    (e_name.strip(), e_owner.strip(), e_status, e_progress, e_start.isoformat(), e_end.isoformat(), e_desc.strip(), int(p["id"])))
                            st.success("Projeto atualizado.")
                            st.rerun()
                confirm_delete = st.checkbox("Confirmo que desejo excluir este projeto", key=f"confirm_delete_{p['id']}")
                if st.button("Excluir projeto", key=f"delete_{p['id']}", disabled=not confirm_delete):
                    execute("DELETE FROM risks WHERE project_id=?", (int(p["id"]),))
                    execute("DELETE FROM projects WHERE id=?", (int(p["id"]),))
                    st.rerun()

# ---------- Riscos ----------
else:
    st.markdown("<div class='page-eyebrow'>Workspace / Controle</div>", unsafe_allow_html=True)
    st.title("Riscos e impedimentos")
    st.markdown("<p class='page-subtitle'>Registre ameaças, avalie probabilidade e impacto e documente as respostas planejadas.</p>", unsafe_allow_html=True)

    projects = query("SELECT id, name FROM projects ORDER BY name")
    risks = query("""SELECT r.*, p.name AS project_name FROM risks r JOIN projects p ON p.id=r.project_id ORDER BY r.id DESC""") if not projects.empty else pd.DataFrame()
    open_count = int((risks["status"] != "Resolvido").sum()) if not risks.empty else 0
    high_count = int(sum(risk_level(r["probability"], r["impact"]) == "Alto" and r["status"] != "Resolvido" for _, r in risks.iterrows())) if not risks.empty else 0
    risk_cols = st.columns(3)
    with risk_cols[0]: metric_card("RISCOS REGISTRADOS", len(risks), "No portfólio atual", "blue")
    with risk_cols[1]: metric_card("EM ABERTO", open_count, "Aberto ou em tratamento", "orange")
    with risk_cols[2]: metric_card("NÍVEL ALTO", high_count, "Prioridade de resposta", "red")

    st.write("")
    with st.expander("＋  Registrar novo risco", expanded=projects.empty):
        if projects.empty:
            st.info("Cadastre um projeto antes de registrar riscos.")
        else:
            project_options = {int(row["id"]): row["name"] for _, row in projects.iterrows()}
            with st.form("new_risk", clear_on_submit=True):
                project_id = st.selectbox("Projeto relacionado", options=list(project_options), format_func=lambda x: project_options[x])
                title = st.text_input("Nome do risco *", placeholder="Ex.: Atraso na liberação do ambiente de testes")
                description = st.text_area("Descrição e possível impacto")
                c1, c2 = st.columns(2)
                probability = c1.selectbox("Probabilidade", ["Baixa", "Média", "Alta"])
                impact = c2.selectbox("Impacto", ["Baixo", "Médio", "Alto"])
                mitigation = st.text_area("Plano de resposta / mitigação", placeholder="Ação preventiva, contingência ou responsável...")
                risk_status = st.selectbox("Situação", RISK_STATUSES)
                level = risk_level(probability, impact)
                st.info(f"Nível calculado automaticamente: **{level}**")
                add_risk = st.form_submit_button("Salvar risco", type="primary", use_container_width=True)
                if add_risk:
                    if not title.strip():
                        st.error("Informe o nome do risco.")
                    else:
                        execute("""INSERT INTO risks (project_id, title, description, probability, impact, mitigation, status, created_at)
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                                (project_id, title.strip(), description.strip(), probability, impact, mitigation.strip(), risk_status, datetime.now().isoformat(timespec="seconds")))
                        st.success("Risco registrado.")
                        st.rerun()

    risks = query("""SELECT r.*, p.name AS project_name FROM risks r JOIN projects p ON p.id=r.project_id ORDER BY r.id DESC""") if not projects.empty else pd.DataFrame()
    if not risks.empty:
        st.subheader("Registro de riscos")
        for _, r in risks.iterrows():
            level = risk_level(r["probability"], r["impact"])
            icon = "🔴" if level == "Alto" else ("🟠" if level == "Médio" else "🟢")
            with st.expander(f"{icon}  {r['title']}  ·  {r['project_name']}  ·  Nível {level}"):
                st.write(r["description"] or "Descrição não informada.")
                c1, c2, c3 = st.columns(3)
                c1.caption(f"**Probabilidade**\n\n{r['probability']}")
                c2.caption(f"**Impacto**\n\n{r['impact']}")
                c3.caption(f"**Situação**\n\n{r['status']}")
                st.markdown("**Plano de mitigação**")
                st.write(r["mitigation"] or "Nenhum plano registrado.")
                new_status = st.selectbox("Atualizar situação", RISK_STATUSES, index=RISK_STATUSES.index(r["status"]), key=f"risk_status_{r['id']}")
                if st.button("Salvar situação", key=f"save_risk_{r['id']}", type="primary"):
                    execute("UPDATE risks SET status=? WHERE id=?", (new_status, int(r["id"])))
                    st.rerun()
    else:
        st.info("Ainda não há riscos registrados para os projetos cadastrados.")

st.markdown("<div style='border-top:1px solid #e7ebf3;margin-top:35px;padding-top:16px;color:#9aa3b3;font-size:11px'>NEXO · SISTEMA DEMONSTRATIVO DE GESTÃO DE PROJETOS · Não utilize dados confidenciais de clientes.</div>", unsafe_allow_html=True)
