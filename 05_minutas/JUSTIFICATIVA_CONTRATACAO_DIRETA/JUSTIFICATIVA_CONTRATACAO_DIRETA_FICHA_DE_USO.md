---
tipo: minuta
hierarquia: oficial
documento: justificativa de contratacao direta
tema: contratacao direta
fonte: Câmara Municipal de Itanhandu / minuta-mãe redigida pelo Charles (Lei 14.133 + Portarias 03 e 06/2024)
orgao: camara municipal de itanhandu
uso: dispensa e inexigibilidade (peça central de fundamentacao)
versao: 1.1
vigencia: vigente
atualizado_em: 2026-06-27
tags: [minuta, justificativa, contratacao-direta, art-72, art-74, art-75, aviso, dispensa, inexigibilidade]
---

# Ficha de Uso — Justificativa de Contratação Direta

Arquivo: `05_minutas/JUSTIFICATIVA_CONTRATACAO_DIRETA/JUSTIFICATIVA_CONTRATACAO_DIRETA_MINUTA_MAE.docx` (DOCX, timbre da Câmara no header).

## 1. Finalidade

Peça central da contratação direta: reúne o **enquadramento legal**, a **razão da escolha do
contratado** (art. 72, VI), a **justificativa de preço** (art. 72, VII), a **justificativa da
(não) divulgação do aviso** (art. 75, §3º) e a verificação da habilitação (art. 72, V).
Serve tanto para **dispensa** (art. 75) quanto para **inexigibilidade** (art. 74).

## 2. Campos variáveis (`{{...}}`)

`{{NUMERO_SOLICITACAO}}` · `{{NUMERO_PROCESSO}}` · `{{MODALIDADE}}` · `{{NUMERO_DISPENSA}}` ·
`{{OBJETO}}` · `{{VALOR_ESTIMADO}}` · `{{VALOR_ESTIMADO_EXTENSO}}` · `{{MODALIDADE_EXTENSO}}` ·
`{{FUNDAMENTO_LEGAL}}` · `{{JUSTIFICATIVA_ENQUADRAMENTO}}` · `{{SOMATORIO_EXERCICIO}}` ·
`{{CONTRATADO}}` · `{{CNPJ_CPF}}` · `{{RAZAO_ESCOLHA}}` · `{{METODO_PESQUISA}}` ·
`{{JUSTIFICATIVA_MENOS_ORCAMENTOS}}` · `{{JUSTIFICATIVA_NAO_AVISO}}` ·
`{{JUSTIFICATIVA_HABILITACAO}}` · `{{DATA}}` · `{{NOME_RESPONSAVEL}}` · `{{CARGO}}`

**Seleções `(  )`:** menos de 3 preços / objeto exclusivo (item 4); houve aviso / não houve
aviso (item 5); habilitação dispensada (item 6). Marcar apenas as aplicáveis e apagar/justificar
as demais.

## 3. Regras-chave embutidas

- **Aviso é preferencial** (art. 75, §3º; Portaria 06/2024, art. 2º) — pode-se dispensar, mas
  a ausência deve ser **motivada** (item 5, com 3 motivos usuais a/b/c).
- **Pesquisa de preços:** regra de 3+ preços (Portaria 03/2024, art. 5º); **menos de 3** só com
  justificativa **e aprovação do Presidente** (art. 5º, §7º); objeto exclusivo → notas fiscais
  (art. 6º, §§1º-2º).
- **Anti-fracionamento:** registrar o somatório do exercício por ramo de atividade/CNAE
  (art. 75, §1º, da Lei; art. 2º, §§1º-2º, da Portaria 06/2024).
- **Habilitação** pode ser dispensada nos casos do art. 16 da Portaria 06/2024.
- **Análise jurídica (item 7):** em regra **dispensável** nas contratações diretas de menor
  valor com minuta padronizada ou entrega imediata, nos termos do **Ato do Diretor Jurídico
  nº 01/2024** (até 50% dos limites do art. 75, I e II); exigível acima do limite ou havendo
  dúvida jurídica. Ver [[ato-diretor-juridico-01-2024-dispensa-analise-juridica]].

## 4. O que NÃO alterar
Timbre, estrutura, numeração das seções e as remissões legais — salvo revisão expressa.

## 5. Fontes prioritárias
1. Lei nº 14.133/2021 (arts. 72, 74, 75 e §§)
2. Portaria nº 06/2024 (contratação direta) e Portaria nº 03/2024 (pesquisa de preços)
3. Demais portarias internas
4. Modelos oficiais (esta biblioteca)
5. Artigos e materiais de apoio

## 6. Riscos e cautelas

- **Execução antes da formalização é irregular.** A justificativa NÃO legitima iniciar o
  serviço antes da autorização (art. 72, VIII) e do empenho. Se já ocorreu, é caso de
  reconhecimento de dívida e análise jurídica — não de "justificar a ausência do aviso".
- **Inexigibilidade (art. 74):** vedada se houver competição possível (Portaria 03/2024,
  art. 6º, §3º); a justificativa de preço segue o art. 6º, §1º (notas fiscais).
- O `{{FUNDAMENTO_LEGAL}}` deve casar com `{{MODALIDADE_EXTENSO}}`.
- Encaminhar para **parecer jurídico** (art. 72, III) e **autorização** (art. 72, VIII) — ver
  [[autorizacao-abertura]] e [[certidao-recursos-orcamentarios]].
- Validação jurídica antes do 1º uso oficial.
