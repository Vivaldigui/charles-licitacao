---
tipo: checklist
hierarquia: operacional
tema: plano de implementacao do modo auditor tce-mg
fonte: diagnostico local do repositorio Charles
vigencia: vigente
atualizado_em: 2026-07-31
tags: [modo-auditor, tce-mg, implementacao, diagnostico]
---

# Plano de implementação — Modo Auditor de Contratações Diretas

## 1. Diagnóstico do repositório

O repositório já contém a base jurídica do Charles, minutas-mãe, checklists, scripts em Python,
testes e processos/precedentes locais. A implementação será aditiva: não substituirá a arquitetura
existente, não alterará minutas-mãe e preservará as alterações locais já existentes no worktree.

Pontos de integração identificados:

- `CLAUDE.md` e `AGENTS.md`: regras de comportamento jurídico e de desenvolvimento;
- `00_indices/`: índice geral e mapas por tema/modalidade;
- `03_jurisprudencia/tce_mg/`: duas fichas/estudos já existentes;
- `07_checklists/modo-auditor.md`: roteiro inicial, a ser preservado e ampliado;
- `scripts/`: ferramentas majoritariamente stdlib, com CLIs via `argparse` e códigos de saída;
- `scripts/tests/` e `99_testes/`: testes mecânicos e cenários de validação do comportamento.

## 2. Corpus localizado

Camada bruta existente: `TCE-MG_JULGADOS/`.

| Conjunto | PDFs | Índice/apoio |
|---|---:|---|
| `TCE-MG_Contratacao_Direta_2022-07-31_a_2026-07-31` | 26 | JSON, CSV e TXT |
| `TCE-MG_Contratacao_Direta_Inteiro_Teor_2023-01-01_a_2026-07-31` | 555 | JSON, CSV e TXT |
| `TCE-MG_Dispensa_de_Licitacao_Inteiro_Teor_2023-01-01_a_2026-07-31` | 387 | JSON, CSV e TXT |
| **Total bruto** | **968** | **9 arquivos auxiliares** |

Formatos encontrados no corpus: 968 PDFs, 3 JSON, 3 CSV e 3 TXT (977 arquivos no total).
Não foram encontrados HTML, Markdown ou DOCX dentro do corpus bruto, embora o pipeline suporte
esses formatos para ingestões futuras.

## 3. Duplicidades e preservação

O diagnóstico por SHA-256 encontrou 628 hashes únicos entre 968 PDFs, com 256 grupos repetidos e
340 cópias excedentes. Há grupos em que o mesmo binário aparece com nomes de processos distintos;
por isso o pipeline preservará todas as ocorrências como fontes/aliases, sem concluir que os
processos são equivalentes. A deduplicação será física/lógica por hash, nunca exclusão automática.

Os originais permanecerão intocados em `TCE-MG_JULGADOS/`, que será tratado como a camada bruta.
O diretório processado conterá manifesto, hashes e caminhos relativos que provam a associação com
cada original. Não haverá cópia automática de 445 MB nem movimentação dos arquivos de origem.

## 4. Qualidade de extração observada

Uma amostra representativa de cinco PDFs, distribuída entre os três conjuntos, foi extraída com
`pypdf`. Todos eram pesquisáveis, tinham entre 6 e 28 páginas, e não apresentaram páginas vazias.
A conferência visual de uma página confirmou que a página física do PDF coincide com o marcador de
página que será gravado no texto extraído. O processamento integral ainda poderá localizar PDFs
sem texto, corrompidos ou com extração insuficiente; eles serão relatados como pendentes de OCR.

## 5. Arquitetura escolhida

Saída principal: `03_jurisprudencia/tce_mg/contratacao_direta/`.

```text
contratacao_direta/
├── inteiro_teor_bruto/README.md          # ponte rastreável para TCE-MG_JULGADOS
├── texto_extraido/                       # um TXT por documento, com marcadores de página
├── fichas/                               # fichas Markdown geradas sem completar lacunas
├── indices/                              # JSONL, CSV e SQLite/FTS5
├── consolidacoes/                        # consolidações sempre ligadas às fontes
└── relatorios_processamento/             # falhas, OCR, duplicidades e validação
```

O SQLite separará documentos, ocorrências de origem, páginas, metadados, temas, teses, achados,
dispositivos, citações, relações, histórico e revisões humanas. A busca padrão excluirá relevância
incidental/falso positivo, salvo opção expressa.

## 6. Arquivos a criar

- pacote `scripts/auditor_tcemg/` com CLI, ingestão, metadados, banco, busca e relatórios;
- `requirements-auditor.txt`;
- estrutura processada sob `03_jurisprudencia/tce_mg/contratacao_direta/`;
- `07_checklists/roteiro-modo-auditor-contratacao-direta.md`;
- testes em `99_testes/auditor_tcemg/`;
- auditoria de exemplo e pacote de contexto jurisprudencial;
- documentação operacional e relatórios do corpus.

## 7. Arquivos existentes a alterar

- `README.md`;
- `CLAUDE.md`;
- `AGENTS.md` (substituição da cópia atual por instruções de desenvolvimento que referenciem o
  `CLAUDE.md`, preservando as regras locais específicas);
- `00_indices/INDICE_GERAL.md`;
- `00_indices/MAPA_POR_TEMA.md`;
- `00_indices/MAPA_POR_MODALIDADE.md`;
- `07_checklists/modo-auditor.md` (ponte para o roteiro completo);
- `99_testes/PERGUNTAS_DE_VALIDACAO.md` e índice gerado da base, quando aplicável.

Nenhum arquivo em `05_minutas/` será alterado.

## 8. Dependências

- Python 3.9+ e SQLite com FTS5 (confirmado no runtime do workspace);
- `pypdf` somente para extração de PDF, isolado em `requirements-auditor.txt`;
- biblioteca padrão para hash, CSV, JSONL, SQLite, HTML, TXT, Markdown e DOCX;
- `tesseract` opcional, nunca executado indiscriminadamente, apenas para documentos sinalizados e
  quando o usuário/ambiente o disponibilizar.

Não haverá embeddings, API paga ou integração externa com modelo de linguagem.

## 9. Riscos técnicos

- PDFs repetidos com nomes/processos diferentes exigem preservar aliases e impedir colapso indevido;
- extração automática não distingue com segurança voto, defesa, unidade técnica e decisão em todos
  os formatos; campos jurídicos não confirmados permanecerão como `Não identificado no documento`;
- classificação de relevância e temas é triagem mecânica, sujeita a revisão humana;
- OCR pode alterar caracteres e paginação; por isso será opcional e identificado;
- o corpus é grande; processamento será incremental, retomável e idempotente;
- fichas automáticas não serão tratadas como validação jurídica do precedente;
- o worktree já está sujo; qualquer conflito com alterações locais será evitado e relatado.

## 10. Etapas verificáveis

1. Implementar e testar hash, extração, metadados e banco com 3 a 5 documentos.
2. Validar marcadores de página, citações e idempotência da amostra.
3. Processar o corpus completo, sem mover originais.
4. Gerar catálogos, relatórios, fichas e consolidações rastreáveis.
5. Implementar busca e preparação de auditoria.
6. Integrar regras/checklists ao Charles.
7. Executar testes e validação amostral, sem declarar validação humana onde ela não ocorreu.

## 11. Critérios de aceite técnicos

- inventário completo e SHA-256 para cada ocorrência;
- originais sem alteração (hash antes/depois em amostra e manifesto do corpus);
- extração por página ou status explícito de falha/OCR;
- catálogos JSONL/CSV e SQLite FTS5 consistentes;
- busca com arquivo, página, trecho, score e filtros;
- fichas sem dados presumidos e sem duplicação na reexecução;
- pacote de contexto que registra resultados selecionados e descartados;
- testes automatizados dos casos mecânicos e dos sete cenários anti-alucinação;
- documentação Windows e códigos de saída claros;
- limitações e pendências de revisão humana explicitadas.
