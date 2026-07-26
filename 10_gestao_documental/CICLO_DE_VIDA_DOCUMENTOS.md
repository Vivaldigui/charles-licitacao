---
tipo: norma_interna
hierarquia: operacional
tema: ciclo de vida dos documentos do processo
fonte: base Charles
vigencia: vigente
atualizado_em: 2026-07-25
tags: [gestao documental, ciclo de vida, promocao, assinatura, publicacao]
---

# Ciclo de Vida dos Documentos

## Estados

| Estado | O que significa | Pode ser substituído? |
|---|---|---|
| `rascunho` | esboço inicial | sim, arquivando a anterior |
| `em_elaboracao` | em produção | sim, arquivando a anterior |
| `em_revisao` | em conferência | sim, arquivando a anterior |
| `aprovado` | conferido e aceito | sim, **com motivo e responsável** |
| `assinado` | assinado | **não** — imutável |
| `publicado` | publicado | **não** — imutável |
| `substituido` | versão anterior no histórico | — |
| `cancelado` | descontinuado | — |
| `arquivado` | encerrado, sem arquivo corrente | — |

## Transições previstas

```
rascunho ──► em_elaboracao ──► em_revisao ──► aprovado ──► assinado ──► publicado ──► arquivado
                    ▲                │             │
                    └────────────────┘             │
                                                   ▼
                                              (retificação)
```

Qualquer estado editável pode ir a `cancelado`. O que não está no diagrama exige
decisão humana e não é executado automaticamente.

## O que cada promoção faz de concreto

### para `em_revisao`
Só muda o estado. O arquivo continua em `01_EM_ELABORACAO/`.

### para `aprovado`
A peça editável **sai** de `01_EM_ELABORACAO/` e passa a documento oficial em
`02_DOCUMENTOS_OFICIAIS/<FASE>/`. Exige ausência de campo pendente.

### para `assinado`
Exige o arquivo assinado (`--arquivo`). Ele entra em `05_ASSINADOS/<TIPO>/` como
**representação da mesma versão** — não cria versão nova. O hash do assinado é
gravado. A partir daqui o documento é imutável.

### para `publicado`
Registra o comprovante em `04_PUBLICACOES/<VEÍCULO>/` (`AVISOS`, `EXTRATOS`,
`PNCP`, `DIARIO_OFICIAL`, `PACOTES`). O pacote do Aviso Completo vai para
`04_PUBLICACOES/PACOTES/AVISO_COMPLETO/`, como artefato derivado. Também
imutável.

## O que é verificado antes de promover

Verificável e **bloqueante**:

- campos `[PREENCHER: ...]` e `{{CAMPO}}` ainda presentes;
- número de processo divergente citado no documento.

Verificável e **ressalva** (a promoção para, e só segue com `--ignorar-avisos`):

- comentários internos no DOCX;
- marcas de controle de alterações;
- blocos alternativos ("OU") aparentemente abertos.

**Não verificável** (declarado como tal, nunca presumido aprovado):

- campos pendentes em PDF e formatos sem extrator de texto;
- comentários e controle de alterações fora de DOCX;
- o mérito do conteúdo — quem responde é o responsável registrado na promoção.

## Retificação

Única saída de `assinado` e `publicado`:

```bash
python scripts/gestao_documental/promover_documento.py \
  --processo PA_031_2026 --tipo AVISO --retificar \
  --arquivo AVISO_corrigido.docx --motivo "Erro material na data de abertura"
```

O que acontece:

1. a peça imutável desce ao histórico **com o status que tinha**
   (`status_ao_arquivar: publicado`, `retificado: true`);
2. o substitutivo nasce como versão nova, em `em_revisao`;
3. grava-se `retifica_versao` na versão nova e `substituido_por_versao` na
   antiga — a relação entre as duas fica explícita;
4. o evento `documento_retificado` entra no log.

A **nova publicação é ato separado**: a retificação não presume que o
substitutivo já esteja publicado.

## Restauração

```bash
python scripts/gestao_documental/restaurar_versao.py \
  --processo PA_031_2026 --tipo TR --versao 2
```

A versão atual é arquivada; o conteúdo da versão 2 é copiado como versão
**nova** (5 → 6), com `origem_da_versao.tipo = "restauracao"`. O contador nunca
retrocede, e a versão restaurada continua no histórico onde sempre esteve.

Antes de restaurar, o hash do arquivo histórico é conferido contra o manifesto:
divergindo, a restauração é recusada até conferência humana.

## Eventos registrados no log

`processo_criado`, `documento_importado`, `documento_gerado`,
`documento_substituido`, `documento_promovido`, `documento_assinado`,
`documento_publicado`, `documento_retificado`, `documento_arquivado`,
`documento_externo_classificado`, `duplicado_descartado`,
`arquivo_colocado_em_quarentena`, `erro_de_validacao`, `restauracao_de_versao`,
`geracao_sem_alteracao`, `lock_recuperado`, `rollback_executado`,
`temporarios_limpos`, `processo_migrado`.
