---
tipo: checklist
hierarquia: operacional
tema: painel de controle por cnae
fonte: base Charles / controle oficial de contratacoes
vigencia: vigente
atualizado_em: 2026-08-03
tags: [painel, cnae, dispensa, fracionamento, controle]
---

# Painel de controle por CNAE

> [!important] Registro único
> O controle oficial é [[06_precedentes_camara/CONTROLE_CONTRATACOES]]. Este painel não recebe
> lançamentos e não mantém soma paralela. Atualize o controle somente pelo fluxo documentado nele e
> por `python scripts/controle_cnae.py registrar ...`.

## Leitura operacional — Markdown básico

| Informação | Onde consultar no controle oficial | Ação |
|---|---|---|
| Exercício, objeto e subclasse CNAE | Tabela “Registro de contratações” | Confirmar o enquadramento; nunca inventar CNAE. |
| Valores acumulados, limite e margem disponível | Tabela “Acumulado por subclasse/exercício” | Conferir o limite vigente antes de decidir. |
| Alertas de possível fracionamento | Seções de alertas e análise | Tratar como alerta para instrução, não conclusão automática. |
| Contratações sem CNAE confirmado | Seção de validação humana e pendências | Obter fonte oficial ou validar no IBGE/CONCLA. |

Use também [[07_checklists/roteiro-limite-dispensa-cnae]] e
[[01_legislacao/limites-vigentes-dispensa-art-75]].

## Processos em análise — tabela auxiliar, sem registrar acumulados

| Processo/ficha | Exercício | Objeto | Subclasse CNAE | CNAE confirmado? | Valor previsto | Simulação executada? | Alerta/próxima ação |
|---|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — | — |

## Visualização automática — opcional, requer Dataview

```dataview
TABLE exercicio, objeto, cnae, cnae_confirmado, valor_estimado, alerta_fracionamento, proxima_acao
FROM "08_processos_em_andamento"
WHERE tipo = "processo" AND modelo != true AND status != "concluido"
SORT exercicio DESC, cnae ASC
```

