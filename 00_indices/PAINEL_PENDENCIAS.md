---
tipo: checklist
hierarquia: operacional
tema: painel de pendencias
fonte: base Charles
vigencia: vigente
atualizado_em: 2026-08-03
tags: [painel, pendencias, prazos, preencher]
---

# Painel de pendências

## Registro manual — funciona sem plugins

| Prioridade | Prazo | Processo/arquivo | Categoria | Pendência | Responsável | Próxima providência | Situação |
|---|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — | — |

Categorias mínimas: campo a preencher, documento faltante, proposta não recebida, diligência,
decisão da autoridade, consulta jurídica, fonte não confirmada, prazo, frontmatter e link quebrado.

## Conferência rápida

- [ ] Revisar ocorrências de `[PREENCHER: ...]` antes de assinatura ou publicação.
- [ ] Conferir documentos faltantes em cada [[08_processos_em_andamento/_FICHAS_OBSIDIAN/FICHA_PROCESSO|ficha de processo]].
- [ ] Verificar propostas ainda não recebidas e diligências sem resposta.
- [ ] Destacar decisões da autoridade competente e consultas jurídicas necessárias.
- [ ] Revisar fontes não confirmadas no [[00_indices/PAINEL_FONTES]].
- [ ] Ordenar prazos próximos no [[00_indices/PAINEL_PROCESSOS]].
- [ ] Executar `python scripts/validar_base_obsidian.py` para frontmatter, links e referências.

## Visualizações automáticas — opcionais, requerem Dataview

```dataview
TABLE tipo, processo, prazo, responsavel, status
FROM "08_processos_em_andamento"
WHERE modelo != true AND (status = "pendente" OR status = "bloqueado")
SORT prazo ASC
```

```dataview
TABLE file.folder AS pasta, atualizado_em
FROM "00_indices" OR "01_legislacao" OR "02_normas_internas" OR "03_jurisprudencia"
WHERE !atualizado_em
SORT file.path ASC
```

> [!note]
> A busca textual de `[PREENCHER]`, arquivos sem frontmatter e links quebrados é feita pelo script
> de validação; o Dataview não substitui essa verificação.

