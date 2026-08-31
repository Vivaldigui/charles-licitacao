---
tipo: minuta
hierarquia: oficial
documento: contrato administrativo
tema: contratacao direta e licitacao
fonte: Câmara Municipal de Itanhandu / minuta-mãe aprimorada a partir de contrato real (Inexigibilidade 01/2026 - Auditoria CEI)
orgao: camara municipal de itanhandu
uso: formalizacao de contratos (dispensa, inexigibilidade e licitacao) - generico para qualquer objeto
versao: 1.1
vigencia: vigente
atualizado_em: 2026-06-27
tags: [minuta, contrato, art-92, art-95, portaria-19-2024, lgpd, anticorrupcao, lei-14133]
---

# Ficha de Uso — Contrato Administrativo

Arquivo: `05_minutas/CONTRATO/CONTRATO_MINUTA_MAE.docx` (DOCX, timbre no header).

## 1. Finalidade
Termo de contrato administrativo para formalizar contratações da Câmara (dispensa,
inexigibilidade e licitação), com as cláusulas do art. 92 da Lei 14.133/2021 e da
Portaria 19/2024.

## 2. Campos variáveis (`{{...}}`)
`{{NUMERO_CONTRATO}}` · `{{NOME_PRESIDENTE}}` · `{{CONTRATADO}}` · `{{CNPJ_CONTRATADO}}` ·
`{{ENDERECO_CONTRATADO}}` · `{{REPRESENTANTE_CONTRATADO}}` · `{{CARGO_REPRESENTANTE}}` ·
`{{TIPO_PROCESSO}}` (ex.: Processo de Inexigibilidade) · `{{NUMERO_PROCESSO}}` ·
`{{MODALIDADE_EXTENSO}}` (ex.: Inexigibilidade de Licitação / Dispensa de Licitação) ·
`{{OBJETO}}` · `{{VALOR_TOTAL}}` · `{{VALOR_TOTAL_EXTENSO}}` · `{{CONDICOES_PAGAMENTO}}` ·
`{{DOTACAO_ORCAMENTARIA}}` · `{{DATA}}` · `{{PRAZO_VIGENCIA}}` · `{{REGIME_EXECUCAO}}` ·
`{{CONDICOES_SUBCONTRATACAO}}`
(O CNPJ/endereço da Câmara já constam fixos.)

## 3. Aprimoramentos aplicados

- **Generalizado para QUALQUER contratação (v1.1):** removidas as cláusulas específicas de
  auditoria (NBC-TA, "5 relatórios anuais", vigência atrelada a "relatórios") e o linguajar de
  obras (preposto "no local", guarda/vigilância de materiais, limpeza do local, "memorial
  descritivo", acesso "ao local dos trabalhos"). Vigência, regime de execução, subcontratação e
  garantia passaram a remeter ao **Termo de Referência** / campos `{{...}}`.
- **Adicionada a CLÁUSULA DÉCIMA OITAVA – Proteção de Dados (LGPD) e Anticorrupção**, exigida
  pelo **art. 2º, I e II, da Portaria 19/2024** (estava ausente).
- **Corrigida a contradição de preço:** retirado o "valor meramente estimativo/por
  quantitativos" (o contrato é **preço global fixo**).
- **Corrigido o vínculo:** "aviso de dispensa eletrônica" → "aviso de contratação direta,
  quando houver" (serve a dispensa e inexigibilidade).
- **Corrigida a remissão das sanções:** "subitem 12.1" → "11.1".

## 4. Fontes prioritárias
1. Lei nº 14.133/2021 (art. 89 a 95; cláusulas do art. 92; art. 124 e ss.)
2. Portaria nº 19/2024 da Câmara (contratos — arts. 2º, 3º, 4º, 5º, 6º)
3. Termo de Referência do processo (execução, recebimento, fiscalização, pagamento)
4. Modelos oficiais (esta biblioteca)

## 5. Riscos e cautelas
- **Definir por objeto:** preencher `{{REGIME_EXECUCAO}}`, `{{PRAZO_VIGENCIA}}` e a opção de
  `{{CONDICOES_SUBCONTRATACAO}}` conforme o Termo de Referência de cada contratação.
- **Conferir a dosimetria das sanções:** as multas remetem a alíneas "a) a h)" do subitem
  11.1 — confirmar que a lista de infrações está com as letras correspondentes.
- **Recebimento/fiscalização/pagamento** seguem o TR (art. 5º da Portaria 19/2024).
- **Publicação no PNCP** é condição de eficácia (art. 94) — usar [[extrato-de-contratacao-direta]].
- **Instrumento substitutivo:** na dispensa por valor/entrega imediata, pode-se usar a
  [[ordem-de-fornecimento]] em vez do termo de contrato (art. 95).
- Validação jurídica antes do 1º uso oficial.
