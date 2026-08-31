---
tipo: norma_interna
hierarquia: operacional
tema: gestao documental dos processos em andamento
fonte: base Charles
vigencia: vigente
atualizado_em: 2026-07-25
tags: [gestao documental, versionamento, processos, manifesto, historico]
---

# Módulo de Gestão Documental dos Processos em Andamento

## O problema que este módulo resolve

Uma pasta de processo, depois de algumas semanas, costuma ficar assim:

```
DFD.docx  DFD_novo.docx  DFD_final.docx
TR.docx   TR_1.docx  TR_corrigido.docx  TR_final_2.docx  Cópia de TR.docx
proposta.pdf  certidão.pdf  ~$TR.docx  anotações.txt
```

Ninguém sabe qual é a versão vigente, o que já foi assinado, o que veio de
fornecedor e o que é sobra de script. O módulo troca isso por:

```
01_EM_ELABORACAO/     DFD.docx  ETP.docx  TR.docx
02_DOCUMENTOS_OFICIAIS/  peças aprovadas, por fase
03_DOCUMENTOS_EXTERNOS/  propostas, certidões, e-mails — classificados
04_PUBLICACOES/       avisos, extratos, PNCP, pacotes
05_ASSINADOS/         representações assinadas
07_MATERIAL_DE_TRABALHO/ evidência de pesquisa, com o nome original
90_HISTORICO/         TR_v001_20260720_100000.docx, TR_v002_...
98_QUARENTENA/        o que depende de decisão humana
99_TEMPORARIOS/       sessões de geração, invisíveis ao fluxo
00_CONTROLE/          PROCESSO.json, DOCUMENTOS.json, PAINEL, LOG
```

**Um arquivo de trabalho visível por tipo documental. Nenhuma versão perdida.**

## Onde ficam os processos

Processo real tem proposta, CNPJ, certidão e assinatura. Ele **não** deve ficar
num repositório público. Configure:

```bash
CHARLES_PROCESSOS_DIR=C:\Charles\Processos
```

Sem essa variável, os processos cairiam em `08_processos_em_andamento/`, que
neste repositório só pode conter exemplo fictício. Veja
[SEGURANCA_E_PRIVACIDADE.md](SEGURANCA_E_PRIVACIDADE.md).

## Documentos deste módulo

| Arquivo | O que traz |
|---|---|
| [REGRAS_GESTAO_DOCUMENTAL.md](REGRAS_GESTAO_DOCUMENTAL.md) | as regras inegociáveis e o porquê de cada uma |
| [CONVENCAO_NOMES.md](CONVENCAO_NOMES.md) | nomes canônicos, do histórico e dos documentos externos |
| [CICLO_DE_VIDA_DOCUMENTOS.md](CICLO_DE_VIDA_DOCUMENTOS.md) | rascunho → assinado → publicado, e a retificação |
| [SEGURANCA_E_PRIVACIDADE.md](SEGURANCA_E_PRIVACIDADE.md) | repositório público, `.gitignore`, dados pessoais |
| [processo.schema.json](processo.schema.json) | esquema do `PROCESSO.json` |
| [documentos.schema.json](documentos.schema.json) | esquema do `DOCUMENTOS.json` |
| [exemplos/PROCESSO_EXEMPLO/](exemplos/PROCESSO_EXEMPLO/) | processo fictício completo, sem dado real |

Roteiro operacional e regras de conduta do Charles:
`07_checklists/roteiro-gestao-documental-processo.md` e
`07_checklists/regras-gestao-documental-processo.md`.

## Comandos

```bash
# criar a pasta organizada de um processo
python scripts/gestao_documental/iniciar_processo.py \
  --numero "PA 031/2026" --objeto "Aquisição de material de limpeza"

# registrar um documento gerado (primeira versão)
python scripts/gestao_documental/registrar_documento.py \
  --processo PA_031_2026 --tipo TR --arquivo saida/TR_gerado.docx \
  --motivo "Primeira geração" --minuta-origem 05_minutas/TR/TR_MINUTA_MAE.docx

# substituir a versão vigente (motivo obrigatório)
python scripts/gestao_documental/substituir_documento.py \
  --processo PA_031_2026 --tipo TR --arquivo saida/TR_revisado.docx \
  --motivo "Ajuste do prazo de entrega"

# promover no ciclo de vida
python scripts/gestao_documental/promover_documento.py \
  --processo PA_031_2026 --tipo TR --status aprovado --responsavel "Agente"

# registrar a versão assinada (representação, não versão nova)
python scripts/gestao_documental/promover_documento.py \
  --processo PA_031_2026 --tipo TR --status assinado --arquivo TR_assinado.pdf

# retificar documento assinado ou publicado
python scripts/gestao_documental/promover_documento.py \
  --processo PA_031_2026 --tipo AVISO --retificar --arquivo AVISO_corrigido.docx \
  --motivo "Erro material na data de abertura"

# importar documentos externos
python scripts/gestao_documental/importar_documento_externo.py \
  --processo PA_031_2026 --arquivo proposta_fornecedor.pdf --categoria proposta

# histórico e restauração
python scripts/gestao_documental/restaurar_versao.py --processo PA_031_2026 --tipo TR --listar
python scripts/gestao_documental/restaurar_versao.py --processo PA_031_2026 --tipo TR --versao 2

# organizar uma pasta antiga: primeiro o plano, depois a execução
python scripts/gestao_documental/migrar_processo.py \
  --origem "pasta_antiga" --destino PA_031_2026 --somente-planejar --plano plano.json
python scripts/gestao_documental/migrar_processo.py \
  --origem "pasta_antiga" --destino PA_031_2026 --executar

# manutenção
python scripts/gestao_documental/detectar_duplicados.py --processo PA_031_2026
python scripts/gestao_documental/limpar_temporarios.py --processo PA_031_2026 --simular
python scripts/gestao_documental/gerar_painel.py --processo PA_031_2026
python scripts/gestao_documental/validar_processo.py --processo PA_031_2026
python scripts/gestao_documental/seguranca_repositorio.py --diagnostico
```

## A interface única dos geradores

Nenhum gerador escolhe onde salvar. Todos terminam em:

```python
from registrar_documento import registrar_saida_gerada

registrar_saida_gerada(
    processo="PA_031_2026",
    tipo_documento="TR",
    arquivo_temporario="/tmp/TR_gerado.docx",
    minuta_origem="05_minutas/TR/TR_MINUTA_MAE.docx",
    motivo="Atualização dos requisitos",
    status="em_elaboracao",
)
```

A função devolve um `ResultadoRegistro` com a situação (`registrado`,
`sem_alteracao`), a versão, o caminho final, os campos pendentes encontrados e
o que **não** foi possível verificar.

## Dependências

Nenhuma além da biblioteca padrão do Python. O módulo lê o texto de um DOCX
abrindo o pacote OOXML diretamente — `python-docx` só é necessário para o
módulo de padronização (`scripts/docx_cmi/`), que é independente deste.

## Testes

```bash
python -m pytest 99_testes/gestao_documental/ -v
```

Os 34 testes obrigatórios do escopo estão nomeados por número
(`test_01_...` a `test_34_...`).

## Limites deste módulo

- **Não lê PDF.** Sem OCR nem parser na base, um PDF é classificado pelo nome e
  o registro diz que o texto não foi lido. Campo pendente em PDF não é
  verificado — e isso aparece como "NÃO VERIFICADO", nunca como "aprovado".
- **Não julga mérito.** Promover para aprovado confere campos pendentes,
  comentários e controle de alterações; quem responde pelo conteúdo é o
  responsável nominalmente registrado.
- **Não decide enquadramento.** A lista de documentos obrigatórios gravada no
  `PROCESSO.json` é sugestão operacional, marcada como tal.
- **Não verifica visibilidade real do repositório.** Havendo remoto, trata-se o
  repositório como público, por precaução.
