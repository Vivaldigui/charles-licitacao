---
tipo: referencia
tema: glossário operacional das fontes de dados
fonte: reconhecimento técnico (Fase 1) — Charles
vigencia: vigente
atualizado_em: 2026-08-09
tags: [fontes, urls, parametros, tclegis, transparencia, comprasmg]
---

# Fontes — glossário operacional

Como **uso** cada fonte (URLs concretas, parâmetros descobertos e estado de
acesso). Detalhamento e evidências: `00_CONTROLE/diagnostico_fontes.md`.

## TCLEGIS — atos normativos (operacional, sem captcha)

- Base: `https://tclegis.tce.mg.gov.br`
- Página de busca (TCE): `GET /Home/Index/TCE` — devolve o form + token
  `__RequestVerificationToken`.
- Busca textual: `POST /Home/RetornoBusca` — o campo de texto é
  `<textarea name="termos">` (o campo "Assuntos" não existe no form).
  - Parâmetros: `tipoConsulta`, `numNorma`, `numAno`, `dataInicio`, `dataFim`,
    `tipoNorma`, `tipoOrigem`, `indRevogada`, `qtdPorPagina`, `orderby`, `page`,
    `termos`, checkboxes `testEmenta|testIndexacao|testObservacao|testIntegra|
    testVide|testFonte`.
  - Resultado: `<ul class="LinhasRetornoBusca">` → `<li><a href="/Home/Detalhe/{id}">`.
  - Limite: 1.000 registros por busca ("A quantidade de registros foi limitada a 1000").
- Detalhe: `GET /Home/Detalhe/{id}` — metadados (título, ementa, fonte, **VIDE**,
  indexação) + caminhos de download.
- Download (3 variantes):
  - `GET /Home/DownloadPDFCompilado/{id}` — **texto consolidado** (prioridade).
    Para muitos atos novos (portarias alteradoras) retorna **HTTP 500** do servidor.
  - `GET /Home/DownloadPDFCompleto/{id}` — idem, não consolida.
  - `GET /Home/DownloadPDFOriginal/{id}` — **PDF original**; sempre funciona.
- Regra de leitura: o texto consolidado de um ato alterado está no PDF **Compilado
  da última portaria alteradora** (não no original). A cadeia hoje está em
  `01_ATOS_NORMATIVOS/indice_normas.*` e `00_CONTROLE/hashes/norma_*.json`.

## Portal da Transparência TCE-MG — processos licitatórios (`ACESSIVEL_EM_NAVEGADOR`)

- Base: `https://transparencia.tce.mg.gov.br/public/licitacoes`
- Natureza: SPA Angular; dados via API:
  `https://arabiasaudita.tce.mg.gov.br:8443/TCEMG-proxy-web/publico/apimoci/p-portal-transparencia/api/CompraLicitacao/GetAllCompraLicitacao/{fonte}/{lei}`
  - `{fonte}`: `SIAD` | `Admin` · `{lei}`: `14.133`.
- Revalidação em 2026-08-09: a interface abriu sem CAPTCHA e exportou **210**
  registros com os filtros `SIAD`, `Lei 14.133/21`, `Compra direta`, todos os anos
  e todas as situações. Distribuição: 2023 = 6; 2024 = 58; 2025 = 67; 2026 = 79.
- Preferir o XLSX oficial. O CSV oficial não escapa corretamente vírgulas decimais,
  vírgulas e quebras de linha e foi preservado somente para auditoria.
- A API direta fora da sessão continuou respondendo HTTP 401. Uso atual: catálogo
  e conferência pela interface pública; não reutilizar cookies nem tentar contornar
  o HTTP 401.

## Portal de Compras MG — processos do órgão 1020 (`ACESSIVEL_EM_SESSAO_HUMANA`)

- Consulta: `https://www1.compras.mg.gov.br/processocompra/processo/consultaProcessoCompra.html?orgaoEntidade=1020&metodo=pesquisar&estaPesquisando=true`
- Órgão **1020 = TRIBUNAL DE CONTAS DO ESTADO DE MINAS GERAIS** (label do form).
- Sistema Struts/Dojo; grade de resultados por JS; busca exigindo **hCaptcha**
  (sitekey `e518a43a-5916-4627-b07b-c6e0c2713f24`) → **exige ação humana**.
- Após resolução humana em 2026-08-09, o filtro `462 → 513 → 514` com
  `especializacao=515` retornou **201 itens**. A diferença para os 210 registros
  do Portal da Transparência permanece pendente de reconciliação.
- Padrões expostos pelo front-end:
  `visualizacaoArquivosProcesso.html?id=<id_interno>` e
  `visualizacaoArquivosProcessoOrdenados.html?id=<id_interno>`.
- Uso atual: **pesquisa humana assistida**; registrar filtros e percurso, e só
  depois automatizar a leitura dentro da sessão liberada.

## Complementares

- Sentinela dos atos normativos: `https://www.tce.mg.gov.br/Noticia/Detalhe/30`.
- SICOM: `https://www.tce.mg.gov.br/sicom` (sistemas; conferência).
- IN 2/2023 (alterada pela IN 1/2024): remessa de informações e documentos de
  licitações pelo Módulo Edital e Licitação do SICOM — coletada (`in-2-2023-sicom-licitacoes`).
- PNCP (contratações de outros órgãos, fase 2): `https://pncp.gov.br` — uso conforme
  regras da pesquisa de preços do Charles.

## Estado de acesso (resumo)

| Fonte | Status | Ação necessária |
|---|---|---|
| TCLEGIS | `OPERACIONAL` | nenhuma (coletor automático já funciona) |
| Transparência TCE-MG | `ACESSIVEL_EM_NAVEGADOR` | exportar XLSX pela interface; API direta ainda retorna HTTP 401 |
| Compras MG (1020) | `ACESSIVEL_EM_SESSAO_HUMANA` | humano resolve hCaptcha; automação atua na sessão liberada |
| PNCP | aberto | nenhuma (fase 2) |
