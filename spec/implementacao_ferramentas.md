# Relatório de Implementação: Ferramentas Python para Acesso a Dados Externos (TP)

Este documento registra a evolução do **Agente 1 (Extrator Enriquecido)** para um agente funcional dotado de ferramentas Python (`@function_tool`), integrando módulos de cálculo, normalização temporal e consistência financeira diretamente ao fluxo de extração e estruturação documental.

---

## 🎯 1. Objetivo da Evolução

Na primeira etapa do projeto, o agente operava de forma isolada, extraindo apenas o texto bruto do contrato via prompt básico. Contudo, em processos corporativos de extração contratual, o modelo enfrenta desafios que exigem ferramentas externas:
1. **Normalização e Resolução Temporal de Vigência:** Minutas contratuais raramente trazem a data de término de forma explícita, utilizando redações como *"vigência de 12 meses a contar da assinatura"*. O agente utiliza ferramenta especializada para calcular a data final exata em formato ISO-8601 (`YYYY-MM-DD`) e o cômputo de dias corridos.
2. **Consistência Matemática Financeira:** Cláusulas de preço trazem valores globais e cronogramas de parcelamento que necessitam de conferência algorítmica exata, garantindo que o somatório das parcelas coincide com o valor global sem divergência de centavos.
3. **Integração no Modelo de Dados Estruturado:** Os dados retornados pelas ferramentas são diretamente incorporados ao schema Pydantic v2 do contrato extraído, preparando uma base factual íntegra para o futuro Agente 2 (Avaliador de Risco).

---

## 🛠️ 2. Declaração das Ferramentas (@function_tool e Type Annotations)

As ferramentas foram implementadas no módulo [`agent/tools.py`](../agent/tools.py) utilizando o decorador `@function_tool` do **OpenAI Agents SDK** e tipagem estrita (PEP 484):

### 2.1 Ferramenta 1: `normalizar_prazos_e_datas`
- **Finalidade:** Normalização temporal da vigência contratual e cálculo de data de término no padrão internacional ISO-8601.
- **Assinatura e Tipos:**
  - `data_inicio_str: str`: Data de assinatura ou início mencionada no texto (ex: `'15/01/2026'`).
  - `meses_vigencia: int`: Prazo em meses estipulado no instrumento (ex: `12`).
  - `dias_aviso_previo: int`: Prazo formal de aviso prévio de rescisão (padrão: `30`).
- **Retorno:** JSON string contendo `data_inicio_iso`, `data_fim_calculada_iso`, `dias_corridos_totais` e `vigencia_formatada`.

### 2.2 Ferramenta 2: `extrair_e_validar_tabela_financeira`
- **Finalidade:** Decomposição do cronograma de desembolso e verificação algorítmica de integridade matemática entre valor global e parcelas.
- **Assinatura e Tipos:**
  - `valor_total: float`: Valor global expresso no contrato em Reais (ex: `120000.0`).
  - `parcelas_qtd: int`: Número total de parcelas (ex: `12`).
  - `valor_parcela: float`: Valor unitário de cada parcela (ex: `10000.0`).
  - `periodicidade: str`: Periodicidade de faturamento (padrão: `'mensal'`).
- **Retorno:** JSON string com indicação de `soma_consistente: bool`, discrepância em centavos e resumo do parcelamento.

---

## 🔄 3. Fluxo de Execução e Verificação da Invocação

Ao processar a minuta contratual em [`agent/contrato_exemplo.txt`](../agent/contrato_exemplo.txt), o fluxo do agente executa a seguinte sequência:

1. **Leitura e Extração Primária:** O modelo extrai as partes, o objeto, os valores brutos (`R$ 120.000,00` em `12 parcelas de R$ 10.000,00`) e a data inicial (`15/01/2026` por `12 meses`).
2. **Invocação da Tool Temporal:** O agente emite a chamada `normalizar_prazos_e_datas(data_inicio_str="15/01/2026", meses_vigencia=12, dias_aviso_previo=30)`.
3. **Invocação da Tool Financeira:** O agente emite a chamada `extrair_e_validar_tabela_financeira(valor_total=120000.0, parcelas_qtd=12, valor_parcela=10000.0, periodicidade="mensal")`.
4. **Execução das Funções Python:** As ferramentas processam os cálculos determinísticos e retornam os payloads JSON.
5. **Síntese Estruturada:** O modelo integra os dados retornados no modelo Pydantic v2 `DadosContratoExtraido`.

### Registro de Log do Fluxo de Execução:
```text
[EXECUÇÃO DE TOOL] >>> Invocando 'normalizar_prazos_e_datas' com data_inicio=15/01/2026, vigencia=12 meses
[EXECUÇÃO DE TOOL] <<< Retorno da normalização de prazos: {"data_inicio_iso": "2026-01-15", "data_fim_calculada_iso": "2027-01-15", "vigencia_meses": 12, "dias_corridos_totais": 365, "aviso_previo_dias": 30, "vigencia_formatada": "De 2026-01-15 a 2027-01-15 (12 meses / 365 dias)"}

[EXECUÇÃO DE TOOL] >>> Invocando 'extrair_e_validar_tabela_financeira' com valor=120000.0, parcelas=12x 10000.0
[EXECUÇÃO DE TOOL] <<< Retorno da validação financeira: {"moeda": "BRL", "valor_total_brl": 120000.0, "parcelas_quantidade": 12, "valor_parcela_brl": 10000.0, "periodicidade": "mensal", "soma_parcelas_calculada": 120000.0, "soma_consistente": true, "discrepancia_centavos": 0.0, "cronograma_resumo": "12 parcelas de R$ 10,000.00 (mensal)"}
```

---

## 📊 4. Registro Auditável das Tools (`agent/registro_execucao_tool.json`)

O arquivo [`agent/registro_execucao_tool.json`](../agent/registro_execucao_tool.json) armazena as evidências de execução:

```json
[
  {
    "ferramenta": "normalizar_prazos_e_datas",
    "input_args": {
      "data_inicio_str": "15/01/2026",
      "meses_vigencia": 12,
      "dias_aviso_previo": 30
    },
    "output_retornado": {
      "data_inicio_iso": "2026-01-15",
      "data_fim_calculada_iso": "2027-01-15",
      "vigencia_meses": 12,
      "dias_corridos_totais": 365,
      "aviso_previo_dias": 30,
      "vigencia_formatada": "De 2026-01-15 a 2027-01-15 (12 meses / 365 dias)"
    }
  },
  {
    "ferramenta": "extrair_e_validar_tabela_financeira",
    "input_args": {
      "valor_total": 120000.0,
      "parcelas_qtd": 12,
      "valor_parcela": 10000.0,
      "periodicidade": "mensal"
    },
    "output_retornado": {
      "moeda": "BRL",
      "valor_total_brl": 120000.0,
      "parcelas_quantidade": 12,
      "valor_parcela_brl": 10000.0,
      "periodicidade": "mensal",
      "soma_parcelas_calculada": 120000.0,
      "soma_consistente": true,
      "discrepancia_centavos": 0.0,
      "cronograma_resumo": "12 parcelas de R$ 10,000.00 (mensal)"
    }
  }
]
```

---

## 🎯 5. Integração na Resposta Final do Agente 1

Os retornos estruturados das duas ferramentas são injetados diretamente nos nós correspondentes do contrato extraído:
- Os dados temporais preenchem a entidade `PeriodoVigencia`, eliminando datas em formato textual ambíguo.
- Os dados de parcelamento preenchem a entidade `CronogramaFinanceiro`, com ateste de consistência matemática (`soma_consistente: true`).
- O payload gerado em [`agent/resultado_saida_tipada.json`](../agent/resultado_saida_tipada.json) atua como a interface limpa e sanitizada que será consumida pelo Agente 2 (Avaliador de Risco).
