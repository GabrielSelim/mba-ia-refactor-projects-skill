# Playbook de Refatoração (Fase 3)

Cada padrão (PB-xx) corrige um ou mais anti-patterns (AP-xx) do catálogo. Os exemplos mostram **antes → depois** em
Python/Flask e Node/Express. Adapte a outras stacks mantendo a mesma ideia.

---

## PB-01 — Extrair configuração e segredos para o ambiente (AP-01, AP-11)

**Antes (Python)**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.run(host="0.0.0.0", port=5000, debug=True)
```
**Depois**
```python
# src/config/settings.py
import os, secrets

class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)   # dev: aleatória por boot
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")

# app.py (runner)
app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
```

**Antes (Node)**
```js
const config = { dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_1234567890abcdef", port: 3000 };
```
**Depois**
```js
// src/config/index.js
module.exports = Object.freeze({
  port: Number(process.env.PORT) || 3000,
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',   // nunca uma chave live no código
  dbPath: process.env.DB_PATH || ':memory:',
});
```

---

## PB-02 — Queries parametrizadas (AP-02)

**Antes**
```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
query += " AND (nome LIKE '%" + termo + "%')"
```
**Depois**
```python
cursor.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
clauses.append("(nome LIKE ? OR descricao LIKE ?)")
params += [f"%{termo}%", f"%{termo}%"]
cursor.execute(f"SELECT * FROM produtos WHERE {' AND '.join(clauses)}", params)  # só nomes fixos interpolados
```
**Node**
```js
// antes: db.get(`SELECT * FROM users WHERE email = '${email}'`)
db.get('SELECT * FROM users WHERE email = ?', [email]);
```

---

## PB-03 — Quebrar o God File/Class em camadas por domínio (AP-03)

**Antes:** `models.py` com SQL + regras de produtos, usuários, pedidos e relatórios; `AppManager.js` com schema,
rotas, regra e banco.

**Depois:** um arquivo por domínio em cada camada.
```
models/produto_model.py      controllers/produto_controller.py
models/usuario_model.py      controllers/usuario_controller.py
models/pedido_model.py       controllers/pedido_controller.py
views/routes.py              (mapeia todas as URLs para os controllers)
```
```js
// AppManager.setupRoutes(app)  →
// routes/index.js
router.post('/api/checkout', asyncHandler(checkoutController.checkout));
router.get('/api/admin/financial-report', asyncHandler(reportController.financialReport));
```
Passos:
1. Liste as responsabilidades do arquivo.
2. Crie os módulos destino.
3. Mova as funções sem mudar a lógica.
4. Ajuste os imports.
5. Valide.
6. Só então melhore o código interno.

---

## PB-04 — Tirar regra de negócio e validação da rota (AP-07, AP-14, AP-15)

**Antes**
```python
@task_bp.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    if not data.get('title'): return jsonify({'error': 'Título é obrigatório'}), 400
    if data.get('status') not in ['pending', 'in_progress', 'done', 'cancelled']: ...
    task = Task(); task.title = data['title']; db.session.add(task); db.session.commit()
    return jsonify(task.to_dict()), 201
```
**Depois**
```python
# routes/task_routes.py (View)
@task_bp.route('/tasks', methods=['POST'])
def create_task():
    return jsonify(task_controller.create_task(request.get_json(silent=True))), 201

# controllers/task_controller.py
def create_task(data):
    payload = validate_task_payload(data, partial=False)   # lança ValidationError
    _ensure_relations_exist(payload)                         # lança NotFoundError
    return task_model.create(payload).to_dict()
```
A validação vive em uma função única, reutilizada por create e update (`partial=True`), e acaba com a duplicação.

---

## PB-05 — Eliminar estado global mutável (AP-08)

**Antes**
```python
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(db_path, check_same_thread=False)
    return db_connection
```
**Depois** (conexão por requisição, fechada no teardown)
```python
from flask import g, current_app

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_app(app):
    app.teardown_appcontext(close_db)
```
**Node:** troque `let globalCache = {}` exportado por uma instância criada no composition root e injetada
(`createCache()`), ou remova-a se ninguém lê o cache.

---

## PB-06 — Injeção de dependência pelo composition root (AP-09, AP-18)

**Antes**
```js
class AppManager {
  constructor() { this.db = new sqlite3.Database(':memory:'); }
  setupRoutes(app) { app.post('/api/checkout', (req, res) => { /* usa this.db, cobra o cartão inline */ }); }
}
```
**Depois**
```js
// src/app.js
function createApp({ db, paymentGateway, passwordHasher }) {
  const models = createModels(db);
  const controllers = {
    checkout: createCheckoutController({ models, paymentGateway, passwordHasher, db }),
    report: createReportController({ models }),
  };
  const app = express();
  app.use(express.json());
  app.use(buildRouter(controllers));
  app.use(errorHandler);
  return app;
}
```
**Python (efeitos colaterais):**
```python
# antes, no controller: print("ENVIANDO EMAIL: ..."); print("ENVIANDO SMS: ...")
notification_service.notify_order_created(pedido_id, usuario_id)   # service com logger, substituível em testes
```

---

## PB-07 — Eliminar N+1 (AP-13)

**Antes (SQL cru)**
```python
for row in pedidos:
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    for item in itens:
        cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```
**Depois:** uma query com JOIN e agrupamento em memória.
```python
rows = db.execute("""
    SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
           i.produto_id, i.quantidade, i.preco_unitario, pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
    ORDER BY p.id""").fetchall()
```
**Depois (SQLAlchemy)**
```python
from sqlalchemy.orm import joinedload
tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
counts = dict(db.session.query(Task.status, func.count(Task.id)).group_by(Task.status).all())
```
**Depois (Node, relatório)**
```js
const rows = await db.all(`
  SELECT c.id AS course_id, c.title, u.name AS student, p.amount, p.status
  FROM courses c
  LEFT JOIN enrollments e ON e.course_id = c.id
  LEFT JOIN users u ON u.id = e.user_id
  LEFT JOIN payments p ON p.enrollment_id = e.id
  ORDER BY c.id`);
```

---

## PB-08 — Tratamento de erros centralizado (AP-16, AP-05)

**Antes**
```python
def listar_produtos():
    try:
        ...
    except Exception as e:
        return jsonify({"erro": str(e)}), 500      # repetido em 16 funções, vaza detalhes internos
```
**Depois (Flask)**
```python
# middlewares/error_handler.py
class AppError(Exception):
    status_code = 400
    def __init__(self, message): super().__init__(message); self.message = message
class NotFoundError(AppError): status_code = 404
class ValidationError(AppError): status_code = 400

def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"erro": err.message, "sucesso": False}), err.status_code

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        app.logger.exception("unhandled_error")
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500
```
**Depois (Express)**
```js
// middlewares/errorHandler.js
module.exports = (err, req, res, next) => {
  const status = err.statusCode || 500;
  if (status >= 500) console.error('[error]', err);
  res.status(status).json({ error: status >= 500 ? 'Erro interno' : err.message });
};
// middlewares/asyncHandler.js
module.exports = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
```

---

## PB-09 — Hash de senha forte e token assinado (AP-06, AP-12)

**Antes**
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()
'token': 'fake-jwt-token-' + str(user.id)
```
**Depois (sem dependência nova: werkzeug e itsdangerous já vêm com o Flask)**
```python
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer

def set_password(self, raw): self.password = generate_password_hash(raw)
def check_password(self, raw): return check_password_hash(self.password, raw)

def issue_token(user_id):
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="auth").dumps({"uid": user_id})
```
Hashes legados (MD5 de 32 caracteres hexadecimais) podem ser verificados uma última vez e migrados para o hash novo
no login.

**Node (crypto nativo)**
```js
// antes: badCrypto(pwd) — base64 repetido
const crypto = require('crypto');
function hashPassword(pwd) {
  const salt = crypto.randomBytes(16).toString('hex');
  return `${salt}:${crypto.scryptSync(pwd, salt, 64).toString('hex')}`;
}
```

---

## PB-10 — Remover dados sensíveis das respostas e dos logs (AP-05)

**Antes**
```python
def to_dict(self):
    return {"id": self.id, "email": self.email, "password": self.password}
# health: "secret_key": "minha-chave-super-secreta-123", "debug": True
```
```js
console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
```
**Depois**
```python
def to_dict(self):
    return {"id": self.id, "name": self.name, "email": self.email, "role": self.role}   # sem senha
# health: só status, database e contagens
```
```js
logger.info(`Processando pagamento do cartão final ${card.slice(-4)}`);   // nunca o PAN completo nem a chave
```

---

## PB-11 — Callback hell → async/await (AP-17)

**Antes**
```js
db.get(sqlA, [a], (err, course) => {
  db.get(sqlB, [b], (err, user) => {
    db.run(sqlC, [c], function (err) {
      db.run(sqlD, [d], function (err) { res.json(...); });
    });
  });
});
```
**Depois**
```js
// database/connection.js — helpers promisificados
const run = (sql, params = []) => new Promise((resolve, reject) =>
  db.run(sql, params, function (err) { err ? reject(err) : resolve({ lastID: this.lastID, changes: this.changes }); }));

// controller
const course = await models.courses.findActiveById(courseId);
const user = await models.users.findByEmail(email);
const enrollmentId = await db.transaction(async () => { /* ... */ });
res.json({ msg: 'Sucesso', enrollment_id: enrollmentId });
```

---

## PB-12 — Transação para escritas em várias etapas e integridade referencial (AP-10)

**Antes**
```python
cursor.execute("INSERT INTO pedidos ...")
for item in itens:
    cursor.execute("INSERT INTO itens_pedido ...")
    cursor.execute("UPDATE produtos SET estoque = estoque - ...")
db.commit()     # falha no meio deixa pedido sem itens ou estoque inconsistente
```
**Depois**
```python
with db:                         # sqlite3: commit no sucesso, rollback em exceção
    pedido_id = db.execute("INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
                           (usuario_id, total)).lastrowid
    db.executemany("INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                   [(pedido_id, i.produto_id, i.quantidade, i.preco) for i in itens])
```
**Node (DELETE sem órfãos)**
```js
await db.transaction(async () => {
  await db.run('DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)', [id]);
  await db.run('DELETE FROM enrollments WHERE user_id = ?', [id]);
  await db.run('DELETE FROM users WHERE id = ?', [id]);
});
```

---

## PB-13 — Substituir APIs deprecated (AP-19)

**Antes**
```python
user = User.query.get(user_id)                       # LegacyAPIWarning no SQLAlchemy 2.x
created_at = db.Column(db.DateTime, default=datetime.utcnow)   # DeprecationWarning no Python 3.12
```
**Depois**
```python
user = db.session.get(User, user_id)

# utils/time.py — mantém datetime naive em UTC, compatível com o que já está gravado no SQLite
from datetime import datetime, timezone
def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

created_at = db.Column(db.DateTime, default=utc_now)
```
**Node**
```js
new Buffer(str)   →   Buffer.from(str)
res.send(404)     →   res.sendStatus(404)
```

---

## PB-14 — Legibilidade: constantes, nomes, logger, imports (AP-20 a AP-24)

**Antes**
```python
if faturamento > 10000: desconto = faturamento * 0.1
elif faturamento > 5000: desconto = faturamento * 0.05
print("Produto criado com ID: " + str(id))
def is_admin(self):
    if self.role == 'admin': return True
    else: return False
```
**Depois**
```python
DISCOUNT_TIERS = ((10_000, 0.10), (5_000, 0.05), (1_000, 0.02))   # (faturamento mínimo, taxa)

def calcular_desconto(faturamento):
    return next((faturamento * taxa for minimo, taxa in DISCOUNT_TIERS if faturamento > minimo), 0)

logger.info("produto_criado id=%s", produto_id)

def is_admin(self):
    return self.role == ROLE_ADMIN
```
```js
// antes: let u = req.body.usr; let e = req.body.eml; let cc = req.body.card;
const { usr: name, eml: email, pwd: password, c_id: courseId, card: cardNumber } = req.body;
```
Remova imports sem uso (`import os, sys, json, time`) e variáveis exportadas mortas.

---

## PB-15 — Proteger ou desabilitar endpoints perigosos (AP-04, AP-12)

**Antes**
```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    cursor.execute(request.get_json()["sql"])    # qualquer SQL, sem autenticação
```
**Depois:** a rota existe (o contrato é preservado), mas exige um token administrativo configurado no ambiente. Sem
o token configurado, a rota fica desabilitada (403). SQL arbitrário fica restrito a leitura.
```python
# middlewares/admin_auth.py
def require_admin_token(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = current_app.config.get("ADMIN_TOKEN")
        given = request.headers.get("X-Admin-Token", "")
        if not expected or not hmac.compare_digest(given, expected):
            raise ForbiddenError("Acesso administrativo negado")
        return view(*args, **kwargs)
    return wrapper

# controllers/admin_controller.py
if not sql.lstrip().upper().startswith("SELECT"):
    raise ValidationError("Somente consultas SELECT são permitidas")
```
Registre essa mudança em "Contract changes (intentional)" no resumo da Fase 3.
