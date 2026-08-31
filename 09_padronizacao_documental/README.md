---
tipo: norma_interna
hierarquia: padrao_visual
tema: modulo de padronizacao e formatacao documental
fonte: base Charles
orgao: camara municipal de itanhandu
versao: 1.0
vigencia: vigente
atualizado_em: 2026-07-25
tags: [padronizacao, formatacao, docx, modulo, indice]
---

# Módulo de Padronização e Formatação Documental

Faz com que os documentos gerados pelo Charles tenham aparência profissional e
uniforme — fontes padronizadas, títulos hierarquizados, numeração correta, tabelas
bem dimensionadas, espaçamento consistente, timbre preservado — **sem alterar o
conteúdo jurídico ou administrativo**.

---

## Arquivos desta pasta

| Arquivo | Para quê |
|---|---|
| [`PADRAO_VISUAL_DOCUMENTOS.md`](PADRAO_VISUAL_DOCUMENTOS.md) | Fonte de verdade **narrativa** do padrão visual: tipografia, cores, espaçamento, página, estilos |
| [`PERFIS_DOCUMENTAIS.json`](PERFIS_DOCUMENTAIS.json) | Fonte de verdade **técnica**, lida pelos scripts. Em caso de divergência, **vale o JSON** |
| [`REGRAS_DE_FORMATACAO.md`](REGRAS_DE_FORMATACAO.md) | Fronteira entre conteúdo e formatação, e como ela é imposta |
| [`REFERENCIAS_VISUAIS.md`](REFERENCIAS_VISUAIS.md) | Documentos oficiais consultados, com o que foi e o que não foi aproveitado |
| [`EXCECOES_AUTORIZADAS.md`](EXCECOES_AUTORIZADAS.md) | Divergências conhecidas e aceitas |
| `relatorios/` | Relatórios de auditoria e padronização |

Código: [`scripts/docx_cmi/`](../scripts/docx_cmi/).
Roteiros: [`07_checklists/roteiro-padronizacao-documental.md`](../07_checklists/roteiro-padronizacao-documental.md)
e [`07_checklists/regras-padronizacao-documental.md`](../07_checklists/regras-padronizacao-documental.md).
Testes: [`99_testes/padronizacao_documental/`](../99_testes/padronizacao_documental/).

---

## Instalação

```bash
python -m pip install -r requirements-docx.txt
```

Única dependência externa do repositório (`python-docx==1.2.0`), isolada de propósito.
Sem ela, os comandos param com mensagem explícita em vez de falhar de forma obscura.

---

## Os três modos

### 1. Auditoria — analisa sem alterar

```bash
python scripts/docx_cmi/auditar_docx.py --entrada documento.docx --perfil tr --saida-relatorio relatorio.md
```

Levanta fontes, tamanhos, cores, estilos, formatação direta, numeração, tabelas,
paginação, cabeçalho/rodapé, campos pendentes, comentários e controle de alterações.
Produz relatório em Markdown e JSON, nota de 0 a 100 e a separação entre o que é
corrigível automaticamente e o que exige pessoa.

### 2. Padronização automática — corrige sobre uma cópia

```bash
python scripts/docx_cmi/formatar_docx.py --entrada documento.docx --saida documento_formatado.docx --perfil tr --preservar-conteudo
```

O arquivo de entrada nunca é sobrescrito. Havendo qualquer alteração de conteúdo não
autorizada, **nada é gravado**.

### 3. Revisão de minuta-mãe — só com pedido expresso

```bash
python scripts/docx_cmi/formatar_docx.py --entrada 05_minutas/TR/TR_MINUTA_MAE.docx --revisar-minuta-mae --perfil tr
```

Faz backup em `_arquivo/`, grava o relatório do estado anterior, aplica as correções,
incrementa a versão na ficha de uso e registra no changelog. Fora deste modo, gravar
dentro de `05_minutas/` é recusado com erro.

---

## Outros comandos

```bash
# apenas diagnosticar, usando o executável de formatação
python scripts/docx_cmi/formatar_docx.py --entrada 05_minutas/TR/TR_MINUTA_MAE.docx --saida testes/tr_formatado.docx --perfil tr --somente-auditoria
```

```bash
# corrigir numeração com trava de referências internas
python scripts/docx_cmi/formatar_docx.py --entrada documento.docx --saida documento_formatado.docx --perfil contrato --corrigir-numeracao --validar-referencias-internas
```

```bash
# lote, sem sobrescrever os originais
python scripts/docx_cmi/formatar_docx.py --diretorio 08_processos_em_andamento/PROCESSO_X/ --saida-diretorio 08_processos_em_andamento/PROCESSO_X/documentos_formatados/
```

```bash
# preencher campos {{CAMPO}} e formatar em uma passada
python scripts/docx_cmi/formatar_docx.py --entrada 05_minutas/TR/TR_MINUTA_MAE.docx --saida processo/TR_PREENCHIDO_FORMATADO.docx --perfil tr --campos processo/campos.json
```

### Opções

| Opção | Efeito |
|---|---|
| `--perfil` | Perfil documental. Omitido, é deduzido do nome do arquivo |
| `--minuta-mae` | Compara timbre e estrutura com a minuta oficial |
| `--campos` | JSON com os `{{CAMPO}}` a preencher |
| `--somente-auditoria` | Não grava nada |
| `--preservar-conteudo` | Bloqueia a saída se o conteúdo mudar (**ligado por padrão**) |
| `--corrigir-numeracao` | Aplica a renumeração proposta, se for segura |
| `--validar-referencias-internas` | Impede renumeração que invalide referência interna |
| `--normalizar-cores` | Converte texto colorido em preto. **Desligado por padrão** — nas minutas o vermelho marca campo a preencher |
| `--limpar-metadados` | Limpa autor e último editor |
| `--revisar-minuta-mae` | Modo revisão, com backup e versionamento |

---

## Status possíveis

| Status | Significado |
|---|---|
| `APROVADO NA VALIDAÇÃO AUTOMÁTICA` | Nenhuma pendência automática. **Não** substitui conferência visual |
| `APROVADO COM RESSALVAS` | Formatado, com pontos anotados no relatório |
| `EXIGE CONFERÊNCIA HUMANA` | Campos pendentes, comentários internos ou revisões |
| `BLOQUEADO POR ALTERAÇÃO DE CONTEÚDO` | O texto mudou — nada foi gravado |
| `BLOQUEADO POR ERRO ESTRUTURAL` | Timbre ou estrutura comprometidos — nada foi gravado |

---

## Garantias verificadas a cada execução

- **Conteúdo preservado** — hash antes/depois, diferenças classificadas uma a uma.
- **Timbre intacto** — cabeçalho, rodapé e mídia referenciada conferidos.
- **Idempotência** — formatar duas vezes dá o mesmo resultado.
- **Original preservado** — a entrada nunca é sobrescrita.
- **Validação visual** — executada se houver LibreOffice; **nunca simulada**. Neste
  ambiente `soffice` não está instalado, e o relatório diz isso.

---

## Testes

```bash
python -m pytest 99_testes/padronizacao_documental/ -v
```

104 testes, cobrindo os 12 casos obrigatórios do escopo. Os testes 9, 10, 11 e 12 rodam
parametrizados sobre as **22 minutas-mãe reais**.
