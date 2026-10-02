# Avaliação de Variantes de Prompt e Ciclo Prompt-Response-Reflect-Revise (evaluation/)

Este diretório contém a avaliação sistemática da qualidade de prompts para o **Agente 1 (Extrator Enriquecido)**, detalhando o benchmark comparativo A/B, critérios objetivos de decisão e a aplicação do ciclo metodológico **Prompt-Response-Reflect-Revise (PRRR)**.

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

## ⚖️ 2. Comparativo de Variantes (Benchmark A/B)

O benchmark foi aplicado sobre o documento [`agent/contrato_exemplo.txt`](../agent/contrato_exemplo.txt):

### 2.1 Descrição das Variantes Testadas
- **Variante A (Prompt Monolítico / Não Estruturado):** Prompt básico solicitando extração em texto livre, sem validação de schema e sem ativação de tools.
- **Variante B (Prompt Anatômico + CoT + Tools + Pydantic v2):** Prompt com anatomia em 4 componentes (Instrução, Contexto, Exemplos e Restrições de Schema), invocação mandatória de tools e validação por `output_type`.

### 2.2 Tabela Comparativa de Resultados

| Métrica | Variante A (Prompt Básico) | Variante B (Prompt Estruturado + Tools) | Ganho |
| :--- | :---: | :---: | :---: |
| **TCS (Schema Adherence)** | `0.00` | `1.00` | **+1.00** |
| **TIT (Tool Invocation)** | `0.00` | `1.00` | **+1.00** |
| **AFC (Acurácia Factual)** | `0.50` | `1.00` | **+0.50** |
| **ASC (Sanitização e Cálculo)** | `0.00` | `1.00` | **+1.00** |
| **Índice Geral de Qualidade (IGQ)** | **`0.200`** | **`1.000`** | **+0.800 (+400%)** |

### 2.3 Registro da Decisão com Justificativa
> **Decisão Final:** Adoção definitiva da **Variante B**.  
> **Justificativa:** A Variante A gerou texto livre não tipado, não ativou as ferramentas de normalização temporal e cálculo financeiro, e não calculou a data de término no calendário internacional. A Variante B atingiu 100% de conformidade técnica (IGQ = 1.000), garantindo um contrato de dados limpo e sanitizado para o Agente 2.

---

## 🔄 3. Ciclo Prompt-Response-Reflect-Revise (PRRR)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  1. PROMPT   │ ──> │ 2. RESPONSE  │ ──> │  3. REFLECT  │ ──> │  4. REVISE   │
│  (Versão V1) │     │  (Saída V1)  │     │ (Diagnóstico)│     │  (Versão V2) │
│              │     │              │     │              │     │              │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### 1. Prompt (V1 - Inicial)
```text
Extraia as informações do contrato jurídico abaixo e retorne partes, valores e vigência.
```

### 2. Response (Produzida pela V1)
```text
Identifiquei os dados do contrato:
Contratante: Empresa Contratante S.A.
Contratada: TechSolutions Ltda.
Valor: R$ 120.000,00 divididos em 12 parcelas de R$ 10.000,00.
Vigência: 12 meses a partir de 15/01/2026.
Multa por rescisão: 20% sobre o saldo remanescente.
```

### 3. Reflect (Diagnóstico Crítico das Falhas da V1)
1. **Ausência de Normalização de Datas:** O modelo apenas repetiu "12 meses a partir de 15/01/2026", sem calcular a data de término no padrão ISO-8601 (`2027-01-15`) nem o número total de dias corridos.
2. **Falta de Validação Matemática:** O modelo não conferiu algebricamente se `12 x 10.000 == 120.000` para garantir a integridade financeira.
3. **Quebra de Integração Tipada:** A resposta em texto corrido não respeita nenhum schema Pydantic, inviabilizando o consumo automático pelo pipeline do n8n / Agente 2.

### 4. Revise (Revisão para o Prompt V2 e Sucesso da Execução)
O prompt foi reestruturado com **Anatomia Anatômica**, **Imposição Mandatória de Tools de Cálculo** e **Vinculação ao Schema Pydantic v2**:

```text
### 1. INSTRUÇÃO (Role & Task)
Você é o Agente 1 (Extrator Enriquecido de Contratos).
Sua missão é extrair os metadados factuais da minuta e acionar as ferramentas de resolução:
1. Invocar 'normalizar_prazos_e_datas' passando data de início e meses de vigência.
2. Invocar 'extrair_e_validar_tabela_financeira' para atestar a consistência matemática das parcelas.
3. Formatar a saída estritamente segundo o schema DadosContratoExtraido.
```

- **Resultado da V2:** Objeto Pydantic v2 gerado com 100% de aderência de schema (TCS = 1.0), invocação autônoma de todas as tools (TIT = 1.0) e data final e parcelas conferidas (ASC = 1.0).
