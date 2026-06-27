---
tipo: checklist
tema: pesquisa de precos
fonte: base Charles / Lei 14.133/2021 art. 23 / Portaria 03/2024 da Câmara de Itanhandu
vigencia: vigente
atualizado_em: 2026-06-27
tags: [pesquisa-de-precos, executar, roteiro, pncp, art-23, portaria-03-2024, cesta-de-precos]
---

# Roteiro — Executar Pesquisa de Preços

Roteiro operacional do Charles para a função **"executar_pesquisa_de_precos"**: instruir,
de forma rastreável e crítica, a estimativa de valor de uma contratação da Câmara Municipal
de Itanhandu, e preencher a **minuta-mãe oficial** de Pesquisa de Preços.

> **Comando de uso (linguagem natural):**
> "Charles, execute pesquisa de preços para o objeto: {{OBJETO}}, quantidade {{QUANTIDADE}},
> unidade {{UNIDADE}}, usando PNCP e fontes oficiais externas, e preencha a minuta-mãe de
> Pesquisa de Preços."

---

## Regra principal (inegociável)

O Charles **não cria** modelo novo de Pesquisa de Preços. Usa **exclusivamente** a minuta-mãe
oficial `05_minutas/PESQUISA_DE_PRECOS/PESQUISA_PRECOS_MINUTA_MAE.docx`, preenchendo apenas os
campos `{{...}}` e marcando as opções `(  )`. Estrutura, ordem, timbre, cabeçalho, rodapé e
assinaturas são preservados. Se a minuta não existir ou estiver inadequada, **pare e avise**
(ver §9).

---

## Fundamento na base (citar sempre a fonte)

- **Lei 14.133/2021, art. 23** e §§ — parâmetros da estimativa
  (`01_legislacao/lei-14133-2021-licitacoes-contratos-administrativos.md`).
- **Lei 14.133/2021, art. 72, II** — contratação direta instruída com estimativa na forma do art. 23.
- **Portaria 03/2024 da Câmara** (transcrita em
  `02_normas_internas/regulamento-licitacoes-camara-itanhandu.md`):
  - art. 2º — conteúdo mínimo do documento (8 incisos);
  - art. 3º — condições comerciais a observar (frete, garantia, prazo, marca/modelo…);
  - art. 4º — parâmetros (I PNCP/painel; II contratações similares; III mídia/sites; IV pesquisa
    direta ≥3; V NF-e), com **prioridade dos incisos I e II** (§1º) e requisitos da pesquisa
    direta (§2º);
  - art. 5º — métodos (média/mediana/menor), **mínimo de 3 preços**, exclusão fundamentada de
    inexequíveis/inconsistentes/excessivos (§4º), <3 só com aprovação do Presidente (§7º);
  - art. 6º — contratação direta; **estimativa concomitante** na dispensa art. 75, I e II (§4º);
  - art. 8º — orçamento sigiloso quando justificado.
- **Ficha de uso da minuta** — `05_minutas/PESQUISA_DE_PRECOS/PESQUISA_PRECOS_FICHA_DE_USO.md`
  (campos variáveis e o que não alterar).
- Apoio doutrinário: `04_doutrina_artigos/artigo-pesquisa-precos-concomitante-dispensa-eletronica.md`.
- Regras de comparabilidade, tratamento de valores e segurança jurídica:
  `07_checklists/regras-pesquisa-de-precos.md`.

---

## Fluxo (13 passos)

1. **Ler a normativa interna** sobre pesquisa de preços (Portaria 03/2024) e a **ficha de uso**.
2. **Ler o art. 23 da Lei 14.133/2021** e os demais dispositivos aplicáveis ao caso.
3. **Coletar os dados mínimos do processo** (ver §"Entrada"). Faltando dado essencial, pedir ao
   usuário antes de prosseguir.
4. **Identificar os critérios obrigatórios** de instrução (art. 2º da Portaria 03/2024 + art. 23):
   objeto, fontes, série de preços, método, justificativa, memória de cálculo, fornecedores.
5. **Consultar o PNCP** por contratações similares (`scripts/pncp_consulta.py` ou consulta manual
   ao portal). Registrar URL, data da consulta, órgão, modalidade, nº, data, valores e link.
6. **Pesquisar fontes complementares** em portais oficiais (`scripts/busca_web.py` gera as
   consultas; com chave de API executa a busca). Priorizar `.gov.br`, `.leg.br`, transparência,
   câmaras, prefeituras, tribunais, diários oficiais.
7. **Montar a cesta de preços** com as fontes comparáveis (`scripts/cesta_precos.py`).
8. **Normalizar os valores** (moeda BR, unitário × global) — `scripts/normalizar_precos.py`.
9. **Sinalizar** valores discrepantes, inexequíveis, antigos ou pouco comparáveis — **sem excluir
   sozinho**: a exclusão é fundamentada e registrada (art. 5º, §4º).
10. **Calcular** média, mediana e menor preço válido (mínimo 3 preços — art. 5º).
11. **Justificar a metodologia** adotada e o tratamento dos valores.
12. **Gerar o conteúdo** para preencher a minuta-mãe (campos `{{...}}` — ver §"Mapeamento").
13. **Registrar as fontes**: links, datas de acesso e justificativa de comparabilidade.

---

## Entrada (dados mínimos do processo)

Objeto; descrição detalhada; unidade de medida; quantidade estimada; categoria do objeto;
período de busca; filtros opcionais (município, estado, esfera, modalidade, dispensa,
inexigibilidade, pregão, contratação direta); valor estimado inicial (se houver); observações;
minuta-mãe a usar. Modelo: `scripts/exemplos/entrada-exemplo.json`.

---

## Ferramentas de apoio (opcionais — não obrigatórias)

Os scripts em `scripts/` automatizam a parte **mecânica** (coleta, normalização, estatística,
triagem, montagem do relatório). Funcionam **sem chave de API** (PNCP é público; a busca web cai
no modo de consultas sugeridas). Detalhes e exemplos: `scripts/README.md`.

- `pncp_consulta.py` — busca contratações similares no PNCP.
- `busca_web.py` — busca complementar (Google CSE/SerpAPI) ou gera consultas para pesquisa manual.
- `normalizar_precos.py` — moeda BR, discrepância (IQR), média/mediana/menor.
- `cesta_precos.py` — orquestra tudo e gera o relatório com os 13 blocos + textos para a minuta.

> O Charles pode operar **sem** os scripts, fazendo as consultas e o cálculo manualmente — o
> roteiro e as regras valem igual. Os scripts apenas reduzem trabalho e padronizam a rastreabilidade.

---

## Modo manual (sem internet ou sem chave de busca)

O usuário cola os resultados que encontrou (ou exporta do portal). O Charles (ou
`cesta_precos.py --manual`) extrai os dados, verifica comparabilidade, monta a cesta, calcula os
valores e preenche a minuta. Modelo de entrada: `scripts/exemplos/manual-exemplo.json`.

---

## Saída esperada (relatório estruturado)

1. Resumo da pesquisa · 2. Termos pesquisados · 3. Fontes PNCP · 4. Fontes externas ·
5. **Tabela da cesta de preços** · 6. Análise de comparabilidade · 7. Tratamento de discrepantes ·
8. Memória de cálculo · 9. Valor estimado sugerido · 10. Justificativa da metodologia ·
11. **Texto pronto para a minuta-mãe** · 12. Fontes utilizadas · 13. Alertas e ressalvas.

### Tabela mínima da cesta

| Nº | Fonte | Órgão | Objeto encontrado | Modalidade | Data | Quantidade | Unidade | Valor unitário | Valor total | Link | Comparabilidade | Situação |
| -- | ----- | ----- | ----------------- | ---------- | ---- | ---------- | ------- | -------------- | ----------- | ---- | --------------- | -------- |

**Situações:** válido · válido com ressalva · excluído por baixa comparabilidade · excluído por
ausência de valor · excluído por data antiga · excluído por especificação incompatível · excluído
por valor discrepante.

Exemplo completo de saída: `scripts/exemplos/saida-exemplo.md`.

---

## Mapeamento dos campos da minuta-mãe

| Campo `{{...}}` | De onde vem |
|---|---|
| `{{OBJETO}}` | objeto do processo |
| `{{PERIODO_PESQUISA}}` | período de busca / data da pesquisa |
| `{{SERIE_PRECOS_COLETADOS}}` | lista da cesta (bloco 5/8) |
| `{{JUSTIFICATIVA_METODOLOGIA}}` | bloco 10 + tratamento de valores (art. 5º, §4º) |
| `{{MEMORIA_CALCULO}}` | bloco 8 (operação que levou ao valor) |
| `{{JUSTIFICATIVA_FORNECEDORES}}` | só na pesquisa direta (art. 4º, §2º) |
| `{{VALOR_REFERENCIA}}` / `{{VALOR_REFERENCIA_EXTENSO}}` | valor final escolhido |
| `{{OUTRA_METODOLOGIA}}` | só se marcar "Outra" |
| `{{NUMERO_FOLHAS}}` / `{{NUMERO_FOLHAS_EXTENSO}}` | nº de folhas dos comprovantes |
| `{{DIA}}` / `{{MES}}` / `{{ANO}}` | data da assinatura |

Marcar `(  )` a metodologia (Média/Mediana/Menor/Outra) e as fontes do art. 23/art. 4º
efetivamente usadas. Lacunas que exigem decisão humana: `[PREENCHER: ...]`. **Suprimir as "Notas
Explicativas"** ao finalizar (ver ficha de uso).

---

## §9 — Quando NÃO há base suficiente

Se PNCP + fontes complementares não reunirem preços comparáveis suficientes (< 3 válidos),
**não force conclusão**. Gere relatório de insuficiência com: termos pesquisados; fontes
consultadas; resultados; motivo da insuficiência; sugestão de novas palavras-chave; sugestão de
ampliar período; sugestão de pesquisa direta (art. 4º, IV), contratações locais ou base interna;
e texto de ressalva para o processo. Escreva, quando for o caso, a frase padrão da base:
**"Não encontrei fundamento suficiente na base documental disponível"** e diga o que falta.

---

## Integração com o controle de fracionamento (CNAE)

Concluída a estimativa, antes de seguir para a contratação, rode o controle de limite por
subclasse CNAE (`07_checklists/roteiro-limite-dispensa-cnae.md`) e, ao concluir a contratação,
atualize `06_precedentes_camara/CONTROLE_CONTRATACOES.md`. A pesquisa de preços alimenta o valor
que será somado no exercício.

---

## Checklist final (antes de juntar ao processo)

- [ ] Objeto e especificação conferem com DFD/ETP/TR.
- [ ] Mínimo de 3 preços válidos (ou justificativa do art. 5º, §7º registrada).
- [ ] Priorizados os incisos I e II do art. 4º (ou justificada a impossibilidade — §1º).
- [ ] Cada fonte tem identificação, link/registro, data e (sites) data/hora de acesso.
- [ ] Exclusões fundamentadas e descritas (art. 5º, §4º).
- [ ] Método (média/mediana/menor) escolhido e justificado.
- [ ] Memória de cálculo coerente com a quantidade do processo.
- [ ] Pesquisa direta com propostas formais do art. 4º, §2º (quando usada).
- [ ] Minuta-mãe preenchida sem alterar estrutura/timbre; Notas Explicativas suprimidas.
- [ ] **Revisão humana** feita: nenhum dado inventado; ressalvas registradas.
