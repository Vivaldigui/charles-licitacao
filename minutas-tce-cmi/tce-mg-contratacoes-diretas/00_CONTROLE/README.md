# Controle e auditoria

Esta pasta reúne evidências brutas, registros de execução, erros, logs, hashes e o
diagnóstico técnico das fontes. Os textos metodológicos mantidos desde o início do
projeto permanecem em [`../metodologia.md`](../metodologia.md) e
[`../fontes.md`](../fontes.md); estes links evitam duplicar conteúdo.

Conferência somente leitura do manifesto:

```powershell
python scripts/09_reconciliar_manifesto.py --check
```

Reconciliação deliberada, quando novos arquivos forem incorporados:

```powershell
python scripts/09_reconciliar_manifesto.py
```

