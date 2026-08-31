---
tipo: diagnostico
tema: fontes de dados — contratações diretas no TCE-MG
fonte: reconhecimento técnico (Fase 1) + coleta estruturada (Fase 2) — Charles
vigencia: vigente
atualizado_em: 2026-08-09
tags: [fase-1, fase-2, diagnostico, tce-mg, portal-transparencia, comprasmg, tclegis, captcha]
---

# Diagnóstico de fontes — contratações diretas no TCE-MG

## 1. Objetivo desta fase

Reconhecer, tecnicamente, onde e como os dados de contratação direta do TCE-MG
(dispensas, inexigibilidades e SICOM) podem ser obtidos de forma **documentada,
rastreável e legal**, antes de qualquer coleta automatizada em massa (Fases 2–4).

Este documento registra o que foi **verificado** (com evidência em arquivo),
o que é **inferência** e o que exige **ação humana** — nunca mistura os três.

## 2. Evidências geradas nesta fase (links)

| O que | Onde |
|---|---|
| 32 atos normativos no índice (PDF + texto; 61 PDFs + 61 .md no total) | `01_ATOS_NORMATIVOS/` + `indice_normas.json\|csv` |
| Proveniência + SHA-256 de cada PDF | `00_CONTROLE/hashes/norma_*.json` (33 arquivos) |
| Triagem dos 49 candidatos (classificação por ementa extraída) | `00_CONTROLE/coleta/candidatos_triagem.json` |
| Decisão de triagem: 14 coletar / 35 descartar (com motivo) | `00_CONTROLE/coleta/decisao_triagem.md`, `descarte.json` |
| Manifesto de todas as capturas brutas (107 arquivos, com SHA-256) | `00_CONTROLE/registros_web/MANIFESTO_EVIDENCIAS.json` |
| Revalidação interativa do Portal da Transparência (amostras 2025/2026) | `00_CONTROLE/registros_web/validacao_interativa/portal_transparencia_amostra_2025_2026.json` |
| Exportação completa — SIAD + Lei 14.133/21 + Compra direta (210 registros) | `00_CONTROLE/registros_web/validacao_interativa/portal_transparencia_compra_direta_siad_lei_14133_20260809.xlsx` |
| Catálogo normalizado dos 210 candidatos | `03_INDICES/processos_candidatos.csv` e `processos_candidatos.json` |
| HTML cru: página de busca TCLEGIS | `00_CONTROLE/registros_web/tclegis_index_TCE.html` |
| HTML cru: resultado de busca TCLEGIS | `00_CONTROLE/registros_web/tclegis_resultado_*.html` |
| HTML cru: Detalhe dos atos | `00_CONTROLE/registros_web/tclegis_detalhe_*.html` |
| HTML cru: grid Compras MG (vazio p/ script) | `00_CONTROLE/registros_web/comprasmg_busca_1020_resultado.html` |
| HTML cru: transparência (SPA) em navegador real | `00_CONTROLE/registros_web/tce_transparencia_licitacoes_playwright.html` |
| Bundle JS analisado (API `arabiasaudita.../p-portal-transparencia/`) | `00_CONTROLE/registros_web/tce_transparencia_main_js_bundle.js` + `chunks_js/` |

> Na fase 1, os arquivos crus residiam como `_tmp_*.html` na raiz de
> `00_CONTROLE/`; em 2026-08-09 foram **canonizados** (nomes + SHA-256 no
> manifesto) para `registros_web/`. Os `_tmp_*` originais foram preservados
> por cópia; em 2026-08-09 (tarefa 8) foram **arquivados** — os `_tmp_*` que
> já tinham equivalente canônico idêntico (mesmo SHA-256, conferido) foram movidos
> para `00_CONTROLE/_arquivo_tmp_fase1/` (não apagados; sem histórico git, apagar
> seria irreversível). O manifesto passou a cobrir 100% de `registros_web/`
> (`scripts/09_reconciliar_manifesto.py`).

## 3. Fonte A — Portal da Transparência TCE-MG

- URL: <https://transparencia.tce.mg.gov.br/public/licitacoes>
- Natureza: SPA Angular (chunks carregados sob demanda); dados vêm de API.
- API descoberta no JS do bundle:
  `https://arabiasaudita.tce.mg.gov.br:8443/TCEMG-proxy-web/publico/apimoci/p-portal-transparencia/`
- Endpoint de licitações:
  `api/CompraLicitacao/GetAllCompraLicitacao/{fonte}/{lei}` — fontes: `SIAD` e `Admin`; lei: `14.133`.
- **Comportamento observado inicialmente:** F5 BIG-IP + fluxo
  `captcha_simples.jsf`; scripts simples receberam **HTTP 401** e a primeira
  tentativa com Playwright/Edge foi redirecionada ao desafio.
- **Revalidação em 2026-08-09:** a interface pública abriu normalmente em
  navegador interativo, sem CAPTCHA, e permitiu filtrar, ler e exportar resultados
  reais. Com os filtros **SIAD + Lei 14.133/21 + Compra direta + todos os anos +
  TODAS as situações**, a interface retornou e exportou **210 registros**: 6 de
  2023, 58 de 2024, 67 de 2025 e 79 de 2026. A requisição direta à API, fora da
  sessão do navegador, continuou retornando **HTTP 401**.
- A exportação XLSX foi validada como `A1:J211` (1 cabeçalho + 210 registros) e
  preservada com SHA-256. O CSV produzido pela própria interface é defeituoso:
  não escapa corretamente vírgulas decimais, vírgulas e quebras de linha dos
  objetos; foi preservado apenas como original, não como fonte de ingestão.
- Alguns pares número/ano se repetem. Como a exportação não traz a unidade de
  compra, os candidatos repetidos receberam identificador técnico com sufixo de
  hash, sem afirmar que sejam duplicatas administrativas.
- **Documentos de processo:** na amostra do processo 310/2025, a interface informou
  não possuir documentos da fase interna/externa e orientou consultar os anexos no
  Portal de Compras MG com órgão 1020, número e ano.
- O próprio portal informa que o TCE utiliza **SIAD/MG** e que as informações são as do
  **Portal de Compras MG** (sem acesso direto ao SIAD).

**Classificação atual:** `ACESSIVEL_EM_NAVEGADOR`; API direta
`INACESSIVEL_POR_SCRIPT` (HTTP 401). Nenhum CAPTCHA, cookie ou controle de acesso
foi contornado.

**Status:** fonte operacional para catálogo por exportação da interface. A automação
HTTP direta da API permanece pendente de endpoint público documentado.

## 4. Fonte B — Portal de Compras MG (órgão 1020)

- URL de consulta:
  `https://www1.compras.mg.gov.br/processocompra/processo/consultaProcessoCompra.html?orgaoEntidade=1020&metodo=pesquisar&estaPesquisando=true`
- Órgão **1020 = TRIBUNAL DE CONTAS DO ESTADO DE MINAS GERAIS** (evidência: label
  retornado pelo próprio formulário).
- Sistema legado Struts/Dojo (Java); a grade de resultados é carregada por JS.
- Filtros disponíveis no formulário: publicação, N° anual, modalidade, fornecedor,
  situação, componente/unidade de compras.
- **Portão de acesso:** **hCaptcha** (sitekey `e518a43a-5916-4627-b07b-c6e0c2713f24`)
  na busca de resultados. Sem resolução humana, orquestradores recebem o formulário
  sem a grade; o desafio não foi contornado.
- **Validação humana assistida em 2026-08-09:** após a resolução humana do hCaptcha,
  a consulta do órgão 1020 funcionou. A hierarquia observada para compra direta foi
  `procedimento1=462` (Bens e serviços — Lei 14.133/21), `procedimento2=513`
  (Dispensa de Licitação — Por valor), `procedimento3=514` (Compra direta) e
  `especializacao=515` (administração direta, fundação ou autarquia). A grade
  retornou **201 itens**. Essa contagem difere dos 210 registros exportados pelo
  Portal da Transparência e deve ser reconciliada por número/ano na Fase 3.
- O front-end expõe os padrões de arquivo
  `visualizacaoArquivosProcesso.html?id=<id_interno>` e
  `visualizacaoArquivosProcessoOrdenados.html?id=<id_interno>`; o `id_interno`
  aparece nos rádios da grade após a consulta.
- **Piloto 287/2026:** quatro documentos públicos únicos foram baixados e
  organizados (relatório de detalhes, Termo de Referência, mapa comparativo de
  preços e autorização), com 19 páginas renderizadas e extraídas. Duas cópias
  adicionais da autorização tinham SHA-256 idêntico e foram registradas como
  duplicatas, sem exclusão dos originais.

**Classificação:** `ACESSIVEL_EM_SESSAO_HUMANA` (hCaptcha). Documentado; não contornado.

**Status:** consulta e anexos acessíveis depois de ação humana; automação autônoma
continua bloqueada pelo hCaptcha. A coleta deve preservar a sessão visível e registrar
o caminho percorrido.

## 5. Fonte C — TCLEGIS (fonte normativa, sem captcha)

- URL: <https://tclegis.tce.mg.gov.br>
- Natureza: ASP.NET MVC, token antiforgery por formulário; **funciona sem captcha**.
- Fluxo verificado (scripts):
  1. `GET /Home/Index/TCE` → página de busca + `__RequestVerificationToken`;
  2. `POST /Home/RetornoBusca` com campos do formulário e o token;
  3. Resultado: `<ul class="LinhasRetornoBusca">` → `<li><a href="/Home/Detalhe/{id}">`;
  4. `GET /Home/Detalhe/{id}` → metadata (título, ementa, fonte, **VIDE** = relações,
     indexação) + botões de download;
  5. Download: `GET /Home/DownloadPDFCompatado|Completo|Original/{id}`.
- Busca textual: campo `<textarea name="termos">` (descoberto em 2026-08-09;
  o `Assuntos` testado antes **não existe** e buscava tudo).
- Operadores de filtro: `tipoNorma`, `tipoOrigem`, `indRevogada`, `qtdPorPagina`,
  checkboxes `testEmenta|testIndexacao|testObservacao|testIntegra|testVide|testFonte`.
- Limite por busca: **1.000 registros** ("A quantidade de registros foi limitada a 1000");

**Classificação:** `ACESSIVEL_POR_SCRIPT` — fonte primária dos atos normativos
do TCE-MG. Limitação conhecida: para alguns atos, `DownloadPDFCompatado`/`Completo`
retornam HTTP 500 (servidor); **ORIGINAL sempre funciona**. PDFs digitalizados
dependem de OCR (ver `99_ORIGINAIS/`).

**Status:** `OPERACIONAL`.

## 6. Fontes complementares (referência normativa)

- Instrução Normativa TCE-MG **2/2023** (alterada pela IN **1/2024**): obriga a
  remessa de informações e documentos de procedimentos licitatórios pelo **Módulo
  Edital e Licitação do SICOM** — a porta técnica da fiscalização de licitações.
- Portal dos atos normativos do TCE-MG: <https://www.tce.mg.gov.br/Noticia/Detalhe/30>.
- SICOM (sistemas do TCE-MG): <https://www.tce.mg.gov.br/sicom> (para conferência).

## 7. Atos normativos identificados (núcleo curado)

18 atos coletados com **evidência** (PDF original baixado + SHA-256 no
`00_CONTROLE/hashes/`). Relações de alteração verificadas no campo VIDE do TCLEGIS:

| Ato | Matriz | Ato(s) que o(s) alteram(se) |
|---|---|---|
| Portaria 83/2023 — transição art. 191 | ✓ | — |
| Portaria 1/2024 — PCA | ✓ | 14/2024 · 26/2025 · **22/2026** |
| Portaria 2/2024 — dispensa art. 75 I e II | ✓ | **141/2025** |
| Portaria 8/2024 — agente/equipe/comissão/gestor/fiscal | ✓ | **60/2025** |
| Portaria 9/2024 — ETP | ✓ | **20/2025** |
| Portaria 43/2024 — registro de preços | ✓ | — |
| Ordem de Serviço 4/2024 — dispensa de análise jurídica | ✓ | — |
| Resolução 06/2024 — bens comuns/luxo | ✓ | — |
| Resolução 07/2024 — sanções | ✓ | — |
| IN 2/2023 — SICOM/licitações | ✓ | **IN 1/2024** |
| Portaria 85/2025 — comissão análise qualif. econ.-fin. | ✓ | — |

> **Importante para o uso:** o texto **consolidado** de cada ato alterado está no
> PDF **COMPILADO** da portaria **alteradora** mais recente (ex.: dispensa art. 75 →
> ler a **141/2025**), quando disponível; o ORIGINAL é o ato publicado. A cadeia de
> alterações está nos `hashes/norma_*.json` e no `01_ATOS_NORMATIVOS/indice_normas.*`.

### 7.1 Coleta estruturada ampliada (Fase 2 — script 04)

Em 2026-08-09/10 a coleta deixou de se limitar ao núcleo curado: o `04_coletar_atos_tclegis.py`
fez **busca textual documentada** (6 termos da agenda de contratação direta →
`00_CONTROLE/busca/resultados_busca.json`), **triagem de 49 candidatos** por leitura da ementa
extraída da página Detalhe (HTML cru em `registros_web/tclegis_detalhe/`) e **coleta dos 14
atos** classificados relevante/contexto (PDF COMPILADO → COMPLETO → ORIGINAL + .md, SHA-256
por variante). Resultado:

- **32 atos no índice** (`indice_normas.json|csv`): 18 do núcleo curado (preservados, com
  numeração curatorial tipo `83/PRES./2023`) + 14 da Fase 2 (com `coletado_em`; reconstruídos
  a cada `--indices`, caminhos de arquivo relativos ao repositório).
- **35 descartes documentados** em `00_CONTROLE/coleta/decisao_triagem.md`/`descarte.json`
  (irrelevantes — ex.: fiscalização contábil, atos de instauração de inquérito, sanções — e
  superseded — estrutura organizacional coberta pela cadeia 1142590/1142694/1142792). Nenhum
  ato irrelevante entrou no índice.
- Convenção de pastas aplicada: `vigentes/` (inclui situação `alterada`), `revogados/`,
  `situacao_nao_confirmada/` — **61 PDFs + 61 .md** ao todo em `01_ATOS_NORMATIVOS/`.

Interessante para instrução de contratação direta, entre os 14 da Fase 2: **Resolução 8/2003**
(pregão), **Portaria 114/2010** + alteradora **15/2014** (competência para aprovação de projeto
básico/TR — fase preparatória), **Orientação 3/2013** (coerência entre objeto e funções no TR),
**Ordem de Serviço 2/1997** (atualização de valores de contratos/convênios), **IN 6/2011** (PPP),
**Portarias 3/2016** (programação anual de contratações — antecedente do PCA) e **59/2023**/**75/2022**
(GTs de transição para a Lei 14.133/2021), além do **Regimento Interno 2023**.

## 8. Riscos, regras e decisões

- **IMPORTANTE — anti-alucinação:** nenhum número, ementa ou relação acima é inventado;
  todos foram listados a partir das **respostas reais do TCLEGIS**. Se a base ficar
  sem uma informação, escreve-se `não identificado / não localizado na fonte pesquisada`.
- Cada documento baixado tem **SHA-256** e registro de proveniência (data, URL, status).
- Nenhum original é alterado: permanece em `99_ORIGINAIS/` (para quando a cópia de
  trabalho precisar ser normalizada/OCR).
- Captcha/Autenticação: **não** contornados (regra do projeto). Registra-se a
  necessidade de ação humana e o caminho.
- Acessos em série com pausa de ≥0,4 s; UA identificável e educado.
- Limitações de servidor não são "falha do coletor": são registradas como tal.
