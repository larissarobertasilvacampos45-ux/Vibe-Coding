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
RESET_PASSWORD_URL = "https://larissarobertasilvacampos45-ux.github.io/Vibe-Coding/reset-password.html"


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
    :root { color-scheme: light; }
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
      background: #f4f7fb !important; color: #172033 !important;
    }
    [data-testid="stMain"] .block-container { max-width: 980px; padding-top: 2rem; color: #172033 !important; }
    .login-shell { max-width: 590px; margin: 2vh auto 0; padding: 34px 40px;
      background: #ffffff; border: 1px solid #e1e8f2; border-radius: 24px;
      box-shadow: 0 18px 55px rgba(22,34,66,.07); }
    .login-brand { color: #1e3a5f !important; font-size: 34px; font-weight: 800;
      letter-spacing: -1.4px; margin-bottom: 4px; }
    .login-sub { color: #64748b !important; font-size: 14px; margin-bottom: 24px; }
    [data-testid="stMain"] h1, [data-testid="stMain"] h2, [data-testid="stMain"] h3,
    [data-testid="stMain"] p, [data-testid="stMain"] label,
    [data-testid="stMain"] [data-testid="stCaptionContainer"],
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] {
      color: #172033 !important;
    }
    [data-testid="stMain"] h1, [data-testid="stMain"] h2, [data-testid="stMain"] h3 {
      font-family: 'Manrope', 'DM Sans', sans-serif !important;
      font-weight: 800 !important;
    }
    [data-testid="stMain"] [data-testid="stWidgetLabel"] p { color: #475569 !important; }
    [data-testid="stMain"] input, [data-testid="stMain"] textarea,
    [data-testid="stMain"] [data-baseweb="input"] > div,
    [data-testid="stMain"] [data-baseweb="textarea"] > div {
      background: #ffffff !important; color: #172033 !important;
      border: 1px solid #cbd5e1 !important; border-radius: 10px !important;
    }
    [data-testid="stMain"] input::placeholder,
    [data-testid="stMain"] textarea::placeholder {
      color: #8491a5 !important; opacity: 1 !important;
    }
    [data-testid="stMain"] [data-testid="stForm"] {
      background: #ffffff !important; border: 1px solid #e1e8f2 !important;
      border-radius: 16px !important; padding: 20px !important;
    }
    [data-testid="stMain"] .stFormSubmitButton button,
    [data-testid="stMain"] button[kind="primary"] {
      background: #2563eb !important; color: #ffffff !important;
      border: 1px solid #2563eb !important; border-radius: 10px !important;
      min-height: 44px; font-weight: 700 !important;
    }
    [data-testid="stMain"] .stFormSubmitButton button:hover,
    [data-testid="stMain"] button[kind="primary"]:hover {
      background: #1d4ed8 !important; border-color: #1d4ed8 !important;
    }
    [data-testid="stMain"] a { color: #1d4ed8 !important; }
    @media (max-width: 768px) {
      .login-shell { margin: 0 auto; padding: 26px 22px; }
      [data-testid="stMain"] .block-container { padding: 1.2rem .8rem 2rem; }
    }
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
                            {"redirect_to": RESET_PASSWORD_URL},
                        )
                        st.success("Se a conta existir, você receberá as instruções de recuperação.")
                    except Exception:
                        st.error("Não foi possível solicitar a recuperação agora. Tente novamente mais tarde.")

        st.caption("Acesso restrito a usuários cadastrados pelo administrador.")
        st.stop()


supabase = get_supabase()

# A recuperação de senha acontece na página estática reset-password.html, que processa o fragmento do link padrão do Supabase.

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
:root { --ink:#172033; --muted:#758097; --line:#e8edf4; --blue:#3b82f6; --navy:#1e3a5f; --emerald:#10b981; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.stApp { background:#f6f8fc; color:var(--ink); }
.block-container { max-width:1440px; padding-top:1.7rem; padding-bottom:3rem; }
[data-testid="stSidebar"] { background:#111a2e; border-right:1px solid #202b43; }
[data-testid="stSidebar"] * { color:#e8edf8; }
[data-testid="stSidebar"] .stRadio label { padding:7px 10px; border-radius:9px; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#9eabc4; }
.brand { display:flex; align-items:center; gap:12px; padding:8px 4px 28px; }
.brand-mark { display:flex; align-items:center; justify-content:center; width:42px; height:42px; border-radius:13px; background:linear-gradient(135deg,#3b82f6,#10b981); color:white; font-size:25px; font-weight:800; }
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
.metric-card:before { content:''; position:absolute; top:0; left:0; height:3px; width:100%; background:#3b82f6; }
.metric-card.purple:before { background:#10b981; } .metric-card.orange:before { background:#f59e0b; } .metric-card.red:before { background:#ef4444; } .metric-card.green:before { background:#10b981; }
.metric-label { color:#7c879b; font-size:12px; font-weight:600; margin-bottom:13px; }
.metric-value { font-family:'Manrope',sans-serif; font-size:31px; font-weight:800; color:#172033; line-height:1.05; }
.metric-note { color:#9aa3b3; font-size:11px; margin-top:10px; }
.panel { background:#fff; border:1px solid #e9edf5; border-radius:16px; padding:20px 22px; box-shadow:0 3px 14px rgba(22,34,66,.025); }
.status-pill { display:inline-block; border-radius:20px; padding:5px 10px; font-size:11px; font-weight:700; white-space:nowrap; }
.planning { color:#596579; background:#eef1f6; } .active { color:#2563eb; background:#e8f0ff; }
.attention { color:#b45309; background:#fff1d6; } .paused { color:#6b7280; background:#f1f2f5; } .done { color:#047857; background:#dff8ed; }
/* Contraste explícito dos campos e rótulos no modo claro */
[data-testid="stMain"] [data-testid="stWidgetLabel"],
[data-testid="stMain"] [data-testid="stWidgetLabel"] p,
[data-testid="stMain"] [data-testid="stWidgetLabel"] label {
  color:#475569 !important;
}
[data-testid="stMain"] textarea,
[data-testid="stMain"] input,
[data-testid="stMain"] [data-baseweb="textarea"] > div,
[data-testid="stMain"] [data-baseweb="input"] > div {
  background:#ffffff !important;
  color:#172033 !important;
  -webkit-text-fill-color:#172033 !important;
  border-color:#cbd5e1 !important;
}
[data-testid="stMain"] textarea::placeholder,
[data-testid="stMain"] input::placeholder {
  color:#8491a5 !important;
  -webkit-text-fill-color:#8491a5 !important;
  opacity:1 !important;
}
.stButton > button:not([kind="primary"]) {
  background:#ffffff !important; color:#1e3a5f !important;
  border:1px solid #cbd5e1 !important;
}
.stButton > button:not([kind="primary"]):hover {
  background:#eff6ff !important; border-color:#93c5fd !important; color:#1d4ed8 !important;
}
.stButton > button { border-radius:9px; font-weight:650; min-height:40px; }
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] { background:#3b82f6; border-color:#3b82f6; }
div[data-testid="stForm"] { background:#fff; border:1px solid #e8edf4; border-radius:14px; padding:18px; }
div[data-testid="stExpander"] { background:#fff; border:1px solid #e8edf4; border-radius:12px; }
div[data-testid="stMetric"] { background:#fff; border:1px solid #e8edf4; padding:14px 16px; border-radius:12px; }
.stProgress > div > div > div > div { background:#10b981; }
hr { border-color:#e8edf4; }
.small-muted { color:#8a94a8; font-size:12px; }
.dashboard-hint { color:#7b8498; font-size:12px; padding:11px 0; }

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
        ["Visão Geral", "Projetos", "Riscos"],
        label_visibility="collapsed",
        key="navigation_page",
        format_func=lambda x: {"Visão Geral": "◫  Visão Geral", "Projetos": "▦  Projetos", "Riscos": "◇  Riscos e impedimentos"}[x],
    )
    st.markdown("<div class='sidebar-label'>Aparência</div>", unsafe_allow_html=True)
    st.toggle("🌙 Modo noturno", key="dark_mode", value=st.session_state.get("dark_mode", False))
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


if st.session_state.get("dark_mode", False):
    st.markdown("""
    <style>
    .stApp { background:#0f172a !important; color:#e2e8f0 !important; }
    [data-testid="stMain"] .block-container { color:#e2e8f0; }
    h1, h2, h3, h4, p, label, .stMarkdown, [data-testid="stCaptionContainer"] { color:#e2e8f0 !important; }
    .page-eyebrow { color:#60a5fa !important; }
    .page-subtitle, .small-muted, .metric-label, .metric-note { color:#a8b5c9 !important; }
    .metric-card, .panel, div[data-testid="stForm"], div[data-testid="stExpander"],
    div[data-testid="stMetric"], div[data-testid="stDataFrame"], [data-testid="stAlert"] {
      background:#1e293b !important; border-color:#334155 !important; color:#e2e8f0 !important;
    }
    .metric-value { color:#f8fafc !important; }
    input, textarea, [data-baseweb="select"] > div, [data-baseweb="popover"] {
      background:#111c31 !important; color:#f1f5f9 !important; border-color:#475569 !important;
    }
    .stButton > button:not([kind="primary"]) {
      background:#1e293b !important; color:#e2e8f0 !important; border-color:#475569 !important;
    }
    .stButton > button:not([kind="primary"]):hover {
      background:#334155 !important; color:#ffffff !important; border-color:#64748b !important;
    }
    [data-testid="stSidebar"] { background:#0b1220 !important; }
    [data-testid="stSidebar"] * { color:#e2e8f0; }
    hr { border-color:#334155 !important; }
    .planning { color:#cbd5e1 !important; background:#334155 !important; }
    .active { color:#bfdbfe !important; background:#1e3a5f !important; }
    .attention { color:#fde68a !important; background:#78350f !important; }
    .paused { color:#d1d5db !important; background:#374151 !important; }
    .done { color:#a7f3d0 !important; background:#064e3b !important; }
    </style>
    """, unsafe_allow_html=True)

projects = query("SELECT * FROM projects ORDER BY id DESC")
risks = query("""
    SELECT r.*, p.name AS project_name
    FROM risks r JOIN projects p ON p.id = r.project_id
    ORDER BY r.id DESC
""") if not projects.empty else pd.DataFrame()

# ---------- Visão geral / Dashboard executivo e operacional ----------
if page == "Visão Geral":
    st.markdown("<div class='page-eyebrow'>Workspace / Dashboard</div>", unsafe_allow_html=True)
    st.title("Visão Geral")
    st.markdown(
        "<p class='page-subtitle'>Acompanhe resultados, antecipe prazos e identifique as próximas ações do portfólio.</p>",
        unsafe_allow_html=True,
    )

    # Datas e métricas calculadas diretamente dos dados persistidos no Supabase.
    today_date = date.today()
    today = today_date.isoformat()
    total = len(projects)
    completed = int((projects["status"] == "Concluído").sum()) if total else 0
    active = int(projects["status"].isin(["Em andamento", "Atenção"]).sum()) if total else 0
    paused = int((projects["status"] == "Pausado").sum()) if total else 0
    high_risks = int(sum(
        risk_level(r["probability"], r["impact"]) == "Alto" and r["status"] != "Resolvido"
        for _, r in risks.iterrows()
    )) if not risks.empty else 0
    overdue_projects = projects[
        projects.apply(
            lambda row: bool(row.get("end_date"))
            and str(row.get("end_date"))[:10] < today
            and row.get("status") != "Concluído",
            axis=1,
        )
    ].copy() if total else projects.copy()
    overdue = len(overdue_projects)
    avg_progress = int(pd.to_numeric(projects["progress"], errors="coerce").fillna(0).mean()) if total else 0

    # Atalhos operacionais.
    action_a, action_b, action_c = st.columns([1, 1, 2])
    with action_a:
        st.button(
            "＋ Novo projeto",
            type="primary",
            use_container_width=True,
            on_click=lambda: st.session_state.update({"navigation_page": "Projetos"}),
        )
    with action_b:
        st.button(
            "＋ Registrar risco",
            use_container_width=True,
            on_click=lambda: st.session_state.update({"navigation_page": "Riscos"}),
        )
    with action_c:
        st.markdown(
            "<div class='dashboard-hint'>Visão executiva e operacional · Atualizado com os dados cadastrados</div>",
            unsafe_allow_html=True,
        )

    cols = st.columns(4)
    with cols[0]:
        metric_card("PROJETOS NO PORTFÓLIO", total, f"{completed} concluído(s)", "blue")
    with cols[1]:
        metric_card("EM ANDAMENTO", active, "Em execução ou atenção", "green")
    with cols[2]:
        metric_card("PROJETOS ATRASADOS", overdue, "Prazo vencido e não concluídos", "orange")
    with cols[3]:
        metric_card("RISCOS CRÍTICOS", high_risks, "Riscos altos ainda não resolvidos", "red")

    st.write("")
    # Gráfico em largura total para ganhar destaque e leitura.
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.subheader("Saúde do portfólio")
    st.markdown(
        "<p class='small-muted'>Distribuição dos projetos por status, com leitura ampliada.</p>",
        unsafe_allow_html=True,
    )
    if projects.empty:
        st.info("O gráfico aparecerá após o cadastro de projetos.")
    else:
        status_counts = projects["status"].value_counts().reindex(STATUSES, fill_value=0)
        chart_df = status_counts[status_counts > 0].rename_axis("Status").reset_index(name="Projetos")
        st.bar_chart(chart_df.set_index("Status"), use_container_width=True, height=320)
        chart_summary = st.columns([1, 1, 2])
        chart_summary[0].metric("Progresso médio", f"{avg_progress}%")
        chart_summary[1].metric("Concluídos", completed)
        with chart_summary[2]:
            st.markdown("<div class='dashboard-hint'>Use esta visão para identificar concentração de projetos por situação e acompanhar a evolução geral.</div>", unsafe_allow_html=True)
        st.progress(min(max(avg_progress, 0), 100) / 100)
    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    left, right = st.columns([1.45, 1], gap="large")
    with left:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("Portfólio de projetos")
        st.markdown(
            "<p class='small-muted'>Progresso, status e prazo das iniciativas prioritárias.</p>",
            unsafe_allow_html=True,
        )
        if projects.empty:
            st.info("Seu portfólio ainda está vazio. Use **Novo projeto** para cadastrar a primeira iniciativa.")
        else:
            portfolio = projects.copy()
            portfolio["_deadline"] = portfolio["end_date"].fillna("").astype(str)
            portfolio["_progress"] = pd.to_numeric(portfolio["progress"], errors="coerce").fillna(0)
            portfolio["_overdue"] = portfolio.apply(
                lambda row: bool(row["_deadline"])
                and row["_deadline"][:10] < today
                and row["status"] != "Concluído",
                axis=1,
            )
            portfolio = portfolio.sort_values(
                ["_overdue", "_deadline"], ascending=[False, True], na_position="last"
            ).head(7)
            for _, p in portfolio.iterrows():
                st.markdown(f"**{p['name']}**")
                detail_cols = st.columns([2, 1])
                with detail_cols[0]:
                    st.markdown(
                        f"<span class='status-pill {status_class(p['status'])}'>{p['status']}</span>",
                        unsafe_allow_html=True,
                    )
                    st.caption(f"Prazo: {fmt_date(p['end_date'])}")
                with detail_cols[1]:
                    st.markdown(
                        f"<div style='text-align:right;font-size:13px;font-weight:700;padding-top:3px'>{int(p['_progress'])}%</div>",
                        unsafe_allow_html=True,
                    )
                st.progress(min(max(float(p["_progress"]), 0), 100) / 100)
                st.markdown("<div style='height:5px'></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("Resumo operacional")
        st.markdown(
            "<p class='small-muted'>Indicadores complementares do portfólio.</p>",
            unsafe_allow_html=True,
        )
        summary_cols = st.columns(2)
        summary_cols[0].metric("Concluídos", completed)
        summary_cols[1].metric("Pausados", paused)
        summary_cols[0].metric("Progresso médio", f"{avg_progress}%")
        summary_cols[1].metric("Riscos críticos", high_risks)
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    deadline_col, alert_col = st.columns([1.15, 1], gap="large")
    with deadline_col:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("Agendas e entregas")
        if st.button("＋ Cadastrar agenda ou entrega", key="dashboard_add_agenda", use_container_width=True):
            st.session_state["navigation_page"] = "Projetos"
            st.rerun()
        st.markdown(
            "<p class='small-muted'>Prazos vencidos e entregas previstas para os próximos 14 dias.</p>",
            unsafe_allow_html=True,
        )
        if projects.empty:
            st.info("Cadastre projetos para acompanhar os próximos prazos.")
        else:
            deadlines = projects.copy()
            deadlines["_date"] = pd.to_datetime(deadlines["end_date"], errors="coerce").dt.date
            deadlines = deadlines[
                deadlines["_date"].notna()
                & (deadlines["_date"] <= today_date + pd.Timedelta(days=14))
                & (deadlines["status"] != "Concluído")
            ].copy()
            if deadlines.empty:
                st.success("Nenhum prazo vencido ou previsto para os próximos 14 dias.")
            else:
                deadlines["_late"] = deadlines["_date"] < today_date
                deadlines = deadlines.sort_values(["_late", "_date"], ascending=[False, True]).head(8)
                for _, p in deadlines.iterrows():
                    days_left = (p["_date"] - today_date).days
                    if days_left < 0:
                        urgency = f"ATRASADO · {abs(days_left)} dia(s)"
                        st.error(f"**{p['name']}** · {fmt_date(p['end_date'])}\n\n{urgency}")
                    elif days_left == 0:
                        st.warning(f"**{p['name']}** · vence hoje")
                    else:
                        st.info(f"**{p['name']}** · {fmt_date(p['end_date'])} · em {days_left} dia(s)")
        st.markdown("</div>", unsafe_allow_html=True)

    with alert_col:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("Alertas e prioridades")
        st.markdown(
            "<p class='small-muted'>Itens que podem exigir acompanhamento ou uma decisão.</p>",
            unsafe_allow_html=True,
        )
        alert_count = 0
        if overdue:
            st.error(f"{overdue} projeto(s) com prazo vencido. Revise o cronograma e os próximos passos.")
            alert_count += 1
        if high_risks:
            st.warning(f"{high_risks} risco(s) alto(s) sem resolução. Verifique o plano de mitigação.")
            alert_count += 1
        if paused:
            st.info(f"{paused} projeto(s) pausado(s). Avalie os impedimentos e as condições para retomada.")
            alert_count += 1
        if total:
            due_soon_count = int(sum(
                bool(row.get("end_date"))
                and today_date <= date.fromisoformat(str(row.get("end_date"))[:10]) <= today_date + pd.Timedelta(days=7)
                and row.get("status") != "Concluído"
                for _, row in projects.iterrows()
            ))
            if due_soon_count:
                st.warning(f"{due_soon_count} projeto(s) vencem nos próximos 7 dias. Confirme o plano de entrega.")
                alert_count += 1
        if alert_count == 0:
            st.success("Nenhum alerta identificado com os dados atuais. Continue acompanhando os prazos e riscos.")
        st.markdown("</div>", unsafe_allow_html=True)

# ---------- Projetos ----------
elif page == "Projetos":
    st.markdown("<div class='page-eyebrow'>Workspace / Gestão</div>", unsafe_allow_html=True)
    st.title("Projetos")
    st.markdown("<p class='page-subtitle'>Cadastre iniciativas, mantenha os dados atualizados e acompanhe a evolução das entregas.</p>", unsafe_allow_html=True)

    with st.expander("＋  Cadastrar novo projeto", expanded=projects.empty):
        with st.form("new_project", clear_on_submit=True):
            name = st.text_input("Nome do projeto *", placeholder="Ex.: Implantação de sistema de gestão")
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
