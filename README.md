# Skill `refactor-arch` — Refatoração Arquitetural Automatizada

Entrega do desafio do módulo **Desenvolvimento de Software e Aplicações com IA** (MBA em Engenharia de Software com
IA — Full Cycle). O enunciado original está no
[repositório base](https://github.com/devfullcycle/mba-ia-refactor-projects-skill).

A skill **`refactor-arch`** (Claude Code) audita e refatora projetos backend para o padrão MVC em 3 fases:
1. **Análise:** detecta stack, domínio, arquitetura e endpoints.
2. **Auditoria:** cruza o código com um catálogo de anti-patterns e gera um relatório com severidade e arquivo:linha,
   depois **pausa para confirmação**.
3. **Refatoração:** reestrutura para MVC e **valida** boot e endpoints contra um baseline.

Ela foi executada nos 3 projetos: dois em Python/Flask (um monolito, outro parcialmente organizado) e um em
Node.js/Express.

| O quê | Onde |
|---|---|
| Skill (idêntica nos 3 projetos) | `*/.claude/skills/refactor-arch/` (SKILL.md + 5 referências) |
| Relatórios da Fase 2 | [`reports/audit-project-1.md`](reports/audit-project-1.md), [`-2`](reports/audit-project-2.md), [`-3`](reports/audit-project-3.md) |
| Código refatorado (Fase 3) | `code-smells-project/`, `ecommerce-api-legacy/`, `task-manager-api/` |
| Evidências de validação | [`validation/`](validation/) (scripts de smoke test e logs antes e depois) |

---

## A) Análise Manual

Feita **antes** de escrever a skill, lendo os três projetos inteiros. Os problemas abaixo viraram os sinais de
detecção do catálogo.

### Projeto 1 — `code-smells-project` (Python/Flask, e-commerce)

| Severidade | Problema | Local (original) | Por que é relevante |
|---|---|---|---|
| CRITICAL | **SQL Injection**: todas as queries concatenam a entrada do usuário | `models.py:28, 109-111, 289-297` (e outras) | O login `' OR '1'='1' --` entra sem senha. Confirmado no baseline: **200**. |
| CRITICAL | **`POST /admin/query` executa qualquer SQL** e `/admin/reset-db` apaga o banco, sem autenticação | `app.py:47-78` | Uma requisição anônima destrói ou altera todos os dados. |
| CRITICAL | **Senhas em texto puro** e devolvidas em `GET /usuarios` | `database.py:76-78`, `models.py:83,99` | Vazamento direto de credenciais de todos os usuários. |
| CRITICAL | **SECRET_KEY hardcoded**, inclusive exposta no `/health` | `app.py:7`, `controllers.py:289` | Quem lê o código ou chama `/health` forja sessões e tokens. |
| HIGH | **Conexão global** compartilhada entre threads (`check_same_thread=False`) | `database.py:4-12` | Condições de corrida, sem isolamento por requisição. |
| HIGH | **Pedido sem transação**: valida o estoque e grava em passos separados | `models.py:133-169` | Pedido sem itens ou estoque inconsistente se algo falhar no meio. |
| MEDIUM | **N+1** na listagem de pedidos (query por pedido e por item) | `models.py:171-233` | 1 + P + P×I queries, com latência crescente. |
| MEDIUM | **Validação frágil**: `preco` string gera 500, quantidade negativa aumenta o estoque | `controllers.py:43, 195-201` | Erros 500 triviais e regra de estoque burlável. |
| LOW | **Magic numbers** nas faixas de desconto | `models.py:256-262` | Regra de negócio escondida em literais. |
| LOW | **`print`** no lugar de logger | `controllers.py` (12 pontos) | Sem nível, sem estrutura e sem como filtrar. |

### Projeto 2 — `ecommerce-api-legacy` (Node.js/Express, LMS com checkout)

| Severidade | Problema | Local (original) | Por que é relevante |
|---|---|---|---|
| CRITICAL | **Chave live do gateway** (`pk_live_...`) e senha do banco no código | `src/utils.js:1-7` | Permite cobrar cartões com a conta da empresa. |
| CRITICAL | **Número do cartão e chave logados** a cada checkout | `src/AppManager.js:45` | Viola PCI-DSS: dados de cartão vão para os logs. |
| CRITICAL | **God Class `AppManager`**: banco, schema, seed, rotas e regras em uma classe | `src/AppManager.js:4-139` | Nada é testável nem substituível. |
| CRITICAL | **`badCrypto`**: "hash" base64 truncado e senha padrão "123456" | `src/utils.js:17-23`, `AppManager.js:68` | Senhas recuperáveis e contas com senha conhecida. |
| HIGH | **Exclusão deixa órfãos**, e o checkout grava 3 tabelas sem transação | `AppManager.js:50-62, 131-136` | O baseline mostra alunos "Unknown" no relatório depois do DELETE. |
| MEDIUM | **N+1** no relatório financeiro (1 + C + 2×M queries) | `AppManager.js:83-127` | Degrada com o número de matrículas. |
| MEDIUM | **Callback hell** com contadores manuais | `AppManager.js:37-77, 83-128` | Risco de responder duas vezes ou nunca. |
| LOW | **Nomes opacos** (`u`, `e`, `p`, `cid`, `cc`) | `AppManager.js:29-33` | Leitura e manutenção difíceis. |
| LOW | **Código morto** (`totalRevenue`, `globalCache` nunca lido, `dbUser`) | `src/utils.js:2-15` | Ruído e falsa sensação de funcionalidade. |

### Projeto 3 — `task-manager-api` (Python/Flask, gerenciador de tarefas, parcialmente organizado)

| Severidade | Problema | Local (original) | Por que é relevante |
|---|---|---|---|
| CRITICAL | **Hash de senha MD5** e **exposto** em todas as respostas de usuário | `models/user.py:16-32` | Hash MD5 sem salt exposto equivale à senha. |
| CRITICAL | **SECRET_KEY e senha SMTP hardcoded** | `app.py:13`, `services/notification_service.py:7-10` | Credenciais versionadas. |
| HIGH | **Token falso** `'fake-jwt-token-' + id` | `routes/user_routes.py:210` | Qualquer um fabrica o token de qualquer usuário. |
| HIGH | **Regra de negócio nas rotas**: não há camada de controller, e categorias vivem no blueprint de relatórios | `routes/task_routes.py:85-223`, `routes/report_routes.py:12-223` | O projeto *parece* organizado, mas as rotas fazem tudo. |
| MEDIUM | **APIs deprecated**: `Query.get()` (16×) e `datetime.utcnow()` (22×) | `routes/*.py`, `models/*.py` | `LegacyAPIWarning` e `DeprecationWarning` em runtime, confirmados no baseline. |
| MEDIUM | **N+1** em `/tasks`, `/users`, `/reports/summary`, `/categories` | `routes/task_routes.py:41-57` e outros | Queries proporcionais ao número de registros. |
| MEDIUM | **Validação de tipo ausente**: `priority: "alta"` e `?priority=abc` dão **500** | `routes/task_routes.py:113, 261` | Erro interno com entrada trivial, confirmado no baseline. |
| LOW | **Imports e dependências mortos** (`os`, `sys`, `json`, `marshmallow`, `requests`) | `app.py:7`, `requirements.txt` | Ruído e superfície de dependências desnecessária. |
| LOW | **Regra "overdue" copiada 6 vezes** enquanto `Task.is_overdue()` existe | `routes/*.py` | Regras divergentes ao corrigir uma só cópia. |

---

## B) Construção da Skill

### Decisões de design

```
.claude/skills/refactor-arch/
├── SKILL.md                              # o "prompt": papel, regras e as 3 fases com formatos de saída
└── references/
    ├── project-analysis.md               # Fase 1: heurísticas de linguagem, framework, banco, domínio, arquitetura
    ├── anti-patterns-catalog.md          # Fase 2: 24 anti-patterns com sinais de detecção e severidade
    ├── report-template.md                # Fase 2: formato exato do relatório + exemplos bom e ruim
    ├── mvc-guidelines.md                 # Fase 3: camadas, direção de dependências, estrutura por stack
    └── refactoring-playbook.md           # Fase 3: 15 transformações (PB-01..PB-15) com antes/depois
```

- **O SKILL.md diz o *quê* e o *quando*; as referências trazem o *conhecimento*.** O SKILL.md fica curto e manda
  ler a referência certa no início de cada fase, o que mantém o contexto enxuto.
- **Saídas com formato fixo** (blocos `PHASE 1`, `ARCHITECTURE AUDIT REPORT`, `PHASE 3`). Isso torna as execuções
  comparáveis entre projetos e faz o relatório seguir sempre o mesmo template.
- **IDs ligando catálogo e playbook:** cada anti-pattern (`AP-xx`) aponta o padrão de correção (`PB-xx`), e cada
  finding do relatório aponta ambos. A Fase 3 vira um mapeamento finding → transformação → arquivo.
- **Pausa obrigatória** depois do relatório (`Proceed with refactoring (Phase 3)? [y/n]`), proibindo qualquer
  escrita antes do "y".
- **Validação contra baseline:** a Fase 3 começa subindo a aplicação *original* e registrando status e chaves de cada
  endpoint. No fim, refaz as mesmas chamadas. "Endpoints funcionando" passa a ser uma comparação objetiva, e não uma
  impressão.
- **Regra de contrato:** preservar rotas, métodos e formato de sucesso. As únicas exceções permitidas, sempre
  listadas, são: remover dados sensíveis, proteger execução arbitrária (AP-04) e padronizar erros. Mudanças que
  exigem decisão de produto (por exemplo, exigir login em rotas públicas) vão para "Pending recommendations", sem
  aplicação automática.

### Anti-patterns do catálogo (24, com severidade distribuída)

| Severidade | Anti-patterns | Por que entraram |
|---|---|---|
| CRITICAL | AP-01 segredos hardcoded · AP-02 SQL injection · AP-03 God Class/File · AP-04 endpoint de execução arbitrária/destrutivo · AP-05 exposição de dados sensíveis · AP-06 senha insegura | Os problemas que comprometem dados ou impedem qualquer evolução, todos presentes em pelo menos um projeto |
| HIGH | AP-07 regra no controller/rota · AP-08 estado global mutável · AP-09 acoplamento sem DI · AP-10 escrita sem transação/órfãos · AP-11 debug/CORS inseguro · AP-12 autenticação falsa/ausente | Violações de MVC e SOLID que travam teste e manutenção |
| MEDIUM | AP-13 N+1 · AP-14 duplicação · AP-15 validação ausente · AP-16 erro genérico · AP-17 callback hell · AP-18 efeito colateral no fluxo HTTP · **AP-19 APIs deprecated** | Performance e padronização. O AP-19 traz uma tabela por stack (SQLAlchemy 2.x, Python 3.12, Flask 2.3+, Node, Express 5, Mongoose) com o substituto moderno |
| LOW | AP-20 magic numbers · AP-21 nomes ruins · AP-22 print/console.log · AP-23 código morto · AP-24 booleanos verbosos | Legibilidade |

Cada entrada tem **sinais concretos** (por exemplo `execute("..." + var)`, `` `...${var}` `` passado a
`db.run`, `Model.query.get(`, `for row in rows: cursor.execute(`), e não descrições vagas. Os sinais vieram
diretamente da análise manual.

### Como a skill é agnóstica de tecnologia

- A Fase 1 **detecta** a stack pelo manifesto e confirma pelos imports, sem assumir nada (`project-analysis.md`
  cobre Python, Node/TS, Java, Go, Ruby, PHP e C#).
- Os sinais de detecção são escritos **por stack** (Flask, Express, FastAPI, Django) quando a sintaxe difere.
- `mvc-guidelines.md` tem **variantes de estrutura**: Flask monolito, Flask parcialmente organizado, Express e
  princípios para FastAPI, Django e Spring. A Fase 3 escolhe a variante e **adapta ao ponto de partida**: cria tudo no
  monolito e preserva o que já está certo no projeto parcial.
- O playbook mostra cada transformação em **Python e JavaScript**.
- A validação tem **fallback em container**: se o runtime não estiver instalado, usa a imagem Docker oficial da
  linguagem.
- **Prova:** a mesma pasta da skill, byte a byte (`diff -r` sem diferenças), rodou nos 3 projetos.

### Desafios encontrados e como resolvi

1. **Quando bloquear um endpoint inseguro?** A primeira versão da regra mandava "proteger endpoints destrutivos sem
   autenticação". Aplicada ao projeto 2, isso bloquearia o `DELETE /api/users/:id` e quebraria o contrato. Refinei o
   catálogo (AP-12) e o SKILL.md: só a **execução arbitrária ou destruição em massa (AP-04)** é protegida
   automaticamente. CRUD sem autenticação vira recomendação pendente.
2. **"Endpoints funcionando" é subjetivo.** Resolvi com o baseline: smoke test igual antes e depois. No projeto 3
   fui além e comparei os **valores** dos relatórios, porque troquei loops N+1 por `GROUP BY`. Os 6 conjuntos de
   valores ficaram idênticos ([`validation/logs/project3-values-*.json`](validation/logs/)).
3. **Projeto parcialmente organizado.** Reescrever tudo seria desnecessário e arriscado. A variante "parcialmente
   organizado" das guidelines preserva `models/`, `routes/` e `services/`, cria só `controllers/`, `config/` e
   `middlewares/`, e move categorias para um blueprint próprio.
4. **Migração de senhas sem quebrar logins.** Trocar o MD5 (ou o texto puro) por hash forte invalidaria bancos
   existentes. O playbook (PB-09) prevê verificar o hash legado uma última vez e migrá-lo no login.
5. **Ambiente sem Python.** A máquina de execução não tinha Python. Por isso a skill ganhou a instrução de fallback
   em Docker, e a validação dos projetos Flask rodou em `python:3.12-slim`.
6. **Encerrar o processo de teste com segurança.** Para parar a API Node depois do smoke test, a primeira tentativa
   matava todos os processos `node.exe`, e foi barrada. Troquei por um harness que sobe a app como processo filho e
   encerra só ele.

---

## C) Resultados

### Resumo das auditorias (Fase 2)

| Projeto | Stack detectada | CRITICAL | HIGH | MEDIUM | LOW | Total | Deprecated |
|---|---|---|---|---|---|---|---|
| 1 — code-smells-project | Python + Flask 3.1.1 | 6 | 5 | 5 | 4 | **20** | nenhuma (Flask 3.1 em uso correto) |
| 2 — ecommerce-api-legacy | Node.js + Express 4.22.1 | 4 | 5 | 4 | 4 | **17** | nenhuma |
| 3 — task-manager-api | Python + Flask 3.0.0 / SQLAlchemy | 3 | 3 | 5 | 4 | **15** | `Query.get()` (16×), `datetime.utcnow()` (22×) |

### Estrutura antes → depois

**Projeto 1** — monolito de 4 arquivos → MVC em `src/`
```
ANTES                          DEPOIS
app.py         (rotas+admin)   app.py                       (runner)
controllers.py (HTTP+SQL)      src/app.py                   (composition root)
models.py      (4 domínios)    src/config/settings.py
database.py    (global)        src/database.py              (conexão por request + transaction)
                               src/errors.py
                               src/models/{produto,usuario,pedido}_model.py
                               src/controllers/{produto,usuario,pedido,system}_controller.py + validators.py
                               src/views/routes.py
                               src/services/notification_service.py
                               src/middlewares/{error_handler,admin_auth}.py
```

**Projeto 2** — God Class → MVC com injeção de dependência
```
ANTES                          DEPOIS
src/app.js                     src/server.js                (entry: dependências concretas)
src/AppManager.js (tudo)       src/app.js                   (createApp({ db, paymentGateway, passwordHasher, logger }))
src/utils.js (segredos+cache)  src/config/index.js · src/errors.js
                               src/database/{connection,schema}.js
                               src/models/index.js
                               src/controllers/{checkout,report,user}Controller.js
                               src/routes/index.js
                               src/services/{paymentGateway,passwordHasher,logger}.js
                               src/middlewares/{asyncHandler,errorHandler}.js
```

**Projeto 3** — camadas parciais → MVC completo (preservando o que estava certo)
```
ANTES                          DEPOIS
app.py (config hardcoded)      app.py                       (create_app + runner)
                               config/settings.py           (NOVO)
                               errors.py                    (NOVO)
models/ (MD5, password exposto) models/                     (mantido, corrigido)
                               controllers/                 (NOVO: task, user, report, category, validators)
routes/ (regra de negócio)     routes/                      (só URL → controller; + category_routes.py)
services/ (SMTP hardcoded)     services/                    (config injetada; + auth_service.py)
                               middlewares/error_handler.py (NOVO)
utils/helpers.py (código morto) utils/helpers.py            (constantes + helpers puros)
```

### Checklist de validação

| Item | Projeto 1 | Projeto 2 | Projeto 3 |
|---|---|---|---|
| **Fase 1** — Linguagem detectada corretamente | ✅ Python | ✅ JavaScript/Node | ✅ Python |
| Framework detectado corretamente | ✅ Flask 3.1.1 | ✅ Express 4.22.1 | ✅ Flask 3.0.0 + SQLAlchemy |
| Domínio descrito corretamente | ✅ E-commerce | ✅ LMS com checkout | ✅ Task Manager |
| Nº de arquivos condiz com a realidade | ✅ 4 | ✅ 3 | ✅ 15 |
| **Fase 2** — Relatório segue o template | ✅ | ✅ | ✅ |
| Cada finding com arquivo e linhas exatos | ✅ | ✅ | ✅ |
| Ordenado CRITICAL → LOW | ✅ | ✅ | ✅ |
| Mínimo de 5 findings | ✅ 20 | ✅ 17 | ✅ 15 |
| APIs deprecated (se aplicável) | ✅ verificado: nenhuma | ✅ verificado: nenhuma | ✅ 2 APIs, 38 usos |
| Pausa e pede confirmação antes da Fase 3 | ✅ | ✅ | ✅ |
| **Fase 3** — Estrutura MVC | ✅ | ✅ | ✅ |
| Configuração extraída (sem hardcoded) | ✅ `src/config/settings.py` | ✅ `src/config/index.js` | ✅ `config/settings.py` |
| Models abstraem os dados | ✅ | ✅ | ✅ |
| Views/Routes separadas | ✅ `src/views/routes.py` | ✅ `src/routes/index.js` | ✅ `routes/` |
| Controllers concentram o fluxo | ✅ | ✅ | ✅ |
| Error handling centralizado | ✅ | ✅ | ✅ |
| Entry point claro | ✅ `app.py` → `create_app()` | ✅ `server.js` → `createApp()` | ✅ `app.py` → `create_app()` |
| Aplicação inicia sem erros | ✅ | ✅ | ✅ |
| Endpoints originais respondem | ✅ 19/19 | ✅ 3/3 | ✅ 22/22 |

### Logs das aplicações rodando após a refatoração

Os logs completos estão em [`validation/logs/`](validation/logs/): `projectN-baseline.txt` (original),
`projectN-after.txt` (refatorado) e `projectN-phase3.md` (resumo da Fase 3). Trechos:

**Projeto 1** (`python app.py` em `python:3.12-slim`): mesmos status do baseline, exceto as correções intencionais.
```
POST   /login  (' OR '1'='1' --)    antes -> 200   depois -> 401    # SQL injection fechada
GET    /health                      antes: [..., 'secret_key', 'debug', 'db_path']   depois: ['counts','database','status','versao']
POST   /admin/query (sem token)     antes -> 200   depois -> 403
POST   /admin/query (token, DELETE)                depois -> 400    # só SELECT
GET    /produtos ... /relatorios/vendas            200 = 200 (todas as demais chamadas iguais)
```

**Projeto 2** (`npm start` → `node src/server.js`): 8/8 status idênticos.
```
2026-11-09T13:39:34.223Z INFO LMS API rodando na porta 3000
2026-11-09T13:39:34.372Z INFO payment_processing {"card_last4":"4444","amount":497,"live":false}
2026-11-09T13:39:34.419Z INFO checkout_completed {"course_id":2,"enrollment_id":2}
2026-11-09T13:39:34.507Z INFO user_deleted {"user_id":1}
report after delete (antes): [... {"student":"Unknown","paid":997} ...]   # órfãos
report after delete (depois): [{"course":"Clean Architecture","revenue":0,"students":[]}, ...]  # cascata
```

**Projeto 3** (`python seed.py && python app.py`): 22 endpoints respondendo, com zero warnings.
```
POST   /tasks {"priority":"alta"}       antes -> 500 (TypeError, HTML)   depois -> 400 ['error']
GET    /tasks/search?priority=abc       antes -> 500 (ValueError, HTML)  depois -> 400 ['error']
GET    /users/1                         antes: [..., 'password', ...]    depois: sem 'password'
APP LOG antes: 17 linhas distintas de LegacyAPIWarning/DeprecationWarning   depois: nenhuma
values (stats, summary, user_report, users, categories, tasks): IGUAL nas 6 comparações
```

### Observações sobre o comportamento em stacks diferentes

- **Monolito (projetos 1 e 2):** a skill criou todas as camadas. No Express, o foco extra foi o fluxo assíncrono:
  helpers com Promise, `async/await` e uma fila de transações sobre a conexão única do SQLite. Isso não existe no
  Flask.
- **Projeto parcial (projeto 3):** a mudança estrutural foi menor (controllers e config), e a maior parte do
  ganho veio de segurança, APIs deprecated e N+1. O relatório mostra que "ter pastas" não é ter MVC: a regra estava
  toda nas rotas.
- **Deprecated APIs:** só apareceram onde a versão da stack torna o uso obsoleto (SQLAlchemy 2.x e Python 3.12 no
  projeto 3). Nos outros dois a skill registrou explicitamente "nenhuma", em vez de inventar achados.
- **Contrato:** nos 3 projetos as mudanças de contrato ficaram restritas às categorias permitidas e foram
  declaradas. Autenticação nas rotas públicas ficou como recomendação pendente nos três, porque é decisão de
  produto.

### Como a skill foi executada

A execução foi feita pelo **Claude Code** (app desktop, modelo Claude Opus 5.5), seguindo o `SKILL.md` de cada
projeto fase a fase. O CLI `claude` não estava instalado nesta máquina, por isso a skill não foi disparada por
`claude "/refactor-arch"`. Depois da Fase 2, a execução **parou e pediu confirmação**, e a Fase 3 só começou com o
"y" do autor. A validação usou:
- o Node local para o projeto 2;
- containers `python:3.12-slim` para os projetos Flask.

---

## D) Como Executar

### Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) instalado e autenticado
  (`npm install -g @anthropic-ai/claude-code`).
- Python 3.10+ (projetos 1 e 3) e Node.js 18+ (projeto 2), ou Docker para rodar a validação em container.

### Executar a skill em cada projeto

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch audit-project-1"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch audit-project-2"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch audit-project-3"
```

O argumento define o nome do relatório salvo em `reports/` (sem argumento: `audit-<pasta>.md`). Depois da Fase 2,
responda `y` para a refatoração ou `n` para parar só com o relatório.

> Como este repositório já contém o código refatorado, para reproduzir do zero faça checkout do commit anterior à
> refatoração: `git checkout b076a74 -- code-smells-project ecommerce-api-legacy task-manager-api`.

### Validar que a refatoração funcionou

```bash
# Projeto 1
cd code-smells-project && pip install -r requirements.txt
ADMIN_TOKEN=dev-token python app.py &
python ../validation/smoke_project1.py http://127.0.0.1:5000 dev-token

# Projeto 2
cd ecommerce-api-legacy && npm install && npm start &
node ../validation/smoke_project2.js http://127.0.0.1:3000

# Projeto 3
cd task-manager-api && pip install -r requirements.txt
python seed.py && python app.py &
python ../validation/smoke_project3.py http://127.0.0.1:5000
python ../validation/values_project3.py http://127.0.0.1:5000   # valores agregados
```

Compare a saída com `validation/logs/projectN-baseline.txt`. Os status devem ser os mesmos, exceto as mudanças
intencionais listadas em `validation/logs/projectN-phase3.md`.
