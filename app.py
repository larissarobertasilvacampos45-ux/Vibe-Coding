import os
from datetime import date, datetime
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from supabase import Client, create_client

app = FastAPI(title="Nexo | Gestão de Projetos", version="2.0.0")
PROJECT_STATUSES = ["Planejamento", "Em andamento", "Atenção", "Pausado", "Concluído"]


def supabase_client() -> Client:
    url = os.getenv("SUPABASE_URL", "").strip()
    key = (os.getenv("SUPABASE_PUBLISHABLE_KEY", "").strip()
           or os.getenv("SUPABASE_ANON_KEY", "").strip())
    if not url or not key:
        raise HTTPException(503, "Configure SUPABASE_URL e SUPABASE_PUBLISHABLE_KEY na Vercel.")
    return create_client(url, key)


def user_context(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Faça login para continuar.")
    token = authorization.split(" ", 1)[1].strip()
    client = supabase_client()
    try:
        user = client.auth.get_user(token).user
        if not user:
            raise ValueError("Sessão inválida")
        client.postgrest.auth(token)
        return client, user
    except Exception:
        raise HTTPException(401, "Sua sessão expirou. Entre novamente.")


class LoginBody(BaseModel):
    email: str
    password: str = Field(min_length=1, max_length=256)


class ResetBody(BaseModel):
    email: str


class RefreshBody(BaseModel):
    refresh_token: str


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
def login(body: LoginBody):
    try:
        result = supabase_client().auth.sign_in_with_password(
            {"email": body.email, "password": body.password}
        )
        if not result.session or not result.user:
            raise ValueError("Login inválido")
        return {
            "access_token": result.session.access_token,
            "refresh_token": result.session.refresh_token,
            "user": {"id": result.user.id, "email": result.user.email or body.email},
        }
    except Exception:
        raise HTTPException(401, "Não foi possível entrar. Confira seu e-mail e sua senha.")


@app.post("/api/auth/refresh")
def refresh(body: RefreshBody):
    try:
        result = supabase_client().auth.refresh_session(body.refresh_token)
        if not result.session or not result.user:
            raise ValueError("Sessão inválida")
        return {
            "access_token": result.session.access_token,
            "refresh_token": result.session.refresh_token,
            "user": {"id": result.user.id, "email": result.user.email or ""},
        }
    except Exception:
        raise HTTPException(401, "Sua sessão expirou. Entre novamente.")


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
        "name": body.name.strip(), "owner": body.owner.strip() or None,
        "owner_id": user.id,
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
        rs = client.table("risks").select("*").order("created_at", desc=True).execute().data or []
        ps = client.table("projects").select("id,name").execute().data or []
        names = {str(p["id"]): p.get("name") or "" for p in ps}
        return [{**r, "project_name": names.get(str(r.get("project_id")), "")} for r in rs]
    except Exception:
        raise HTTPException(400, "Não foi possível carregar os riscos.")


@app.post("/api/risks", status_code=201)
def create_risk(body: RiskBody, ctx=Depends(user_context)):
    client, _ = ctx
    mitigation = body.mitigation.strip() or None
    data = {
        "project_id": body.project_id, "title": body.title.strip(),
        "description": body.description.strip() or None,
        "probability": body.probability, "impact": body.impact,
        "mitigation": mitigation, "mitigation_plan": mitigation,
        "status": body.status,
        "updated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
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
            "status": body.status,
            "updated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        }).eq("id", risk_id).select("*").execute()
        if not result.data:
            raise HTTPException(404, "Risco não encontrado ou sem permissão para alterá-lo.")
        return result.data[0]
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(400, "Não foi possível atualizar a situação do risco.")
