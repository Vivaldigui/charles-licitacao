# Desenvolvimento do auditor TCE-MG

- Leia o `AGENTS.md` e o `CLAUDE.md` da raiz antes de alterar este pacote.
- Preserve `TCE-MG_JULGADOS/`; originais nunca são sobrescritos, movidos ou excluídos.
- Toda evidência recuperada deve manter `document_id`, caminho, página e trecho.
- Extração/classificação mecânica não é conclusão jurídica; dado ausente permanece não identificado.
- O caminho feliz deve funcionar sem embeddings, API externa ou serviço pago.
- OCR é opcional e somente para documentos comprovadamente sem texto.
- Mudança de esquema exige migração compatível ou reconstrução documentada do índice.
- Execute os testes de `99_testes/auditor_tcemg/` e uma ingestão de amostra antes do corpus inteiro.
