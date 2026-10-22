import sqlite3
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).with_name("projetos.db")

st.set_page_config(page_title="Acompanhamento de Projetos", page_icon="📊", layout="wide")

PURPLE = "#7C3AED"

def connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
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
    score = {"Baixa": 1, "Média": 2, "Alta": 3}[probability] * {"Baixo": 1, "Médio": 2, "Alto": 3}[impact]
    if score >= 6:
        return "Alto"
    if score >= 3:
        return "Médio"
    return "Baixo"

init_db()
st.markdown(f"""
<style>
.block-container {{padding-top: 2rem;}}
h1, h2, h3 {{color: {PURPLE};}}
div[data-testid="stMetric"] {{border: 1px solid #e5e7eb; padding: 14px; border-radius: 12px;}}
</style>
""", unsafe_allow_html=True)

st.title("📊 Acompanhamento de Projetos")
st.caption("Painel simples para acompanhar cronograma, progresso e riscos. Os dados ficam salvos localmente no arquivo projetos.db.")

projects = query("SELECT * FROM projects ORDER BY id DESC")
risks = query("""
    SELECT r.*, p.name AS project_name
    FROM risks r JOIN projects p ON p.id = r.project_id
    ORDER BY r.id DESC
""") if not projects.empty else pd.DataFrame()

tab_overview, tab_projects, tab_risks = st.tabs(["Visão geral", "Projetos", "Riscos"])

with tab_overview:
    total = len(projects)
    active = int(projects["status"].isin(["Em andamento", "Atenção"]).sum()) if total else 0
    completed = int((projects["status"] == "Concluído").sum()) if total else 0
    high_risks = int(sum(risk_level(r["probability"], r["impact"]) == "Alto" and r["status"] != "Resolvido" for _, r in risks.iterrows())) if not risks.empty else 0
    overdue = 0
    if total:
        today = date.today().isoformat()
        overdue = int(sum((row["end_date"] or "") < today and row["status"] != "Concluído" for _, row in projects.iterrows()))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total de projetos", total)
    c2.metric("Em andamento / atenção", active)
    c3.metric("Projetos atrasados", overdue)
    c4.metric("Riscos altos em aberto", high_risks)

    if projects.empty:
        st.info("Ainda não há projetos cadastrados. Acesse a aba **Projetos** para adicionar o primeiro.")
    else:
        st.subheader("Resumo dos projetos")
        view = projects[["name", "owner", "status", "progress", "start_date", "end_date"]].copy()
        view.columns = ["Projeto", "Responsável", "Status", "Progresso (%)", "Início", "Prazo"]
        st.dataframe(view, use_container_width=True, hide_index=True)
        st.subheader("Progresso")
        for _, project in projects.iterrows():
            st.write(f"**{project['name']}** — {project['progress']}%")
            st.progress(int(project["progress"]) / 100)

    if not risks.empty:
        st.subheader("Riscos que merecem atenção")
        open_risks = risks[risks["status"] != "Resolvido"].copy()
        if not open_risks.empty:
            open_risks["Nível"] = open_risks.apply(lambda r: risk_level(r["probability"], r["impact"]), axis=1)
            priority = {"Alto": 0, "Médio": 1, "Baixo": 2}
            open_risks["_sort"] = open_risks["Nível"].map(priority)
            open_risks = open_risks.sort_values("_sort")
            st.dataframe(open_risks[["project_name", "title", "Nível", "probability", "impact", "status"]].rename(columns={
                "project_name": "Projeto", "title": "Risco", "probability": "Probabilidade", "impact": "Impacto", "status": "Situação"
            }), use_container_width=True, hide_index=True)
        else:
            st.success("Todos os riscos cadastrados estão resolvidos.")

with tab_projects:
    st.subheader("Cadastrar novo projeto")
    with st.form("new_project", clear_on_submit=True):
        name = st.text_input("Nome do projeto *", placeholder="Ex.: Implantação de sistema CLM")
        col1, col2 = st.columns(2)
        owner = col1.text_input("Responsável")
        status = col2.selectbox("Status", ["Planejamento", "Em andamento", "Atenção", "Pausado", "Concluído"])
        col3, col4 = st.columns(2)
        start = col3.date_input("Data de início", value=date.today())
        end = col4.date_input("Prazo previsto", value=date.today())
        progress = st.slider("Progresso (%)", 0, 100, 0, step=5)
        description = st.text_area("Objetivo / observações")
        submitted = st.form_submit_button("Salvar projeto", type="primary")
        if submitted:
            if not name.strip():
                st.error("Informe o nome do projeto.")
            elif end < start:
                st.error("O prazo previsto não pode ser anterior à data de início.")
            else:
                execute("""INSERT INTO projects (name, owner, start_date, end_date, status, progress, description, created_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (name.strip(), owner.strip(), start.isoformat(), end.isoformat(), status, progress, description.strip(), datetime.now().isoformat(timespec="seconds")))
                st.success("Projeto cadastrado!")
                st.rerun()

    projects = query("SELECT * FROM projects ORDER BY id DESC")
    st.subheader("Projetos cadastrados")
    if projects.empty:
        st.caption("Seus projetos aparecerão aqui.")
    else:
        for _, p in projects.iterrows():
            with st.expander(f"{p['name']} · {p['status']} · {p['progress']}%"):
                with st.form(f"edit_project_{p['id']}"):
                    e_name = st.text_input("Nome", value=p["name"])
                    e_owner = st.text_input("Responsável", value=p["owner"] or "")
                    e_status = st.selectbox("Status", ["Planejamento", "Em andamento", "Atenção", "Pausado", "Concluído"], index=["Planejamento", "Em andamento", "Atenção", "Pausado", "Concluído"].index(p["status"]))
                    e_progress = st.slider("Progresso (%)", 0, 100, int(p["progress"]), step=5)
                    e_start = st.date_input("Início", value=date.fromisoformat(p["start_date"]) if p["start_date"] else date.today(), key=f"start_{p['id']}")
                    e_end = st.date_input("Prazo", value=date.fromisoformat(p["end_date"]) if p["end_date"] else date.today(), key=f"end_{p['id']}")
                    e_desc = st.text_area("Observações", value=p["description"] or "")
                    save = st.form_submit_button("Atualizar projeto")
                    if save:
                        if not e_name.strip() or e_end < e_start:
                            st.error("Confira o nome e as datas do projeto.")
                        else:
                            execute("""UPDATE projects SET name=?, owner=?, status=?, progress=?, start_date=?, end_date=?, description=? WHERE id=?""",
                                    (e_name.strip(), e_owner.strip(), e_status, e_progress, e_start.isoformat(), e_end.isoformat(), e_desc.strip(), int(p["id"])))
                            st.success("Projeto atualizado.")
                            st.rerun()
                if st.button("Excluir projeto", key=f"delete_{p['id']}"):
                    execute("DELETE FROM risks WHERE project_id=?", (int(p["id"]),))
                    execute("DELETE FROM projects WHERE id=?", (int(p["id"]),))
                    st.rerun()

with tab_risks:
    st.subheader("Registrar risco")
    projects = query("SELECT id, name FROM projects ORDER BY name")
    if projects.empty:
        st.info("Cadastre um projeto antes de registrar riscos.")
    else:
        project_options = {int(row["id"]): row["name"] for _, row in projects.iterrows()}
        with st.form("new_risk", clear_on_submit=True):
            project_id = st.selectbox("Projeto relacionado", options=list(project_options), format_func=lambda x: project_options[x])
            title = st.text_input("Nome do risco *", placeholder="Ex.: Ambiente de testes indisponível")
            description = st.text_area("Descrição / possível impacto")
            col1, col2 = st.columns(2)
            probability = col1.selectbox("Probabilidade", ["Baixa", "Média", "Alta"])
            impact = col2.selectbox("Impacto", ["Baixo", "Médio", "Alto"])
            mitigation = st.text_area("Plano de resposta / mitigação")
            risk_status = st.selectbox("Situação", ["Aberto", "Em tratamento", "Resolvido"])
            level = risk_level(probability, impact)
            st.info(f"Nível calculado automaticamente: **{level}**")
            add_risk = st.form_submit_button("Salvar risco", type="primary")
            if add_risk:
                if not title.strip():
                    st.error("Informe o nome do risco.")
                else:
                    execute("""INSERT INTO risks (project_id, title, description, probability, impact, mitigation, status, created_at)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                            (project_id, title.strip(), description.strip(), probability, impact, mitigation.strip(), risk_status, datetime.now().isoformat(timespec="seconds")))
                    st.success("Risco registrado.")
                    st.rerun()

    risks = query("""SELECT r.*, p.name AS project_name FROM risks r JOIN projects p ON p.id=r.project_id ORDER BY r.id DESC""")
    if not risks.empty:
        st.subheader("Registro de riscos")
        for _, r in risks.iterrows():
            level = risk_level(r["probability"], r["impact"])
            icon = "🔴" if level == "Alto" else ("🟠" if level == "Médio" else "🟢")
            with st.expander(f"{icon} {r['title']} · {r['project_name']} · Nível {level}"):
                st.write(f"**Descrição:** {r['description'] or 'Não informada'}")
                st.write(f"**Probabilidade:** {r['probability']}  |  **Impacto:** {r['impact']}  |  **Situação:** {r['status']}")
                st.write(f"**Plano de mitigação:** {r['mitigation'] or 'Não informado'}")
                new_status = st.selectbox("Atualizar situação", ["Aberto", "Em tratamento", "Resolvido"], index=["Aberto", "Em tratamento", "Resolvido"].index(r["status"]), key=f"risk_status_{r['id']}")
                if st.button("Salvar situação", key=f"save_risk_{r['id']}"):
                    execute("UPDATE risks SET status=? WHERE id=?", (new_status, int(r["id"])))
                    st.rerun()

st.divider()
st.caption("Protótipo de portfólio — os dados inseridos são salvos no computador/ambiente onde o app estiver rodando. Não inclua informações confidenciais de clientes.")
