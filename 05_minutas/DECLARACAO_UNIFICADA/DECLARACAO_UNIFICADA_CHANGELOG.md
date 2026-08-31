# Changelog — Declaração Unificada

## v1.0 — 2026-07-22

- Minuta criada a partir do modelo utilizado no PA 016/2026, mediante autorização do usuário.

## v1.1 — 2026-07-26

Revisão de PADRONIZAÇÃO VISUAL pelo Módulo de Padronização Documental (perfil `declaracao`).

- Backup da versão anterior: `05_minutas\DECLARACAO_UNIFICADA\_arquivo\DECLARACAO_UNIFICADA_MINUTA_MAE_v1.0.docx`
- Relatório do estado anterior: `05_minutas\DECLARACAO_UNIFICADA\DECLARACAO_UNIFICADA_MINUTA_MAE_ESTADO_ANTERIOR_v1.0.md`
- Correções aplicadas: 32
- Conteúdo preservado: sim
- Timbre (cabeçalho/rodapé/mídia) intacto: sim

### Reparo do timbre — v1.1 (2026-07-26)

Antes desta versão o documento **não exibia timbre**: o pacote já continha
`word/header1.xml`, `word/footer1.xml` e os relacionamentos correspondentes,
mas o `w:sectPr` não os referenciava. O timbre existia e nunca era mostrado.

O que foi feito, sob autorização expressa do usuário:

- ligadas as referências `headerReference` e `footerReference` no `sectPr`;
- instalados o cabeçalho, o rodapé e as imagens do **aviso oficial**
  (`05_minutas/AVISO/AVISO_CONTRATACAO_DIRETA_MINUTA_MAE.docx`), byte a byte —
  o cabeçalho anterior era uma geração sem o brasão;
- geometria vertical ajustada para comportar a faixa de 3,93 cm e o rodapé
  timbrado: `top` 3,49 → 4,23 cm, `bottom` 1,52 → 2,22 cm, `header` 0,37 → 0 cm,
  `footer` 1,06 → 1,71 cm. Margens laterais, tamanho de página e todo o
  conteúdo permaneceram inalterados.

Estado anterior preservado em `_arquivo/`:
`*_v1.0_sem_timbre.docx` (original) e `*_v1.0.docx` (com timbre, antes da
padronização visual).


## v1.2 — 2026-07-26

Revisão de PADRONIZAÇÃO VISUAL pelo Módulo de Padronização Documental (perfil `declaracao`).

- Backup da versão anterior: `05_minutas\DECLARACAO_UNIFICADA\_arquivo\DECLARACAO_UNIFICADA_MINUTA_MAE_v1.1.docx`
- Relatório do estado anterior: `05_minutas\DECLARACAO_UNIFICADA\DECLARACAO_UNIFICADA_MINUTA_MAE_ESTADO_ANTERIOR_v1.1.md`
- Correções aplicadas: 4
- Conteúdo preservado: sim
- Timbre (cabeçalho/rodapé/mídia) intacto: sim

### Campos do fornecedor — v1.2 (2026-07-26)

Autorizado expressamente pelo usuário: estas minutas são **formulários preenchidos por
terceiros**, não documentos que a Câmara redige. Marcador `{{CAMPO}}` e literal
`[PREENCHER]` são notação interna do repositório — para quem recebe o arquivo, não
indicam onde escrever.

- Campos do domínio do proponente convertidos em **campo de preenchimento**: régua no
  texto corrido, célula vazia dentro de tabela.
- Tabelas **emolduradas** (borda simples, cinza), para que a célula em branco se leia
  como campo.
- `[PREENCHER]` eliminado.
- Preservados como marcador apenas os campos que a **montagem do aviso completo**
  preenche: processo, aviso, objeto e o quadro de itens.
- Linhas com campo de preenchimento deixaram de ser justificadas — a régua não quebra, e
  justificar espalhava as palavras da linha.
