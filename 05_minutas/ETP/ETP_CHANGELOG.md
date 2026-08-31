---
tipo: checklist
hierarquia: oficial
tema: changelog minuta etp
fonte: 05_minutas/_CONTROLE_MINUTAS.md
vigencia: vigente
atualizado_em: 2026-08-12
tags: [minutas, changelog, governanca]
---

# Changelog — ETP

## ETP_MINUTA_MAE.docx — v1.4 — 2026-08-12

- **Removido `keepNext`/`keepLines` herdado de praticamente todo parágrafo de corpo.** Era resíduo
  da estrutura em tabela-envelope da v1.3: quando cada seção era uma tabela de 1 linha só, a
  formatação automática ligava esses flags em todo parágrafo daquela linha (regra pensada para
  cabeçalho de tabela de verdade). O achatamento da v1.3 mudou o estilo dos parágrafos, mas não
  desligou o flag herdado — e parágrafos de corpo encadeados por `keepNext` formam um bloco que "não
  pode dividir" entre páginas, pulando inteiro quando não cabe e deixando a página anterior com um
  vão em branco (num caso, uma página saiu totalmente vazia).
- **Motivo:** pedido do usuário — "o etp esta com quebras e espaços em branco, principalmente apos
  tabelas, corrija isso" e, após uma primeira limpeza incompleta (só parágrafos vazios em excesso),
  "cheio de quebras e espaços em branco ainda".
- **Correção de escopo geral em `scripts/docx_cmi/estilos_docx.py`** (`aplicar_formatacao_paragrafo`):
  agora desliga `keepNext`/`keepLines` explicitamente em qualquer parágrafo que não seja título,
  assinatura ou cabeçalho de tabela — vale para qualquer documento/perfil formatado a partir de
  agora, não só o ETP.
- **Resultado no ETP de Assessoria Patrimonial** (documento gerado do processo): 43 → **33 páginas**
  no Word, 44 → **33** no LibreOffice — os dois conversores convergem agora. Zero páginas vazias ou
  com menos de 50% da área útil ocupada (antes: 1 página totalmente vazia + 6 com baixa ocupação).
  Ver `08_processos/em_andamento/ASSESSORIA_PATRIMONIAL/ETP_VALIDACAO_VISUAL.md`, seção 10.
- Conteúdo textual conferido idêntico (hash) antes/depois, na minuta-mãe e no documento gerado.
- Responsável pela revisão: gui.rib.pi@gmail.com (via Charles).
- Backup do arquivo anterior: `05_minutas/ETP/_backups/ETP_MINUTA_MAE_20260812_220725.docx`.

## ETP_MINUTA_MAE.docx — v1.3 — 2026-08-12

- **As 14 seções deixam de usar tabela-envelope de 1 coluna como estrutura.** Cada seção era uma
  única linha de tabela com `cantSplit` (não dividir); virou parágrafo de título com estilo
  `CMI Titulo 1` seguido de parágrafo(s) de corpo com `CMI Corpo`, em texto corrido.
- **Motivo:** ao gerar o ETP de Assessoria Patrimonial (Solicitação nº 31/2026) e validar a
  renderização no Microsoft Word, o `cantSplit` combinado com o cinza de fundo do envelope
  produzia páginas quase vazias e, num achado mais grave na mesma conferência, os quadros de
  dados aninhados (alternativas, resultados pretendidos, etapas, cesta de preços) colapsavam para
  uma coluna de um caractere por linha, ocupando a página inteira — o documento saía com
  "fundo cinza" cobrindo quase a página toda e viravam ~114 páginas em vez de ~31/44. A causa raiz
  identificada foi um `tblW` (largura declarada da tabela) deixado como `type="auto" w="0"` pelo
  `python-docx` mesmo com o `tblGrid` já tendo larguras de coluna explícitas — o Word (ao contrário
  do LibreOffice) trata isso como "sem largura declarada" e encolhe as colunas ao mínimo.
  Pedido expresso do usuário: "TIRE AS ORGANIZAÇÃO POR TABELA E O FUNDO CINZA, FORMATE E ORGANIZE
  O ETP", com decisão de aplicar também à minuta-mãe e de manter os 4 quadros de dados como
  tabela (só corrigindo a largura).
- **Sombreamento cinza (D9D9D9) removido** de todas as células remanescentes. O perfil `etp` em
  `09_padronizacao_documental/PERFIS_DOCUMENTAIS.json` ganhou
  `"tabelas_overrides": {"sombrear_cabecalho": false}` para que o pipeline de padronização não volte
  a aplicar esse sombreamento em execuções futuras.
- **Correção estrutural em `scripts/docx_cmi/tabelas_docx.py` (`_reescalar`):** agora sempre grava
  `tblW type="dxa"` batendo com a soma do `tblGrid` (antes só corrigia quando a tabela excedia a
  área útil), e define `tblLayout type="fixed"`. Vale para qualquer tabela de qualquer perfil, não
  só o ETP — corrige a causa raiz do colapso de coluna no Word onde quer que ela ocorra.
- **Preservados:** timbre/cabeçalho/rodapé, as 14 seções, sua ordem e numeração, os textos fixos
  "PREENCHIMENTO OBRIGATÓRIO/FACULTATIVO" e "DEFINIÇÃO:" (que já viviam fora da tabela, como
  parágrafo solto, e não foram tocados), as notas em vermelho (FF3333) e os 4 quadros de dados
  (agora com largura corrigida). Conteúdo textual conferido idêntico caractere a caractere antes e
  depois (script `scripts/docx_cmi/achatar_envelopes_etp.py`).
- Aplicado também ao documento já gerado do processo:
  `08_processos/em_andamento/ASSESSORIA_PATRIMONIAL/ETP_ASSESSORIA_PATRIMONIAL.docx` (backup em
  `_backups_docx/` da própria pasta do processo). Ver
  `08_processos/em_andamento/ASSESSORIA_PATRIMONIAL/ETP_VALIDACAO_VISUAL.md`, seção 8, para a
  conferência visual pós-correção (Word: 114 → 43 páginas, sem colapso de coluna; LibreOffice:
  31 → 44 páginas).
- Responsável pela revisão: gui.rib.pi@gmail.com (via Charles).
- Backup do arquivo anterior: `05_minutas/ETP/_backups/ETP_MINUTA_MAE_20260812_214921.docx`.

Registro de evolu??o das minutas-m?e desta pasta. Hist?rico anterior ? vers?o atual n?o foi inventado.

## ETP_MINUTA_MAE.docx — v1.2 — 2026-07-26

- **Removida a página de capa.** O documento passa a iniciar diretamente com o título
  ("ESTUDO TÉCNICO PRELIMINAR") e a linha "Solicitação nº {{NUMERO_SOLICITACAO}}", seguidos da
  INTRODUÇÃO. Foram excluídos: as linhas em branco de diagramação da capa, o campo `{{OBJETO}}`,
  a linha de data da capa (`{{LOCAL}}, {{MES}} de {{ANO}}`) e o título duplicado
  "ESTUDO TÉCNICO PRELIMINAR DA CONTRATAÇÃO".
- **Campo descontinuado:** `{{OBJETO}}` deixa de existir na minuta (era usado só na capa). O objeto
  continua descrito nas seções 1, 3 e 7. `{{LOCAL}}`, `{{MES}}` e `{{ANO}}` permanecem, pois também
  são usados no bloco de assinatura (seção 14).
- Motivo: pedido expresso do usuário ("tirar essa página de capa, só colocar um título e a
  solicitação de compra").
- Preservados: timbre/cabeçalho/rodapé, as 14 seções, sua ordem e numeração, as linhas fixas
  "PREENCHIMENTO OBRIGATÓRIO/FACULTATIVO" e "DEFINIÇÃO:", e o bloco de assinatura (16 tabelas).
- Responsável pela revisão: gui.rib.pi@gmail.com (via Charles).
- Backup do arquivo anterior: `05_minutas/ETP/_backups/ETP_MINUTA_MAE_20260726_162920.docx`.

## ETP_MINUTA_MAE.docx — v1.1 — 2026-07-26

- Removido o preenchimento cinza (fundos das caixas de seção) das células: `CCCCCC` (14 seções),
  `B2B2B2` (INTRODUÇÃO) e `EEEEEE` (bloco de assinatura), neutralizados para `auto`. As bordas, o
  texto, a numeração e a ordem das seções foram preservados; nenhum conteúdo foi alterado.
- Motivo: pedido expresso do usuário — os documentos gerados saíam com fundo cinza nas seções.
- Responsável pela revisão: gui.rib.pi@gmail.com (via Charles).
- Backup do arquivo anterior: `05_minutas/ETP/_backups/ETP_MINUTA_MAE_20260726_114430.docx`.

## ETP_MINUTA_MAE.docx ? v1.0 ? 2026-07-01

- Registro retroativo da vers?o atual cadastrada no `_CONTROLE_MINUTAS.md`.
- Minuta-m?e oficial existente na biblioteca da C?mara.
- [VALIDA??O HUMANA] Hist?rico anterior n?o registrado nesta base.
