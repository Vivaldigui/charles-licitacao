---
tipo: checklist
hierarquia: operacional
tema: regras de conduta na gestao documental dos processos
fonte: base Charles
vigencia: vigente
atualizado_em: 2026-07-25
tags: [gestao documental, regras, antialucinacao, rastreabilidade, lgpd]
---

# Regras — Gestão Documental do Processo

Regras de conduta do Charles ao operar o módulo. As regras técnicas estão em
`10_gestao_documental/REGRAS_GESTAO_DOCUMENTAL.md`; o passo a passo, em
`roteiro-gestao-documental-processo.md`.

---

## 1. Nunca salvar documento na pasta do processo por fora do módulo

Toda gravação passa por `registrar_saida_gerada` (ou pelos scripts que a usam).
Copiar arquivo manualmente para `01_EM_ELABORACAO/` cria documento sem
manifesto, sem hash e sem log — exatamente a desordem que o módulo existe para
evitar.

## 2. Nunca criar arquivo com nome de versão solta

`TR_final.docx`, `TR_2.docx`, `DFD_novo.docx`, `Cópia de TR.docx` não são
gerados em hipótese alguma. A versão vive no manifesto.

## 3. Não relatar como alteração o que não alterou nada

Quando o resultado é `sem_alteracao`, diga: *"a geração produziu conteúdo
idêntico à versão vigente; nenhuma versão nova foi criada"*. Não descreva
melhorias que não existem no arquivo.

## 4. Não converter "não verificado" em "aprovado"

PDF sem extrator de texto: os campos pendentes **não** foram verificados. Diga
isso. Formatação não auditada é `nao_executada`, não "aprovada".

## 5. Não afirmar que um documento está pronto para assinatura com campo pendente

Havendo `[PREENCHER: ...]` ou `{{CAMPO}}`, liste todos e diga que o documento
**não** está pronto.

## 6. Documento assinado e publicado não se sobrescreve

Pedido para "corrigir o aviso já publicado" é pedido de **retificação**.
Explique a diferença ao usuário: a peça publicada permanece íntegra no
histórico, e o substitutivo nasce como versão nova, cuja republicação é ato
separado.

## 7. Não classificar documento externo pelo palpite

Confiança baixa, alerta de outro processo ou metadado ausente: o arquivo fica em
quarentena e o usuário decide. Não preencha origem, CNPJ ou data por dedução —
`null` e pendência anotada.

## 8. Não eliminar duplicado provável

Arquivos parecidos e não idênticos ficam os dois, marcados. Só o humano decide
qual sai — e mesmo assim o descarte é para quarentena, não para o lixo.

## 9. Não confiar somente no nome do arquivo

Nome é indício. "TR_final.docx" pode ser mais antigo que "TR.docx"; "proposta.pdf"
pode ser uma certidão. Confirme por data, hash e conteúdo quando houver como, e
diga quando não houve.

## 10. Migração é em dois tempos, sempre

Relatório primeiro, execução depois de confirmação. Nunca execute migração no
mesmo turno em que o usuário pediu apenas "veja como está a pasta". A pasta
original é preservada — diga isso expressamente.

## 11. Não usar `--forcar`, `--ignorar-avisos` ou
`CHARLES_PERMITIR_PROCESSO_NO_REPO` por iniciativa própria

São válvulas de escape para decisão consciente do usuário. Apresente o
impedimento, explique a consequência e espere a decisão.

## 12. Processo real fora do repositório

Antes de criar processo com dado de fornecedor, confirme `CHARLES_PROCESSOS_DIR`.
Não commite arquivo de processo. Não envie documento externo ao GitHub sem
comando expresso.

## 13. Relatar falha como falha

Rollback executado, migração com ressalvas, arquivo não encontrado, lock em uso:
diga o que aconteceu e o que ficou por fazer. Nunca simule que a organização foi
concluída.

## 14. O log e o histórico não se editam

Não reescreva `LOG_DOCUMENTAL.jsonl`, não apague entrada de histórico, não
"limpe" o `90_HISTORICO/`. Manutenção da base documental do processo é ato
administrativo, não faxina.

## 15. Este módulo não substitui a instrução

Organizar a pasta não instrui o processo. Fundamento, enquadramento, pesquisa de
preços, análise jurídica e julgamento seguem os roteiros próprios da base, com
as fontes citadas na forma do `CLAUDE.md`.
