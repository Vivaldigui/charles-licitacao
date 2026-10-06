---
tipo: checklist
hierarquia: operacional
tema: limite de dispensa por valor e ramo de atividade (CNAE)
fonte: Lei 14.133/2021, art. 75, §1º + Portaria 06/2024 + Consulta TCEMG 1104833 + IBGE/CONCLA + estudo ramo de atividade (2026-10-06)
vigencia: vigente
atualizado_em: 2026-10-06
tags: [checklist, dispensa, limite, cnae, ramo-de-atividade, fracionamento, art-75]
---

# Roteiro — Análise do limite de dispensa por valor (ramo de atividade / CNAE)

Roteiro que o **Charles** segue para avaliar o **cabimento da dispensa por valor** (art. 75, I e
II) e o **risco de fracionamento**, com base no **ramo de atividade** (subclasse CNAE). O
resultado alimenta o controle vivo em `06_precedentes_camara/CONTROLE_CONTRATACOES.md`.

## 1. Fundamento
- **Lei 14.133/2021, art. 75, §1º, II** — o limite da dispensa por valor é aferido pelo
  **somatório da despesa realizada com objetos de mesma natureza**, "entendidos como tais
  aqueles relativos a contratações no **mesmo ramo de atividade**".
- **Portaria 06/2024 da Câmara, art. 2º, §§1º-2º** — afere-se pelo somatório do **exercício
  financeiro** da Câmara, e **"considera-se ramo de atividade a partição econômica do mercado,
  identificada pelo nível de subclasse da CNAE"**.
- **Consulta TCEMG nº 1104833** — "mesma natureza" = mesmo ramo de atividade; usar critério
  objetivo (subclasse CNAE); não definir a natureza apenas pelo elemento de despesa contábil.
- **Doutrina** (Jacoby Fernandes, 2021): ramos de especialidade diversos podem ser contratados
  separadamente (ex.: reforma de edifício e instalação de piso são ramos distintos), pois o que
  importa é o universo de fornecedores aptos àquele objeto.

## 2. O que é a CNAE (para enquadrar o ramo)
Classificação Nacional de Atividades Econômicas, hierárquica em **5 níveis**: seção → divisão →
grupo → classe → **subclasse**. O **5º nível (subclasse)** é o critério adotado pela Câmara.
Versão vigente: **CNAE-Subclasses 2.3** (em vigor desde 01/01/2019; 1.332 subclasses).
Consulta oficial: **https://concla.ibge.gov.br/busca-online-cnae.html**.

## 2-A. Enquadra-se o OBJETO, não o fornecedor

A subclasse que entra na soma é a do **objeto** da contratação. O CNAE e o objeto social do
fornecedor **não** definem a subclasse da despesa.

- **Fundamento.** A Lei compara "objetos de mesma natureza" (art. 75, §1º, II). A Consulta TCEMG
  1104833 (p. 9) afirma que o critério da subclasse não se refere ao objeto social ou ao CNAE do
  futuro fornecedor: é verificação feita no planejamento, antes de haver fornecedor.
- **Onde entra o CNAE do fornecedor:** só na habilitação, para verificar se a atividade dele é
  compatível com o objeto, ainda que de forma genérica. Se não for, o problema é de habilitação e
  não muda a subclasse da despesa.
- **Exemplos.**
  - Cadeira de rodas comprada de loja de informática: soma em 4773-3/00 (artigos médicos e
    ortopédicos), não em 4751-2/01.
  - Certificado digital: soma em 6319-4/00, mesmo que o vendedor tenha CNAE principal de
    informática.
- **Vedação.** Não escolher a subclasse pelo CNAE do vencedor para fugir de uma subclasse já perto
  do limite. Isso inverte o critério e caracteriza o risco que o §1º quer evitar.
- **Objeto misto.** Enquadrar pelo item predominante (leitura conservadora) ou item a item, com
  justificativa escrita para cada item.
- **Objeto com instalação ou montagem.** Verificar se é serviço de engenharia (art. 75, I). As
  subclasses de instalação da divisão 43 da CNAE são tratadas pelo TCE-MG como serviço
  especializado de engenharia.
- **Outros modelos, sem efeito para a Câmara.** A União usa a linha de fornecimento do Sicaf
  vinculada ao catálogo (IN SEGES/MGI 8/2023). O TCE-SP usa a classe do catálogo federal para as
  próprias contratações (Resolução 16/2025). A Câmara segue a Portaria 06/2024 (subclasse CNAE)
  até que ela seja alterada.

Estudo completo: `04_doutrina_artigos/estudo-ramo-atividade-objeto-ou-fornecedor-cnae.md`.

## 3. Passo a passo
1. **Enquadrar o objeto** na **subclasse CNAE** correspondente (consultar a ferramenta do IBGE;
   **não inventar código** — registrar o código e a denominação encontrados). Use o objeto,
   nunca o CNAE do fornecedor (item 2-A).
2. No `CONTROLE_CONTRATACOES.md`, **somar o já despendido no exercício financeiro corrente**
   pela Câmara com a **mesma subclasse CNAE** (dispensas por valor — art. 75, I/II).
3. **Somar o valor** da nova contratação pretendida.
4. **Comparar com o limite vigente** do inciso aplicável (ver
   `01_legislacao/limites-vigentes-dispensa-art-75.md`):
   - **I** — obras e serviços de engenharia; manutenção de veículos automotores;
   - **II** — demais compras e serviços.
5. **Decidir:**
   - Somatório **≤ limite** → dispensa por valor **cabível**.
   - Somatório **> limite** → **não** cabe dispensa por valor; planejar licitação ou outra
     hipótese legal, **sem fracionar** a despesa.
   - **Próximo do limite** → **alertar** e orientar planejamento (agregação de demandas — PCA).
6. **Registrar a conclusão** no `CONTROLE_CONTRATACOES.md`, atualizando o acumulado da subclasse
   no exercício.

## 3-A. Quando aferir: na ABERTURA, não no fim

A aferição é **pré-requisito da abertura do processo**, não conferência final. Descobrir o
estouro depois do DFD, do TR e da pesquisa de preços custa o trabalho todo — e obriga a
refazer o enquadramento com o processo já instruído.

```bash
# Simulação isolada, antes de abrir qualquer coisa:
python scripts/controle_cnae.py simular --objeto "<objeto>" --cnae "<subclasse>" --valor "<BR>" --como-trava
```

`--como-trava` faz o comando **sair com código 1** nas faixas impeditivas, para poder ser usado
como porta de entrada em script ou rotina.

A abertura do processo já faz isso sozinha quando recebe `--cnae`:

```bash
python scripts/gestao_documental/iniciar_processo.py --numero "PA 031/2026" --objeto "<objeto>" --fundamento "art. 75, II" --valor-estimado 15000 --cnae "4751-2/01"
```

| Situação | O que acontece |
|---|---|
| Fundamento **não** é dispensa por valor | não afere (inexigibilidade não entra na conta do § 1º) |
| Verde / amarelo | abre; o amarelo vira pendência de acompanhamento |
| Vermelho / estouro / limite não confirmado | **abertura recusada**, com o somatório na mensagem |
| Sem CNAE ou sem valor | abre, e registra "o limite NÃO foi aferido" como pendência |

O impedimento se destrava com `--justificativa-fracionamento "<razão>"`, que fica gravada no
`PROCESSO.json` e vira pendência de juntada aos autos. **Não existe `--forcar` aqui**: o que
destrava é uma razão escrita, que o controle interno pode ler.

### Faixas

| Faixa | Uso do limite | Leitura |
|---|---|---|
| verde | < 60% | segue |
| amarelo | 60% a 85% | segue, planejando agregação no PCA |
| vermelho | 85% a 100% | impeditivo: reavaliar antes de enquadrar |
| **estouro** | **> 100%** | impeditivo: **não cabe** dispensa por valor neste ramo |

`estouro` é faixa própria desde 2026-08-01. Antes, 86% e 240% recebiam o mesmo rótulo — o que
escondia exatamente a situação que o art. 75, § 1º, quer evitar.

## 4. Cautelas
- O agente deve **estudar as subclasses** e enquadrar corretamente (familiaridade com a CNAE).
- Objetos de **ramos diversos** (fornecedores distintos) **não** se somam; objetos do **mesmo
  ramo** somam-se, ainda que adquiridos em momentos diferentes do exercício.
- Não usar o **elemento de despesa contábil** como critério de "natureza".
- Inexigibilidade (art. 74) e demais dispensas que **não** são por valor não entram na aferição
  dos limites dos incisos I e II (mas devem ser registradas no controle).
- **Art. 75, § 7º** (R$ 10.478,74 em 2026) afasta a regra do § 1º **apenas** para manutenção de
  veículos automotores do próprio órgão, incluído o fornecimento de peças. Não é franquia geral
  de valor abaixo da qual o fracionamento deixa de ser aferido.

## Fontes
Lei nº 14.133/2021 (art. 75, §1º); Portaria nº 06/2024 (art. 2º, §§1º-2º);
[[consulta-tcemg-1104833-dispensa-valor-ramo-atividade]]; [[limites-vigentes-dispensa-art-75]];
[[estudo-ramo-atividade-objeto-ou-fornecedor-cnae]];
[[resolucao-tcesp-16-2025-ramo-de-atividade-dispensa]]; IBGE/CONCLA (CNAE-Subclasses 2.3).
