---
tipo: checklist
hierarquia: operacional
tema: modo auditor de contratacoes diretas
fonte: base Charles / jurisprudencia local TCE-MG / protocolo de auditoria preventiva
vigencia: vigente
atualizado_em: 2026-07-31
tags: [modo-auditor, contratacao-direta, tce-mg, riscos, auditoria-preventiva]
---

# Roteiro — Modo Auditor de Contratações Diretas

Use quando o usuário pedir: “Charles, ative o Modo Auditor”, “audite este processo de contratação
direta”, “analise como auditor do TCE-MG”, “verifique indícios de irregularidade” ou “compare com a
jurisprudência do TCE-MG”.

O Modo Auditor é apoio técnico e auditoria preventiva. Não substitui controle interno, assessoria
jurídica, autoridade competente, Tribunal de Contas nem validação humana.

## 1. Pré-condições

1. Ler `CLAUDE.md`, este roteiro e `07_checklists/esteira-contratacao-direta.md`.
2. Inventariar os arquivos antes de afirmar presença ou ausência.
3. Ler a legislação e as normas internas aplicáveis na base; conferir vigência/frontmatter.
4. Preparar o pacote jurisprudencial:

```bash
python -m scripts.auditor_tcemg preparar-auditoria \
  --processo CAMINHO_DO_PROCESSO \
  --saida CAMINHO_DO_PROCESSO/CONTEXTO_JURISPRUDENCIAL_AUDITORIA.md
```

5. Citar no relatório apenas jurisprudência contida no pacote e cuja página tenha sido lida.

## 2. Etapa 1 — Inventário documental

Classificar cada peça como: **presente**, **ausente**, **aparentemente dispensável**, **ilegível**,
**incompleta** ou **necessidade de diligência**. Ausência não equivale automaticamente a irregularidade.

Verificar, conforme o caso: DFD; ETP ou justificativa de dispensa; TR; pesquisa de preços; mapa
comparativo; propostas; justificativa do preço; razão da escolha; habilitação; manifestação jurídica;
autorização; aviso; publicidade; homologação/ratificação; contrato ou equivalente; empenho; fiscal;
execução; notas fiscais; liquidação; pagamento; aditivos e demais peças pertinentes.

## 3. Etapa 2 — Delimitação do caso

Identificar sem presumir: objeto; valor; exercício; fundamento; regime jurídico; fase; fornecedor;
forma de seleção; urgência; disputa; aviso; metodologia de pesquisa; contrato/equivalente; unidade
gestora e subclasse CNAE quando houver dispensa por valor.

## 4. Etapa 3 — Critérios

Cruzar, na ordem de hierarquia do `CLAUDE.md`: legislação existente na base; normas
regulamentadoras; Regulamento e normas internas; jurisprudência vinculante; jurisprudência
persuasiva pertinente, com atenção ao TCE-MG; doutrina apenas como apoio; precedentes internos; e
documentos do caso.

Norma diz literalmente e interpretação do Charles aparecem separadas. Toda afirmação jurídica traz
arquivo + dispositivo; toda evidência do processo traz documento + página/folha.

## 5. Etapa 4 — Achados

Cada achado contém: ID (`AUD-001` em diante), título, área/fase, classificação, condição, critério,
evidências, causa provável somente quando demonstrável, risco/efeito, jurisprudência, agravantes,
atenuantes, documentos faltantes, diligência, recomendação e nível de confiança.

Classificações permitidas: **ponto positivo**, **oportunidade de melhoria**, **alerta**, **possível
irregularidade**, **indício relevante de irregularidade**, **irregularidade documental aparente**,
**insuficiência de evidências**, **matéria que exige análise jurídica**, **matéria que exige decisão
da autoridade**. Não usar “irregularidade comprovada” sem documentação suficiente e fundamento inequívoco.

## 6. Etapa 5 — Gravidade

Valores: **crítica**, **alta**, **média**, **baixa**, **informativa** ou **indeterminada**.

Motivar por impacto financeiro, competitividade, direcionamento, sobrepreço, motivação, publicidade,
planejamento, possibilidade/estágio de correção, dano efetivo ou potencial, recorrência e justificativa
plausível. Quantidade de documentos ausentes, isoladamente, não define gravidade.

## 7. Etapa 6 — Contraditório analítico

Antes de concluir, apresentar: elementos que indicam irregularidade; elementos que afastam/reduzem o
risco; justificativas da Administração; documentos saneadores; jurisprudência favorável e
desfavorável; divergências; e limitações.

## 8. Etapa 7 — Regime jurídico e tempo

Para cada precedente: legislação do caso, dispositivo atual existente na base, fundamentos que
permanecem, pontos não transplantáveis e motivo da pertinência. Classificar aplicação como:
**diretamente aplicável**, **por identidade de princípio**, **com adaptações**, **apenas histórico**,
**incompatível com o regime atual** ou **incerta**.

Julgado da Lei nº 8.666/1993 não é aplicado automaticamente à Lei nº 14.133/2021. Não afirmar
vigência/superação sem verificar a base.

## 9. Etapa 8 — Conclusão

Conclusões permitidas: **aparentemente regular**, **regular com recomendações**, **regular com
ressalvas**, **falhas sanáveis**, **indícios de irregularidade**, **risco elevado que recomenda
suspensão ou correção antes do prosseguimento**, **documentação insuficiente para concluir**.

Não concluir automaticamente por nulidade. Suspensão exige risco concreto, evidenciado e motivado.

## 10. Regras anti-alucinação

1. Nunca inventar processo, acórdão, consulta, decisão, relator ou página.
2. Nunca citar julgado não recuperado e lido.
3. Nunca usar nome do arquivo como prova do conteúdo.
4. Nunca confundir unidade técnica com decisão.
5. Nunca confundir voto vencido com entendimento vencedor.
6. Nunca substituir inteiro teor disponível por ementa.
7. Nunca generalizar decisão dependente de fatos peculiares.
8. Nunca omitir divergência relevante.
9. Nunca chamar precedente persuasivo de vinculante.
10. Nunca aplicar retroativamente exigência posterior.
11. Nunca presumir ausência sem inventário.
12. Nunca afirmar dano ao erário sem evidência.
13. Nunca afirmar direcionamento só por fornecedor conhecido.
14. Nunca afirmar sobrepreço só por aumento nominal.
15. Nunca considerar uma proposta automaticamente irregular.
16. Nunca considerar ausência de aviso automaticamente irregular sem fundamento, norma e motivação.
17. Nunca validar emergência apenas pela palavra “urgente”.
18. Sempre diferenciar falha formal, risco, indício e irregularidade demonstrada.
19. Sempre indicar o que falta para elevar a segurança.
20. Se a base for insuficiente, escrever exatamente: **“Não encontrei fundamento suficiente na
base documental disponível”** e indicar o documento/fonte faltante.

## 11. Testes de raciocínio obrigatórios

- **Aumento de preço:** comparar quantidade, unidade, escopo, período, reajuste, mercado e método;
  não concluir sobrepreço automaticamente.
- **Uma proposta:** examinar tentativas, preço, comparabilidade e norma interna; não concluir
  irregularidade automaticamente.
- **Supressão do aviso:** verificar fundamento, norma interna, urgência e motivação; rejeitar
  justificativa genérica.
- **Fracionamento:** exercício, unidade gestora, objetos de mesma natureza/ramo, CNAE, planejamento,
  somatório e jurisprudência.
- **Emergência:** fato, imprevisibilidade, demora, extensão, prazo, limite ao necessário e urgência fabricada.
- **Inexigibilidade:** inviabilidade, exclusividade/notória especialização quando pertinente,
  justificativa do preço e comprovação.
- **Documento incompleto:** não inventar; classificar insuficiência, diligenciar e limitar conclusão.

## 12. Formato do relatório

```markdown
# RELATÓRIO DE AUDITORIA PREVENTIVA
## 1. Identificação do processo
## 2. Objeto e fundamento da contratação
## 3. Escopo da auditoria
## 4. Documentos analisados
## 5. Documentos ausentes, incompletos ou ilegíveis
## 6. Legislação e normas internas aplicáveis
## 7. Jurisprudência selecionada
## 8. Síntese executiva
## 9. Pontos positivos
## 10. Achados de auditoria

### ACHADO AUD-001 — Título
**Classificação:**
**Gravidade:**
**Nível de confiança:**
**Condição encontrada:**
**Critério:**
**Evidências:**
**Jurisprudência relacionada:**
**Causa provável:**
**Risco ou efeito:**
**Fatores atenuantes:**
**Documentos necessários:**
**Recomendação:**

## 11. Matriz consolidada de riscos
## 12. Possíveis diligências
## 13. Argumentos favoráveis à regularidade
## 14. Argumentos indicativos de irregularidade
## 15. Conclusão
## 16. Limitações da análise
## 17. Fontes efetivamente utilizadas
## 18. Validação humana necessária
```

Cada jurisprudência contém processo, órgão julgador, data, arquivo, página, trecho/síntese,
pertinência e compatibilidade com o regime. Ao final de resposta jurídica, manter o bloco `FONTES:`
do `CLAUDE.md`.

## 13. Validação final

- [ ] Inventário concluído antes de registrar ausências.
- [ ] Critérios jurídicos conferidos nos arquivos-fonte.
- [ ] Jurisprudência consta do pacote e foi lida nas páginas citadas.
- [ ] Regime jurídico/tempo comparados.
- [ ] Elementos favoráveis e desfavoráveis apresentados.
- [ ] Gravidade motivada pelo risco, não pela contagem de documentos.
- [ ] Diligências indicam o que pode sanar cada dúvida.
- [ ] Limitações e validação humana estão expressas.
- [ ] Nenhuma conclusão automática de nulidade, dano, direcionamento ou sobrepreço.
