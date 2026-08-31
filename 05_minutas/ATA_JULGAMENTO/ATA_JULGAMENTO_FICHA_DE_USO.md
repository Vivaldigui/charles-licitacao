---
tipo: minuta
hierarquia: oficial
documento: ata de julgamento
tema: contratacao direta
fonte: Câmara Municipal de Itanhandu / minuta-mãe redigida pelo Charles (Lei 14.133 + Portaria 06/2024)
orgao: camara municipal de itanhandu
uso: julgamento de dispensa com aviso de contratacao direta
versao: 1.0
vigencia: vigente
atualizado_em: 2026-07-31
tags: [minuta, ata, julgamento, dispensa, aviso, classificacao, habilitacao]
---

# Ficha de Uso — Ata de Julgamento (Dispensa com Aviso)

Arquivo: `05_minutas/ATA_JULGAMENTO/ATA_JULGAMENTO_MINUTA_MAE.docx` (DOCX, timbre no header).
Roteiro de análise: `07_checklists/roteiro-julgamento-dispensa-com-aviso.md`.

## 1. Finalidade
Registrar o julgamento das propostas e a habilitação na dispensa por valor **com aviso**
(Portaria 06/2024, arts. 11-19). Inclui **Anexo Único** com a ordem de classificação.

## 2. Como o Charles preenche
1. Segue o **roteiro de julgamento** (checklist) para analisar propostas, objeto, preço,
   classificação e habilitação.
2. Preenche os campos `{{...}}` da Ata com o resultado.
3. Registra **justificativa** em toda desclassificação/inabilitação.
4. Preenche o **Anexo Único** (quadro de classificação).

## 3. Campos variáveis (`{{...}}`)
**Cabeçalho:** `{{NUMERO_PROCESSO}}` · `{{NUMERO_DISPENSA}}` · `{{NUMERO_AVISO}}` · `{{OBJETO}}` ·
`{{CRITERIO_JULGAMENTO}}` · `{{VALOR_ESTIMADO}}` · `{{DATA_HORA_ABERTURA}}` · `{{DATA_EXTENSO}}`
**Corpo:** `{{RELACAO_PROPOSTAS}}` · `{{ANALISE_PROPOSTAS}}` · `{{RESULTADO_NEGOCIACAO}}` ·
`{{DESCLASSIFICACOES_JUSTIFICATIVA}}` · `{{ANALISE_HABILITACAO}}` ·
`{{INABILITACOES_JUSTIFICATIVA}}` · `{{VENCEDOR}}` · `{{CNPJ_CPF}}` · `{{VALOR_VENCEDOR}}` ·
`{{PROVIDENCIAS_FRACASSADO_DESERTO}}` · `{{DATA}}` · `{{NOME_AGENTE}}`
**Anexo Único (por fornecedor):** `{{CLASS_n}}` · `{{FORNECEDOR_n}}` · `{{CNPJCPF_n}}` ·
`{{PRECO_n}}` · `{{SITUACAO_n}}` (acrescentar/remover linhas conforme o nº de fornecedores).

**Seleções `(  )`:** negociação sim/não; houve/não desclassificações; habilitado/inabilitado;
fracassado/deserto.

## 4. O que NÃO alterar
Timbre, estrutura, numeração das seções, o Anexo Único e o bloco de assinatura do Agente de
Contratação — salvo revisão expressa.

## 5. Fontes prioritárias
1. Lei nº 14.133/2021 (arts. 8º, 68)
2. Portaria nº 06/2024 (arts. 11 a 19)
3. Portaria nº 24/2024 (art. 1º - agente de contratação designado)
4. Aviso de Contratação Direta e Termo de Referência do processo
5. Modelos oficiais (esta biblioteca)

## 6. Riscos e cautelas
- Justificar **sempre** desclassificação e inabilitação.
- Conferir **validade** das certidões na data exigida.
- Antes de desclassificar por inexequibilidade, abrir **diligência** (oportunidade de comprovação).
- Após a Ata: encaminhar ao Presidente para **adjudicação e homologação** (art. 19) — ver
  [[autorizacao-abertura]] e a futura minuta de homologação.
