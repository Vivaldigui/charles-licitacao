---
tipo: minuta
documento: estudo tecnico preliminar
tema: planejamento da contratacao
fonte: Câmara Municipal de Itanhandu / modelo "Estudo Técnico Preliminar - Padronizado" enviado pelo usuário
orgao: camara municipal de itanhandu
uso: contratacoes diretas e licitacoes (fase preparatoria)
versao: 1.0
vigencia: vigente
atualizado_em: 2026-06-27
tags: [minuta, etp, planejamento, fase-preparatoria, portaria-12-2024, lei-14133, art-18]
---

# Ficha de Uso — ETP (Estudo Técnico Preliminar)

Arquivo da minuta-mãe: `05_minutas/ETP/ETP_MINUTA_MAE.docx` (formato DOCX, com timbre/brasão preservados no header).

## 1. Finalidade

Minuta para elaboração do Estudo Técnico Preliminar – ETP da Câmara Municipal de Itanhandu,
documento da fase preparatória que demonstra a viabilidade técnica e econômica da contratação
e dá base ao Termo de Referência.

## 2. Regra principal

O Charles usa esta minuta como base obrigatória, preservando estrutura, timbre, cabeçalho,
rodapé, ordem das 14 seções, numeração e linguagem institucional. Preenche **apenas** os
campos entre chaves `{{...}}`. As linhas "PREENCHIMENTO OBRIGATÓRIO/FACULTATIVO" e "DEFINIÇÃO:"
são orientações fixas — **não** são apagadas ao gerar o documento.

## 3. Campos variáveis (preencher)

**Capa:** `{{NUMERO_SOLICITACAO}}` · `{{OBJETO}}` · `{{LOCAL}}` · `{{MES}}` · `{{ANO}}`

**Seções (1 a 13):**

| # | Seção | Campo | Obrigatoriedade |
|---|---|---|---|
| 1 | Descrição da necessidade | `{{DESCRICAO_NECESSIDADE}}` | **Obrigatório** |
| 2 | Previsão no PCA | `{{PREVISAO_PCA}}` | Facultativo* |
| 3 | Estimativas das quantidades | `{{ESTIMATIVA_QUANTIDADES}}` | **Obrigatório** |
| 4 | Levantamento de mercado | `{{LEVANTAMENTO_MERCADO}}` | Facultativo* |
| 5 | Requisitos da contratação | `{{REQUISITOS_CONTRATACAO}}` | Facultativo* |
| 6 | Estimativa do valor | `{{ESTIMATIVA_VALOR}}` | **Obrigatório** |
| 7 | Descrição da solução como um todo | `{{DESCRICAO_SOLUCAO}}` | Facultativo* |
| 8 | Justificativa do parcelamento | `{{JUSTIFICATIVA_PARCELAMENTO}}` | **Obrigatório** |
| 9 | Resultados pretendidos | `{{RESULTADOS_PRETENDIDOS}}` | Facultativo* |
| 10 | Providências a serem adotadas | `{{PROVIDENCIAS_ADMINISTRACAO}}` | Facultativo* |
| 11 | Contratações correlatas/interdependentes | `{{CONTRATACOES_CORRELATAS}}` | Facultativo* |
| 12 | Possíveis impactos ambientais | `{{IMPACTOS_AMBIENTAIS}}` | Facultativo* |
| 13 | Declaração de viabilidade | `{{DECLARACAO_VIABILIDADE}}` | **Obrigatório** |

\* *Facultativo: quando não for preenchido, o campo deve trazer a **justificativa da
inaplicabilidade** (art. 18, §3º, da Lei 14.133/2021 e art. 2º, §1º, da Portaria 12/2024).*

**Assinatura:** `{{NOME_SERVIDOR}}` · `{{LOCAL}}` · `{{DIA}}` · `{{MES}}` · `{{ANO}}`

## 4. O que NÃO pode ser alterado

- Timbre, cabeçalho, rodapé e brasão (header do DOCX).
- Numeração e ordem das 14 seções e a Introdução.
- Textos fixos "PREENCHIMENTO OBRIGATÓRIO/FACULTATIVO" e "DEFINIÇÃO:".
- Bloco de aprovação e assinatura.
- Salvo solicitação expressa de revisão da minuta-mãe.

## 5. Fundamento das seções (Portaria nº 12/2024, art. 2º, I a XIII = art. 18, §1º, Lei 14.133/2021)

Obrigatórios (art. 2º, §1º): incisos **I (seção 1), IV (3), VI (6), VIII (8) e XIII (13)**.
Os demais, quando não contemplados, exigem justificativa.

## 6. Fontes prioritárias

1. Lei nº 14.133/2021 (art. 18, §1º e §3º)
2. Portaria nº 12/2024 da Câmara Municipal de Itanhandu (diretrizes e estrutura do ETP)
3. Demais portarias internas da Câmara (ex.: Portaria 03/2024 — pesquisa de preços; Portaria 13/2024 — TR)
4. Modelos oficiais padronizados (esta biblioteca)
5. Artigos e materiais de apoio cadastrados no Charles

## 7. Comando padrão para geração

Ao gerar um ETP, o Charles preenche esta minuta conforme os dados fornecidos, sem criar
modelo novo e sem alterar a estrutura. Faltando dado, marcar `[PREENCHER: ...]` e apontar
a pendência ao final.

## 8. Riscos e cautelas

- **Cabimento do ETP:** verificar na Portaria 12/2024 (art. 8º e art. 9º) e na Lei 14.133/2021
  as hipóteses de dispensa/simplificação do estudo antes de exigi-lo.
- **Requisitos (seção 5):** não inserir exigências imoderadas — risco de direcionamento e
  de frustrar a competitividade.
- **Estimativa do valor (seção 6):** pode ser sumária (art. 2º, §3º, da Portaria 12/2024),
  mas deve refletir a realidade de mercado; não confundir com a pesquisa de preços do art. 23.
- A declaração de viabilidade (seção 13) deve ser referendada pela autoridade competente.
- Vedada a participação do agente de contratação na elaboração do ETP (art. 8º, §1º, do
  regulamento interno).
