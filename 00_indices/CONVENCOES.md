---
tipo: checklist
hierarquia: operacional
tema: convencoes da base
fonte: base Charles
vigencia: vigente
atualizado_em: 2026-07-01
tags: [convencoes, frontmatter, indices, versionamento, nomenclatura]
---

# Convenções da base Charles

## Nomenclatura

- Fichas Markdown: `kebab-case.md`.
- Minutas-mãe: `TIPO_MINUTA_MAE.docx`.
- Fichas de uso: `TIPO_FICHA_DE_USO.md`.
- Changelog de minuta: `05_minutas/<TIPO>/<TIPO>_CHANGELOG.md`.
- Artigos: `artigo-<tema>.md`.
- Consultas de tribunal: `consulta-tcemg-NNNNNNN-<tema>.md` ou prefixo equivalente do órgão.
- Arquivos de processo real ficam em `08_processos_em_andamento/` e não entram no versionamento,
  salvo `08_processos_em_andamento/_MODELO/`.

## Frontmatter obrigatório

```yaml
---
tipo: lei | norma_interna | jurisprudencia | doutrina | minuta | precedente | checklist
hierarquia: oficial | interpretativa | operacional
tema: [tema principal]
fonte: [origem / autor / órgão]
vigencia: vigente | revogado | alterado
atualizado_em: AAAA-MM-DD
tags: [ ... ]
---
```

## Hierarquia

- `oficial`: legislação, normas internas e fichas de minutas oficiais.
- `interpretativa`: jurisprudência, doutrina e artigos.
- `operacional`: índices, precedentes, checklists, testes e modelos de processo.

## Versionamento de minutas

- Alteração em DOCX de minuta-mãe exige aumento de versão na ficha de uso.
- A versão anterior do DOCX deve ir para `05_minutas/<TIPO>/_arquivo/<nome>_vX.Y.docx`.
- O changelog da pasta deve receber nova entrada com data, versão, mudança e motivo.
- O Charles não altera DOCX de minuta-mãe sem comando expresso e validação humana.

## Atualização de índices

Após criar ou alterar fichas Markdown:

1. Atualizar mapas humanos em `00_indices/`, quando necessário.
2. Rodar `python scripts/indexar_base.py`.
3. Rodar `python scripts/validar_base.py`.
4. Conferir citações no arquivo-fonte; `BASE_INDEXADA.json` é ponto de partida, não fonte final
   para citação jurídica.

