---
tipo: minuta
hierarquia: oficial
documento: documento de formalizacao de demanda
tema: planejamento da contratacao
fonte: Câmara Municipal de Itanhandu / minuta-mãe padronizada a partir de modelo enviado pelo usuário
orgao: camara municipal de itanhandu
uso: abertura do processo de contratacao concreta (contratacoes diretas e licitacoes)
versao: 1.2
vigencia: vigente
atualizado_em: 2026-09-23
tags: [minuta, dfd, planejamento, pca, portaria-04-2024, portaria-08-2024, lei-14133,
  planejamento-estrategico, prioridade]
---

# Ficha de Uso — DFD da contratação (Documento de Formalização de Demanda)

Arquivo: `05_minutas/DFD/DFD_MINUTA_MAE.docx` (DOCX, timbre da Câmara). Versão anterior (v1.1) em
`05_minutas/DFD/_arquivo/DFD_MINUTA_MAE_v1.1.docx`.

## 1. Finalidade e relação com o DFD para o PCA

A base tem **dois** DFDs, com funções diferentes:

| Documento | Momento | Função |
|---|---|---|
| DFD para o PCA (`DFD_PARA_PCA_MINUTA_MAE.docx`) | Elaboração do PCA do exercício seguinte ou alteração do PCA em execução | Registrar a demanda que poderá virar contratação |
| **DFD da contratação (esta minuta)** | Quando o processo administrativo é efetivamente aberto | Confirmar a necessidade atual, a quantidade atualizada, o vínculo com o PCA e a prioridade |
| ETP, quando cabível | Depois | Estudar o problema e a solução |
| Termo de Referência | Depois | Especificar definitivamente o objeto |

Este DFD **não inclui demanda no PCA nem autoriza a alteração do Plano**. A alteração se formaliza
pelo DFD para o PCA (finalidade "alteração"), com aprovação da Presidência (Portaria nº 04/2024,
art. 6º).

## 2. Antes de gerar

1. **Verificar se existe DFD para o PCA da mesma demanda.** Se existir, recuperar o número do DFD e o
   item do PCA e marcar a primeira opção da seção 2 ("Origem da demanda").
2. Havendo DFD para o PCA atual e completo, as seções 3 a 5 podem **remeter a ele**, registrando só o
   que mudou (quantidade, estimativa, data). Se a necessidade, a quantidade ou o contexto mudaram
   substancialmente, preencher tudo de novo.
3. Conferir no **PCA publicado** o item, a descrição e o valor. Nunca inferir.

## 3. Regra de conteúdo

O DFD formaliza **a necessidade**, não desenvolve a solução. Deve permitir o planejamento, mas não
antecipa, sem necessidade:

- especificação técnica detalhada, marca ou modelo;
- requisitos de habilitação;
- obrigações contratuais ou cláusulas próprias de Termo de Referência;
- metodologia de pesquisa de preços.

Exemplo: "aquisição de computadores para substituição de equipamentos obsoletos dos setores X e Y" —
e não processador, memória, armazenamento, marca ou garantia.

**A justificativa (seção 3) deve responder:** qual é a situação atual ou o problema; por que há
necessidade administrativa; qual o prejuízo ou risco de não atender; qual resultado a Câmara pretende
alcançar.

## 4. Não inventar informações

O Charles **não infere** e marca `[PREENCHER: ...]` quando o dado não for fornecido:

- que a demanda consta do PCA, o número do item, a descrição ou o valor no PCA;
- o número do DFD para o PCA;
- a existência de planejamento estratégico;
- a quantidade e o critério de dimensionamento;
- o valor estimado, a fonte e a data da referência;
- o grau de prioridade e seu enquadramento;
- disponibilidade orçamentária (não é declarada no DFD; comprova-se depois — Lei nº 14.133/2021,
  art. 72, IV; minuta `CERTIDAO_ORCAMENTARIA/`).

## 5. Estrutura e fundamento (Portaria nº 04/2024, art. 3º)

| Seção da minuta | Fundamento |
|---|---|
| 1. Identificação da unidade demandante (unidade, responsável, cargo) | art. 3º, I |
| 2. Origem da demanda (DFD para o PCA e item) | controle interno — liga ao PCA |
| 3. Justificativa da necessidade | art. 3º, IV |
| 4. Descrição sucinta do objeto | art. 3º, II |
| 5. Quantidade estimada e critério de dimensionamento | art. 3º, III ("considerada a expectativa de consumo anual") |
| 6. Alinhamento com o planejamento estratégico | art. 3º, V ("quando houver") |
| 7. Situação da demanda no PCA (prevista / não prevista / dispensada) | arts. 2º, § 3º, e 6º |
| 8. Estimativa sumária do valor (valor, referência, data) | art. 3º, VI e § 1º |
| 9. Data provável da contratação | art. 3º, VII |
| 10. Vinculação ou dependência | art. 3º, VIII |
| 11. Grau de prioridade (enquadramento e justificativa) | art. 3º, IX, e § 2º |

**Planejamento estratégico ≠ PCA.** O art. 3º, V, trata do planejamento estratégico. A previsão no PCA
é tratada à parte, na seção 7.

## 6. Campos variáveis

| Campo | Conteúdo |
|---|---|
| `{{UNIDADE_SETOR}}`, `{{RESPONSAVEL_REQUISITANTE}}`, `{{CARGO_FUNCAO}}` | Requisitante (nome e cargo também na assinatura) |
| `{{NUMERO_DFD_PCA}}`, `{{ITEM_PCA}}`, `{{ANO_PCA}}` | Origem no DFD para o PCA e item do PCA (seções 2 e 7) |
| `{{JUSTIFICATIVA_NECESSIDADE}}` | Ver seção 3 desta ficha |
| `{{DESCRICAO_OBJETO}}` | Descrição sucinta, sem especificação detalhada |
| `{{QUANTIDADE_ESTIMADA}}`, `{{CRITERIO_QUANTIDADE}}` | Quantidade e como foi dimensionada |
| `{{ALINHAMENTO_ESTRATEGICO}}` | Instrumento e objetivo, se houver planejamento estratégico formal |
| `{{DESCRICAO_OBJETO_PCA}}`, `{{VALOR_PCA}}` | Conferidos no PCA publicado |
| `{{JUSTIFICATIVA_INCLUSAO_PCA}}` | Só quando não prevista no PCA |
| `{{INCISO_DISPENSA_PCA}}`, `{{FUNDAMENTO_DISPENSA_PCA}}` | Só nas hipóteses do art. 2º, § 3º |
| `{{ESTIMATIVA_VALOR}}`, `{{FONTE_ESTIMATIVA}}`, `{{DATA_ESTIMATIVA}}` | Estimativa sumária |
| `{{DATA_PROVAVEL_CONTRATACAO}}` | Data provável |
| `{{VINCULACAO_DEPENDENCIA}}` | Contratação vinculada, se houver |
| `{{INCISO_PRIORIDADE}}`, `{{ALINEA_PRIORIDADE}}`, `{{JUSTIFICATIVA_PRIORIDADE}}` | Enquadramento no art. 3º, § 2º |
| `{{DATA_ASSINATURA}}` | Data |

Campos de seleção `(  )`: seções 2, 6, 7, 10 e 11. **Orientações em vermelho** são instruções da
minuta e devem ser **excluídas antes da assinatura**. A frase em itálico preto da seção 8 é texto do
documento e permanece.

## 7. Situação no PCA — as três opções

- **Prevista:** preencher a tabela com os dados do PCA publicado.
- **Não prevista:** a justificativa **subsidia a proposta** de alteração do Plano; quem aprova é a
  Presidência (art. 6º). O requisitante não declara que o PCA foi alterado.
- **Dispensada de indicação:** só nas hipóteses do art. 2º, § 3º — art. 75, VI, VII e VIII, da Lei
  nº 14.133/2021 (inciso I) e pequenas compras e serviços de pronto pagamento do art. 95, § 2º
  (inciso II). **A dispensa em razão do valor (art. 75, I e II) não está dispensada de indicação no
  PCA.** Verificar esta opção antes de tratar a demanda como "não prevista".

## 8. Grau de prioridade (art. 3º, § 2º)

| Grau | Hipóteses |
|---|---|
| ALTA (inciso I) | a) renovação ou prorrogação de serviço continuado em execução; b) material de consumo ou serviço cuja falta possa comprometer o funcionamento da Câmara; c) prazo legal, decisão judicial ou determinação de órgão de controle; d) acessória ou vinculada a contratação de prioridade alta; e) assim classificada pelo Presidente |
| MÉDIA (inciso II — sem alíneas) | serviço sem contratação vigente; material de consumo fora do inciso I; bem permanente para substituir bem danificado ou deteriorado; acessória ou vinculada a contratação de prioridade média |
| BAIXA (inciso III) | bem permanente que não substitua outro existente; obras e serviços não incluídos nos incisos I e II |

Só o inciso I tem alíneas. No inciso III, o texto publicado traz uma hipótese sem letra seguida de
"b)"; indicar apenas o inciso nesse caso.

## 9. Riscos e cautelas

- Não confundir PCA com planejamento estratégico.
- Não declarar disponibilidade orçamentária no DFD.
- A estimativa sumária **não é** pesquisa de preços (art. 3º, § 1º; Lei nº 14.133/2021, art. 23;
  Portaria nº 03/2024).
- Não classificar prioridade sem enquadramento no art. 3º, § 2º.
- Não justificar a quantidade com expressão genérica.
- Bem de consumo de luxo é vedado (Portaria nº 08/2024, art. 3º); se identificado no PCA, o DFD é
  devolvido ao requisitante (art. 5º).
- A assinatura não traz mais a frase fixa "Assinado eletronicamente" (nenhuma outra minuta a usa);
  a forma de assinatura segue o meio efetivamente utilizado.

## 10. Fontes prioritárias

1. Lei nº 14.133/2021 (art. 12, VII; art. 18; art. 72, I e IV)
2. Portaria nº 04/2024 da Câmara (arts. 2º, § 3º; 3º; 6º)
3. Portaria nº 08/2024 da Câmara (bens de consumo de luxo)
4. Ficha do DFD para o PCA (`05_minutas/DFD/DFD_PARA_PCA_FICHA_DE_USO.md`) e do PCA
   (`05_minutas/PCA/PCA_FICHA_DE_USO.md`)

FONTES:
- 02_normas_internas/regulamento-licitacoes-camara-itanhandu.md | Portaria 04/2024, arts. 2º §3º, 3º, 4º, 6º; Portaria 08/2024, arts. 3º e 5º | vigente | 2026-06-25
- 01_legislacao/lei-14133-2021-licitacoes-contratos-administrativos.md | arts. 12 VII, 18, 72 I e IV, 75 VI a VIII, 95 §2º | vigente | 2026-06-27
