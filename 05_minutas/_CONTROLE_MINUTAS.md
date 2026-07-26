---
tipo: checklist
tema: controle de minutas
fonte: base Charles
vigencia: vigente
atualizado_em: 2026-07-01
tags: [minutas, controle, governanca]
---

# _CONTROLE_MINUTAS

Índice e governança da biblioteca oficial de minutas da Câmara Municipal de Itanhandu.

---

## REGRA PERMANENTE PARA USO DAS MINUTAS OFICIAIS

Ao gerar documentos administrativos da Câmara Municipal de Itanhandu, o Charles deve
utilizar **exclusivamente** as minutas-mãe da pasta `05_minutas/`.

- É **proibido** criar modelo novo, reorganizar a estrutura, alterar timbre, cabeçalho,
  rodapé, assinaturas, numeração padrão ou cláusulas fixas da minuta — **salvo** se o
  usuário solicitar expressamente a revisão ou aprimoramento da minuta-mãe.
- Ao gerar um documento concreto, o Charles **apenas preenche, complementa ou adapta os
  campos variáveis** da minuta oficial, respeitando a linguagem institucional, a ordem das
  seções e o padrão documental da Câmara.
- Quando a minuta estiver incompleta, desatualizada ou juridicamente frágil, o Charles
  **aponta o problema em comentário separado**, sem alterar a estrutura oficial automaticamente.
- O Charles **não inventa** fundamento legal, artigo, inciso, jurisprudência, entendimento
  de tribunal ou requisito documental. Sem base suficiente, informa expressamente.

Em conflito entre fontes, prevalece nesta ordem:
1. Lei nº 14.133/2021
2. Regulamento de Licitações da Câmara Municipal de Itanhandu
3. Portarias e normas internas da Câmara
4. Modelos oficiais padronizados (esta biblioteca)
5. Artigos e materiais de apoio cadastrados no Charles

---

## Convenções da biblioteca

- **Organização**: uma subpasta por tipo de documento dentro de `05_minutas/`
  (ex.: `05_minutas/DFD/`, `05_minutas/TR/`).
- **Cada minuta tem dois arquivos**:
  - `*_MINUTA_MAE.docx` — modelo oficial (fonte da verdade), com timbre/cabeçalho/rodapé/assinaturas.
  - `*_FICHA_DE_USO.md` — ficha que descreve finalidade, estrutura, campos variáveis e regras de uso.
- **Campos variáveis**: marcados como `{{NOME_DO_CAMPO}}` (chaves duplas) — preenchidos pelo
  Charles com dados do processo. Use `[PREENCHER: ...]` apenas para lacunas pontuais que
  exigem decisão humana e não são campo padrão.
- **Versão**: cada ficha registra `versao:` no frontmatter; mudanças na minuta-mãe sobem a versão.
- **Timbre único**: todas as minutas em DOCX usam o mesmo cabeçalho (brasão) e rodapé oficiais —
  endereço Rua Engenheiro Paulo Franco da Rosa, 298, Itanhandu/MG; Portal/e-mail
  `secretaria@itanhandu.cam.mg.gov.br`; **TEL (35) 3504-0397**. **Toda a biblioteca está em DOCX
  com este timbre** (o DFD, antes em `.odt`, foi reemitido em DOCX).

---

## Fluxo de padronização (5 etapas por documento)

1. **Diagnóstico** da minuta atual (Lei 14.133/2021, regulamento interno, cláusulas
   repetidas/frágeis, seções faltantes, linguagem, risco de direcionamento, reaproveitamento).
2. **Padronização da estrutura** (ordem fixa de seções, ajustada ao modelo real da Câmara).
3. **Campos variáveis** `{{...}}`.
4. **Ficha de uso** em Markdown.
5. **Conclusão** (status da minuta).

---

## Ordem de padronização

| # | Documento | Pasta | Status |
|---|-----------|-------|--------|
| 1 | DFD — Documento de Formalização de Demanda | `DFD/` | ✅ padronizada (v1.0) |
| 1b | DFD para PCA - Documento de Formalizacao de Demanda para o Plano de Contratacoes Anual | `DFD/` | cadastrada (v1.0) |
| 2 | ETP — Estudo Técnico Preliminar | `ETP/` | ✅ padronizada (v1.0) |
| 3 | TR — Termo de Referência | `TR/` | ✅ padronizada (v1.0) |
| 4 | Mapa de Riscos | `MAPA_DE_RISCOS/` | — fora do escopo por enquanto (jun/2026) |
| 5 | Pesquisa de Preços | `PESQUISA_DE_PRECOS/` | ✅ padronizada (v1.0) |
| 6 | Justificativa da contratação direta | `JUSTIFICATIVA_CONTRATACAO_DIRETA/` | ✅ padronizada (v1.0) |
| 6b | Certidão de Recursos Orçamentários (art. 72, IV) | `CERTIDAO_ORCAMENTARIA/` | ✅ padronizada (v1.0) |
| 7 | Autorização de abertura | `AUTORIZACAO/` | ✅ padronizada (v1.0) |
| 8 | Aviso de contratação direta | `AVISO/` | ✅ padronizada (v1.0) |
| 9 | Certidão de dispensa de aviso / procedimento simplificado | `CERTIDOES/` | pendente |
| 10 | Termo de Adjudicação e Homologação | `HOMOLOGACAO/` | ✅ padronizada (v1.0) |
| 10b | Termo de Ratificação (inexigibilidade / dispensa sem disputa) | `RATIFICACAO/` | ✅ padronizada (v1.0) |
| 11 | Ordem de fornecimento | `ORDEM_FORNECIMENTO/` | ✅ padronizada (v1.0) |
| 12 | Contrato | `CONTRATO/` | ✅ padronizada (v1.0) |
| 12b | Termo de Recebimento e Atesto | `RECEBIMENTO/` | ✅ padronizada (v1.0) |
| 13 | Extrato para publicação | `EXTRATO/` | ✅ padronizada (v1.0) |

---

## AVISO DE DISPENSA COMPLETO — composição, não duplicação

A pasta [`AVISO_COMPLETO/`](AVISO_COMPLETO/) **não tem minuta-mãe DOCX própria**, e isso é
deliberado. O aviso completo é a **montagem** das minutas que já estão nesta biblioteca:

| Anexo | Minuta-mãe usada |
| --- | --- |
| — Aviso | `AVISO/AVISO_CONTRATACAO_DIRETA_MINUTA_MAE.docx` |
| I — Habilitação | **já incorporado** à minuta do aviso — recortado dela, nunca recriado |
| II — Termo de Referência | não é minuta: é o TR já elaborado do processo |
| III — Modelo de Proposta | `PROPOSTA_COMERCIAL/PROPOSTA_COMERCIAL_MINUTA_MAE.docx` |
| IV — Minuta de contrato (quando houver) | `CONTRATO/`, `CONTRATO_COMPRAS/` ou `CONTRATO_SERVICOS_CONTINUOS/` |
| IV ou V — Declaração conjunta | `DECLARACAO_UNIFICADA/DECLARACAO_UNIFICADA_MINUTA_MAE.docx` |

Criar cópias dessas minutas em `AVISO_COMPLETO/` violaria a regra de não duplicar conteúdo:
a revisão de uma cópia não chegaria à outra, e o aviso publicado passaria a divergir da minuta
oficial. A pasta guarda apenas as **fichas de uso** que documentam a composição.


## Índice de minutas cadastradas

| Documento | Minuta-mãe | Ficha de uso | Versão | Status |
|---|---|---|---|---|
| DFD | [DFD_MINUTA_MAE.docx](DFD/DFD_MINUTA_MAE.docx) | [DFD_FICHA_DE_USO.md](DFD/DFD_FICHA_DE_USO.md) | 1.1 | apta para uso |
| DFD para PCA | [DFD_PARA_PCA_MINUTA_MAE.docx](DFD/DFD_PARA_PCA_MINUTA_MAE.docx) | [DFD_PARA_PCA_FICHA_DE_USO.md](DFD/DFD_PARA_PCA_FICHA_DE_USO.md) | 1.0 | apta para uso |
| ETP | [ETP_MINUTA_MAE.docx](ETP/ETP_MINUTA_MAE.docx) | [ETP_FICHA_DE_USO.md](ETP/ETP_FICHA_DE_USO.md) | 1.0 | apta para uso |
| TR | [TR_MINUTA_MAE.docx](TR/TR_MINUTA_MAE.docx) | [TR_FICHA_DE_USO.md](TR/TR_FICHA_DE_USO.md) | 1.0 | apta para uso |
| Pesquisa de Preços | [PESQUISA_PRECOS_MINUTA_MAE.docx](PESQUISA_DE_PRECOS/PESQUISA_PRECOS_MINUTA_MAE.docx) | [PESQUISA_PRECOS_FICHA_DE_USO.md](PESQUISA_DE_PRECOS/PESQUISA_PRECOS_FICHA_DE_USO.md) · [roteiro executar pesquisa](../07_checklists/roteiro-executar-pesquisa-de-precos.md) | 1.0 | apta para uso |
| Certidão de Recursos Orçamentários | [CERTIDAO_RECURSOS_ORCAMENTARIOS_MINUTA_MAE.docx](CERTIDAO_ORCAMENTARIA/CERTIDAO_RECURSOS_ORCAMENTARIOS_MINUTA_MAE.docx) | [CERTIDAO_RECURSOS_ORCAMENTARIOS_FICHA_DE_USO.md](CERTIDAO_ORCAMENTARIA/CERTIDAO_RECURSOS_ORCAMENTARIOS_FICHA_DE_USO.md) | 1.0 | apta para uso |
| Autorização de Abertura | [AUTORIZACAO_ABERTURA_MINUTA_MAE.docx](AUTORIZACAO/AUTORIZACAO_ABERTURA_MINUTA_MAE.docx) | [AUTORIZACAO_ABERTURA_FICHA_DE_USO.md](AUTORIZACAO/AUTORIZACAO_ABERTURA_FICHA_DE_USO.md) | 1.0 | apta para uso |
| Justificativa de Contratação Direta | [JUSTIFICATIVA_CONTRATACAO_DIRETA_MINUTA_MAE.docx](JUSTIFICATIVA_CONTRATACAO_DIRETA/JUSTIFICATIVA_CONTRATACAO_DIRETA_MINUTA_MAE.docx) | [JUSTIFICATIVA_CONTRATACAO_DIRETA_FICHA_DE_USO.md](JUSTIFICATIVA_CONTRATACAO_DIRETA/JUSTIFICATIVA_CONTRATACAO_DIRETA_FICHA_DE_USO.md) | 1.1 | apta para uso |
| Aviso de Contratação Direta | [AVISO_CONTRATACAO_DIRETA_MINUTA_MAE.docx](AVISO/AVISO_CONTRATACAO_DIRETA_MINUTA_MAE.docx) | [AVISO_CONTRATACAO_DIRETA_FICHA_DE_USO.md](AVISO/AVISO_CONTRATACAO_DIRETA_FICHA_DE_USO.md) | 1.0 | apta para uso |
| Ata de Julgamento (+ Anexo de classificação) | [ATA_JULGAMENTO_MINUTA_MAE.docx](ATA_JULGAMENTO/ATA_JULGAMENTO_MINUTA_MAE.docx) | [ATA_JULGAMENTO_FICHA_DE_USO.md](ATA_JULGAMENTO/ATA_JULGAMENTO_FICHA_DE_USO.md) · [roteiro de julgamento](../07_checklists/roteiro-julgamento-dispensa-com-aviso.md) | 1.0 | apta para uso |
| Termo de Adjudicação e Homologação | [TERMO_ADJUDICACAO_HOMOLOGACAO_MINUTA_MAE.docx](HOMOLOGACAO/TERMO_ADJUDICACAO_HOMOLOGACAO_MINUTA_MAE.docx) | [TERMO_ADJUDICACAO_HOMOLOGACAO_FICHA_DE_USO.md](HOMOLOGACAO/TERMO_ADJUDICACAO_HOMOLOGACAO_FICHA_DE_USO.md) | 1.0 | apta para uso |
| Extrato de Contratação Direta | [EXTRATO_CONTRATACAO_DIRETA_MINUTA_MAE.docx](EXTRATO/EXTRATO_CONTRATACAO_DIRETA_MINUTA_MAE.docx) | [EXTRATO_CONTRATACAO_DIRETA_FICHA_DE_USO.md](EXTRATO/EXTRATO_CONTRATACAO_DIRETA_FICHA_DE_USO.md) | 1.0 | apta para uso |
| Ordem de Fornecimento | [ORDEM_FORNECIMENTO_MINUTA_MAE.docx](ORDEM_FORNECIMENTO/ORDEM_FORNECIMENTO_MINUTA_MAE.docx) | [ORDEM_FORNECIMENTO_FICHA_DE_USO.md](ORDEM_FORNECIMENTO/ORDEM_FORNECIMENTO_FICHA_DE_USO.md) | 1.0 | apta para uso |
| Contrato Administrativo (genérico) | [CONTRATO_MINUTA_MAE.docx](CONTRATO/CONTRATO_MINUTA_MAE.docx) | [CONTRATO_FICHA_DE_USO.md](CONTRATO/CONTRATO_FICHA_DE_USO.md) | 1.1 | apta para uso |
| Contrato de Serviços Contínuos | [CONTRATO_SERVICOS_CONTINUOS_MINUTA_MAE.docx](CONTRATO_SERVICOS_CONTINUOS/CONTRATO_SERVICOS_CONTINUOS_MINUTA_MAE.docx) | [CONTRATO_SERVICOS_CONTINUOS_FICHA_DE_USO.md](CONTRATO_SERVICOS_CONTINUOS/CONTRATO_SERVICOS_CONTINUOS_FICHA_DE_USO.md) | 1.0 | apta para uso |
| Contrato de Compras (entrega imediata / forn. contínuo) | [CONTRATO_COMPRAS_ENTREGA_FORN_CONTINUO_MINUTA_MAE.docx](CONTRATO_COMPRAS/CONTRATO_COMPRAS_ENTREGA_FORN_CONTINUO_MINUTA_MAE.docx) | [CONTRATO_COMPRAS_ENTREGA_FORN_CONTINUO_FICHA_DE_USO.md](CONTRATO_COMPRAS/CONTRATO_COMPRAS_ENTREGA_FORN_CONTINUO_FICHA_DE_USO.md) | 1.0 | apta para uso |
| Termo de Ratificação (inex./dispensa sem disputa) | [TERMO_RATIFICACAO_MINUTA_MAE.docx](RATIFICACAO/TERMO_RATIFICACAO_MINUTA_MAE.docx) | [TERMO_RATIFICACAO_FICHA_DE_USO.md](RATIFICACAO/TERMO_RATIFICACAO_FICHA_DE_USO.md) | 1.0 | apta para uso |
| Termo de Recebimento e Atesto | [TERMO_RECEBIMENTO_ATESTO_MINUTA_MAE.docx](RECEBIMENTO/TERMO_RECEBIMENTO_ATESTO_MINUTA_MAE.docx) | [TERMO_RECEBIMENTO_ATESTO_FICHA_DE_USO.md](RECEBIMENTO/TERMO_RECEBIMENTO_ATESTO_FICHA_DE_USO.md) | 1.0 | apta para uso |
| Aviso de Dispensa Completo (composição) | *sem minuta própria — compõe as minutas acima* | [AVISO_COMPLETO_FICHA_DE_USO.md](AVISO_COMPLETO/AVISO_COMPLETO_FICHA_DE_USO.md) · [Anexo I](AVISO_COMPLETO/ANEXO_I_HABILITACAO_FICHA_DE_USO.md) · [Proposta](AVISO_COMPLETO/MODELO_PROPOSTA_FICHA_DE_USO.md) · [Declaração](AVISO_COMPLETO/DECLARACAO_CONJUNTA_FICHA_DE_USO.md) | 1.0 | apta para uso |
| Modelo de Proposta Comercial | [PROPOSTA_COMERCIAL_MINUTA_MAE.docx](PROPOSTA_COMERCIAL/PROPOSTA_COMERCIAL_MINUTA_MAE.docx) | [PROPOSTA_COMERCIAL_FICHA_DE_USO.md](PROPOSTA_COMERCIAL/PROPOSTA_COMERCIAL_FICHA_DE_USO.md) | 1.1 | apta para uso |
| Declaração Unificada | [DECLARACAO_UNIFICADA_MINUTA_MAE.docx](DECLARACAO_UNIFICADA/DECLARACAO_UNIFICADA_MINUTA_MAE.docx) | [DECLARACAO_UNIFICADA_FICHA_DE_USO.md](DECLARACAO_UNIFICADA/DECLARACAO_UNIFICADA_FICHA_DE_USO.md) | 1.1 | apta para uso |
