"""
Módulo de Padronização e Formatação Documental — Charles / Câmara Municipal de Itanhandu.

Pacote de manipulação segura de DOCX: auditoria de formatação, padronização
automática sobre cópia e revisão controlada das minutas-mãe.

Por que `docx_cmi` e não `docx`: `scripts/` entra no `sys.path` (ver
`scripts/tests/conftest.py`). Um pacote chamado `docx` ali sombrearia a
biblioteca `python-docx`, quebrando todo o módulo. `CMI` = Câmara Municipal de
Itanhandu, o mesmo prefixo dos estilos nomeados.

Entradas de linha de comando:
    python scripts/docx_cmi/auditar_docx.py  --entrada X.docx --perfil tr
    python scripts/docx_cmi/formatar_docx.py --entrada X.docx --saida Y.docx --perfil tr
"""

__all__ = [
    "util_ooxml",
    "estilos_docx",
    "numeracao_docx",
    "tabelas_docx",
    "cabecalho_rodape_docx",
    "validar_conteudo_docx",
    "relatorio_docx",
    "auditar_docx",
    "formatar_docx",
]

__version__ = "1.0.0"
