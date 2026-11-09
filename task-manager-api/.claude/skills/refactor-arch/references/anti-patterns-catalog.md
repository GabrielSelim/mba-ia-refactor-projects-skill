# Catálogo de Anti-patterns (Fase 2)

Cada entrada traz: **ID**, **severidade padrão**, **sinais de detecção** (o que procurar no código, por stack), a
**regra de ajuste** da severidade quando houver, e o **padrão do playbook** que corrige.

Escala de severidade:
- **CRITICAL** — segurança grave ou violação total de separação de responsabilidades;
- **HIGH** — violação forte de MVC/SOLID;
- **MEDIUM** — padronização, duplicação, performance moderada, validação;
- **LOW** — legibilidade.

---

## CRITICAL

### AP-01 — Credenciais e segredos hardcoded
- **Sinais:** literais atribuídos a `SECRET_KEY`, `password`, `pass`, `pwd`, `api_key`, `apiKey`, `token`, `secret`,
  `dbPass`, `paymentGatewayKey`, `smtp*`. Prefixos `pk_live_`, `sk_live_`, `AKIA`. Connection strings com usuário e
  senha. `app.config['SECRET_KEY'] = '...'`. Objetos `config = { ...: "..." }` com segredos.
- **Ajuste:** HIGH se o valor é claramente de desenvolvimento e não dá acesso a nada (ex.: só a porta).
- **Playbook:** PB-01.

### AP-02 — SQL Injection (query montada por concatenação ou interpolação)
- **Sinais:** `execute("... " + var)`, `execute(f"... {var}")`, `"... '%s'" % var`, template string
  `` `... ${var}` `` passada a `db.run/get/all/query`, `LIKE '%" + termo + "%'`. Inclui IDs numéricos concatenados
  (`WHERE id = " + str(id)`).
- **Playbook:** PB-02.

### AP-03 — God Class / God File
- **Sinais:** um arquivo ou classe que contém **ao mesmo tempo** acesso a banco (SQL/ORM), regra de negócio e
  roteamento/HTTP. Ou um arquivo único servindo vários domínios (produtos + usuários + pedidos). Classes chamadas
  `*Manager`, `*Utils` com dezenas de responsabilidades. Métodos com mais de 50 linhas e vários níveis de aninhamento.
- **Ajuste:** HIGH se o arquivo mistura só duas das três responsabilidades.
- **Playbook:** PB-03, PB-04.

### AP-04 — Endpoint de execução arbitrária ou destrutivo sem proteção
- **Sinais:** rota que recebe SQL/código no body e executa (`cursor.execute(dados['sql'])`, `eval`, `exec`,
  `child_process.exec(req.body...)`). Rotas `/admin/*`, `reset`, `drop`, `delete-all` sem autenticação ou
  autorização.
- **Playbook:** PB-15.

### AP-05 — Exposição de dados sensíveis
- **Sinais:** respostas JSON com `senha`, `password`, `pass`, hash de senha, `secret_key` ou config interna.
  `to_dict()` incluindo a senha. Logs (`print`, `console.log`) com número de cartão, senha ou chave
  (`console.log(\`... ${cc} ... ${key}\`)`). Mensagens de exceção cruas devolvidas ao cliente (`str(e)`).
- **Playbook:** PB-10, PB-08.

### AP-06 — Armazenamento de senha inseguro
- **Sinais:** senha gravada em texto puro (`INSERT ... senha ... VALUES ('" + senha`), comparação direta
  `WHERE senha = '...'`, hash fraco ou rápido (`md5`, `sha1` sem salt), "criptografia" caseira (base64 repetido,
  `badCrypto`).
- **Ajuste:** texto puro → CRITICAL; MD5/SHA1/caseiro → CRITICAL quando os hashes são expostos ou usados em login.
  HIGH nos outros casos.
- **Playbook:** PB-09.

---

## HIGH

### AP-07 — Regra de negócio no controller/rota (Fat Controller)
- **Sinais:** handlers de rota com validação extensa, cálculos (totais, descontos, estatísticas), loops sobre
  entidades, chamadas a ORM/SQL e formatação, tudo no mesmo corpo. Funções de rota com mais de 30 linhas. Regras de
  domínio (ex.: "atrasada se due_date < agora e status não final") escritas dentro da rota.
- **Playbook:** PB-04.

### AP-08 — Estado global mutável
- **Sinais:** `global db_connection`, variáveis de módulo reatribuídas (`let globalCache = {}`,
  `let totalRevenue = 0`), singletons mutáveis compartilhados entre requisições, listas de módulo usadas como
  armazenamento (`self.notifications = []` em uma instância global).
- **Playbook:** PB-05.

### AP-09 — Acoplamento forte sem injeção de dependência
- **Sinais:** handlers que instanciam dependências (`new sqlite3.Database` no construtor da classe de rotas,
  `NotificationService()` dentro da função), imports diretos de conexão global em todas as camadas, `require`/`import`
  de implementações concretas sem composition root.
- **Playbook:** PB-06.

### AP-10 — Escrita em várias etapas sem transação / integridade quebrada
- **Sinais:** vários `INSERT/UPDATE/DELETE` relacionados (pedido + itens + estoque; matrícula + pagamento + auditoria)
  sem `BEGIN/COMMIT/ROLLBACK`. `DELETE` de entidade-pai deixando filhos órfãos (mensagem "ficaram sujos no banco").
  Validação de estoque fora da transação.
- **Playbook:** PB-12.

### AP-11 — Configuração insegura de execução
- **Sinais:** `debug=True` / `DEBUG = True` fixo, `app.run(host='0.0.0.0', debug=True)`, `CORS(app)` liberando todas
  as origens sem configuração, flags de ambiente "produção" fixas no código.
- **Playbook:** PB-01.

### AP-12 — Autenticação falsa ou ausente
- **Sinais:** token previsível (`'fake-jwt-token-' + id`), login que retorna o usuário sem gerar credencial
  verificável, rotas administrativas sem nenhum controle de acesso.
- **Ajuste:** CRITICAL só quando a rota desprotegida permite execução arbitrária ou destruição em massa (nesse caso
  registre como AP-04).
- **Playbook:** PB-09 (token assinado), aplicado automaticamente quando não muda o contrato (o campo `token`
  continua existindo). Exigir autenticação em rotas hoje públicas muda o contrato e vai para "Pending
  recommendations". PB-15 só é aplicado automaticamente aos casos AP-04.

---

## MEDIUM

### AP-13 — Queries N+1
- **Sinais:** query dentro de `for`/`forEach` sobre o resultado de outra query (`for row in rows: cursor.execute(...)`,
  `Model.query.get(t.user_id)` no loop, `db.get` em `enrollments.forEach`). `len(u.tasks)` em lista de usuários com
  lazy loading. Várias contagens separadas (`count()` por status) que caberiam em um `GROUP BY`.
- **Playbook:** PB-07.

### AP-14 — Código duplicado
- **Sinais:** o mesmo bloco de serialização de linha → dict repetido em várias funções, a mesma validação repetida em
  create/update, a mesma regra (ex.: cálculo de "overdue") copiada em 3 ou mais lugares, listas de valores válidos
  repetidas.
- **Playbook:** PB-04, PB-14.

### AP-15 — Validação de entrada ausente ou inconsistente
- **Sinais:** `request.get_json()` usado sem checar `None`, campos numéricos sem checagem de tipo
  (`priority < 1` com string quebra), body acessado sem validação (`req.body.x`), update que aceita qualquer campo,
  validação diferente entre create e update.
- **Playbook:** PB-04.

### AP-16 — Tratamento de erros genérico / sem centralização
- **Sinais:** `except:` sem tipo, `except Exception as e: return jsonify({'erro': str(e)}), 500` repetido em cada
  handler, callbacks que ignoram `err`, ausência de `@app.errorhandler` / middleware `(err, req, res, next)`.
- **Playbook:** PB-08.

### AP-17 — Callback hell / fluxo assíncrono frágil
- **Sinais:** mais de 3 níveis de callbacks aninhados, contadores manuais (`pending--; if (pending === 0)`) para saber
  quando terminou, `res` respondido de dentro de callbacks profundos.
- **Playbook:** PB-11.

### AP-18 — Efeitos colaterais acoplados ao fluxo HTTP
- **Sinais:** envio de e-mail, SMS, push, pagamento ou escrita em cache dentro do handler da rota (`print("ENVIANDO
  EMAIL...")`, `smtplib` chamado na rota, gateway de pagamento simulado inline).
- **Playbook:** PB-06.

### AP-19 — APIs deprecated
Cruze com a **versão detectada** na Fase 1 e recomende o equivalente moderno:

| Stack | Uso deprecated (sinal) | Substituto moderno |
|---|---|---|
| SQLAlchemy ≥ 2.0 / Flask-SQLAlchemy ≥ 3.0 | `Model.query.get(id)` | `db.session.get(Model, id)` |
| SQLAlchemy ≥ 2.0 | `session.query(X).get(id)` | `session.get(X, id)` |
| Python ≥ 3.12 | `datetime.utcnow()`, `datetime.utcfromtimestamp()` | `datetime.now(timezone.utc)` (ou helper que remove o tzinfo, se o banco guarda datetime naive) |
| Flask ≥ 2.3 | `@app.before_first_request` | executar no `create_app()` / `with app.app_context()` |
| Flask ≥ 2.3 | `app.json_encoder` / `flask.json.JSONEncoder` | `app.json` provider (`DefaultJSONProvider`) |
| Python | `pkg_resources` | `importlib.metadata` |
| Node.js | `new Buffer(x)` | `Buffer.from(x)` |
| Node.js | `url.parse()` | `new URL()` (WHATWG) |
| Node.js | `crypto.createCipher()` | `crypto.createCipheriv()` |
| Node.js | `fs.exists()` | `fs.existsSync()` / `fs.promises.access()` |
| Express 4 → 5 | `req.param('x')`, `res.send(statusNumber)`, `res.json(status, body)` | `req.params/query/body`, `res.sendStatus()`, `res.status(s).json(body)` |
| Express | `body-parser` separado | `express.json()` / `express.urlencoded()` |
| Mongoose | `findByIdAndRemove`, `remove()` | `findByIdAndDelete`, `deleteOne()` |

- **Ajuste:** LOW se o uso só gera warning e não há previsão de remoção. MEDIUM quando já foi removido na próxima
  major ou gera `LegacyAPIWarning` / `DeprecationWarning` em runtime.
- Se não houver nenhum uso, registre na seção "Deprecated APIs" do relatório: "Nenhuma API deprecated encontrada
  para as versões detectadas".
- **Playbook:** PB-13.

---

## LOW

### AP-20 — Magic numbers / strings
- **Sinais:** limites e percentuais soltos (`if faturamento > 10000: desconto = faturamento * 0.1`), listas de status
  literais espalhadas, portas e tamanhos (`len(senha) < 4`) sem constante nomeada.
- **Playbook:** PB-14.

### AP-21 — Nomenclatura ruim
- **Sinais:** variáveis de uma letra ou abreviações opacas (`u`, `e`, `p`, `cid`, `cc`, `t`, `d`), nomes que mentem
  (`badCrypto`, `AppManager`), parâmetros que sombreiam builtins (`id`, `type`, `input`).
- **Playbook:** PB-14.

### AP-22 — `print`/`console.log` no lugar de logger
- **Sinais:** `print(...)` / `console.log(...)` para eventos de negócio ou erros, sem nível nem estrutura.
- **Playbook:** PB-14.

### AP-23 — Imports não usados / código morto
- **Sinais:** `import os, sys, json, time` sem uso, funções nunca chamadas, variáveis exportadas sem uso
  (`totalRevenue`), constantes definidas e ignoradas (`VALID_STATUSES` declarada, mas a lista é repetida inline).
- **Playbook:** PB-14.

### AP-24 — Retornos booleanos verbosos / condicionais aninhadas
- **Sinais:** `if cond: return True else: return False`, `if a: if b: if c:` que cabe em uma expressão.
- **Playbook:** PB-14.

---

## Como deduplicar e escolher severidade

1. O mesmo AP em vários arquivos vira **um finding** com a lista de `arquivo:linha`.
2. Quando um trecho dispara dois APs, registre os dois só se as correções forem diferentes (ex.: AP-02 SQL injection
   e AP-06 senha em texto puro na mesma função de login). Senão, fique com o de maior severidade.
3. Um finding CRITICAL exige evidência de exploração ou exposição real no código, não uma hipótese.
