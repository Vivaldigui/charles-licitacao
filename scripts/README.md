# scripts/ — Ferramentas de apoio à Pesquisa de Preços

Utilitários em **Python 3 (somente biblioteca padrão — não exige `pip install`)** que automatizam
a parte **mecânica** da funcionalidade "Executar Pesquisa de Preços": coleta no PNCP, busca
complementar, normalização de valores e montagem do relatório/cesta.

> O **juízo jurídico** (comparabilidade final, exclusões fundamentadas, escolha de metodologia,
> redação institucional) é do agente/Charles. Veja as regras em
> [`../07_checklists/roteiro-executar-pesquisa-de-precos.md`](../07_checklists/roteiro-executar-pesquisa-de-precos.md)
> e [`../07_checklists/regras-pesquisa-de-precos.md`](../07_checklists/regras-pesquisa-de-precos.md).
> Os scripts **nunca inventam** preço, órgão, número de contratação ou link.

## Requisitos

- Python 3.9+ (testado em 3.12). Nada além da stdlib.
- Acesso à internet apenas para o PNCP e para a busca web com provedor. **Sem internet**, use o
  **modo manual**.

## Arquivos

| Script | O que faz |
|---|---|
| `pncp_consulta.py` | Busca contratações similares no PNCP (API pública de busca textual). |
| `busca_web.py` | Busca complementar (Google CSE / SerpAPI) **ou** gera consultas/links para pesquisa manual. |
| `normalizar_precos.py` | Converte moeda BR, recalcula unitário, detecta discrepantes (IQR), calcula média/mediana/menor. |
| `cesta_precos.py` | **Orquestrador**: reúne as fontes, monta a cesta e gera o relatório com os 13 blocos + textos para a minuta-mãe. |
| `exemplos/` | `entrada-exemplo.json`, `manual-exemplo.json`, `saida-exemplo.md`. |

## Variáveis de ambiente (todas opcionais)

| Variável | Default | Uso |
|---|---|---|
| `PNCP_API_BASE_URL` | `https://pncp.gov.br/api` | Base da API do PNCP. |
| `PNCP_SEARCH_PATH` | `/search/` | Caminho da busca textual. |
| `SEARCH_PROVIDER` | `none` | `google`, `serpapi` ou `none` (gera consultas manuais). |
| `GOOGLE_SEARCH_API_KEY` / `GOOGLE_SEARCH_CX` | — | Google Programmable Search. |
| `SERPAPI_KEY` | — | SerpAPI. |

Modelo em [`../.env.example`](../.env.example). **Funciona sem nenhuma chave**: o PNCP é público e
a busca web cai no modo de consultas sugeridas.

## Exemplos de uso

```bash
cd scripts

# 1) Normalização/estatística rápida (lista de preços):
echo '[789.00, 812.50, 865.00, 2490.00]' | python normalizar_precos.py

# 2) Consulta PNCP (público, sem chave):
python pncp_consulta.py --objeto "cadeira de escritório" --uf MG --max 10
python pncp_consulta.py --objeto "toner impressora" --json > pncp.json

# 3) Busca complementar (sem chave -> consultas/links manuais):
python busca_web.py --objeto "cadeira de escritório giratória"

# 4) Pesquisa completa — automática (PNCP + web) gerando o relatório:
python cesta_precos.py --processo exemplos/entrada-exemplo.json --pncp --web --saida relatorio.md

# 5) Modo manual (cola dados já coletados pelo humano):
python cesta_precos.py --processo exemplos/entrada-exemplo.json --manual exemplos/manual-exemplo.json --saida relatorio.md

# 6) Combinar tudo:
python cesta_precos.py --processo exemplos/entrada-exemplo.json --pncp --web --manual exemplos/manual-exemplo.json
```

## Notas

- **Filtro de UF/município:** o PNCP pode ou não honrar o filtro na busca textual; confira sempre a
  localidade no resultado e despreze o que não for comparável.
- **`valor_global` do PNCP = total da contratação**, não preço unitário. O orquestrador só calcula
  unitário quando há quantidade confiável; caso contrário, deixa em branco (não chuta).
- **Erros de rede** não interrompem a pesquisa: viram mensagem estruturada com a URL chamada e a
  data, para rastreabilidade. Nesses casos, use o modo manual.
- A saída é um **documento de trabalho** com marcadores `[PREENCHER]` e `[VALIDAÇÃO HUMANA]`. O
  texto final vai para a **minuta-mãe oficial** (`05_minutas/PESQUISA_DE_PRECOS/`), sem alterar
  estrutura/timbre.
