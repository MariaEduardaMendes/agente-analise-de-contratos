---
name: validacao-financeira-contratual
description: Extrai, audita e normaliza cláusulas financeiras de minutas contratuais, confrontando valor total, número de parcelas, valor unitário e calculando discrepâncias centesimais.
allowed-tools:
  - Read
  - Grep
  - Bash(python agente_extracao.py*)
version: 1.0.0
author: Agente 1 (Extrator Enriquecido de Contratos)
tags:
  - financas
  - normalizacao
  - contratos
  - pydantic
---

# Skill: Validação Financeira Contratual

Esta skill provê as diretrizes e procedimentos determinísticos para leitura, decomposição e verificação matemática de cláusulas econômico-financeiras em contratos de serviços e tecnologia.

## 1. Responsabilidade da Skill
- Identificar a moeda e o valor global expresso em algarismos e por extenso.
- Extrair o plano de parcelamento (quantidade de parcelas, valor de cada parcela, periodicidade e data de vencimento da primeira parcela).
- Invocar a ferramenta determinística `extrair_e_validar_tabela_financeira`.
- Detectar eventuais divergências de centavos e assegurar consistência matemática rigorosa antes de persistir no schema `CronogramaFinanceiro`.

## 2. Ferramenta Vinculada
- **Nome:** `extrair_e_validar_tabela_financeira`
- **Assinatura:**
  ```python
  def extrair_e_validar_tabela_financeira(
      valor_total: float,
      parcelas_qtd: int,
      valor_parcela: float,
      periodicidade: str = "mensal"
  ) -> str
  ```

## 3. Regras de Interpretação
1. **Prioridade Numérica:** Em caso de conflito textual simples, privilegie o valor explícito em moeda corrente (ex: `R$ 120.000,00`).
2. **Cálculo de Consistência:**
   $$\text{soma\_parcelas} = \text{parcelas\_qtd} \times \text{valor\_parcela}$$
   $$\text{discrepancia} = |\text{valor\_total} - \text{soma\_parcelas}|$$
   Se $\text{discrepancia} \le 0.05$, `soma_consistente = True`. Caso contrário, sinalizar inconsistência com o valor da discrepância.
3. **Periodicidade Padrão:** Na ausência de menção explícita de periodicidade, adote `"mensal"`.

## 4. Schema de Saída (JSON / Pydantic)
```json
{
  "moeda": "BRL",
  "valor_total_brl": 120000.0,
  "parcelas_quantidade": 12,
  "valor_parcela_brl": 10000.0,
  "periodicidade": "mensal",
  "soma_consistente": true,
  "discrepancia_centavos": 0.0,
  "cronograma_resumo": "12x de R$ 10.000,00 mensais"
}
```

