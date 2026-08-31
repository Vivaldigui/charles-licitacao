---
tipo: metodologia
tema: como a base é construída e mantida
fonte: projeto
vigencia: vigente
atualizado_em: 2026-08-09
tags: [metodologia, fases, reproducibilidade]
---

# Metodologia da base

## Ciclo de vida de um dado

1. **Descoberta** — onde o dado existe e como acessá-lo (Fase 1; registro em
   `00_CONTROLE/diagnostico_fontes.md`).
2. **Coleta** — download com pausa (≥0,4 s), UA identificável, `urllib`/stdlib;
   cada baixado recebe SHA-256 + registro de proveniência (URL, data, status HTTP).
3. **Quarentena** — arquivo cru vai para `99_ORIGINAIS/`; a cópia de trabalho é
   separada por tipo (`01_ATOS_NORMATIVOS/`, `03_ORIENTACOES_TCE_MG/`, etc.).
4. **Extração** — texto via `pypdf` (quando o PDF tiver camada de texto); se
   digitalizado sem OCR, registra-se `DOCUMENTO DIGITALIZADO — depende de OCR`.
5. **Catalogação** — metadados em `indice_*.json|csv` e fichas em `05_BASE_CONHECIMENTO/`.
6. **Validação** — conferência de vigência, relações de alteração (VIDE), coerência
   de números/ementas contra os arquivos; nunca de cabeça.

## Classificação de evidência

- `oficial` — baixado do órgão emissor (ex.: PDF do TCLEGIS).
- `normalizada` — derivada de material oficial (ex.: texto extraído do PDF).
- `inferência` — decorre de outra evidência e está marcada como tal (ex.: cadeia de
  alterações deduzida do campo VIDE).

## Regras rígidas

- **Anti-alucinação:** nenhum número, ementa ou relação é escrito sem arquivo de
  origem; ausência vira `não identificado / não localizado na fonte pesquisada`.
- **Legitimidade:** CAPTCHA, autenticação e limites de acesso não são contornados.
  Se algo exige ação humana, o caminho humano é documentado.
- **Original intacto:** jamais sobrescrever um arquivo-fonte; trabalhar em cópia.
- **Determinismo:** coleta idempotente (já baixado = não baixa de novo, compara
  hash).

## Fases

### Fase 1 — Reconhecimento (concluída e revalidada)
Objetivo: saber *onde* e *como* obter cada dado, com evidência verificável.
Entregas: `00_CONTROLE/diagnostico_fontes.md`, evidências canonizadas, 32 atos
normativos no índice (61 PDFs válidos), prova de conceito de download e
revalidação interativa do Portal da Transparência.

### Fase 2 — Coleta estruturada
- Serializar busca no TCLEGIS por assunto (campo `termos`) para a agenda completa
  de contratação direta (ETP, TR, DFD, pesquisa de preços, parecer, registro de
  preços, sanções, bens comuns/luxo).
- Para processos (dispensas/inexigibilidades concretas): o Portal da Transparência
  está acessível em navegador, mas a API direta retorna HTTP 401; o Compras MG
  continua exigindo hCaptcha. Em 2026-08-09, a interface oficial exportou 210
  registros com os filtros SIAD + Lei 14.133/21 + Compra direta; o XLSX foi
  adotado como fonte de ingestão porque o CSV oficial não escapa corretamente
  vírgulas e quebras de linha. A pesquisa humana assistida no Compras MG observou
  201 itens no filtro equivalente, sem contornar controles de acesso.

### Fase 3 — Catalogação
- O primeiro catálogo está em `03_INDICES/processos_candidatos.csv|json`, com 210
  registros, identificadores normalizados e URLs de consulta por órgão 1020,
  número e ano. Pares número/ano repetidos recebem sufixo de hash calculado sobre
  campos oficiais; isso evita colisão sem afirmar que sejam duplicatas.
- Antes da promoção para `03_INDICES/processos.*`, reconciliar a contagem 210 × 201,
  recuperar o id interno/unidade de compra e executar a coleta piloto documental.
- Fichas padronizadas em `05_BASE_CONHECIMENTO/` (frente: resumo objetivo, tese,
  fundamentos, aplicação, trechos, riscos) — mesmo padrão das fichas do Charles.

### Fase 4 — Base de conhecimento reutilizável
- Índice único (`BASE_CONHECIMENTO.json`), ligações entre atos (grafo de
  alterações) e material pronto para leitura pelo Charles sem risco de
  alucinação (toda afirmação aponta o arquivo-fonte).
