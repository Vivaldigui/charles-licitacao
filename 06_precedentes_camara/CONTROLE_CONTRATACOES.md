---
tipo: precedente
tema: controle de contratacoes e afericao de limite por cnae
fonte: base Charles / contratações concluídas da Câmara Municipal de Itanhandu
vigencia: vigente
atualizado_em: 2026-06-27
tags: [controle, contratacoes, cnae, limite, dispensa, fracionamento, precedentes]
---

# CONTROLE DE CONTRATAÇÕES (aferição de limite por CNAE)

Registro vivo das contratações da Câmara. **O Charles atualiza este controle sempre que uma
contratação for concluída**, para aferir os limites da dispensa por valor (art. 75, I/II) por
**ramo de atividade (subclasse CNAE)** e prevenir fracionamento. Roteiro de análise:
`07_checklists/roteiro-limite-dispensa-cnae.md`.

## Como atualizar (a cada contratação concluída)
1. Acrescentar uma linha em **Registro de contratações** com data, processo, objeto, **subclasse
   CNAE** (consultar https://concla.ibge.gov.br/busca-online-cnae.html — não inventar código),
   modalidade/fundamento, valor e exercício.
2. Atualizar o **Acumulado por subclasse/exercício** somando o valor (apenas dispensas por valor
   — art. 75, I/II) e recalcular o saldo até o limite vigente.
3. Atualizar `atualizado_em` no frontmatter.

## Registro de contratações

| Data conclusão | Processo / Dispensa | Objeto | CNAE (subclasse) | Modalidade / Fundamento | Valor (R$) | Conta p/ limite? | Exercício |
|---|---|---|---|---|---|---|---|
| 08/06/2026 | PA 021/2026 — Dispensa 11/2026 | Aquisição e instalação de claraboia | `[PREENCHER: consultar subclasse]` | Dispensa — art. 75, II | 2.780,00 | Sim | 2026 |
| _exemplo_ | _Inexigibilidade 01/2026_ | _Auditoria contábil (CEI)_ | _[consultar]_ | _Inexigibilidade — art. 74_ | _25.000,00_ | _Não (art. 74)_ | _2026_ |

## Acumulado por subclasse CNAE × exercício (somente dispensa por valor — art. 75, I/II)

| Exercício | CNAE (subclasse) | Total acumulado (R$) | Inciso | Limite vigente | Saldo até o limite |
|---|---|---|---|---|---|
| 2026 | `[PREENCHER]` | 2.780,00 | II | `[CONFIRMAR no decreto]` | `[CALCULAR]` |

> O limite vigente vem de `01_legislacao/limites-vigentes-dispensa-art-75.md` (atualizado por
> decreto). Quando o acumulado de uma subclasse se aproximar do limite, **alertar** e planejar
> licitação/agregação no PCA, evitando fracionamento.
