---
tipo: checklist
hierarquia: operacional
tema: painel de vigencia e atualizacao de fontes
fonte: base Charles
vigencia: vigente
atualizado_em: 2026-08-03
tags: [painel, fontes, vigencia, atualizacao]
---

# Painel de fontes

Este painel localiza fontes; não reescreve nem interpreta normas. Antes de afirmar conteúdo jurídico,
abra o arquivo-fonte e confira dispositivo, vigência e `atualizado_em`.

## Fontes prioritárias — Markdown básico

| Fonte | Categoria | Vigência registrada | Atualizado em | Verificação necessária |
|---|---|---|---|---|
| [[01_legislacao/lei-14133-2021-licitacoes-contratos-administrativos|Lei nº 14.133/2021]] | legislação | vigente | 2026-06-27 | Conferir alterações legislativas antes de uso sensível. |
| [[01_legislacao/limites-vigentes-dispensa-art-75|Limites do art. 75]] | legislação operacional | vigente | 2026-08-01 | Manutenção anual e confirmação do decreto vigente. |
| [[02_normas_internas/regulamento-licitacoes-camara-itanhandu|Regulamento da Câmara]] | norma interna | vigente | 2026-06-25 | Conferir atos posteriores da Câmara. |
| [[02_normas_internas/ato-diretor-juridico-01-2024-dispensa-analise-juridica|Ato Jurídico nº 01/2024]] | norma interna | vigente | 2026-06-27 | Conferir alteração ou revogação. |
| [[03_jurisprudencia/tce_mg/consulta-tcemg-1104833-dispensa-valor-ramo-atividade|Consulta TCE-MG 1104833]] | jurisprudência persuasiva | vigente | 2026-06-25 | Conferir arquivo-fonte antes de citar. |
| [[estudo-ramo-atividade-objeto-ou-fornecedor-cnae|Estudo: ramo de atividade, objeto x fornecedor]] | doutrina / estudo temático | vigente | 2026-10-06 | Conferir as fichas de origem antes de citar. |
| [[resolucao-tcesp-16-2025-ramo-de-atividade-dispensa|Resolução TCE-SP 16/2025]] | ato de outro Tribunal (referência comparativa) | vigente | 2026-10-06 | Data de publicação no DOE-SP não conferida. |

## Fila manual de manutenção

| Arquivo | Motivo | Origem confirmada? | Responsável | Prazo | Resultado da revisão |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

Inclua aqui fontes alteradas, revogadas, sem data, antigas, com vigência a confirmar ou sem origem
clara. Não mude `vigencia` sem confirmação documental.

## Visualizações automáticas — opcionais, requerem Dataview

```dataview
TABLE tipo, vigencia, atualizado_em, fonte
FROM "01_legislacao" OR "02_normas_internas" OR "03_jurisprudencia" OR "04_doutrina_artigos"
SORT vigencia ASC, atualizado_em ASC
```

```dataview
TABLE tipo, fonte, atualizado_em
FROM "01_legislacao" OR "02_normas_internas" OR "03_jurisprudencia" OR "04_doutrina_artigos"
WHERE vigencia = "alterado" OR vigencia = "revogado" OR !atualizado_em
SORT file.path ASC
```

