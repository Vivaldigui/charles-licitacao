"""
Gestão Documental dos Processos em Andamento — Charles / Câmara de Itanhandu.

Mantém a pasta de cada processo com **um arquivo de trabalho por tipo
documental**, sem perder versão nenhuma: o que sai da área corrente vai para
`90_HISTORICO/` com número de versão, carimbo de tempo, hash e motivo.

O módulo cuida de cinco coisas:

* **área corrente limpa** — `DFD.docx`, `ETP.docx`, `TR.docx`, e nunca
  `TR_final_2.docx`;
* **histórico controlado** — versões anteriores preservadas e rastreáveis;
* **documentos externos** — proposta, certidão e e-mail passam por quarentena,
  são classificados e ficam separados do que o Charles gerou;
* **registro estruturado** — `PROCESSO.json`, `DOCUMENTOS.json` e o log
  `LOG_DOCUMENTAL.jsonl`, que só cresce;
* **segurança** — processo real mora em `CHARLES_PROCESSOS_DIR`, fora do
  repositório público.

Toda gravação passa por `registrar_documento.registrar_saida_gerada`: nenhum
gerador escolhe sozinho onde salvar. Documento assinado ou publicado é
imutável; geração idêntica à vigente não cria versão; falha no meio desfaz a
operação inteira e preserva o documento anterior.

Só biblioteca padrão. Linha de comando:

    python scripts/gestao_documental/iniciar_processo.py --numero "PA 031/2026" \
        --objeto "Aquisição de material de limpeza"
    python scripts/gestao_documental/registrar_documento.py --processo PA_031_2026 \
        --tipo TR --arquivo saida/TR_gerado.docx --motivo "Primeira geração"
    python scripts/gestao_documental/validar_processo.py --processo PA_031_2026
"""

__all__ = [
    "hashes",
    "locks",
    "transacoes",
    "nomes_arquivos",
    "manifesto",
    "seguranca_repositorio",
    "iniciar_processo",
    "registrar_documento",
    "substituir_documento",
    "promover_documento",
    "arquivar_versao",
    "restaurar_versao",
    "importar_documento_externo",
    "classificar_documento",
    "detectar_duplicados",
    "migrar_processo",
    "limpar_temporarios",
    "gerar_painel",
    "validar_processo",
]

__version__ = "1.0.0"
