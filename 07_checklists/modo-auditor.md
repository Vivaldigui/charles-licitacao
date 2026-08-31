---
tipo: checklist
hierarquia: operacional
tema: modo auditor de processo
fonte: base Charles / esteira de contratação direta
vigencia: vigente
atualizado_em: 2026-07-01
tags: [auditoria, processo, checklist, contratacao-direta, riscos]
---

# Modo auditor — "Charles, audite este processo"

Roteiro para auditar uma pasta de processo em `08_processos_em_andamento/`.

> **Roteiro completo:** antes de iniciar, leia e siga
> [`roteiro-modo-auditor-contratacao-direta.md`](roteiro-modo-auditor-contratacao-direta.md),
> que governa inventário, recuperação da jurisprudência do TCE-MG, achados, contraditório,
> gravidade, conclusão e relatório. Este arquivo permanece como referência resumida da esteira.

## Regra principal

O auditor só afirma o que verificou em arquivo. Documento não encontrado = **ausente**, nunca
presumido. Dado que não está no `processo.json` ou em documento anexado deve ser marcado como
`[PREENCHER]` ou `[VALIDAÇÃO HUMANA]`.

## Entrada

- `processo.json` da pasta do processo.
- Documentos DOCX/PDF/MD anexados à mesma pasta.
- Esteira aplicável: `07_checklists/esteira-contratacao-direta.md`.
- Fundamento do processo: `processo.json.fundamento`.

## Saída obrigatória

### 1. Documentos obrigatórios

Classificar cada etapa da esteira como:

- **presente** — documento localizado e compatível com a etapa;
- **ausente** — documento não localizado;
- **com ressalva** — documento localizado, mas com campo pendente, dado incompatível ou validação
  humana necessária.

### 2. Riscos

Verificar e listar, no mínimo:

- pesquisa de preços com menos de 3 preços válidos;
- CNAE não confirmado;
- limite de dispensa próximo, não confirmado ou ultrapassado;
- campos `{{CAMPO}}` ou `[PREENCHER]` remanescentes;
- parecer jurídico exigível pelo Ato do Diretor Jurídico nº 01/2024;
- documento de proposta/habilitação citado sem arquivo-fonte;
- divergência entre `processo.json`, TR, pesquisa, ata e homologação.

### 3. Providências antes de prosseguir

Listar providências numeradas, objetivas e executáveis. Exemplo:

1. Juntar certidão orçamentária ou indicar sua ausência.
2. Confirmar subclasse CNAE no IBGE/CONCLA e atualizar `processo.json`.
3. Rodar `python scripts/controle_cnae.py simular ...`.
4. Resolver campos `[PREENCHER]` antes de gerar contrato.

## Restrições

- Não declarar processo apto se houver documento obrigatório ausente.
- Não afirmar regularidade fiscal sem certidão anexada.
- Não afirmar atendimento de proposta sem apontar documento/fólio.
- Não substituir parecer jurídico quando ele for exigível.
