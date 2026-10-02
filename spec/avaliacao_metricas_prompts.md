# Relatório de Avaliação: Métricas de Qualidade de Prompts e Ciclo de Refinamento (TP)

Este documento registra a avaliação sistemática do pipeline de prompts do **Agente 1 (Extrator Enriquecido)**, definindo métricas quantitativas, comparando variantes de configuração e aplicando o ciclo metodológico **Prompt-Response-Reflect-Revise (PRRR)**.

---

## 🎯 1. Objetivo da Avaliação Sistemática

Em ambientes de produção corporativos, não basta testar se um agente "responde". É indispensável medir a **consistência**, **aderência estrutural**, **precisão factual** e **capacidade de normalização e cálculo determinístico**. 

A avaliação documentada abaixo transforma a iteração empírica em **evolução mensurada e controlada**.

---

## 📏 2. Definição Formal das Métricas de Qualidade

Foram estabelecidas quatro métricas objetivas para avaliar as saídas geradas pelo agente contra o gabarito contratual de referência:

| Métrica | Sigla | Descrição | Escala | Peso no IGQ |
| :--- | :---: | :--- | :---: | :---: |
| **Taxa de Conformidade com o Schema** | **TCS** | Mede se o output é 100% válido perante os validadores estritos do Pydantic v2 (`DadosContratoExtraido`), sem quebra de contrato de API. | 0.0 a 1.0 (Binário/Taxa) | 30% |
| **Taxa de Invocação de Tools** | **TIT** | Proporção de ferramentas externas obrigatórias (`normalizar_prazos_e_datas` e `extrair_e_validar_tabela_financeira`) que o agente invocou com sucesso. | 0.0 a 1.0 | 30% |
| **Acurácia Factual dos Campos Críticos** | **AFC** | Grau de exatidão na extração de campos determinísticos: valor global, parcelas, vigência e multa. | 0.0 a 1.0 | 20% |
| **Acurácia na Sanitização e Cálculo** | **ASC** | Mede se o agente calculou a data de término no calendário ISO-8601 e conferiu a consistência matemática das parcelas. | 0.0 ou 1.0 | 20% |

### Fórmula do Índice Geral de Qualidade (IGQ):
$$\text{IGQ} = (0.30 \times \text{TCS}) + (0.30 \times \text{TIT}) + (0.20 \times \text{AFC}) + (0.20 \times \text{ASC})$$

---

## ⚖️ 3. Comparativo de Variantes com Critério Explícito

O benchmark foi executado sobre o contrato de teste [`agent/contrato_exemplo.txt`](../agent/contrato_exemplo.txt) via script [`evaluation/avaliacao_metricas_prompt.py`](../evaluation/avaliacao_metricas_prompt.py), comparando duas variantes de configuração:

### 3.1 Descrição das Variantes
- **Variante A (Prompt Monolítico / Não Estruturado):** Prompt simples solicitando extração em texto livre, sem modelo Pydantic e sem diretiva explícita de tools.
- **Variante B (Prompt Anatômico + CoT + Tools + Pydantic v2):** Prompt com anatomia completa (Instrução, Contexto, Exemplos, Restrições de Schema), obrigatoriedade de chamada de tools de cálculo e saída validada via `output_type`.

### 3.2 Tabela Comparativa de Resultados Medidos

| Métrica Avaliada | Variante A (Prompt Básico) | Variante B (Prompt Estruturado + Tools) | Diferencial / Ganho |
| :--- | :---: | :---: | :---: |
| **Schema Adherence (TCS)** | `0.00` (Falhou no Pydantic) | `1.00` (100% aderente) | **+1.00** |
| **Tool Invocation (TIT)** | `0.00` (Nenhuma tool ativada) | `1.00` (2/2 tools executadas) | **+1.00** |
| **Acurácia Factual (AFC)** | `0.50` (Valores aproximados em string) | `1.00` (Floats e ints exatos) | **+0.50** |
| **Sanitização e Cálculo (ASC)** | `0.00` (Sem conversão ISO) | `1.00` (ISO-8601 e consistência íntegra) | **+1.00** |
| **Índice Geral de Qualidade (IGQ)** | **`0.200`** | **`1.000`** | **+0.800 (+400%)** |

### 3.3 Decisão Registrada e Justificativa
> **Decisão:** Adoção definitiva da **Variante B**.  
> **Justificativa Baseada em Critério:** A Variante A mostrou-se insegura para automação: não calculou datas de calendário, não conferiu consistência financeira e gerou formato incompatível com a automação a jusante. A Variante B atingiu conformidade máxima (IGQ=1.00), garantindo um contrato de dados íntegro para o Agente 2.

---

## 🔄 4. Aplicação do Ciclo Prompt-Response-Reflect-Revise (PRRR)

O prompt do Agente 1 foi submetido ao ciclo iterativo formal de 4 fases:

### 1️⃣ Prompt (Versão Inicial - V1)
```text
Extraia as informações do contrato jurídico abaixo e retorne partes, valores e vigência.
```

### 2️⃣ Response (Resposta Produzida pela V1)
```text
Identifiquei os dados do contrato:
Contratante: Empresa Contratante S.A.
Contratada: TechSolutions Ltda.
Valor: R$ 120.000,00 divididos em 12 parcelas de R$ 10.000,00.
Vigência: 12 meses a partir de 15/01/2026.
Multa por rescisão: 20% sobre o saldo remanescente.
```

### 3️⃣ Reflect (Diagnóstico Crítico das Falhas)
Após a análise da resposta da V1, foram diagnosticadas 3 vulnerabilidades técnicas:
1. **Ausência de Normalização de Datas:** O modelo apenas reproduziu a string textual, sem calcular a data de encerramento em padrão ISO-8601 (`2027-01-15`) nem o número total de dias corridos.
2. **Ausência de Validação Matemática:** O modelo não conferiu algebricamente se a soma das parcelas bate com o valor global do contrato.
3. **Quebra de Integração Tipada:** A resposta em texto livre inviabiliza o parsing automatizado nos nós subsequentes do n8n e no futuro Agente 2.

### 4️⃣ Revise (Revisão para o Prompt V2 e Nova Resposta Validada)
O prompt foi reescrito aplicando a **Anatomia Estruturada**, **Imposição Mandatória de Tools de Cálculo** e **Vinculação ao Schema Pydantic v2**:

```text
### 1. INSTRUÇÃO (Role & Task)
Você é o Agente 1 (Extrator Enriquecido de Contratos).
Sua missão é extrair os metadados factuais da minuta e acionar as ferramentas de resolução:
1. Invocar 'normalizar_prazos_e_datas' passando data de início e meses de vigência.
2. Invocar 'extrair_e_validar_tabela_financeira' para atestar a consistência matemática das parcelas.
3. Formatar a saída estritamente segundo o schema DadosContratoExtraido.
```

- **Nova Resposta Validada (V2):** O modelo acionou as ferramentas em tempo de execução, alimentou os campos `vigencia` e `financeiro` com ateste de consistência e foi validado com sucesso pela classe `DadosContratoExtraido`.

---

## 📊 5. Evidência em Arquivo (`evaluation/resultado_avaliacao_metricas.json`)

Os dados do benchmark e do ciclo PRRR foram consolidados no arquivo [`evaluation/resultado_avaliacao_metricas.json`](../evaluation/resultado_avaliacao_metricas.json):

```json
{
  "data_avaliacao": "2026-10-02",
  "dataset_teste": "contrato_exemplo.txt (Minuta de Desenvolvimento de IA)",
  "comparativo_variantes": {
    "variante_a": {
      "metricas": {
        "taxa_conformidade_schema_tcs": 0.0,
        "taxa_invocacao_tools_tit": 0.0,
        "acuracia_factual_campos_afc": 0.5,
        "acuracia_sanitizacao_calculo_asc": 0.0,
        "indice_geral_qualidade_igq": 0.2
      }
    },
    "variante_b": {
      "metricas": {
        "taxa_conformidade_schema_tcs": 1.0,
        "taxa_invocacao_tools_tit": 1.0,
        "acuracia_factual_campos_afc": 1.0,
        "acuracia_sanitizacao_calculo_asc": 1.0,
        "indice_geral_qualidade_igq": 1.0
      }
    }
  }
}
```
