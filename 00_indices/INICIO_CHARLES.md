---
tipo: checklist
hierarquia: operacional
tema: pagina inicial do Charles
fonte: base Charles
vigencia: vigente
atualizado_em: 2026-08-03
tags: [inicio, obsidian, navegacao, painel]
---

# Início do Charles

O Charles é o cérebro documental de apoio às licitações e contratações da Câmara Municipal de
Itanhandu. A base organiza fontes, rotinas, precedentes e minutas, mas não substitui a conferência
humana, a decisão da autoridade competente nem a assessoria jurídica.

> [!warning] Regras obrigatórias
> Leia primeiro [[CLAUDE]]. Ele governa a hierarquia de fontes, a segurança, a prevenção de
> alucinações e o uso travado das minutas oficiais. Este painel é apenas navegação.

## Começar por aqui

- [[00_indices/ROTAS_DE_CONSULTA_DO_CHARLES|Rotas de consulta para pessoas e IAs]]
- [[00_indices/INDICE_GERAL|Índice geral]]
- [[00_indices/MAPA_POR_TEMA|Mapa por tema]]
- [[00_indices/MAPA_POR_MODALIDADE|Mapa por modalidade]]
- [[00_indices/PAINEL_PROCESSOS|Processos em andamento]]
- [[00_indices/PAINEL_PENDENCIAS|Pendências]]

## Fontes e instrumentos

| Área | Acesso principal | Observação |
|---|---|---|
| Legislação | [[01_legislacao/lei-14133-2021-licitacoes-contratos-administrativos|Lei nº 14.133/2021]] · [[01_legislacao/limites-vigentes-dispensa-art-75|Limites vigentes]] | Confirmar vigência e atualização antes de citar. |
| Normas internas | [[02_normas_internas/regulamento-licitacoes-camara-itanhandu|Regulamento da Câmara]] | Prevalece sobre a praxe no procedimento interno. |
| Jurisprudência | [[03_jurisprudencia/sumulas|Súmulas]] · [[03_jurisprudencia/tce_mg/contratacao_direta/consolidacoes/MAPA_TEMATICO_CONTRATACAO_DIRETA|Mapa TCE-MG]] | Conferir toda citação no arquivo-fonte. |
| Minutas oficiais | [[05_minutas/_CONTROLE_MINUTAS|Controle de minutas]] · [[00_indices/PAINEL_MINUTAS|Painel de minutas]] | Não duplicar nem alterar conteúdo fixo sem pedido expresso. |
| Precedentes da Câmara | [[06_precedentes_camara/CONTROLE_CONTRATACOES|Controle de contratações]] | Precedente interno não é fundamento jurídico geral. |
| Checklists | [[07_checklists/esteira-contratacao-direta|Esteira de contratação direta]] · [[07_checklists/rotina-diaria-agente-contratacao|Rotina diária]] | Conferência humana permanece obrigatória. |
| Pesquisa de preços | [[07_checklists/roteiro-executar-pesquisa-de-precos|Roteiro]] · [ferramentas Python](../scripts/README.md) | Pesquisa rastreável, comparável e documentada. |
| Controle CNAE | [[00_indices/PAINEL_CONTROLE_CNAE|Painel CNAE]] | O registro oficial único permanece no controle de contratações. |

## Trabalho operacional

- Processos: [[00_indices/PAINEL_PROCESSOS]]
- Modelos de notas operacionais: [[08_processos_em_andamento/_FICHAS_OBSIDIAN/FICHA_PROCESSO]]
- Pendências e prazos: [[00_indices/PAINEL_PENDENCIAS]]
- Fontes a revisar: [[00_indices/PAINEL_FONTES]]
- Rotina semanal: [[07_checklists/rotina-semanal-manutencao-charles]]

## Pendências

Registre e revise no [[00_indices/PAINEL_PENDENCIAS]]. Dado ausente deve permanecer marcado como
`[PREENCHER: descrição objetiva]`; dúvida jurídica sem suporte deve ser registrada conforme o
texto obrigatório do [[CLAUDE]].

## Fontes que precisam de atualização

Consulte o [[00_indices/PAINEL_FONTES]] e execute `python scripts/gerar_relatorio_base.py`. Limites
de dispensa e demais fontes com manutenção periódica devem ser conferidos antes do uso.

## Processos prioritários

Mantenha a lista manual no [[00_indices/PAINEL_PROCESSOS]] e, em cada ficha, preencha `prioridade`,
`prazo` e `proxima_acao`. Processos reais e dados de fornecedores devem permanecer fora do Git.

