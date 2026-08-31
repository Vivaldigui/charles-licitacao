"""
Aviso de Dispensa Completo — Charles / Câmara Municipal de Itanhandu.

Reúne, valida, numera, formata e monta em um único DOCX o Aviso de Contratação
Direta e todos os seus anexos aplicáveis, além de gerar os anexos separados e o
pacote de publicação.

O módulo NÃO redige documento: ele monta peças que já existem — as minutas-mãe
oficiais de `05_minutas/` e o Termo de Referência já elaborado para o processo.
Todo o acabamento visual é delegado ao Módulo de Padronização Documental
(`scripts/docx_cmi/`), e nenhuma minuta-mãe é gravada por este módulo.

Entradas de linha de comando:
    python scripts/aviso_completo/montar_aviso_completo.py --processo PASTA/
    python scripts/aviso_completo/validar_aviso_completo.py --processo PASTA/ \
        --somente-auditoria
"""

__all__ = [
    "ocorrencias",
    "localizar_componentes",
    "extrair_dados_tr",
    "gerar_modelo_proposta",
    "numerar_anexos",
    "unir_docx",
    "validar_aviso_completo",
    "gerar_pacote_publicacao",
    "relatorio_aviso_completo",
    "montar_aviso_completo",
]

__version__ = "1.0.0"
