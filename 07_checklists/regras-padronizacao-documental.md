---
tipo: checklist
hierarquia: oficial
tema: regras inegociaveis da padronizacao documental
fonte: base Charles
orgao: camara municipal de itanhandu
versao: 1.0
vigencia: vigente
atualizado_em: 2026-07-25
tags: [checklist, padronizacao, formatacao, docx, regras, seguranca]
---

# Regras — Padronização e Formatação Documental

Regras **inegociáveis**. O roteiro operacional está em
[`roteiro-padronizacao-documental.md`](roteiro-padronizacao-documental.md); o
detalhamento técnico, em
[`09_padronizacao_documental/REGRAS_DE_FORMATACAO.md`](../09_padronizacao_documental/REGRAS_DE_FORMATACAO.md).

---

## R1. Formatação não é conteúdo

A padronização visual **não autoriza** alterar redação, fundamento, valor, data, nome,
obrigação, requisito, cláusula, condição, ordem das seções ou decisão administrativa.
Revisão textual só com pedido expresso — e aí já não é padronização automática.

## R2. A minuta-mãe é a fonte

A geração continua **travada** nas minutas de `05_minutas/`. O módulo formata o que
existe; não cria estrutura, seção, cláusula ou capa. Não há minuta adequada? **Pare e
avise.**

## R3. O original nunca é sobrescrito

Saída igual à entrada é recusada. Gravar em `05_minutas/` é recusado, salvo em modo
revisão de minuta-mãe — que exige backup, versionamento e changelog.

## R4. Timbre é intocável

Cabeçalho, rodapé, brasão, logotipo, endereço, telefone e e-mail institucionais não são
recriados, redimensionados, reposicionados nem convertidos em texto. Divergência
bloqueia a saída.

## R5. Numeração jurídica não se renumera

Artigo, inciso, número de processo, portaria, decreto, valor, data, CATMAT, CATSER,
CNAE, CNPJ e CPF nunca. Cláusula contratual: só com análise jurídica — o perfil
`contrato` proíbe renumeração automática.

## R6. Referência interna quebrada trava a correção

Se a renumeração invalidar "conforme o item 6", "nos termos do subitem 4.2", "cláusula
terceira" ou "Anexo I", a correção **não é concluída silenciosamente**: vira pendência
para validação humana.

## R7. Fragmentação se sinaliza, não se consolida

Fundir tópicos altera conteúdo. No modo automático, apenas reporte. Consolidar exige
autorização expressa e nunca pode eliminar requisito ou obrigação.

## R8. Vermelho é dado, não defeito

Nas minutas, texto avermelhado marca campo a preencher ou nota de orientação. Reporte;
não recolora sem `--normalizar-cores` e sem decisão do usuário.

## R9. Negrito, itálico e sublinhado ficam

Têm função semântica. O módulo mexe em fonte, tamanho e (sob pedido) cor.

## R10. Campo pendente impede "pronto para assinatura"

`{{CAMPO}}`, `[PREENCHER...]`, `(definir...)`, `____`, bloco `OU` não resolvido e opção
`( )` não marcada: liste **todos** e nunca declare o documento pronto.

## R11. Comentário e revisão não se resolvem sozinhos

Controle de alterações não é aceito nem rejeitado automaticamente; comentário interno
não é apagado. Detecte, informe, e nunca entregue documento final com comentário sem
alerta expresso.

## R12. Conferência visual não se simula

**Nunca** afirme ter conferido visualmente o que não conferiu, nem culpe o ambiente sem
ter procurado a ferramenta. Havendo LibreOffice ou Word, a validação visual **roda** por
padrão na CLI (`--sem-validacao-visual` desliga): entrada e saída são renderizadas em PDF
e comparadas — nº de páginas e páginas em branco novas. Sem conversor, registre
"validação visual não executada" com o motivo verdadeiro. A validação estrutural continua
valendo nos dois casos.

O que a validação visual **não** diz: que o documento está bonito, alinhado ou pronto
para assinatura. Mudança de paginação é consequência esperada de reformatar; por isso ela
nunca bloqueia a gravação — no máximo exige conferência humana (PDF que não abre, página
em branco nova). A conferência final no Word continua sendo do usuário.

## R13. Idempotência

Formatar duas vezes tem de dar o mesmo resultado. Falhou? Status `EXIGE CONFERÊNCIA
HUMANA`.

## R14. Toda execução gera relatório

Markdown + JSON, com as seções fixas e o status. O relatório é o que se anexa ao
processo.

## R15. Honestidade no resultado

Não afirme que o documento está perfeito. Diga o que foi corrigido, o que não foi, o
que ficou pendente e o que depende de pessoa. Documento externo é referência visual,
nunca norma da Câmara.

---

## Proibições absolutas

Alterar conteúdo jurídico silenciosamente · excluir cláusula · inventar título ou seção ·
mudar a ordem oficial da minuta · alterar timbre · remover brasão · recriar cabeçalho
sem necessidade · apagar rodapé · substituir assinatura · inventar nome, cargo, data,
assinatura digital ou código de verificação · transformar o documento em listas · usar
várias fontes · usar cores aleatórias · aplicar estilo publicitário · criar capa
desnecessária · sobrescrever a minuta-mãe · aceitar documento com marcador pendente sem
alerta · afirmar conferência visual não executada.
