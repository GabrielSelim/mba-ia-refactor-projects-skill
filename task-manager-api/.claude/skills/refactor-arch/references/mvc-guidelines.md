# Diretrizes de Arquitetura MVC (Fase 3)

## 1. Camadas e responsabilidades

| Camada | Faz | Não faz |
|---|---|---|
| **Config** | Lê configuração do ambiente (`os.environ` / `process.env`) com defaults seguros de dev. Centraliza porta, banco, segredos, flags e constantes de negócio configuráveis. | Ter segredo real hardcoded. Ser importada para ler `request`. |
| **Models** | Representam entidades e encapsulam o acesso a dados: queries **parametrizadas** ou ORM, transações, regras intrínsecas da entidade (ex.: `task.is_overdue()`, `pedido` calculando o total), serialização segura (`to_dict()` sem senha). | Conhecer HTTP (`request`, `res`, status code). Logar ou notificar. |
| **Controllers** | Concentram o **fluxo da aplicação**: recebem dados já extraídos da requisição, validam a entrada, orquestram models e services, decidem o resultado (sucesso ou erro de domínio). | Montar SQL. Registrar rotas. Ter segredos. Fazer I/O externo direto (usam services). |
| **Views / Routes** | Mapeiam URL + método → controller e convertem o resultado em resposta HTTP (JSON, status). Em APIs a "View" é a representação JSON. | Ter regra de negócio ou acesso a dados. |
| **Services** (apoio) | Efeitos colaterais e integrações: e-mail, notificação, pagamento, hashing, cache. Injetados pelo composition root. | Conhecer HTTP. |
| **Middlewares** | Preocupações transversais: error handler central, autenticação, logging de requisição. | Ter regra de domínio. |
| **Composition root / Entry point** | Cria a app (factory), carrega a config, monta as dependências (db, services), registra rotas e middlewares. Um runner separado só sobe o servidor. | Ter lógica de negócio. |

**Direção de dependências (obrigatória):** `routes → controllers → models/services → database/config`. Nenhuma camada
inferior importa uma superior. Models nunca importam controllers ou routes.

## 2. Regras transversais

1. **Erros:** os controllers lançam exceções de domínio (`NotFoundError`, `ValidationError`, `ConflictError`), e um
   **handler central** converte em JSON + status. Nada de `try/except` repetido em cada rota. Erro 500 nunca expõe
   `str(e)` ao cliente: a mensagem vai para o log.
2. **Config:** nenhum segredo literal no código. Defaults de dev são permitidos quando não dão acesso a sistema real e
   são marcados como dev (ex.: `SECRET_KEY` gerada aleatoriamente se ausente, `DEBUG` falso por padrão).
3. **Banco:** a conexão é criada pela app (factory ou por requisição) e não por estado global mutável
   compartilhado. Escritas com várias etapas acontecem em uma transação.
4. **Logs:** use o logger da plataforma (`logging` / `console` encapsulado em um módulo logger) com nível. Nunca logue
   senha, cartão ou chave.
5. **Contrato:** rotas, métodos e formatos de resposta de sucesso preservados (ver a regra 3 do SKILL.md).
6. **Nomes:** arquivos por domínio (`produto_model.py`, `checkoutController.js`), seguindo a convenção de nomes da
   linguagem (snake_case em Python, camelCase em JS).

## 3. Estrutura alvo por stack

### Python / Flask (monolito → MVC)

```
<projeto>/
├── app.py                      # runner: from src.app import create_app; app.run(...)
├── requirements.txt
└── src/
    ├── __init__.py
    ├── app.py                  # composition root: create_app()
    ├── config/
    │   └── settings.py         # Config lida do ambiente
    ├── database.py             # conexão por requisição (flask.g) + init de schema/seed
    ├── models/                 # <entidade>_model.py — acesso a dados parametrizado
    ├── controllers/            # <entidade>_controller.py — fluxo e validação
    ├── views/
    │   └── routes.py           # Blueprint: URL → controller → jsonify
    ├── services/               # notificação, hashing, ...
    └── middlewares/
        └── error_handler.py    # exceções de domínio + register_error_handlers(app)
```

### Python / Flask (parcialmente organizado: já tem `models/`, `routes/`, `services/`)

Preserve os módulos corretos e complete as camadas. Não reescreva o que já está certo:

```
<projeto>/
├── app.py                      # runner + create_app() (composition root)
├── config/settings.py          # NOVO: config do ambiente
├── database.py                 # instância do ORM (mantida)
├── models/                     # mantido, corrigido (sem senha no to_dict, hash forte, APIs modernas)
├── controllers/                # NOVO: regra que estava nas rotas
├── routes/                     # mantido como camada View: só mapeia URL → controller
├── services/                   # mantido, config injetada
├── middlewares/error_handler.py  # NOVO
└── utils/                      # só helpers puros, sem imports mortos
```

### Node.js / Express (God Class → MVC)

```
<projeto>/
├── package.json                # "start": "node src/server.js"
└── src/
    ├── server.js               # runner: createApp() + app.listen(config.port)
    ├── app.js                  # composition root: createApp({ db, services })
    ├── config/index.js         # process.env com defaults de dev
    ├── database/
    │   ├── connection.js       # abre o banco + helpers promisificados (run/get/all/transaction)
    │   └── schema.js           # criação de tabelas + seed
    ├── models/                 # <entidade>Model.js — SQL parametrizado
    ├── controllers/            # <fluxo>Controller.js — orquestram models e services
    ├── routes/index.js         # Router: URL → controller (camada View)
    ├── services/               # paymentGateway.js, passwordHasher.js, cache.js
    └── middlewares/
        ├── asyncHandler.js
        └── errorHandler.js
```

### Outras stacks (princípios)

- FastAPI: `routers/` (views), `controllers/` ou `services/`, `models/` (ORM ou repositórios), `core/config.py`,
  `exception_handler`.
- Django: já é MTV. Garanta views finas, regra em `services.py` ou managers, e `settings` lendo do ambiente.
- Java/Spring: `controller/`, `service/`, `repository/`, `model/`, `config/`, `@ControllerAdvice`.

## 4. Checklist de saída da Fase 3

- [ ] Estrutura de diretórios segue o padrão MVC da stack
- [ ] Configuração extraída para o módulo de config (sem segredos hardcoded)
- [ ] Models abstraem os dados (sem SQL fora dos models)
- [ ] Views/Routes separadas e finas
- [ ] Controllers concentram o fluxo
- [ ] Error handling centralizado
- [ ] Entry point claro (composition root + runner)
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem como no baseline
