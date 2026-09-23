---
tipo: minuta
hierarquia: oficial
documento: aviso de contratacao direta
tema: contratacao direta
fonte: Câmara Municipal de Itanhandu / Minuta-Mãe 2026 revisada
orgao: camara municipal de itanhandu
uso: dispensa por valor (art. 75, I e II) realizada sem sistema eletronico
versao: 2.1
vigencia: vigente
atualizado_em: 2026-09-23
tags: [minuta, aviso, dispensa, contratacao-direta, art-75, portaria-06-2024,
  nao-eletronica, habilitacao, diligencia, me-epp, desempate, saneamento,
  formalismo-moderado, proposta-email]
---

# Ficha de Uso — Aviso de Contratação Direta (Minuta-Mãe 2026 revisada, v2.1)

Arquivo: `05_minutas/AVISO/AVISO_CONTRATACAO_DIRETA_MINUTA_MAE.docx` (DOCX, timbre da Câmara
no cabeçalho). Versões anteriores arquivadas em `05_minutas/AVISO/_arquivo/` (v1.0 e v2.0).

Esta ficha funciona como manual rápido: diz para que serve a minuta, como conduzir a dispensa
depois de publicada e o que conferir antes de publicar.

> **Anexos (item 10.8):** I — Documentação exigida para habilitação (**na própria minuta**, após a
> assinatura); II — TR aprovado do processo; III — minuta de contrato, quando houver. Ver seção 8.

---

## 1. Finalidade e limites de uso

Minuta destinada **exclusivamente** às dispensas de licitação em razão do valor, com fundamento
no art. 75, incisos I ou II, da Lei nº 14.133/2021, realizadas **sem sistema eletrônico**, com
recebimento de propostas por e-mail institucional e, facultativamente, por entrega presencial.

> **NÃO UTILIZAR esta minuta, sem adaptação específica e fundamentada, para:**
> - dispensa emergencial ou qualquer outra hipótese do art. 75 além dos incisos I e II;
> - inexigibilidade;
> - credenciamento;
> - contratação direta sem disputa (sem aviso) — nesse caso, a ausência do aviso se justifica na
>   [[justificativa-contratacao-direta]], não nesta peça;
> - dispensa eletrônica (Portaria 06/2024, art. 2º, §3º: segue regulamento próprio).

### Por que a forma não eletrônica

O recebimento por e-mail é simples e gratuito: o fornecedor não precisa se cadastrar em
plataforma, e o canal não tem limitação territorial. A minuta registra isso no item 1.2 e abre a
participação "independentemente de sua localização geográfica" (item 2.1).

A justificativa **não** usa "participação de fornecedores locais". A expressão não tem apoio
jurídico e pode ser lida como favorecimento geográfico.

---

## 2. Prazo de divulgação: o que vem da Lei e o que vem da Portaria

| Fonte | O que diz (texto) | Efeito |
|---|---|---|
| Lei 14.133/2021, art. 75, §3º | As contratações dos incisos I e II "serão **preferencialmente** precedidas de divulgação de aviso em sítio eletrônico oficial, pelo prazo mínimo de 3 (três) dias úteis" | A Lei **não** torna o aviso obrigatório. Se houver aviso, o prazo mínimo é de 3 dias úteis. |
| Portaria 06/2024, art. 2º | Repete o texto do §3º ("preferencialmente") | Mesmo efeito da Lei. |
| Portaria 06/2024, art. 5º, caput | A Câmara "**deverá** publicar aviso de contratação direta" com as informações dos incisos I a VII | Regra **interna** mais rígida que a Lei, para as dispensas regidas pela Portaria (art. 1º: dispensa por valor sem sistema eletrônico). |
| Portaria 06/2024, art. 5º, §1º | O prazo para abertura e julgamento "não será inferior a 3 (três) dias úteis, **contados da data de divulgação** do aviso" | Prazo mínimo obrigatório, contado da divulgação. |
| Portaria 06/2024, art. 5º, VI | Data e horário máximo de envio, "respeitado o horário comercial" | `{{HORA_FIM_PROPOSTAS}}` deve cair em horário comercial. |

**Interpretação:** o caráter preferencial vem da Lei. A obrigatoriedade do aviso nas dispensas por
valor não eletrônicas decorre da Portaria 06/2024, art. 5º. Deixar de publicar aviso nesses casos
exige justificativa específica e, conforme o caso, manifestação jurídica sobre o afastamento da
regra interna.

**Divulgação (Portaria 06/2024, art. 6º; Aviso, item 8.1):** Diário Oficial do Município, sítio
oficial da Câmara (íntegra) e PNCP (parágrafo único, observado o art. 176 da Lei).

---

## 3. Fluxo operacional da dispensa

1. Publicar o Aviso e o Termo de Referência, juntos.
2. Receber propostas durante o prazo fixado. Nada é comparado, classificado ou negociado antes do
   encerramento (item 3.3).
3. Encerrar o recebimento e classificar as propostas pelo critério de julgamento (item 4.1).
4. Analisar a proposta mais bem classificada e negociar, se necessário (itens 4.6 e 4.7).
5. Havendo empate: disputa final entre os empatados; persistindo, art. 60 da Lei e, por último,
   sorteio público registrado em ata (itens 4.8 e 4.9).
6. Convocar **somente o primeiro colocado** para habilitação, pelo e-mail da proposta, com prazo de
   1 dia útil, prorrogável uma vez (itens 5.1 e 5.2).
7. Consultar diretamente certidões, registros e cadastros disponíveis em fontes oficiais e juntar os
   comprovantes (item 5.3).
8. Pedir ao fornecedor apenas o que a Câmara não conseguir obter ou verificar (item 5.2).
9. Diligenciar o que for sanável (item 5.5 e seção 5 desta ficha).
10. Primeiro colocado inabilitado: repetir negociação e habilitação com o seguinte (item 5.10).
11. Encaminhar ao Presidente para adjudicação e homologação (Portaria 06/2024, art. 19) e formalizar
    por contrato ou instrumento equivalente (item 6.1).
12. Fazer as publicações posteriores (itens 8.2 e 8.3) e registrar a contratação no controle por
    CNAE (`python scripts/controle_cnae.py registrar ...`).

Roteiro detalhado de julgamento: `07_checklists/roteiro-julgamento-dispensa-com-aviso.md`.

---

## 4. Regra principal de habilitação

- A documentação de habilitação **não precisa acompanhar a proposta** (itens 3.10 e 5.1.1).
- A ausência de documentos de habilitação junto à proposta **não desclassifica nem inabilita**
  (itens 3.10, 5.9 e 7.3).
- A habilitação é verificada **apenas do fornecedor provisoriamente classificado em primeiro
  lugar** (item 5.1).
- A Câmara obtém diretamente, sempre que possível, certidões e registros em sítios oficiais
  (item 5.3). Documento que a Câmara consegue obter em fonte oficial não inabilita por estar
  ausente do e-mail do fornecedor (item 5.3.1).
- O fornecedor apresenta, no prazo da convocação, só o que não puder ser obtido pela Administração
  (item 5.2).

**Fundamento na base:**
- Lei 14.133/2021, art. 72, V: o processo de contratação direta deve conter "comprovação de que o
  contratado preenche os requisitos de habilitação e qualificação mínima necessária". A Lei exige a
  comprovação do contratado, não de todos os proponentes.
- Lei 14.133/2021, art. 68, §1º: os documentos de regularidade fiscal, social e trabalhista "poderão
  ser substituídos ou supridos, no todo ou em parte, por outros meios hábeis a comprovar a
  regularidade do licitante, inclusive por meio eletrônico".

---

## 5. Diligências e saneamento

**Pergunta-chave:** faltou comprovar documentalmente uma condição que **já existia**? Avaliar
diligência. A condição só passou a existir **depois**? Não sanar como se já existisse.

Antes de inabilitar ou desclassificar por falha documental, verificar:

- o requisito material existia na data relevante (data-limite de recebimento das propostas)?
- é possível comprová-lo por fonte oficial?
- trata-se de erro, omissão ou falha formal?
- o saneamento preserva a isonomia e não altera o preço nem a substância da proposta?
- o documento apenas comprova situação preexistente?

| Pode ser sanado | Não pode ser sanado |
|---|---|
| Complementar informação sobre documento já apresentado, para apurar fato existente à época (Lei, art. 64, I; item 5.5) | Criar depois um requisito de habilitação que o fornecedor não tinha na data exigida (item 5.5) |
| Atualizar documento cuja validade expirou **após** a data de recebimento das propostas (Lei, art. 64, II; item 5.5.1) | Aceitar documento vencido **antes** da data-limite como se estivesse válido |
| Erro material, aritmético ou de preenchimento, sem majorar o preço global (item 4.3) | Majorar o preço ou mudar a substância ou as condições competitivas da proposta (item 4.3) |
| Falta de assinatura, se autoria e integridade forem confirmáveis por outro meio (item 3.5) | Suprir por diligência condição essencial do objeto que a proposta não atende (item 4.2, b) |

Texto da Lei (art. 64): após a entrega, só se admitem novos documentos em diligência para
"complementação de informações acerca dos documentos já apresentados pelos licitantes e desde que
necessária para apurar fatos existentes à época da abertura do certame" (I) e "atualização de
documentos cuja validade tenha expirado após a data de recebimento das propostas" (II). O §1º
permite sanar erros ou falhas que não alterem a substância dos documentos, por despacho
fundamentado. A minuta aplica essa lógica também às propostas (itens 4.3 e 10.1 — formalismo
moderado). Toda diligência e seu resultado vão para os autos.

---

## 6. Habilitação simplificada

Antes de definir o Anexo I, verificar se cabe dispensa total ou parcial da documentação.

Texto da Lei 14.133/2021, art. 70, III (repetido na Portaria 06/2024, art. 16): a documentação
pode ser "dispensada, total ou parcialmente, nas contratações para entrega imediata, nas
contratações em valores inferiores a 1/4 (um quarto) do limite para dispensa de licitação para
compras em geral e nas contratações de produto para pesquisa e desenvolvimento até o valor de
R$ 300.000,00". O valor atualizado de 1/4 do limite está em
`01_legislacao/limites-vigentes-dispensa-art-75.md`.

- Não exigir automaticamente todos os documentos em toda contratação. As exigências devem ser
  proporcionais ao objeto, ao valor e aos riscos (item 5.11).
- A dispensa é **faculdade**, não direito do fornecedor: selecionar os requisitos no Anexo I e
  motivar a escolha nos autos (item 5.11).
- O art. 72, V, continua valendo: mesmo com habilitação simplificada, o processo precisa comprovar a
  qualificação mínima do contratado.
- Qualificação técnica e econômico-financeira só quando previstas no TR, justificadas e
  proporcionais (Anexo I, notas das seções 3 e 4).

---

## 7. ME/EPP

Havendo restrição de regularidade fiscal ou trabalhista de ME/EPP, **não inabilitar
automaticamente** (Aviso, item 5.7; Anexo I, subitem 2.10). Texto da LC 123/2006
(`01_legislacao/lc-123-2006-estatuto-microempresa-epp.md`):

- art. 42: a comprovação de regularidade fiscal e trabalhista de ME/EPP "somente será exigida para
  efeito de assinatura do contrato";
- art. 43, caput: a ME/EPP deve apresentar toda a documentação de regularidade, "mesmo que esta
  apresente alguma restrição";
- art. 43, § 1º: prazo de **5 dias úteis**, contado do momento em que for declarada vencedora,
  prorrogável por igual período a critério da Administração, para regularizar;
- art. 43, § 2º: sem regularização, decadência do direito à contratação, facultado convocar os
  remanescentes na ordem de classificação.

**Empate ficto (arts. 44 e 45):** proposta de ME/EPP igual ou até 10% superior à mais bem
classificada (quando esta não for de ME/EPP) dá à ME/EPP o direito de apresentar preço inferior.
Verificar antes de convocar para habilitação e registrar na ata. A Lei 14.133/2021, art. 4º, manda
aplicar os arts. 42 a 49 da LC 123/2006, com os limites dos §§ 1º e 2º.

A Portaria 06/2024, art. 5º, IV, exige que o aviso observe a LC 123/2006.

---

## 8. Campos variáveis e anexos

### 8.1 Campos do Aviso (preenchidos pela Câmara)

| Campo | Conteúdo | Cautela |
|---|---|---|
| `{{NUMERO_AVISO}}` | nº/ano do aviso | |
| `{{CRITERIO_JULGAMENTO}}` | ex.: MENOR PREÇO POR ITEM | coerente com o TR |
| `{{FUNDAMENTO_LEGAL}}` | ex.: 75, inciso II | a frase já traz "art." antes do campo |
| `{{DATA_INICIO_PROPOSTAS}}` | data de início | a partir da divulgação |
| `{{HORA_INICIO_PROPOSTAS}}` | hora de início | |
| `{{DATA_FIM_PROPOSTAS}}` | data-limite | ≥ 3 dias úteis contados da divulgação (Portaria, art. 5º, §1º) |
| `{{HORA_FIM_PROPOSTAS}}` | hora-limite | horário comercial (Portaria, art. 5º, VI) |
| `{{OBJETO}}` | objeto | idêntico ao do TR |
| `{{DATA}}` | data de assinatura | |
| `{{NOME_PRESIDENTE}}` | Presidente da Câmara | |

Dados institucionais fixos já constam do modelo: e-mail `compras@itanhandu.cam.mg.gov.br`,
endereço da sede e link `https://www.itanhandu.cam.mg.gov.br/imprensa/licitacoes`.

### 8.2 Anexo I — Documentação exigida para habilitação (na minuta)

Estrutura no molde do Anexo I dos modelos de aviso de dispensa
(`14_referencias_externas/modelos_aviso_contratacao_direta/`): 1. habilitação jurídica (art. 66);
2. regularidade fiscal, social e trabalhista (art. 68); 3. qualificação econômico-financeira
(art. 69); 4. qualificação técnica (art. 67); 5. disposições gerais do anexo.

- **Notas explicativas** em vermelho itálico orientam a escolha e **devem ser excluídas antes da
  publicação**.
- **Trechos entre colchetes em vermelho** (`[indicar ...]`) são campos a preencher conforme o objeto.
- Seções 3 e 4 só quando previstas e justificadas no TR. Nas hipóteses do art. 70, III, manter ao
  menos a seção 2 (ver seção 6 desta ficha).
- Ao excluir subitens, renumerar apenas dentro da seção; não alterar a numeração do Aviso.

### 8.3 Anexos II e III (fora desta minuta)

O aviso não traz modelo de proposta. O fornecedor usa formulário próprio, PDF ou o corpo do
e-mail (item 3.4), com as informações mínimas do item 3.6: razão social, CPF/CNPJ, contatos,
descrição do objeto, preços, prazo e validade.

| Anexo | Origem |
|---|---|
| II — Termo de Referência | TR aprovado do processo |
| III — Minuta de contrato (se houver) | `05_minutas/CONTRATO*/`; com instrumento equivalente, excluir o Anexo III do item 10.8 |

---

## 9. Ajustes da revisão v2.1 (2026-09-23)

- Item 8.1: publicação do aviso no Diário Oficial do Município (Portaria 06/2024, art. 6º).
- Item 3.9, c: declaração de reserva de cargos para pessoa com deficiência e reabilitado.
- Item 9.1, d: cotação com pelo menos 3 fornecedores (Portaria 06/2024, art. 18, IV).
- Item 10.8 e Anexo I: relação de anexos (I habilitação, II TR, III contrato quando houver) e
  documentação de habilitação incorporadas à minuta. Modelo de proposta e declaração unificada
  não são anexos do aviso.
- Item 1.2: numeração corrigida (a minuta saltava do 1.1 para o 1.3).

---

## 10. Partes fixas e partes adaptáveis

**Dados fixos (não alterar):**
- timbre e identificação institucional;
- endereço;
- e-mail institucional;
- sítio oficial;
- bloco de assinatura.

**Alterar somente com justificativa nos autos:**
- sistemática de julgamento (item 4);
- sistemática de habilitação (item 5);
- diligências e saneamento (itens 4.3, 5.5 e 10.1);
- desempate (itens 4.8 e 4.9);
- sanções (item 7);
- comunicações e contagem de prazos (item 8);
- procedimento deserto ou fracassado (item 9).

**Adaptar em toda contratação:**
- objeto;
- fundamento legal;
- critério de julgamento;
- datas e horários;
- requisitos de habilitação (Anexo I: selecionar subitens, preencher colchetes, excluir notas);
- exigências técnicas (no TR);
- instrumento de contratação: contrato ou equivalente (item 6.1) e, com ele, o Anexo III do item 10.8.

---

## 11. Checklist antes da publicação

- [ ] Hipótese é art. 75, I ou II, sem sistema eletrônico (seção 1).
- [ ] Fundamento legal correto e coerente com o objeto.
- [ ] Limite por CNAE conferido (`07_checklists/roteiro-limite-dispensa-cnae.md`).
- [ ] Objeto idêntico ao do Termo de Referência.
- [ ] Critério de julgamento definido e coerente com o TR.
- [ ] Datas e horários preenchidos; fim em horário comercial.
- [ ] Prazo mínimo de 3 dias úteis contados da divulgação conferido.
- [ ] Preço estimado, quantidades, local e prazo de entrega constam do TR publicado (Portaria,
      art. 5º, II e III).
- [ ] Habilitação proporcional ao objeto; art. 70, III avaliado (seção 6).
- [ ] Anexo I ajustado ao objeto: subitens inaplicáveis excluídos e colchetes preenchidos.
- [ ] Anexo I coerente com o TR (nada exigido no Anexo I sem previsão no TR, e vice-versa).
- [ ] Notas explicativas em vermelho removidas.
- [ ] Item 10.8 coerente com os anexos efetivamente publicados.
- [ ] Orientações internas e blocos opcionais não utilizados removidos.
- [ ] Nenhum `{{CAMPO}}` sem preenchimento.
- [ ] E-mail e link institucionais conferidos.
- [ ] Aviso e TR publicados juntos: sítio oficial, Diário Oficial do Município e PNCP (Portaria,
      art. 6º).

---

## 12. Fontes prioritárias

1. Lei nº 14.133/2021 (arts. 60, 64, 68, 70, 72, 75, §3º) —
   `01_legislacao/lei-14133-2021-licitacoes-contratos-administrativos.md`
2. Portaria nº 06/2024 da Câmara (arts. 1º, 2º, 5º, 6º, 9º a 19) —
   `02_normas_internas/regulamento-licitacoes-camara-itanhandu.md`
3. Demais normas internas da Câmara.
4. Lei Complementar nº 123/2006 (arts. 42 a 49) —
   `01_legislacao/lc-123-2006-estatuto-microempresa-epp.md`
5. Modelo de Aviso de Contratação Direta da AGU (abr/2026), referência externa preferencial —
   `14_referencias_externas/modelos_aviso_contratacao_direta/modelo-agu-aviso-contratacao-direta-abr-2026.md`;
   molde do Anexo I —
   `14_referencias_externas/modelos_aviso_contratacao_direta/modelo-portal-compras-publicas-aviso-dispensa-eletronica.md`
6. Jurisprudência do TCU e do TCE-MG aplicável (`03_jurisprudencia/`).
7. Doutrina e materiais de apoio, apenas subsidiariamente.

---

## 13. Regra de ouro

A minuta-mãe não se usa por simples preenchimento automático. Antes de cada publicação, adaptar o
documento à natureza, ao valor, aos riscos e às peculiaridades do objeto, e excluir as instruções
internas e as cláusulas opcionais que não se aplicam.

---

FONTES:
- 01_legislacao/lei-14133-2021-licitacoes-contratos-administrativos.md | arts. 4º, 60, 63, 64, 65 §1º, 66 a 70, 72 V, 75 §3º | vigente | 2026-06-27
- 01_legislacao/lc-123-2006-estatuto-microempresa-epp.md | arts. 42 a 45, 49 | vigente | 2026-09-23
- 02_normas_internas/regulamento-licitacoes-camara-itanhandu.md | Portaria 06/2024, arts. 1º, 2º, 5º, 6º, 9º, 15, 16, 18, 19 | vigente | 2026-06-25
- 01_legislacao/limites-vigentes-dispensa-art-75.md | 1/4 do limite (art. 70, III) | vigente | ver frontmatter
