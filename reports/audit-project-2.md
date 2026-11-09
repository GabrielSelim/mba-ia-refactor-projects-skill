================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express 4.22.1
Files:   3 analyzed | ~180 lines of code
Date:    2026-11-09

## Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 4 | LOW: 4

## Findings

### F-01 [CRITICAL] Segredos de produção hardcoded (AP-01)
File: src/utils.js:1-7
Description: O objeto `config` contém `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"`
(chave **live** de gateway) e `smtpUser`, todos versionados no código.
Impact: Quem lê o repositório pode cobrar cartões com a conta da empresa e acessar o banco de produção.
Recommendation: `src/config/index.js` lendo `process.env`, sem chave live no código (PB-01).

### F-02 [CRITICAL] Número do cartão e chave do gateway escritos em log (AP-05)
File: src/AppManager.js:45
Description: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` registra o PAN completo e
a chave do gateway a cada checkout.
Impact: Violação de PCI-DSS. Os logs passam a conter dados de cartão e segredo de pagamento.
Recommendation: Logar só os 4 últimos dígitos e nunca a chave (PB-10).

### F-03 [CRITICAL] God Class: AppManager concentra banco, schema, seed, rotas e regras de negócio (AP-03)
Files:
- src/AppManager.js:4-139 — classe única
- src/AppManager.js:7 — cria a conexão
- src/AppManager.js:10-23 — schema e seed
- src/AppManager.js:25-138 — rotas
- src/AppManager.js:43-75 — regra de pagamento e matrícula
Description: Uma classe faz conexão com o banco, cria tabelas, popula dados, registra as 3 rotas, decide pagamento,
cria usuário e gera relatório.
Impact: Nada é testável isoladamente, e qualquer mudança mexe no arquivo inteiro.
Recommendation: Separar em `config/`, `database/`, `models/`, `controllers/`, `routes/` e `services/`, com
composition root (PB-03, PB-06).

### F-04 [CRITICAL] Armazenamento de senha com "criptografia" caseira e senhas em texto puro (AP-06)
Files:
- src/utils.js:17-23 — `badCrypto`: base64 da senha repetido e truncado em 10 caracteres
- src/AppManager.js:68 — usa `badCrypto(p || "123456")`: senha padrão quando ausente
- src/AppManager.js:18 — seed com senha `'123'` em texto puro
Description: O "hash" é determinístico, sem salt e reversível na prática (os 2 primeiros caracteres do base64 da
senha, repetidos). Usuários criados sem senha recebem "123456".
Impact: Qualquer leitura da tabela `users` revela as senhas, e contas novas ficam com senha conhecida.
Recommendation: `crypto.scrypt` com salt aleatório (nativo do Node), sem senha padrão (PB-09).

### F-05 [HIGH] Checkout e exclusão sem transação, deixando dados inconsistentes (AP-10)
Files:
- src/AppManager.js:50-62 — matrícula, pagamento e auditoria em 3 `INSERT`s encadeados sem transação
- src/AppManager.js:131-136 — `DELETE /api/users/:id` apaga só o usuário, e a própria resposta admite: "as matrículas e pagamentos ficaram sujos no banco"
Description: Uma falha no pagamento deixa matrícula sem pagamento, e excluir um usuário deixa matrículas e pagamentos
órfãos.
Impact: Relatório financeiro e acesso a cursos inconsistentes.
Recommendation: `BEGIN/COMMIT/ROLLBACK` no checkout e exclusão em cascata transacional (PB-12).

### F-06 [HIGH] Estado global mutável exportado (AP-08)
File: src/utils.js:9-15, 25
Description: `globalCache` (objeto de módulo que só cresce, com uma chave por usuário) e `totalRevenue` (`let`
exportado) ficam compartilhados entre requisições. O cache é escrito e nunca lido.
Impact: Vazamento de memória e estado que contamina testes.
Recommendation: Remover o cache morto ou criar uma instância injetada pelo composition root (PB-05).

### F-07 [HIGH] Acoplamento forte sem injeção de dependência (AP-09)
Files:
- src/AppManager.js:7 — `new sqlite3.Database(':memory:')` no construtor
- src/AppManager.js:46 — gateway de pagamento simulado inline (`cc.startsWith("4")`)
- src/app.js:8-10 — `new AppManager()` acoplado ao bootstrap
Description: O banco e o "gateway" são concretos e criados dentro da classe de rotas.
Impact: É impossível trocar o banco ou o gateway e testar o checkout sem o SQLite real.
Recommendation: Composition root `createApp({ db, paymentGateway, passwordHasher })` (PB-06).

### F-08 [HIGH] Regra de negócio dentro do handler HTTP (AP-07)
File: src/AppManager.js:28-78
Description: O handler de `/api/checkout` valida a entrada, busca o curso, cria o usuário com hash, decide o pagamento,
matricula, registra a auditoria e o cache, tudo dentro da closure da rota.
Impact: O fluxo de checkout não é reutilizável nem testável fora do Express.
Recommendation: `checkoutController` orquestrando models e services, com a rota só mapeando URL → controller (PB-04).

### F-09 [HIGH] Rotas administrativas e de exclusão sem autenticação (AP-12)
Files:
- src/AppManager.js:80 — `GET /api/admin/financial-report` expõe nomes de alunos e valores pagos
- src/AppManager.js:131 — `DELETE /api/users/:id` sem nenhum controle de acesso
Description: Não existe autenticação na API.
Impact: Qualquer cliente lê dados financeiros e apaga usuários.
Recommendation: Introduzir autenticação e autorização por papel. Muda o contrato público e depende de decisão
humana (PB-09).

### F-10 [MEDIUM] Queries N+1 no relatório financeiro (AP-13)
File: src/AppManager.js:83-127
Description: Para cada curso, 1 query de matrículas (92). Para cada matrícula, 1 query de usuário (104) e 1 de
pagamento (106). São 1 + C + 2×M queries.
Impact: O relatório degrada linearmente com o número de matrículas.
Recommendation: Uma query com `LEFT JOIN` entre courses, enrollments, users e payments, agrupada em memória (PB-07).

### F-11 [MEDIUM] Callback hell e controle manual de concorrência (AP-17)
Files:
- src/AppManager.js:37-77 — 5 níveis de callbacks aninhados no checkout
- src/AppManager.js:83-128 — contadores manuais `coursesPending--` e `enrPending--` para saber quando responder
Description: O fluxo assíncrono depende de aninhamento e contadores mutáveis.
Impact: Fácil responder duas vezes ou nunca responder. A leitura é difícil.
Recommendation: Helpers promisificados e `async/await` (PB-11).

### F-12 [MEDIUM] Erros ignorados e sem tratamento central (AP-16)
Files:
- src/AppManager.js:57 — erro do INSERT de auditoria ignorado
- src/AppManager.js:92-93 — `err` ignorado, e `enrollments.length` quebra o processo se a query falhar
- src/AppManager.js:104, 106 — `err` ignorado
- src/AppManager.js:133-135 — erro do DELETE ignorado, e a resposta é sempre de sucesso
- respostas de erro em texto puro e inconsistentes (`"Erro DB"`, `"Bad Request"`)
Description: Falhas de banco são engolidas ou derrubam o processo, e não há middleware de erro.
Impact: Respostas de sucesso mentirosas e crash do servidor em erro de query.
Recommendation: `asyncHandler` + `errorHandler` centralizado (PB-08).

### F-13 [MEDIUM] Validação de entrada insuficiente (AP-15)
Files:
- src/AppManager.js:35 — `pwd` não é obrigatório, e `c_id`, `card` e e-mail não têm validação de formato
- src/AppManager.js:132 — `id` da rota não é validado
Description: Qualquer string serve de cartão ou e-mail, e um id não numérico chega ao SQL.
Impact: Dados inválidos persistidos e regras de pagamento contornáveis.
Recommendation: Validação no controller, lançando erro 400 (PB-04).

### F-14 [LOW] Nomes opacos e enganosos (AP-21)
Files:
- src/AppManager.js:29-33 — `u`, `e`, `p`, `cid`, `cc`
- src/utils.js:17 — `badCrypto`
- src/AppManager.js:4 — `AppManager` (nome genérico para uma classe que faz tudo)
Recommendation: Nomes descritivos internamente (`name`, `email`, `courseId`, `cardNumber`), mantendo os campos
públicos do body (PB-14).

### F-15 [LOW] Código morto e imports sem uso (AP-23)
Files:
- src/AppManager.js:2 — importa `totalRevenue` sem uso
- src/utils.js:10 — `totalRevenue` nunca atualizado
- src/utils.js:2-5 — `dbUser`, `dbPass`, `smtpUser` sem uso
- src/utils.js:14 — `globalCache` escrito e nunca lido
Recommendation: Remover (PB-14).

### F-16 [LOW] `console.log` como mecanismo de log (AP-22)
Files:
- src/AppManager.js:45
- src/utils.js:13
- src/app.js:13
Recommendation: Módulo `logger` com níveis e sem dados sensíveis (PB-14).

### F-17 [LOW] Magic numbers e strings (AP-20)
Files:
- src/AppManager.js:46 — regra de aprovação "cartão começa com 4"
- src/AppManager.js:46, 108 — `"PAID"`, `"DENIED"` literais
- src/utils.js:6 — porta `3000` fixa
Recommendation: Constantes (`PAYMENT_STATUS`) e regra encapsulada no `paymentGateway` (PB-14).

## Deprecated APIs
Nenhuma API deprecated encontrada para as versões detectadas (Express 4.22.1, sqlite3 5.1.7). O código usa
`express.json()`, `res.status().send()` e `res.json()`, que estão vigentes no Express 4 e 5.

================================
Total: 17 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
