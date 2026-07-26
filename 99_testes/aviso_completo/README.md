---
tipo: checklist
hierarquia: operacional
tema: testes do aviso de dispensa completo
fonte: base Charles
orgao: camara municipal de itanhandu
versao: 1.0
vigencia: vigente
atualizado_em: 2026-07-25
tags: [testes, aviso, anexos, dispensa, docx]
---

# Testes — Aviso de Dispensa Completo

```bash
python -m pip install -r requirements-docx.txt
python -m pytest 99_testes/aviso_completo/ -v
```

Cobrem os 25 testes obrigatórios do escopo, mais as regras que não podem regredir
(não gravar em `05_minutas/`, prazo mínimo de 3 dias úteis, exigência negada no TR
não virar divergência, e `APTO PARA PUBLICAÇÃO` nunca sair automaticamente).

Os testes marcados `slow` dependem de ferramenta externa (Word ou LibreOffice) e são
**pulados** — não falsamente aprovados — quando ela não existe no ambiente.

---

## `fixtures/`

| Arquivo | O que é |
| --- | --- |
| `TR_FINAL.docx` | TR de exemplo, derivado de um TR real da Câmara com os campos pendentes preenchidos com dados de teste |
| `manifesto_aviso_completo.json` | processo de exemplo **sem** contrato (ordem de fornecimento) |
| `manifesto_com_contrato.json` | mesmo processo **com** minuta de contrato |

> São **dados de teste**, não processo real da Câmara. O número de processo (026/2026) e
> a dispensa (011/2026) existem apenas para exercitar a validação cruzada.

---

## `exemplo/`

Aviso completo de exemplo, gerado por:

```bash
python scripts/aviso_completo/montar_aviso_completo.py \
  --manifesto 99_testes/aviso_completo/fixtures/manifesto_aviso_completo.json \
  --saida 99_testes/aviso_completo/exemplo
```

Versionados: o relatório de validação (`.md` e `.json`) e o `MANIFESTO_ARQUIVOS.json`.
Os DOCX, PDF e ZIP ficam fora do Git — são alguns megabytes e o comando acima os
reproduz a qualquer momento.

Resultado esperado desta execução: **APTO COM RESSALVAS**, sem erro bloqueante, com
duas ressalvas de timbre (as minutas de proposta e declaração têm cabeçalho de geração
diferente da do aviso) e uma pendência humana (a minuta-mãe do aviso não traz relação
de anexos no corpo).
