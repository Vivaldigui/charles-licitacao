# Changelog

Registro da evolução da base Charles. Entradas retroativas foram montadas a partir do histórico
Git local disponível em 2026-07-01, sem inventar detalhes não verificáveis.

## 2026-10-06 — Controle CNAE: classificação item a item e claraboia

- Método item a item adotado para processos com vários itens, com a regra "cesta + exceções"
  (roteiro `07_checklists/roteiro-limite-dispensa-cnae.md`, item 2-A). PAs 006, 013 e 016/2026
  desmembrados por subclasse, com valores dos termos de homologação; o registro passou de 36 para
  44 linhas, sem alteração de totais.
- Subclasse 4751-2/01 (informática): de R$ 61.212,38 (93,5%, vermelho) para R$ 33.554,47 (51,2%,
  verde). Novas subclasses no controle: 4752-1/00, 4789-0/08, 4757-1/00, 5611-2/03, 4723-7/00,
  4784-9/00.
- PA 020/2026 (claraboia) reclassificado de 4743-1/00 para 2512-8/00. PA 035/2026 mantido em
  4321-5/00, inciso II.
- Formalização do método por despacho do agente de contratação registrada como pendência.

## 2026-10-06 — Controle CNAE: critério do objeto e contratações de jul.–set./2026

- Pesquisa sobre "ramo de atividade" (art. 75, §1º, II): o enquadramento é pelo **objeto**, não
  pelo CNAE do fornecedor (Consulta TCEMG 1104833, p. 9). Fichas novas:
  `04_doutrina_artigos/estudo-ramo-atividade-objeto-ou-fornecedor-cnae.md` e
  `03_jurisprudencia/tce_sp/resolucao-tcesp-16-2025-ramo-de-atividade-dispensa.md`.
- `07_checklists/roteiro-limite-dispensa-cnae.md`: novo item 2-A (objeto x fornecedor, objeto
  misto, objeto com instalação, vedação de escolher subclasse pelo vencedor).
- Controle de contratações: 11 contratações registradas (6 dispensas e 5 inexigibilidades,
  homologadas/ratificadas entre 27/07 e 30/09/2026); PA 001/2026 reclassificado de 4751-2/01 para
  6319-4/00; análise do exercício reescrita. A subclasse 4751-2/01 passou a 93,5% do limite
  (vermelho). Numeração de quatro dispensas pendente de confirmação no SICOM.

## 2026-09-23 — Aviso de contratação direta v2.1 e fim do módulo "Aviso Completo"

- Minuta-mãe do aviso substituída pela Minuta-Mãe 2026 revisada (v2.0) e depois revisada (v2.1):
  Anexo I de habilitação incorporado no molde dos modelos de aviso de dispensa, reserva de cargos
  PcD no item 3.9, Diário Oficial do Município no 8.1, cotação com 3 fornecedores no 9.1 e
  relação de anexos no 10.8. Ficha de uso reescrita como manual rápido. Ver
  `05_minutas/AVISO/AVISO_CHANGELOG.md`.
- Nova ficha de lei: `01_legislacao/lc-123-2006-estatuto-microempresa-epp.md` (texto compilado do
  Planalto, sem trechos tachados).
- Novo acervo de referência: `14_referencias_externas/modelos_aviso_contratacao_direta/` (modelo AGU
  abr/2026 e modelo de dispensa eletrônica do Portal de Compras Públicas); originais em `_entrada/`.
- **Removido o módulo "Aviso Completo"**, a pedido do usuário: `scripts/aviso_completo/`,
  `99_testes/aviso_completo/`, `05_minutas/AVISO_COMPLETO/`,
  `07_checklists/roteiro-gerar-aviso-dispensa-completo.md` e `regras-aviso-dispensa-completo.md`,
  seção do `CLAUDE.md`, do `README.md` e dependência `docxcompose`. O tipo documental
  `AVISO_COMPLETO` da gestão documental foi mantido (processos já registrados continuam válidos).
  Os arquivos seguem recuperáveis pelo histórico do Git.

## 2026-08-10 — Contratações do TCE-MG coletadas como referência externa

- Arquivos: `scripts/tce_mg_licitacoes.py` (novo), `scripts/tce_mg_fichas.py` (novo),
  `14_referencias_externas/` (nova), `CLAUDE.md`, `00_indices/INDICE_GERAL.md`.
- O que mudou:
  - o Portal da Transparência do TCE-MG publica, por contratação, uma "DOC Interna/Externa" —
    PDF único com as peças do processo SEI que o Tribunal divulga. Não há API aberta: o front
    Angular autentica por captcha e guarda um JWT de ~2h em `localStorage`. O novo
    `tce_mg_licitacoes.py` recebe esse token já obtido no navegador (`--token-file`) e repete as
    mesmas chamadas da página; não resolve captcha e não faz login;
  - coletadas **75 contratações distintas** sob a Lei 14.133/2021 (18 dispensas, 57 pregões,
    fontes SIAD e Admin TCEMG), **83 PDFs / ~271 MB**. **12** responderam HTTP 404 — o botão
    existe na tela, não há arquivo; **1** veio digitalizado, sem camada de texto. As três
    situações estão registradas nas fichas e no índice, nenhuma foi suposta;
  - `tce_mg_fichas.py` lê o rodapé do SEI de cada página para reconstruir as peças que compõem
    cada documentação, separa o dispositivo **adotado como fundamento** (precedido de "com
    fundamento/arrimo/fulcro no") do que é **apenas citado** no texto, e transcreve a lista de
    documentos que o parecer diz instruírem o processo. Tudo marcado como extração automática, a
    conferir no PDF;
  - quatro análises: instrução da dispensa, fase interna do pregão, modelos padronizados
    (TR, ETP, edital de 14 seções + 9 anexos, contrato de 19 cláusulas) e o confronto com
    Itanhandu, com cinco medidas aplicáveis e o que não vale copiar;
  - achado central: **nenhuma dispensa por valor (art. 75, I/II) tem documentação instrutória
    publicada** — os casos publicados são art. 75, VIII, IX e III. Para o rito que a Câmara mais
    usa, a referência útil do TCE-MG é a **norma** (Portaria 02/PRES./2024, já em
    `03_jurisprudencia/tce_mg/atos_normativos/`), não o exemplo;
  - PDFs brutos e texto extraído ficam em `_entrada/tce_mg_licitacoes/`, já coberto pelo
    `.gitignore` — são documentos de terceiros, com nome de servidor e dados de habilitação de
    fornecedor. O que a base cita são as fichas.
- Limite declarado: a coleta correu em ambiente sem renderização de tela, então **não há print**
  do portal. No lugar, cada arquivo tem URL, data/hora de acesso, status HTTP, tamanho e sha256
  em `EVIDENCIAS_DOWNLOAD.json`. Quem precisar do print para juntar aos autos deve capturá-lo.

## 2026-08-07 — Validação visual deixa de ser texto fixo e passa a rodar

- Arquivos: `scripts/docx_cmi/validacao_visual_docx.py` (novo),
  `scripts/docx_cmi/formatar_docx.py`, `scripts/docx_cmi/relatorio_docx.py`,
  `scripts/aviso_completo/gerar_pacote_publicacao.py`, `07_checklists/`, `CLAUDE.md`,
  `99_testes/padronizacao_documental/`.
- O que mudou:
  - o relatório declarava "validação visual não executada — LibreOffice/soffice não disponível no
    ambiente" por **string fixa**, sem que nada procurasse o conversor. Com LibreOffice instalado
    (26.2.5.2, `C:\Program Files\LibreOffice\program\soffice.exe`), a frase virava afirmação falsa
    sobre o ambiente — exatamente a conferência não executada que a regra R12 proíbe declarar;
  - novo módulo `validacao_visual_docx.py`: detecta LibreOffice/Word, converte entrada e saída em
    PDF e compara **nº de páginas** e **páginas em branco novas**. Roda por padrão na CLI
    (`--sem-validacao-visual` desliga; `--guardar-pdfs` preserva os PDFs para conferência) e vem
    desligada na chamada programática, pelo custo de dois processos de LibreOffice;
  - a validação **nunca bloqueia**: reformatar muda paginação por definição. PDF que não renderiza
    ou página em branco nova rebaixam o status para `EXIGE CONFERÊNCIA HUMANA`;
  - `pypdf` é opcional: sem ele o PDF é gerado, mas a contagem de páginas sai como
    `NÃO VERIFICADA` — nunca presumida;
  - a conversão passou a usar `-env:UserInstallation` isolado. Sem isso, o LibreOffice headless
    disputa o perfil de uma instância já aberta e sai **sem converter e sem erro** — falha
    silenciosa que este repositório não tolera;
  - eliminada a duplicação: `gerar_pacote_publicacao.py` reexporta a detecção e a conversão do novo
    módulo em vez de manter sua própria cópia da lista de caminhos.
- Validação: 119 testes do módulo (6 novos, incluindo execução real ponta a ponta com LibreOffice);
  comando de CLI reexecutado sobre a Pesquisa de Preços SC 27/2026 — "executada com libreoffice;
  páginas 5 -> 5", com os dois PDFs conferíveis em disco.
- Limite: a suíte de `99_testes/aviso_completo/` está **pulando** por falta de `docxcompose` neste
  ambiente, então o ajuste em `gerar_pacote_publicacao.py` foi verificado por importação e execução
  direta de `detectar_conversor()`, não pelos testes daquele módulo.

## 2026-08-07 — Correção: nome de estilo deixa de ser prova de papel documental

- Arquivos: `scripts/docx_cmi/estilos_docx.py`, `99_testes/padronizacao_documental/`.
- O que mudou:
  - o classificador de papéis deduzia o papel do parágrafo apenas pelo **nome do estilo**. Como a
    minuta-mãe de Pesquisa de Preços usa o estilo `Nivel 2` para o **texto de corpo**, todos os
    parágrafos de corpo do relatório eram convertidos em `CMI Titulo 2` (negrito, à esquerda) —
    degradação, não padronização (ocorrência de 07/08/2026, Pesquisa de Preços SC 27/2026);
  - a promoção a título passa a exigir **confirmação independente do nome**: `w:outlineLvl` do
    parágrafo ou herdado pelo encadeamento `w:basedOn` do estilo e, na falta dele, a forma do
    parágrafo (≤ 120 caracteres, ≤ 20 palavras, uma única frase, sem pontuação final de corpo,
    salvo rótulo em caixa alta). Sem confirmação, o parágrafo segue para as demais heurísticas,
    que na dúvida devolvem `corpo`;
  - a troca de estilo passa a respeitar a **numeração automática herdada do estilo**: `Nivel 01`
    carrega `w:numPr`, e substituí-lo por um estilo CMI sem numeração apagaria os números dos
    títulos sem deixar rastro no texto extraído.
- Validação: 113 testes do módulo; 4 testes de regressão novos (13, 13b, 13c, 13d), verificados
  falhando antes da correção; reprodução do comando da ocorrência — nenhum `CMI Titulo 2` na saída
  e os 12 parágrafos de corpo preservados.
- Limite: validação visual (renderização) não executada — sem LibreOffice/Word neste ambiente.

## 2026-08-01 — Corpus TCU dos Informativos de Licitações e Contratos nº 452 a 531

- Arquivos: `TCU_INFORMATIVOS_LICITACOES_CONTRATOS/`,
  `03_jurisprudencia/tcu/informativos_licitacoes_contratos/`, `scripts/tcu_informativos.py`,
  `99_testes/tcu_informativos/` e `00_indices/`.
- O que mudou:
  - coletados os **80 informativos** do recorte solicitado, preservando os PDFs oficiais, URL,
    tamanho e SHA-256;
  - selecionados **6 enunciados** relacionados expressamente a contratação direta, dispensa,
    inexigibilidade ou credenciamento, com acórdão, colegiado, classe, responsável indicado na
    citação final, páginas e link incorporado para o inteiro teor;
  - criadas fichas individuais, texto integral paginado, manifesto JSONL, catálogo JSONL/CSV e
    mapa temático para pesquisa e uso como cautela;
  - excluídos falsos positivos como “dispensado de balanço”, “dedicação exclusiva de mão de obra”
    e “rede credenciada”, porque a seleção é aplicada ao enunciado completo do sumário.
- Validação: conferência visual de cinco páginas relevantes; correspondência exata entre itens do
  sumário e citações finais nas 80 edições; 5 testes específicos; hashes, páginas, IDs e links do
  inteiro teor validados mecanicamente; execução integral concluída sem erro.
- Limite: o próprio TCU declara que o informativo não é resumo oficial da decisão nem representa
  necessariamente o entendimento prevalecente. Todas as fichas exigem conferência do acórdão e do
  voto condutor; nenhuma força vinculante é presumida.

## 2026-08-01 — Corpus TCE-SP de contratação direta e dispensa de licitação

- Arquivos: `TCE-SP_BOLETINS/`, `03_jurisprudencia/tce_sp/contratacao_direta/`,
  `scripts/tcesp_boletins.py`, `99_testes/tcesp_boletins/` e `00_indices/`.
- O que mudou:
  - coletadas as **53 edições** disponíveis na página oficial do Boletim de Jurisprudência do
    TCE-SP (fevereiro/2021 a março/2026), preservando URL, arquivo original e SHA-256;
  - extraídos **98 registros de julgados** relacionados a contratação direta e dispensa de
    licitação, com processo, sessão, relatoria, órgão julgador, página e texto oficial do boletim;
  - criadas fichas individuais, catálogo JSONL/CSV, manifesto dos originais, texto paginado e mapa
    temático para uso como cautelas e referências na instrução e auditoria;
  - incorporadas salvaguardas contra falsos positivos, cabeçalhos de processos antigos e novos,
    palavras quebradas pela extração PDF e uso do boletim como substituto do inteiro teor.
- Validação: amostra visual de cinco páginas; todos os 53 PDFs com texto extraível; 7 testes do
  parser; cobertura adicional de sessões não reconhecidas sem ocorrência relevante nas janelas;
  validação de página/hash/ID e execução integral sem erro mecânico.
- Limite: os boletins são sínteses oficiais, não inteiro teor. As fichas permanecem com status
  `verificar-inteiro-teor`, e o TCE-SP é jurisprudência persuasiva de outro Estado.

## 2026-08-01 — Segurança do repositório, limites conferidos, trava de fracionamento e inexigibilidade

- Arquivos: `.gitignore`, `scripts/gestao_documental/seguranca_repositorio.py`,
  `scripts/gestao_documental/nomes_arquivos.py`, `scripts/gestao_documental/migrar_processo.py`,
  `scripts/gestao_documental/manifesto.py`, `scripts/gestao_documental/iniciar_processo.py`,
  `scripts/controle_cnae.py`, `01_legislacao/limites-vigentes-dispensa-art-75.md`,
  `06_precedentes_camara/limites.json`, `07_checklists/roteiro-inexigibilidade-art-74.md`,
  `07_checklists/esteira-contratacao-direta.md`, `07_checklists/roteiro-limite-dispensa-cnae.md`,
  `10_gestao_documental/*`, `99_testes/gestao_documental/test_gestao_documental.py`.
- O que mudou:
  - **Material de trabalho deixou de ser documento externo.** Nova área
    `07_MATERIAL_DE_TRABALHO/`, com nome e subpasta originais preservados. Na migração de um
    processo real, os documentos externos caíram de 68 para 1 e as pendências humanas de
    **157 para 3**.
  - **`.gitignore` ampliado** para material bruto de jurisprudência (`texto_extraido/`,
    `inteiro_teor_bruto/`, `*.sqlite3`), `TCE-MG_JULGADOS/`, `SICOM/` e
    `06_precedentes_camara/processos_2025/` (976 arquivos de processos reais de 2025).
  - **"Não verificado" deixou de virar afirmação.** Sem `.git`, a cobertura do `.gitignore` não
    é consultável; a mensagem dizia "NÃO coberto pelo .gitignore". Agora diz que não pôde ser
    verificada, com o motivo, mantendo a recusa por precaução.
  - **Limites de 2026 conferidos no texto oficial** (Anexo do Decreto 12.807/2025, Planalto):
    art. 75, I — R$ 130.984,20; II — R$ 65.492,11. Ressalva de fonte secundária encerrada.
    Registrados também art. 75, § 7º (R$ 10.478,74) e art. 95, § 2º (R$ 13.098,41).
  - **Trava de fracionamento na abertura do processo**, não no fim: `iniciar_processo.py`
    recebe `--cnae`, afere o somatório do exercício e **recusa** a abertura em faixa
    impeditiva. Faixa `estouro` separada de `vermelho` — antes, 86% e 240% tinham o mesmo
    rótulo. Destrava com `--justificativa-fracionamento`, gravada no `PROCESSO.json`.
  - **Roteiro de inexigibilidade (art. 74)**, que não existia, e variante própria na esteira.
- Achados registrados: 9 CPF em `03_jurisprudencia/.../texto_extraido/` e 26 no
  `auditor_tcemg.sqlite3` — fichas e consolidações estão limpas; a base **não é um repositório
  Git**, de modo que o `.gitignore` não protege nada hoje; e-mail pessoal em
  `ETP_CHANGELOG.md` (não alterado — é registro de auditoria).
- Motivo: fechar a exposição antes de qualquer `git init`, e mover as travas para onde elas
  custam pouco — o começo do processo.
- Testes: 281 passed, 1 skipped. A falha histórica de `test_22` foi resolvida.

## 2026-07-31 — Controle de contratações por CNAE do exercício 2026

- Arquivos: `06_precedentes_camara/contratacoes.csv`,
  `06_precedentes_camara/CONTROLE_CONTRATACOES.md`, `06_precedentes_camara/cnae-precedentes.md`,
  `06_precedentes_camara/limites.json`, `01_legislacao/limites-vigentes-dispensa-art-75.md`,
  `08_processos_em_andamento/2026/CONCLUIDOS/*/processo.json`, `00_indices/BASE_INDEXADA.json`.
- O que mudou:
  - Levantadas e registradas as **25 contratações concluídas de 2026** (PA 001 a 025/2026),
    com processo, objeto, fundamento legal, fornecedor, CNPJ, valor homologado e data.
  - Preenchidos os **limites vigentes de 2026** (Decreto nº 12.807/2025): art. 75, I —
    R$ 130.984,20; art. 75, II — R$ 65.492,11. **Pendente de conferência no texto oficial.**
  - Montado o **mapa de precedentes CNAE**, antes vazio, com a evidência de cada enquadramento.
  - Preenchidos os `processo.json` dos processos concluídos, que estavam integralmente com
    placeholders da migração de 2026-07-04; criados os três que não existiam.
- Fontes: remessas SICOM `EDITAL_01712_01_2026-23` a `-32` (arquivo `DISPENSA.csv`), termos de
  adjudicação/homologação e ratificação das pastas dos processos, Cartões CNPJ juntados às
  habilitações e API oficial IBGE/CONCLA (CNAE-Subclasses 2.3).
- Achado principal: **subclasse 4751-2/01 (equipamentos e suprimentos de informática) acumula
  R$ 54.600,38, ou 83,4% do limite do art. 75, II**, com saldo de R$ 10.891,73 para o resto do
  exercício. PA 013 e PA 016, que somam R$ 48.806,47, foram concluídos com 34 dias de intervalo
  e objetos próximos — ponto de atenção quanto a fracionamento, a justificar nos autos.
- Correção: o único registro anterior do controle apontava a claraboia como "PA 021/2026 —
  Dispensa 11/2026"; o número oficial é **PA 020/2026 — Dispensa 011/2026**, homologada em
  2026-06-10. PA 021/2026 é a inexigibilidade do curso de IA.
- Motivo: dar à Câmara o controle anual por ramo de atividade exigido pelo art. 75, §1º, II, da
  Lei 14.133/2021 e pelo art. 2º, §§1º-2º, da Portaria 06/2024, prevenindo fracionamento.

## 2026-07-01 — dce917f — Adiciona minuta DFD para PCA

- Arquivos: `05_minutas/DFD/DFD_PARA_PCA_MINUTA_MAE.docx`,
  `05_minutas/DFD/DFD_PARA_PCA_FICHA_DE_USO.md`, `05_minutas/_CONTROLE_MINUTAS.md`.
- O que mudou: cadastrada minuta/ficha de DFD para PCA.
- Motivo: apoiar formalização de demanda para o Plano de Contratações Anual.

## 2026-06-27 — f4dbb8c — Adiciona funcionalidade Executar Pesquisa de Precos

- Arquivos: `scripts/`, `07_checklists/`, `05_minutas/PESQUISA_DE_PRECOS/`, `README.md`,
  `CLAUDE.md`.
- O que mudou: adicionados scripts de pesquisa de preços, roteiro operacional, regras de
  comparabilidade e integração com a minuta oficial de Pesquisa de Preços.
- Motivo: padronizar a pesquisa de preços sob Lei 14.133/2021 e Portaria 03/2024.

## 2026-06-25 — 071ea39 — Initial Charles knowledge base

- Arquivos: estrutura inicial das pastas `00_indices/` a `99_testes/`, minutas oficiais,
  legislação, normas internas, doutrina, jurisprudência, checklists e scripts iniciais.
- O que mudou: criada a base documental inicial do Charles.
- Motivo: consolidar base de conhecimento e ferramenta de trabalho para licitações da Câmara.
