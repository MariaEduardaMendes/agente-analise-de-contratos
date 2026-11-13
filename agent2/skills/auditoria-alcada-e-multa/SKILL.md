---
name: auditoria-alcada-e-multa
description: Realiza a auditoria corporativa de tetos de multas rescisórias, limites de alçada gerencial vs. diretoria executiva e conformidade do cadastro de fornecedores com emissão de parecer de risco tipado.
allowed-tools:
  - Read
  - Grep
  - Bash(python agente_auditoria.py*)
version: 1.0.0
author: Agente 2 (Auditor de Risco e Conformidade)
tags:
  - governanca
  - compliance
  - auditoria
  - gestao-risco
---

# Skill: Auditoria de Alçada e Multa Rescisória

Esta skill provê as diretrizes e regras de negócio corporativas para avaliação de riscos jurídicos e limites financeiros em contratos pré-aprovados ou minutas sob análise.

## 1. Diretrizes Regulatórias e Limites de Governança
- **Teto Recomendado de Multa Rescisória:** Até **10.0%** sobre o saldo remanescente do contrato.
  - Se $\text{multa} \le 10\%$: `Status = CONFORME` e `Risco = BAIXO`.
  - Se $10\% < \text{multa} \le 20\%$: `Status = ALERTA` e `Risco = MEDIO`.
  - Se $\text{multa} > 20\%$: `Status = NAO_CONFORME` e `Risco = ALTO` (potencial cláusula abusiva segundo Art. 413 do Código Civil).
- **Limite de Alçada Gerencial:** Até **R$ 100.000,00**.
  - Acima de R$ 100.000,00: exige obrigatoriamente ratificação e assinatura formal da Diretoria Executiva (`Status = ALERTA`, `Risco = ALTO/MEDIO`).
- **Prazo Mínimo de Aviso Prévio:** Mínimo de **30 dias** corridos.
  - Abaixo de 30 dias: `Status = NAO_CONFORME`.
  - Igual a 30 dias: `Status = CONFORME` (com recomendação operacional de 45 dias para serviços críticos).

## 2. Ferramenta Vinculada
- **Nome:** `auditar_parametros_contratuais`
- **Assinatura:**
  ```python
  def auditar_parametros_contratuais(
      valor_total_brl: float,
      vigencia_meses: int,
      aviso_previo_dias: int,
      percentual_multa: float,
      situacao_fornecedor: str = "ATIVA",
      score_compliance_fornecedor: float = 90.0
  ) -> str
  ```

## 3. Diretriz para Formulação de Recomendações
Para cada item classificado como `ALERTA` ou `NAO_CONFORME`, a skill deve gerar uma ação prática de mitigação:
- Sugestão de renegociação percentual do teto rescisório.
- Encaminhamento do dossiê para deliberação da Diretoria Executiva.
- Inclusão de cláusulas de SLA e garantias contratuais compensatórias.
