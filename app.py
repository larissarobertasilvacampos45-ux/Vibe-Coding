import os
from datetime import date, datetime
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from pydantic import BaseModel, Field
from supabase import Client, create_client

app = FastAPI(title="Nexo | Gestão de Projetos", version="2.0.0")


def supabase_client() -> Client:
    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_PUBLISHABLE_KEY", "").strip() or os.getenv("SUPABASE_ANON_KEY", "").strip()
    if not url or not key:
        raise HTTPException(503, "Configure SUPABASE_URL e SUPABASE_PUBLISHABLE_KEY na Vercel.")
    return create_client(url, key)


def cookie_options():
    return {
        "httponly": True,
        "secure": os.getenv("VERCEL") == "1" or os.getenv("ENVIRONMENT") == "production",
        "samesite": "lax",
        "path": "/",
    }


def set_session_cookies(response: Response, session):
    opts = cookie_options()
    response.set_cookie("nexo_access", session.access_token, max_age=3600, **opts)
    response.set_cookie("nexo_refresh", session.refresh_token, max_age=60 * 60 * 24 * 30, **opts)


def clear_session_cookies(response: Response):
    opts = cookie_options()
    response.delete_cookie("nexo_access", path=opts["path"], secure=opts["secure"], httponly=True, samesite=opts["samesite"])
    response.delete_cookie("nexo_refresh", path=opts["path"], secure=opts["secure"], httponly=True, samesite=opts["samesite"])


def user_context(request: Request, response: Response):
    access = request.cookies.get("nexo_access")
    refresh = request.cookies.get("nexo_refresh")
    if not access and not refresh:
        raise HTTPException(401, "Faça login para continuar.")
    client = supabase_client()
    user = None
    if access:
        try:
            user = client.auth.get_user(access).user
        except Exception:
            user = None
    if not user and refresh:
        try:
            refreshed = client.auth.refresh_session(refresh)
            if refreshed.session and refreshed.user:
                set_session_cookies(response, refreshed.session)
                access = refreshed.session.access_token
                user = refreshed.user
        except Exception:
            user = None
    if not user or not access:
        clear_session_cookies(response)
        raise HTTPException(401, "Sua sessão expirou. Entre novamente.")
    # Encaminha o JWT do usuário para o PostgREST. As políticas RLS do banco
    # continuam controlando quais registros podem ser consultados ou alterados.
    client.postgrest.auth(access)
    return client, user


class LoginBody(BaseModel):
    email: str
    password: str = Field(min_length=1, max_length=256)


class ResetBody(BaseModel):
    email: str


class PasswordBody(BaseModel):
    access_token: str
    refresh_token: str
    password: str = Field(min_length=8, max_length=128)


class ProjectBody(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    owner: str = ""
    status: Literal["Planejamento", "Em andamento", "Atenção", "Pausado", "Concluído"] = "Planejamento"
    progress: int = Field(default=0, ge=0, le=100)
    start_date: date | None = None
    end_date: date | None = None
    description: str = ""


class RiskBody(BaseModel):
    project_id: str
    title: str = Field(min_length=1, max_length=180)
    description: str = ""
    probability: Literal["Baixa", "Média", "Alta"] = "Média"
    impact: Literal["Baixo", "Médio", "Alto"] = "Médio"
    mitigation: str = ""
    status: Literal["Aberto", "Em tratamento", "Resolvido"] = "Aberto"


class RiskStatusBody(BaseModel):
    status: Literal["Aberto", "Em tratamento", "Resolvido"]


@app.get("/api/health")
def health():
    return {"status": "ok", "runtime": "Python + FastAPI"}


@app.post("/api/auth/login")
def login(body: LoginBody, response: Response):
    client = supabase_client()
    try:
        result = client.auth.sign_in_with_password({"email": body.email, "password": body.password})
        if not result.session or not result.user:
            raise ValueError("Login inválido")
        set_session_cookies(response, result.session)
        return {"user": {"id": result.user.id, "email": result.user.email or body.email}}
    except Exception:
        raise HTTPException(401, "Não foi possível entrar. Confira seu e-mail e sua senha.")


@app.post("/api/auth/logout")
def logout(request: Request, response: Response):
    access = request.cookies.get("nexo_access")
    refresh = request.cookies.get("nexo_refresh")
    if access and refresh:
        try:
            client = supabase_client()
            client.auth.set_session(access, refresh)
            client.auth.sign_out()
        except Exception:
            pass
    clear_session_cookies(response)
    return {"message": "Sessão encerrada."}


@app.post("/api/auth/reset")
def reset_password(body: ResetBody):
    client = supabase_client()
    base = os.getenv("FRONTEND_URL", "").strip()
    if not base:
        domain = os.getenv("VERCEL_PROJECT_PRODUCTION_URL") or os.getenv("VERCEL_URL")
        base = f"https://{domain}" if domain else "http://localhost:8000"
    try:
        client.auth.reset_password_for_email(
            body.email, {"redirect_to": base.rstrip("/") + "/reset-password.html"}
        )
        return {"message": "Se a conta existir, você receberá as instruções de recuperação."}
    except Exception:
        raise HTTPException(400, "Não foi possível solicitar a recuperação agora. Tente novamente mais tarde.")


@app.post("/api/auth/update-password")
def update_password(body: PasswordBody):
    client = supabase_client()
    try:
        client.auth.set_session(body.access_token, body.refresh_token)
        client.auth.update_user({"password": body.password})
        return {"message": "Senha alterada com sucesso."}
    except Exception:
        raise HTTPException(400, "Não foi possível alterar a senha. Solicite um novo link de recuperação.")


@app.get("/api/me")
def me(ctx=Depends(user_context)):
    _, user = ctx
    return {"id": user.id, "email": user.email or ""}


@app.get("/api/projects")
def projects(ctx=Depends(user_context)):
    client, _ = ctx
    try:
        return client.table("projects").select("*").order("created_at", desc=True).execute().data or []
    except Exception:
        raise HTTPException(400, "Não foi possível carregar os projetos.")


@app.post("/api/projects", status_code=201)
def create_project(body: ProjectBody, ctx=Depends(user_context)):
    client, user = ctx
    if body.start_date and body.end_date and body.end_date < body.start_date:
        raise HTTPException(422, "O prazo não pode ser anterior à data de início.")
    end_date = body.end_date.isoformat() if body.end_date else None
    data = {
        "name": body.name.strip(), "owner": body.owner.strip() or None, "owner_id": user.id,
        "start_date": body.start_date.isoformat() if body.start_date else None,
        "end_date": end_date, "due_date": end_date, "status": body.status,
        "progress": body.progress, "description": body.description.strip() or None,
        "updated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
    try:
        result = client.table("projects").insert(data).execute()
        return result.data[0]
    except Exception:
        raise HTTPException(400, "Não foi possível cadastrar o projeto. Verifique os dados e as permissões.")


@app.patch("/api/projects/{project_id}")
def edit_project(project_id: str, body: ProjectBody, ctx=Depends(user_context)):
    client, _ = ctx
    if body.start_date and body.end_date and body.end_date < body.start_date:
        raise HTTPException(422, "O prazo não pode ser anterior à data de início.")
    end_date = body.end_date.isoformat() if body.end_date else None
    data = {
        "name": body.name.strip(), "owner": body.owner.strip() or None,
        "start_date": body.start_date.isoformat() if body.start_date else None,
        "end_date": end_date, "due_date": end_date, "status": body.status,
        "progress": body.progress, "description": body.description.strip() or None,
        "updated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
    try:
        result = client.table("projects").update(data).eq("id", project_id).select("*").execute()
        if not result.data:
            raise HTTPException(404, "Projeto não encontrado ou sem permissão para alterá-lo.")
        return result.data[0]
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(400, "Não foi possível atualizar o projeto.")


@app.delete("/api/projects/{project_id}")
def remove_project(project_id: str, ctx=Depends(user_context)):
    client, _ = ctx
    try:
        # Protege tarefas e registros relacionados que a interface não gerencia.
        for table in ("tasks", "project_updates", "scope_changes"):
            related = client.table(table).select("id").eq("project_id", project_id).limit(1).execute()
            if related.data:
                raise HTTPException(409, "Este projeto possui tarefas, atualizações ou mudanças de escopo vinculadas. Trate esses registros antes de excluí-lo.")
        client.table("risks").delete().eq("project_id", project_id).execute()
        result = client.table("projects").delete().eq("id", project_id).select("id").execute()
        if not result.data:
            raise HTTPException(404, "Projeto não encontrado ou sem permissão para excluí-lo.")
        return {"message": "Projeto excluído."}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(400, "Não foi possível excluir o projeto. Verifique os registros relacionados.")


@app.get("/api/risks")
def risks(ctx=Depends(user_context)):
    client, _ = ctx
    try:
        risk_rows = client.table("risks").select("*").order("created_at", desc=True).execute().data or []
        project_rows = client.table("projects").select("id,name").execute().data or []
        names = {str(p["id"]): p.get("name") or "" for p in project_rows}
        return [{**r, "project_name": names.get(str(r.get("project_id")), "")} for r in risk_rows]
    except Exception:
        raise HTTPException(400, "Não foi possível carregar os riscos.")


@app.post("/api/risks", status_code=201)
def create_risk(body: RiskBody, ctx=Depends(user_context)):
    client, _ = ctx
    mitigation = body.mitigation.strip() or None
    data = {
        "project_id": body.project_id, "title": body.title.strip(),
        "description": body.description.strip() or None, "probability": body.probability,
        "impact": body.impact, "mitigation": mitigation, "mitigation_plan": mitigation,
        "status": body.status, "updated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
    try:
        result = client.table("risks").insert(data).execute()
        return result.data[0]
    except Exception:
        raise HTTPException(400, "Não foi possível registrar o risco. Verifique o projeto e suas permissões.")


@app.patch("/api/risks/{risk_id}")
def edit_risk(risk_id: str, body: RiskStatusBody, ctx=Depends(user_context)):
    client, _ = ctx
    try:
        result = client.table("risks").update({
            "status": body.status, "updated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z"
        }).eq("id", risk_id).select("*").execute()
        if not result.data:
            raise HTTPException(404, "Risco não encontrado ou sem permissão para alterá-lo.")
        return result.data[0]
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(400, "Não foi possível atualizar a situação do risco.")
