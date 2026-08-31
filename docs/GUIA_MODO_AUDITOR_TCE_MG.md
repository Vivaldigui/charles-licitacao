---
tipo: checklist
hierarquia: operacional
tema: guia do modo auditor tce-mg
fonte: implementação local do Charles
vigencia: vigente
atualizado_em: 2026-07-31
tags: [modo-auditor, tce-mg, sqlite, fts5]
---

# Guia do Modo Auditor de Contratações Diretas

## Finalidade

O modo auditor inventaria documentos do processo, cruza critérios da base e recupera jurisprudência
local do TCE-MG com arquivo, página e trecho. A busca é mecanicamente reprodutível; relevância,
tese, contraditório, gravidade e conclusão continuam sujeitos a leitura e validação humana.

Gatilho principal: **“Charles, audite este processo”**. O fluxo normativo está em
`07_checklists/roteiro-modo-auditor-contratacao-direta.md`.

## Instalação

```powershell
python -m pip install -r requirements-auditor.txt
```

O SQLite do Python deve oferecer FTS5. OCR é opcional e só é tentado para PDF sem texto quando
`--ocr` é informado; nesse caso, `tesseract` e `pdftoppm` devem estar acessíveis.

## Estrutura gerada

```text
03_jurisprudencia/tce_mg/contratacao_direta/
├── inteiro_teor_bruto/README.md
├── texto_extraido/
├── fichas/
├── indices/
│   ├── auditor_tcemg.sqlite3
│   ├── catalogo_julgados.jsonl
│   ├── catalogo_julgados.csv
│   └── manifesto_originais.jsonl
├── consolidacoes/
└── relatorios_processamento/
```

`TCE-MG_JULGADOS/` permanece como camada bruta imutável. O manifesto registra cada ocorrência,
inclusive duplicidades, com caminho e SHA-256. Arquivos idênticos são reaproveitados sem perder a
proveniência de cada pasta/processo.

## Comandos

```powershell
# Diagnóstico sem escrita no corpus
python -m scripts.auditor_tcemg diagnosticar --entrada TCE-MG_JULGADOS

# Ingestão incremental e retomável
python -m scripts.auditor_tcemg ingerir --entrada TCE-MG_JULGADOS

# Reprocessamento explícito
python -m scripts.auditor_tcemg ingerir --entrada TCE-MG_JULGADOS --forcar

# Recalcular metadados/relevância sem reextrair PDFs
python -m scripts.auditor_tcemg reclassificar --entrada TCE-MG_JULGADOS

# Busca textual e por filtros
python -m scripts.auditor_tcemg buscar --consulta "pesquisa de preços" --regime lei-14133
python -m scripts.auditor_tcemg buscar --tema fracionamento --data-inicial 2023-01-01
python -m scripts.auditor_tcemg buscar --processo 1148718

# Incluir, deliberadamente, referências incidentais
python -m scripts.auditor_tcemg buscar --consulta "dispensa" --incluir-incidentais

# Preparar pacote jurisprudencial para um processo
python -m scripts.auditor_tcemg preparar-auditoria `
  --processo 08_processos_em_andamento/PA_000_2026 `
  --saida 08_processos_em_andamento/PA_000_2026/CONTEXTO_JURISPRUDENCIAL_AUDITORIA.md

# Conferência técnica, integridade e preservação dos originais
python -m scripts.auditor_tcemg validar --amostra 10
```

## Correções humanas

Correções não devem ser feitas diretamente no JSONL/CSV. Registre-as no banco com autoria e notas:

```powershell
python -m scripts.auditor_tcemg revisar `
  --documento tcemg-1121072-615acc4f1065 `
  --campo legal_regime `
  --valor lei-8666 `
  --revisor "Nome do revisor" `
  --notas "Fundamento e páginas conferidas"

python -m scripts.auditor_tcemg relatorio-corpus --entrada TCE-MG_JULGADOS
```

Revisões concluídas prevalecem sobre reclassificações mecânicas posteriores. Para validar uma amostra,
copie a estrutura de `99_testes/auditor_tcemg/confirmacoes_amostra.json`, confira cada campo contra o
PDF e rode `validar --confirmacoes arquivo.json`.

## Adição de novos julgados

1. Acrescente o original ao corpus sem alterar o arquivo.
2. Rode `diagnosticar` para conferir formato/hash.
3. Rode `ingerir`; itens cujo caminho e hash não mudaram serão ignorados.
4. Rode `validar` e confira a amostra/relatórios.
5. Reindexe a base geral com `python scripts/indexar_base.py`.

## Como interpretar resultados

- `direta`: tema na ementa/cabeçalho ou desenvolvido em múltiplas ocorrências;
- `parcial`: desenvolvimento limitado, ainda útil sob leitura humana;
- `incidental`: menção isolada, excluída da busca padrão;
- `falso_positivo`: termo central não recuperado;
- `pendente_revisao`: extração/classificação insuficiente.

BM25 mede correspondência textual, não força jurídica. Um resultado alto pode ser alegação da parte,
manifestação técnica, voto vencido ou contexto histórico. Abra sempre a página e o inteiro teor.

## Limitações e falhas comuns

- Metadados ausentes ficam como “Não identificado no documento”; o sistema não completa por palpite.
- OCR ruim ou indisponível gera fila de revisão, não texto inventado.
- A ementa é preservada como ementa oficial, não convertida automaticamente em tese do Charles.
- Precedente sob a Lei 8.666/1993 não é transplantado automaticamente à Lei 14.133/2021.
- Divergência, voto vencido, superação e efeito vinculante exigem análise humana.
- Se FTS5 não estiver disponível, use outra distribuição oficial do Python com SQLite FTS5.
- Se um processamento for interrompido, execute novamente: caminho + SHA-256 tornam a ingestão
  idempotente e retomável.
- Nunca edite ou apague `TCE-MG_JULGADOS/` para “corrigir” o índice; corrija metadados no histórico.

## Verificação automatizada

```powershell
python -m unittest discover -s 99_testes/auditor_tcemg -p "test_*.py" -v
python -m scripts.auditor_tcemg validar --amostra 5 `
  --confirmacoes 99_testes/auditor_tcemg/confirmacoes_amostra.json
```

O exemplo completo está em `99_testes/auditor_tcemg/exemplo_auditoria/`.
