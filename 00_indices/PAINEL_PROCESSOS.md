---
tipo: checklist
hierarquia: operacional
tema: painel de processos em andamento
fonte: base Charles
vigencia: vigente
atualizado_em: 2026-08-03
tags: [painel, processos, prazos, acompanhamento]
---

# Painel de processos

Use este painel como visão de trabalho. A ficha operacional não substitui qualquer peça oficial do
processo. Processos reais devem ficar no diretório definido por `CHARLES_PROCESSOS_DIR`, fora do
repositório Git; no vault, vincule somente notas e documentos cuja guarda seja autorizada.

## Processos em andamento — Markdown básico

Atualize uma linha por processo prioritário. Use links para a ficha e para os documentos, sem copiar
conteúdo processual para esta tabela.

| Processo/ficha | Objeto | Modalidade ou fundamento | Fase | Responsável | Prioridade | Prazo | Próxima ação |
|---|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — | — |

## Controle documental por processo

| Processo/ficha | Produzidos | Faltantes | Pesquisa de preços | Aviso | Julgamento | Contratação |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — |

Estados sugeridos: `nao_iniciado`, `em_elaboracao`, `em_conferencia`, `concluido`, `nao_aplicavel`
e `bloqueado`. Descreva a causa de todo bloqueio.

## Visualização automática — opcional, requer Dataview

```dataview
TABLE objeto, modalidade, fundamento_legal, fase, responsavel, prioridade, prazo, proxima_acao
FROM "08_processos_em_andamento"
WHERE tipo = "processo" AND modelo != true AND status != "concluido"
SORT prioridade ASC, prazo ASC
```

```dataview
TABLE documentos_produzidos, documentos_faltantes, pesquisa_precos_status, aviso_status,
julgamento_status, contratacao_status
FROM "08_processos_em_andamento"
WHERE tipo = "processo" AND modelo != true AND status != "concluido"
SORT prazo ASC
```

Veja também [[00_indices/PAINEL_PENDENCIAS]] e [[07_checklists/rotina-diaria-agente-contratacao]].

