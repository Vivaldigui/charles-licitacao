---
tipo: minuta
hierarquia: oficial
documento: plano de contratacoes anual
tema: plano de contratacoes anual
fonte: Camara Municipal de Itanhandu / arquitetura adaptada do PCA 2026 do TCE-MG (12_pca/modelo/plano-anual-de-contratacoes-2026.pdf)
orgao: camara municipal de itanhandu
uso: elaboracao do PCA do exercicio subsequente
versao: 1.0
vigencia: vigente
atualizado_em: 2026-08-04
tags: [minuta, pca, plano-de-contratacoes-anual, planejamento, portaria-04-2024, lei-14133, tce-mg]
---

# Ficha de Uso — Plano de Contratações Anual (PCA)

Arquivo da minuta-mãe: [`05_minutas/PCA/PCA_MINUTA_MAE.docx`](PCA_MINUTA_MAE.docx).

## 1. Finalidade

Modelo do **corpo do Plano de Contratações Anual** da Câmara Municipal de Itanhandu — o
documento narrativo que consolida e apresenta as demandas do exercício seguinte, aprovado
pela Presidência e divulgado no sítio oficial e no PNCP.

**Não substitui o registro do PCA no sistema de compras.** O registro de referência é o
gerado pelo sistema e publicado no PNCP (art. 5º da Portaria nº 04/2024). Esta minuta
produz o **memorial que o acompanha**. Havendo divergência entre os dois, ela deve ser
sanada antes da divulgação — não apenas registrada.

## 2. Quando usar

- "elabore o PCA {{ano}}";
- "monte o Plano de Contratações Anual";
- "atualize o PCA para o próximo exercício";
- consolidação dos DFD do levantamento anual de necessidades.

Para **coletar** cada demanda, use antes
[`DFD/DFD_PARA_PCA_MINUTA_MAE.docx`](../DFD/DFD_PARA_PCA_MINUTA_MAE.docx). Esta minuta
consolida; aquela levanta.

## 3. Origem da arquitetura

A estrutura reproduz a do **PCA 2026 do Tribunal de Contas do Estado de Minas Gerais**
(`12_pca/modelo/plano-anual-de-contratacoes-2026.pdf`): documento principal enxuto —
apresentação, classificação por categoria econômica, unidades, lista corrida de
contratações planejadas, notas explicativas — com o detalhamento analítico remetido a
anexo.

O TCE-MG é referência de **forma**, não de rito nem de competência. Não foram importados
para esta minuta a Portaria nº 1/PRES./2024, a Resolução Delegada nº 01/2025, a
Coordenadoria de Planejamento das Contratações nem a distinção "unidade de pedido ×
unidade demandante" daquela Corte. O conteúdo obrigatório vem da **Portaria nº 04/2024 da
Câmara Municipal de Itanhandu** e da **Lei nº 14.133/2021**.

Diferenças deliberadas em relação ao modelo do TCE-MG:

| Ponto | TCE-MG | Esta minuta | Motivo |
|---|---|---|---|
| Metodologia da estimativa | não há seção própria | item 2 | as estimativas da Câmara derivam de execução corrigida por índice; a metodologia precisa ficar explícita |
| Unidades | "unidade de pedido × unidade demandante" | "unidades requisitantes e competências" | a Câmara não tem unidades de pedido; a coordenação é do contador (art. 4º da Portaria nº 04/2024) |
| Anexo analítico | planilha Excel apartada | Anexo I, no próprio documento, em paisagem | mantém o memorial autossuficiente para publicação |
| Não realizadas no exercício anterior | não há | item 6.4 | exigido pelo art. 7º da Portaria nº 04/2024 |

## 4. Estrutura fixa

```
Capa
Página de créditos (elaborado / coordenado / revisado / aprovado)
1.  APRESENTAÇÃO
    1.1. Abrangência e exclusões
2.  METODOLOGIA DAS ESTIMATIVAS
3.  CLASSIFICAÇÃO (CATEGORIA ECONÔMICA)
4.  UNIDADES REQUISITANTES E COMPETÊNCIAS
5.  CONTRATAÇÕES PLANEJADAS
6.  NOTAS EXPLICATIVAS
    6.1. Estimativas que se afastam da metodologia geral
    6.2. Despesas apartadas da base de cálculo (atipicidade)
    6.3. Demandas apresentadas e não acolhidas
    6.4. Contratações planejadas no exercício anterior e não realizadas
7.  EXECUÇÃO, MONITORAMENTO E DIVULGAÇÃO
Assinaturas
ANEXO I — RELAÇÃO ANALÍTICA DAS DEMANDAS (seção em paisagem)
```

Nenhum item pode ser suprimido. Não havendo ocorrência em 6.1 a 6.4, registre
expressamente "não houve" — a supressão do item 6.4 é a omissão mais frequente no
encerramento do ciclo.

## 5. Campos variáveis

| Campo | Conteúdo esperado |
|---|---|
| `{{EXERCICIO_PCA}}` | exercício a que o Plano se refere (ex.: 2027) |
| `{{EXERCICIO_BASE}}` | exercício em curso, de onde vêm os empenhos (ex.: 2026) |
| `{{EXERCICIO_M2}}` | exercício anterior ao base, de onde vem a despesa realizada (ex.: 2025) |
| `{{DATA_CORTE}}` | data de corte dos empenhos do exercício-base — **a mesma para todas as demandas** |
| `{{MES_ANO_ELABORACAO}}`, `{{DATA_ELABORACAO}}`, `{{DATA_ASSINATURA}}` | datas do ciclo |
| `{{BIENIO}}` | biênio da Mesa em exercício na data da assinatura |
| `{{PRESIDENTE}}`, `{{SECRETARIO}}`, `{{CONTADOR}}`, `{{CRC_CONTADOR}}`, `{{CONTROLADOR_INTERNO}}`, `{{RESPONSAVEL_DFD}}` | responsáveis |
| `{{INDICE_NOME}}`, `{{INDICE_REFERENCIA}}`, `{{INDICE_PERCENTUAL}}`, `{{INDICE_FONTE}}` | índice de atualização, sua referência, o percentual e a fonte de apuração |
| `{{VALOR_CUSTEIO}}`, `{{VALOR_INVESTIMENTO}}`, `{{VALOR_TOTAL_PCA}}` | totais por categoria econômica |
| `{{PERCENTUAL_CUSTEIO}}`, `{{PERCENTUAL_INVESTIMENTO}}` | participação de cada categoria |
| `{{QUANTIDADE_DEMANDAS}}` | número de demandas do Plano |
| `{{TOTAL_DESPESA_ORCADA}}` | total do QDD do exercício-base |
| `{{DATA_PUBLICACAO_SITIO}}`, `{{ENDERECO_SITIO}}` | divulgação no sítio oficial |
| `{{DATA_PUBLICACAO_PNCP}}`, `{{IDENTIFICACAO_PNCP}}` | divulgação no PNCP |
| `{{DATA_REMESSA_EXECUTIVO}}`, `{{PROTOCOLO_REMESSA}}` | remessa ao Poder Executivo |

Os quadros usam `[PREENCHER: ...]` nas linhas-modelo, que devem ser replicadas por
demanda e substituídas pelos dados reais.

## 6. Conteúdo obrigatório por norma

Item 5 e Anexo I, em conjunto, cobrem o **§ 2º do art. 2º da Portaria nº 04/2024**:
descrição sucinta do objeto; tipo de material, serviço ou obra; mês previsto; quantitativo
estimado; possibilidade de renovação contratual; subelemento de despesa.

O Anexo I acrescenta os elementos do **art. 3º**: requisitante, justificativa, estimativa
sumária, data provável, vinculação/dependência e grau de prioridade.

O item 1.1 registra as exclusões do **§ 3º do art. 2º** (art. 75, VI, VII e VIII, e art.
95, § 2º, da Lei nº 14.133/2021, até 10% do valor previsto).

## 7. Regras de preenchimento que a minuta impõe

1. **A base de cálculo é a despesa realizada e empenhada** — nunca a estimativa do PCA
   anterior. Índice sobre índice descola o Plano da execução e inutiliza o controle de
   fracionamento.
2. **Empenho parcial é anualizado** (valor ÷ meses × 12), com memória de cálculo no Anexo
   I. Empenho global anual entra sem anualização, e isso é declarado.
3. **O rótulo de ano de cada coluna é campo variável.** Confira, antes de publicar, se
   cada coluna corresponde ao exercício que o cabeçalho anuncia.
4. **O percentual aplicado nas linhas do Anexo I tem de ser o índice declarado no item
   2.** Divergência entre os dois é erro material que compromete todo o Plano.
5. **A data de corte dos empenhos é única** para todas as demandas.
6. **O número da demanda é o mesmo** no item 5, no Anexo I e no registro do sistema. Não
   renumere ao reordenar.
7. **O quadro de divulgação (item 7) só é preenchido depois da divulgação efetiva.** Data
   prevista não se registra como realizada.
8. **O bloco de assinaturas reproduz a página de créditos.** Confira ambos contra a
   portaria de posse vigente na data da assinatura.

## 8. Fluxo de uso

1. As unidades requisitantes preenchem os DFD (minuta `DFD_PARA_PCA`).
2. O contador consolida os DFD, agrega demandas de mesma natureza e apura a base de
   cálculo a partir do realizado e do empenhado.
3. Aplica-se o índice; as atipicidades são apartadas e registradas em 6.2.
4. Preenchem-se o item 5 e o Anexo I, demanda a demanda.
5. Fecham-se os totais (item 3) e as notas explicativas (item 6).
6. A Controladoria Interna revisa; a Presidência aprova ou redimensiona.
7. Divulgação no sítio oficial e no PNCP; remessa ao Poder Executivo; preenchimento do
   quadro do item 7.

Prazo: art. 2º da Portaria nº 04/2024, observado o art. 8º, que admite alteração de prazos
por ato do Diretor Geral para alinhamento com o planejamento orçamentário.

## 9. Riscos e cautelas

- **A previsão no PCA não instrui contratação alguma.** Não dispensa ETP, TR nem pesquisa
  de preços (art. 23 da Lei nº 14.133/2021 e Portaria nº 03/2024).
- A estimativa sumária do PCA **não é** pesquisa de preços (art. 3º, § 1º, da Portaria
  nº 04/2024).
- Descrição genérica de objeto prejudica a consolidação e o controle de fracionamento.
  Objeto genérico do tipo "outros serviços de terceiros" deve vir acompanhado de
  justificativa do que efetivamente se pretende contratar.
- O Plano é **alterável** durante o exercício, mediante justificativa aprovada pela
  Presidência (art. 6º). Contratação fora do previsto exige o registro do art. 6º, não o
  silêncio.
- As notas de orientação em **vermelho** são instruções da minuta e devem ser **removidas**
  antes da publicação — não são conteúdo do Plano.
- Os PCA anteriores desta Casa citam o **Acórdão TCU nº 1524/2019**. Essa citação **não
  está conferida em ficha de jurisprudência da base**; antes de reutilizá-la, confira o
  acórdão na origem ou suprima a referência.

## 10. Formatação

Perfil documental `pca` em
[`09_padronizacao_documental/PERFIS_DOCUMENTAIS.json`](../../09_padronizacao_documental/PERFIS_DOCUMENTAIS.json).
Auditoria:

```bash
python scripts/docx_cmi/auditar_docx.py --entrada 05_minutas/PCA/PCA_MINUTA_MAE.docx --perfil pca --minuta-mae 05_minutas/TR/TR_MINUTA_MAE.docx
```

Divergências conhecidas e aceitas: **E-10** em
[`EXCECOES_AUTORIZADAS.md`](../../09_padronizacao_documental/EXCECOES_AUTORIZADAS.md).
Não use `--normalizar-cores` nesta minuta: o vermelho é marcação, não defeito.

## 11. Fontes prioritárias

1. Lei nº 14.133/2021 — art. 12, VII e § 1º; art. 18 e § 1º, II; art. 23; art. 75, VI a
   VIII; art. 95, § 2º; art. 176.
2. Portaria nº 04/2024 da Câmara Municipal de Itanhandu (DOM-MG de 03/04/2024, ed. 3738)
   — arts. 1º a 10.
3. Portaria nº 03/2024 da Câmara Municipal de Itanhandu (pesquisa de preços).
4. Decreto Federal nº 10.947/2022 — aplicação **subsidiária** apenas nos casos omissos,
   na forma do parágrafo único do art. 9º da Portaria nº 04/2024.
5. PCA 2026 do TCE-MG (`12_pca/modelo/`) — referência de forma.
