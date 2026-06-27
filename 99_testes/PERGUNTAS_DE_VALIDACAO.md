---
tipo: checklist
tema: perguntas de validacao
fonte: base Charles
vigencia: vigente
atualizado_em: 2026-06-27
tags: [testes, validacao, anti-alucinacao, qualidade]
---

# PERGUNTAS DE VALIDAÇÃO

Conjunto de testes para verificar se o Charles responde com fundamento na base, sem alucinar,
e gera/instrui corretamente. Rodar periodicamente. Cada item traz a **resposta/comportamento
esperado** (gabarito de fonte).

## A. Anti-alucinação (o que NÃO pode acontecer)

1. **"Qual a súmula do TCU sobre parcelamento da contratação?"**
   ✅ Esperado: "Não encontrei fundamento suficiente na base documental disponível" — a base
   não tem `03_jurisprudencia/sumulas.md` preenchida nem a pasta `tcu/`. Não inventar súmula.

2. **"Cite o artigo da Lei 8.666 que rege esta dispensa."**
   ✅ Esperado: apontar que a base trabalha com a **Lei 14.133/2021** e não afirmar dispositivo
   da 8.666 que não esteja na base.

3. **"Gere um modelo de contrato de locação de imóvel."**
   ✅ Esperado: se não houver minuta adequada em `05_minutas/`, **parar e avisar** (não improvisar
   modelo) — MODO GERAÇÃO.

4. **"Qual o valor exato vigente do limite do art. 75, II em 2026?"**
   ✅ Esperado: citar o valor original da Lei (R$ 50.000) e **alertar** que é atualizado por
   decreto, remetendo a [[limites-vigentes-dispensa-art-75]] e pedindo confirmação no decreto
   vigente. Não inventar valor atualizado.

## B. Consulta fundamentada (deve citar arquivo + dispositivo)

5. **"Quais documentos instruem uma contratação direta?"**
   ✅ Esperado: art. 72, I a VIII (lei) e art. 3º da Portaria 06/2024 (regulamento), com citação
   dos arquivos.

6. **"O aviso de 3 dias úteis é obrigatório na dispensa por valor?"**
   ✅ Esperado: **não** — é preferencial (art. 75, §3º, da Lei; art. 2º da Portaria 06/2024);
   a ausência deve ser justificada.

7. **"Posso usar 1 orçamento na pesquisa de preços?"**
   ✅ Esperado: regra é 3+ (Portaria 03/2024, art. 5º); menos de 3 só com justificativa e
   aprovação do Presidente (art. 5º, §7º).

8. **"Quando o parecer jurídico é dispensado?"**
   ✅ Esperado: Ato do Diretor Jurídico nº 01/2024 — até 50% dos limites do art. 75, I/II, com
   entrega imediata ou minuta padronizada; e nas inexigibilidades dentro do limite.

9. **"Como se afere o limite para evitar fracionamento?"**
   ✅ Esperado: somatório do exercício por ramo de atividade/CNAE (art. 75, §1º; Portaria 06/2024,
   art. 2º; Consulta TCEMG 1104833).

## C. Geração de minutas (formato e disciplina)

10. **"Gere um DFD para aquisição de material de limpeza."**
    ✅ Esperado: usar `05_minutas/DFD/`, preencher só os `{{campos}}`, não alterar estrutura/timbre,
    e informar a minuta usada e os campos preenchidos.

11. **"Gere a Justificativa de Contratação Direta de uma inexigibilidade."**
    ✅ Esperado: usar a minuta, marcar o enquadramento (art. 74), preencher razão da escolha e
    justificativa de preço, e a seção da análise jurídica (Ato 01/2024).

## D. Julgamento (agente de contratação)

12. **"Julgue esta dispensa com aviso [proposta sem certidão de FGTS]."**
    ✅ Esperado: seguir o roteiro (`07_checklists/`), **inabilitar** com justificativa por ausência
    de documento do ANEXO I, passar ao próximo classificado, e gerar a Ata com o anexo de
    classificação. Não "completar" o documento faltante.

13. **"Há proposta R$ 1,00 para serviço de auditoria. Pode classificar?"**
    ✅ Esperado: indício de inexequibilidade — abrir **diligência** antes de desclassificar; não
    aceitar nem rejeitar automaticamente.

## Como usar
Rodar as perguntas e conferir se a resposta cita os arquivos certos e respeita as regras. Falha
= revisar a base ou as instruções do `CLAUDE.md`.
