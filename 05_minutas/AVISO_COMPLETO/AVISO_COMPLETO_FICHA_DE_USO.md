---
tipo: minuta
hierarquia: oficial
documento: aviso de dispensa completo (aviso + anexos)
tema: contratacao direta
fonte: Câmara Municipal de Itanhandu / composição das minutas-mãe já cadastradas
orgao: camara municipal de itanhandu
uso: montagem do aviso de contratação direta com todos os anexos aplicáveis
versao: 1.0
vigencia: vigente
atualizado_em: 2026-07-25
tags: [minuta, aviso, anexos, dispensa, contratacao-direta, art-75, montagem]
---

# Ficha de Uso — Aviso de Dispensa Completo

Esta pasta **não contém minuta-mãe própria**. Ela documenta a **composição** do aviso
completo a partir das minutas oficiais que já existem na biblioteca.

> **Por que não há DOCX aqui.** Criar `ANEXO_I_HABILITACAO_MINUTA_MAE.docx`,
> `MODELO_PROPOSTA_MINUTA_MAE.docx` e `DECLARACAO_CONJUNTA_MINUTA_MAE.docx` nesta pasta
> duplicaria conteúdo oficial que já está cadastrado — e duplicata de minuta é a origem
> clássica de divergência entre versões (uma é revisada, a outra não, e o processo sai com
> a errada). O `_CONTROLE_MINUTAS.md` e o `CLAUDE.md` proíbem duplicar conteúdo: havendo
> sobreposição, referencia-se o arquivo existente. É o que esta ficha faz.

---

## 1. Componentes do aviso completo

| Anexo | Conteúdo | Minuta-mãe oficial |
| --- | --- | --- |
| — | Aviso de Contratação Direta | [`AVISO/AVISO_CONTRATACAO_DIRETA_MINUTA_MAE.docx`](../AVISO/AVISO_CONTRATACAO_DIRETA_MINUTA_MAE.docx) |
| I | Documentos exigidos para habilitação | **já incorporado** à minuta do aviso (ver ficha própria) |
| II | Termo de Referência | **não é minuta**: é o TR já elaborado e aprovado no processo |
| III | Modelo de Proposta Comercial | [`PROPOSTA_COMERCIAL/PROPOSTA_COMERCIAL_MINUTA_MAE.docx`](../PROPOSTA_COMERCIAL/PROPOSTA_COMERCIAL_MINUTA_MAE.docx) |
| IV* | Minuta de contrato (quando houver) | `CONTRATO/`, `CONTRATO_COMPRAS/`, `CONTRATO_SERVICOS_CONTINUOS/` |
| IV/V | Declaração conjunta | [`DECLARACAO_UNIFICADA/DECLARACAO_UNIFICADA_MINUTA_MAE.docx`](../DECLARACAO_UNIFICADA/DECLARACAO_UNIFICADA_MINUTA_MAE.docx) |

\* Só entra quando o processo decidir pelo Termo de Contrato. Sem contrato, a declaração
é o **Anexo IV**; com contrato, é o **Anexo V**. Não fica lacuna na numeração.

Fichas dos componentes nesta pasta: [Anexo I](ANEXO_I_HABILITACAO_FICHA_DE_USO.md) ·
[Modelo de Proposta](MODELO_PROPOSTA_FICHA_DE_USO.md) ·
[Declaração Conjunta](DECLARACAO_CONJUNTA_FICHA_DE_USO.md).

---

## 2. Como gerar

Comando do Charles: **"Charles, gere o Aviso de Dispensa Completo deste processo."**

Roteiro operacional: [`07_checklists/roteiro-gerar-aviso-dispensa-completo.md`](../../07_checklists/roteiro-gerar-aviso-dispensa-completo.md).
Regras inegociáveis: [`07_checklists/regras-aviso-dispensa-completo.md`](../../07_checklists/regras-aviso-dispensa-completo.md).

```bash
python scripts/aviso_completo/montar_aviso_completo.py --processo 08_processos_em_andamento/PA_XXX_2026/
```

---

## 3. O que a montagem preenche

Do aviso: `{{NUMERO_AVISO}}`, `{{CRITERIO_JULGAMENTO}}`, `{{FUNDAMENTO_LEGAL}}`,
`{{DATA_INICIO_PROPOSTAS}}`, `{{DATA_FIM_PROPOSTAS}}`, `{{OBJETO}}`, `{{DATA}}`,
`{{NOME_PRESIDENTE}}` — todos vindos do `manifesto_aviso_completo.json`.

Dos anexos: apenas a identificação do processo, do aviso e do objeto, além dos itens do
quadro do TR no modelo de proposta. **Preço, marca e dados do fornecedor nunca são
preenchidos** — ficam como lacuna destinada ao proponente.

---

## 4. O que NÃO alterar

Timbre, brasão, cabeçalho, rodapé, estrutura, ordem das seções, cláusulas fixas,
numeração de artigos/incisos/cláusulas, bloco de assinatura e o conteúdo do Termo de
Referência. A montagem acrescenta **somente** o rótulo de cada anexo (ex.: "ANEXO II —
TERMO DE REFERÊNCIA") e a quebra de página que o inicia.

---

## 5. Limitações conhecidas

- A minuta-mãe do aviso **não traz relação de anexos** no corpo ("ANEXO I — ..., ANEXO II
  — ..."). A montagem numera e rotula os anexos, mas não inventa essa relação: incluí-la
  exige revisão expressa da minuta-mãe. A ausência é reportada como pendência.
- O Anexo I conserva o título que a minuta já traz em caixa de texto
  ("DOCUMENTAÇÃO EXIGIDA PARA HABILITAÇÃO") e não recebe o rótulo "ANEXO I — ...", para
  não duplicar título. Uniformizar depende de revisão da minuta-mãe.
- ~~As minutas de proposta e de declaração têm cabeçalho de geração diferente da do aviso.~~
  **Resolvido na v1.1 dessas minutas (26/07/2026):** elas não exibiam timbre algum — o
  cabeçalho e o rodapé estavam no pacote, mas o `sectPr` não os referenciava. As duas
  passaram a usar o timbre oficial do aviso. Ver os changelogs de
  [`PROPOSTA_COMERCIAL/`](../PROPOSTA_COMERCIAL/PROPOSTA_COMERCIAL_CHANGELOG.md) e
  [`DECLARACAO_UNIFICADA/`](../DECLARACAO_UNIFICADA/DECLARACAO_UNIFICADA_CHANGELOG.md).

---

## 6. Fontes prioritárias

1. Lei nº 14.133/2021 (art. 75, §3º; art. 5º)
2. Portaria nº 06/2024 da Câmara (arts. 1º, 2º, 5º, 6º)
3. Demais normas internas
4. Minutas oficiais desta biblioteca
