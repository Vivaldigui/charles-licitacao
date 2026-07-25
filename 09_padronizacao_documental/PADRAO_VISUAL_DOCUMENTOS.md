---
tipo: norma_interna
hierarquia: padrao_visual
tema: padronizacao e formatacao documental
fonte: analise das minutas-mae da Camara Municipal de Itanhandu + referencias visuais externas
orgao: camara municipal de itanhandu
versao: 1.0
vigencia: vigente
atualizado_em: 2026-07-25
tags: [padronizacao, formatacao, docx, identidade-visual, minutas, estilos]
---

# Padrão Visual dos Documentos — Câmara Municipal de Itanhandu

Fonte de verdade **narrativa** do padrão visual. A fonte de verdade **técnica**, lida
pelos scripts, é [`PERFIS_DOCUMENTAIS.json`](PERFIS_DOCUMENTAIS.json). Divergiu? Vale o
JSON, e este arquivo deve ser corrigido.

> **Regra de ouro:** a padronização visual **não autoriza** alteração de conteúdo.
> Ver [`REGRAS_DE_FORMATACAO.md`](REGRAS_DE_FORMATACAO.md).

---

## 1. Como este padrão foi definido

Não foi escolhido por gosto. Foi **extraído das 22 minutas-mãe** de `05_minutas/` e
confrontado com referências oficiais externas (ver
[`REFERENCIAS_VISUAIS.md`](REFERENCIAS_VISUAIS.md)).

Levantamento realizado em 25/07/2026 sobre os 22 DOCX da biblioteca:

| Característica | O que as minutas mostram |
|---|---|
| Estilo `Normal` | **Calibri 12 pt** em 17 das 22 minutas |
| Papel | A4 (21,0 × 29,7 cm) em 22 de 22 |
| Margens dominantes | **Sup. 4,23 / Inf. 2,50 / Esq. 3,00 / Dir. 2,00 cm** (11 de 22) |
| Margem superior | 4,23 cm em 18 de 22 — acomoda o brasão do cabeçalho |
| Alinhamento do corpo | Justificado (estilo `Normal` do TR: JUSTIFY) |
| Entrelinhas | 1,5 é o valor explícito mais frequente (384 parágrafos), seguido de 1,15 (195) |
| Cabeçalho/rodapé | **Imagem** (3 desenhos no cabeçalho, 2 no rodapé) em 19 de 22 |
| Campo de paginação | **Ausente** em todas — o rodapé é imagem institucional |
| Fonte nos *runs* | Majoritariamente herdada do estilo (bom sinal) |

Esse levantamento também expôs a **inconsistência que o módulo existe para resolver**:
espaçamento antes de parágrafo com 50+ valores distintos (0,05 pt, 2,85 pt, 7,85 pt…),
espaçamento entre linhas gravado em unidades absolutas por conversão de formato,
434 parágrafos vazios usados como espaçador (26% do total) e fontes divergentes
(Times New Roman, Bookman Old Style, Arial) em minutas isoladas.

---

## 2. Princípios

O padrão é **formal, institucional, limpo e sóbrio**, legível em tela e em papel, e
apropriado para conversão em PDF. Fica **proibido**: emoji, ícone decorativo, título
gigante, caixa colorida, cor sem função, aparência publicitária e qualquer coisa com
cara de resposta de chat.

---

## 3. Tipografia

Fonte institucional: **Calibri**. Aceita-se **Carlito** como equivalente métrico
(é a substituta do LibreOffice — o documento não muda de aparência).

| Elemento | Tamanho | Estilo |
|---|---|---|
| Título do documento | 14 pt | negrito, centralizado |
| Título de 1º nível | 12 pt | negrito, à esquerda |
| Título de 2º nível | 12 pt | negrito, à esquerda |
| Título de 3º nível | 12 pt | negrito + itálico, à esquerda |
| Corpo | 12 pt | justificado |
| Citação legal recuada | 11 pt | justificado, recuo 4 cm |
| Tabela | 11 pt | conforme a natureza da coluna |
| Cabeçalho de tabela | 11 pt | negrito, centralizado |
| Nota / fonte de tabela | 10 pt | justificado |
| Assinatura | 12 pt | centralizado |
| Cabeçalho e rodapé | **preservados como estão** | é imagem institucional |

**Sobre a fonte de segurança.** O escopo do módulo previa Arial 11 como padrão de
fallback. Ele **não se aplica** aqui: as minutas-mãe têm padrão institucional
consolidado (Calibri 12) e, pela regra do próprio escopo, *o padrão da minuta
prevalece*. Arial 11 permanece como fallback apenas para documento sem minuta de
referência e sem estilo `Normal` utilizável.

**Exceção por perfil.** O `DFD para PCA` usa Times New Roman e cabeçalho/rodapé em
texto. O perfil declara `fonte_principal` própria para não descaracterizar a minuta.
Ver [`EXCECOES_AUTORIZADAS.md`](EXCECOES_AUTORIZADAS.md).

---

## 4. Cores

| Uso | Cor |
|---|---|
| Corpo do texto | Preto `#000000` |
| Títulos | Preto `#000000` |
| Sombreado de cabeçalho de tabela | Cinza-claro `#D9D9D9` |
| Elementos auxiliares | Cinza-escuro `#595959` |
| Campo pendente (estilo `CMI Campo Pendente`) | `#C00000` |

Não foi possível extrair com segurança uma cor institucional do timbre: o brasão é
**imagem** no cabeçalho, e amostrar pixel de imagem para inventar uma "cor da Câmara"
seria adivinhação. Por isso o padrão é **monocromático**, como prevê a regra de
segurança do escopo. O módulo **não colore documento para deixá-lo bonito**.

**Vermelho é dado, não defeito.** Nas minutas de contrato o vermelho (`FF0000`,
`CC0000`) marca campo a preencher, e no ETP marca nota de orientação. O módulo
**reporta** esses trechos como pendência e **nunca** os recolore em modo automático.
A conversão só ocorre com `--normalizar-cores`, sob responsabilidade de quem executa.

---

## 5. Alinhamento, espaçamento e recuo

- Título do documento: centralizado. Títulos de seção: à esquerda.
- Corpo: justificado, entrelinhas **1,5**, **6 pt** depois do parágrafo, 0 pt antes.
- Títulos: entrelinhas simples; 12/10/8 pt antes (níveis 1/2/3) e 6 pt depois.
- Assinatura: centralizada, entrelinhas simples, bloco mantido junto.
- **Recuo de primeira linha: preservado como está na minuta** (`null` no JSON).
  As minutas não usam recuo de forma consistente, e impor 2,5 cm mudaria a aparência
  de toda a biblioteca sem decisão humana.
- Recuo nunca em: títulos, listas, tabelas, campos de identificação, cláusulas
  numeradas, assinaturas e itens curtos.
- Espaçamento vem de **estilo**, nunca de linha em branco ou tabulação manual.

### Normalização de alinhamento — o limite deliberado
O corpo só é justificado quando o parágrafo já está à esquerda ou sem alinhamento **e**
tem 80+ caracteres. Parágrafo **centralizado é preservado**: centralização em documento
administrativo costuma ser intencional (epígrafe, local e data, bloco de assinatura), e
achatá-la destruiria o layout.

---

## 6. Página

| Item | Valor de referência |
|---|---|
| Papel | A4, retrato |
| Margem superior | 4,23 cm |
| Margem inferior | 2,50 cm |
| Margem esquerda | 3,00 cm |
| Margem direita | 2,00 cm |

**As margens NÃO são corrigidas automaticamente** (`ajustar_margens: false`). A margem
superior de 4,23 cm existe para acomodar o brasão; alterá-la deslocaria a mancha
gráfica em relação ao timbre. Divergência é **reportada** na auditoria e decidida por
pessoa.

---

## 7. Estilos nomeados

O módulo prioriza **estilo nomeado** sobre formatação direta. Prefixo `CMI` = Câmara
Municipal de Itanhandu.

`CMI Título do Documento` · `CMI Identificacao` · `CMI Corpo` · `CMI Corpo sem Recuo` ·
`CMI Titulo 1` · `CMI Titulo 2` · `CMI Titulo 3` · `CMI Item Numerado 1/2/3` ·
`CMI Marcador` · `CMI Tabela` · `CMI Cabecalho de Tabela` · `CMI Nota` ·
`CMI Assinatura` · `CMI Campo Pendente` · `CMI Citacao Legal`

Cada perfil documental declara quais desses estilos podem aparecer.

**Quando o estilo é trocado.** Só em parágrafo com estilo genérico (`Normal`,
`Body Text`, `Standard`, `Text body`) ou com estilo de título mapeável
(`Heading 1-3`, `Nivel 01/2/3`). Parágrafo com **numeração automática** (`w:numPr`)
mantém o estilo original e recebe apenas normalização de fonte, espaçamento e
paginação — trocar o estilo quebraria a lista numerada do Word.

**O que nunca é removido.** Negrito, itálico e sublinhado: têm função semântica.
E *runs* dentro de hyperlink não têm cor alterada.

---

## 8. Numeração

Hierarquia de referência, quando compatível com a minuta:

```text
1. TÍTULO PRINCIPAL
1.1. Subtítulo
1.1.1. Subitem
a) Alínea
I – Inciso
```

A hierarquia já existente na minuta oficial prevalece quando estiver correta.

**Nunca renumerado:** artigo de lei, inciso citado, número de processo, portaria,
decreto, valor, data, código CATMAT/CATSER/CNAE/CNPJ/CPF, e cláusula contratual
(o perfil `contrato` traz `renumeracao_automatica: false`).

A renumeração só é aplicada com `--corrigir-numeracao`, **e** apenas se todos os
problemas forem corrigíveis **e** nenhuma referência interna ("conforme o item 6",
"nos termos do subitem 4.2") ficar inconsistente.

---

## 9. Tabelas

Largura reescalada proporcionalmente até caber na área útil; linha de cabeçalho
repetida nas páginas seguintes (`tblHeader`); linhas impedidas de se partir entre
páginas (`cantSplit`); margens internas de 0,1 cm; alinhamento vertical centralizado;
sombreado `#D9D9D9` só no cabeçalho; fonte uniforme entre células.

Mesclagens são **preservadas** — o reescalonamento respeita `gridSpan`. Nenhuma
célula, linha ou coluna é removida, e a validação de conteúdo compara a grade textual
célula a célula.

Tabela muito larga: avaliar paisagem **apenas na seção da tabela**, nunca no documento
inteiro, e registrar no relatório.

---

## 10. Paginação

Títulos com "manter com o próximo" e "manter linhas juntas"; bloco de assinatura
mantido junto; controle de órfãs/viúvas religado onde tiver sido desligado; parágrafos
vazios consecutivos reduzidos a no máximo 1; quebras de página duplicadas removidas.

Quebras intencionais são preservadas. O módulo **não** insere quebra antes de cada
título.

---

## 11. Cabeçalho, rodapé e assinatura

Cabeçalho e rodapé são **partes protegidas**: nunca recriados, redimensionados,
reposicionados ou convertidos em texto. A verificação usa assinatura semântica
(textos + número de imagens + imagens referenciadas + dimensões), de modo que
reserialização inofensiva não gera alarme falso, mas brasão removido ou redimensionado
bloqueia a saída.

Assinaturas: espaçamento e alinhamento padronizados, bloco mantido na mesma página.
**Nunca** se inventa nome, cargo, autoridade, data, assinatura digital ou código de
verificação.

---

## 12. Campos pendentes

Padrão único: `[PREENCHER: descrição do que falta]`.

O módulo detecta `{{CAMPO}}`, `[PREENCHER...]`, `(definir...)`, `____`, blocos `OU`
não resolvidos, opções `( )` não marcadas e texto avermelhado. Documento com qualquer
pendência **não** pode ser declarado pronto para assinatura: o status vai para
`EXIGE CONFERÊNCIA HUMANA`.

---

## 13. Perfis por tipo de documento

Definidos em [`PERFIS_DOCUMENTAIS.json`](PERFIS_DOCUMENTAIS.json): `dfd`, `dfd_pca`,
`etp`, `tr`, `pesquisa_precos`, `justificativa`, `certidao`, `autorizacao`, `aviso`,
`ata_julgamento`, `homologacao`, `ratificacao`, `ordem_fornecimento`, `contrato`,
`termo_aditivo`, `recebimento`, `extrato`, `mapa_riscos`, `declaracao`, `generico`.

Cada perfil define estilos permitidos, níveis de numeração, capa, sumário, padrão de
tabelas, forma de assinatura, paginação, orientação, títulos e exceções.

Exemplos do porquê de perfis distintos: o **extrato** é curto, sem seções, sem sumário
e sem tabelas — fragmentá-lo em tópicos é erro; o **contrato** usa cláusulas por
extenso e proíbe renumeração automática; o **TR** admite seções, subseções, quadros de
itens e anexos.

**Sem minuta-mãe:** `termo_aditivo` e `mapa_riscos` não têm modelo em `05_minutas/`.
Os perfis servem para formatar documento existente; a **geração continua bloqueada**
até que a minuta seja criada e aprovada.
