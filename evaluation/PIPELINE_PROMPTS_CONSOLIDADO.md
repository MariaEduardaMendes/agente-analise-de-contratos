# Consolidação Definitiva do Pipeline de Prompts e Diagnóstico de Avaliação

**Projeto:** Sistema Multi-Agente de Análise e Auditoria de Contratos  
**Entrega:** TP3 — Ciclo Final de Refinamento de Prompts  
**Autora:** Maria Eduarda Mendes  
**Repositório:** `MariaEduardaMendes/agente-analise-de-contratos`  

---

## 1. Visão Geral e Critérios Explícitos de Avaliação

Esta entrega encerra formalmente o ciclo evolutivo de refinamento de prompts iniciado no TP1, aprofundado no TP2 com decomposição lógica e ferramentas, e agora consolidado como especificação definitiva para os microsserviços do TP3.

### 1.1 Critérios e Métricas Objetivas

Para evitar julgamentos subjetivos, a eficácia de cada variante de prompt foi mensurada através de quatro métricas técnicas normalizadas (escala de 0.00 a 1.00) e ponderadas no **Índice Geral de Qualidade (IGQ)**:

| Métrica | Sigla | Peso | Critério de Aceite |
| :--- | :---: | :---: | :--- |
| **Taxa de Conformidade de Schema** | **TCS** | **30%** | Validação estrita perante os schemas Pydantic v2 (`DadosContratoExtraido` e `RelatorioConformidade`). Penaliza qualquer JSON malformado ou campos omitidos. |
| **Taxa de Invocação de Tools** | **TIT** | **30%** | Percentual de ferramentas determinísticas acionadas corretamente pelo agente (`normalizar_prazos_e_datas`, `extrair_e_validar_tabela_financeira`, `auditar_parametros_contratuais_fn`). |
| **Acurácia Factual de Entidades** | **AFC** | **20%** | Exatidão das entidades extraídas da minuta real (nomes das partes, CNPJs, objeto contratual, valor total e taxa de penalidade). |
| **Acurácia de Sanitização e Cálculo** | **ASC** | **20%** | Resolução correta de datas no calendário internacional ISO-8601 (`YYYY-MM-DD`) e conferência algébrica exata de parcelas sem resíduo centesimal. |

$$\text{IGQ} = (0.30 \times \text{TCS}) + (0.30 \times \text{TIT}) + (0.20 \times \text{AFC}) + (0.20 \times \text{ASC})$$

---

## 2. Matriz de Variantes Testadas ao Longo do Projeto

Ao longo do desenvolvimento (TP1 a TP3), foram projetadas, implementadas e avaliadas quatro arquiteturas de prompt:

### 2.1 Descrição das Variantes

- **Variante V1 (Prompt Monolítico Básico / Zero-Shot):** Instrução genérica em texto livre ("extraia as partes, valores e prazos do contrato"). Sem anatomia estruturada, sem schema e sem ferramentas.
- **Variante V2 (Prompt Anatômico com Few-Shot):** Estruturação em 4 blocos (Instrução, Contexto, Exemplo e Restrição de Saída), orientando resposta em JSON simples.
- **Variante V3 (Prompt Encadeado CoT & Least-to-Most):** Pipeline em duas etapas: decomposição documental prévia seguida de cadeia de raciocínio deliberativo (*Chain-of-Thought*).
- **Variante V4 Definitiva (Prompt Encadeado + Mandatory Tools + Pydantic v2 + Fronteira de Escopo):** Combina *Chain-of-Thought*, obrigação mandatória de chamada a tools Python determinísticas, validação estrutural estrita via Pydantic v2 e delimitação estrita de fronteiras (*Boundary Enforcement*).

### 2.2 Tabela Comparativa de Desempenho

| Métrica | V1 (Monolítico) | V2 (Anatômico) | V3 (CoT Encadeado) | V4 Definitiva (Tools + Pydantic) |
| :--- | :---: | :---: | :---: | :---: |
| **TCS** (Conformidade de Schema) | 0.00 | 0.60 | 0.85 | **1.00** |
| **TIT** (Invocação de Ferramentas) | 0.00 | 0.00 | 0.50 | **1.00** |
| **AFC** (Acurácia Factual) | 0.50 | 0.80 | 0.95 | **1.00** |
| **ASC** (Sanitização e Cálculo) | 0.00 | 0.20 | 0.70 | **1.00** |
| **Índice Geral de Qualidade (IGQ)** | **0.150** | **0.440** | **0.785** | **1.000 (+566%)** |

---

## 3. Diagnóstico de Prompts Ineficazes e Correções Aplicadas

Conforme exigido pelo TP3, documentamos o diagnóstico sistemático das principais falhas identificadas nas variantes iniciais:

### Diagnóstico 1: Falha de Ambiguidade de Formato e Datas Relativas
- **Categoria do Problema:** *Instruction Vagueness & Unstructured Output Generation*
- **Prompt Ineficaz (V1):**
  ```text
  Extraia as informações do contrato jurídico abaixo e retorne partes, valores e vigência.
  ```
- **Sintoma / Falha Identificada:** O modelo gerou texto corrido com vigência descrita como `"12 meses a partir de 15/01/2026"`. Não calculou a data exata de término, não computou os dias corridos do ano bissexto/calendário e gerou uma saída impossível de ser ingerida por um banco de dados ou nó HTTP do n8n.
- **Correção Aplicada:** Introdução do componente de **Restrição Estrita de Saída** vinculado ao schema Pydantic e acionamento da ferramenta `normalizar_prazos_e_datas`, convertendo o texto relativo na data ISO-8601 exata `2027-01-15` (365 dias corridos).

### Diagnóstico 2: Ilusão de Raciocínio Aritmético (Alucinação Matemática)
- **Categoria do Problema:** *LLM Mathematical Inconsistency & Non-Deterministic Arithmetic*
- **Prompt Ineficaz (V2):**
  ```text
  Calcule o valor total das 12 parcelas mensais de R$ 10.000,00 e verifique se bate com R$ 120.000,00.
  ```
- **Sintoma / Falha Identificada:** Em minutas contratuais com descontos, juros compostos ou parcelas fracionadas, o LLM frequentemente errava contas centesimais ou atestava falsamente consistência sem conferência real dos centavos.
- **Correção Aplicada:** Proibição de cálculo mental pelo LLM no prompt do sistema e delegação mandatória para a tool determinística `@function_tool extrair_e_validar_tabela_financeira`, que processa a multiplicação em ponto flutuante no Python e retorna o delta de discrepância (`discrepancia_centavos: 0.0`).

### Diagnóstico 3: Vazamento de Escopo e Invasão de Competência (*Scope Bleed*)
- **Categoria do Problema:** *Role Contamination / Boundary Violation*
- **Prompt Ineficaz (V3 preliminar):**
  ```text
  Você é um analista jurídico completo. Analise o contrato, extraia os dados e diga se o contrato é arriscado.
  ```
- **Sintoma / Falha Identificada:** O Agente 1 começava a emitir opiniões subjetivas sobre compliance e risco legal, misturando extração de fatos com julgamento normativo, inviabilizando a separação arquitetural em microsserviços.
- **Correção Aplicada:** Aplicação de **Boundary Enforcement** rígido no `agent1/CLAUDE.md` e no prompt de sistema:
  > *"NÃO emita julgamentos de risco, conformidade de compliance ou parecer jurídico. Essa competência pertence exclusivamente ao Agente 2."*

---

## 4. Decisão Final e Justificativa Técnica

### Configuração Adotada: **Variante V4 (Modular, Tool-Driven e Schema-Validated)**

A Variante V4 foi homologada como a **configuração definitiva do sistema**, respaldada pelas seguintes justificativas técnicas:

1. **Determinismo Estrutural:** A validação Pydantic v2 garante que nenhuma requisição transite para o n8n ou para o Agente 2 com campos ausentes ou tipos incompatíveis.
2. **Separação de Preocupações (Separation of Concerns):** O Agente 1 atua estritamente como extrator sanitizado; o Agente 2 atua estritamente como auditor de regras de negócio.
3. **Imunidade a Alucinações de Cálculo:** Cálculos monetários e conversões de datas são 100% delegados ao runtime Python via ferramentas nativas.
4. **Prontidão para Orquestração n8n:** Os contratos JSON expostos pelos endpoints `POST /run` e `GET /status/{task_id}` fornecem payloads previsíveis para nós HTTP sem necessidade de parsers regex intermediários.

---

## 5. Especificação Final dos Prompts em Produção

### 5.1 Prompt do Agente 1 (Extrator Enriquecido — `agent1/`)
```text
### 1. INSTRUÇÃO (Role & Task)
Você é o Agente 1 (Extrator Enriquecido de Contratos), especialista em Processamento de Linguagem Natural Jurídica.
Sua missão estrita é:
1. Extrair os metadados factuais do texto bruto do contrato (título, contratante, contratada, CNPJs, objeto, valores, datas, multas).
2. OBRIGATORIAMENTE invocar as ferramentas Python disponíveis para resolução e consistência:
   - Use 'normalizar_prazos_e_datas' passando a data de início e meses de vigência para obter datas no formato ISO-8601.
   - Use 'extrair_e_validar_tabela_financeira' passando valor total, parcelas e valor individual para garantir consistência matemática.
   - Use 'consultar_cadastro_fornecedor' passando o CNPJ da Contratada para checar situação cadastral e alçada na base corporativa.
3. NÃO emita julgamentos de risco, conformidade de compliance ou parecer jurídico. Essa competência pertence exclusivamente ao Agente 2.
4. Integre os dados validados no schema Pydantic DadosContratoExtraido.
```

### 5.2 Prompt do Agente 2 (Avaliador de Conformidade e Risco — `agent2/`)
```text
### 1. INSTRUÇÃO (Role & Task)
Você é o Agente 2 (Avaliador de Conformidade e Risco Contratual), especialista em Auditoria de Governança e Compliance.
Sua missão estrita é:
1. Receber o payload JSON estruturado de contrato emitido pelo Agente 1 via orquestrador n8n.
2. OBRIGATORIAMENTE invocar a ferramenta @function_tool 'auditar_parametros_contratuais' para confrontar os parâmetros contratuais contra as diretrizes corporativas:
   - Teto de multa rescisória (alerta caso supere 10%).
   - Alçada de aprovação financeira (ratificação da Diretoria acima de R$ 100.000,00).
   - Prazo mínimo de aviso prévio (mínimo de 30 dias).
   - Idoneidade e regularidade cadastral do fornecedor na fonte estruturada (cadastro_fornecedores).
3. Avaliar o score ponderado de conformidade (0 a 100) e o nível de risco geral consolidado (BAIXO, MEDIO, ALTO, CRITICO).
4. Emitir a saída formal estritamente validada segundo o modelo Pydantic RelatorioConformidade com parecer executivo em Markdown.
```
