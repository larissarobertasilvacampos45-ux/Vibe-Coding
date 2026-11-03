# Nexo — Gestão de Projetos

Aplicação migrada de Streamlit para **Python + FastAPI**, preparada para execução na Vercel. O backend, as regras de negócio e a integração com Supabase permanecem em Python; a interface utiliza HTML, CSS e JavaScript.

## Estrutura

- `app.py`: aplicação FastAPI e endpoints HTTP.
- `public/index.html`: interface (dashboard, projetos, riscos e agendas/entregas).
- `public/reset-password.html`: fluxo de recuperação de senha.
- `requirements.txt`: dependências Python com versões fixadas.
- `.python-version`: runtime Python 3.12.

## Variáveis de ambiente na Vercel

Configure:

- `SUPABASE_URL`: URL do projeto Supabase.
- `SUPABASE_PUBLISHABLE_KEY`: chave publishable. Também é aceito `SUPABASE_ANON_KEY`.
- `FRONTEND_URL`: URL pública do Nexo, por exemplo `https://seu-projeto.vercel.app`.

Não configure nem exponha a chave `service_role` ou uma chave secreta no frontend.

## Supabase Auth

No Supabase, em Authentication → URL Configuration:

1. Defina `Site URL` com o domínio público do Nexo.
2. Inclua `https://SEU-DOMINIO/reset-password.html` em Redirect URLs.
3. Inclua domínios de preview somente se forem usados nos testes.

O pedido de recuperação de senha usa `FRONTEND_URL/reset-password.html`.

## Executar localmente

Use Python 3.12:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export SUPABASE_URL="..."
export SUPABASE_PUBLISHABLE_KEY="..."
export FRONTEND_URL="http://localhost:8000"
uvicorn app:app --reload
```

Acesse `http://localhost:8000` e a documentação da API em `/docs`.

## Funcionalidades migradas

- Login, sessão e recuperação de senha.
- Dashboard com indicadores, status, progresso, prazos e alertas.
- Cadastro, edição, pesquisa, filtro e exclusão protegida de projetos.
- Cadastro e atualização da situação de riscos.
- Agenda baseada nos prazos registrados nos projetos.
- Demonstração pública somente leitura em `/?demo=1`.

## Segurança e dados

As chamadas autenticadas encaminham o JWT do usuário ao Supabase. As políticas RLS existentes continuam sendo aplicadas; a aplicação não usa `service_role` e não cria nem altera tabelas. A exclusão de projetos é bloqueada quando existem tarefas, atualizações ou mudanças de escopo vinculadas, para evitar apagar dados que esta interface não gerencia.
