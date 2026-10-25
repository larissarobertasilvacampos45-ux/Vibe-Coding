from datetime import date, datetime
from html import escape

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
:root { --ink:#172133; --muted:#5e6e85; --line:#dee5f0; --blue:#2563eb; --navy:#132541; --emerald:#14997a; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.stApp { background:#f3f7fc; color:var(--ink); }
header[data-testid="stHeader"] { background:transparent !important; }
[data-testid="stSidebar"] { width:252px !important; min-width:252px !important; background:#132541 !important; border-right:1px solid #203553; }
[data-testid="stSidebar"] > div { width:252px !important; }
[data-testid="stSidebar"] * { color:#bacfe8; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#b8cce5; }
[data-testid="stSidebar"] .stRadio label { padding:7px 10px; border-radius:9px; }
[data-testid="stSidebar"] [data-testid="stRadio"] > label { display:none; }
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] { gap:7px; }
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label { min-height:42px; padding:10px 12px; border-radius:10px; }
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) { background:#17365c; border-left:3px solid #14997a; }
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label p { font-size:13px; color:#bacfe8; }
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) p { color:#ffffff; font-weight:700; }
.brand { display:flex; align-items:center; gap:12px; padding:8px 4px 28px; }
.brand-mark { display:flex; align-items:center; justify-content:center; width:42px; height:42px; border-radius:13px; background:#14997a; color:white !important; font-size:25px; font-weight:800; }
.brand-name { color:#fff !important; font-family:'DM Sans',sans-serif; font-size:25px; font-weight:800; letter-spacing:-.7px; }
.brand-sub { color:#adc9eb !important; font-size:10px; letter-spacing:1.6px; text-transform:uppercase; margin-top:1px; }
.sidebar-label { color:#8ca8cc !important; font-size:10px; letter-spacing:1.5px; font-weight:700; text-transform:uppercase; margin:12px 0 8px; }
h1, h2, h3 { font-family:'DM Sans',sans-serif !important; color:#172133 !important; letter-spacing:-.4px; }
h1 { font-size:30px !important; font-weight:800 !important; margin-bottom:2px !important; }
h2 { font-size:18px !important; font-weight:700 !important; }
h3 { font-size:16px !important; font-weight:700 !important; }
.page-eyebrow { color:#2563eb; text-transform:uppercase; letter-spacing:1.8px; font-size:10px; font-weight:800; margin-bottom:7px; }
.page-subtitle { color:#5e6e85; font-size:14px; margin:0 0 22px; }
.metric-card { background:#fff; border:1px solid #dee5f0; border-radius:16px; padding:19px 20px; min-height:140px; box-shadow:0 5px 18px rgba(31,56,92,.08); position:relative; overflow:hidden; }
.metric-card:before { content:''; position:absolute; top:0; left:0; height:4px; width:100%; background:#2563eb; }
.metric-card.green:before { background:#14997a; } .metric-card.orange:before { background:#c76e14; } .metric-card.red:before { background:#c73840; }
.metric-label { color:#5e6e85; font-size:10px; font-weight:700; margin-bottom:13px; letter-spacing:.2px; }
.metric-value { font-family:'Manrope',sans-serif; font-size:31px; font-weight:800; color:#172133; line-height:1.05; }
.metric-note { color:#5e6e85; font-size:11px; margin-top:10px; }
.panel { background:#fff; border:1px solid #dee5f0; border-radius:16px; padding:20px 22px; box-shadow:0 5px 18px rgba(31,56,92,.08); }
.status-pill { display:inline-block; border-radius:20px; padding:5px 10px; font-size:11px; font-weight:700; white-space:nowrap; }
.planning { color:#596579; background:#eef1f6; } .active { color:#2563eb; background:#e8f0ff; }
.attention { color:#b45309; background:#fff1d6; } .paused { color:#6b7280; background:#f1f2f5; } .done { color:#047857; background:#dff8ed; }
[data-testid="stMain"] [data-testid="stWidgetLabel"], [data-testid="stMain"] [data-testid="stWidgetLabel"] p { color:#475569 !important; }
[data-testid="stMain"] textarea, [data-testid="stMain"] input, [data-testid="stMain"] [data-baseweb="textarea"] > div, [data-testid="stMain"] [data-baseweb="input"] > div {
  background:#ffffff !important; color:#172033 !important; -webkit-text-fill-color:#172033 !important; border-color:#cbd5e1 !important;
}
[data-testid="stMain"] textarea::placeholder, [data-testid="stMain"] input::placeholder { color:#8491a5 !important; -webkit-text-fill-color:#8491a5 !important; opacity:1 !important; }
.stButton > button:not([kind="primary"]) { background:#ffffff !important; color:#132541 !important; border:1px solid #dee5f0 !important; }
.stButton > button:not([kind="primary"]):hover { background:#eff6ff !important; border-color:#93c5fd !important; color:#1d4ed8 !important; }
.stButton > button { border-radius:10px; font-weight:650; min-height:44px; }
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] { background:#2563eb !important; color:#ffffff !important; border-color:#2563eb !important; }
div[data-testid="stForm"] { background:#fff; border:1px solid #dee5f0; border-radius:14px; padding:18px; }
div[data-testid="stExpander"] { background:#fff; border:1px solid #dee5f0; border-radius:12px; }
div[data-testid="stMetric"] { background:#fff; border:1px solid #dee5f0; padding:14px 16px; border-radius:12px; }
.stProgress > div > div > div > div { background:#14997a; }
hr { border-color:#dee5f0; }
.small-muted { color:#5e6e85; font-size:12px; }
.dashboard-hint { color:#5e6e85; font-size:11px; padding:11px 0; }
div[data-testid="stDataFrame"] { border:1px solid #dee5f0; border-radius:12px; overflow:hidden; }

/* Página Visão Geral: dimensões, hierarquia e componentes alinhados ao frame Figma 1440×1024. */
.block-container:has(.nexo-dashboard) {
  width:calc(100% - 52px) !important; max-width:none !important;
  margin-left:40px !important; margin-right:auto !important;
  padding-top:2.1rem !important; padding-bottom:1.8rem !important;
}
.nexo-dashboard { display:none; }
.block-container:has(.nexo-dashboard) .stMarkdown:has(.nexo-dashboard) { display:none; }
.block-container:has(.nexo-dashboard) h1.nexo-page-title { font-size:34px !important; line-height:1.2; margin:0 0 7px !important; color:#172133 !important; }
.nexo-page-subtitle { color:#5e6e85 !important; font-size:15px; margin:0 !important; line-height:1.45; }
.nexo-header-tools { display:flex; align-items:center; justify-content:flex-end; gap:12px; padding-top:2px; }
.nexo-notification,.nexo-avatar { display:inline-flex; align-items:center; justify-content:center; width:40px; height:40px; border-radius:12px; background:#fff; border:1px solid #dee5f0; color:#132541 !important; font-size:18px; }
.nexo-avatar { width:44px; height:44px; border-radius:22px; font-size:13px; font-weight:800; }
.nexo-updated-label { color:#5e6e85; font-size:11px; letter-spacing:.25px; padding:14px 0; white-space:nowrap; }
.block-container:has(.nexo-dashboard) [data-testid="stHorizontalBlock"] { gap:12px; }
.block-container:has(.nexo-dashboard) .stButton > button { height:44px; min-height:44px; }
.nexo-kpi-grid { display:grid; grid-template-columns:repeat(4, minmax(0,252px)); gap:20px; margin:20px 0 20px; }
.nexo-kpi { height:140px; box-sizing:border-box; position:relative; background:#fff; border:1px solid #dee5f0; border-radius:16px; box-shadow:0 5px 18px rgba(31,56,92,.08); padding:18px 17px; overflow:hidden; }
.nexo-kpi-accent { position:absolute; top:0; left:0; right:0; height:4px; background:#2563eb; }
.nexo-kpi-green .nexo-kpi-accent { background:#14997a; } .nexo-kpi-orange .nexo-kpi-accent { background:#c76e14; } .nexo-kpi-red .nexo-kpi-accent { background:#c73840; }
.nexo-kpi-label { color:#5e6e85; font-size:10px; font-weight:700; line-height:1.3; letter-spacing:.2px; }
.nexo-kpi-value { color:#172133; font-family:'DM Sans',sans-serif; font-size:31px; font-weight:800; line-height:1; margin-top:13px; }
.nexo-kpi-icon { position:absolute; top:39px; right:17px; width:30px; height:30px; border-radius:9px; display:flex; align-items:center; justify-content:center; background:#f0f5fc; color:#2563eb; font-size:15px; font-weight:700; }
.nexo-kpi-green .nexo-kpi-icon { color:#14997a; } .nexo-kpi-orange .nexo-kpi-icon { color:#c76e14; } .nexo-kpi-red .nexo-kpi-icon { color:#c73840; }
.nexo-kpi-note { position:absolute; left:17px; bottom:17px; color:#5e6e85; font-size:11px; line-height:1.25; }
.nexo-dashboard-stack { display:flex; flex-direction:column; gap:18px; }
.nexo-panel { box-sizing:border-box; width:100%; background:#fff; border:1px solid #dee5f0; border-radius:16px; box-shadow:0 5px 18px rgba(31,56,92,.08); padding:20px 21px; color:#172133; overflow:hidden; }
.nexo-panel h2 { color:#172133 !important; font-size:18px !important; margin:0 0 5px !important; line-height:1.3; }
.nexo-panel p { color:#5e6e85; margin:0; font-size:12px; line-height:1.4; }
.nexo-panel-heading { display:flex; justify-content:space-between; align-items:flex-start; gap:12px; }
.nexo-period-pill { flex-shrink:0; background:#e3f0ff; color:#2563eb; border-radius:13px; padding:6px 10px; font-size:10px; font-weight:700; letter-spacing:.2px; }
.nexo-panel-divider { height:1px; background:#dee5f0; margin:16px 0 12px; }
.nexo-chart-panel { height:310px; }
.nexo-chart-bars { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:20px; padding:0 10px; }
.nexo-chart-item { min-width:0; }
.nexo-chart-count { color:#5e6e85; font-size:12px; font-weight:700; margin-bottom:6px; }
.nexo-chart-track { height:126px; background:#f0f5fa; border-radius:8px; display:flex; align-items:flex-end; overflow:hidden; }
.nexo-chart-fill { width:100%; min-height:0; border-radius:8px 8px 0 0; }
.nexo-chart-label { color:#5e6e85; text-align:center; font-size:10px; line-height:1.25; margin-top:9px; overflow-wrap:anywhere; }
.nexo-chart-insight { border-top:1px solid #edf1f7; color:#5e6e85; font-size:11px; margin-top:13px; padding-top:8px; }
.nexo-progress-panel { height:146px; position:relative; }
.nexo-progress-number { color:#172133; font-size:31px; font-weight:800; line-height:1; margin-top:12px; }
.nexo-progress-trend { position:absolute; top:56px; right:20px; border-radius:13px; padding:6px 10px; background:#e2f8ef; color:#087a60; font-size:10px; font-weight:700; }
.nexo-progress-panel p { margin-top:4px; font-size:11px; }
.nexo-progress-track { height:8px; background:#e7edf5; border-radius:99px; margin-top:10px; overflow:hidden; }
.nexo-progress-fill { height:100%; background:#14997a; border-radius:99px; }
.nexo-agenda-panel { height:248px; }
.nexo-panel-subtitle { margin-bottom:12px !important; }
.nexo-agenda-list { margin-top:13px; }
.nexo-agenda-row { display:flex; align-items:center; gap:12px; padding:8px 0; border-bottom:1px solid #edf1f7; min-height:48px; }
.nexo-agenda-row:last-child { border-bottom:0; }
.nexo-date-tile { flex-shrink:0; width:48px; height:42px; border-radius:8px; background:#e3f0ff; color:#2563eb; display:flex; flex-direction:column; align-items:center; justify-content:center; }
.nexo-date-tile strong { font-size:16px; line-height:1.05; }
.nexo-date-tile span { font-size:9px; font-weight:700; letter-spacing:.5px; }
.nexo-date-tile.is-overdue { background:#fff0ef; color:#c73840; } .nexo-date-tile.is-today { background:#fff6e5; color:#a85a08; }
.nexo-agenda-copy { min-width:0; display:flex; flex-direction:column; gap:5px; }
.nexo-agenda-copy strong { color:#172133; font-size:12px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.nexo-agenda-copy span { color:#5e6e85; font-size:10px; }
.nexo-empty-state { color:#5e6e85; background:#f7f9fc; border-radius:10px; padding:16px; font-size:12px; line-height:1.5; margin-top:14px; }
.nexo-alerts-panel { height:280px; }
.nexo-alert-row { display:flex; align-items:center; gap:12px; padding:12px 0; border-bottom:1px solid #edf1f7; min-height:52px; }
.nexo-alert-row:last-child { border-bottom:0; }
.nexo-alert-icon { flex-shrink:0; width:38px; height:38px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:16px; font-weight:800; background:#e3f0ff; color:#2563eb; }
.nexo-alert-red { background:#fff0ef; color:#c73840; } .nexo-alert-orange { background:#fff5e7; color:#b65e0b; } .nexo-alert-green { background:#e2f8ef; color:#087a60; }
.nexo-alert-copy { display:flex; flex-direction:column; gap:4px; min-width:0; flex:1; }
.nexo-alert-copy strong { color:#172133; font-size:12px; }
.nexo-alert-copy span { color:#5e6e85; font-size:10px; }
.nexo-priority { flex-shrink:0; border-radius:13px; padding:6px 9px; font-size:9px; font-weight:700; letter-spacing:.2px; background:#e3f0ff; color:#2563eb; }
.nexo-priority-red { background:#fff0ef; color:#c73840; } .nexo-priority-orange { background:#fff5e7; color:#b65e0b; } .nexo-priority-green { background:#e2f8ef; color:#087a60; }
.nexo-alert-footer { color:#5e6e85; font-size:10px; margin-top:12px; }
@media (max-width:1100px) {
  .nexo-kpi-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }
  .nexo-chart-panel,.nexo-alerts-panel,.nexo-progress-panel,.nexo-agenda-panel { height:auto; min-height:unset; }
  .nexo-chart-bars { gap:12px; }
  .nexo-updated-label { white-space:normal; }
}
@media (max-width:768px) {
  [data-testid="stSidebar"] { width:280px !important; min-width:280px !important; }
  .block-container:has(.nexo-dashboard) { width:calc(100% - 28px) !important; margin-left:14px !important; padding-top:1.2rem !important; }
  .nexo-kpi-grid { grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; }
  .nexo-kpi { padding:14px 12px; }
  .nexo-kpi-label { font-size:9px; }
  .nexo-kpi-icon { right:10px; top:38px; }
  .nexo-kpi-note { left:12px; bottom:12px; font-size:10px; }
  .nexo-panel { padding:16px; }
  .nexo-chart-bars { gap:8px; padding:0; }
  .nexo-chart-label { font-size:9px; }
  .nexo-alert-row { flex-wrap:wrap; }
  .nexo-priority { margin-left:50px; }
}
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
        ["Visão Geral", "Projetos", "Riscos", "Agendas e entregas"],
        label_visibility="collapsed",
        key="navigation_page",
        format_func=lambda x: {"Visão Geral": "▦  Visão Geral", "Projetos": "▤  Projetos", "Riscos": "◇  Riscos e impedimentos", "Agendas e entregas": "◷  Agendas e entregas"}[x],
    )
    st.markdown("<div class='sidebar-label'>Preferências</div>", unsafe_allow_html=True)
    st.toggle("🌙 Modo noturno", key="dark_mode", value=st.session_state.get("dark_mode", False))
    st.markdown("<br><div class='sidebar-label'>Sobre o Nexo</div>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:12px;line-height:1.6'>Organize entregas, acompanhe prazos e dê visibilidade aos riscos do projeto.</p>", unsafe_allow_html=True)
    st.markdown("<br><div style='border-top:1px solid #29344b;padding-top:15px;color:#8492ad;font-size:11px'>NEXO · GESTÃO DE PROJETOS<br>Workspace de projetos</div>", unsafe_allow_html=True)
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
    .page-subtitle, .small-muted, .metric-label, .metric-note { color:#c0ccdd !important; }
    .metric-card, .panel, div[data-testid="stForm"], div[data-testid="stExpander"],
    [data-testid="stVerticalBlockBorderWrapper"], div[data-testid="stMetric"], div[data-testid="stDataFrame"], [data-testid="stAlert"] {
      background:#1e293b !important; border-color:#334155 !important; color:#e2e8f0 !important;
    }
    .metric-value { color:#f8fafc !important; }
[data-testid="stVerticalBlockBorderWrapper"] h2, [data-testid="stVerticalBlockBorderWrapper"] h3, [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetricValue"] { color:#f8fafc !important; }
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
    .nexo-panel, .nexo-kpi { background:#1e293b !important; border-color:#334155 !important; }
    .nexo-panel h2, .nexo-kpi-value, .nexo-agenda-copy strong, .nexo-alert-copy strong { color:#f8fafc !important; }
    .nexo-panel p, .nexo-page-subtitle, .nexo-kpi-label, .nexo-kpi-note, .nexo-chart-count, .nexo-chart-label, .nexo-chart-insight, .nexo-agenda-copy span, .nexo-alert-copy span, .nexo-alert-footer { color:#cbd5e1 !important; }
    .nexo-chart-track, .nexo-progress-track { background:#334155 !important; }
    .nexo-notification, .nexo-avatar { background:#1e293b !important; color:#f8fafc !important; border-color:#475569 !important; }
    .nexo-date-tile, .nexo-kpi-icon { background:#253a58 !important; }
    .nexo-agenda-row, .nexo-alert-row, .nexo-chart-insight, .nexo-panel-divider { border-color:#334155 !important; }
    .nexo-empty-state { background:#111c31 !important; color:#cbd5e1 !important; }
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


# ---------- Visão Geral / Dashboard executivo e operacional ----------
if page == "Visão Geral":
    import html

    # Valores calculados a partir dos registros reais do Supabase.
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
    avg_progress = int(
        pd.to_numeric(projects["progress"], errors="coerce").fillna(0).mean()
    ) if total else 0

    # Cabeçalho e perfil: alinhados ao frame de 1440 px do Figma.
    st.markdown("<span class='nexo-dashboard'></span>", unsafe_allow_html=True)
    header_main, header_tools = st.columns([8, 1], gap="small")
    with header_main:
        st.markdown(
            "<h1 class='nexo-page-title'>Visão Geral</h1>"
            "<p class='nexo-page-subtitle'>Acompanhe resultados, antecipe prazos e identifique as próximas ações do portfólio.</p>",
            unsafe_allow_html=True,
        )
    with header_tools:
        email_initials = str(st.session_state.auth_user.get("email", "NX"))[:2].upper()
        st.markdown(
            f"<div class='nexo-header-tools'><span class='nexo-notification' aria-label='Notificações'>♧</span>"
            f"<span class='nexo-avatar'>{html.escape(email_initials)}</span></div>",
            unsafe_allow_html=True,
        )

    # Ações principais e quatro cartões no mesmo alinhamento do design.
    action_a, action_b, action_c = st.columns([1, 1, 4], gap="small")
    with action_a:
        st.button(
            "＋ Novo projeto",
            type="primary",
            use_container_width=True,
            on_click=lambda: st.session_state.update({"navigation_page": "Projetos"}),
            key="dashboard_new_project",
        )
    with action_b:
        st.button(
            "◇ Registrar risco",
            use_container_width=True,
            on_click=lambda: st.session_state.update({"navigation_page": "Riscos"}),
            key="dashboard_new_risk",
        )
    with action_c:
        st.markdown(
            "<div class='nexo-updated-label'>PORTFÓLIO ATUALIZADO COM OS DADOS CADASTRADOS</div>",
            unsafe_allow_html=True,
        )

    kpi_cards = [
        ("PROJETOS NO PORTFÓLIO", f"{total:02d}", f"{completed} concluído(s)", "blue", "▦"),
        ("EM ANDAMENTO", f"{active:02d}", "Em execução ou atenção", "green", "↗"),
        ("PROJETOS ATRASADOS", f"{overdue:02d}", "Todos dentro do prazo" if overdue == 0 else "Exigem revisão do cronograma", "orange", "◷"),
        ("RISCOS CRÍTICOS", f"{high_risks:02d}", "Nenhum risco alto em aberto" if high_risks == 0 else "Risco alto não resolvido", "red", "◇"),
    ]
    cards_html = []
    for label, value, note, accent, symbol in kpi_cards:
        cards_html.append(
            f"<article class='nexo-kpi nexo-kpi-{accent}'>"
            f"<div class='nexo-kpi-accent'></div>"
            f"<div class='nexo-kpi-label'>{label}</div>"
            f"<div class='nexo-kpi-value'>{value}</div>"
            f"<div class='nexo-kpi-icon'>{symbol}</div>"
            f"<div class='nexo-kpi-note'>{html.escape(note)}</div>"
            f"</article>"
        )
    st.markdown("<div class='nexo-kpi-grid'>" + "".join(cards_html) + "</div>", unsafe_allow_html=True)

    # Agrupamento visual de status conforme o gráfico do Figma. "Atenção"
    # é contabilizado junto de "Em andamento" para manter quatro barras.
    chart_items = [
        ("Planejamento", int((projects["status"] == "Planejamento").sum()) if total else 0, "#8cb2e8"),
        ("Em andamento", active, "#14997a"),
        ("Concluídos", completed, "#2563eb"),
        ("Pausados", paused, "#c7d5e8"),
    ]
    max_count = max([item[1] for item in chart_items] + [1])
    chart_bars = []
    for label, count, color in chart_items:
        bar_height = int(126 * count / max_count) if count else 0
        chart_bars.append(
            f"<div class='nexo-chart-item'>"
            f"<div class='nexo-chart-count'>{count:02d}</div>"
            f"<div class='nexo-chart-track'><div class='nexo-chart-fill' style='height:{bar_height}px;background:{color}'></div></div>"
            f"<div class='nexo-chart-label'>{label}</div>"
            f"</div>"
        )
    chart_panel = (
        "<section class='nexo-panel nexo-chart-panel'>"
        "<div class='nexo-panel-heading'><div><h2>Saúde do portfólio</h2>"
        "<p>Distribuição das iniciativas por situação</p></div>"
        "<span class='nexo-period-pill'>VISÃO ATUAL</span></div>"
        "<div class='nexo-panel-divider'></div>"
        "<div class='nexo-chart-bars'>" + "".join(chart_bars) + "</div>"
        f"<div class='nexo-chart-insight'>{total} iniciativa(s) no portfólio · {completed} concluída(s)</div>"
        "</section>"
    )

    progress_panel = (
        "<section class='nexo-panel nexo-progress-panel'>"
        "<h2>Progresso do portfólio</h2>"
        f"<div class='nexo-progress-number'>{avg_progress}%</div>"
        "<span class='nexo-progress-trend'>PORTFÓLIO</span>"
        f"<p>{completed} de {total} projeto(s) concluído(s)</p>"
        f"<div class='nexo-progress-track'><div class='nexo-progress-fill' style='width:{min(max(avg_progress, 0), 100)}%'></div></div>"
        "</section>"
    )

    # A agenda usa os prazos cadastrados nos projetos; não cria dados fictícios.
    deadline_rows = []
    if total:
        agenda_df = projects.copy()
        agenda_df["_deadline"] = pd.to_datetime(agenda_df["end_date"], errors="coerce").dt.date
        agenda_df = agenda_df[
            agenda_df["_deadline"].notna()
            & (agenda_df["status"] != "Concluído")
        ].copy()
        agenda_df["_late"] = agenda_df["_deadline"] < today_date
        agenda_df = agenda_df.sort_values(["_late", "_deadline"], ascending=[False, True]).head(3)
        month_names = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]
        for _, project in agenda_df.iterrows():
            due = project["_deadline"]
            days_left = (due - today_date).days
            if days_left < 0:
                detail = f"Atrasado há {abs(days_left)} dia(s)"
                date_class = "is-overdue"
            elif days_left == 0:
                detail = "Entrega prevista para hoje"
                date_class = "is-today"
            else:
                detail = f"{project['status']} · em {days_left} dia(s)"
                date_class = ""
            deadline_rows.append(
                f"<div class='nexo-agenda-row'>"
                f"<div class='nexo-date-tile {date_class}'><strong>{due.day:02d}</strong><span>{month_names[due.month - 1]}</span></div>"
                f"<div class='nexo-agenda-copy'><strong>{html.escape(str(project['name']))}</strong><span>{html.escape(detail)}</span></div>"
                "</div>"
            )
    if not deadline_rows:
        agenda_rows_html = "<div class='nexo-empty-state'>Nenhuma entrega próxima cadastrada. Adicione um prazo a um projeto para acompanhá-lo aqui.</div>"
    else:
        agenda_rows_html = "".join(deadline_rows)
    agenda_panel = (
        "<section class='nexo-panel nexo-agenda-panel'>"
        "<h2>Agendas e entregas</h2>"
        "<p class='nexo-panel-subtitle'>Próximos prazos dos projetos cadastrados</p>"
        f"<div class='nexo-agenda-list'>{agenda_rows_html}</div>"
        "</section>"
    )

    # Alertas com dados reais, em linhas compactas no lugar de caixas Streamlit genéricas.
    alert_items = []
    if high_risks:
        alert_items.append(("!", "Risco alto não resolvido", f"{high_risks} risco(s) crítico(s) exigem um plano de resposta.", "ALTA PRIORIDADE", "red"))
    if overdue:
        alert_items.append(("◷", "Projeto com prazo vencido", f"{overdue} projeto(s) estão fora do prazo previsto.", "PRAZO VENCIDO", "orange"))
    due_soon = 0
    if total:
        for _, project in projects.iterrows():
            try:
                due = date.fromisoformat(str(project.get("end_date"))[:10])
            except (TypeError, ValueError):
                continue
            if today_date <= due <= date.fromordinal(today_date.toordinal() + 7) and project.get("status") != "Concluído":
                due_soon += 1
    if due_soon:
        alert_items.append(("↗", "Entrega próxima", f"{due_soon} projeto(s) vencem nos próximos 7 dias.", "ACOMPANHAR", "blue"))
    if paused:
        alert_items.append(("Ⅱ", "Projeto pausado", f"{paused} projeto(s) precisam de avaliação para retomada.", "ATENÇÃO", "orange"))
    if not alert_items:
        alert_items.append(("✓", "Tudo em acompanhamento", "Nenhum alerta prioritário foi identificado nos dados atuais.", "ESTÁVEL", "green"))
    alert_rows = []
    for symbol, title, description, priority, accent in alert_items[:3]:
        alert_rows.append(
            f"<div class='nexo-alert-row'>"
            f"<div class='nexo-alert-icon nexo-alert-{accent}'>{symbol}</div>"
            f"<div class='nexo-alert-copy'><strong>{html.escape(title)}</strong><span>{html.escape(description)}</span></div>"
            f"<span class='nexo-priority nexo-priority-{accent}'>{priority}</span>"
            "</div>"
        )
    alerts_panel = (
        "<section class='nexo-panel nexo-alerts-panel'>"
        "<div class='nexo-panel-heading'><div><h2>Alertas e prioridades</h2>"
        "<p>Itens que merecem acompanhamento ou decisão</p></div>"
        f"<span class='nexo-period-pill'>{len(alert_items):02d} ATIVO(S)</span></div>"
        "<div class='nexo-panel-divider'></div>"
        f"<div class='nexo-alert-list'>{''.join(alert_rows)}</div>"
        "<div class='nexo-alert-footer'>Prioridades calculadas com base nos prazos e riscos cadastrados.</div>"
        "</section>"
    )

    left_column, right_column = st.columns([700, 416], gap="medium")
    with left_column:
        st.markdown("<div class='nexo-dashboard-stack'>" + chart_panel + alerts_panel + "</div>", unsafe_allow_html=True)
    with right_column:
        st.markdown("<div class='nexo-dashboard-stack'>" + progress_panel + agenda_panel + "</div>", unsafe_allow_html=True)

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

# ---------- Agendas e entregas ----------
elif page == "Agendas e entregas":
    import html

    st.markdown("<div class='page-eyebrow'>Workspace / Planejamento</div>", unsafe_allow_html=True)
    st.title("Agendas e entregas")
    st.markdown("<p class='page-subtitle'>Acompanhe os próximos prazos registrados nos seus projetos.</p>", unsafe_allow_html=True)
    if projects.empty:
        st.info("Cadastre um projeto com prazo previsto para começar a acompanhar as entregas.")
    else:
        agenda = projects.copy()
        agenda["_deadline"] = pd.to_datetime(agenda["end_date"], errors="coerce").dt.date
        agenda = agenda[agenda["_deadline"].notna()].sort_values("_deadline")
        if agenda.empty:
            st.info("Ainda não há datas válidas de entrega nos projetos cadastrados.")
        else:
            for _, project in agenda.iterrows():
                due = project["_deadline"]
                remaining = (due - date.today()).days
                if project["status"] == "Concluído":
                    label = "Concluído"
                elif remaining < 0:
                    label = f"Atrasado há {abs(remaining)} dia(s)"
                elif remaining == 0:
                    label = "Entrega prevista para hoje"
                else:
                    label = f"Entrega em {remaining} dia(s)"
                with st.container(border=True):
                    date_col, name_col, status_col = st.columns([1, 4, 2])
                    date_col.markdown(f"**{due.strftime('%d/%m/%Y')}**")
                    name_col.markdown(f"**{html.escape(str(project['name']))}**")
                    name_col.caption(f"Responsável: {html.escape(str(project.get('owner') or 'Não definido'))}")
                    status_col.markdown(f"**{label}**")
                    status_col.caption(f"Status do projeto: {project['status']}")
                    progress_value = pd.to_numeric(project.get("progress", 0), errors="coerce")
                    progress_value = 0 if pd.isna(progress_value) else float(progress_value)
                    st.progress(min(max(progress_value, 0), 100) / 100)
    st.caption("Esta agenda reflete os prazos dos projetos cadastrados; agendas independentes ainda não estão armazenadas separadamente.")

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
