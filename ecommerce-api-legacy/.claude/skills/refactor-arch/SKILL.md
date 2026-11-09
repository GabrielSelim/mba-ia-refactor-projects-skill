---
name: refactor-arch
description: Analisa, audita e refatora uma codebase backend para o padrão MVC, em qualquer linguagem ou framework. Detecta a stack e a arquitetura (Fase 1), cruza o código com um catálogo de anti-patterns e gera um relatório de auditoria com severidade, arquivo e linha (Fase 2), pausa para confirmação humana e só então reestrutura o projeto em Models / Views (Routes) / Controllers, validando boot e endpoints (Fase 3). Use quando pedirem para auditar a arquitetura, encontrar code smells, ou refatorar um projeto legado para MVC.
argument-hint: "[nome-do-relatório, ex.: audit-project-1]"
---

# refactor-arch — Refatoração Arquitetural Automatizada

Você é um arquiteto de software sênior. Sua tarefa é levar o projeto do **diretório atual** a uma arquitetura MVC
limpa, sem quebrar o comportamento observável da API. Trabalhe em **3 fases sequenciais**. **Nunca** pule a pausa
entre a Fase 2 e a Fase 3.

## Arquivos de referência (leia antes de cada fase)

| Arquivo | Quando usar |
|---|---|
| [references/project-analysis.md](references/project-analysis.md) | Fase 1 — heurísticas para detectar linguagem, framework, banco, domínio e arquitetura |
| [references/anti-patterns-catalog.md](references/anti-patterns-catalog.md) | Fase 2 — catálogo de anti-patterns com sinais de detecção, severidade e APIs deprecated |
| [references/report-template.md](references/report-template.md) | Fase 2 — formato obrigatório do relatório de auditoria |
| [references/mvc-guidelines.md](references/mvc-guidelines.md) | Fase 3 — arquitetura MVC alvo, responsabilidades e estrutura por stack |
| [references/refactoring-playbook.md](references/refactoring-playbook.md) | Fase 3 — transformações concretas (antes/depois) para cada anti-pattern |

## Regras gerais

1. **Agnóstico de tecnologia.** Nunca assuma a stack: detecte-a pelos sinais da Fase 1 e escolha a variante da
   estrutura MVC correspondente em `mvc-guidelines.md`. Se a stack não estiver listada, aplique os princípios gerais.
2. **Evidência sempre.** Todo finding cita `arquivo:linha` (ou `arquivo:início-fim`) reais. Releia o arquivo para
   confirmar o número da linha antes de escrever. Não invente problemas, nem conte o mesmo problema duas vezes.
3. **Preserve o contrato público.** Mesmas rotas, métodos HTTP, nomes de campos de entrada e formato de resposta de
   sucesso. Exceções permitidas, sempre declaradas no relatório da Fase 3:
   - remover dados sensíveis das respostas (senhas, hashes, secrets);
   - proteger ou desabilitar endpoints que permitem **execução arbitrária ou destruição em massa** sem autenticação
     (AP-04, CRITICAL). Rotas de CRUD comuns sem autenticação (AP-12) **não** são bloqueadas automaticamente, porque
     isso exige decisão humana;
   - padronizar respostas de erro.
4. **Não adicione dependências** se a stack já resolve (ex.: `werkzeug.security` no Flask, `crypto` no Node). Se uma
   dependência nova for inevitável, justifique no relatório.
5. **Mudanças de contrato que exigem decisão humana** (ex.: exigir autenticação em rotas hoje públicas) **não são
   aplicadas automaticamente**. Liste-as em "Recomendações pendentes" no resumo da Fase 3.

---

## FASE 1 — Análise do projeto

1. Leia `references/project-analysis.md`.
2. Liste os arquivos de código-fonte (ignore `node_modules/`, `venv/`, `.git/`, `__pycache__/`, lockfiles, bancos
   `*.db` e a própria pasta `.claude/`). Conte os arquivos e as linhas.
3. Detecte: linguagem, framework **e versão** (do manifesto de dependências), dependências relevantes, banco de dados
   e forma de acesso (driver cru, ORM), tabelas/entidades, domínio da aplicação, arquitetura atual e entry point.
4. Faça o **inventário de endpoints** (método + rota + arquivo:linha do handler). Ele é a base da validação da Fase 3.
5. Imprima exatamente neste formato:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem e versão, se conhecida>
Framework:     <framework + versão>
Dependencies:  <principais, separadas por vírgula>
Database:      <banco + forma de acesso>
Domain:        <descrição curta do domínio e entidades>
Architecture:  <classificação + justificativa em uma linha>
Source files:  <N> files analyzed (~<L> lines)
DB tables:     <tabelas/entidades>
Entry point:   <arquivo e comando de execução>
Endpoints:     <quantidade> (lista abaixo)
  <MÉTODO> <rota>  -> <arquivo:linha>
================================
```

---

## FASE 2 — Auditoria

1. Leia `references/anti-patterns-catalog.md` e `references/report-template.md`.
2. Percorra **todos** os arquivos de código-fonte da Fase 1 procurando cada sinal de detecção do catálogo, incluindo a
   seção **APIs deprecated**, cruzada com as versões detectadas na Fase 1.
3. Para cada ocorrência, registre: severidade, ID do anti-pattern, título, `arquivo:linhas`, descrição concreta
   (o que o código faz), impacto e recomendação (aponte o padrão do playbook, ex.: `PB-02`).
   - O mesmo anti-pattern em vários pontos vira **um finding** com todas as localizações, e não vários findings.
   - Use a severidade padrão do catálogo. Ajuste só quando o catálogo indicar a regra de ajuste.
4. Ordene: CRITICAL → HIGH → MEDIUM → LOW. Dentro da mesma severidade, ordene pelo maior impacto.
5. Monte o relatório **exatamente** no formato de `report-template.md` e imprima-o.
6. **Salve o relatório** em `reports/<nome>.md` na **raiz do repositório git** (se o projeto estiver em uma
   subpasta, suba até a raiz; crie `reports/` se não existir). Para `<nome>`, use o argumento da invocação
   (`$ARGUMENTS`), se houver; senão `audit-<nome-da-pasta-do-projeto>`.
7. **PARE.** Pergunte exatamente:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

Não modifique **nenhum** arquivo do projeto antes de receber uma resposta afirmativa explícita (`y`, `yes`, `sim`).
Se a resposta for negativa, encerre informando onde está o relatório.

---

## FASE 3 — Refatoração para MVC

Só execute depois da confirmação.

1. **Baseline.** Antes de mudar qualquer arquivo:
   - suba a aplicação original;
   - chame cada endpoint do inventário da Fase 1 com uma requisição válida (use os exemplos do projeto, como
     `api.http`, README ou seeds, quando existirem);
   - registre status HTTP e chaves de primeiro nível do JSON;
   - encerre a aplicação.
   Se a aplicação original não sobe, registre isso: nesse caso a meta é fazê-la subir.
2. Leia `references/mvc-guidelines.md` e `references/refactoring-playbook.md`.
3. **Planeje a estrutura alvo** a partir da variante da stack em `mvc-guidelines.md`, adaptada ao ponto de partida:
   - *monolito/God file*: crie as camadas do zero e distribua o código;
   - *parcialmente organizado*: preserve o que já está correto (ex.: `models/` com ORM) e crie as camadas que
     faltam. Normalmente isso significa mover a lógica de `routes/` para `controllers/`, extrair `config/`, criar o
     error handler e corrigir os problemas dentro dos arquivos.
4. **Execute as transformações** do playbook para cada finding, da severidade mais alta para a mais baixa:
   - configuração e segredos → `config` lido do ambiente, com defaults seguros para desenvolvimento;
   - acesso a dados → **Models** (queries parametrizadas, ORM, sem regra HTTP);
   - fluxo da aplicação → **Controllers** (validam a entrada, orquestram models e services, decidem o status);
   - roteamento e serialização → **Views/Routes** (só mapeiam URL → controller);
   - efeitos colaterais (e-mail, notificação, pagamento, cache) → **services**, injetados pelo composition root;
   - tratamento de erros → **middleware/handler centralizado**;
   - entry point → **composition root** que monta a app (factory) e um runner separado.
   - Remova os arquivos antigos que ficaram vazios ou substituídos. Mantenha o comando de execução documentado
     (ex.: `python app.py`, `npm start`) funcionando, atualizando o manifesto se preciso.
5. **Valide** (obrigatório, não declare sucesso sem executar):
   1. **Boot:** a aplicação sobe sem erros nem stack traces. Se o runtime não estiver instalado na máquina, use a
      imagem Docker oficial da linguagem (ex.: `python:3.12-slim`, `node:20-slim`) montando o projeto como volume.
   2. **Endpoints:** repita as chamadas do baseline. Cada endpoint precisa responder com o mesmo status e as mesmas
      chaves de primeiro nível. A única exceção são as mudanças de contrato permitidas na regra 3, que devem ser
      listadas.
   3. **Anti-patterns:** refaça a busca dos sinais de detecção dos findings CRITICAL/HIGH/MEDIUM no código novo. Não
      pode sobrar ocorrência sem justificativa.
   4. Se algo falhar, corrija e valide de novo. Não declare sucesso sem a validação.
6. Imprima o resumo final:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios do código-fonte>

## Findings addressed
<ID do finding -> transformação aplicada (PB-xx) -> arquivo(s) novo(s)>

## Contract changes (intentional)
<lista ou "none">

## Pending recommendations (need human decision)
<lista ou "none">

## Validation
  ✓/✗ Application boots without errors
  ✓/✗ All <N> endpoints respond (<N>/<N> match baseline)
  ✓/✗ Zero CRITICAL/HIGH anti-patterns remaining
================================
```
