---
tipo: checklist
hierarquia: operacional
tema: rotina semanal de manutencao do Charles
fonte: base Charles
vigencia: vigente
atualizado_em: 2026-08-03
tags: [rotina, semanal, manutencao, validacao, git, obsidian]
---

# Rotina semanal de manutenção do Charles

- [ ] Executar `python scripts/validar_base_obsidian.py`.
- [ ] Executar `python scripts/gerar_relatorio_base.py`.
- [ ] Revisar links internos quebrados e referências a arquivos inexistentes.
- [ ] Revisar fontes desatualizadas, alteradas, revogadas ou sem origem clara no [[00_indices/PAINEL_FONTES]].
- [ ] Revisar processos sem próxima ação, responsável ou prazo.
- [ ] Atualizar os índices quando houver nova ficha, checklist ou fonte.
- [ ] Verificar arquivos duplicados pelo nome antes de concluir que são duplicatas de conteúdo.
- [ ] Revisar [[06_precedentes_camara/CONTROLE_CONTRATACOES|controle por CNAE]], enquadramentos não confirmados e alertas de possível fracionamento.
- [ ] Conferir se alguma minuta oficial foi alterada e, se houve pedido expresso de revisão, verificar backup, versão, changelog e validação.
- [ ] Executar `git status` e conferir `git diff`/`git diff --no-index` conforme o estado do repositório.
- [ ] Preparar seleção de arquivos para commit somente após revisão humana; não fazer `push` automaticamente.
- [ ] Confirmar que nenhum documento pessoal, proposta, processo real, credencial ou arquivo de `_entrada` será incluído.

> [!note]
> O relatório gerado é local e ignorado pelo Git. Ocorrência automática é sinal para revisão, não
> correção jurídica automática.

