---
tipo: checklist
hierarquia: oficial
tema: padronizacao e formatacao documental
fonte: base Charles
orgao: camara municipal de itanhandu
versao: 1.0
vigencia: vigente
atualizado_em: 2026-07-25
tags: [checklist, padronizacao, formatacao, docx, minutas]
---

# Roteiro — Padronização e Formatação Documental

Roteiro operacional do Charles quando o usuário pede documento **bem formatado**,
auditoria de formatação ou revisão do padrão visual.

Regras que não podem ser flexibilizadas: [`regras-padronizacao-documental.md`](regras-padronizacao-documental.md).
Padrão visual: [`09_padronizacao_documental/PADRAO_VISUAL_DOCUMENTOS.md`](../09_padronizacao_documental/PADRAO_VISUAL_DOCUMENTOS.md).

---

## 0. Antes de qualquer coisa

- [ ] `python-docx` instalado? Se não: `python -m pip install -r requirements-docx.txt`.
- [ ] Identificou o **tipo** de documento e, portanto, o **perfil**?
- [ ] Sabe qual é a **minuta-mãe** de referência (`05_minutas/<TIPO>/`)?
- [ ] Leu a **ficha de uso** (`*_FICHA_DE_USO.md`) da minuta?

---

## 1. Fluxo padrão — gerar documento novo já formatado

1. **Localizar a minuta-mãe** em `05_minutas/`. Não existe minuta adequada?
   **Pare e avise.** Não improvise modelo (regra do `_CONTROLE_MINUTAS.md`).
2. **Criar cópia de trabalho** em `08_processos_em_andamento/<PROCESSO>/`.
   Sufixo `_PREENCHIDO_RASCUNHO.docx`.
3. **Preencher os campos** `{{CAMPO}}`, com `--campos campos.json`. A substituição
   preserva a formatação mesmo com o marcador quebrado entre *runs*.
4. **Resolver blocos alternativos "OU"** e opções `( )`, conforme a ficha de uso.
   Sem decisão possível, deixar `[PREENCHER: ...]` e registrar como pendência.
5. **Executar a auditoria estrutural** (`--somente-auditoria`) e ler o diagnóstico.
6. **Corrigir a numeração**, se necessário e seguro:
   `--corrigir-numeracao --validar-referencias-internas`.
7. **Aplicar os estilos padronizados** com o perfil correto.
8. **Ajustar tabelas e paginação** — automático no pipeline.
9. **Validar a preservação do conteúdo** — automático; a saída é bloqueada se falhar.
10. **Gerar o documento final** com sufixo `_FORMATADO.docx`.
11. **Gerar o relatório** `_FORMATADO_RELATORIO.md` + `.json`.

Comando único que cobre 3 a 11:

```bash
python scripts/docx_cmi/formatar_docx.py \
  --entrada 08_processos_em_andamento/PROCESSO_X/TR_PREENCHIDO_RASCUNHO.docx \
  --saida  08_processos_em_andamento/PROCESSO_X/TR_PREENCHIDO_FORMATADO.docx \
  --perfil tr \
  --minuta-mae 05_minutas/TR/TR_MINUTA_MAE.docx \
  --campos 08_processos_em_andamento/PROCESSO_X/campos.json \
  --preservar-conteudo
```

---

## 2. Fluxo de auditoria — "audite a formatação deste documento"

```bash
python scripts/docx_cmi/auditar_docx.py \
  --entrada documento.docx --perfil contrato \
  --minuta-mae 05_minutas/CONTRATO/CONTRATO_MINUTA_MAE.docx \
  --saida-relatorio 09_padronizacao_documental/relatorios/contrato_auditoria.md
```

O documento **não** é alterado. Ao relatar, separe sempre:
- o que pode ser corrigido automaticamente;
- o que exige avaliação humana;
- campos pendentes;
- pontos que dependem de análise jurídica.

---

## 3. Fluxo de revisão de minuta-mãe — só com pedido expresso

Aplicável apenas quando o usuário pedir, com todas as letras: revisão da minuta-mãe,
repadronização da biblioteca, alteração do padrão visual oficial, correção definitiva
da numeração da minuta ou atualização do modelo oficial.

```bash
python scripts/docx_cmi/formatar_docx.py \
  --entrada 05_minutas/TR/TR_MINUTA_MAE.docx --revisar-minuta-mae --perfil tr
```

Depois, **manualmente**:
- [ ] atualizar `05_minutas/_CONTROLE_MINUTAS.md` com a nova versão;
- [ ] conferir visualmente o DOCX resultante no Word;
- [ ] confirmar que o backup ficou em `05_minutas/<TIPO>/_arquivo/`.

---

## 4. Lote — formatar todos os documentos de um processo

```bash
python scripts/docx_cmi/formatar_docx.py \
  --diretorio 08_processos_em_andamento/PROCESSO_X/ \
  --saida-diretorio 08_processos_em_andamento/PROCESSO_X/documentos_formatados/
```

Os originais não são tocados. Cada documento gera o seu relatório.

---

## 5. Checklist de conclusão — antes de dizer que o documento está pronto

- [ ] Status do relatório conferido (e **não** é `BLOQUEADO`).
- [ ] Conteúdo preservado: `SIM`.
- [ ] Partes protegidas (cabeçalho/rodapé/mídia) intactas: `SIM`.
- [ ] Idempotência: `OK`.
- [ ] **Zero** campos pendentes — ou eles foram informados ao usuário, um a um.
- [ ] Nenhum bloco `OU` sem resolução e nenhuma opção `( )` sem marcação.
- [ ] Nenhum comentário interno e nenhuma revisão pendente no arquivo entregue.
- [ ] Numeração conferida; referências internas ("conforme o item 6") coerentes.
- [ ] Tabelas dentro da margem e com cabeçalho repetido.
- [ ] Nenhum título isolado no fim de página (**depende de conferência visual**).
- [ ] Validação visual: executada, ou **declarada como não executada**.

---

## 6. O que responder ao usuário

Sempre nesta estrutura:

**Documento gerado** — tipo · minuta-mãe utilizada · arquivo original · arquivo
formatado · perfil visual aplicado.

**Padronizações aplicadas** — fontes · tamanhos · títulos · numeração · espaçamento ·
tabelas · paginação.

**Validações** — conteúdo preservado · cabeçalho preservado · rodapé preservado ·
marcadores restantes · campos pendentes · necessidade de conferência humana.

**Nunca** afirme que o documento está perfeito quando houver pendência ou quando a
conferência visual não tiver sido feita. Se a validação visual não rodou, diga.

---

## 7. Comandos em linguagem natural que acionam este roteiro

- "gere o TR e aplique o padrão visual institucional"
- "formate este documento sem alterar seu conteúdo"
- "corrija a numeração e padronize as fontes"
- "audite a formatação deste contrato"
- "deixe o documento pronto para assinatura"
- "verifique se há campos pendentes ou comentários internos"
- "compare a formatação deste documento com a minuta-mãe"
- "gere o documento em DOCX e execute a validação de formatação"
