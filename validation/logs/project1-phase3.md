```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
code-smells-project/
├── app.py                          (entry point / runner)
└── src/
    ├── app.py                      (composition root: create_app)
    ├── config/settings.py
    ├── database.py                 (conexão por requisição + transaction() + schema/seed)
    ├── errors.py                   (exceções de domínio)
    ├── models/
    │   ├── produto_model.py
    │   ├── usuario_model.py
    │   └── pedido_model.py
    ├── controllers/
    │   ├── produto_controller.py
    │   ├── usuario_controller.py
    │   ├── pedido_controller.py
    │   ├── system_controller.py
    │   └── validators.py
    ├── views/routes.py
    ├── services/notification_service.py
    └── middlewares/
        ├── error_handler.py
        └── admin_auth.py

## Findings addressed
F-01 SQL Injection          -> PB-02 -> queries parametrizadas em models/*_model.py
F-02 /admin sem proteção    -> PB-15 -> middlewares/admin_auth.py (X-Admin-Token) + SELECT-only
F-03 Segredos hardcoded     -> PB-01 -> config/settings.py (ambiente, secret aleatória em dev)
F-04 Dados sensíveis        -> PB-10/PB-08 -> usuario_model sem senha; /health mínimo; 500 genérico
F-05 Senha em texto puro    -> PB-09 -> werkzeug hash + migração no login de senhas legadas
F-06 God File               -> PB-03/PB-04 -> models/, controllers/, views/ por domínio
F-07 Conexão global         -> PB-05 -> database.get_db() em flask.g + teardown
F-08 Pedido sem transação   -> PB-12 -> transaction() (BEGIN IMMEDIATE); cancelamento devolve estoque
F-09 Debug/CORS             -> PB-01 -> FLASK_DEBUG/HOST/CORS_ORIGINS via ambiente (debug off)
F-10 Controller com SQL     -> PB-04/PB-06 -> controllers só orquestram; NotificationService injetado
F-11 Sem autenticação       -> pendente (decisão humana)
F-12 N+1                    -> PB-07 -> JOIN em pedido_model._listar; agregação única no relatório
F-13 Duplicação             -> PB-04 -> _to_dict único; validar_produto() para criar e atualizar
F-14 Erros genéricos        -> PB-08 -> middlewares/error_handler.py
F-15 Validação              -> PB-04 -> controllers/validators.py (tipos, quantidade >= 1)
F-16 Notificação no ctrl    -> PB-06 -> services/notification_service.py
F-17..F-20 LOW              -> PB-14 -> constantes, logging, nomes, imports removidos

## Contract changes (intentional)
- GET /health não retorna mais secret_key, db_path, debug e ambiente
- GET /usuarios e /usuarios/<id> não retornam mais o campo senha
- /admin/query e /admin/reset-db exigem header X-Admin-Token (403 sem token); /admin/query aceita só SELECT
- Respostas de erro padronizadas: {"erro": ..., "sucesso": false}
- PUT /pedidos/<id>/status em pedido inexistente → 404 (antes 200 sem efeito)

## Pending recommendations (need human decision)
- F-11: exigir autenticação (token) nas rotas de usuários e pedidos — muda o contrato público

## Validation
  ✓ Application boots without errors (python app.py, python:3.12-slim)
  ✓ All 19 endpoints respond (25/25 baseline calls match; differences only the intentional contract changes above)
  ✓ Zero CRITICAL/HIGH anti-patterns remaining (grep: no SQL concat, no hardcoded secret, no global state, no password in responses)
================================
```
