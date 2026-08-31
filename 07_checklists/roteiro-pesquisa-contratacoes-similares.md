---
tipo: checklist
hierarquia: operacional
tema: pesquisa de contratacoes similares
fonte: base Charles / Lei 14.133/2021 / PNCP / portais oficiais
vigencia: vigente
atualizado_em: 2026-07-23
tags: [pesquisa-contratacoes-similares, pncp, referencia-tecnica, dfd, etp, tr, roteiro]
---

# Roteiro — Pesquisa de Contratações Similares

Roteiro operacional do Charles para o **MODO PESQUISA DE CONTRATAÇÕES SIMILARES**: localizar,
acessar, ler, comparar e organizar contratações públicas semelhantes ao objeto que a Câmara
Municipal de Itanhandu pretende contratar, para uso como **referência técnica e redacional**
(DFD, ETP, TR, requisitos, obrigações, prazos, garantias, análise de riscos, minuta de contrato).

> **Não é pesquisa formal de preços.** Esta funcionalidade pode registrar valores apenas como
> **contexto**; ela **não** estima o valor da contratação. Para formar a cesta e estimar o valor,
> use o fluxo próprio: [`roteiro-executar-pesquisa-de-precos.md`](roteiro-executar-pesquisa-de-precos.md).

> **Comando de uso (linguagem natural):**
> "Charles, pesquise contratações similares para {{OBJETO}}. Antes de iniciar o DFD/TR, localize
> como outros órgãos contrataram, leia os documentos e extraia objeto, solução, requisitos,
> obrigações, prazos e garantias."

---

## Regras principais (inegociáveis)

- **Independe da modalidade.** Referências de pregão, concorrência, dispensa, inexigibilidade,
  credenciamento, registro de preços ou adesão são todas aproveitáveis. A modalidade é **metadado**,
  nunca filtro de exclusão. A relevância decorre da semelhança do objeto/necessidade/solução, da
  qualidade do documento técnico e da atualidade — não da forma de seleção.
- **Ler antes de recomendar.** Não basta o título no PNCP: acessar a página, localizar e **ler** os
  documentos. Informar quais documentos foram efetivamente lidos.
- **Referência ≠ regra local.** Documento de outro órgão é fonte comparativa, não norma da Câmara.
  Separar o que pode ser aproveitado do que é rito/competência/regulamento do órgão pesquisado.
- **Antialucinação.** Nunca inventar contratação, processo, link, documento, valor, fornecedor ou
  e-mail. Sem documento aberto, a evidência é "indício"/"parcial", nunca "confirmada".
- **Geração de documento continua travada nas minutas** de `05_minutas/`. A pesquisa alimenta o
  conteúdo; a estrutura é sempre a da minuta oficial.

---

## Fluxo (16 passos)

1. **Receber a demanda** e criar a **Ficha da Demanda** (§Entrada). Campos ausentes: marcar
   `A preencher pela Câmara Municipal de Itanhandu`; não travar a pesquisa por dado secundário.
2. **Decompor o objeto** em elementos pesquisáveis: produto/serviço, problema, finalidade,
   usuários, quantidade, unidade, local, características indispensáveis, serviços acessórios,
   resultado esperado.
3. **Gerar palavras-chave**: nome popular e técnico, sinônimos, singular/plural, finalidade,
   problema, componentes da solução, termos de mercado, CATMAT/CATSER (só se de fonte oficial).
4. **Pesquisar no PNCP** por várias palavras-chave, sem filtrar modalidade
   (`scripts/contratacoes_similares.py --pncp` ou consulta manual ao portal). Registrar URL, data,
   órgão, modalidade, nº de controle, data e link.
5. **Pesquisar na web** (modo similares) priorizando domínios oficiais (`.gov.br`, `.leg.br`,
   `.jus.br`, `.mp.br`, `.tc.br`) e documentos técnicos (DFD, ETP, TR, projeto básico, edital,
   contrato). O buscador é ferramenta de **descoberta**, não prova.
6. **Triar** os resultados: eliminar falsos positivos e duplicidades; priorizar objeto/contexto
   semelhantes e documentos acessíveis.
7. **Acessar os processos** nas páginas oficiais.
8. **Baixar os documentos** relevantes, preservando o original (não alterar), com origem e data de
   acesso (`04_documentos_originais/`).
9. **Ler efetivamente** DFD, ETP, TR, projeto básico, edital, aviso, proposta, ata, contrato, etc.
   PDF digitalizado ilegível: `DOCUMENTO DIGITALIZADO — depende de OCR/conferência manual`.
10. **Extrair** por referência (§Extração): objeto, necessidade, solução, especificações,
    requisitos, obrigações, prazos, garantia, critérios de aceitação, habilitação/qualificação,
    valores (contexto), documentos lidos, links, data de acesso.
11. **Comparar** as referências em quadro (`06_quadros_comparativos/`): requisitos recorrentes,
    isolados, potencialmente excessivos; obrigações; prazos e garantias.
12. **Classificar a evidência** (confirmada/parcial/indício/não confirmada) e a **relevância**
    (alta/média/baixa/descartada), justificando exclusões relevantes.
13. **Separar** referência técnica aproveitável × regra procedimental do órgão pesquisado.
14. **Adaptar para Itanhandu**: o que adotar, adaptar, descartar, submeter ao setor
    requisitante/técnico/jurídico. Sugestões fora do modelo: `SUGESTÃO ADICIONAL — depende de
    avaliação da Câmara` (`08_.../aplicacao_itanhandu/`).
15. **Gerar o relatório** de contratações similares (§Saída).
16. **Validação humana** (§Checklist final) antes de usar a pesquisa no processo. A geração de
    qualquer documento continua **exclusivamente** pelas minutas de `05_minutas/`.

---

## Entrada (Ficha da Demanda)

Órgão (Câmara de Itanhandu/MG); setor requisitante; objeto pretendido; problema/necessidade;
finalidade; quantidade e unidade; prazo; contratação continuada ou pontual; há contrato anterior;
há urgência; palavras-chave e sinônimos; filtros (UF, município, período); observações.
Modelo: `scripts/exemplos/demanda-exemplo.json`.

---

## Ferramentas de apoio (opcionais — não obrigatórias)

- `scripts/contratacoes_similares.py` — orquestra a pesquisa: gera palavras-chave, consulta o PNCP
  (multi palavra-chave, sem filtrar modalidade), prepara/roda a busca web (modo similares),
  deduplica, sugere relevância preliminar por sobreposição de termos, monta a fila de leitura e
  escreve o relatório inicial e a estrutura de pastas.
- `scripts/pncp_consulta.py` — `consultar_pncp_multi(...)` para várias palavras-chave.
- `scripts/busca_web.py --modo similares` — consultas/links de descoberta em portais oficiais.

> Funcionam **sem chave de API** (PNCP é público; a busca web cai em consultas manuais). O Charles
> pode operar **sem** os scripts, fazendo consultas e leitura manualmente — o roteiro vale igual.

---

## Extração técnica (por referência)

Objeto; necessidade administrativa; solução (fornecimento, instalação, entrega, treinamento,
garantia, manutenção, suporte); especificações; requisitos (comuns × isolados × excessivos);
obrigações da contratada e da contratante; prazos de entrega/execução; garantia e suporte;
critérios de aceitação; recebimento provisório/definitivo; habilitação e qualificação técnica;
exigência de amostra/catálogo; sustentabilidade; vigência; sanções; riscos; valores (contexto);
documentos efetivamente lidos; links oficiais; data de acesso.

Ficha por referência: ver §17 do prompt-mestre (frontmatter `tipo: referencia_contratacao`),
gravada em `05_fichas_de_leitura/`.

---

## Saída esperada (relatório)

Demanda · problema · estratégia · termos · fontes · contratações localizadas · contratações
descartadas · documentos lidos · quadro comparativo · padrões · descrições de objeto · soluções ·
requisitos recorrentes/isolados/excessivos · obrigações · prazos e garantias · valores (contexto) ·
fornecedores · elementos aproveitáveis/adaptáveis/a evitar · sugestão de objeto/necessidade/solução/
requisitos · informações pendentes · riscos e pontos de atenção · fontes e links · validação humana.

Estrutura de pastas (gerada por `--saida-dir`):

```text
pesquisa_contratacoes_similares/
├── 01_ficha_demanda.md
├── 03_resultados_brutos/ (pncp.json, web.json, manual.json, referencias.json, fila_leitura.json)
├── 04_documentos_originais/ (preservar os arquivos baixados, sem alterar)
├── 05_fichas_de_leitura/
├── 06_quadros_comparativos/
├── 07_relatorio/relatorio_contratacoes_similares.md
└── 08_aplicacao_itanhandu/
```

---

## Critério de suficiência

Buscar ≥5 contratações relevantes (idealmente 8–15), com ≥3 documentos técnicos efetivamente
acessíveis, de mais de um órgão, recentes, e ao menos uma de contexto semelhante quando houver.
**Não** preencher a quantidade mínima com resultados irrelevantes. Persistindo a insuficiência,
registrar: _"A pesquisa não localizou quantidade suficiente de contratações com documentos técnicos
acessíveis. Os resultados encontrados foram apresentados, mas não permitem afirmar que representam
um padrão consolidado de contratação."_

---

## Checklist final (validação humana)

- [ ] Os links abrem e os documentos pertencem ao processo indicado.
- [ ] Os trechos foram extraídos corretamente; a modalidade foi registrada certa.
- [ ] Não se importou regra local de outro órgão como obrigação da Câmara.
- [ ] As referências estão atuais; os valores foram tratados apenas como contexto.
- [ ] A relevância sugerida foi confirmada após a leitura dos documentos.
- [ ] Requisitos comparáveis; exclusões relevantes justificadas.
- [ ] Sugestões fora do modelo marcadas como `SUGESTÃO ADICIONAL`.
- [ ] Minuta oficial preservada; campos pendentes identificados.
- [ ] Nenhum dado inventado (contratação, link, documento, valor, fornecedor, e-mail).
