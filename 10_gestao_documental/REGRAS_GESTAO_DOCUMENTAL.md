---
tipo: norma_interna
hierarquia: operacional
tema: regras da gestao documental dos processos
fonte: base Charles
vigencia: vigente
atualizado_em: 2026-07-25
tags: [gestao documental, regras, versionamento, rastreabilidade]
---

# Regras da Gestão Documental

## 1. Princípio central

**Para cada tipo documental existe um, e apenas um, arquivo de trabalho visível.**

```
01_EM_ELABORACAO/
├── DFD.docx
├── ETP.docx
└── TR.docx
```

Nunca são gerados `TR_1.docx`, `TR_novo.docx`, `TR_final.docx`,
`TR_final_corrigido.docx`, `Cópia de TR.docx` ou `TR (1).docx`. O número da
versão vive no manifesto, não no nome do arquivo corrente.

Quando uma nova versão substitui a atual, nesta ordem: a anterior sai da área
corrente, vai ao histórico com número de versão, é registrada no manifesto, e a
nova assume o nome canônico.

## 2. Arquivo único não significa apagar versão

Documento administrativo precisa de rastreabilidade. As versões anteriores
continuam existindo — em `90_HISTORICO/`, com versão, carimbo de tempo, hash e
motivo. O que elas não fazem é continuar ao lado do arquivo atual, confundindo
quem abre a pasta.

## 3. Alteração real, e só ela, gera versão

Antes de arquivar e substituir, comparam-se o hash binário e o **conteúdo
textual normalizado**, incluindo tabelas, cabeçalho e rodapé. Salvar um DOCX de
novo muda os bytes sem mudar uma vírgula do texto: isso é mudança de metadado
interno, e **não** cria versão. O evento é registrado como
`geracao_sem_alteracao` e o arquivo vigente permanece.

## 4. Estados imutáveis

- **Assinado** é imutável. Nunca se sobrescreve documento assinado.
- **Publicado** é imutável. Mudança gera retificação, documento substitutivo e
  nova publicação, com a relação entre as versões registrada.
- **Aprovado** não é silenciosamente substituído: exige motivo e responsável.
- **Rascunho** e **em elaboração** podem ser substituídos, desde que a versão
  anterior seja arquivada.

A única porta de saída de assinado e publicado é a **retificação**, que preserva
a peça imutável no histórico e abre versão nova em revisão.

## 5. Versão ≠ formato

`TR.docx` e `TR.pdf` podem ser o mesmo conteúdo em formatos diferentes. Eles são
**representações** da mesma versão, não duas versões. O PDF assinado não
substitui o DOCX editável no registro.

## 6. Nenhum gerador grava direto na pasta do processo

Todo documento gerado passa por `registrar_saida_gerada`, que executa sempre a
mesma sequência: sessão temporária → validação → campos pendentes → hash →
comparação → decisão de alteração → arquivamento da anterior → movimento
atômico → manifesto → log → painel → limpeza.

## 7. Falha não deixa estado pela metade

Toda substituição é transacional. Se algo falha no meio: o documento anterior
permanece onde estava, nenhum arquivo incompleto sobra, o erro é registrado e os
temporários são isolados. Manifesto e arquivos nunca divergem.

## 8. Concorrência

Duas gerações simultâneas do mesmo documento não coexistem: há lock por processo
e tipo (`.locks/TR.lock`). Lock abandonado é recuperado apenas quando o prazo
expirou ou o PID que o criou não existe mais nesta máquina — e a recuperação
fica registrada. Na dúvida, o lock é respeitado.

## 9. Documento externo não se mistura ao gerado

Proposta, cotação, certidão, declaração, parecer, ofício, comprovante, e-mail,
nota fiscal, catálogo e referência do PNCP entram por `98_QUARENTENA/`, são
identificados por hash, classificados, conferidos quanto a duplicidade e
pertencimento ao processo, renomeados pelo padrão e só então movidos para
`03_DOCUMENTOS_EXTERNOS/<categoria>/`.

**O arquivo original nunca é alterado.** Ele entra por cópia e o nome original
fica gravado no manifesto.

## 10. Duplicidade

- **Exata** (mesmo SHA-256): não se copia de novo; registra-se a tentativa e
  aponta-se o arquivo já existente.
- **Provável** (nome, tamanho ou texto parecidos): os dois ficam, marcados como
  possíveis versões, e a decisão é humana. Duplicado provável **não** se elimina
  automaticamente.

## 11. Documento de outro processo

Antes de registrar, conferem-se número do processo, objeto, fornecedor, datas e
referências internas. Aparentando pertencer a outro processo, o arquivo **não**
vai para a pasta oficial: permanece em quarentena, com alerta, aguardando
confirmação.

## 12. Metadado ausente é `null`

Origem, CNPJ, data e tipo que não constam do documento entram como `null`, com
pendência anotada. Não se inventa metadado, nem se deduz fornecedor pelo nome do
arquivo. Confiar somente no nome do arquivo é proibido.

## 13. O que não foi verificado é dito

PDF sem extrator de texto: os campos pendentes **não** foram verificados, e o
registro diz isso. Validação não executada aparece como `nao_executada`, nunca
como "aprovado" por omissão.

## 14. Restauração não volta o contador

Restaurar o conteúdo da versão 2 quando a atual é 5 cria a versão **6**, com
origem registrada como restauração da 2. A versão 5 vai para o histórico. Nada
é apagado, nada é reescrito.

## 15. O log só cresce

`LOG_DOCUMENTAL.jsonl` recebe uma linha por evento. Evento antigo não é
reescrito nem removido.

## 16. Limpeza é estreita

A limpeza automática só alcança `99_TEMPORARIOS/` e locks vencidos. Nunca são
apagados automaticamente: documento assinado, documento publicado, proposta,
certidão, e-mail, parecer, documento externo, versão histórica ou comprovante.
O que poderia ser removido vai primeiro para quarentena.

## 17. Migração planeja antes de mexer

A organização de pasta antiga produz **primeiro um relatório**, e só executa
depois de confirmação. A pasta original é preservada intacta como backup — a
migração copia, não move. Quando a versão vigente é ambígua (duas candidatas com
a mesma data), a migração **bloqueia** e pede escolha humana em vez de chutar.

## 18. Processo real fora do repositório

Documento com dado pessoal ou de fornecedor não vai para repositório público.
`CHARLES_PROCESSOS_DIR` define onde ficam os processos reais;
`08_processos_em_andamento/` neste repositório guarda apenas exemplo fictício.
Nada é enviado ao GitHub sem comando expresso do usuário.

---

## Regras inegociáveis (o que nunca se faz)

- apagar versão anterior sem registro;
- sobrescrever documento assinado ou publicado;
- classificar documento externo sem rastreabilidade;
- alterar arquivo original recebido;
- colocar proposta junto às minutas;
- deixar arquivo temporário na raiz do processo;
- criar arquivos "final_final";
- criar versão sem alteração real;
- misturar documentos de processos diferentes;
- enviar documento sensível a repositório público;
- confiar somente no nome do arquivo;
- excluir duplicado provável sem validação humana;
- atualizar manifesto sem atualizar arquivos, ou o contrário;
- terminar uma operação parcialmente;
- simular que a organização foi concluída;
- esconder falha de migração;
- usar exemplo com dado pessoal real.
