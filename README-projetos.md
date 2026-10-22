# Sistema de Gestão de Projetos

Aplicação web em Python com Streamlit para demonstrar práticas de PMO e implantação de sistemas. O sistema permite cadastrar projetos, acompanhar prazos e progresso e registrar riscos.

## Funcionalidades

- Cadastro, edição e exclusão de projetos.
- Acompanhamento de responsável, status, datas, progresso e observações.
- Painel com indicadores de projetos ativos, projetos atrasados e riscos altos em aberto.
- Registro de riscos por projeto, com probabilidade, impacto e nível calculado automaticamente.
- Plano de resposta/mitigação e atualização da situação dos riscos.

## Executar localmente

Requer Python 3.10 ou superior.

```bash
python -m venv .venv
source .venv/bin/activate
# No Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

## Publicar para visualizar online

O código pode ser publicado no Streamlit Community Cloud:

1. Acesse o [Streamlit Community Cloud](https://share.streamlit.io/).
2. Entre com sua conta do GitHub e autorize o acesso ao repositório.
3. Clique em **Create app**.
4. Selecione o repositório `larissarobertasilvacampos45-ux/Vibe-Coding), a branch `main` e o arquivo `app.py).
5. Clique em **Deploy** e aguarde a instalação das dependências.

O arquivo `requirements.txt` já lista as dependências necessárias para executar esta versão.

## Importante sobre os dados

Esta versão inicial usa SQLite e grava os dados no arquivo local `projetos.db`. Em serviços de hospedagem, esse armazenamento local pode não ser persistente entre reinicializações/redeploys e não é um banco compartilhado confiável para uso contínuo. Para manter os dados de forma confiável na versão online, o próximo passo é conectar o sistema a um banco de dados hospedado, como Supabase.

Não inclua informações confidenciais de clientes. Esta versão ainda não tem autenticação de usuários.

## Regra de classificação de riscos

O nível é calculado pela combinação de probabilidade e impacto:
- **Alto:** pontuação de 6 a 9.
- **Médio:** pontuação de 3 a 4.
- **Baixo:** pontuação de 1 a 2.
