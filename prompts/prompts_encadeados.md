# Documentação dos Prompts Encadeados e Outputs Intermediários

Este documento consolida a sequência de prompts estruturados para a técnica de **Prompt Chaining** combinada com **Least-to-Most Prompting** e **Chain-of-Thought (CoT)**, detalhando os inputs e outputs intermediários de cada etapa do pipeline de extração e sanitização do **Agente 1 (Extrator Enriquecido)**.

---

## 🏗️ Visão Geral do Encadeamento

```
[Texto Bruto da Minuta Contratual]
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│ ETAPA 1: Decomposição Estrutural (Least-to-Most)       │
└────────────────────────────────────────────────────────┘
                 │
                 ▼ Output Intermediário 1 (5 Seções Atômicas Isoladas)
┌────────────────────────────────────────────────────────┐
│ ETAPA 2: Resolução Factual & Tools com CoT             │
└────────────────────────────────────────────────────────┘
                 │
                 ▼ Output Intermediário 2 (Raciocínio Passo a Passo e Retorno das Tools)
┌────────────────────────────────────────────────────────┐
│ ETAPA 3: Síntese Estruturada e Emissão Tipada          │
└────────────────────────────────────────────────────────┘
                 │
                 ▼ Output Final Consolidado (DadosContratoExtraido para o Agente 2)
```

---

## 🔹 ETAPA 1: Decomposição Estrutural (Least-to-Most Prompting)

### Objetivo
Isolar as partes fundamentais da minuta sem emitir juízos de conformidade jurídica prematuros, fatiando o documento em 5 seções atômicas: Preâmbulo/Qualificação, Objeto, Condições Financeiras, Prazos/Vigência e Penalidades/Rescisão.

### Prompt da Etapa 1
```text
Você é o Agente 1 (Extrator Enriquecido), especialista na técnica de Least-to-Most Prompting.
Sua tarefa é DECOMPOR o contrato complexo em suas unidades fundamentais mais simples, isolando estritamente 5 blocos:
1. PREAMBULO_QUALIFICACAO: identificação das partes e CNPJs.
2. OBJETO_CONTRATUAL: descrição concisa do escopo dos serviços.
3. CONDICOES_FINANCEIRAS: valor total, parcelamento e condições de liquidação.
4. PRAZOS_E_VIGENCIA: data base de início, prazo em meses e aviso prévio.
5. PENALIDADES_E_RESCISAO: percentual da multa rescisória, base de cálculo e gatilhos.

NÃO faça julgamentos de risco jurídico nesta etapa. Apenas isole, decomponha e normalize os parâmetros.
```

### Output Intermediário 1 ([`output_etapa1_decomposicao.json`](output_etapa1_decomposicao.json))
```json
{
  "titulo_documento": "Contrato de Prestação de Serviços de Desenvolvimento de Inteligência Artificial",
  "total_secoes_identificadas": 5,
  "secoes": [
    {
      "secao": "PREAMBULO_QUALIFICACAO",
      "texto_original_relevante": "EMPRESA CONTRATANTE S.A., CNPJ 98.765.432/0001-10... e TECHSOLUTIONS LTDA., CNPJ 12.345.678/0001-90",
      "entidades_brutas_identificadas": {
        "contratante_raw": "EMPRESA CONTRATANTE S.A.",
        "cnpj_contratante_raw": "98.765.432/0001-10",
        "contratada_raw": "TECHSOLUTIONS LTDA.",
        "cnpj_contratada_raw": "12.345.678/0001-90"
      }
    },
    {
      "secao": "CONDICOES_FINANCEIRAS",
      "texto_original_relevante": "Valor total de R$ 120.000,00 a serem pagos em 12 parcelas mensais e sucessivas de R$ 10.000,00...",
      "entidades_brutas_identificadas": {
        "valor_total_citado": 120000.0,
        "parcelas_citadas": 12,
        "valor_parcela_citado": 10000.0
      }
    }
  ]
}
```

---

## 🔹 ETAPA 2: Resolução Factual e Invocação de Tools (Chain-of-Thought - CoT)

### Objetivo
Raciocinar passo a passo sobre cada dimensão para resolver ambiguidades textuais, acionando ferramentas determinísticas para garantir consistência algorítmica:
1. *Dimensão Financeira:* Compara o valor global com o valor das parcelas, invocando a ferramenta `extrair_e_validar_tabela_financeira`.
2. *Dimensão Temporal:* Cruza a data de assinatura e os meses de vigência, invocando a ferramenta `normalizar_prazos_e_datas`.
3. *Dimensão de Qualificação e Penalidades:* Valida os formatos numéricos de CNPJ e extrai os percentuais exatos da multa.

### Output Intermediário 2 ([`output_etapa2_cot.json`](output_etapa2_cot.json))
```json
{
  "resolucoes_passo_a_passo": [
    {
      "dimensao": "CONDICOES_FINANCEIRAS",
      "raciocinio_passo_a_passo": "Passo 1: Identifico o valor de R$ 120.000,00. Passo 2: Identifico 12 parcelas de R$ 10.000,00. Passo 3: Invoco a tool 'extrair_e_validar_tabela_financeira'. Passo 4: Constata-se 12 × 10.000 = 120.000 (diferença zero). Passo 5: Parâmetro financeiro normalizado.",
      "tool_invocada": "extrair_e_validar_tabela_financeira"
    },
    {
      "dimensao": "PRAZOS_E_VIGENCIA",
      "raciocinio_passo_a_passo": "Passo 1: Data de assinatura 15/01/2026. Passo 2: Duração de 12 meses. Passo 3: Invoco 'normalizar_prazos_e_datas'. Passo 4: Término computado em 2027-01-15 (365 dias corridos). Passo 5: Normalizado em padrão ISO-8601.",
      "tool_invocada": "normalizar_prazos_e_datas"
    }
  ]
}
```

---

## 🔹 ETAPA 3: Síntese Estruturada e Emissão Tipada (Pydantic v2)

### Objetivo
Agregar os dados intermediários resolvidos no modelo tipado Pydantic v2 `DadosContratoExtraido`, produzindo o contrato de dados oficial a ser entregue ao **Agente 2 (Avaliador de Risco)**.

### Output Final Consolidado ([`resultado_pipeline_raciocinio.json`](resultado_pipeline_raciocinio.json))
```json
{
  "status_extracao": "SUCESSO_VALIDADO",
  "contrato_extraido": {
    "titulo": "Contrato de Prestação de Serviços de Desenvolvimento de Inteligência Artificial",
    "contratante": {
      "nome": "Empresa Contratante S.A.",
      "cnpj_cpf": "98.765.432/0001-10",
      "papel": "CONTRATANTE"
    },
    "contratada": {
      "nome": "TechSolutions Ltda.",
      "cnpj_cpf": "12.345.678/0001-90",
      "papel": "CONTRATADA"
    },
    "objeto": "Desenvolvimento, homologação e implantação de agentes inteligentes integrados a sistemas legados.",
    "financeiro": {
      "moeda": "BRL",
      "valor_total_brl": 120000.0,
      "parcelas_quantidade": 12,
      "valor_parcela_brl": 10000.0,
      "periodicidade": "mensal",
      "soma_consistente": true,
      "discrepancia_centavos": 0.0,
      "cronograma_resumo": "12 parcelas de R$ 10,000.00 (mensal)"
    },
    "vigencia": {
      "data_inicio_iso": "2026-01-15",
      "data_fim_calculada_iso": "2027-01-15",
      "vigencia_meses": 12,
      "dias_corridos_totais": 365,
      "aviso_previo_dias": 30,
      "vigencia_formatada": "De 2026-01-15 a 2027-01-15 (12 meses / 365 dias)"
    },
    "penalidades": {
      "percentual_multa_rescisoria": 20.0,
      "base_calculo": "saldo remanescente do contrato",
      "gatilho_aplicacao": "rescisao_imotivada_sem_justa_causa"
    }
  }
}
```
