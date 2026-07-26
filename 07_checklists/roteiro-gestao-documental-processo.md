---
tipo: checklist
hierarquia: operacional
tema: gestao documental dos processos em andamento
fonte: base Charles
vigencia: vigente
atualizado_em: 2026-07-25
tags: [gestao documental, roteiro, versionamento, processos]
---

# Roteiro — Gestão Documental do Processo

Roteiro operacional do módulo. As regras de conduta estão em
`regras-gestao-documental-processo.md`; o detalhamento técnico, em
`10_gestao_documental/`.

---

## 0. Antes de qualquer coisa: onde o processo mora

```bash
python scripts/gestao_documental/seguranca_repositorio.py --diagnostico
```

`CHARLES_PROCESSOS_DIR` configurada? Se não, **avise o usuário** antes de criar
processo real: sem ela, os arquivos cairiam dentro do repositório.

---

## 1. "Charles, crie a pasta organizada deste novo processo"

```bash
python scripts/gestao_documental/iniciar_processo.py \
  --numero "PA 031/2026" \
  --objeto "Aquisição de material de limpeza" \
  --setor "Setor de Compras" \
  --fundamento "art. 75, II, da Lei 14.133/2021" \
  --instrumento ordem_fornecimento
```

Informe ao usuário: caminho criado, que a lista de documentos obrigatórios é
**sugestão** a confirmar na esteira, e onde ficam os arquivos.

---

## 2. "Charles, gere o TR e substitua a versão atual"

1. Gere o documento a partir da minuta-mãe de `05_minutas/` — a geração continua
   travada nas minutas.
2. Aplique o perfil documental, se for o caso (`scripts/docx_cmi/`).
3. **Registre pela interface única**, nunca salvando na pasta à mão:

```bash
python scripts/gestao_documental/registrar_documento.py \
  --processo PA_031_2026 --tipo TR --arquivo <arquivo gerado> \
  --minuta-origem 05_minutas/TR/TR_MINUTA_MAE.docx \
  --motivo "Atualização dos requisitos"
```

Leia o resultado e **repasse-o com fidelidade**:

- `registrado` → versão nova; diga qual, e onde ficou a anterior;
- `sem_alteracao` → **não houve versão nova**; diga isso, não invente melhoria;
- campos pendentes → liste-os; eles impedem "pronto para assinatura";
- "NÃO VERIFICADO" → repita a ressalva; não converta em aprovação.

Para substituir documento já existente, prefira `substituir_documento.py`, que
exige motivo.

---

## 3. "Charles, promova o TR para aprovado"

```bash
python scripts/gestao_documental/promover_documento.py \
  --processo PA_031_2026 --tipo TR --status aprovado --responsavel "<nome>"
```

- Sem responsável identificado, **pergunte**: promoção sem responsável não se faz.
- Recusa por campo pendente: liste os campos e pare.
- Ressalvas (comentários, controle de alterações): apresente-as ao usuário e só
  repita com `--ignorar-avisos` se ele assumir expressamente.

Assinatura e publicação:

```bash
# assinado — exige o arquivo assinado
python scripts/gestao_documental/promover_documento.py \
  --processo PA_031_2026 --tipo TR --status assinado --arquivo TR_assinado.pdf

# publicado
python scripts/gestao_documental/promover_documento.py \
  --processo PA_031_2026 --tipo AVISO --status publicado --veiculo PNCP
```

---

## 4. "Charles, importe estas propostas"

```bash
python scripts/gestao_documental/importar_documento_externo.py \
  --processo PA_031_2026 --arquivo proposta1.pdf --arquivo proposta2.pdf \
  --fonte email
```

Ao relatar:

- `classificado` → diga a categoria, o nome padronizado e as pendências;
- `duplicado` → diga que **nada foi copiado** e aponte o arquivo existente;
- `em_quarentena` → explique por quê (outro processo? classificação incerta?) e
  peça a confirmação humana. Não force a classificação por conta própria.

PDF: lembre que o texto **não foi lido**; a classificação veio do nome.

---

## 5. "Charles, mostre os documentos atuais" / "o histórico do TR"

```bash
python scripts/gestao_documental/gerar_painel.py --processo PA_031_2026 --mostrar
python scripts/gestao_documental/restaurar_versao.py --processo PA_031_2026 --tipo TR --listar
```

---

## 6. "Charles, restaure a versão 2 do DFD"

```bash
python scripts/gestao_documental/restaurar_versao.py \
  --processo PA_031_2026 --tipo DFD --versao 2 --motivo "<motivo>"
```

Explique ao usuário que a versão restaurada vira uma versão **nova** e que a
atual foi para o histórico — o contador não retrocede.

---

## 7. "Charles, organize a pasta antiga sem apagar nada"

**Sempre em dois tempos.**

```bash
# 1) plano — não move nada
python scripts/gestao_documental/migrar_processo.py \
  --origem "<pasta antiga>" --destino PA_031_2026 \
  --somente-planejar --plano plano.json --relatorio relatorio_migracao.md
```

Apresente o relatório inteiro e **espere confirmação**. Havendo
`BLOQUEADO POR AMBIGUIDADE`, mostre as ambiguidades e peça a escolha
(`--escolher TIPO=<arquivo>`). Não use `--forcar` por iniciativa própria.

```bash
# 2) execução
python scripts/gestao_documental/migrar_processo.py \
  --origem "<pasta antiga>" --destino PA_031_2026 --executar
```

Depois, informe: quantidade conferida, pasta original preservada como backup, e
o que ficou em quarentena.

---

## 8. Manutenção

```bash
python scripts/gestao_documental/detectar_duplicados.py --processo PA_031_2026
python scripts/gestao_documental/limpar_temporarios.py --processo PA_031_2026 --simular
python scripts/gestao_documental/limpar_temporarios.py --processo PA_031_2026
python scripts/gestao_documental/validar_processo.py --processo PA_031_2026
```

`validar_processo.py` sai com código 1 havendo erro. Antes de fechar uma fase
(publicar aviso, homologar, assinar contrato), rode-o e resolva os erros.

---

## 9. Ao final de qualquer operação, informe

1. **o que foi gravado** — documento, versão, caminho;
2. **o que foi arquivado** — versão anterior e onde está;
3. **o que não mudou** — e por quê (conteúdo idêntico não gera versão);
4. **o que ficou pendente** — campos, quarentena, confirmações humanas;
5. **o que não foi verificado** — e o motivo.

Nunca declare processo organizado, documento pronto para assinatura ou migração
concluída sem que a saída do script diga isso.
