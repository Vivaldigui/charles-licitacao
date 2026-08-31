---
tipo: precedente
hierarquia: operacional
tema: mapa de precedentes cnae
fonte: base Charles / contratações anteriores da Câmara Municipal de Itanhandu
vigencia: vigente
atualizado_em: 2026-07-31
tags: [cnae, precedentes, controle, dispensa, fracionamento]
---

# CNAE — precedentes internos por objeto típico

Mapa operacional para consultar, antes de nova contratação, se a Câmara já adotou uma subclasse
CNAE para objeto similar.

## Como usar

1. Consulte este mapa antes de pesquisar no IBGE/CONCLA.
2. Se houver precedente compatível, confira se o objeto atual é realmente do mesmo ramo de
   atividade.
3. Se não houver precedente, consulte a ferramenta oficial do IBGE/CONCLA.
4. Nunca invente código CNAE.
5. Registre sempre o código e a denominação oficial da subclasse.
6. Em caso de dúvida, marque `[VALIDAÇÃO HUMANA]` e não conclua sozinho o enquadramento.

> **Origem deste mapa.** Montado em 2026-07-31 a partir dos 25 processos concluídos do exercício
> 2026 (`08_processos_em_andamento/2026/CONCLUIDOS`), cruzando o objeto homologado, o fundamento
> legal registrado no SICOM e o Cartão CNPJ do fornecedor, quando juntado aos autos. As
> denominações vêm da **API oficial do IBGE** (CNAE-Subclasses 2.3). A CNAE **não é campo do
> SICOM** nem dos documentos do processo — por isso a coluna "Evidência" importa.

## Objeto típico × subclasse CNAE já adotada

### Confirmados por Cartão CNPJ do fornecedor

| Objeto típico | CNAE subclasse | Denominação oficial | Processo de referência | Observação |
|---|---|---|---|---|
| Locação de veículo por diária, sem condutor | 7711-0/00 | Locação de automóveis sem condutor | PA 002/2026 | Atividade **principal** do fornecedor. Precedente sólido. |
| Gêneros alimentícios, higiene, limpeza, descartáveis, água e GLP | 4712-1/00 | Comércio varejista de mercadorias em geral, com predominância de produtos alimentícios — minimercados, mercearias e armazéns | PA 006/2026 | Principal dos **dois** fornecedores. Objeto misto tratado como ramo único de mercearia. |
| Auditoria contábil e financeira | 6920-6/02 | Atividades de consultoria e auditoria contábil e tributária | PA 003/2026 | Atividade **principal** do fornecedor. |
| Inscrição em curso de capacitação para agentes públicos | 8599-6/04 | Treinamento em desenvolvimento profissional e gerencial | PA 004, 007, 008, 017, 022, 025/2026 | Principal do INSTITUTO GLOBAL. Ramo mais recorrente da Câmara. |
| Recarga e manutenção de extintores de incêndio | 3314-7/10 | Manutenção e reparação de máquinas e equipamentos para uso geral não especificados anteriormente | PA 023/2026 | Atividade **secundária** do fornecedor (principal é 4789-0/99). |

### Propostos pelo Charles — dependem de validação humana

| Objeto típico | CNAE subclasse | Denominação oficial | Processo de referência | Observação |
|---|---|---|---|---|
| Equipamentos e suprimentos de informática, áudio, vídeo e rede | 4751-2/01 | Comércio varejista especializado de equipamentos e suprimentos de informática | PA 011, 013, 016, 019/2026 | **[VALIDAÇÃO HUMANA]** — sem Cartão CNPJ na base. **Subclasse mais crítica do exercício: 83,4% do limite.** Ver alerta em [[CONTROLE_CONTRATACOES]]. |
| Material de expediente / papelaria | 4761-0/03 | Comércio varejista de artigos de papelaria | PA 005, 015/2026 | **[VALIDAÇÃO HUMANA]** — no PA 015 a principal do fornecedor é 4763-6/01 (brinquedos), divergente do objeto. |
| Certificado digital (e-CPF / e-CNPJ, ICP-Brasil) | 4751-2/01 | Comércio varejista especializado de equipamentos e suprimentos de informática | PA 001/2026 | **[VALIDAÇÃO HUMANA]** — alternativa defensável e talvez melhor: **6209-1/00** (suporte técnico, manutenção e outros serviços em TI), que é secundária do fornecedor. Decidir antes de reusar como precedente. |
| Placas de homenagem em metal | 3299-0/03 | Fabricação de letras, letreiros e placas de qualquer material, exceto luminosos | PA 010/2026 | **[VALIDAÇÃO HUMANA]** — principal do fornecedor é 7312-2/00, divergente do objeto. |
| Claraboia — aquisição com instalação | 4743-1/00 | Comércio varejista de vidros | PA 020/2026 | **[VALIDAÇÃO HUMANA]** — objeto inclui instalação; avaliar se atrai o art. 75, **I** (serviço de engenharia) e, no enquadramento como obra, subclasse da divisão 43. |
| Perícia técnica (áudio) | 7120-1/00 | Testes e análises técnicas | PA 024/2026 | **[VALIDAÇÃO HUMANA]** — sem Cartão CNPJ na base. Alternativa: 7112-0/00, se o laudo for de natureza predominantemente de engenharia. |
| Licenciamento de uso de software | 6203-1/00 | Desenvolvimento e licenciamento de programas de computador não customizáveis | PA 012/2026 | **[VALIDAÇÃO HUMANA]** — se o software for customizado para a Câmara, a subclasse correta é **6202-3/00**. Inexigibilidade (art. 74, I): não conta para o limite. |
| Consultoria e assessoria jurídica | 6911-7/01 | Serviços advocatícios | PA 018/2026 | **[VALIDAÇÃO HUMANA]** — sem Cartão CNPJ na base. Inexigibilidade (art. 74, III, c): não conta para o limite. |

## Cuidados ao reutilizar este mapa

- Subclasse adotada em precedente **não vincula** objeto diferente. Reconfira o ramo.
- Inexigibilidade (art. 74) e dispensas que não são por valor **não** entram na aferição dos
  limites do art. 75, I e II — mas continuam registradas no controle.
- Antes de abrir processo em ramo já usado no exercício, rode
  `python scripts/controle_cnae.py simular` para ver o saldo.

**FONTES:**
- `06_precedentes_camara/CONTROLE_CONTRATACOES.md` | registro do exercício 2026 | vigente | 2026-07-31
- `07_checklists/roteiro-limite-dispensa-cnae.md` | itens 2 e 3 | vigente | 2026-07-31
- `02_normas_internas/regulamento-licitacoes-camara-itanhandu.md` | Portaria 06/2024, art. 2º, §2º | vigente | 2026-07-31
- IBGE/CONCLA — API oficial de subclasses CNAE 2.3 | consulta em 2026-07-31
