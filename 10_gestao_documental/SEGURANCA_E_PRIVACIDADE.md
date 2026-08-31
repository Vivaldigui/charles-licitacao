---
tipo: norma_interna
hierarquia: operacional
tema: seguranca e privacidade dos processos
fonte: base Charles
vigencia: vigente
atualizado_em: 2026-07-25
tags: [gestao documental, seguranca, lgpd, repositorio publico, gitignore]
---

# Segurança e Privacidade dos Processos

## A fronteira

Este repositório é público por vocação: guarda minutas, scripts, checklists,
doutrina e exemplos. **Processo real é outra coisa.** Ele contém proposta de
fornecedor, CNPJ, CPF, certidão, e-mail, telefone e assinatura — dado pessoal e
dado empresarial que não se publica por descuido.

Um vazamento não se desfaz com `git rm`: o histórico do Git preserva o que foi
commitado, e um repositório clonado ou indexado já saiu do seu controle.

## Onde os processos reais devem ficar

```bash
# Windows
CHARLES_PROCESSOS_DIR=C:\Charles\Processos

# Linux / macOS
CHARLES_PROCESSOS_DIR=/dados/charles/processos
```

Com a variável configurada, `iniciar_processo.py` cria tudo fora do
repositório, e o módulo confirma no diagnóstico:

```bash
python scripts/gestao_documental/seguranca_repositorio.py --diagnostico
```

**Sem a variável**, os processos cairiam em `08_processos_em_andamento/`. Essa
pasta, neste repositório, só pode conter:

- exemplos fictícios;
- arquivos sem dado pessoal;
- estruturas demonstrativas;
- manifestos sanitizados;
- documentação de uso.

## O que o módulo verifica antes de gravar

1. **O destino está dentro do repositório?**
2. **O repositório é público?** Declaração explícita em `CHARLES_REPO_PUBLICO`
   vence. Sem ela, havendo remoto configurado, o repositório é tratado como
   público — por precaução, já que a visibilidade real não é verificável sem
   rede.
3. **O caminho está coberto pelo `.gitignore`?** (via `git check-ignore`)
4. **O arquivo parece sensível?** Nome com `proposta`, `cotacao`, `certidao`,
   `cnd`, `fgts`, `habilitacao`, `cnpj`, `cpf`, `declaracao`, `email`,
   `nota_fiscal`, `comprovante`, `assinado`, `procuracao` — ou localização em
   `03_DOCUMENTOS_EXTERNOS/`, `98_QUARENTENA/`, `05_ASSINADOS/`,
   `07_MATERIAL_DE_TRABALHO/`.

   `07_MATERIAL_DE_TRABALHO/` guarda produção do próprio Charles, mas entra na
   lista assim mesmo: a pesquisa de contratações similares baixa documento de
   outro órgão, e edital alheio traz CPF de responsável. Separar material de
   trabalho de documento externo corrige o **destino** do arquivo — não o torna
   publicável.

**"Não verificado" não é "não coberto".** Sem `.git` na pasta, ou com o `git`
indisponível, a cobertura do `.gitignore` não pode ser consultada. Nesse caso a
gravação continua **recusada** — o que não se verificou não conta como protegido
—, mas a mensagem diz *"a cobertura NÃO PÔDE SER VERIFICADA"* e o motivo, em vez
de afirmar *"NÃO coberto pelo .gitignore"*, que seria uma conclusão que o código
não tem como sustentar. O motivo fica em `Avaliacao.motivo_indeterminado`.

Somando **dentro do repositório + público + sensível + não ignorado**, a
gravação é **recusada** com `OperacaoBloqueada`. Coberto pelo `.gitignore`, a
operação segue com aviso.

Para insistir conscientemente existe `CHARLES_PERMITIR_PROCESSO_NO_REPO=1` — e a
responsabilidade passa a ser de quem definiu a variável.

## Verificação antes do commit

```bash
python scripts/gestao_documental/seguranca_repositorio.py --verificar-staged
```

Lista os arquivos sensíveis prestes a entrar num commit e sai com código 1
havendo bloqueio. Para usar como gancho de pré-commit, **instale manualmente**:

```bash
printf '#!/bin/sh\npython scripts/gestao_documental/seguranca_repositorio.py --verificar-staged\n' \
  > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

O Charles **não** instala ganchos no `.git` por conta própria: alterar a
configuração local de um repositório é decisão do usuário.

## Varredura de um processo

```bash
python scripts/gestao_documental/seguranca_repositorio.py --processo PA_031_2026
python scripts/gestao_documental/validar_processo.py --processo PA_031_2026
```

A validação do processo inclui os bloqueios de exposição entre os erros.

## O que o Charles nunca faz

- enviar documento ao GitHub sem comando expresso do usuário;
- fazer commit ou push automático de arquivo de processo;
- copiar documento externo para dentro de área versionável de repositório
  público;
- usar dado real em exemplo versionado.

## Exemplos versionados

`10_gestao_documental/exemplos/PROCESSO_EXEMPLO/` é fictício de ponta a ponta:
"EMPRESA EXEMPLO LTDA", CNPJ `00.000.000/0001-00`, e-mail em domínio
`.invalido`. O teste `test_34_exemplos_do_repositorio_sem_dados_pessoais`
varre a pasta procurando CPF, CNPJ e e-mail reais, e falha se encontrar.

## O que este módulo NÃO faz

- **Não substitui a análise da LGPD** para publicação. Para o que vai ao PNCP e
  ao Diário Oficial, veja `07_checklists/checklist-lgpd-publicacao.md`.
- **Não criptografa** nada. Proteção do disco e controle de acesso à pasta são
  responsabilidade da infraestrutura da Câmara.
- **Não decide grau de sigilo.** `publicidade` no `PROCESSO.json` registra o que
  o operador declarou.
