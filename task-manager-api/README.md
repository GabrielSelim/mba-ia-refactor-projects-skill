# task-manager-api

API de Task Manager em Python/Flask. O projeto já tinha separação parcial (`models/`, `routes/`, `services/`,
`utils/`); a skill `refactor-arch` completou o MVC (`config/`, `controllers/`, `middlewares/`) e corrigiu os
problemas de segurança e qualidade — relatório em [`../reports/audit-project-3.md`](../reports/audit-project-3.md).

## Como rodar

```bash
pip install -r requirements.txt
python seed.py
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000`. Rode o `seed.py` antes do primeiro boot para popular o `tasks.db`.

## Configuração (variáveis de ambiente)

| Variável | Padrão | Descrição |
|---|---|---|
| `SECRET_KEY` | aleatória a cada boot | Assina os tokens de login. Defina em produção. |
| `DATABASE_URL` | `sqlite:///tasks.db` | URI do SQLAlchemy |
| `FLASK_DEBUG` | `false` | Modo debug |
| `HOST` / `PORT` | `127.0.0.1` / `5000` | Endereço do servidor |
| `CORS_ORIGINS` | `*` | Origens permitidas |
| `TOKEN_MAX_AGE_SECONDS` | `28800` | Validade do token de login |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` | — | E-mail de notificações (sem credenciais = não envia) |

## Estrutura

```
app.py                  # composition root (create_app) + entry point
config/settings.py      # configuração do ambiente
database.py             # instância do SQLAlchemy
errors.py               # exceções de domínio
models/                 # Task, User, Category (ORM)
controllers/            # task, user, report, category + validators
routes/                 # views: task, user, report, category (URL → controller)
services/               # notification_service, auth_service (token assinado)
middlewares/            # error_handler central
utils/helpers.py        # constantes de domínio e helpers puros (utc_now, ...)
seed.py                 # dados de exemplo
```
