# Relatório de Implementação: Pipelines de Raciocínio Encadeado e Decomposição de Tarefas (TP)

Este documento registra a implementação de técnicas de engenharia de prompts avançadas — **Prompt Chaining**, **Least-to-Most Prompting** e **Chain-of-Thought (CoT)** — aplicadas à tarefa complexa de extração, sanitização e resolução de ambiguidades documentais pelo **Agente 1 (Extrator Enriquecido)**.

---

## 🎯 1. Identificação da Tarefa Complexa

### 1.1 A Tarefa Escolhida
**"Extração Estruturada, Sanitização e Resolução de Ambiguidade de Minutas Contratuais"**

Nesta tarefa, o Agente 1 não pode se limitar a capturar palavras-chave superficiais; ele deve:
1. Decompor uma minuta jurídica extensa e densa em seções atômicas independentes (partes, objeto, financeiro, vigência e penalidades).
2. Resolver ambiguidades temporais (datas por extenso, prazos em meses) através do cálculo determinístico em calendário.
3. Raciocinar passo a passo sobre a consistência matemática de valores expressos em múltiplos parágrafos (valor global versus somatório de parcelas).
4. Sanitizar os dados e estruturá-los em um modelo Pydantic v2 estrito (`DadosContratoExtraido`), que servirá como entrada limpa para o Agente 2 (Avaliador de Risco).

### 1.2 Por Que um Único Prompt Falha Nesta Tarefa?
Quando a extração é solicitada em uma única instrução direta (*Zero-Shot / Single Prompt*):
- **Sobrecarga Cognitiva:** O modelo tenta simultaneamente ler texto corrido, fazer parsing de CNPJs, calcular datas de encerramento em calendário e verificar se 12 parcelas batem com o valor total.
- **Erros de Cálculo Temporal e Financeiro:** LLMs cometem alucinações matemáticas frequentes ao projetar datas em calendários ou calcular valores residuais.
- **Estruturação Deficiente:** Campos críticos acabam extraídos como strings genéricas ou formatos inconsistentes, impedindo a integração com a próxima etapa do pipeline.

---

## 🏗️ 2. Arquitetura da Solução em Etapas (Prompt Chaining)

O pipeline foi decomposto em **três etapas sequenciais**, implementadas no módulo [`agent/pipeline_raciocinio.py`](../agent/pipeline_raciocinio.py):

```mermaid
graph LR
    Doc[Minuta Bruta do Contrato] --> E1[Etapa 1: Decomposição Estrutural<br/><i>Least-to-Most Prompting</i>]
    E1 --> Out1[(Output Intermediário 1<br/>Seções Atômicas Isoladas)]
    Out1 --> E2[Etapa 2: Resolução Factual & Tools<br/><i>Chain-of-Thought</i>]
    E2 --> Out2[(Output Intermediário 2<br/>CoT e Retorno das Tools)]
    Out2 --> E3[Etapa 3: Síntese e Emissão Tipada<br/><i>DadosContratoExtraido</i>]
    E3 --> OutFinal[Payload Sanitizado para Agente 2]
```

---

## 📝 3. Sequência de Prompts e Outputs Intermediários

### 🔹 ETAPA 1: Decomposição Estrutural (Least-to-Most Prompting)
- **Técnica:** *Least-to-Most Prompting*. Decompõe o documento complexo em 5 subproblemas atômicos, isolando os trechos literais de cada seção sem emitir juízos de conformidade jurídica.
- **Prompt Utilizado:**
```text
Você é o Agente 1 (Extrator Enriquecido), especialista na técnica de Least-to-Most Prompting.
Sua tarefa é DECOMPOR o contrato complexo em suas seções fundamentais mais simples, isolando estritamente 5 blocos:
1. PREAMBULO_QUALIFICACAO: identificação das partes e CNPJs.
2. OBJETO_CONTRATUAL: descrição concisa do escopo dos serviços.
3. CONDICOES_FINANCEIRAS: valor total, parcelamento e condições de liquidação.
4. PRAZOS_E_VIGENCIA: data base de início, prazo em meses e aviso prévio.
5. PENALIDADES_E_RESCISAO: percentual da multa rescisória, base de cálculo e gatilhos.

NÃO faça julgamentos de risco jurídico nesta etapa. Apenas isole, decomponha e normalize os parâmetros.
```

- **Output Intermediário 1 ([`agent/output_etapa1_decomposicao.json`](../agent/output_etapa1_decomposicao.json)):**
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
      "secao": "OBJETO_CONTRATUAL",
      "texto_original_relevante": "Prestação de serviços especializados em desenvolvimento, homologação e implantação de agentes inteligentes de IA...",
      "entidades_brutas_identificadas": {
        "escopo_resumido": "Desenvolvimento, homologação e implantação de agentes de inteligência artificial integrados a sistemas legados."
      }
    },
    {
      "secao": "CONDICOES_FINANCEIRAS",
      "texto_original_relevante": "Valor total de R$ 120.000,00 a serem pagos em 12 parcelas mensais e sucessivas de R$ 10.000,00...",
      "entidades_brutas_identificadas": {
        "valor_total_citado": 120000.0,
        "parcelas_citadas": 12,
        "valor_parcela_citado": 10000.0,
        "periodicidade_citada": "mensal"
      }
    },
    {
      "secao": "PRAZOS_E_VIGENCIA",
      "texto_original_relevante": "Vigência de 12 meses a contar da data de sua assinatura em 15 de janeiro de 2026, com aviso prévio de 30 dias...",
      "entidades_brutas_identificadas": {
        "data_assinatura_raw": "15/01/2026",
        "prazo_meses_raw": 12,
        "aviso_previo_dias_raw": 30
      }
    },
    {
      "secao": "PENALIDADES_E_RESCISAO",
      "texto_original_relevante": "Multa compensatória de 20% sobre o saldo remanescente do contrato na hipótese de rescisão imotivada sem justa causa...",
      "entidades_brutas_identificadas": {
        "multa_percentual_raw": 20.0,
        "base_calculo_raw": "saldo remanescente",
        "gatilho_raw": "rescisao_imotivada_sem_justa_causa"
      }
    }
  ]
}
```

---

### 🔹 ETAPA 2: Resolução Factual e Invocação de Tools (Chain-of-Thought - CoT)
- **Técnica:** *Chain-of-Thought (CoT)*. O modelo explicita o raciocínio encadeado passo a passo para cada dimensão, acionando ferramentas determinísticas de cálculo e normalização:
  1. *CoT Financeiro:* Compara valor global e parcelas, invocando a ferramenta `extrair_e_validar_tabela_financeira`.
  2. *CoT de Prazos:* Cruza a data de assinatura com os meses de vigência, invocando a ferramenta `normalizar_prazos_e_datas`.
  3. *CoT de Penalidades e Partes:* Valida os formatos numéricos de CNPJ e extrai o percentual fidedigno da multa.

- **Output Intermediário 2 ([`agent/output_etapa2_cot.json`](../agent/output_etapa2_cot.json)):**
```json
{
  "resolucoes_passo_a_passo": [
    {
      "dimensao": "CONDICOES_FINANCEIRAS",
      "premissa_bruta": "Texto indica R$ 120.000,00 divididos em 12 parcelas mensais de R$ 10.000,00.",
      "raciocinio_passo_a_passo": "Passo 1: Identifico o valor global expresso como R$ 120.000,00. Passo 2: Identifico o cronograma de 12 parcelas de R$ 10.000,00. Passo 3: Invoco a ferramenta 'extrair_e_validar_tabela_financeira' para atestar consistência matemática. Passo 4: A ferramenta verifica que 12 × 10.000 = 120.000,00 (diferença de 0 centavos). Passo 5: Conclui-se que o plano financeiro é matematicamente íntegro e normalizado em BRL.",
      "tool_invocada": "extrair_e_validar_tabela_financeira",
      "dado_resolvido_final": {
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
    },
    {
      "dimensao": "PRAZOS_E_VIGENCIA",
      "premissa_bruta": "Assinatura em 15/01/2026 com vigência de 12 meses e aviso prévio de 30 dias.",
      "raciocinio_passo_a_passo": "Passo 1: Extraio a data base de início como 15/01/2026. Passo 2: Extraio o prazo de 12 meses estipulado no instrumento. Passo 3: Invoco a ferramenta 'normalizar_prazos_e_datas' para computar a data de encerramento. Passo 4: O algoritmo projeta 12 meses no calendário, definindo término em 2027-01-15 (365 dias corridos). Passo 5: Converte-se para o padrão internacional ISO-8601 (YYYY-MM-DD).",
      "tool_invocada": "normalizar_prazos_e_datas",
      "dado_resolvido_final": {
        "data_inicio_iso": "2026-01-15",
        "data_fim_calculada_iso": "2027-01-15",
        "vigencia_meses": 12,
        "dias_corridos_totais": 365,
        "aviso_previo_dias": 30,
        "vigencia_formatada": "De 2026-01-15 a 2027-01-15 (12 meses / 365 dias)"
      }
    },
    {
      "dimensao": "QUALIFICACAO_E_PENALIDADES",
      "premissa_bruta": "Contratante e Contratada com CNPJs explícitos e multa de rescisão de 20%.",
      "raciocinio_passo_a_passo": "Passo 1: Verifico a higidez formal dos CNPJs (98.765.432/0001-10 e 12.345.678/0001-90), ambos com 14 dígitos numéricos. Passo 2: Isolei a cláusula de rescisão imotivada que estipula multa de 20% sobre o saldo remanescente. Passo 3: Registro o percentual bruto de 20.0% sem efetuar juízos de conformidade ou risco, preservando o dado fidedigno para que o Agente 2 (Avaliador de Risco) execute a auditoria jurídica futura.",
      "tool_invocada": null,
      "dado_resolvido_final": {
        "cnpj_contratada_validado": "12.345.678/0001-90",
        "percentual_multa_extraido": 20.0,
        "base_calculo": "saldo_remanescente"
      }
    }
  ],
  "resumo_sanitizacao": "Todas as ambiguidades temporais, financeiras e contratuais foram resolvidas e validadas por ferramentas de cálculo."
}
```

---

### 🔹 ETAPA 3: Síntese e Emissão Tipada (Pydantic v2)
- **Técnica:** Síntese Estruturada. Agrega os outputs intermediários validados em uma instância do modelo `DadosContratoExtraido` e gera o relatório técnico em Markdown [`agent/parecer_auditoria_raciocinio.md`](../agent/parecer_auditoria_raciocinio.md).
- **Output Consolidado ([`agent/resultado_pipeline_raciocinio.json`](../agent/resultado_pipeline_raciocinio.json)):** Contém a rastreabilidade completa das três etapas, preservando a higidez factual dos dados para a etapa posterior de auditoria de risco.
