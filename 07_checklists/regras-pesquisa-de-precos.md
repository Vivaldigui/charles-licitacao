---
tipo: checklist
tema: pesquisa de precos
fonte: base Charles / Lei 14.133/2021 art. 23 / Portaria 03/2024 da Câmara de Itanhandu
vigencia: vigente
atualizado_em: 2026-06-27
tags: [pesquisa-de-precos, regras, comparabilidade, seguranca-juridica, antialucinacao]
---

# Regras — Pesquisa de Preços (comparabilidade, tratamento de valores e segurança jurídica)

Regras de conduta que o Charles aplica ao executar a pesquisa de preços. Complementa o
`roteiro-executar-pesquisa-de-precos.md`. Fonte normativa: art. 23 da Lei 14.133/2021 e
Portaria 03/2024 da Câmara (em `02_normas_internas/regulamento-licitacoes-camara-itanhandu.md`).

---

## 1. Critérios de comparabilidade (art. 3º da Portaria 03/2024)

Antes de incluir um preço na cesta, confirmar a similaridade com o objeto da Câmara quanto a:

- descrição e **especificações técnicas** do objeto;
- **unidade de medida** e **quantidade** (economia de escala);
- **localidade** e peculiaridades do local de execução;
- **data** da contratação (atualidade — ver §3);
- **modalidade** e condições de fornecimento;
- prazo de execução/entrega;
- se inclui **frete, instalação, suporte, garantia** ou outros custos;
- se o preço é **unitário ou global**;
- se a contratação é **realmente** similar (não basta o nome do objeto).

Item sem aderência ao objeto → situação "excluído por baixa comparabilidade" ou "excluído por
especificação incompatível", **com justificativa**.

Graus de confiabilidade da fonte (triagem): **alto** (portais oficiais `.gov.br`/`.leg.br`/
`.jus.br`, PNCP, Painel de Preços, transparência), **médio** (mídia especializada com data/hora),
**baixo** (sites comerciais genéricos, marketplaces, blogs). A confiabilidade alta **não dispensa**
a análise de comparabilidade; a baixa exige justificativa expressa e normalmente não serve como
fonte principal.

---

## 2. Tratamento de valores

- Converter moeda BR para número (R$ 1.234,56 → 1234.56); valor ausente/ilegível → **sem valor**
  (não é zero, não se inventa).
- Separar **valor unitário** e **valor total**; recalcular o unitário quando houver quantidade e
  valor global. Atenção: o `valor_global` do PNCP é o **total da contratação**, não o preço
  unitário — só vira unitário se houver quantidade confiável.
- Marcar a fonte como **inválida** quando não for possível identificar valor seguro.
- **Discrepantes:** destacar preços muito distantes da amostra (o script usa IQR como triagem).
  A **exclusão** depende de critério fundamentado descrito nos autos (art. 5º, §4º). Não excluir
  automaticamente.
- **Inexequível** (art. 5º, §5º): preço que não cobre custo/lucro do fornecedor — presunção
  justificada após notificação sem resposta.
- **Inconsistente** (art. 5º, §6º): proposta que não atende às especificações exigidas.
- **Excessivamente elevado:** sobrepreço frente aos referenciais (art. 1º, II).
- **Cálculo:** média simples, mediana e menor preço sobre o conjunto **válido**; mínimo de **3**
  preços (art. 5º). Menos de 3 só com justificativa **aprovada pelo Presidente** (art. 5º, §7º).
- Acréscimo para atratividade limitado a **20%** mediante justificativa (art. 5º, §2º); redução
  da média quando os preços estiverem acima do mercado (art. 5º, §3º).
- **Sugerir** metodologia conforme os dados (mediana é mais robusta a extremos); a escolha final
  é do agente.

---

## 3. Atualidade dos preços

- Contratações similares: período de **1 ano** anterior à pesquisa (art. 4º, II).
- Sites/mídia especializada: até **6 meses** e **com data e hora de acesso** (art. 4º, III).
- Pesquisa direta: orçamentos com até **6 meses** (art. 4º, IV).
- Fora do prazo: só **excepcionalmente**, justificado, com índice de atualização (art. 4º, §3º).
- Preço antigo sem atualização → situação "excluído por data antiga" ou ressalva expressa.

---

## 4. Segurança jurídica (anti-alucinação)

O Charles **NÃO**:

1. inventa fundamento legal, artigo, inciso ou súmula;
2. inventa número de contratação;
3. inventa preço;
4. inventa órgão público;
5. inventa link;
6. usa fonte sem identificação mínima;
7. declara a pesquisa "completa" quando as fontes são frágeis ou insuficientes;
8. mistura dado encontrado, cálculo feito e interpretação — **separar sempre** os três;
9. deixa de alertar quando a pesquisa exige **validação humana**;
10. deixa de alertar quando uma fonte **não é plenamente comparável**.

Toda afirmação jurídica indica **arquivo + dispositivo**. Sem base suficiente, escrever:
**"Não encontrei fundamento suficiente na base documental disponível"** e dizer o que falta.

---

## 5. Insuficiência de dados (não forçar conclusão)

Quando a cesta não reunir preços comparáveis suficientes, gerar relatório de insuficiência
(ver §9 do roteiro): termos pesquisados, fontes consultadas, resultados, motivo, sugestões de
novas palavras-chave, de ampliar período e de pesquisa direta/base interna, e **texto de ressalva**
para o processo — sem fixar valor artificial.

---

## 6. Checklist de validação humana

Antes de o documento ir ao processo, um servidor responsável deve confirmar:

- [ ] As fontes existem e os links abrem (não há link inventado).
- [ ] Os preços conferem com os comprovantes anexados.
- [ ] As exclusões estão justificadas e descritas.
- [ ] O método e o valor final estão corretos e motivados.
- [ ] A comparabilidade de cada item foi efetivamente analisada.
- [ ] A pesquisa direta (se houver) traz propostas formais do art. 4º, §2º.
- [ ] Os campos `[PREENCHER: ...]` foram resolvidos.
- [ ] O documento usa a minuta-mãe oficial, sem alteração de estrutura/timbre.

> A pesquisa de preços é **apoio à decisão**. Não substitui o agente de contratação, a autoridade
> competente nem a assessoria jurídica.
