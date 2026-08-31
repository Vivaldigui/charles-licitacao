---
tipo: norma_interna
hierarquia: padrao_visual
tema: excecoes ao padrao visual
fonte: analise das minutas-mae da Camara Municipal de Itanhandu
orgao: camara municipal de itanhandu
versao: 1.0
vigencia: vigente
atualizado_em: 2026-07-25
tags: [padronizacao, excecoes, minutas, docx]
---

# Exceções Autorizadas

Divergências **conhecidas e aceitas** em relação ao padrão de
[`PADRAO_VISUAL_DOCUMENTOS.md`](PADRAO_VISUAL_DOCUMENTOS.md). Estar aqui significa:
a auditoria pode acusar, mas **não** é defeito a corrigir sem decisão humana.

Cada exceção informa: o quê, onde, por quê, o que o módulo faz e o que ficou pendente.

---

## E-01 — Margens diferentes entre minutas

**Onde.** A maioria usa Sup. 4,23 / Inf. 2,50 / Esq. 3,00 / Dir. 2,00 cm. Divergem:
`AVISO`, `DFD`, `JUSTIFICATIVA_DISPENSA_ETP_RISCOS` (4,23/2,22/2,75/0,99);
`TR` (4,23/2,00/3,00/2,50); `CONTRATO` (4,23/2,05/1,50/1,25);
`CONTRATO_COMPRAS` e `CONTRATO_SERVICOS_CONTINUOS` (4,23/2,00/2,00/2,00);
`DECLARACAO_UNIFICADA` e `PROPOSTA_COMERCIAL` (3,49/1,52/1,50/1,50);
`DFD_PARA_PCA` e `JUSTIFICATIVA_CURSO` (2,50/2,50/3,00/3,00).

**Por quê.** A margem superior acomoda o brasão, que é imagem. Mudar margem desloca a
mancha gráfica em relação ao timbre e pode cortar ou desalinhar o cabeçalho.

**O que o módulo faz.** `ajustar_margens: false`. Reporta a divergência em "Problemas
de paginação" e não corrige.

**Pendente.** Decidir se a biblioteca deve convergir para uma única configuração. É
revisão de minuta-mãe, uma a uma, com conferência visual.

---

## E-02 — `DFD_PARA_PCA` usa Times New Roman e timbre em texto

**Onde.** `05_minutas/DFD/DFD_PARA_PCA_MINUTA_MAE.docx`.

**O que diverge.** Fonte Times New Roman (o resto da biblioteca é Calibri); estilo
`Normal` em 11 pt; margens 2,50/2,50/3,00/3,00; e **cabeçalho/rodapé em TEXTO**, não em
imagem — é a única minuta com o endereço institucional escrito no rodapé em vez de
faixa gráfica.

**O que o módulo faz.** O perfil `dfd_pca` declara `fonte_principal: "Times New Roman"`,
de modo que a minuta não é descaracterizada. O cabeçalho em texto continua protegido
como qualquer outro.

**Pendente.** Uniformizar esta minuta ao timbre gráfico e à tipografia da biblioteca —
exige revisão expressa da minuta-mãe e conferência visual.

---

## E-03 — Vermelho como marcação de campo a preencher

**Onde.** `CONTRATO_COMPRAS` (100 *runs* em `FF0000`), `CONTRATO_SERVICOS_CONTINUOS`
(99 em `FF0000`, 15 em `CC0000`), `ETP` (37 em `FF3333`), `TR`, `DFD_PARA_PCA`.

**Por quê.** Nas minutas de contrato o vermelho marca o que o agente precisa completar;
no ETP marca nota de orientação de preenchimento. É **informação**, não erro de estilo.

**O que o módulo faz.** Reporta em "Campos pendentes" como provável instrução de
preenchimento e **não altera a cor**. Só `--normalizar-cores` converte, sob
responsabilidade de quem executa.

**Pendente.** Nada. É o comportamento desejado.

---

## E-04 — `JUSTIFICATIVA_CURSO_CAPACITACAO` fora do padrão tipográfico

**Onde.** `05_minutas/JUSTIFICATIVA_CURSO_CAPACITACAO/JUSTIFICATIVA_ESCOLHA_CONTRATADO_CURSO_MINUTA_MAE.docx`.

**O que diverge.** Estilo `Normal` em **Bookman Old Style 15 pt**; todos os *runs* em
**Arial 14 pt**; margens 2,50/2,50/3,00/3,00; sem `numbering.xml`.

**O que o módulo faz.** Esta minuta usa o perfil `justificativa`, cuja fonte é a
institucional. A padronização **converte Arial 14 em Calibri 12** — mudança visual real
e desejada, mas que altera a aparência da minuta.

**Pendente. ⚠️ Requer conferência humana antes de virar revisão de minuta-mãe.** Se a
Câmara quiser preservar a aparência atual, crie perfil próprio com
`fonte_principal: "Arial"` e o tamanho correspondente, como se fez no `dfd_pca`.

---

## E-05 — `DECLARACAO_UNIFICADA` e `PROPOSTA_COMERCIAL` são modelos para terceiros

**Onde.** As duas minutas do perfil `declaracao`.

**Por quê.** Não são documentos da Câmara: são formulários que o licitante/fornecedor
preenche. Têm margens próprias (3,49/1,52/1,50/1,50) e apenas 2 imagens de cabeçalho.

**O que o módulo faz.** Perfil `declaracao`, com nota explícita de não normalizar
página. Formatação limitada ao essencial.

**Pendente.** Nada.

---

## E-06 — Minutas com comentários internos

**Onde.** `CONTRATO_COMPRAS_ENTREGA_FORN_CONTINUO_MINUTA_MAE.docx` e
`CONTRATO_SERVICOS_CONTINUOS_MINUTA_MAE.docx` contêm `word/comments.xml`.

**Por quê.** São observações de elaboração que ficaram na minuta oficial.

**O que o módulo faz.** Detecta, reporta e **impede** que o documento seja declarado
aprovado — o status vai para `EXIGE CONFERÊNCIA HUMANA`. Não aceita nem rejeita
revisão automaticamente.

**Pendente.** Revisar os comentários e decidir, um a um, se viram texto, se são
descartados ou se permanecem. **Não** é tarefa do módulo.

---

## E-07 — Metadados pessoais nas minutas

**Onde.** Praticamente toda a biblioteca (`creator`, `lastModifiedBy` com nomes de
servidores).

**O que o módulo faz.** Reporta em "Alterações que exigem validação humana". Só limpa
com `--limpar-metadados`.

**Pendente.** Definir se documento publicado (PNCP, portal, diário) deve sair sempre com
metadados limpos. Ver `07_checklists/checklist-lgpd-publicacao.md`.

---

## E-08 — Estilo sem `<w:name>`

**Onde.** `CONTRATO_COMPRAS` e `CONTRATO_SERVICOS_CONTINUOS` têm um estilo cujo nome é
nulo (herança de conversão de formato).

**O que o módulo faz.** Trata como `Normal` (`estilos_docx.nome_do_estilo`). Não quebra
e não remove o estilo.

**Pendente.** Nada — é defeito inócuo do arquivo de origem.

---

## E-09 — Imagens órfãs no pacote

**Onde.** Quase toda a biblioteca. A `TR`, por exemplo, tem 22 imagens, das quais só 11
(`tbr_image*`) são referenciadas pelo cabeçalho e pelo rodapé; as outras 11 (`image*`)
não são referenciadas por nenhum `.rels`.

**Por quê.** Sobra de edições anteriores. O Word e o python-docx as descartam ao salvar.

**O que o módulo faz.** Só protege mídia **referenciada**. A saída fica menor sem
qualquer perda visual.

**Pendente.** Nada.

---

## E-10 — `PCA` tem anexo em paisagem e quadros de duas colunas

**Onde.** `05_minutas/PCA/PCA_MINUTA_MAE.docx`, perfil `pca`.

**O que diverge.** Quatro pontos, todos deliberados:

1. **Anexo I em seção própria, orientação paisagem** (margens 4,23/2,50/2,00/2,00), para
   acomodar as 19 colunas do detalhamento analítico exigido pelos arts. 2º, § 2º, e 3º da
   Portaria nº 04/2024. A seção **não tem** `headerReference` própria: herda cabeçalho e
   rodapé da seção anterior, e o timbre não é recriado.
2. **Tabela 9 acusada como excedendo a área útil.** A auditoria mede a largura contra a
   área útil da **seção 0** (retrato, 8.504 twips). A tabela está na seção 1 (paisagem,
   ~14.570 twips de área útil) e cabe. Falso positivo de seção.
3. **Tabela 0 sem cabeçalho repetido.** É o quadro de créditos, de duas colunas
   chave/valor, com cabeçalho **lateral** e não superior — não há linha de cabeçalho a
   repetir. Mesma situação em qualquer quadro `cabecalho_lateral` da minuta.
4. **Margem direita da seção 0 em 3,00 cm**, herdada da `TR`, sobre a qual a minuta foi
   construída para preservar o timbre. Ver E-01.

Há ainda o aviso *"Seção 1: cabeçalho difere da seção 1"*: a seção não declara referência
de cabeçalho, o que em OOXML significa herança da anterior. É comportamento correto.

**O que o módulo faz.** As quatro divergências estão declaradas em `excecoes` do perfil
`pca`. Reporta, não corrige. O vermelho da minuta marca nota de orientação e campo a
preencher — vale a E-03, e `--normalizar-cores` não deve ser usado aqui.

**Pendente.** Decidir se o Anexo I permanece no corpo do documento ou migra para planilha
apartada, como faz o TCE-MG no modelo de origem. Se migrar, a seção em paisagem sai e as
exceções 1 e 2 deixam de existir.

---

## Como registrar uma nova exceção

Use o próximo número livre e mantenha os cinco campos: **Onde**, **O que diverge / Por
quê**, **O que o módulo faz**, **Pendente**. Se a exceção precisar de tratamento no
código, ela também tem de aparecer em `excecoes` do perfil correspondente em
`PERFIS_DOCUMENTAIS.json` — este arquivo explica, o JSON executa.
