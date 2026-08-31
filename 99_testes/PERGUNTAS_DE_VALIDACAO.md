---
tipo: checklist
hierarquia: operacional
tema: perguntas de validacao
fonte: base Charles
vigencia: vigente
atualizado_em: 2026-07-01
tags: [testes, validacao, anti-alucinacao, qualidade]
---

# Perguntas de validação

O gabarito estruturado oficial está em `99_testes/casos_validacao.yaml`.

Use este Markdown como documentação do fluxo:

1. Rode `python scripts/validar_respostas.py --casos 99_testes/casos_validacao.yaml`.
2. Para cada pergunta, forneça a resposta do Charles por arquivo, stdin ou modo headless.
3. O runner confere `deve_conter`, `nao_pode_conter`, `nao_pode_conter_regex` e
   `fontes_esperadas`.
4. Falha no gabarito indica necessidade de revisar a base, a resposta ou as instruções do
   `CLAUDE.md`/`AGENTS.md`.

Regra permanente: estes testes existem para impedir alucinação jurídica, geração fora das
minutas oficiais e julgamento sem documento-fonte.

## Cenários obrigatórios do Modo Auditor

Os cenários estruturados estão em `99_testes/auditor_tcemg/cenarios_modo_auditor.yaml` e são
verificados pela suíte `test_auditor_tcemg.py`:

1. processo incompleto — inventariar e limitar a conclusão;
2. documentos ilegíveis — criar fila de OCR/revisão sem inventar conteúdo;
3. recebimento de uma proposta — não declarar irregularidade automaticamente;
4. pesquisa de preços fraca — testar fontes, comparabilidade, memória e justificativa;
5. indícios de fracionamento — exigir CNAE, unidade gestora, exercício e somatório;
6. inexigibilidade mal justificada — separar inviabilidade, escolha e preço;
7. julgados divergentes — apresentar ambos, regime, tempo e limites de aplicação.
