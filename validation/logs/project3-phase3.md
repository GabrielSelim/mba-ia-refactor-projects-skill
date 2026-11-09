```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
task-manager-api/
├── app.py                      (composition root create_app + entry point)
├── config/settings.py          (NOVO)
├── database.py                 (mantido)
├── errors.py                   (NOVO)
├── models/                     (mantido; corrigido)
│   ├── task.py  user.py  category.py
├── controllers/                (NOVO — regra que estava nas rotas)
│   ├── task_controller.py  user_controller.py  report_controller.py  category_controller.py  validators.py
├── routes/                     (mantido como camada View, agora fino)
│   ├── task_routes.py  user_routes.py  report_routes.py  category_routes.py (NOVO)
├── services/
│   ├── notification_service.py (config injetada)  auth_service.py (NOVO)
├── middlewares/error_handler.py (NOVO)
├── utils/helpers.py            (limpo: constantes + helpers puros)
└── seed.py

## Findings addressed
F-01 Segredos hardcoded        -> PB-01 -> config/settings.py; SMTP via ambiente injetado no NotificationService
F-02 Hash exposto              -> PB-10 -> User.to_dict() sem password
F-03 MD5                       -> PB-09 -> werkzeug hash; MD5 legado migrado no login
F-04 Token falso               -> PB-09 -> services/auth_service.py (token assinado com expiração)
F-05 Regra nas rotas           -> PB-04 -> controllers/*; routes só mapeiam; categorias em blueprint próprio
F-06 Debug/CORS                -> PB-01 -> FLASK_DEBUG/HOST/CORS_ORIGINS via ambiente
F-07 APIs deprecated           -> PB-13 -> db.session.get(); utc_now() (0 warnings no log de runtime)
F-08 N+1                       -> PB-07 -> joinedload + GROUP BY (valores idênticos ao original)
F-09 Duplicação                -> PB-04 -> Task.is_overdue() único; validators compartilhados
F-10 except genérico           -> PB-08 -> middlewares/error_handler.py
F-11 Validação de tipos        -> PB-04 -> validators (3 erros 500 viraram 400)
F-12..F-15 LOW                 -> PB-14 -> imports/deps mortos removidos, constantes, booleanos diretos, logging

## Contract changes (intentional)
- Respostas de usuário (GET/POST/PUT /users, POST /login) não incluem mais o campo password
- POST /login: token agora é assinado (itsdangerous) — mesmo campo "token"
- Entradas inválidas que davam 500 (priority texto, ?priority=abc) ou HTML 400 (PUT /categories sem body) → 400 JSON
- POST/PUT /categories validam a cor (#RRGGBB)
- requirements.txt sem marshmallow, requests e python-dotenv (não usados)

## Pending recommendations (need human decision)
- Exigir o token nas rotas (hoje públicas) — muda o contrato público

## Validation
  ✓ Application boots without errors (python seed.py && python app.py, python:3.12-slim)
  ✓ All 22 endpoints respond (30/30 baseline calls: mesmos status, exceto 3 erros 500/HTML → 400 JSON)
  ✓ Valores de /tasks/stats, /reports/*, /users, /categories, /tasks idênticos ao original
  ✓ Zero CRITICAL/HIGH anti-patterns remaining; zero LegacyAPIWarning/DeprecationWarning no runtime
================================
```
