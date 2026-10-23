from datetime import date, datetime

import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(
    page_title="Nexo | Gestão de Projetos",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

STATUSES = ["Planejamento", "Em andamento", "Atenção", "Pausado", "Concluído"]
RISK_STATUSES = ["Aberto", "Em tratamento", "Resolvido"]
APP_URL = "https://larissarobertasilvacampos45-ux-vibe-coding-app-zfk4fm.streamlit.app/"


def get_supabase():
    """Cria um cliente Supabase por sessão usando apenas a chave pública."""
    try:
        config = st.secrets["supabase"]
        url = config["url"]
        anon_key = config["anon_key"]
    except Exception:
        st.error(
            "Configure os Secrets do Streamlit: [supabase], url e anon_key. "
            "Não use a chave service_role nesta aplicação."
        )
        st.stop()

    if "supabase_client" not in st.session_state:
        st.session_state.supabase_client = create_client(url, anon_key)

    client = st.session_state.supabase_client
    access_token = st.session_state.get("access_token")
    refresh_token = st.session_state.get("refresh_token")
    if access_token and refresh_token:
        try:
            client.auth.set_session(access_token, refresh_token)
        except Exception:
            for key in ("auth_user", "access_token", "refresh_token"):
                st.session_state.pop(key, None)
    return client


def render_login(client):
    """Tela pública de autenticação; não carrega dados privados antes do login."""
    st.markdown("""
    <style>
    .stApp { background: #f5f7fc; }
    .login-shell { max-width: 470px; margin: 5vh auto 0; padding: 34px 36px;
      background: white; border: 1px solid #e7ebf4; border-radius: 22px;
      box-shadow: 0 18px 55px rgba(22,34,66,.08); }
    .login-brand { color: #6d42a1; font-size: 34px; font-weight: 800;
      letter-spacing: -1.4px; margin-bottom: 4px; }
    .login-sub { color: #7b8498; font-size: 14px; margin-bottom: 24px; }
    </style>
    <div class="login-shell">
      <div class="login-brand">◈ nexo</div>
      <div class="login-sub">Project workspace · Acesse seu espaço de trabalho</div>
    </div>
    """, unsafe_allow_html=True)

    left, center, right = st.columns([1, 1.25, 1])
    with center:
        if st.session_state.pop("password_reset_success", False):
            st.success("Senha alterada com sucesso. Entre com sua nova senha.")
        st.subheader("Entrar na sua conta")
        st.caption("Use o e-mail e a senha cadastrados no Nexo.")
        with st.form("nexo_login"):
            email = st.text_input("E-mail", placeholder="voce@exemplo.com")
            password = st.text_input("Senha", type="password", placeholder="Sua senha")
            submitted = st.form_submit_button("Entrar", type="primary", use_container_width=True)
        if submitted:
            if not email.strip() or not password:
                st.error("Informe seu e-mail e sua senha.")
            else:
                try:
                    result = client.auth.sign_in_with_password({
                        "email": email.strip(),
                        "password": password,
                    })
                    if not result.session or not result.user:
                        st.error("Não foi possível iniciar a sessão. Confira suas credenciais.")
                    else:
                        st.session_state.auth_user = {
                            "id": result.user.id,
                            "email": result.user.email or email.strip(),
                        }
                        st.session_state.access_token = result.session.access_token
                        st.session_state.refresh_token = result.session.refresh_token
                        st.rerun()
                except Exception:
                    st.error("Não foi possível entrar. Confira o e-mail e a senha e tente novamente.")

        with st.expander("Esqueci minha senha"):
            with st.form("nexo_password_reset"):
                reset_email = st.text_input("E-mail da conta", key="reset_email")
                reset_submitted = st.form_submit_button("Enviar instruções")
            if reset_submitted:
                if not reset_email.strip():
                    st.warning("Informe o e-mail da sua conta.")
                else:
                    try:
                        client.auth.reset_password_for_email(
                            reset_email.strip(),
                            {"redirect_to": APP_URL},
                        )
                        st.success("Se a conta existir, você receberá as instruções de recuperação.")
                    except Exception:
                        st.error("Não foi possível solicitar a recuperação agora. Tente novamente mais tarde.")

        st.caption("Acesso restrito a usuários cadastrados pelo administrador.")
        st.stop()


supabase = get_supabase()

# ---------- Recuperação de senha via link de e-mail ----------
# O template de recuperação do Supabase deve enviar token_hash e type=recovery
# diretamente para a URL do Streamlit, pois o Streamlit não lê fragmentos (#) da URL.
if (
    st.query_params.get("token_hash")
    and st.query_params.get("type") == "recovery"
    and not st.session_state.get("password_recovery_mode")
):
    try:
        verified = supabase.auth.verify_otp({
            "token_hash": st.query_params.get("token_hash"),
            "type": "recovery",
        })
        if verified.session and verified.user:
            st.session_state.auth_user = {
                "id": verified.user.id,
                "email": verified.user.email or "",
            }
            st.session_state.access_token = verified.session.access_token
            st.session_state.refresh_token = verified.session.refresh_token
            st.session_state.password_recovery_mode = True
            st.query_params.clear()
            st.rerun()
        else:
            st.error("O link de recuperação é inválido ou expirou. Solicite um novo link.")
            st.query_params.clear()
    except Exception:
        st.error("Não foi possível validar o link. Solicite uma nova recuperação de senha.")
        st.query_params.clear()

if st.session_state.get("password_recovery_mode"):
    st.markdown("## Criar nova senha")
    st.caption("Escolha uma senha nova para sua conta Nexo.")
    with st.form("nexo_set_new_password"):
        new_password = st.text_input("Nova senha", type="password")
        confirm_password = st.text_input("Confirme a nova senha", type="password")
        save_password = st.form_submit_button("Salvar nova senha", type="primary", use_container_width=True)
    if save_password:
        if len(new_password) < 8:
            st.error("Use uma senha com pelo menos 8 caracteres.")
        elif new_password != confirm_password:
            st.error("As senhas não coincidem.")
        else:
            try:
                supabase.auth.update_user({"password": new_password})
                try:
                    supabase.auth.sign_out()
                except Exception:
                    pass
                for key in ("auth_user", "access_token", "refresh_token", "password_recovery_mode"):
                    st.session_state.pop(key, None)
                st.session_state.password_reset_success = True
                st.rerun()
            except Exception:
                st.error("Não foi possível alterar a senha. Solicite um novo link e tente novamente.")
    st.stop()

if not st.session_state.get("auth_user"):
    render_login(supabase)

# ---------- Persistência na nuvem (Supabase) ----------
def query(sql, params=()):
    """Mantém a interface usada pela tela e consulta as tabelas do Supabase."""
    normalized = " ".join(sql.lower().split())
    if "from projects" in normalized and "join risks" not in normalized and "from risks" not in normalized:
        response = supabase.table("projects").select("*").order("created_at", desc=True).execute()
        rows = response.data or []
        if "select id, name from projects" in normalized:
            rows = sorted(rows, key=lambda row: (row.get("name") or "").lower())
            rows = [{"id": row.get("id"), "name": row.get("name")} for row in rows]
        return pd.DataFrame(rows)
    if "from risks" in normalized:
        risks_response = supabase.table("risks").select("*").order("created_at", desc=True).execute()
        projects_response = supabase.table("projects").select("id,name").execute()
        names = {str(row["id"]): row.get("name", "") for row in (projects_response.data or [])}
        rows = []
        for risk in risks_response.data or []:
            project_name = names.get(str(risk.get("project_id")), "")
            if "join projects" in normalized and not project_name:
                continue
            rows.append({**risk, "project_name": project_name})
        return pd.DataFrame(rows)
    raise ValueError(f"Consulta não suportada pelo adaptador Supabase: {sql}")


def execute(sql, params=()):
    """Traduz as operações usadas pela interface para chamadas Supabase."""
    normalized = " ".join(sql.lower().split())
    now = datetime.now().isoformat(timespec="seconds")
    if normalized.startswith("insert into projects"):
        name, owner, start_date, end_date, status, progress, description, created_at = params
        supabase.table("projects").insert({
            "name": name, "owner": owner or None,
            "owner_id": st.session_state.auth_user["id"],
            "start_date": start_date, "end_date": end_date,
            "due_date": end_date, "status": status, "progress": progress,
            "description": description or None, "created_at": created_at,
            "updated_at": now,
        }).execute()
        return
    if normalized.startswith("update projects set"):
        name, owner, status, progress, start_date, end_date, description, project_id = params
        supabase.table("projects").update({
            "name": name, "owner": owner or None, "status": status,
            "progress": progress, "start_date": start_date,
            "end_date": end_date, "due_date": end_date,
            "description": description or None, "updated_at": now,
        }).eq("id", str(project_id)).execute()
        return
    if normalized.startswith("delete from risks"):
        supabase.table("risks").delete().eq("project_id", str(params[0])).execute()
        return
    if normalized.startswith("delete from projects"):
        supabase.table("projects").delete().eq("id", str(params[0])).execute()
        return
    if normalized.startswith("insert into risks"):
        project_id, title, description, probability, impact, mitigation, status, created_at = params
        supabase.table("risks").insert({
            "project_id": str(project_id), "title": title,
            "description": description or None, "probability": probability,
            "impact": impact, "mitigation": mitigation or None,
            "status": status, "created_at": created_at, "updated_at": now,
        }).execute()
        return
    if normalized.startswith("update risks set status"):
        status, risk_id = params
        supabase.table("risks").update({
            "status": status, "updated_at": now
        }).eq("id", str(risk_id)).execute()
        return
    raise ValueError(f"Operação não suportada pelo adaptador Supabase: {sql}")


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
    st.caption(f"Conectada: {st.session_state.auth_user.get('email', '')}")
    if st.button("Sair da conta", use_container_width=True):
        try:
            supabase.auth.sign_out()
        finally:
            for key in ("auth_user", "access_token", "refresh_token"):
                st.session_state.pop(key, None)
            st.rerun()

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
        filtered = filtered[filtered["name"].str.contains(search, case=False, na=False) | filtered["owner"].fillna("").str.contains(search, case=False, na=False)]
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
                                    (e_name.strip(), e_owner.strip(), e_status, e_progress, e_start.isoformat(), e_end.isoformat(), e_desc.strip(), str(p["id"])))
                            st.success("Projeto atualizado.")
                            st.rerun()
                confirm_delete = st.checkbox("Confirmo que desejo excluir este projeto", key=f"confirm_delete_{p['id']}")
                if st.button("Excluir projeto", key=f"delete_{p['id']}", disabled=not confirm_delete):
                    execute("DELETE FROM risks WHERE project_id=?", (str(p["id"]),))
                    execute("DELETE FROM projects WHERE id=?", (str(p["id"]),))
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
            project_options = {str(row["id"]): row["name"] for _, row in projects.iterrows()}
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
                    execute("UPDATE risks SET status=? WHERE id=?", (new_status, str(r["id"])))
                    st.rerun()
    else:
        st.info("Ainda não há riscos registrados para os projetos cadastrados.")

st.markdown("<div style='border-top:1px solid #e7ebf3;margin-top:35px;padding-top:16px;color:#9aa3b3;font-size:11px'>NEXO · SISTEMA DEMONSTRATIVO DE GESTÃO DE PROJETOS · Não utilize dados confidenciais de clientes.</div>", unsafe_allow_html=True)
