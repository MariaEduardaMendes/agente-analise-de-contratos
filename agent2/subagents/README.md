# Subagentes do Agente 2 (Avaliador de Conformidade e Risco)

Este diretório contém a especificação formal e arquitetura dos subagentes especializados que operam sob governança do Agente 2.

---

## 1. Subagente: `auditor-clausulas-penais`
- **Arquivo de Especificação:** [`especialista_clausulas_penais.md`](./especialista_clausulas_penais.md)
- **Implementação Python:** [`../subagente_penalidades.py`](../subagente_penalidades.py)
- **Papel (*Role*):** Especialista Jurídico em Cláusulas Penais e Limitação de Responsabilidade
- **Ferramentas (*Tools*):** `auditar_parametros_contratuais`
- **Contrato de Saída:** `ItemAuditoria` (Pydantic v2)

---

## 2. Justificativa Técnica do Isolamento de Contexto

A decisão de isolar a auditoria de cláusulas penais em um subagente independente é fundamentada em:

### A. Especialização Regulatória e Redução de Viés Comercial
A avaliação de penalidades rescisórias e multas compensatórias requer o confronto estrito contra a jurisprudência civil (ex: Art. 412 e 413 do Código Civil Brasileiro) e a diretriz interna de riscos corporativos (teto de 10%).
Ao isolar o subagente, impedimos que o modelo geral de auditoria "compense" ou justifique uma multa abusiva (ex: 20%) simplesmente porque o valor global ou o prazo do contrato parecem atrativos do ponto de vista do negócio. O subagente avalia a cláusula penal sob critérios estritamente jurídicos e de solvência.

### B. Modularidade de Análise para Aditivos Contratuais
Em fluxos de renegociação contratual e aditivos bilaterais, frequentemente apenas a cláusula rescisória é alterada. Com o subagente isolado, o sistema pode auditar e emitir o parecer pontual de risco da penalidade sem incorrer no custo de reavaliar todo o contrato no n8n.

### C. Saída Tipada Modular (`ItemAuditoria`)
O subagente devolve um único objeto tipado e validado (`ItemAuditoria`), permitindo que o Agente 2 agregue as conclusões de múltiplos subagentes especialistas antes de compor o relatório executivo final (`RelatorioConformidade`).

