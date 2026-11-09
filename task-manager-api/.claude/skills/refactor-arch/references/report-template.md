# Template do Relatório de Auditoria (Fase 2)

O relatório é impresso no terminal **e** salvo em `reports/<nome>.md` na raiz do repositório. Siga o formato abaixo
literalmente. As partes entre `< >` são preenchidas. Não acrescente seções nem remova as obrigatórias.

## Regras de preenchimento

- **Ordem:** todos os CRITICAL, depois HIGH, MEDIUM e LOW.
- **Numeração:** `F-01`, `F-02`, … na ordem final.
- **File:** caminho relativo à raiz do projeto + linha exata (`models.py:28`) ou intervalo (`models.py:1-314`). Com
  várias ocorrências, uma por linha na lista `Files:`.
- **Description:** o que o código faz, de forma concreta e verificável (cite o trecho quando curto).
- **Impact:** a consequência real (segurança, manutenção, desempenho, testabilidade).
- **Recommendation:** a ação e o padrão do playbook (`PB-xx`).
- **Summary:** as contagens precisam bater com a lista de findings.

## Formato

````markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome da pasta>
Stack:   <linguagem> + <framework versão>
Files:   <N> analyzed | ~<L> lines of code
Date:    <AAAA-MM-DD>

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### F-01 [CRITICAL] <Título> (AP-xx)
File: <arquivo:linha>
Description: <descrição concreta>
Impact: <impacto>
Recommendation: <ação> (PB-xx)

### F-02 [CRITICAL] <Título> (AP-xx)
Files:
- <arquivo:linha>
- <arquivo:linha>
Description: ...
Impact: ...
Recommendation: ...

... (demais findings, em ordem de severidade)

## Deprecated APIs
| Local | Uso deprecated | Substituto | Finding |
|---|---|---|---|
| <arquivo:linha> | <API> | <API moderna> | F-xx |
<ou: "Nenhuma API deprecated encontrada para as versões detectadas.">

================================
Total: <N> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
````

## Exemplo de um finding bem escrito

```markdown
### F-02 [CRITICAL] SQL Injection em queries montadas por concatenação (AP-02)
Files:
- models.py:28 — `"SELECT * FROM produtos WHERE id = " + str(id)`
- models.py:109-111 — login: `"... WHERE email = '" + email + "' AND senha = '" + senha + "'"`
Description: 15 queries concatenam valores vindos do request direto no SQL.
Impact: Um atacante faz login sem senha (`' OR '1'='1`) e lê ou altera qualquer tabela.
Recommendation: Usar queries parametrizadas (`?`) em todos os acessos (PB-02).
```

## Exemplo de finding ruim (não faça)

```markdown
### [HIGH] Código ruim
File: models.py
Description: O código poderia ser melhor.
```

Problemas: não tem linha, não tem ID do catálogo, a descrição não é verificável e não há recomendação.
