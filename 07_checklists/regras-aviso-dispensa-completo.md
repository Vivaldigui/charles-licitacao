---
tipo: checklist
hierarquia: oficial
tema: regras inegociaveis do aviso de dispensa completo
fonte: base Charles
orgao: camara municipal de itanhandu
versao: 1.0
vigencia: vigente
atualizado_em: 2026-07-25
tags: [checklist, aviso, anexos, dispensa, contratacao-direta, regras, seguranca]
---

# Regras — Aviso de Dispensa Completo

Regras **inegociáveis** da montagem do aviso com seus anexos. O roteiro operacional está
em [`roteiro-gerar-aviso-dispensa-completo.md`](roteiro-gerar-aviso-dispensa-completo.md).

---

## R1. O aviso completo não é o processo completo

O aviso completo é a **peça de divulgação**: aviso + anexos que o fornecedor precisa para
propor. Não é o processo administrativo, não contém DFD, ETP, pesquisa de preços,
certidão orçamentária, autorização nem parecer jurídico. Confundir os dois publica
documento interno.

## R2. Só minuta oficial

Aviso, modelo de proposta, declaração e contrato vêm **exclusivamente** de
`05_minutas/`. Não se improvisa modelo, não se copia modelo de outro órgão, não se
"melhora" a estrutura. Sem minuta adequada, **pare e avise** — para contrato, com a
frase exata: *"Não há minuta de contrato oficial adequada cadastrada para este objeto."*

## R3. O TR é o do processo, e é anexado como está

O Termo de Referência **não é gerado** na montagem. É o TR já elaborado e aprovado.
É proibido usar minuta-mãe vazia, TR de outro processo, TR com campo pendente ou TR
identificado como rascunho (salvo autorização expressa). O conteúdo do TR **não é
alterado** durante a montagem.

## R4. O Anexo I não é duplicado

O Anexo I já está incorporado à minuta-mãe do aviso. Ele é **recortado** de lá para
existir como arquivo separado — nunca recriado em minuta paralela.

## R5. Habilitação é proporcional, e divergência não se resolve sozinha

Nenhuma exigência entra porque aparece em aviso de outro órgão. Qualificação técnica e
econômico-financeira só quando previstas no TR, justificadas, proporcionais, autorizadas
pela minuta e confirmadas pelo setor responsável. Divergência entre TR e Anexo I é
**reportada**, nos dois sentidos, e decidida por pessoa.

## R6. Preço é do fornecedor

Marca, modelo, valor unitário, valor total, valor global e dados cadastrais do proponente
ficam em branco. **Nunca** se preenche proposta em nome do fornecedor.

## R7. Quem decide se haverá contrato é o processo

O Charles não decide sozinho. A decisão vem, nesta ordem: campo estruturado do processo →
determinação expressa do usuário → Termo de Referência → autorização da contratação →
ficha de uso → documento oficial do processo. Divergência ou silêncio **bloqueia** a
montagem com a pendência:

> PENDÊNCIA: definir se a contratação será formalizada por contrato ou instrumento
> equivalente.

Minuta de contrato **nunca** é escolhida por semelhança do nome do objeto. Com nota de
empenho, ordem ou autorização de fornecimento, **não** se anexa minuta de contrato.

## R8. Numeração de anexo é a única que se toca

Com contrato: I habilitação · II TR · III proposta · IV contrato · V declaração.
Sem contrato: I habilitação · II TR · III proposta · IV declaração.

Sem lacuna, sem duplicidade. Artigo, inciso, cláusula, número de processo, número de
dispensa, CATMAT/CATSER/CNAE e itens do TR **não são renumerados**. Referência a anexo
inexistente é erro bloqueante.

## R9. Timbre é intocável

Cabeçalho, rodapé e brasão não são recriados, redimensionados nem substituídos. No
documento único prevalece o timbre oficial do aviso; timbre divergente em componente é
reportado. Timbre de outro órgão é achado grave.

## R10. Nada é sobrescrito

O arquivo de entrada nunca é sobrescrito. Gravar em `05_minutas/` é recusado. A saída vai
para `08_processos_em_andamento/[PROCESSO]/07_AVISO_COMPLETO/`.

## R11. Conteúdo preservado, ou não grava

Toda linha dos componentes tem de aparecer no documento único. Perda de linha é erro
bloqueante. O único acréscimo autorizado é o rótulo do anexo ("ANEXO II — ...") e, quando
pedido, a marca de rascunho.

## R12. Campo pendente impede dar por pronto

Marcador `{{...}}`, `[PREENCHER]` e bloco "OU" não resolvido bloqueiam a geração final.
Lacuna reservada ao proponente e lacuna da minuta de contrato que só se preenche na
assinatura **não** são defeito — mas são listadas, e impedem tratar o documento como
pronto para assinatura.

## R13. "APTO PARA PUBLICAÇÃO" não é status automático

A automação concede, no máximo, **APTO PARA CONFERÊNCIA**. A publicação depende de
conferência humana final, sempre declarada no relatório.

## R14. O que não existe, não se afirma

Sem conversor de PDF no ambiente, registra-se que a conversão não foi executada — não se
afirma um PDF que não existe. Sem LibreOffice, a validação visual fica registrada como
não executada, e a validação estrutural continua valendo.
