---
tipo: minuta
hierarquia: oficial
documento: documento de formalizacao de demanda para o pca
tema: plano de contratacoes anual
fonte: Câmara Municipal de Itanhandu / modelo enviado pelo usuário em 2026-07-01, revisado em 2026-09-23
orgao: camara municipal de itanhandu
uso: levantamento de demandas para elaboracao ou alteracao do PCA
versao: 1.1
vigencia: vigente
atualizado_em: 2026-09-23
tags: [minuta, dfd, pca, planejamento, renovacao, portaria-04-2024, portaria-08-2024, lei-14133,
  planejamento-estrategico, prioridade]
---

# Ficha de Uso — DFD para o PCA

Arquivo: `05_minutas/DFD/DFD_PARA_PCA_MINUTA_MAE.docx` (DOCX, timbre da Câmara). Versão anterior
(v1.0) em `05_minutas/DFD/_arquivo/DFD_PARA_PCA_MINUTA_MAE_v1.0.docx`.

## 1. Finalidade

Registrar a demanda que a Câmara pretende contratar, para **formar o PCA** do exercício seguinte ou
**alterar o PCA em execução**. É a origem do fluxo: o DFD da contratação
(`DFD_MINUTA_MAE.docx`), feito quando o processo é aberto, remete a este documento e ao item do PCA
que ele gerou.

**Usar para:** elaboração ou alteração do PCA.
**Não usar automaticamente como:** documento de abertura de uma contratação concreta, sem verificar
se as informações continuam atuais — para isso existe o DFD da contratação.

## 2. Dois fluxos (quadro 2 — "Finalidade do formulário")

| Fluxo | Quadros | Quem decide |
|---|---|---|
| **Elaboração do PCA** | 1 a 11; **excluir o quadro 12** | O coordenador do PCA analisa e consolida (art. 4º); a Presidência aprova ou redimensiona **o PCA consolidado** (art. 4º, parágrafo único), e não cada DFD |
| **Alteração do PCA em execução** | 1 a 12 | A Presidência aprova a alteração (art. 6º) no quadro 12 |

O "AUTORIZO a inclusão" individual da v1.0 foi retirado do fluxo ordinário: duplicava a aprovação do
PCA consolidado.

## 3. Estrutura e fundamento

| Quadro | Conteúdo | Fundamento |
|---|---|---|
| 1 | Identificação do requisitante (unidade, responsável, cargo, matrícula, e-mail, telefone) | art. 3º, I |
| 2 | Finalidade: elaboração ou alteração do PCA | arts. 4º e 6º |
| 3 | Identificação da demanda: natureza, objeto, tipo, quantidade, unidade, critério do quantitativo, subelemento, renovação, contrato | art. 3º, II e III; art. 2º, § 2º, I a VI |
| 4 | Justificativa da necessidade | art. 3º, IV |
| 5 | Alinhamento com o planejamento estratégico | art. 3º, V |
| 6 | Estimativa sumária (valor, referência, data; valores do contrato em renovação) | art. 3º, VI e § 1º |
| 7 | Data provável: mês previsto, data-limite de formalização e, em renovação, vigências | art. 3º, VII; art. 2º, § 2º, III |
| 8 | Vinculação ou dependência | art. 3º, VIII |
| 9 | Grau de prioridade (enquadramento e justificativa) | art. 3º, IX, e § 2º |
| 10 | Submissão pela chefia da área requisitante | art. 4º |
| 11 | Análise do coordenador do PCA: incorporada / devolvida / não incorporada | art. 4º; Portaria nº 08/2024, art. 5º |
| 12 | Aprovação da alteração do PCA pela Presidência (só no fluxo de alteração) | art. 6º |

**Por que o quadro 3 coleta tipo, subelemento e renovação:** são elementos do PCA consolidado (art. 2º,
§ 2º) e colunas do Anexo I da minuta do PCA (`05_minutas/PCA/`). Coletá-los aqui evita que o
coordenador tenha de buscá-los depois.

**Renovação:** a v1.0 trocava a data provável pela vigência. A v1.1 mantém as duas — a data-limite de
formalização cumpre o art. 3º, VII; a vigência atual e a pretendida informam a renovação.

## 4. Campos variáveis

| Campo | Conteúdo |
|---|---|
| `{{NUMERO_DFD}}`, `{{ANO_PCA}}` | Número deste DFD e exercício do PCA |
| `{{UNIDADE_REQUISITANTE}}`, `{{RESPONSAVEL_DEMANDA}}`, `{{CARGO_FUNCAO}}`, `{{MATRICULA}}`, `{{EMAIL_INSTITUCIONAL}}`, `{{TELEFONE_INSTITUCIONAL}}` | Requisitante (telefone institucional — documento público) |
| `{{OBJETO}}` | Descrição sucinta, sem marca, modelo ou especificação detalhada |
| `{{QUANTIDADE}}`, `{{UNIDADE_MEDIDA}}`, `{{CRITERIO_QUANTIDADE}}` | Quantidade para o exercício e como foi dimensionada |
| `{{SUBELEMENTO_DESPESA}}` | Quando conhecido; na falta, o coordenador indica |
| `{{NUMERO_CONTRATO}}`, `{{CONTRATADA}}` | Só em renovação |
| `{{JUSTIFICATIVA}}` | Situação atual, necessidade, risco de não atender, resultado esperado |
| `{{ALINHAMENTO_ESTRATEGICO}}` | Se houver planejamento estratégico formal |
| `{{ESTIMATIVA_VALOR}}`, `{{FONTE_ESTIMATIVA}}`, `{{DATA_ESTIMATIVA}}` | Estimativa sumária |
| `{{VALOR_CONTRATO}}`, `{{VALOR_EXERCICIO}}` | Só em renovação |
| `{{MES_PREVISTO}}`, `{{DATA_LIMITE_FORMALIZACAO}}` | Data provável |
| `{{VIGENCIA_ATUAL}}`, `{{VIGENCIA_PRETENDIDA}}` | Só em renovação |
| `{{VINCULACAO_DEPENDENCIA}}` | Contratação vinculada, se houver |
| `{{INCISO_PRIORIDADE}}`, `{{ALINEA_PRIORIDADE}}`, `{{JUSTIFICATIVA_PRIORIDADE}}` | Enquadramento no art. 3º, § 2º (só o inciso I tem alíneas) |
| `{{DATA_SUBMISSAO}}`, `{{CHEFIA_REQUISITANTE}}` | Submissão |
| `{{NUMERO_DEMANDA_PCA}}`, `{{OBSERVACAO_ANALISE}}`, `{{DATA_ANALISE}}`, `{{COORDENADOR_PCA}}` | Análise do coordenador (preenchidos por ele, não pelo requisitante) |
| `{{DATA_APROVACAO}}`, `{{PRESIDENTE}}` | Só no fluxo de alteração |

Campos de seleção `(  )` nos quadros 2, 3, 5, 8, 9 e 11. **Orientações em vermelho** devem ser
**excluídas antes da assinatura**. Para os critérios de prioridade, ver a seção 8 da ficha do DFD da
contratação.

## 5. Não inventar informações

O Charles não infere quantidade, valor, subelemento, prioridade, existência de planejamento
estratégico nem número da demanda no PCA. Dado ausente vira `[PREENCHER: ...]`.

## 6. Riscos e cautelas

- A estimativa sumária **não substitui** a pesquisa de preços (art. 3º, § 1º; Lei nº 14.133/2021,
  art. 23; Portaria nº 03/2024).
- O DFD para o PCA não substitui ETP, TR ou justificativa de contratação direta.
- Não confundir PCA com planejamento estratégico (quadro 5).
- Em renovação, conferir se a despesa prevista para o exercício está alinhada ao planejamento
  orçamentário.
- Descrição genérica do objeto prejudica a consolidação e o controle de fracionamento.
- Bem de consumo de luxo é vedado; identificado, o DFD é devolvido ao requisitante (Portaria
  nº 08/2024, arts. 3º e 5º).
- Demanda prevista e não executada no ano: justificar e, se ainda necessária, reincorporar ao PCA do
  exercício seguinte (Portaria nº 04/2024, art. 7º).

## 7. Fontes prioritárias

1. Lei nº 14.133/2021 (art. 12, VII; art. 18)
2. Portaria nº 04/2024 da Câmara (arts. 2º a 7º)
3. Portaria nº 08/2024 da Câmara (bens de consumo de luxo)
4. Fichas do DFD da contratação (`05_minutas/DFD/DFD_FICHA_DE_USO.md`) e do PCA
   (`05_minutas/PCA/PCA_FICHA_DE_USO.md`)

FONTES:
- 02_normas_internas/regulamento-licitacoes-camara-itanhandu.md | Portaria 04/2024, arts. 2º §2º, 3º, 4º, 6º, 7º; Portaria 08/2024, arts. 3º e 5º | vigente | 2026-06-25
- 01_legislacao/lei-14133-2021-licitacoes-contratos-administrativos.md | arts. 12 VII, 18, 23 | vigente | 2026-06-27
