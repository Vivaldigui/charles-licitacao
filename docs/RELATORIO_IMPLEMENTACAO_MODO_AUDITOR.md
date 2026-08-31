---
tipo: checklist
hierarquia: operacional
tema: relatorio de implementacao do modo auditor tce-mg
fonte: execução local verificada
vigencia: vigente
atualizado_em: 2026-07-31
tags: [modo-auditor, tce-mg, implementacao, validacao]
---

# Relatório de implementação — Modo Auditor TCE-MG

## Resultado

O Modo Auditor foi implementado de ponta a ponta: diagnóstico, ingestão incremental, preservação,
extração por página, catalogação, SQLite/FTS5, fichas, consolidações, recuperação auditável,
protocolo jurídico, CLI, testes, validação humana e exemplo completo.

## Corpus

| Indicador | Resultado |
|---|---:|
| Arquivos inventariados | 977 |
| PDFs candidatos a julgados | 968 |
| Arquivos auxiliares (JSON/CSV/TXT) | 9 |
| Documentos lógicos processados | 729 |
| Ocorrências preservadas | 968 |
| Hashes únicos | 628 |
| Grupos de duplicidade | 256 |
| Cópias excedentes | 340 |
| Páginas extraídas | 12.196 |
| Textos derivados | 729 |
| Fichas relevantes | 531 |
| Falhas | 0 |
| OCR necessário | 0 |
| Relevância direta | 430 |
| Relevância parcial | 101 |
| Menção incidental | 198 |

O número de documentos lógicos pode ser maior que o de hashes únicos porque ocorrências idênticas
associadas a números de processo distintos não são colapsadas como equivalência jurídica.

## Arquitetura entregue

- Bruta: `TCE-MG_JULGADOS/`, mantida no local e referenciada como imutável.
- Estruturada: `03_jurisprudencia/tce_mg/contratacao_direta/`.
- Código: `scripts/auditor_tcemg/`.
- Raciocínio: `CLAUDE.md` e `07_checklists/roteiro-modo-auditor-contratacao-direta.md`.
- Operação: `docs/GUIA_MODO_AUDITOR_TCE_MG.md`.

O banco contém tabelas de documentos, ocorrências, páginas, metadados, temas, teses, achados,
dispositivos, citações, relações, histórico e revisões humanas, além de FTS5/BM25.

## Arquivos criados

- `docs/PLANO_IMPLEMENTACAO_MODO_AUDITOR.md`;
- `docs/GUIA_MODO_AUDITOR_TCE_MG.md`;
- este relatório;
- `requirements-auditor.txt`;
- `AGENTS.md` e `scripts/auditor_tcemg/AGENTS.md`;
- pacote Python `scripts/auditor_tcemg/`;
- checklist `07_checklists/roteiro-modo-auditor-contratacao-direta.md`;
- suíte, cenários, confirmações e exemplo em `99_testes/auditor_tcemg/`;
- 729 textos, 531 fichas, quatro índices, oito consolidações e seis relatórios de processamento em
  `03_jurisprudencia/tce_mg/contratacao_direta/`.

## Arquivos existentes alterados

- `CLAUDE.md` e `07_checklists/modo-auditor.md`;
- `README.md` e `scripts/README.md`;
- `00_indices/INDICE_GERAL.md`, `MAPA_POR_TEMA.md`, `MAPA_POR_MODALIDADE.md` e
  `BASE_INDEXADA.json`;
- `99_testes/PERGUNTAS_DE_VALIDACAO.md`.

Nenhuma minuta-mãe de `05_minutas/` foi alterada por esta implementação.

## Dependência

Somente `pypdf>=5.0,<7`, isolado em `requirements-auditor.txt`, para extração PDF nativa por página.
SQLite/FTS5, JSONL, CSV e demais recursos usam a biblioteca padrão. Não há API paga, embeddings ou
modelo externo. OCR depende opcionalmente de Tesseract/Poppler e não foi necessário no corpus atual.

## Verificações executadas

- amostra inicial de cinco PDFs, com renderização visual da primeira página e conferência da paginação;
- ingestão completa: 968 ocorrências, 12.196 páginas, zero falha;
- segunda ingestão: `skipped: 968`, comprovando idempotência;
- 19 testes `unittest`: todos passaram;
- `PRAGMA integrity_check`, consistência páginas/FTS5/citações: sem erro;
- recálculo de SHA-256 dos 968 originais: 968 íntegros, zero divergência;
- amostra humana determinística de cinco julgados: 50 campos conferidos, 45 corretos (90%);
- uma correção de regime registrada em `human_reviews` para o Processo 1121072;
- busca `pesquisa de preços` retornou, entre outros, Processo 1196195, arquivo e página 5;
- índice geral reconstruído com 666 arquivos Markdown.

## Limitações e revisão humana

- Os campos estruturados de irregularidades reconhecidas não foram inferidos automaticamente: os
  cinco itens da amostra ficaram não identificados, explicando os 10% de erro e exigindo revisão.
- Classificação de relevância, ementa, objeto e resultado é triagem conservadora, não parecer jurídico.
- Voto vencido, unidade técnica, contraditório, divergência, superação e compatibilidade temporal
  exigem leitura humana do inteiro teor.
- Os 198 documentos incidentais permanecem catalogados, mas fora da busca padrão.
- O validador geral da base ainda acusa dez arquivos alheios ao Modo Auditor sem frontmatter: oito em
  `05_minutas/DECLARACAO_UNIFICADA/` e `05_minutas/PROPOSTA_COMERCIAL/`, um em
  `06_precedentes_camara/analises_manuais/` e um em `99_testes/aviso_completo/`. Eles já estavam no
  worktree e não foram alterados para evitar interferência em trabalho do usuário.

## Evidências principais

- Preservação: `03_jurisprudencia/tce_mg/contratacao_direta/relatorios_processamento/RELATORIO_PRESERVACAO_ORIGINAIS.md`.
- Validação humana: `03_jurisprudencia/tce_mg/contratacao_direta/relatorios_processamento/RELATORIO_VALIDACAO_AMOSTRAL.md`.
- Manifesto: `03_jurisprudencia/tce_mg/contratacao_direta/indices/manifesto_originais.jsonl`.
- Exemplo: `99_testes/auditor_tcemg/exemplo_auditoria/RELATORIO_AUDITORIA_EXEMPLO.md`.
