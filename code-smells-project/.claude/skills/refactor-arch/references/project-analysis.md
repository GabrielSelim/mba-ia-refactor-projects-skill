# Análise de Projeto — Heurísticas (Fase 1)

Objetivo: descobrir **o que** é o projeto (stack, domínio) e **como** ele está organizado (arquitetura), sem assumir
nada. Toda conclusão precisa de um sinal concreto no código ou nos manifestos.

## 1. Arquivos a ignorar

`node_modules/`, `venv/`, `.venv/`, `env/`, `__pycache__/`, `.git/`, `.claude/`, `dist/`, `build/`, `coverage/`,
`*.lock`, `package-lock.json`, `yarn.lock`, `poetry.lock`, bancos (`*.db`, `*.sqlite`), binários e imagens.

## 2. Linguagem

| Sinal (ordem de prioridade) | Linguagem |
|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py`, arquivos `*.py` | Python |
| `package.json` + `*.js`/`*.mjs`/`*.cjs` | JavaScript (Node.js) |
| `package.json` + `tsconfig.json` ou `*.ts` | TypeScript (Node.js) |
| `pom.xml`, `build.gradle`, `*.java` | Java |
| `go.mod`, `*.go` | Go |
| `Gemfile`, `*.rb` | Ruby |
| `composer.json`, `*.php` | PHP |
| `*.csproj`, `*.cs` | C# |

A versão vem do manifesto (`engines` no `package.json`, `python_requires`/`requires-python`, `.nvmrc`,
`.python-version`, `Dockerfile` `FROM`). Se não houver, escreva "versão não fixada".

## 3. Framework e dependências

Leia o manifesto e confirme com o import no código:

| Dependência no manifesto | Confirmação no código | Framework |
|---|---|---|
| `flask` | `from flask import Flask`, `@app.route`, `Blueprint` | Flask |
| `fastapi` | `FastAPI()`, `@app.get` | FastAPI |
| `django` | `settings.py`, `urls.py`, `views.py` | Django |
| `express` | `require('express')` / `import express`, `app.get(` | Express |
| `@nestjs/core` | `@Controller()`, `@Module()` | NestJS |
| `fastify` | `fastify()` | Fastify |
| `spring-boot-starter-web` | `@RestController` | Spring Boot |
| `gin-gonic/gin` | `gin.Default()` | Gin |

Use a **versão exata** pinada (`flask==3.1.1`) ou o range (`express ^4.18.2`). Liste também as dependências relevantes
para a arquitetura: ORM, driver de banco, CORS, validação, auth, HTTP client, e-mail.

## 4. Banco de dados e acesso

| Sinal | Banco / forma de acesso |
|---|---|
| `sqlite3.connect(`, `import sqlite3`, `require('sqlite3')`, `':memory:'`, `*.db` | SQLite, driver cru |
| `flask_sqlalchemy`, `SQLAlchemy(`, `db.Model`, `create_engine` | SQLAlchemy (ORM) |
| `psycopg2`, `pg`, `postgresql://` | PostgreSQL |
| `pymysql`, `mysql2`, `mysql://` | MySQL |
| `mongoose`, `pymongo` | MongoDB |
| `prisma`, `sequelize`, `typeorm` | ORM Node |

**Tabelas/entidades:** procure `CREATE TABLE <nome>`, `__tablename__ = '<nome>'`, `class X(db.Model)`,
`mongoose.model('X'`, `model X {` (Prisma). **Seed:** `INSERT INTO` no boot, `seed.py`, scripts `db:seed`.

## 5. Domínio da aplicação

Deduza pelos substantivos das tabelas e rotas e descreva em uma linha com as entidades principais:

- `produtos`, `pedidos`, `itens_pedido`, `carrinho` → e-commerce;
- `courses`, `enrollments`, `payments` → LMS / plataforma de cursos com checkout;
- `tasks`, `categories`, `users`, `reports` → gerenciador de tarefas;
- `accounts`, `transactions` → financeiro.

## 6. Inventário de endpoints

| Stack | Padrão a procurar |
|---|---|
| Flask | `@app.route('/x', methods=[...])`, `@bp.route(...)`, `app.add_url_rule('/x', ..., methods=[...])` + prefixo do `register_blueprint(url_prefix=...)` |
| Express | `app.get|post|put|patch|delete('/x'`, `router.<método>(` + prefixo de `app.use('/prefix', router)` |
| FastAPI | `@app.get('/x')`, `@router.post(...)` |
| Django | `path('x/', view)` em `urls.py` |

Sem `methods=` no Flask, o método é `GET`. Registre `arquivo:linha` do handler. O inventário vira o roteiro da
validação da Fase 3.

## 7. Classificação da arquitetura atual

| Classificação | Sinais |
|---|---|
| **Monolito sem camadas / God File** | 1 a 4 arquivos. O mesmo arquivo tem SQL, regra de negócio e rotas, ou uma classe (`AppManager`, `Manager`, `Utils`) faz tudo. |
| **Camadas nominais** | Existem arquivos `models.py`, `controllers.py`, mas os "models" retornam dicts formatados para HTTP, os "controllers" têm SQL, ou um arquivo concentra vários domínios. |
| **Parcialmente organizado** | Pastas `models/`, `routes/`, `services/`, `utils/` existem, mas a regra de negócio vive nas rotas, não há camada de controller, a config está hardcoded e não há error handler central. |
| **MVC / camadas adequadas** | `models/`, `controllers/`, `routes|views/`, `config/`, error handler central, composition root. |

Justifique em uma linha, por exemplo: "Monolítica — 4 arquivos, `models.py` mistura SQL e regras de 4 domínios".

## 8. Entry point e execução

- Python: `if __name__ == '__main__': app.run(...)`, `create_app()`, `wsgi.py`. Comando: `python app.py` ou
  `flask run`.
- Node: `main` e `scripts.start` do `package.json`, `app.listen(`. Comando: `npm start`.
- Porta: argumento de `app.run(port=...)` / `app.listen(...)` ou config.
- Pré-requisitos de boot: seed obrigatório (ex.: `python seed.py`), variáveis de ambiente, banco externo.

## 9. Contagem

`Source files` = arquivos de código da linguagem detectada (sem testes, configs de lint ou manifestos). As linhas
contam o total desses arquivos, e um valor aproximado (`~800`) é aceitável.
