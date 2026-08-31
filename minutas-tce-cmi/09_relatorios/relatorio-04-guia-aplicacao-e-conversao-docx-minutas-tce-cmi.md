---
tipo: relatorio
tema: guia de aplicacao das minutas tce-cmi e conversao para docx
fonte: Charles / base documental (minutas-tce-cmi + 09_padronizacao_documental)
vigencia: vigente
atualizado_em: 2026-08-09
tags: [relatorio, tce-cmi, minutas, docx, aplicacao, seguranca-juridica, simplificacao]
---

# RELATÓRIO 04 — Guia de aplicação das minutas TCE-CMI, conversão para DOCX e dicas de segurança/simplicidade

## 1. O que foi feito

As 8 minutas de `minutas-tce-cmi/*.md` foram convertidas para **DOCX** e salvas em
`minutas-tce-cmi/docx/`, um arquivo por minuta, com o mesmo nome-base do Markdown de origem.
Nenhum conteúdo foi alterado — apenas a formatação foi aplicada (conversão de formato, não
geração de documento novo).

| Markdown de origem | DOCX gerado |
|---|---|
| `01-aviso-contratacao-direta.md` | `docx/01-aviso-contratacao-direta.docx` |
| `02-ato-autorizativo-ratificacao.md` | `docx/02-ato-autorizativo-ratificacao.docx` |
| `03-extrato-contrato.md` | `docx/03-extrato-contrato.docx` |
| `04-termo-referencia-sintetico.md` | `docx/04-termo-referencia-sintetico.docx` |
| `05-checklist-verificacao-conformidade.md` | `docx/05-checklist-verificacao-conformidade.docx` |
| `06-justificativa-nao-publicacao-aviso.md` | `docx/06-justificativa-nao-publicacao-aviso.docx` |
| `07-aviso-intencao-adesao-arp.md` | `docx/07-aviso-intencao-adesao-arp.docx` |
| `08-termo-adesao-ata-registro-precos.md` | `docx/08-termo-adesao-ata-registro-precos.docx` |

### 1.1. Formatação aplicada
Seguiu-se, no que era aplicável, o padrão visual institucional descrito em
`09_padronizacao_documental/PADRAO_VISUAL_DOCUMENTOS.md` e `PERFIS_DOCUMENTAIS.json`: papel A4,
margens 4,23/2,50/3,00/2,00 cm, fonte Calibri 12 pt, corpo justificado com entrelinhas 1,5 e 6 pt
depois do parágrafo, títulos em negrito, tabelas com cabeçalho sombreado (`#D9D9D9`) e repetido, e
campos pendentes (`{{CAMPO}}`, `[PREENCHER: ...]`, `____`) destacados em vermelho (`#C00000`), no
espírito do estilo `CMI Campo Pendente`.

### 1.2. O que **não** foi feito, e por quê
- **Cabeçalho e rodapé institucionais (brasão) não foram criados.** Essas minutas não têm timbre de
  referência — diferente das 22 minutas-mãe de `05_minutas/`, que já trazem a imagem institucional no
  DOCX original. Inventar um brasão ou reproduzir a imagem de outro documento seria fabricar
  identidade visual sem fonte, o que a regra antialucinação deste projeto proíbe. **Antes do uso
  oficial**, a assessoria/comunicação da Câmara deve aplicar o timbre oficial (copiando o cabeçalho e
  rodapé de uma minuta-mãe existente, nunca recriando o brasão do zero).
- **Validação visual (DOCX → PDF) não foi executada.** Não há LibreOffice (`soffice`) nem Microsoft
  Word disponíveis neste ambiente para renderizar e conferir a paginação. A verificação estrutural foi
  feita por leitura programática do DOCX (contagem de parágrafos e tabelas, conferência de que
  nenhuma tabela ficou vazia), mas **falta conferência visual humana** antes de considerar o layout
  definitivo.
- **Nenhuma minuta foi movida para `05_minutas/`.** Continuam em `minutas-tce-cmi/`, com status
  **em homologação** (ver `_CONTROLE_MINUTAS_TCE-CMI.md`). A conversão para DOCX é conveniência de
  uso e leitura — **não é aprovação**. Uso em processo real depende de validação pela assessoria
  jurídica da Câmara.

---

## 2. Guia de aplicação — quando usar cada minuta

| # | Minuta | Quando usar | Antecedente / próximo passo |
|---|---|---|---|
| 1 | Aviso de contratação direta | Toda dispensa por valor (art. 75, I ou II), como regra preferencial (Portaria 06/2024, art. 2º). | Antecede o despacho autorizativo (minuta 2). Se não for publicado, usar a minuta 6 (justificativa). |
| 2 | Despacho autorizativo/ratificação | Ato único do Presidente que autoriza e ratifica a contratação direta (dispensa ou inexigibilidade), consolidando fundamento, parecer/checklist, valor, publicidade e habilitação. | Depende do TR (minuta 4), da pesquisa de preços e, quando exigível, do parecer jurídico ou do checklist (minuta 5). Antecede o extrato (minuta 3), quando houver contrato. |
| 3 | Extrato de contrato | Sempre que a contratação for formalizada por **contrato** (não por ordem de fornecimento/nota de empenho direta). | Depende do despacho (minuta 2) já assinado e da dotação orçamentária confirmada. |
| 4 | Termo de Referência sintético | Objetos de **baixa complexidade** (entrega imediata, produto padronizado, serviço de curta duração) — alternativa enxuta ao TR completo de `05_minutas/TR/`. | Insumo do despacho (minuta 2) e do aviso (minuta 1). Não substitui o TR completo quando o objeto for complexo. |
| 5 | Lista de verificação (checklist) | Sempre que a **análise jurídica for dispensada** (Ato do Diretor Jurídico 01/2024: até 50% dos limites, entrega imediata ou minuta padronizada) e para registrar a habilitação simplificada. | Preenchida **antes** do despacho autorizativo (minuta 2); junta-se aos autos como prova da verificação. |
| 6 | Justificativa de não publicação do aviso | Sempre que a contratação direta **não** for precedida do aviso de 3 dias úteis (inexigibilidade, urgência, baixo valor). | Substitui, nos autos, a comprovação de publicação do aviso (minuta 1); referenciada no despacho (minuta 2). |
| 7 | Aviso de intenção de adesão a ARP | Antes de formalizar adesão (carona) a ata de registro de preços de outro órgão gerenciador. | Antecede o termo de adesão (minuta 8); exige justificativa de vantagem e checagem de preços de mercado. |
| 8 | Termo de adesão a ata de registro de preços | Formalização da adesão, após aceite do fornecedor detentor e do órgão gerenciador. | Depende da minuta 7 (quando adotado o aviso prévio) e da confirmação de que a ata não é de município fiscalizado pelo TCE-MG em posição de conflito (ver dica 7 abaixo). |

**Fluxo típico de uma dispensa por valor:** minuta 1 (aviso) → minuta 4 (TR sintético, se baixa
complexidade) → minuta 5 (checklist, se sem parecer) → minuta 2 (despacho) → minuta 3 (extrato, se
houver contrato). Se o aviso não sair, a minuta 6 substitui a comprovação de publicação no fluxo.

**Fluxo típico de uma adesão a ata:** minuta 7 (aviso de intenção) → minuta 8 (termo de adesão).

> Todas as minutas continuam sujeitas às regras gerais do `CLAUDE.md`: nenhuma é usada em processo
> real sem checagem dos **limites vigentes** (`01_legislacao/limites-vigentes-dispensa-art-75.md`) e
> do **controle anual por CNAE** (`06_precedentes_camara/CONTROLE_CONTRATACOES.md`), e nenhuma
> substitui a validação da assessoria jurídica enquanto estiver em homologação.

---

## 3. Dicas para aumentar segurança jurídica e simplicidade em Itanhandu

Consolidação, sob a ótica de **aplicação prática destas 8 minutas**, das lacunas já identificadas nos
Relatórios 02 e 03 desta pasta. Fonte de cada item indicada entre colchetes.

### 3.1. Segurança jurídica
1. **Nunca dispensar a regularidade fiscal/trabalhista na habilitação simplificada.** A minuta 5
   (checklist, bloco D) já fixa isso como item obrigatório — usá-la em toda contratação com
   habilitação simplificada (Portaria 06/2024, art. 16) fecha a lacuna apontada no Relatório 02, item
   2.3. [`relatorio-02`, item 2.3; `relatorio-03`, item 6 do quadro]
2. **Documentar sempre a ausência do aviso.** Toda vez que a minuta 1 não for usada, preencher a
   minuta 6 e juntá-la aos autos — nunca deixar a ausência de aviso sem registro formal. [`relatorio-02`,
   item 2.2; `relatorio-03`, dica 6]
3. **Certificar a dispensa da análise jurídica pelo checklist (minuta 5), sempre.** Sem ele, a
   dispensa do parecer (Ato 01/2024) fica sem prova de verificação nos autos — o mesmo vício que o
   TCE-MG resolve com a Ordem de Serviço 4/2024, §2º. [`relatorio-02`, item 2.5; `relatorio-03`, dica 5]
4. **Usar o despacho único (minuta 2) em vez de autorizações esparsas.** Consolidar base legal,
   parecer/checklist, enquadramento, valor, publicidade e habilitação em um único ato assinado reduz o
   risco de faltar algum elemento e facilita a leitura do controle externo. [`relatorio-03`, dica 1]
5. **Extrato com dotação e remissão ao processo (minuta 3) em todo contrato.** Preenchimento
   completo evita a falta de rastreabilidade entre extrato publicado e processo de origem —
   fragilidade hoje sem padrão na base de Itanhandu. [`relatorio-03`, dica 2 e item 8 do quadro]
6. **Conferir limite e CNAE antes de assinar o despacho (minuta 2).** O campo de somatório anual por
   subclasse CNAE só protege se for **preenchido com o valor real** consultado em
   `06_precedentes_camara/CONTROLE_CONTRATACOES.md` — campo vazio ou copiado sem conferência é
   risco de fracionamento não detectado. [CLAUDE.md, controle de limite por CNAE; `relatorio-03`, item
   5 "Pontos de atenção"]
7. **Vedar, ou ao menos justificar, adesão a ata de município fiscalizado pelo TCE-MG.** A minuta 7
   já traz o alerta de "carona recíproca"; a Câmara deveria registrar essa checagem como item
   obrigatório antes de formalizar a minuta 8. [`relatorio-02`, item 2.7; `relatorio-03`, item 10 do
   quadro]
8. **Revisar anualmente os limites e os percentuais derivados (50% do Ato 01/2024; 1/4 do limite da
   Portaria 06/2024, art. 16).** Uma atualização de decreto que não se propaga para esses percentuais
   torna as minutas 2 e 5 desatualizadas silenciosamente. [`relatorio-02`, item 4]

### 3.2. Simplicidade operacional
1. **Adotar o TR sintético (minuta 4) como padrão para baixa complexidade.** Reduz o TR a um roteiro
   preenchível sem abrir mão dos elementos mínimos — ganho direto de tempo de instrução.
   [`relatorio-03`, dica 3; `relatorio-02`, item 3.2]
2. **Tratar as 8 minutas como um roteiro único de instrução**, não como peças avulsas: o fluxo da
   seção 2 acima (aviso → TR → checklist → despacho → extrato) evita redescobrir a ordem a cada
   processo. [`relatorio-02`, item 3.3]
3. **Usar a lista de verificação (minuta 5) também como roteiro de conferência antes da assinatura**,
   não só como prova posterior — reduz retrabalho de corrigir despacho já assinado. [`relatorio-02`,
   item 3.1]
4. **Padronizar a pesquisa concomitante à seleção da proposta**, já permitida pela Portaria 03/2024,
   §2º do art. 5º, e sinalizada no campo correspondente da minuta 1 — evita etapa sequencial
   desnecessária em contratações de baixo valor. [`relatorio-03`, item 5 do quadro]
5. **Preencher o extrato (minuta 3) a partir de campos já definidos no despacho (minuta 2)** — mesmos
   dados (objeto, valor, contratada, processo), evitando digitação duplicada e divergência entre as
   duas peças.

---

## 4. Pendências para a assessoria jurídica (antes do uso em processo real)

- Validar juridicamente as 8 minutas (conteúdo), como já determina
  `_CONTROLE_MINUTAS_TCE-CMI.md`, item "Status: minutas em HOMOLOGAÇÃO".
- Aplicar o timbre institucional (cabeçalho/rodapé) aos DOCX gerados, copiando de uma minuta-mãe
  existente — este relatório não o fez (ver item 1.2).
- Executar a validação visual (conversão para PDF e conferência de paginação) quando houver
  LibreOffice ou Word disponível.
- Após aprovação, mover as minutas (Markdown e DOCX) para `05_minutas/`, atualizar
  `05_minutas/_CONTROLE_MINUTAS.md` e registrar a incorporação no `CHANGELOG.md`.

## 5. Fontes utilizadas
- `minutas-tce-cmi/01-aviso-contratacao-direta.md` a `minutas-tce-cmi/08-termo-adesao-ata-registro-precos.md`.
- `minutas-tce-cmi/_CONTROLE_MINUTAS_TCE-CMI.md`.
- `minutas-tce-cmi/09_relatorios/relatorio-02-atos-internos-itanhandu-melhorias-pontos-atencao.md`.
- `minutas-tce-cmi/09_relatorios/relatorio-03-comparativo-instrumentacao-tcemg-vs-itanhandu.md`.
- `09_padronizacao_documental/PADRAO_VISUAL_DOCUMENTOS.md` e `PERFIS_DOCUMENTAIS.json`.
