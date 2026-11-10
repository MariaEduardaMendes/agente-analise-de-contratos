# Avaliação de Variantes de Prompt e Ciclo Prompt-Response-Reflect-Revise (evaluation/)

Este diretório contém a avaliação sistemática da qualidade de prompts para o **Agente 1 (Extrator Enriquecido)**, detalhando o benchmark comparativo A/B com **execuções 100% REAIS** via modelo LLM (`nvidia/nemotron-3.5-lightning:free` via OpenRouter e OpenAI Agents SDK), critérios objetivos de decisão e a aplicação do ciclo metodológico **Prompt-Response-Reflect-Revise (PRRR)**.

---

## 📊 1. Critérios de Avaliação e Métricas

Para avaliar os outputs do agente, estabelecemos 4 métricas quantitativas e o Índice Geral de Qualidade (IGQ):

| Métrica | Sigla | Descrição | Escala | Peso |
| :--- | :---: | :--- | :---: | :---: |
| **Taxa de Conformidade de Schema** | **TCS** | Validação estrita perante os validadores Pydantic v2 de `DadosContratoExtraido`. | 0.0 a 1.0 | 30% |
| **Taxa de Invocação de Ferramentas** | **TIT** | Execução autônoma de `normalizar_prazos_e_datas` e `extrair_e_validar_tabela_financeira`. | 0.0 a 1.0 | 30% |
| **Acurácia Factual dos Campos** | **AFC** | Exatidão dos campos monetários, número de parcelas, vigência em meses e percentual de multa. | 0.0 a 1.0 | 20% |
| **Acurácia na Sanitização e Cálculo** | **ASC** | Cálculo da data final no calendário ISO-8601 e verificação de consistência matemática das parcelas. | 0.0 a 1.0 | 20% |

$$\text{IGQ} = (0.30 \times \text{TCS}) + (0.30 \times \text{TIT}) + (0.20 \times \text{AFC}) + (0.20 \times \text{ASC})$$

---

## ⚖️ 2. Comparativo de Variantes (Benchmark A/B Real)

O benchmark foi executado pelo script [`evaluation/avaliacao_metricas_prompt.py`](avaliacao_metricas_prompt.py) sobre a minuta real [`agent1/contrato_exemplo.txt`](../agent1/contrato_exemplo.txt):

### 2.1 Descrição das Variantes Testadas
- **Variante A (Prompt Monolítico / Não Estruturado):** Prompt básico solicitando extração em texto livre via OpenAI Chat Completions, sem validação de schema e sem ativação de tools.
- **Variante B (Prompt Estruturado + CoT + Tools + Pydantic v2):** Prompt com anatomia em 4 componentes (Instrução, Contexto, Exemplos e Restrições de Schema), executado via `Runner.run` com invocação mandatória de tools (`@function_tool`) e validação por `output_type=DadosContratoExtraido`.

### 2.2 Tabela Comparativa de Resultados Reais

| Métrica | Variante A (Prompt Básico / LLM Real) | Variante B (Agente Estruturado + Tools / Runner.run) | Ganho |
| :--- | :---: | :---: | :---: |
| **TCS (Schema Adherence)** | `0.00` | `1.00` | **+1.00** |
| **TIT (Tool Invocation)** | `0.00` | `1.00` | **+1.00** |
| **AFC (Acurácia Factual)** | `1.00` | `1.00` | **0.00** |
| **ASC (Sanitização e Cálculo)** | `0.00` | `1.00` | **+1.00** |
| **Índice Geral de Qualidade (IGQ)** | **`0.200`** | **`1.000`** | **+0.800 (+400%)** |

### 2.3 Registro da Decisão com Justificativa
> **Decisão Final:** Adoção definitiva da **Variante B**.  
> **Justificativa Técnica:** Embora o modelo em texto livre (Variante A) tenha identificado os termos no texto (AFC=1.00), gerou uma resposta em prosa completamente incompatível com integrações de microsserviços (TCS=0.00), não acionou tools (TIT=0.00) e não calculou a data de encerramento no calendário ISO-8601 nem verificou a consistência algébrica das parcelas (ASC=0.00). A Variante B alcançou pontuação máxima (IGQ = 1.000), garantindo um contrato de dados limpo, sanitizado e enriquecido com o cadastro de fornecedores para o Agente 2.

---

## 🔄 3. Ciclo Prompt-Response-Reflect-Revise (PRRR)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  1. PROMPT   │ ──> │ 2. RESPONSE  │ ──> │  3. REFLECT  │ ──> │  4. REVISE   │
│  (Versão V1) │     │  (Saída V1)  │     │ (Diagnóstico)│     │  (Versão V2) │
│              │     │              │     │              │     │              │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### 1. Prompt (V1 - Monolítico)
```text
Você é um assistente geral. Extraia os dados do contrato abaixo e escreva um resumo livre com o título, partes envolvidas, valores, prazos e penalidades:
[texto de agent1/contrato_exemplo.txt]
```

### 2. Response (Produzida pelo Modelo Real na V1)
```text
**Resumo do Contrato – Prestação de Serviços de Desenvolvimento de Inteligência Artificial**
**Partes envolvidas:** TechSolutions Ltda. e Alfa Consultoria em IA S.A.
**Valores:** R$ 45.000,00 distribuídos em 3 parcelas de R$ 15.000,00 com vencimento em 15/09/2026.
**Prazos:** Vigência de 6 meses, com início em 01/09/2026 e término em 01/03/2027.
**Penalidades:** Aviso prévio de 30 dias e multa compensatória de 20% do valor remanescente.
```

### 3. Reflect (Diagnóstico Crítico das Falhas da V1)
1. **Ausência de Normalização de Datas:** O modelo gerou texto corrido informal sem computar os dias corridos exatos nem disponibilizar chaves estruturadas no formato ISO-8601 (`YYYY-MM-DD`).
2. **Falta de Verificação Algébrica Independente:** O modelo fez leitura textual passiva sem conferência determinística de arredondamentos monetários por função externa.
3. **Inviabilidade de Consumo Downstream:** Uma saída em Markdown livre quebra pipelines orientados a serviços (APIs REST e nós n8n) por não garantir tipagem estrita de campos.

### 4. Revise (Revisão para o Prompt V2 e Sucesso da Execução com Tools e Pydantic)
O prompt foi reestruturado com **Anatomia Anatômica em 4 Componentes**, **Delegação Mandatória para Tools Python (@function_tool)** e **Acoplamento a `output_type=DadosContratoExtraido`**:

```text
### 1. INSTRUÇÃO (Role & Task)
Você é o Agente 1 (Extrator Enriquecido de Contratos), especialista em Processamento de Linguagem Natural Jurídica.
Sua missão estrita é:
1. Extrair os metadados factuais do texto bruto do contrato (título, partes, CNPJs, objeto, valores, datas, multas).
2. OBRIGATORIAMENTE invocar as ferramentas Python disponíveis:
   - 'normalizar_prazos_e_datas' para datas ISO-8601 e dias corridos.
   - 'extrair_e_validar_tabela_financeira' para consistência matemática das parcelas.
   - 'consultar_cadastro_fornecedor' para enriquecimento cadastral na fonte corporativa.
3. NÃO emita julgamentos de risco; popule DadosContratoExtraido.
```

- **Resultado Real da V2 via Runner.run:** Objeto Pydantic v2 validado (TCS = 1.0), invocação de tools com execução rastreada (TIT = 1.0), exatidão factual total (AFC = 1.0) e sanitização computacional plena (ASC = 1.0), atingindo **IGQ = 1.000**.
