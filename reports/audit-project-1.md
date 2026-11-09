================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code
Date:    2026-11-09

## Summary
CRITICAL: 6 | HIGH: 5 | MEDIUM: 5 | LOW: 4

## Findings

### F-01 [CRITICAL] SQL Injection em queries montadas por concatenação (AP-02)
Files:
- models.py:28 — `"SELECT * FROM produtos WHERE id = " + str(id)`
- models.py:47-50 — INSERT de produto concatenando `nome`, `descricao`, `categoria`
- models.py:57-61 — UPDATE de produto concatenado
- models.py:68 — DELETE concatenado
- models.py:92 — SELECT de usuário por id
- models.py:109-111 — login: `"... WHERE email = '" + email + "' AND senha = '" + senha + "'"`
- models.py:126-129 — INSERT de usuário
- models.py:140, 148-151, 155, 157-161, 163-166 — criação de pedido
- models.py:174, 188, 192, 220, 224 — listagem de pedidos
- models.py:279-281 — `"UPDATE pedidos SET status = '" + novo_status + "'..."`
- models.py:289-297 — busca: `"... LIKE '%" + termo + "%'"` e `"categoria = '" + categoria + "'"`
Description: Praticamente todas as queries concatenam valores vindos do request direto no SQL, inclusive no login e
na busca textual.
Impact: Login sem senha (`email = "' OR '1'='1' --"`), leitura e alteração de qualquer tabela, exfiltração das senhas
(que estão em texto puro).
Recommendation: Queries parametrizadas com `?` em todos os acessos, com montagem dinâmica só de cláusulas fixas
(PB-02).

### F-02 [CRITICAL] Endpoints administrativos de execução arbitrária e destruição em massa sem autenticação (AP-04)
Files:
- app.py:59-78 — `POST /admin/query` executa qualquer SQL recebido em `dados["sql"]` e faz `commit`
- app.py:47-57 — `POST /admin/reset-db` apaga todas as tabelas
Description: Qualquer cliente HTTP pode rodar `DROP TABLE`, `UPDATE usuarios SET tipo='admin'` ou zerar o banco.
Não há autenticação, autorização nem log de auditoria.
Impact: Comprometimento total dos dados com uma única requisição.
Recommendation: Exigir um token administrativo configurado no ambiente (rota desabilitada se ausente), restringir
`/admin/query` a `SELECT` e logar o uso (PB-15).

### F-03 [CRITICAL] Credenciais e configuração sensível hardcoded (AP-01)
Files:
- app.py:7 — `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"`
- controllers.py:289 — a mesma secret repetida literalmente na resposta do `/health`
- database.py:5 — caminho do banco fixo (`db_path = "loja.db"`)
Description: A chave usada para assinar sessões e tokens está no código-fonte e versionada.
Impact: Quem tem acesso ao repositório (ou ao `/health`) consegue forjar sessões e tokens assinados.
Recommendation: Mover a configuração para `src/config/settings.py`, lida do ambiente, com secret aleatória em dev
(PB-01).

### F-04 [CRITICAL] Exposição de dados sensíveis nas respostas (AP-05)
Files:
- models.py:83, 99 — `"senha": row["senha"]` em `GET /usuarios` e `GET /usuarios/<id>`
- controllers.py:285-289 — `/health` retorna `secret_key`, `db_path`, `debug` e `ambiente`
- controllers.py:11-12, 21-22, 61-62, 96, 109, 126, 134, 144, 165, 186, 220, 227, 235, 255, 262, 292 — `str(e)` devolvido ao cliente
- app.py:77-78 — erro do SQL arbitrário devolvido cru
Description: A listagem de usuários entrega a senha (em texto puro) de todos os usuários. O health check publica a
secret. Exceções internas vazam para o cliente.
Impact: Vazamento direto de credenciais de todos os usuários e da chave da aplicação.
Recommendation: Serialização sem campos sensíveis, health check mínimo e erros 500 genéricos com detalhe só no log
(PB-10, PB-08).

### F-05 [CRITICAL] Senhas armazenadas e comparadas em texto puro (AP-06)
Files:
- database.py:31 — coluna `senha TEXT` recebe o valor puro
- database.py:76-78 — seed com `"admin123"`, `"123456"`, `"senha123"`
- models.py:126-129 — `criar_usuario` grava a senha recebida sem hash
- models.py:109-111 — login compara `senha = '<valor>'` no SQL
Description: Nenhuma senha passa por hash.
Impact: Qualquer leitura do banco (via F-01, F-02 ou F-04) expõe as senhas reais, que costumam ser reutilizadas em
outros serviços.
Recommendation: `werkzeug.security.generate_password_hash` / `check_password_hash`, que já vem com o Flask (PB-09).

### F-06 [CRITICAL] God File: models.py concentra 4 domínios, SQL e regras de negócio (AP-03)
Files:
- models.py:1-314 — produtos (4-70, 285-314), usuários (72-131), pedidos (133-233, 275-283), relatório de vendas (235-273)
- app.py:47-78 — handlers administrativos com SQL direto no arquivo de bootstrap/rotas
Description: Um único arquivo de "models" contém acesso a dados, cálculo de total do pedido, baixa de estoque, regras
de desconto e formatação de resposta para todos os domínios. Não existem classes de modelo, só funções que devolvem
dicts prontos para o HTTP.
Impact: É impossível testar ou alterar um domínio isoladamente, e qualquer mudança arrisca as outras áreas.
Recommendation: Separar em `models/` por domínio, `controllers/` para o fluxo e `views/routes.py` para o
roteamento (PB-03, PB-04).

### F-07 [HIGH] Estado global mutável na conexão do banco (AP-08)
File: database.py:4-12
Description: `db_connection` global criado uma vez com `check_same_thread=False` e compartilhado por todas as
requisições e threads (`global db_connection`).
Impact: Condições de corrida e transações misturadas entre requisições concorrentes. É impossível isolar em testes.
Recommendation: Conexão por requisição em `flask.g`, fechada no teardown do app context (PB-05).

### F-08 [HIGH] Criação de pedido sem transação e com validação de estoque fora do bloco atômico (AP-10)
Files:
- models.py:133-169 — valida estoque em um loop (139-146) e depois insere o pedido, os itens e baixa o estoque em outro loop (148-166)
- controllers.py:249-250 — cancelamento só imprime "Devolver estoque", sem devolver
Description: As escritas não ficam em uma transação explícita. Uma falha no meio deixa pedido sem itens ou estoque
baixado parcialmente, e entre a validação e a baixa outro pedido pode consumir o estoque.
Impact: Estoque e pedidos inconsistentes em produção.
Recommendation: Executar validação e escritas em uma única transação (`with conn:`) com `executemany` (PB-12).

### F-09 [HIGH] Configuração de execução insegura (AP-11)
Files:
- app.py:8 — `app.config["DEBUG"] = True`
- app.py:88 — `app.run(host="0.0.0.0", port=5000, debug=True)`
- app.py:9 — `CORS(app)` libera qualquer origem sem configuração
Description: O debugger interativo do Werkzeug fica ligado e exposto em todas as interfaces de rede.
Impact: O debugger permite executar código remoto se acessível. O CORS aberto permite chamadas de qualquer site.
Recommendation: `DEBUG`, `HOST` e `CORS_ORIGINS` vindos da config do ambiente, com debug desligado por padrão (PB-01).

### F-10 [HIGH] Controllers com acesso direto ao banco e regra de negócio misturada (AP-07, AP-09)
Files:
- controllers.py:3, 264-274 — `health_check` importa `get_db` e executa SQL direto no controller
- controllers.py:24-62 e 64-96 — validação extensa e regras de produto repetidas dentro dos handlers
- controllers.py:188-216 — criação de pedido valida a entrada, chama o model e dispara notificações no mesmo handler
Description: A camada "controller" lê `request`, valida, acessa o banco e faz efeitos colaterais, e depende da
conexão global concreta.
Impact: Acoplamento forte, que impede testar o fluxo sem banco e HTTP reais.
Recommendation: Controllers só orquestram. O SQL fica nos models, a validação em funções reutilizáveis e as
dependências entram pelo composition root (PB-04, PB-06).

### F-11 [HIGH] Autenticação inexistente: login não emite credencial e todas as rotas são públicas (AP-12)
Files:
- controllers.py:167-186 — `/login` só devolve os dados do usuário, sem token ou sessão
- app.py:18-26 — `GET /usuarios`, `GET /pedidos` e `PUT /pedidos/<id>/status` sem nenhum controle de acesso
Description: Não existe mecanismo de autenticação. O login é decorativo.
Impact: Qualquer cliente lista usuários e pedidos de todos e altera o status de pedidos.
Recommendation: Introduzir autenticação (token assinado + decorator). Exigir o token nas rotas muda o contrato
público e depende de decisão humana (PB-09).

### F-12 [MEDIUM] Queries N+1 na listagem de pedidos (AP-13)
Files:
- models.py:171-201 — por pedido, 1 query de itens (188) e, por item, 1 query de produto (192)
- models.py:203-233 — mesmo padrão em `get_todos_pedidos` (220, 224)
- models.py:154-156 — reconsulta o preço de cada produto já carregado no loop anterior
- models.py:239-254 — 5 queries separadas para contagens que cabem em uma agregação
Description: Com P pedidos e I itens, são 1 + P + P×I queries.
Impact: A latência cresce linearmente com o volume de pedidos.
Recommendation: Uma query com `LEFT JOIN` e agrupamento em memória, e agregação com `CASE` no relatório (PB-07).

### F-13 [MEDIUM] Código duplicado de serialização e validação (AP-14)
Files:
- models.py:12-21, 31-40, 304-313 — o mesmo mapeamento de linha de produto repetido 3 vezes
- models.py:79-86, 95-102 — mapeamento de usuário repetido
- models.py:171-201 e 203-233 — `get_pedidos_usuario` e `get_todos_pedidos` praticamente idênticas
- controllers.py:28-50 e 72-90 — validações de produto copiadas entre criar e atualizar, com divergência: a atualização não valida categoria nem tamanho do nome
Description: A mesma lógica aparece em vários lugares e já divergiu.
Impact: Correções aplicadas em um lugar e esquecidas em outro. A atualização aceita categoria inválida.
Recommendation: Funções únicas de serialização e de validação, reutilizadas por create e update (PB-04).

### F-14 [MEDIUM] Tratamento de erros genérico e repetido, sem handler central (AP-16)
Files:
- controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292
- app.py:77-78
Description: Cada handler tem um `try/except Exception` que devolve `str(e)` com status 500, e não há
`errorhandler` registrado.
Impact: Comportamento de erro inconsistente, vazamento de detalhes internos e boilerplate em todo o código.
Recommendation: Exceções de domínio e `register_error_handlers(app)` centralizado (PB-08).

### F-15 [MEDIUM] Validação de entrada ausente ou frágil (AP-15)
Files:
- controllers.py:169-170 — `login`: `dados.get(...)` quebra com 500 se o body não for JSON
- controllers.py:239-240 — `atualizar_status_pedido`: o mesmo problema
- controllers.py:43-46 e 87-90 — `preco < 0` com `preco` string gera `TypeError` → 500
- controllers.py:195-201 — itens do pedido sem validação de `produto_id` e `quantidade` (quantidade negativa aumenta o estoque)
- controllers.py:118-121 — `float(preco_min)` inválido gera 500
Description: A entrada é usada sem checagem de tipo ou de presença.
Impact: Erros 500 para entradas simples e regra de estoque burlável com quantidade negativa.
Recommendation: Validação centralizada que lança `ValidationError` (400) (PB-04, PB-08).

### F-16 [MEDIUM] Efeitos colaterais (e-mail, SMS, push) acoplados ao controller (AP-18)
Files:
- controllers.py:208-210 — `print("ENVIANDO EMAIL...")`, SMS e push dentro do handler de pedido
- controllers.py:247-250 — notificações de status no handler
Description: As notificações são simuladas com `print` no meio do fluxo HTTP.
Impact: É impossível trocar o canal de notificação ou testar sem efeitos colaterais.
Recommendation: `services/notification_service.py` com logger, chamado pelo controller (PB-06).

### F-17 [LOW] Magic numbers e listas literais (AP-20)
Files:
- models.py:256-262 — faixas de desconto `10000/0.1`, `5000/0.05`, `1000/0.02`
- controllers.py:52 — lista de categorias válidas literal
- controllers.py:242 — lista de status válidos literal
- controllers.py:47-50 — limites `2` e `200` do nome
Recommendation: Constantes nomeadas em um módulo de domínio (PB-14).

### F-18 [LOW] `print` no lugar de logger (AP-22)
Files:
- controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250
- app.py:56, 83-86
Recommendation: `logging` com nível e mensagens estruturadas (PB-14).

### F-19 [LOW] Nomenclatura ruim e builtin sombreado (AP-21)
Files:
- controllers.py:14, 56, 64, 98, 136, 160 e models.py:24, 54, 65, 89 — parâmetro e variável `id` sombreiam o builtin
- models.py:187-193 — `cursor2`, `cursor3`, `prod`
Recommendation: Nomes descritivos (`produto_id`, `usuario_id`) (PB-14).

### F-20 [LOW] Imports não utilizados (AP-23)
Files:
- models.py:2 — `import sqlite3` sem uso
- database.py:2 — `import os` sem uso
Recommendation: Remover (PB-14).

## Deprecated APIs
Nenhuma API deprecated encontrada para as versões detectadas (Flask 3.1.1, flask-cors 5.0.1, sqlite3 da stdlib).

================================
Total: 20 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
