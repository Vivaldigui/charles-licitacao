---
tipo: checklist
hierarquia: oficial
tema: changelog minuta pca
fonte: 05_minutas/_CONTROLE_MINUTAS.md
vigencia: vigente
atualizado_em: 2026-08-04
tags: [minutas, changelog, governanca, pca]
---

# Changelog — PCA

Registro de evolução das minutas-mãe desta pasta. Histórico anterior à versão atual não
foi inventado: esta é a primeira versão da minuta.

## PCA_MINUTA_MAE.docx — v1.0 — 2026-08-04

- **Criação da minuta-mãe do Plano de Contratações Anual.** A biblioteca já tinha o
  formulário de coleta de demanda (`DFD/DFD_PARA_PCA_MINUTA_MAE.docx`), mas não tinha
  modelo para o Plano consolidado — que vinha sendo redigido por cópia do PCA do exercício
  anterior.
- **Arquitetura adaptada do PCA 2026 do TCE-MG** (`12_pca/modelo/plano-anual-de-contratacoes-2026.pdf`),
  por pedido expresso do usuário: documento principal enxuto (capa, créditos, apresentação,
  classificação por categoria econômica, unidades, lista corrida de contratações
  planejadas, notas explicativas) e detalhamento analítico remetido a anexo.
- **Referência de forma, não de rito.** Não foram importados a Portaria nº 1/PRES./2024, a
  Resolução Delegada nº 01/2025, a Coordenadoria de Planejamento das Contratações nem a
  distinção "unidade de pedido × unidade demandante" do TCE-MG. O conteúdo obrigatório vem
  da Portaria nº 04/2024 da Câmara e da Lei nº 14.133/2021.
- **Seções acrescentadas ao modelo do TCE-MG:** item 2 (metodologia das estimativas, com
  base de cálculo, anualização de empenho parcial e índice declarado com fonte) e item 6.4
  (contratações planejadas e não realizadas no exercício anterior, exigido pelo art. 7º da
  Portaria nº 04/2024).
- **Anexo I em seção própria, orientação paisagem**, com 19 colunas, cobrindo os elementos
  dos arts. 2º, § 2º, e 3º da Portaria nº 04/2024. A seção herda cabeçalho e rodapé da
  anterior; o timbre não foi recriado.
- **Timbre.** O arquivo foi construído sobre cópia de `TR/TR_MINUTA_MAE.docx` justamente
  para herdar cabeçalho (brasão), rodapé, margens e definições de estilo sem os recriar. A
  auditoria confirma `divergencia_minuta_mae: []` — o timbre é idêntico ao da TR.
- **Estilos.** Aplicados os estilos nomeados `CMI *` previstos no novo perfil `pca`,
  criados por `scripts/docx_cmi/estilos_docx.garantir_estilos`.
- **Metadados** do pacote gravados como "Camara Municipal de Itanhandu" (a base TR trazia
  nomes de pessoas).
- **Perfil documental `pca`** registrado em `09_padronizacao_documental/PERFIS_DOCUMENTAIS.json`,
  com o mapeamento `PCA_MINUTA_MAE.docx → pca`. Exceções de auditoria registradas como
  **E-10** em `09_padronizacao_documental/EXCECOES_AUTORIZADAS.md`.
- **Auditoria na criação:** nota 69/100, status `EXIGE CONFERÊNCIA HUMANA`. Sem problemas
  de fonte, numeração, paginação ou estrutura. As ocorrências remanescentes são as
  registradas em E-10 e as 142 pendências de preenchimento — esperadas em minuta-mãe.
- Origem do pedido: gui.rib.pi@gmail.com (via Charles), a partir da análise comparativa dos
  PCA 2024, 2025 e 2026 da Câmara.
- Sem backup de versão anterior: arquivo novo.

### Pendente de decisão humana

- **Validação jurídica e institucional do modelo** antes do primeiro uso real (PCA 2027).
- Conferir na origem, ou suprimir, a citação do **Acórdão TCU nº 1524/2019** que consta dos
  PCA anteriores da Casa e que **não foi reproduzida** nesta minuta por não haver ficha de
  jurisprudência correspondente na base.
- Definir se o Anexo I permanece no corpo do documento ou migra para planilha apartada,
  como faz o TCE-MG.
