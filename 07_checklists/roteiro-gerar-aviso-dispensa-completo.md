---
tipo: checklist
hierarquia: oficial
tema: roteiro do aviso de dispensa completo
fonte: base Charles
orgao: camara municipal de itanhandu
versao: 1.0
vigencia: vigente
atualizado_em: 2026-07-25
tags: [checklist, roteiro, aviso, anexos, dispensa, contratacao-direta]
---

# Roteiro — Gerar o Aviso de Dispensa Completo

Reúne, valida, numera, formata e monta em um único documento o Aviso de Contratação
Direta e todos os seus anexos aplicáveis, além dos anexos separados e do pacote de
publicação.

Regras inegociáveis: [`regras-aviso-dispensa-completo.md`](regras-aviso-dispensa-completo.md).
Composição das minutas: [`05_minutas/AVISO_COMPLETO/AVISO_COMPLETO_FICHA_DE_USO.md`](../05_minutas/AVISO_COMPLETO/AVISO_COMPLETO_FICHA_DE_USO.md).

---

## 1. Quando usar

Comandos que disparam este roteiro:

- "Charles, gere o Aviso de Dispensa Completo deste processo."
- "Charles, junte o aviso, habilitação, TR, proposta e declaração conjunta."
- "Charles, inclua também a minuta de contrato no aviso."
- "Charles, nesta contratação será usada ordem de fornecimento; não inclua contrato."
- "Charles, audite os anexos antes de montar o aviso."
- "Charles, gere o documento único e também os anexos separados."
- "Charles, verifique se o modelo de proposta corresponde aos itens do TR."

Pressuposto: a dispensa é **com aviso** (art. 75, §3º; Portaria nº 06/2024, arts. 5º-6º).
Sem aviso, a ausência se justifica na justificativa de contratação direta, e este roteiro
não se aplica.

---

## 2. Antes de montar: o manifesto

A entrada é o `manifesto_aviso_completo.json`, na pasta do processo:

```json
{
  "processo": {
    "numero": "000/2026",
    "dispensa": "000/2026",
    "objeto": "...",
    "criterio_julgamento": "MENOR PREÇO POR ITEM",
    "fundamento_legal": "art. 75, inciso II, da Lei nº 14.133/2021"
  },
  "recebimento_propostas": {
    "data_inicio": "AAAA-MM-DD", "hora_inicio": "08:00",
    "data_fim": "AAAA-MM-DD",   "hora_fim": "17:00",
    "email": "compras@itanhandu.cam.mg.gov.br",
    "aceita_protocolo_fisico": true
  },
  "arquivos": {
    "aviso_minuta": "05_minutas/AVISO/AVISO_CONTRATACAO_DIRETA_MINUTA_MAE.docx",
    "termo_referencia": "08_processos_em_andamento/.../03_TR/TR_FINAL.docx",
    "contrato": null
  },
  "instrumento_contratual": {
    "tipo": "contrato | ordem_fornecimento | nota_empenho | autorizacao_fornecimento | outro",
    "incluir_minuta_no_aviso": false,
    "minuta_selecionada": null
  },
  "assinatura": { "nome": "...", "cargo": "...", "data": "AAAA-MM-DD" }
}
```

O bloco `instrumento_contratual` é obrigatório: sem ele a montagem para, porque o Charles
não decide sozinho se haverá contrato.

---

## 3. Auditar antes (recomendado)

```bash
python scripts/aviso_completo/validar_aviso_completo.py \
  --processo 08_processos_em_andamento/PA_XXX_2026/ --somente-auditoria
```

Nada é gravado. Confere localização das peças, correspondência do TR com o processo,
datas, prazo mínimo, numeração dos anexos e divergências de habilitação.

---

## 4. Montar

```bash
python scripts/aviso_completo/montar_aviso_completo.py \
  --processo 08_processos_em_andamento/PA_XXX_2026/
```

Por caminhos avulsos:

```bash
python scripts/aviso_completo/montar_aviso_completo.py \
  --manifesto manifesto_aviso_completo.json \
  --aviso 05_minutas/AVISO/AVISO_CONTRATACAO_DIRETA_MINUTA_MAE.docx \
  --tr caminho/TR_FINAL.docx \
  --contrato 05_minutas/CONTRATO_COMPRAS/CONTRATO_COMPRAS_ENTREGA_FORN_CONTINUO_MINUTA_MAE.docx \
  --incluir-contrato --saida caminho/07_AVISO_COMPLETO/
```

Opções úteis: `--sem-contrato` (instrumento equivalente) · `--sem-pdf` ·
`--sem-pacote` · `--sem-padronizacao` · `--autorizar-tr-rascunho` ·
`--rascunho-com-pendencias`.

---

## 5. Fluxo executado

1. Ler o manifesto do processo.
2. Localizar a minuta-mãe do aviso.
3. Ler a ficha de uso da minuta.
4. Localizar o TR final.
5. Validar se o TR pertence ao mesmo processo.
6. Extrair objeto, itens, unidades e quantidades do TR.
7. Preencher o aviso principal.
8. Preparar o Anexo I de habilitação (recorte da própria minuta).
9. Gerar o Modelo de Proposta a partir dos itens do TR.
10. Verificar se haverá contrato.
11. Localizar e preparar a minuta de contrato, quando aplicável.
12. Preparar a Declaração Conjunta.
13. Definir a numeração dos anexos.
14. Atualizar a relação de anexos no aviso (quando a minuta a tiver).
15. Montar um único DOCX.
16. Aplicar a padronização documental (perfil `aviso`, sem renumerar).
17. Executar a validação cruzada.
18. Gerar relatório.
19. Converter para PDF, quando houver ferramenta disponível.
20. Gerar anexos individuais.
21. Criar pacote ZIP para publicação.

---

## 6. Saída

```
08_processos_em_andamento/[PROCESSO]/07_AVISO_COMPLETO/
├── componentes/
│   ├── 00_AVISO.docx
│   ├── 01_DOCUMENTOS_EXIGIDOS_PARA_HABILITACAO.docx
│   ├── 02_TERMO_DE_REFERENCIA.docx
│   ├── 03_MODELO_DE_PROPOSTA_COMERCIAL.docx
│   ├── 04_MINUTA_DE_CONTRATO.docx        (quando houver)
│   └── 0N_DECLARACAO_CONJUNTA.docx
├── saida/
│   ├── AVISO_DISPENSA_COMPLETO.docx
│   ├── AVISO_DISPENSA_COMPLETO.pdf       (quando houver conversor)
│   ├── anexos_separados/
│   ├── MANIFESTO_ARQUIVOS.json
│   └── PACOTE_PUBLICACAO.zip
├── relatorios/
│   ├── VALIDACAO_AVISO_COMPLETO.md
│   └── VALIDACAO_AVISO_COMPLETO.json
└── manifesto_aviso_completo.json
```

---

## 7. Ler o relatório

Status possíveis:

| Status | Significado |
| --- | --- |
| APTO PARA CONFERÊNCIA | melhor resultado da automação; segue para conferência humana |
| APTO COM RESSALVAS | gerado, com alertas ou pendências humanas a resolver |
| RASCUNHO — NÃO PUBLICAR | gerado a pedido expresso, com pendência conhecida e marca d'água |
| BLOQUEADO | há erro bloqueante; o documento final não foi produzido |
| APTO PARA PUBLICAÇÃO | **não é concedido automaticamente** — depende de conferência humana |

Erros que bloqueiam: TR não localizado ou de outro processo; marcador `{{...}}` ou
`[PREENCHER]` remanescente; bloco "OU" não resolvido; item ou quantidade divergente entre
proposta e TR; processo ou dispensa divergente; datas inválidas; prazo abaixo de 3 dias
úteis; minuta de contrato indefinida ou inadequada; referência a anexo inexistente;
numeração duplicada; perda de conteúdo; perda de cabeçalho ou rodapé; documento
corrompido.

---

## 8. Depois de montar

1. **Confira o documento** — a validação automática não lê o mérito administrativo.
2. Resolva as pendências humanas listadas no relatório.
3. Divulgue no sítio oficial e, quando aplicável, no PNCP (Portaria nº 06/2024, art. 6º).
4. Confira o prazo de 3 dias úteis contra o **calendário local** — o cálculo automático
   não conhece feriados municipais.
5. Concluída a contratação, atualize o controle de contratações por CNAE
   (`scripts/controle_cnae.py`).
