---
tipo: checklist
hierarquia: operacional
tema: esteira canonica de contratacao direta
fonte: base Charles / Lei 14.133/2021 / normas internas da Câmara
vigencia: vigente
atualizado_em: 2026-08-01
tags: [esteira, contratacao-direta, processo-json, dispensa, governanca]
---

# Esteira canônica — contratação direta

Fluxo operacional para processos de dispensa/inexigibilidade na Câmara. O `processo.json` é a
ficha única do processo e alimenta os campos repetidos entre documentos.

Antes de preencher campos de agente de contratação, gestor ou fiscal, consultar a
[Portaria nº 24/2024](../02_normas_internas/portaria-24-2024-designacao-agentes-licitacao-contratos.md)
e conferir se o processo contém designação posterior ou específica.

## Variante com aviso

| Etapa | Minuta usada | Campos do `processo.json` | Campos novos | Pré-requisitos bloqueantes | Validações |
|---|---|---|---|---|---|
| DFD | `05_minutas/DFD/DFD_MINUTA_MAE.docx` | objeto, descricao_detalhada, quantidade, unidade, exercicio | justificativa da necessidade, setor demandante | demanda identificada | objeto claro; sem solução pré-direcionada |
| ETP | `05_minutas/ETP/ETP_MINUTA_MAE.docx` | objeto, descricao_detalhada, quantidade, unidade | alternativas, solução escolhida, riscos | DFD concluído | necessidade e alternativa escolhida motivadas |
| TR | `05_minutas/TR/TR_MINUTA_MAE.docx` | objeto, descricao_detalhada, quantidade, unidade, fundamento | critérios de execução/aceitação, obrigações, prazo | ETP ou justificativa de dispensa de ETP | especificação suficiente e não restritiva |
| Pesquisa de Preços | `05_minutas/PESQUISA_DE_PRECOS/PESQUISA_PRECOS_MINUTA_MAE.docx` | objeto, descricao_detalhada, quantidade, unidade, valor_estimado | fontes, comparabilidade, método, anexos | TR ou especificação mínima consolidada | mínimo de 3 preços ou justificativa; preço unitário seguro |
| Certidão Orçamentária | `05_minutas/CERTIDAO_ORCAMENTARIA/CERTIDAO_RECURSOS_ORCAMENTARIOS_MINUTA_MAE.docx` | valor_estimado, dotacao | saldo e classificação orçamentária | pesquisa de preços suficiente | dotação compatível com objeto e valor |
| Justificativa | `05_minutas/JUSTIFICATIVA_CONTRATACAO_DIRETA/JUSTIFICATIVA_CONTRATACAO_DIRETA_MINUTA_MAE.docx` | objeto, fundamento, valor_estimado, cnae_subclasse | razão da escolha, justificativa do preço, enquadramento | pesquisa e dotação concluídas | limite CNAE simulado; parecer jurídico avaliado |
| Autorização | `05_minutas/AUTORIZACAO/AUTORIZACAO_ABERTURA_MINUTA_MAE.docx` | numero_processo, objeto, fundamento, valor_estimado | despacho da autoridade | documentos preparatórios mínimos | autoridade competente autoriza prosseguimento |
| Aviso | `05_minutas/AVISO/AVISO_CONTRATACAO_DIRETA_MINUTA_MAE.docx` | numero_processo, objeto, quantidade, unidade, valor_estimado, datas.aviso | prazo, anexos, forma de envio | autorização; TR; valor máximo | prazo de 3 dias úteis quando aplicável; anexos completos |
| Julgamento/Ata | `05_minutas/ATA_JULGAMENTO/ATA_JULGAMENTO_MINUTA_MAE.docx` | numero_processo, objeto, valor_estimado, fornecedor | propostas, habilitação, matriz de julgamento | propostas/documentos anexados | matriz proposta x requisito; ATENDE sempre com documento-fonte |
| Adjudicação/Homologação | `05_minutas/HOMOLOGACAO/TERMO_ADJUDICACAO_HOMOLOGACAO_MINUTA_MAE.docx` | fornecedor, valor_homologado, datas.homologacao | decisão da autoridade | ata/julgamento concluído | vencedor e valor coerentes com a ata |
| Contrato/substituto | `05_minutas/CONTRATO/CONTRATO_MINUTA_MAE.docx`, `05_minutas/CONTRATO_COMPRAS/` ou `05_minutas/ORDEM_FORNECIMENTO/` | fornecedor, valor_homologado, datas.homologacao, datas.contrato | cláusulas/campos variáveis da minuta | não gerar contrato sem data de homologação | campos `{{CAMPO}}` resolvidos; sem `[PREENCHER]` |
| Extrato | `05_minutas/EXTRATO/EXTRATO_CONTRATACAO_DIRETA_MINUTA_MAE.docx` | numero_processo, fundamento, objeto, fornecedor, valor_homologado | dados de publicação | homologação/ratificação | conteúdo confere com ato final |
| Ordem de Fornecimento | `05_minutas/ORDEM_FORNECIMENTO/ORDEM_FORNECIMENTO_MINUTA_MAE.docx` | objeto, fornecedor, valor_homologado, datas.contrato | prazo e condições de entrega | contrato/substituto definido | objeto e valores coerentes |
| Recebimento | `05_minutas/RECEBIMENTO/TERMO_RECEBIMENTO_ATESTO_MINUTA_MAE.docx` | objeto, fornecedor | atesto, responsável, data | entrega/execução realizada | recebimento compatível com contrato/OF |
| Registro CNAE | `scripts/controle_cnae.py registrar` | numero_processo, objeto, cnae_subclasse, valor_homologado, exercicio, fundamento | data de conclusão, descrição CNAE | contratação concluída | limites atualizados e relatório regenerado |

## Variante inexigibilidade (art. 74)

Roteiro completo, com a prova exigida por inciso e a justificativa de preço:
[roteiro-inexigibilidade-art-74.md](roteiro-inexigibilidade-art-74.md). Em 2026, esta variante
respondeu por **12 das 25 contratações concluídas** — não é caso excepcional.

O que **muda** em relação à tabela acima:

| Etapa da dispensa | Na inexigibilidade |
|---|---|
| Aviso, Julgamento/Ata, Adjudicação | **não existem** — não há disputa a julgar |
| Pesquisa de Preços | vira **justificativa de preço** (Portaria 03/2024, art. 6º, §§ 1º e 2º) |
| Justificativa | núcleo da peça: **inviabilidade de competição** + prova do inciso + razão da escolha (art. 72, VI) |
| Homologação | **Termo de Ratificação** (`05_minutas/RATIFICACAO/`), art. 72, VIII |
| Registro CNAE | `--conta-para-limite N`: não entra no somatório do art. 75, § 1º |

O que **não muda**: DFD, ETP (ou justificativa de dispensa), TR, certidão orçamentária,
habilitação do contratado (art. 72, V), autorização, contrato ou instrumento equivalente,
extrato/divulgação (art. 72, parágrafo único) e recebimento.

**Trava própria:** se a justificativa de preços demonstrar possibilidade de competição, a
inexigibilidade fica **vedada** (Portaria 03/2024, art. 6º, § 3º) — o fundamento muda, e o
achado se registra nos autos.

## Variante sem aviso

Quando `com_aviso` for `false`, substituir a etapa **Aviso** por certidão/justificativa de
dispensa de aviso:

- Minuta pendente: `05_minutas/CERTIDAO_DISPENSA_AVISO/`.
- Registrar motivo concreto para não publicar aviso.
- Seguir para julgamento/ratificação somente com documentos efetivamente juntados.
- Ausência de aviso não autoriza pular pesquisa de preços, dotação, justificativa, autorização,
  validação CNAE ou controle de campos pendentes.
