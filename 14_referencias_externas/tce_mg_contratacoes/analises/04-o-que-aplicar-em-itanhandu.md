---
tipo: doutrina
hierarquia: persuasiva
tema: comparação TCE-MG × Câmara de Itanhandu e medidas aplicáveis
fonte: base Charles / contratações do TCE-MG / normas internas da Câmara
vigencia: vigente
atualizado_em: 2026-08-10
tags: [tce-mg, itanhandu, boas-praticas, esteira, art-92, parecer-juridico, referencia-externa]
---

# O que é igual, o que é diferente e o que dá para implementar

Confronto entre a prática do TCE-MG (analisada em
[01](01-instrucao-dispensa-tcemg.md), [02](02-fase-interna-pregao-tcemg.md) e
[03](03-modelos-padrao-tcemg.md)) e a da Câmara Municipal de Itanhandu, tal como registrada em
`07_checklists/esteira-contratacao-direta.md`, `05_minutas/` e
`06_precedentes_camara/CONTROLE_CONTRATACOES.md`.

> Este documento propõe. **Nenhuma medida daqui é obrigação legal**, e nenhuma altera minuta,
> portaria ou rito por conta própria. Alteração de minuta-mãe exige pedido expresso
> (`05_minutas/_CONTROLE_MINUTAS.md`).

---

## 1. Os dois órgãos não contratam a mesma coisa

| | TCE-MG (2024–2026, publicado) | Câmara de Itanhandu (exercício 2026) |
|---|---|---|
| Volume analisado | 18 dispensas · 57 pregões | 13 dispensas · 12 inexigibilidades |
| Fundamento típico da dispensa | art. 75, **VIII** (emergência) e **IX** (entidade da Administração) | art. 75, **II** (valor) em **todas** as 13 |
| Dispensa por valor com aviso | **nenhuma publicada** | é o rito padrão |
| Inexigibilidade | não aparece no recorte coletado | 12 casos — quase metade das contratações |
| Faixa de valor da dispensa | R$ 35.196,00 a R$ 6.880.339,56 | R$ 158,00 a R$ 33.073,95 |
| Pregão | 57 registros no recorte | nenhum no controle de 2026 |
| Parecer jurídico | em **todo** processo; nos pregões, **duas ou mais** vezes | dispensado abaixo de 50% dos limites do art. 75, I/II, com minuta padronizada ou entrega imediata (Ato do Diretor Jurídico nº 01/2024) |
| Sistemas | SEI · SIAD · CAGEF · Portal Compras MG · Diário Oficial de Contas | PNCP · veículo oficial próprio |

**A conclusão honesta:** este acervo **não** é modelo para o rito que a Câmara mais usa. O
TCE-MG faz dispensa por valor e inexigibilidade — mas publica delas apenas o ato autorizativo e
o extrato, não a instrução. E opera numa escala em que o parecer jurídico prévio é sempre
obrigatório. Copiar o rito seria importar um custo que a lei não impõe a Itanhandu — e que o
Ato 01/2024 expressamente afasta.

O que se aproveita **daqui** é técnica documental: como a peça é escrita, como o controle é
registrado, como a ausência aparece.

**Onde procurar o resto, na própria base:**

- [`03_jurisprudencia/tce_mg/atos_normativos/portaria-002-2024-dispensa-art75-I-II.md`](../../../03_jurisprudencia/tce_mg/atos_normativos/portaria-002-2024-dispensa-art75-I-II.md)
  — a norma do TCE-MG sobre dispensa por valor (documentos obrigatórios, TR sintético,
  habilitação simplificada, aviso de 3 dias úteis).
- [`03_jurisprudencia/tce_mg/atos_normativos/ordem-servico-004-2024-dispensa-analise-juridica.md`](../../../03_jurisprudencia/tce_mg/atos_normativos/ordem-servico-004-2024-dispensa-analise-juridica.md)
  — o equivalente do Ato 01/2024 de Itanhandu, no TCE-MG.
- [`03_jurisprudencia/tce_mg/amostras-instrumentacao-contratacao-direta-tcemg.md`](../../../03_jurisprudencia/tce_mg/amostras-instrumentacao-contratacao-direta-tcemg.md)
  — o padrão dos atos autorizativos e extratos publicados no Diário Oficial de Contas,
  inclusive das inexigibilidades do art. 74.

---

## 2. O que já é igual — ou melhor — em Itanhandu

| Ponto | Situação |
|---|---|
| Estrutura do TR | O TR de Itanhandu é mapeado ao **art. 6º, XXIII, "a" a "j"** (`05_minutas/TR/TR_FICHA_DE_USO.md`, seção 6). O TR do TCE-MG tem 15–16 seções que **não** seguem a ordem das alíneas. Vantagem de Itanhandu |
| Conteúdo do ETP | 13 seções contra os 16 itens do TCE-MG, mas cobrindo o mesmo art. 18, §1º |
| Registro de fracassado/deserto | A Ata de Julgamento já prevê o resultado fracassado/deserto (`05_minutas/ATA_JULGAMENTO/`), com as providências do art. 18 da Portaria 06/2024. É o documento que, depois, sustentaria uma dispensa do art. 75, III |
| Rastreabilidade das peças | O `PAINEL_PROCESSO.md` da gestão documental (`scripts/gestao_documental/gerar_painel.py`) é o equivalente automático do "relatório" com que o parecer do TCE-MG abre |
| Controle de fracionamento | O `CONTROLE_CONTRATACOES.md` por subclasse CNAE **não tem equivalente** no acervo do TCE-MG. Vantagem de Itanhandu |
| Pesquisa de preços | `07_checklists/regras-pesquisa-de-precos.md` já exige memória de cálculo, comparabilidade e justificativa. Falta o **formato**, não a regra |

---

## 3. O que dá para implementar

Cinco medidas, da mais barata para a mais cara.

### 3.1 Checklist "inciso do art. 92 → cláusula do contrato" — **alta prioridade, custo baixo**

**O que o TCE-MG faz:** o parecer percorre os incisos do art. 92 e escreve, para cada um, em
qual cláusula da minuta ele está; quando não está, escreve **"não prevista"** — e isso vira
pendência na conclusão ([análise 01, seção 4](01-instrucao-dispensa-tcemg.md)).

**Por que serve a Itanhandu:** funciona **sem** consultoria jurídica. É conferência do agente de
contratação sobre a minuta já preenchida. E é justamente onde o Ato 01/2024 dispensa o parecer
que a conferência some — hoje não há, em `05_minutas/` nem em `07_checklists/`, nenhum
mapeamento inciso→cláusula.

**Como fazer:** um checklist novo em `07_checklists/`, com uma linha por inciso do art. 92 e
uma coluna para a cláusula da minuta de contrato de Itanhandu em que ele está atendido.
Preenchido uma vez por minuta (não por processo), revalidado quando a minuta mudar. Vira etapa
da esteira, entre "Contrato/substituto" e "Extrato".

### 3.2 O ETP fecha a conta contra o PCA — **custo baixo**

**O que o TCE-MG faz:** o item 3 do ETP diz o valor previsto no PCA, o valor estimado agora, a
diferença em reais e a razão. O parecer se apoia nesse item para admitir a contratação acima do
planejado.

**Como fazer:** o campo `{{PREVISAO_PCA}}` da minuta de ETP já existe. Muda o **conteúdo**: em
vez de "consta do PCA", escrever previsto / estimado / diferença / motivo. Não exige alterar a
minuta-mãe.

### 3.3 Mapa de preços com o preço descartado e o motivo — **custo médio**

**O que o TCE-MG faz:** cada mapa traz, por item, valor mínimo, valor máximo, orçamento
estimado unitário e total, **metodologia** (média, mediana, menor valor) e, no detalhamento,
cada preço com fornecedor, marca/modelo, procedimento de contratação, data de referência e
origem — além dos **preços desconsiderados e o motivo do descarte**. Em contratação por lotes,
há **um mapa por lote ou por item**, não um mapa da contratação inteira.

**Por que serve:** preço eliminado que não aparece no documento é decisão sem rastro. É
exatamente o que o TCE-MG cobra da Câmara quando fiscaliza.

**Como fazer:** `scripts/normalizar_precos.py` já calcula média, mediana, menor e discrepância
por IQR. O que falta é a saída **mostrar o descartado com o motivo**, e a minuta
`05_minutas/PESQUISA_DE_PRECOS/` acomodar essa coluna. Alteração de minuta-mãe → **depende de
pedido expresso**.

### 3.4 Resposta a fornecedor vira peça dos autos, com prova de publicação — **custo baixo**

**O que o TCE-MG faz:** pedido de esclarecimento, resposta, impugnação, razões de recurso,
contrarrazões e decisões são numerados e juntados. Em um dos pregões há um **print da tela do
SIAD** juntado só para provar que a resposta foi publicada no sistema, e não enviada apenas a
quem perguntou.

**Por que serve:** na dispensa com aviso, responder a um fornecedor sem publicar a resposta
desiguala a disputa. A prova da publicação é o que demonstra que não houve.

**Como fazer:** ao responder qualquer questionamento sobre um aviso, juntar aos autos a
pergunta, a resposta e a evidência de publicação (print com data/hora e URL). Encaixa em
`07_checklists/roteiro-julgamento-dispensa-com-aviso.md` e usa a área
`07_MATERIAL_DE_TRABALHO/` da gestão documental.

### 3.5 O jurídico volta quando o instrumento convocatório muda — **custo baixo**

**O que o TCE-MG faz:** quando uma impugnação altera o edital, sai um parecer só sobre a
impugnação, o edital é republicado e **um novo parecer** examina a versão retificada (Pregão
219/2025: Parecer 1666 → Edital 60 → Parecer 1729 → Edital 63 → Parecer 1733).

**Por que serve:** o Ato 01/2024 dispensa a análise jurídica, **mas** o §2º manda que ela ocorra
"acaso haja dúvida jurídica". Retificar aviso ou TR já publicado é exatamente isso. Vale fixar
o gatilho por escrito para não depender de julgamento caso a caso.

**Como fazer:** registrar o gatilho no roteiro de dispensa com aviso — retificação de aviso ou
de TR já divulgado provoca a assessoria jurídica, ainda que o valor esteja abaixo dos 50%.

---

## 4. O que **não** vale copiar

| Prática do TCE-MG | Por que não |
|---|---|
| Parecer jurídico em toda contratação | O art. 53, §5º autoriza a dispensa, e o Ato do Diretor Jurídico nº 01/2024 já a regulamentou. Reintroduzir o parecer universal é criar exigência que a Câmara afastou |
| Seis declarações separadas (Anexos III a VIII do edital) | Itanhandu usa `05_minutas/DECLARACAO_UNIFICADA/`. Fragmentar aumenta a chance de o fornecedor esquecer uma |
| Reescrever o TR no formato do TCE-MG | O TR de Itanhandu segue a ordem das alíneas do art. 6º, XXIII. Trocar por um modelo que não segue seria piorar |
| Prazos, foro, índices e limites de multa | Decreto Estadual nº 45.902/2012, Resolução 14/2017 do TCEMG, foro de Belo Horizonte, vigência contada da publicação no DOC — tudo estadual |
| Estrutura orgânica (Consultoria-Geral Adjunta, Núcleo de Proteção de Dados, Coordenadoria de Planejamento das Contratações) | Itanhandu transporta a **função** (controle prévio de legalidade, art. 53), não o organograma |

---

## 5. Ordem sugerida

1. **3.1** — checklist do art. 92 (fecha o maior buraco de controle e não depende de ninguém).
2. **3.5** — gatilho de retorno ao jurídico na retificação (uma linha em um roteiro existente).
3. **3.4** — prova de publicação das respostas a fornecedor.
4. **3.2** — ETP fechando a conta contra o PCA.
5. **3.3** — formato do mapa de preços — o único que exige revisar minuta-mãe, com pedido
   expresso, backup, versionamento da ficha e changelog.
