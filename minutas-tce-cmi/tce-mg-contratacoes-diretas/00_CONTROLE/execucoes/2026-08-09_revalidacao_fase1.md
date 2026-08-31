# Execução — revalidação e consolidação da Fase 1

Data local: 2026-08-09 (America/Sao_Paulo)

## Escopo

- preservar e auditar o trabalho existente;
- revalidar Portal da Transparência, Compras MG e TCLEGIS;
- completar a estrutura básica prevista no projeto;
- corrigir rastreabilidade, portabilidade e idempotência.

## Resultados verificados

- 32 atos no índice normativo;
- 33 arquivos de metadados de hash;
- 61 PDFs válidos, sem zero byte, todos com SHA-256 correspondente;
- 107 evidências no manifesto, com caminhos relativos sem colisões;
- Portal da Transparência acessível em navegador interativo;
- API direta do Portal da Transparência: HTTP 401 sem a sessão do navegador;
- Portal de Compras MG: hCaptcha apresentado na busca do órgão 1020;
- TCLEGIS detalhe 1142002: HTTP 200 na revalidação.

## Testes executados

```text
python -m py_compile scripts/*.py scripts/utils/__init__.py
python scripts/08_validar_integridade.py
python scripts/09_reconciliar_manifesto.py --check
python scripts/01_descobrir_normas.py --so-parse  (duas vezes)
python scripts/04_coletar_atos_tclegis.py --indices (duas vezes)
python scripts/02_buscar_tclegis.py --so-listar
```

Resultados: compilação sem erro; scripts 01 e 04 idempotentes; índice permaneceu
com 32 atos; `--help` do reconciliador não alterou o manifesto.

## Limitações

- nenhum hCaptcha foi resolvido ou contornado;
- não foi iniciada coleta em massa de processos;
- a captura interativa do Portal da Transparência é amostral e não foi promovida
  para o índice principal de processos;
- vigência jurídica e completude temática não são aprovadas pelo teste binário.

