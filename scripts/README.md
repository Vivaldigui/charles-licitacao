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
| `cesta_precos.py` | **Orquestrador da pesquisa de preços**: reúne as fontes, monta a cesta e gera o relatório com os 13 blocos + textos para a minuta-mãe. |
| `contratacoes_similares.py` | **Orquestrador da pesquisa de contratações similares** (referência técnica/redacional — **não** é pesquisa de preços). |
| `tce_mg_licitacoes.py` | Coleta as contratações do TCE-MG no Portal da Transparência (`listar` / `baixar` / `extrair`). Exige token de captcha obtido no navegador. |
| `tce_mg_fichas.py` | Gera as fichas Markdown e o índice de `14_referencias_externas/tce_mg_contratacoes/` a partir do que foi coletado. |
| `exemplos/` | `entrada-exemplo.json`, `manual-exemplo.json`, `saida-exemplo.md`, `demanda-exemplo.json`. |

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

### Pesquisa de contratações similares (referência técnica — NÃO é pesquisa de preços)

```bash
cd scripts

# Consultas de descoberta em portais oficiais (modo similares, sem chave -> links manuais):
python busca_web.py --objeto "forno de micro-ondas" --modo similares

# Pesquisa completa (PNCP multi palavra-chave + plano de busca web) gravando a estrutura de pastas:
python contratacoes_similares.py --demanda exemplos/demanda-exemplo.json --pncp --web --saida-dir saida/

# Só o relatório inicial (stdout), sem rede:
python contratacoes_similares.py --demanda exemplos/demanda-exemplo.json

# Com referências já coletadas pelo humano:
python contratacoes_similares.py --demanda exemplos/demanda-exemplo.json --manual referencias.json --saida relatorio.md
```

**Diferença entre as duas pesquisas:**

| | Pesquisa de preços (`cesta_precos.py`) | Contratações similares (`contratacoes_similares.py`) |
|---|---|---|
| Objetivo | estimar o **valor** da contratação (cesta) | **referência técnica/redacional** (objeto, requisitos, obrigações) |
| Modalidade | filtra por comparabilidade de preço | **não filtra** — modalidade é metadado |
| Valores | conclui média/mediana/menor | apenas **contexto**, não conclui preço |
| Saída | relatório + minuta-mãe de Pesquisa de Preços | relatório + fila de leitura + estrutura de pastas |
| Minuta | preenche `05_minutas/PESQUISA_DE_PRECOS/` | alimenta DFD/ETP/TR — geração sempre pelas minutas de `05_minutas/` |

O `contratacoes_similares.py` **reutiliza** `pncp_consulta.consultar_pncp_multi()` e
`busca_web.buscar_web(..., modo="similares")`, funciona **sem chave de API** e nunca simula
resultado nem inventa contratação/link/documento/valor. A leitura dos documentos e a confirmação de
relevância são **humanas** (ver [`../07_checklists/roteiro-pesquisa-contratacoes-similares.md`](../07_checklists/roteiro-pesquisa-contratacoes-similares.md)
e [`../07_checklists/regras-pesquisa-contratacoes-similares.md`](../07_checklists/regras-pesquisa-contratacoes-similares.md)).

## Corpus dos Informativos de Licitações e Contratos do TCU

O `tcu_informativos.py` coleta, por padrão, as edições nº 452 a 531 da página oficial do TCU,
preserva os PDFs e seleciona enunciados sobre contratação direta, dispensa, inexigibilidade e
credenciamento. A seleção é feita no sumário editorial, não em menções incidentais da narrativa.

```bash
# Diagnosticar URLs e datas sem baixar/processar
python -m scripts.tcu_informativos --somente-descobrir

# Processamento integral do recorte padrão
python -m scripts.tcu_informativos

# Teste ou reprocessamento de edições determinadas
python -m scripts.tcu_informativos --edicoes 455,457,462,483,514,525
```

As fichas resultantes são instrumentos de localização. O informativo não substitui o acórdão;
por isso cada registro conserva página, URL, link do inteiro teor, original e SHA-256 e permanece
com o status `verificar-inteiro-teor`.

## Contratações do TCE-MG — `tce_mg_licitacoes.py` e `tce_mg_fichas.py`

O Portal da Transparência do TCE-MG (https://transparencia.tce.mg.gov.br/public/licitacoes) não
tem API aberta: o front Angular resolve um **captcha**, recebe um JWT e o guarda em
`localStorage['tokenAuthorizationProxy']`, válido por cerca de 2 horas. O script **não resolve
captcha e não faz login** — recebe o token já obtido no navegador e repete as mesmas chamadas
que a página faz.

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

- `listar` grava `MANIFESTO.json` e `.csv` em `_entrada/tce_mg_licitacoes/`.
- `baixar` traz a **DOC Interna/Externa** (o PDF único com as peças do processo SEI publicadas) e
  os anexos de URL pública, registrando URL, data/hora, status HTTP, tamanho e **sha256** em
  `EVIDENCIAS_DOWNLOAD.json`. HTTP 404 é registrado como ausência, nunca suprido por suposição.
- `extrair` usa `pypdf`; PDF sem camada de texto é marcado como digitalizado (não há OCR aqui).
- `tce_mg_fichas.py` reconstrói as peças pelo rodapé do SEI de cada página, separa o dispositivo
  **adotado como fundamento** do que é apenas citado, e escreve as fichas + `_INDICE.md`.

Os PDFs brutos ficam em `_entrada/`, fora do versionamento. O que a base cita são as fichas.
Metodologia completa e limites em
[`../14_referencias_externas/tce_mg_contratacoes/_METODOLOGIA_COLETA.md`](../14_referencias_externas/tce_mg_contratacoes/_METODOLOGIA_COLETA.md).

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

---

## Gestão Documental dos Processos — `gestao_documental/`

Camada final comum de **todos** os geradores: nenhum script escolhe onde salvar o documento na
pasta do processo. A entrega é sempre por

```python
from registrar_documento import registrar_saida_gerada
registrar_saida_gerada(processo, tipo_documento, arquivo_temporario,
                       minuta_origem, motivo, status)
```

que compara o conteúdo com a versão vigente (**geração idêntica não cria versão**), arquiva a
anterior em `90_HISTORICO/` com número de versão e carimbo de tempo, move o novo de forma atômica
para o nome canônico (`TR.docx`, nunca `TR_final_2.docx`) e atualiza manifesto, log e painel.
Documento **assinado ou publicado é imutável**; falha no meio desfaz tudo e preserva o anterior.

| Script | Para quê |
|---|---|
| `iniciar_processo.py` | cria a pasta organizada e os arquivos de controle |
| `registrar_documento.py` | **interface única** de gravação; primeira geração e substituição |
| `substituir_documento.py` | troca a versão vigente, com motivo obrigatório |
| `promover_documento.py` | aprovado / assinado / publicado e a **retificação** |
| `arquivar_versao.py` | tira da área corrente preservando no histórico |
| `restaurar_versao.py` | restaura conteúdo antigo como versão **nova** |
| `importar_documento_externo.py` | quarentena → classificação → `03_DOCUMENTOS_EXTERNOS/` |
| `classificar_documento.py` | tipo, origem, CNPJ, data e processo, com grau de confiança |
| `detectar_duplicados.py` | duplicados exatos e prováveis — **não apaga nada** |
| `migrar_processo.py` | organiza pasta antiga: plano primeiro, execução por cópia depois |
| `limpar_temporarios.py` | só `99_TEMPORARIOS/` e locks vencidos |
| `gerar_painel.py` | `PAINEL_PROCESSO.md`, derivado dos JSON |
| `validar_processo.py` | manifesto × arquivos × histórico; sai com 1 havendo erro |
| `seguranca_repositorio.py` | repositório público, `.gitignore`, documentos sensíveis |
| `manifesto.py` `nomes_arquivos.py` `hashes.py` `locks.py` `transacoes.py` | núcleo |

**Sem dependência externa** — só a biblioteca padrão. O texto de um DOCX é lido abrindo o pacote
OOXML diretamente; `python-docx` fica restrito a `docx_cmi/`.

Integração já ligada nos geradores existentes:

```bash
# padronização documental entrega o DOCX formatado ao processo
python scripts/docx_cmi/formatar_docx.py --entrada bruto.docx --saida TR.docx \
  --perfil tr --registrar-em-processo PA_031_2026 --tipo-documento TR

# aviso completo registra o documento único (componentes NÃO são duplicados)
python scripts/aviso_completo/montar_aviso_completo.py --processo <pasta> \
  --registrar-em-processo PA_031_2026
```

Documentação: [`../10_gestao_documental/README.md`](../10_gestao_documental/README.md),
[`../07_checklists/roteiro-gestao-documental-processo.md`](../07_checklists/roteiro-gestao-documental-processo.md)
e [`../07_checklists/regras-gestao-documental-processo.md`](../07_checklists/regras-gestao-documental-processo.md).
