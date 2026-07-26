---
tipo: minuta
hierarquia: oficial
documento: anexo I - documentos exigidos para habilitacao
tema: habilitacao em contratacao direta
fonte: Câmara Municipal de Itanhandu / incorporado à minuta-mãe do aviso
orgao: camara municipal de itanhandu
uso: anexo I do aviso de contratação direta
versao: 1.0
vigencia: vigente
atualizado_em: 2026-07-25
tags: [minuta, anexo, habilitacao, aviso, dispensa]
---

# Ficha de Uso — Anexo I (Documentos exigidos para habilitação)

**Não existe minuta-mãe separada do Anexo I, e não deve existir.**

O Anexo I **já está incorporado** à minuta-mãe do aviso,
[`AVISO/AVISO_CONTRATACAO_DIRETA_MINUTA_MAE.docx`](../AVISO/AVISO_CONTRATACAO_DIRETA_MINUTA_MAE.docx),
depois da assinatura do Presidente, iniciado por quebra de página e pelo título
"DOCUMENTAÇÃO EXIGIDA PARA HABILITAÇÃO" (em caixa de texto).

Criar um `ANEXO_I_HABILITACAO_MINUTA_MAE.docx` produziria **dois Anexos I** com vida
própria: a revisão de um não chegaria ao outro, e o aviso publicado passaria a exigir
documentos diferentes dos que a minuta oficial prevê. É exatamente o que a regra
"não duplicar o Anexo I" impede.

---

## 1. Como a montagem trata o Anexo I

`scripts/aviso_completo/unir_docx.py::dividir_aviso` **recorta** o Anexo I da própria
minuta do aviso, em cópia, para que ele exista também como arquivo separado no pacote de
publicação. O corte é feito no bloco do título de habilitação. Se o ponto de corte não for
reconhecido, o Anexo I permanece dentro do aviso e a montagem avisa — não corta no escuro.

---

## 2. Conteúdo atual (conferido na minuta)

Regularidade fiscal, social e trabalhista:

- inscrição no CNPJ ou CPF, conforme o caso;
- regularidade perante a Fazenda Nacional (certidão conjunta RFB/PGFN, abrangendo
  contribuições previdenciárias);
- regularidade com o FGTS;
- inexistência de débitos inadimplidos perante a Justiça do Trabalho (CNDT).

---

## 3. Habilitação proporcional

**Qualificação técnica e qualificação econômico-financeira não entram automaticamente.**
Só podem ser exigidas quando, cumulativamente:

1. previstas no Termo de Referência do processo;
2. justificadas nos autos;
3. proporcionais ao objeto;
4. autorizadas pela minuta oficial;
5. confirmadas pelo setor responsável.

A validação cruzada compara o TR com este anexo nos dois sentidos e reporta:

> DIVERGÊNCIA: o Termo de Referência prevê qualificação técnica, mas o Anexo I não
> apresenta o documento correspondente.

A divergência **não é resolvida automaticamente**: acrescentar exigência restringe a
competição e retirar exigência muda a regra do julgamento — as duas são decisão humana.

---

## 4. Alteração do conteúdo

Só por revisão expressa da minuta-mãe do aviso
(`formatar_docx.py --revisar-minuta-mae`), com backup, versionamento e changelog.
