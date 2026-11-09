# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express, refatorada para MVC pela skill `refactor-arch`
(relatório da auditoria em [`../reports/audit-project-2.md`](../reports/audit-project-2.md)).

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e carrega seeds automaticamente no boot.
Exemplos de requisições estão em `api.http`.

## Configuração (variáveis de ambiente)

| Variável | Padrão | Descrição |
|---|---|---|
| `PORT` | `3000` | Porta HTTP |
| `DB_PATH` | `:memory:` | Arquivo SQLite (ou memória) |
| `PAYMENT_GATEWAY_KEY` | vazio | Chave do gateway (vazio = gateway simulado em dev) |
| `LOG_LEVEL` | `info` | `error`, `warn`, `info` ou `debug` |

## Estrutura

```
src/
├── server.js               # entry point: dependências concretas + listen
├── app.js                  # composition root: createApp({ db, paymentGateway, passwordHasher, logger })
├── config/index.js         # configuração do ambiente
├── errors.js               # erros de domínio
├── database/               # connection.js (Promise + transações) e schema.js (tabelas + seed)
├── models/index.js         # users, courses, enrollments, payments, auditLogs, reports
├── controllers/            # checkoutController, reportController, userController
├── routes/index.js         # rotas (URL → controller)
├── services/               # paymentGateway, passwordHasher, logger
└── middlewares/            # asyncHandler, errorHandler
```
