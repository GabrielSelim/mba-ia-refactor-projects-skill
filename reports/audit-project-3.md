================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1)
Files:   15 analyzed | ~1160 lines of code
Date:    2026-11-09

## Summary
CRITICAL: 3 | HIGH: 3 | MEDIUM: 5 | LOW: 4

## Findings

### F-01 [CRITICAL] Segredos hardcoded: SECRET_KEY e senha SMTP (AP-01)
Files:
- app.py:11 — `SQLALCHEMY_DATABASE_URI` fixa
- app.py:13 — `app.config['SECRET_KEY'] = 'super-secret-key-123'`
- services/notification_service.py:7-10 — `email_user = 'taskmanager@gmail.com'`, `email_password = 'senha123'`
Description: A chave de assinatura e a credencial do servidor de e-mail estão no código versionado.
Impact: Quem lê o repositório usa a conta SMTP e forja tokens assinados com a SECRET_KEY.
Recommendation: `config/settings.py` lendo do ambiente, com o serviço de notificação recebendo a configuração
injetada (PB-01, PB-06).

### F-02 [CRITICAL] Hash de senha exposto em todas as respostas de usuário (AP-05)
Files:
- models/user.py:16-25 — `to_dict()` inclui `'password': self.password`
- usado em: routes/user_routes.py:33 (GET /users/<id>), 85 (POST /users), 129 (PUT /users/<id>), 209 (POST /login)
Description: A API devolve o hash da senha no cadastro, na consulta, na atualização e no login.
Impact: Com MD5 sem salt (F-03), o hash exposto equivale à senha. Basta uma rainbow table.
Recommendation: Remover o campo da serialização (PB-10).

### F-03 [CRITICAL] Senhas com MD5 sem salt e política fraca (AP-06)
Files:
- models/user.py:27-32 — `hashlib.md5(pwd.encode()).hexdigest()` em `set_password` e `check_password`
- routes/user_routes.py:64, 115 — senha mínima de 4 caracteres
Description: MD5 é um hash rápido e sem salt, quebrável em segundos. Combinado com F-02, os hashes ficam públicos.
Impact: Comprometimento de todas as contas.
Recommendation: `werkzeug.security.generate_password_hash` (scrypt/pbkdf2 com salt), com migração transparente de
hashes MD5 legados no login (PB-09).

### F-04 [HIGH] Token de autenticação falso e previsível (AP-12)
Files:
- routes/user_routes.py:210 — `'token': 'fake-jwt-token-' + str(user.id)`
- nenhuma rota verifica token (todas as blueprints são públicas)
Description: O "token" é só o id do usuário prefixado, e ninguém o valida.
Impact: Qualquer cliente fabrica o token de qualquer usuário. A API não tem autenticação real.
Recommendation: Token assinado e com expiração (`itsdangerous`, que já vem com o Flask). Exigir o token nas rotas
muda o contrato e fica como decisão pendente (PB-09).

### F-05 [HIGH] Regra de negócio e acesso a dados nas rotas, sem camada de controller (AP-07)
Files:
- routes/task_routes.py:85-154 — `create_task`: validação, checagem de relações, parse de data, persistência
- routes/task_routes.py:156-223 — `update_task`: as mesmas regras reescritas
- routes/report_routes.py:12-101 — `summary_report`: 90 linhas de agregação dentro da rota
- routes/user_routes.py:42-90 — `create_user`: validação, unicidade, hash e persistência
- routes/report_routes.py:157-223 — CRUD de categorias dentro do blueprint de relatórios
Description: O projeto tem `models/`, `routes/` e `services/`, mas as rotas fazem papel de controller, model e
view. Categorias vivem no arquivo de relatórios.
Impact: Regras duplicadas e divergentes, e nenhuma lógica testável sem HTTP.
Recommendation: Criar `controllers/` (task, user, report, category). As rotas ficam como camada View fina (PB-04).

### F-06 [HIGH] Configuração de execução insegura (AP-11)
Files:
- app.py:34 — `app.run(debug=True, host='0.0.0.0', port=5000)`
- app.py:15 — `CORS(app)` sem restrição de origem
Description: O debugger do Werkzeug fica ativo e exposto em todas as interfaces.
Impact: Execução remota de código se o debugger for alcançável.
Recommendation: `DEBUG`, `HOST` e `CORS_ORIGINS` via config, com debug desligado por padrão (PB-01).

### F-07 [MEDIUM] APIs deprecated: `Query.get()` e `datetime.utcnow()` (AP-19)
Files:
- routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227 — `Model.query.get(...)`
- routes/user_routes.py:29, 94, 136, 155 — `Model.query.get(...)`
- routes/report_routes.py:105, 192, 213 — `Model.query.get(...)`
- models/task.py:15, 16, 52; models/user.py:14; models/category.py:11 — `datetime.utcnow`
- routes/task_routes.py:31, 72, 215, 285; routes/user_routes.py:172; routes/report_routes.py:35, 42, 45, 71, 133 — `datetime.utcnow()`
- services/notification_service.py:35; utils/helpers.py:38; seed.py:66-74 — `datetime.utcnow()`
Description: `Query.get()` é legado no SQLAlchemy 2.x (emite `LegacyAPIWarning`). `datetime.utcnow()` está deprecated
desde o Python 3.12 (`DeprecationWarning`).
Impact: Warnings em runtime e quebra em versões futuras.
Recommendation: `db.session.get(Model, id)` e o helper `utc_now()` baseado em `datetime.now(timezone.utc)` (PB-13).

### F-08 [MEDIUM] Queries N+1 em listagens e relatórios (AP-13)
Files:
- routes/task_routes.py:41-57 — por task, 1 query de usuário e 1 de categoria
- routes/user_routes.py:22 — `len(u.tasks)` dispara lazy load por usuário
- routes/report_routes.py:53-68 — 1 query de tasks por usuário
- routes/report_routes.py:159-164 — 1 `count()` por categoria
- routes/report_routes.py:15-28 e routes/task_routes.py:275-279 — 9 e 5 `count()` separados que cabem em um `GROUP BY`
Description: O número de queries cresce com o número de tasks, usuários e categorias.
Impact: Latência crescente nos endpoints de listagem e relatório.
Recommendation: `joinedload` e agregações com `GROUP BY` (PB-07).

### F-09 [MEDIUM] Regra de "task atrasada" e validações duplicadas (AP-14)
Files:
- routes/task_routes.py:30-39, 71-80, 283-287; routes/user_routes.py:171-180; routes/report_routes.py:34-36, 132-135 — a mesma regra de overdue copiada 6 vezes, embora `Task.is_overdue()` exista em models/task.py:50-60
- routes/task_routes.py:92-144 e 166-213 — validação de create e update duplicada, e `utils/helpers.py:57-108` (`process_task_data`) faz o mesmo e nunca é usado
- routes/task_routes.py:17-28 — serialização manual duplicando `Task.to_dict()`
Description: A mesma lógica está espalhada em vários arquivos, e o helper que a centralizaria está morto.
Impact: Correções parciais e regras divergentes entre endpoints.
Recommendation: Usar `Task.is_overdue()` e uma função única de validação no controller (PB-04).

### F-10 [MEDIUM] `except:` genérico e ausência de handler central (AP-16)
Files:
- routes/task_routes.py:62, 137, 204, 236
- routes/user_routes.py:130, 149
- routes/report_routes.py:186, 207, 221
- utils/helpers.py:46, 49, 88
- nenhum `errorhandler` registrado em app.py
Description: `except:` sem tipo engole qualquer erro (até `KeyboardInterrupt`). `GET /tasks` responde "Erro interno"
sem log.
Impact: Falhas silenciosas e diagnóstico impossível.
Recommendation: Exceções de domínio e `register_error_handlers(app)` com log (PB-08).

### F-11 [MEDIUM] Validação de tipos ausente gera erros 500 (AP-15)
Files:
- routes/task_routes.py:113, 182 — `priority < 1` com string causa `TypeError` → 500
- routes/task_routes.py:261, 264 — `int(priority)` e `int(user_id)` com texto causam `ValueError` → 500
- routes/report_routes.py:196-197 — `update_category` usa `data` sem checar `None`
- routes/report_routes.py:180 — cor da categoria não é validada (`is_valid_color` em utils/helpers.py:52 nunca é usado)
Description: A entrada de usuário chega sem validação de tipo às comparações e conversões.
Impact: Erros 500 em entradas simples e dados inválidos persistidos.
Recommendation: Validação centralizada que retorna 400 (PB-04, PB-08).

### F-12 [LOW] Imports, dependências e código mortos (AP-23)
Files:
- app.py:7 — `os`, `sys`, `json`
- routes/task_routes.py:7 — `json`, `os`, `sys`, `time`
- routes/user_routes.py:6 — `hashlib`, `json`
- routes/report_routes.py:8 — `json`
- models/task.py:3 — `json`
- utils/helpers.py:3-7 — `os`, `json`, `sys`, `math`, `hashlib`
- services/notification_service.py:4-48 — `NotificationService` nunca é instanciado
- requirements.txt:4-6 — `marshmallow`, `requests`, `python-dotenv` sem uso
Recommendation: Remover imports e dependências mortas. Usar o serviço ou documentá-lo como ponto de extensão (PB-14).

### F-13 [LOW] Magic strings e constantes ignoradas (AP-20)
Files:
- routes/task_routes.py:110, 177; models/task.py:39; utils/helpers.py:75 — lista de status repetida
- routes/user_routes.py:71, 120 — roles literais
- routes/user_routes.py:64, 115 — tamanho mínimo de senha `4`
- utils/helpers.py:110-116 — constantes `VALID_STATUSES`, `VALID_ROLES` e `MIN_PASSWORD_LENGTH` definidas e não usadas
Recommendation: Usar as constantes do domínio em todos os pontos (PB-14).

### F-14 [LOW] Retornos booleanos verbosos e ifs aninhados (AP-24)
Files:
- models/task.py:38-60 — `validate_status`, `validate_priority`, `is_overdue` com if/else aninhados
- models/user.py:34-38 — `is_admin`
- utils/helpers.py:19-23, 52-55
Recommendation: Retornar a expressão booleana diretamente (PB-14).

### F-15 [LOW] `print` no lugar de logger (AP-22)
Files:
- routes/task_routes.py:149, 153, 219, 234
- routes/user_routes.py:83, 89, 147
- services/notification_service.py:21, 24
- utils/helpers.py:39, 41
Recommendation: `logging` com níveis (PB-14).

## Deprecated APIs
| Local | Uso deprecated | Substituto | Finding |
|---|---|---|---|
| routes/*.py (16 ocorrências, ver F-07) | `Model.query.get(id)` (SQLAlchemy 2.x, `LegacyAPIWarning`) | `db.session.get(Model, id)` | F-07 |
| models/*.py, routes/*.py, services, utils, seed (22 ocorrências) | `datetime.utcnow()` (Python 3.12, `DeprecationWarning`) | `datetime.now(timezone.utc)` via helper `utc_now()` | F-07 |

================================
Total: 15 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
