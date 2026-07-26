---
tipo: norma_interna
hierarquia: padrao_visual
tema: limites entre conteudo e formatacao
fonte: base Charles
orgao: camara municipal de itanhandu
versao: 1.0
vigencia: vigente
atualizado_em: 2026-07-25
tags: [padronizacao, formatacao, conteudo, seguranca, docx]
---

# Regras de Formatação — o que pode e o que não pode

## 1. A regra central

**A padronização visual não autoriza a alteração do conteúdo do documento.**

| CONTEÚDO — intocável | FORMATAÇÃO — corrigível |
|---|---|
| redação, fundamentos, valores, datas, nomes | estilos, fontes, tamanhos |
| obrigações, requisitos, cláusulas, condições | negrito, itálico, alinhamento |
| estrutura jurídica | espaçamento, recuos, tabulações |
| ordem das seções prevista na minuta | listas, numeração (nos limites da seção 4) |
| campos preenchidos | bordas, sombreamento, largura de tabelas |
| decisões administrativas | quebras de página, órfãs/viúvas, paginação |

Revisão textual só acontece com **pedido expresso** do usuário, e aí não é mais o modo
de padronização automática.

---

## 2. Como a regra é imposta na prática

Não é promessa: é verificação executada a cada rodada.

1. Extrai-se o conteúdo normalizado **antes** (parágrafos, células de tabela, textos de
   cabeçalho/rodapé), com espaços colapsados e vazios ignorados.
2. Aplica-se a formatação sobre uma cópia em área temporária.
3. Extrai-se o conteúdo normalizado **depois** e calcula-se o hash SHA-256 dos dois.
4. Divergiu? Cada diferença é classificada uma a uma.
5. Havendo **uma única** diferença não autorizada, **o arquivo não é gravado** e o
   status vai para `BLOQUEADO POR ALTERAÇÃO DE CONTEÚDO`.

### Diferenças autorizadas
- parágrafo vazio em excesso removido;
- espaço duplicado colapsado;
- tabulação de alinhamento removida;
- quebra de página duplicada removida;
- **renumeração previamente aprovada** (só com `--corrigir-numeracao` e sem referência
  interna afetada);
- **marcador de campo substituído**, quando o valor foi declarado no preenchimento;
- bloco alternativo não aplicável removido, quando a escolha foi feita antes.

Qualquer outra diferença é registrada e bloqueia a saída.

---

## 3. Partes protegidas

`word/header*.xml`, `word/footer*.xml` e toda a **mídia referenciada** por esses
arquivos são intocáveis. Nenhuma função do módulo escreve nelas.

A verificação usa **assinatura semântica** — textos, quantidade de imagens, quais
imagens são referenciadas e em que dimensões — e não o hash bruto do XML. Motivo: toda
biblioteca que abre e salva um DOCX reserializa a parte e muda os bytes sem mudar nada
visível; comparar bytes daria alarme falso em 100% das execuções. Com a assinatura
semântica, brasão removido, texto de rodapé trocado ou imagem redimensionada
**bloqueiam** a saída, e a reserialização inocente não.

**Imagem órfã não conta.** As minutas carregam imagens que nenhum `.rels` referencia
(sobra de edições antigas — a TR tem 11). O Word e o python-docx as descartam ao
salvar. Isso é limpeza de pacote, não perda de timbre, e por isso a órfã fica fora do
conjunto protegido.

**Cuidado específico com python-docx:** ler `first_page_header` ou `even_page_header` de
uma seção que não os define **cria** a parte no pacote. O módulo só lê partes já
existentes (`partes_cabecalho_rodape`) — auditar não pode alterar o documento auditado.

---

## 4. Numeração

### Nunca renumerar
artigo de lei · inciso citado · número de processo · portaria · decreto · valor · data ·
CATMAT · CATSER · CNAE · CNPJ · CPF · cláusula contratual quando a renumeração dependa
de análise jurídica · referência interna deliberadamente fixada.

Reconhecimento automático: `numeracao_docx.eh_numeracao_protegida`.

### Renumerar apenas se todas as condições forem verdadeiras
1. o perfil permite (`renumeracao_automatica` — **falso** em `contrato` e `termo_aditivo`);
2. o usuário passou `--corrigir-numeracao`;
3. **todos** os problemas detectados são corrigíveis (subitem órfão e mistura de lista
   manual com automática **não** são);
4. com `--validar-referencias-internas`, nenhuma referência ("conforme o item 6", "nos
   termos do subitem 4.2", "cláusula terceira", "Anexo I") fica inconsistente.

Falhou qualquer uma? A renumeração **não é aplicada** e o motivo entra no relatório em
"Correções não aplicadas". Nada é corrigido silenciosamente.

---

## 5. Fragmentação

Documento com excesso de tópicos é **sinalizado, nunca consolidado**. Fundir parágrafos
é alteração de conteúdo. No modo automático o módulo apenas reporta; a consolidação
exige autorização expressa e jamais pode eliminar requisito ou obrigação.

---

## 6. Cores

Texto avermelhado é tratado como **provável campo a preencher ou nota de orientação** —
é assim que as minutas de contrato e o ETP o usam. É reportado como pendência e não é
alterado. `--normalizar-cores` existe, está desligado por padrão e é responsabilidade
de quem o aciona. *Runs* dentro de hyperlink nunca têm cor alterada.

---

## 7. Formatação semântica

Negrito, itálico e sublinhado **não são removidos**: carregam significado. O módulo
mexe em nome de fonte, tamanho e (sob pedido) cor.

---

## 8. Nomes de arquivo

O arquivo de entrada **nunca** é sobrescrito — a saída igual à entrada é recusada com
erro. Convenção:

```text
TR_MINUTA_MAE.docx                     minuta-mãe (biblioteca oficial)
TR_PREENCHIDO_RASCUNHO.docx            preenchido, antes da formatação
TR_PREENCHIDO_FORMATADO.docx           saída padronizada
TR_PREENCHIDO_FORMATADO_RELATORIO.md   relatório
TR_PREENCHIDO_FORMATADO_RELATORIO.json relatório estruturado
```

Gravar dentro de `05_minutas/` levanta `PermissionError`, salvo em modo revisão.

---

## 9. Modo revisão de minuta-mãe

Só com pedido expresso. A sequência é obrigatória e nesta ordem:

1. backup em `05_minutas/<TIPO>/_arquivo/<nome>_vX.Y.docx`;
2. relatório do estado anterior gravado ao lado;
3. correções aplicadas;
4. versão incrementada na ficha de uso (`versao:` e `atualizado_em:`);
5. entrada no changelog da pasta;
6. `_CONTROLE_MINUTAS.md` atualizado (**passo manual**, sinalizado no relatório).

Bloqueou na validação? A minuta-mãe **não é tocada** e o backup permanece.

---

## 10. Comentários, revisões e metadados

Comentários internos, controle de alterações e texto oculto são **detectados e
reportados**, nunca aceitos ou rejeitados automaticamente — o conteúdo de uma revisão
pode ser juridicamente relevante. Metadados pessoais (autor, último editor) só são
limpos com `--limpar-metadados`. Documento com comentário interno nunca sai com status
de aprovado.

---

## 11. Idempotência

Formatar duas vezes tem de dar o mesmo resultado. Toda execução roda a verificação
automaticamente e informa o resultado em "Resultado dos testes". Falhou? O status vai
para `EXIGE CONFERÊNCIA HUMANA`.

---

## 12. Validação visual

Se houver LibreOffice/`soffice`, converte-se para PDF e conferem-se páginas, tabelas
cortadas e títulos isolados. **Não havendo, não se simula**: o relatório registra
`validação visual não executada`. O módulo nunca afirma ter feito conferência visual
que não fez.

---

## 13. Proibições absolutas

O módulo nunca deve: alterar conteúdo jurídico silenciosamente · excluir cláusula ·
inventar título ou seção · mudar a ordem oficial da minuta · alterar timbre · remover
brasão · recriar cabeçalho sem necessidade · apagar rodapé · substituir assinatura ·
transformar o documento em listas · usar várias fontes · usar cores aleatórias ·
aplicar estilo publicitário · criar capa desnecessária · renumerar artigo de lei ·
renumerar cláusula contratual ambígua · sobrescrever a minuta-mãe · aceitar documento
com marcador pendente sem alerta · afirmar conferência visual não executada.
