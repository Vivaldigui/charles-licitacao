---
tipo: minuta
hierarquia: oficial
documento: documento de formalizacao de demanda
tema: planejamento da contratacao
fonte: Câmara Municipal de Itanhandu / minuta-mãe padronizada a partir de modelo enviado pelo usuário
orgao: camara municipal de itanhandu
uso: contratacoes diretas e licitacoes (fase de planejamento)
versao: 1.1
vigencia: vigente
atualizado_em: 2026-06-27
tags: [minuta, dfd, planejamento, pca, portaria-04-2024, lei-14133]
---

# Ficha de Uso — DFD (Documento de Formalização de Demanda)

Arquivo da minuta-mãe: `05_minutas/DFD/DFD_MINUTA_MAE.docx` (DOCX, timbre único da Câmara). Versão anterior em `.odt` foi substituída pelo padrão DOCX.

## 1. Finalidade

Esta minuta deve ser usada para elaboração do Documento de Formalização de Demanda – DFD
da Câmara Municipal de Itanhandu, peça que abre a fase de planejamento da contratação e
alimenta o Plano de Contratações Anual (PCA).

## 2. Regra principal

O Charles deve usar esta minuta como base obrigatória, preservando a estrutura, o timbre,
o cabeçalho, o rodapé, a ordem das seções, a linguagem institucional e os campos fixos.
Preenche **apenas** os campos entre chaves `{{...}}` e marca os campos de seleção `(  )`.

## 3. Campos variáveis (preencher)

| Campo | Conteúdo esperado |
|---|---|
| `{{UNIDADE_SETOR}}` | Unidade/setor requisitante |
| `{{RESPONSAVEL_REQUISITANTE}}` | Nome do requisitante (aparece também na assinatura) |
| `{{JUSTIFICATIVA_NECESSIDADE}}` | Fatos e fundamentos da necessidade, benefícios e problema a resolver (interesse público); pode usar dados, histórico de contratos |
| `{{DESCRICAO_OBJETO_QUANTIDADE}}` | Descrição resumida do objeto e quantidade (ou expectativa de consumo anual) |
| `{{ITEM_PCA}}` / `{{DESCRICAO_OBJETO_PCA}}` / `{{VALOR_PCA}}` | Preencher **quando a demanda estiver prevista no PCA** |
| `{{JUSTIFICATIVA_INCLUSAO_PCA}}` | Preencher **quando NÃO estiver prevista no PCA** (justificativa da inclusão) |
| `{{ESTIMATIVA_VALOR}}` | Estimativa sumária por procedimento simplificado (ex.: CATMAT/CATSER, Painel de Preços, sites, orçamentos) — **não** é a pesquisa de preços do art. 23 |
| `{{DATA_PROVAVEL_CONTRATACAO}}` | Data provável da contratação/aquisição |
| `{{VINCULACAO_DEPENDENCIA}}` | Indicar se há ou não vínculo/dependência em relação a outra contratação |
| `{{JUSTIFICATIVA_PRIORIDADE}}` | Justificativa do grau de prioridade marcado |
| `{{DATA_ASSINATURA}}` | Data da assinatura |

**Campos de seleção (marcar `X`):**
- Alinhamento ao PCA: `(  )` previsto / `(  )` não previsto.
- Grau de prioridade: `( )` ALTA / `( )` MÉDIA / `( )` BAIXA, conforme os critérios do
  art. 3º, §2º, da Portaria nº 04/2024.

## 4. O que NÃO pode ser alterado

- Timbre, cabeçalho, rodapé e brasão (estão no `styles.xml`).
- Numeração e ordem das seções.
- Bloco de assinatura.
- Cláusulas e fundamentos fixos (introdução e remissões legais), salvo solicitação expressa
  de revisão da minuta-mãe.

## 5. Fundamento das seções (Portaria nº 04/2024, art. 3º, I a IX)

| Seção da minuta | Inciso |
|---|---|
| Identificação da unidade/requisitante | I |
| Descrição do objeto | II |
| Quantidade | III |
| Justificativa | IV |
| Alinhamento ao planejamento/PCA | V |
| Estimativa preliminar do valor | VI |
| Data provável da contratação | VII |
| Vinculação ou dependência | VIII |
| Grau de prioridade | IX |

## 6. Fontes prioritárias

1. Lei nº 14.133/2021 (art. 12, VII; art. 18)
2. Portaria nº 04/2024 da Câmara Municipal de Itanhandu (PCA e DFD)
3. Demais portarias internas da Câmara
4. Modelos oficiais padronizados (esta biblioteca)
5. Artigos e materiais de apoio cadastrados no Charles

## 7. Comando padrão para geração

Ao gerar um DFD, o Charles deve preencher esta minuta conforme os dados fornecidos pelo
usuário, sem criar modelo novo e sem alterar a estrutura, salvo autorização expressa.
Quando faltar dado, marcar `[PREENCHER: ...]` e apontar a pendência ao final.

## 8. Riscos e cautelas

- O grau de prioridade deve ser coerente com os critérios objetivos do art. 3º, §2º, da
  Portaria nº 04/2024 — não classificar "alta" sem enquadramento.
- A estimativa sumária do DFD **não substitui** a pesquisa de preços do art. 23 da Lei
  14.133/2021 / Portaria nº 03/2024, exigida em fase posterior.
- Demanda fora do PCA exige justificativa aprovada pela Presidência (art. 6º da Portaria 04/2024).
