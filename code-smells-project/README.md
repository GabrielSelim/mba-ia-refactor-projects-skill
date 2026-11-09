# code-smells-project

API de E-commerce em Python/Flask, refatorada para MVC pela skill `refactor-arch`
(relatório da auditoria em [`../reports/audit-project-1.md`](../reports/audit-project-1.md)).

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot,
com produtos e usuários de exemplo (senhas gravadas com hash).

## Configuração (variáveis de ambiente)

| Variável | Padrão | Descrição |
|---|---|---|
| `SECRET_KEY` | aleatória a cada boot | Chave da aplicação. Defina em produção. |
| `FLASK_DEBUG` | `false` | Liga o modo debug. |
| `HOST` / `PORT` | `127.0.0.1` / `5000` | Endereço do servidor. |
| `DATABASE_PATH` | `loja.db` | Caminho do banco SQLite. |
| `CORS_ORIGINS` | `*` | Origens permitidas no CORS. |
| `ADMIN_TOKEN` | vazio | Habilita `/admin/*` (header `X-Admin-Token`). Vazio = rotas admin desabilitadas (403). |

## Estrutura

```
app.py                      # entry point (runner)
src/
├── app.py                  # composition root: create_app()
├── config/settings.py      # configuração do ambiente
├── database.py             # conexão por requisição, transações, schema e seed
├── errors.py               # exceções de domínio
├── models/                 # produto_model, usuario_model, pedido_model
├── controllers/            # produto, usuario, pedido, system + validators
├── views/routes.py         # rotas (URL → controller → JSON)
├── services/notification_service.py
└── middlewares/            # error_handler (central) e admin_auth
```
