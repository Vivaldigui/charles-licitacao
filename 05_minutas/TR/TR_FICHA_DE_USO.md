---
tipo: minuta
hierarquia: oficial
documento: termo de referencia
tema: fase preparatoria da contratacao
fonte: Câmara Municipal de Itanhandu / modelo "Termo de Referência - Padronizado" enviado pelo usuário
orgao: camara municipal de itanhandu
uso: compras de bens e contratacao de servicos (licitacao e contratacao direta)
versao: 1.0
vigencia: vigente
atualizado_em: 2026-07-26
tags: [minuta, tr, termo-de-referencia, fase-preparatoria, portaria-13-2024, lei-14133, art-6-XXIII]
---

# Ficha de Uso — TR (Termo de Referência)

Arquivo da minuta-mãe: `05_minutas/TR/TR_MINUTA_MAE.docx` (DOCX, com timbre/brasão preservados no header).

## 1. Finalidade

Minuta para elaboração do Termo de Referência da Câmara Municipal de Itanhandu, para compra
de bens e contratação de serviços, tanto em licitação quanto em contratação direta
(art. 8º da Portaria nº 13/2024).

## 2. Regra principal

O Charles usa esta minuta como base obrigatória, preservando estrutura, timbre, cabeçalho,
rodapé, ordem das seções e linguagem institucional. Preenche os campos `{{...}}`, **escolhe**
entre as cláusulas alternativas marcadas com **"OU"** e completa os pontos abertos do corpo.

## 3. Campos variáveis fixos (`{{...}}`)

| Campo | Onde / conteúdo |
|---|---|
| `{{NUMERO_SOLICITACAO}}` | Cabeçalho ("Solicitação nº") |
| `{{OBJETO}}` | Linha OBJETO (descrição sintética do que se pretende contratar) |
| `{{FORMA_SELECAO}}` | Ex.: LICITAÇÃO ou CONTRATAÇÃO DIRETA |
| `{{MODALIDADE}}` | Ex.: PREGÃO, CONCORRÊNCIA, DISPENSA |
| `{{FORMA}}` | Ex.: ELETRÔNICA / PRESENCIAL |
| `{{CRITERIO_JULGAMENTO}}` | Ex.: pelo menor preço, maior desconto |
| `{{DOTACAO_ORCAMENTARIA}}` | Adequação orçamentária (dotações utilizadas) |
| `{{DATA}}` | Data da assinatura (local "Itanhandu" já fixo) |
| `{{NOME_RESPONSAVEL}}` | Assinatura |
| `{{CARGO}}` | Assinatura |

## 4. Pontos abertos do corpo (preencher conforme o caso)

Além dos `{{...}}`, o modelo tem **pontos de preenchimento por caso concreto**, mantidos como
no original: blocos alternativos **"OU"** (prazo, garantia, subcontratação, qualificação
econômica) e marcadores `____`, `(...)`, `(definir ...)` (prazos de entrega, dias de amostra,
meses de garantia, percentuais etc.).

Regra de geração: o Charles **escolhe uma** opção de cada bloco "OU" (apagando as demais) e
substitui cada marcador pelo dado do processo; quando o dado depender de decisão humana ou
jurídica, marca `[PREENCHER: ...]` e aponta a pendência ao final.

## 5. Sub-blocos opcionais de REQUISITOS DA CONTRATAÇÃO

Amostra, Ficha Técnica, Garantia da Contratação e Subcontratação são **opcionais** — manter
apenas os aplicáveis ao objeto e remover/justificar os demais. Não inserir exigências
imoderadas (risco de direcionamento e de frustrar a competitividade).

## 6. Estrutura x Lei (art. 6º, XXIII, "a" a "j", da Lei 14.133/2021)

| Seção da minuta | Alínea |
|---|---|
| Objeto / descrição detalhada / prazo da contratação | a |
| Fundamentação e descrição da necessidade (referência ao ETP) | b |
| Descrição da solução como um todo (ciclo de vida) | c |
| Requisitos da contratação | d |
| Modelo de execução do objeto | e |
| Modelo de gestão do contrato | f |
| Critérios de medição e de pagamento | g |
| Forma e critérios de seleção do fornecedor | h |
| Estimativas do valor da contratação | i |
| Adequação orçamentária | j |

## 7. O que NÃO pode ser alterado

- Timbre, cabeçalho, rodapé e brasão (header do DOCX).
- Ordem das seções e a numeração padrão.
- Cláusulas fixas de gestão/fiscalização, recebimento, liquidação e pagamento, salvo
  ajuste necessário ao objeto.
- Bloco de assinatura.

## 8. Fontes prioritárias

1. Lei nº 14.133/2021 (art. 6º, XXIII; art. 40, §1º)
2. Portaria nº 13/2024 da Câmara Municipal de Itanhandu (elaboração do TR)
3. Portaria nº 12/2024 (ETP, do qual o TR deriva) e demais portarias internas
4. Modelos oficiais padronizados (esta biblioteca)
5. Artigos e materiais de apoio cadastrados no Charles

## 9. Riscos e cautelas

- TR só após o ETP, quando exigível (art. 3º da Portaria 13/2024); dispensado nas hipóteses
  do art. 9º (deserta/fracassada, adesão a ARP, prorrogação de contínuos).
- Aprovação do TR compete ao Presidente da Câmara (art. 7º da Portaria 13/2024).
- "Marcas de referência" só com justificativa técnica — atenção ao risco de direcionamento.
- A estimativa do valor (seção própria) remete ao quadro de prévias/pesquisa de preços
  (Portaria nº 03/2024), em documento separado.

## 10. Especificação técnica: resumo na tabela, detalhamento abaixo dela

A tabela de itens do TR é **resumo** do item — Item · Código/CATMAT · Unidade · Quantidade ·
descrição curta · Valor. A **especificação técnica completa não entra na célula
"Especificação"**.

Como fazer:

- Na célula "Especificação", apenas a descrição curta do item, encerrando com algo como
  "conforme especificação técnica detalhada abaixo desta tabela".
- Logo **após a tabela**, inserir a especificação em texto corrido justificado, sob subtítulo
  do tipo "Especificação técnica detalhada do item N", um parágrafo por componente/requisito.
- Numerar esses parágrafos como **"(1) …", "(2) …"** — **nunca** "1. …": o classificador do
  `scripts/docx_cmi/formatar_docx.py` trata linha curta iniciada por "N." como título e a
  deixa em negrito indevidamente; o prefixo entre parênteses preserva a numeração sem
  disparar essa heurística.

Motivo: especificação longa dentro da célula estreita estoura a altura da linha, o Word
empurra a linha inteira para a página seguinte e o documento fica grande e com páginas quase
em branco (caso real: 26 páginas, ~7 de tabela quase vazia). Fora da tabela, o mesmo conteúdo
vira texto de largura total, legível, e o documento encolhe.

Isso é **organização do conteúdo na geração**, não reescrita: ao padronizar um TR já
existente, mover a especificação para fora da tabela preserva a redação, os valores e as
quantidades **verbatim**, conforme
`09_padronizacao_documental/REGRAS_DE_FORMATACAO.md`.
