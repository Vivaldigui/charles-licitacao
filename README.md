---
tipo: checklist
tema: readme
fonte: base Charles
vigencia: vigente
atualizado_em: 2026-06-27
tags: [readme]
---

# Charles — Consultor de Licitações da Câmara Municipal de Itanhandu (MG)

Base de conhecimento e instruções operacionais para o **Charles**, consultor de licitações e
contratações públicas (Lei 14.133/2021) da Câmara Municipal de Itanhandu. Tudo aqui é Markdown +
documentos oficiais; o Charles **lê os arquivos da base antes de afirmar** (ver `CLAUDE.md`).

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `00_indices/` | Índice geral, mapas por tema/modalidade, glossário. |
| `01_legislacao/` | Leis (Lei 14.133/2021, limites do art. 75). |
| `02_normas_internas/` | Regulamento e portarias da Câmara (inclui a **Portaria 03/2024 — pesquisa de preços**). |
| `03_jurisprudencia/` | TCU, TCE-MG, súmulas. |
| `04_doutrina_artigos/` | Artigos de apoio. |
| `05_minutas/` | **Minutas-mãe oficiais** (DOCX) + fichas de uso. **Única** fonte para gerar documentos. |
| `06_precedentes_camara/` | Controle de contratações (limite por CNAE). |
| `07_checklists/` | Roteiros operacionais (julgamento, limite CNAE, **pesquisa de preços**). |
| `08_processos_em_andamento/` | Instruções/rascunhos atuais. |
| `scripts/` | Ferramentas Python de apoio à **pesquisa de preços** (PNCP, busca web, cálculo). |

## Funcionalidade: Executar Pesquisa de Preços

Instrui, de forma rastreável e crítica, a estimativa de valor de uma contratação (Lei 14.133/2021,
art. 23; Portaria 03/2024 da Câmara) e preenche a **minuta-mãe oficial** de Pesquisa de Preços —
**sem criar modelo novo**.

**Como pedir ao Charles:**

> "Charles, execute pesquisa de preços para o objeto: {{OBJETO}}, quantidade {{QUANTIDADE}},
> unidade {{UNIDADE}}, usando PNCP e fontes oficiais externas, e preencha a minuta-mãe de
> Pesquisa de Preços."

O Charles segue o roteiro e as regras:

- [`07_checklists/roteiro-executar-pesquisa-de-precos.md`](07_checklists/roteiro-executar-pesquisa-de-precos.md) — fluxo de 13 passos, entrada, saída e mapeamento da minuta.
- [`07_checklists/regras-pesquisa-de-precos.md`](07_checklists/regras-pesquisa-de-precos.md) — comparabilidade, tratamento de valores, segurança jurídica e checklist de validação humana.

### Ferramentas de apoio (opcionais)

Scripts em [`scripts/`](scripts/README.md) automatizam a parte mecânica. **Python 3, só stdlib —
sem `pip install`. Funcionam sem chave de API** (PNCP é público; a busca web cai em consultas
manuais). Modo manual disponível para colar resultados já coletados.

```bash
cd scripts
# Pesquisa completa (PNCP + web) gerando o relatório:
python cesta_precos.py --processo exemplos/entrada-exemplo.json --pncp --web --saida relatorio.md
# Modo manual:
python cesta_precos.py --processo exemplos/entrada-exemplo.json --manual exemplos/manual-exemplo.json --saida relatorio.md
```

Variáveis de ambiente em [`.env.example`](.env.example) (todas opcionais).

### Validação humana (obrigatória)

A pesquisa é **apoio à decisão**. Antes de juntar ao processo, um servidor confere: fontes reais e
links que abrem, preços conferidos com os comprovantes, exclusões justificadas, método e valor
final motivados, campos `[PREENCHER]` resolvidos e uso da minuta-mãe sem alterar estrutura/timbre.
Os scripts **nunca inventam** preço, órgão, número de contratação ou link.

## Dois modos de operação do Charles

- **Consulta / instrução** — responde dúvidas citando arquivo + dispositivo.
- **Geração de documentos** — preenche **somente** as minutas-mãe de `05_minutas/`.

Detalhes, hierarquia de fontes e regras anti-alucinação: ver [`CLAUDE.md`](CLAUDE.md).
