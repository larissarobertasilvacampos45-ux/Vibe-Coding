# Acompanhamento de Projetos

Aplicação web simples em Python para acompanhar projetos, progresso, prazos e riscos. Desenvolvida como projeto de portfólio para demonstrar práticas de PMO e implantação de sistemas.

## Funcionalidades

- Cadastro e atualização de projetos: nome, responsável, status, datas, progresso e observações.
- Painel com indicadores de projetos, prazos e riscos altos em aberto.
- Registro de riscos com probabilidade, impacto e cálculo automático de nível (baixo, médio ou alto).
- Plano de resposta/mitigação e atualização da situação dos riscos.
- Persistência local usando SQLite.

## Executar localmente

Requer Python 3.10 ou superior.

```bash
python -m venv .venv
source .venv/bin/activate
# No Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

O navegador abrirá o sistema localmente. Os dados são salvos no arquivo `projetos.db`, criado automaticamente ao executar o aplicativo. Esse arquivo é local e não deve ser enviado ao GitHub.

## Como funciona o alerta de risco

O nível é calculado pela combinação de probabilidade e impacto:
- **Alto:** pontuação 6 a 9
- **Médio:** pontuação 3 a 4
- **Baixo:** pontuação 1 a 2

O painel destaca riscos altos que ainda não foram resolvidos e projetos com prazo vencido.

## Publicação online

O código está preparado para ser executado localmente ou publicado em um serviço compatível com Streamlit, como o Streamlit Community Cloud. O envio ao GitHub, por si só, não deixa o aplicativo online.

## Privacidade

Use apenas dados fictícios ou não confidenciais. Esta versão é um protótipo local, sem autenticação de usuários e sem banco de dados compartilhado.
