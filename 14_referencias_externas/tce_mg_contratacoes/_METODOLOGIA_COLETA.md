---
tipo: checklist
hierarquia: operacional
tema: metodologia da coleta de contratações do TCE-MG
fonte: Portal da Transparência do TCE-MG
vigencia: vigente
atualizado_em: 2026-08-10
tags: [tce-mg, coleta, evidencia, metodologia, rastreabilidade]
---

# Metodologia da coleta — contratações do TCE-MG

Registro de **como** as contratações do Tribunal de Contas do Estado de Minas Gerais foram
localizadas, baixadas e transformadas em fichas. Serve para (a) auditar o que foi feito e
(b) repetir a coleta depois.

---

## 1. Fonte

| Campo | Conteúdo |
|---|---|
| Portal | https://transparencia.tce.mg.gov.br/public/licitacoes |
| Seção | Compras e Licitações |
| Coletado em | **10/08/2026** |
| Filtros aplicados | Fonte da Pesquisa: `SIAD` e `Admin TCEMG` · Lei: `Lei 14.133/21` · Tipo de Procedimento: `Dispensa de Licitação` e `Pregão` · Ano: todos · Situação: TODAS |

O portal oferece duas **fontes de pesquisa**, e elas não trazem a mesma coisa:

- **SIAD** — o Sistema Integrado de Administração de Materiais e Serviços de MG. Traz a
  contratação já executada (valor homologado, fornecedor, contrato) e, no botão
  **"DOC Interna/Externa"**, um PDF único com as peças do processo SEI que foram publicadas.
- **Admin TCEMG** — o cadastro do próprio Tribunal. Traz menos linhas, quase sempre "Em
  andamento", mas publica o **edital completo** como anexo em URL pública.

Para o que interessa à Câmara, as duas se complementam: o SIAD mostra **como o processo foi
instruído e julgado**; o Admin mostra **como o edital foi escrito**.

---

## 2. Caminho técnico (para repetir)

O portal é uma aplicação Angular que fala com um proxy autenticado por **captcha**. Não há API
aberta e não há login: o navegador resolve um captcha, recebe um JWT e o guarda em
`localStorage['tokenAuthorizationProxy']`, válido por cerca de **2 horas**.

1. Abrir o portal no navegador e resolver o captcha (é o próprio carregamento da página).
2. Copiar o valor de `localStorage['tokenAuthorizationProxy']` para um arquivo `token.txt`.
3. Rodar:

```bash
python scripts/tce_mg_licitacoes.py --token-file token.txt listar
```

```bash
python scripts/tce_mg_licitacoes.py --token-file token.txt baixar
```

```bash
python scripts/tce_mg_licitacoes.py extrair
```

```bash
python scripts/tce_mg_fichas.py
```

Endpoints usados (os mesmos que a página chama):

| Uso | Chamada |
|---|---|
| Lista | `GET …/api/CompraLicitacao/GetAllCompraLicitacao/{fonte}/{lei}` com cabeçalho `Pagination` |
| Tipos de procedimento | `GET …/api/CompraLicitacao/GetAllTipoProcedimento?fonte=&lei=` |
| DOC Interna/Externa | `GET …/api/Arquivo/Protocolo/{protocolo}?IdCategoria=28&IdTipoArquivo=30` |
| Anexos (edital etc.) | `urlRaiz` + `nomeAnexo` — URL pública, sem token |

O `protocolo` é montado como `MM(2) + AAAA(4) + NÚMERO(10) + SIGLA(3)`, com `MM = 00` e sigla
`DSP` (dispensa), `PRE` (pregão), `INX` (inexigibilidade), `ARP` (registro de preços) — a mesma
regra do front. `IdCategoria=28` e `IdTipoArquivo=30` vêm de `api/Indicador/Sigla/CODI` e
`api/Indicador/Sigla/ANX`.

Cabeçalho de autenticação: `AuthorizationProxy: token <jwt>` (o prefixo `token ` faz parte).

---

## 3. O que foi coletado

| Fonte | Modalidade | Linhas do portal | Contratações distintas | Anos |
|---|---|---|---|---|
| SIAD | Dispensa de Licitação | 16 | 16 | 2024–2026 |
| SIAD | Pregão | 64 | 40 | 2024–2026 |
| Admin TCEMG | Dispensa de Licitação | 2 | 2 | 2024 |
| Admin TCEMG | Pregão | 18 | 17 | 2024–2025 |
| **Total** | | **100** | **75** | |

A linha do SIAD é por **lote/fornecedor homologado**, não por processo — daí 64 linhas para 40
pregões. As fichas são por contratação.

**Arquivos baixados:** 83 PDFs, ~271 MB — 61 documentações internas/externas e 22 anexos
(editais, publicações e um recurso administrativo).

**Faltas conhecidas:** em **12** contratações o portal respondeu **HTTP 404** ao pedido da
DOC Interna/Externa, ou seja, o botão existe na tela mas não há arquivo associado. São elas,
entre outras, as dispensas SIAD 310/2025 (Serpro MultiCloud), 237/2025 (Consórcio CEMIG SIM),
114/2025 (concurso público CEBRASPE), 98/2025 (café) e 76/2024 (SLU), e os quatro pregões de
registro de preços do cadastro Admin. Nesses casos, a ficha registra a ausência — **não** se
supõe conteúdo.

---

## 4. Onde ficam os arquivos

| O quê | Onde | Versionado? |
|---|---|---|
| PDFs brutos | `_entrada/tce_mg_licitacoes/<fonte>/<modalidade>/<ano>-<nº>_<objeto>/` | **Não** (`.gitignore`) |
| Texto extraído | `…/texto_extraido/*.txt` | **Não** (`.gitignore`) |
| Manifesto da consulta | `_entrada/tce_mg_licitacoes/MANIFESTO.json` e `.csv` | Não |
| Evidência de download | `_entrada/tce_mg_licitacoes/EVIDENCIAS_DOWNLOAD.json` | Não |
| **Fichas Markdown** | `14_referencias_externas/tce_mg_contratacoes/` | **Sim** |

O bruto fica fora do versionamento pelo mesmo motivo já registrado no `.gitignore` para os
julgados: são documentos de terceiros, com nome de servidor, de representante de fornecedor e
dados de habilitação. O que a base cita é a ficha.

---

## 5. Limites desta coleta — leia antes de usar

- **Não há print de tela.** A coleta foi feita pelas mesmas chamadas que a página faz, em
  ambiente sem renderização de tela disponível. No lugar do print, ficou registrado, por
  arquivo: URL exata, data/hora de acesso, status HTTP, tamanho e **sha256**
  (`EVIDENCIAS_DOWNLOAD.json`). Quem precisar do print para juntar aos autos deve abrir o
  portal, aplicar os filtros da seção 1 e capturar a tela.
- **A DOC Interna/Externa não é o processo inteiro.** É o conjunto de peças que o TCE-MG
  escolheu publicar. Nas dispensas, tipicamente: Termo de Referência → Parecer jurídico →
  Termo Autorizativo/Ratificação → Publicação. O DFD, o ETP, a pesquisa de preços, a proposta
  e os documentos de habilitação em geral **só aparecem citados** no relatório do parecer.
- **As fichas são geradas mecanicamente.** Peças, fundamento legal e lista de documentos
  instrutores saem de expressão regular sobre o texto do PDF. Campo marcado
  `(extraído automaticamente)` **precisa ser conferido no PDF** antes de virar citação.
- **PDF digitalizado não é lido.** Onde a extração não encontra texto, a ficha registra a
  ausência; não há OCR nesta base.
- **Nada aqui é norma de Itanhandu.** Ver a advertência em
  [`../README.md`](../README.md).
