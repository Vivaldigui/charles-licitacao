---
tipo: norma_interna
hierarquia: operacional
tema: convencao de nomes dos arquivos dos processos
fonte: base Charles
vigencia: vigente
atualizado_em: 2026-07-25
tags: [gestao documental, nomes, versionamento, sanitizacao]
---

# Convenção de Nomes

## 1. Área corrente — nomes canônicos

O arquivo de trabalho tem nome **estável**, sem versão, sem data e sem adjetivo:

| Tipo | Arquivo | Fase |
|---|---|---|
| DFD | `DFD.docx` | preparatória |
| ETP | `ETP.docx` | preparatória |
| TR | `TR.docx` | preparatória |
| MAPA_DE_RISCOS | `MAPA_DE_RISCOS.docx` | preparatória |
| PESQUISA_DE_PRECOS | `PESQUISA_DE_PRECOS.docx` | preparatória |
| JUSTIFICATIVA_CONTRATACAO_DIRETA | `JUSTIFICATIVA_CONTRATACAO_DIRETA.docx` | preparatória |
| AUTORIZACAO | `AUTORIZACAO.docx` | preparatória |
| AVISO | `AVISO.docx` | seleção do fornecedor |
| AVISO_COMPLETO | `AVISO_COMPLETO.docx` | seleção do fornecedor |
| ATA_JULGAMENTO | `ATA_JULGAMENTO.docx` | seleção do fornecedor |
| HOMOLOGACAO | `HOMOLOGACAO.docx` | seleção do fornecedor |
| CONTRATO | `CONTRATO.docx` | contratação |
| EXTRATO | `EXTRATO.docx` | contratação |
| ORDEM_FORNECIMENTO | `ORDEM_FORNECIMENTO.docx` | execução |
| TERMO_RECEBIMENTO | `TERMO_RECEBIMENTO.docx` | execução |

A tabela é fechada: tipo fora dela é recusado (`TipoDesconhecido`), porque um
tipo inventado quebra o controle de arquivo único.

## 2. Histórico

```
TIPO_vNNN_AAAAMMDD_HHMMSS[_MOTIVO].ext
```

```
TR_v001_20260725_181530.docx
TR_v002_20260726_093210_AJUSTE_PRAZO.docx
DFD_v003_20260727_140500.docx
```

O motivo é opcional, sanitizado e limitado a 40 caracteres. Versão sempre com
três dígitos; carimbo de tempo do momento do arquivamento.

## 3. Documentos externos

```
AAAA-MM-DD_ORIGEM_TIPO_DESCRICAO.ext
```

```
2026-07-20_EMPRESA_X_PROPOSTA_COMERCIAL.pdf
2026-07-21_EMPRESA_Y_CERTIDAO_FGTS.pdf
2026-07-22_PNCP_TERMO_REFERENCIA_INTERNET.pdf
2026-07-23_ASSESSORIA_JURIDICA_PARECER.pdf
```

Campo que o documento não informa **não é inventado**:

- data ausente → `SEM_DATA`
- origem ausente → `ORIGEM_NAO_IDENTIFICADA`
- tipo ausente → `TIPO_NAO_IDENTIFICADO`

E a pendência correspondente vai para o manifesto. O **nome original** é sempre
preservado no registro.

## 4. Sanitização

Todo componente livre (motivo, origem, descrição) passa por:

1. remoção de acentos (NFKD);
2. maiúsculas;
3. troca de qualquer coisa fora de `A-Z0-9` por `_`;
4. colapso de `_` repetidos e corte nas pontas;
5. limite de tamanho;
6. sufixo `_` em nomes reservados do Windows (`CON`, `PRN`, `AUX`, `NUL`,
   `COM1`–`COM9`, `LPT1`–`LPT9`).

Caracteres proibidos em nome de arquivo (`< > : " / \ | ? *` e controles) são
removidos. Espaço nunca sobrevive.

## 5. Nomes que denunciam versão solta

Estes padrões são **sinalizados** em área corrente — e nunca gerados:

| Padrão | Exemplo |
|---|---|
| cópia | `Cópia de TR.docx`, `copy of TR.docx` |
| "final" | `TR_final.docx`, `TR_final_2.docx` |
| "novo", "atualizado", "último", "definitivo" | `DFD_novo.docx` |
| "corrigido" | `TR_corrigido.docx` |
| marcação informal | `TR_versao_certa.docx`, `TR_final_agora_vai.docx` |
| duplicata do sistema | `TR (1).docx` |
| revisão no nome | `TR_rev2.docx`, `TR_v3.docx` |
| sufixo numérico solto | `TR_2.docx` |
| rascunho/temporário | `TR_rascunho.docx`, `~$TR.docx` |

A sinalização entra no relatório de validação e no plano de migração. Ela
**nunca** autoriza apagar arquivo: o nome é indício, não prova.

## 6. Pasta do processo

```
PA_XXX_2026[_OBJETO_RESUMIDO]
```

Identificador derivado do número administrativo, sanitizado. Informando
`--identificador`, o nome é usado tal como veio. Nos comandos, `PA_031_2026`
também encontra `PA_031_2026_MATERIAL_DE_LIMPEZA`, desde que a correspondência
seja única.
