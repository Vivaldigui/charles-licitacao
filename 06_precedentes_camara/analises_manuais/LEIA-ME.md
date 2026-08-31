# Análises manuais — controle CNAE

## `contratacoes_2026_cnae_analise.xlsx`

Movida da raiz do CHARLES (`Contratacoes_2026_CNAE.xlsx`) na reorganização de
2026-07-04. É uma planilha de **análise manual paralela** (4 abas:
"Contratacoes 2026", "Itens 013 e 016", "Acumulado por CNAE", "Itens em
estudo"), não gerada por `scripts/controle_cnae.py`.

**Atenção — risco de duas fontes de verdade:** esta planilha cita como fonte
um arquivo (`REGISTRO_CONTRATACOES_2026.md`) que hoje só existe dentro de
`EQUIPE_LICITACOES_CAMARA_ITANHANDU/08_PROCESSOS_CONCLUIDOS/ACERVO_CONTRATACOES_2026/`
— pasta de um projeto paralelo distinto que **não foi tocada** nesta
reorganização.

Antes de usar esta planilha para decisões de limite por CNAE (art. 75, I e
II), é preciso:

1. Reconciliar os dados desta planilha com o controle oficial em
   `06_precedentes_camara/CONTROLE_CONTRATACOES.md` e `contratacoes.csv`.
2. Registrar qualquer contratação ainda não lançada via
   `python scripts/controle_cnae.py registrar ...` e regenerar o relatório
   com `python scripts/controle_cnae.py relatorio`.
3. Não tratar esta planilha isoladamente como fonte de verdade para o
   controle de fracionamento por subclasse CNAE.
