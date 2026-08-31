---
tipo: indice
tema: base de dados — contratações diretas TCE-MG
fonte: projeto
vigencia: vigente
atualizado_em: 2026-08-09
tags: [indice, leia-me]
---

# Base documental — Contratações diretas no TCE-MG

Base de conhecimento rastreável sobre **dispensa e inexigibilidade de licitação
(Lei 14.133/2021), fase preparatória, pesquisa de preços, parecer jurídico e
contratação direta** no âmbito do Tribunal de Contas do Estado de Minas Gerais
(TCE-MG), voltada a alimentar um material de trabalho do Charles.

## Princípios

1. **Nada inventado.** Cada item da base tem origem identificável (URL, arquivo,
   ementa, PDF baixado). O que não for localizado é registrado como
   `não identificado / não localizado na fonte pesquisada` (nunca chute).
2. **Evidência classificada.** Todo material é `oficial` (baixado do órgão),
   `normalizada` (derivada/reescrita) ou `inferência` (decorre de outra evidência).
3. **SHA-256 obrigatório.** Todo documento baixado tem hash e registro de
   proveniência (`00_CONTROLE/hashes/`).
4. **Original preservado.** Cópias de trabalho em `01_ATOS_NORMATIVOS/`; originais
   em `99_ORIGINAIS/`. Nunca se altera um arquivo-fonte.
5. **Legitimidade.** Sem quebra de CAPTCHA, sem contornar autenticação nem burlar
   limitação de acesso. Onde a ação humana é obrigatória, fica registrada.

## Fontes

| Fonte | Acesso | Status |
|---|---|---|
| Portal da Transparência TCE-MG (licitações) | SPA via API `arabiasaudita.../p-portal-transparencia/` | **210 compras diretas SIAD/Lei 14.133 exportadas pela interface**; API direta retorna HTTP 401 |
| Portal de Compras MG (órgão 1020 = TCE-MG) | Struts/Dojo + hCaptcha | **201 compras diretas observadas após resolução humana**; hCaptcha não contornado |
| **TCLEGIS** (atos normativos) | ASP.NET MVC, sem captcha | **operacional** — fonte dos 32 atos do índice |
| SICOM / IN 2/2023 e 1/2024 | normativo (TCLEGIS); sistema próprio | normativo coletado |
| tce.mg.gov.br — Atos Normativos (Noticia/Detalhe/30) | página oficial | referência curada |

Detalhamento técnico completo: `00_CONTROLE/diagnostico_fontes.md`.

## Estado atual (Fases 1–3 — Reconhecimento, normas e catálogo de processos)

### Fase 1 — Reconhecimento

- [x] Estrutura de pastas criada
- [x] Reconhecimento técnico do **Portal da Transparência TCE-MG**
- [x] Reconhecimento técnico do **Portal de Compras MG (órgão 1020)**
- [x] Pesquisa das fontes normativas (TCLEGIS) → **32 atos no índice**
      (núcleo curado)
- [x] Teste de download de documentos reais (prova de conceito)
- [x] `00_CONTROLE/diagnostico_fontes.md` redigido
- [x] Evidências brutas canonizadas em `00_CONTROLE/registros_web/`
      (manifesto com caminhos relativos e SHA-256; 107 arquivos após a
      revalidação do Portal da Transparência)
- [x] Esqueleto de scripts de coleta criado: `02_buscar_tclegis` (auto),
      `03_captura_humana_portais` (capturas registradas), `09_reconciliar_manifesto`

### Fase 2 — Coleta estruturada no TCLEGIS (script `04`, operacional)

- [x] Busca textual documentada (6 termos da agenda →
      `00_CONTROLE/busca/resultados_busca.json`) e triagem de **49 candidatos**
      por leitura da ementa extraída (`00_CONTROLE/coleta/candidatos_triagem.json`,
      com HTML cru em `registros_web/tclegis_detalhe/`)
- [x] **14 atos coletados** além do núcleo (relevantes/contexto), com PDF
      (COMPILADO → COMPLETO → ORIGINAL + texto .md) e SHA-256 por variante em
      `00_CONTROLE/hashes/norma_*.json`
- [x] **32 atos no índice** (`01_ATOS_NORMATIVOS/indice_normas.json|csv`):
      18 do núcleo (preservados, numeração curatorial tipo `83/PRES./2023`) +
      14 da Fase 2 (rebuildáveis e idempotentes via `--indices`; caminhos de
      arquivo relativos à raiz do repositório)
- [x] **35 descartes documentados** (irrelevantes/superseded) com motivo em
      `00_CONTROLE/coleta/decisao_triagem.md` e `descarte.json` — nenhum ato
      irrelevante entrou no índice
- [x] Convenção de pastas aplicada: `vigentes/` (inclui "alterada"),
      `revogados/`, `situacao_nao_confirmada/` (61 PDFs + 61 .md no total)

### Fase 3 — Catálogo inicial de processos (em andamento)

- [x] Exportação oficial com filtros **SIAD + Lei 14.133/21 + Compra direta**:
      **210 registros** (2023: 6; 2024: 58; 2025: 67; 2026: 79)
- [x] Originais XLSX/CSV preservados com SHA-256 em
      `00_CONTROLE/registros_web/validacao_interativa/`
- [x] Catálogo normalizado em `03_INDICES/processos_candidatos.csv|json`
- [x] Processo piloto `TCE-MG_2026_DISPENSA_000287` organizado com relatório SIAD,
      Termo de Referência, mapa comparativo de preços e autorização; 19 páginas
      extraídas, 4 documentos únicos e 2 duplicatas binárias registradas
- [ ] Reconciliar os 210 registros do Portal da Transparência com os 201 itens
      observados no Compras MG e recuperar a unidade/id interno
- [ ] Ampliar a coleta piloto para aproximadamente 5 dispensas e 5 inexigibilidades

### Pendências

- [ ] Concluir a Fase 3 (reconciliação e piloto documental) e avançar à Fase 4

## Estrutura

```
tce-mg-contratacoes-diretas/
├── README.md                    # este arquivo
├── metodologia.md               # como a base é construída e mantida
├── fontes.md                    # glossário operacional das fontes
├── 00_CONTROLE/                 # diagnóstico, hashes, evidências brutas
│   ├── diagnostico_fontes.md
│   ├── hashes/                  # proveniência + SHA-256 de cada download
│   └── registros_web/           # HTML/JS crus + MANIFESTO_EVIDENCIAS.json
├── 01_ATOS_NORMATIVOS/          # atos normativos do TCE-MG (32 no índice)
│   ├── indice_normas.csv|json
│   ├── vigentes/                # um diretório por ato (PDF + .md + proveniência)
│   ├── revogados/
│   └── situacao_nao_confirmada/
├── 02_PROCESSOS/                # estrutura anual para dispensa/inexigibilidade
├── 03_INDICES/                  # catálogo de 210 processos candidatos + índices documentais
├── 04_ANALISES/                 # análises transversais futuras
├── 05_BASE_CONHECIMENTO/        # corpus futuro para IA
├── 02_LEGISLACAO_FEDERAL/       # área legada preservada
├── 03_ORIENTACOES_TCE_MG/       # área legada preservada
├── 04_JURISPRUDENCIA_TCE_MG/    # área legada preservada
├── 99_ORIGINAIS/                # originais, imutáveis
└── scripts/                     # ferramentas de coleta e validação (Python)
```

## Como executar

```bash
# Dependências declaradas da coleta e extração
python -m pip install -r requirements.txt

# Atualizar a coleta de atos normativos (TCLEGIS) — idempotente
python scripts/01_descobrir_normas.py

# Busca textual documentada no TCLEGIS (indices de contratação direta)
python scripts/02_buscar_tclegis.py                # agenda da config.yaml
python scripts/02_buscar_tclegis.py --so-listar    # mostra os termos
python scripts/02_buscar_tclegis.py --termo "inexigibilidade"

# Capturas assistidas (Compras MG exige hCaptcha; Transparência funciona no navegador)
python scripts/03_captura_humana_portais.py --modelo   # modelo do registro

# Fase 2 — coleta estruturada no TCLEGIS (script 04, operacional)
python scripts/04_coletar_atos_tclegis.py              # triagem dos candidatos
python scripts/04_coletar_atos_tclegis.py --coleta     # baixa PDFs+texto dos relevantes
python scripts/04_coletar_atos_tclegis.py --indices    # reconstrói o índice (idempotente)
python scripts/04_coletar_atos_tclegis.py --status     # estado da triagem

# Manter manifesto de evidências em dia (idempotente)
python scripts/09_reconciliar_manifesto.py
python scripts/09_reconciliar_manifesto.py --check     # somente leitura

# Conferir PDFs e SHA-256 (padrão: somente leitura)
python scripts/08_validar_integridade.py
python scripts/08_validar_integridade.py --normalizar-caminhos --relatorio

# (Fase 2+) Coleta de processos/pesquisa de preços — ver metodologia
```
