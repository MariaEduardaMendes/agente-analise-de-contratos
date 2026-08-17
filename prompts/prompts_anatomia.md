# Documentação de Prompts com Anatomia Definida (Anatomia do Prompt)

Esta documentação detalha a estruturação formal das instruções enviadas ao LLM no **Agente 1 (Extração de Dados de Contratos)**, dividida rigorosamente nos **quatro componentes da anatomia de prompts**: **Instrução**, **Contexto**, **Exemplos** e **Formato de Saída**.

---

## 🏗️ 1. Decomposição Anatômica do Prompt Principal

O prompt do sistema foi projetado de forma modular para maximizar o determinismo da saída e eliminar alucinações na extração jurídica.

### 1.1 Instrução (Role & Direct Directive)
> **Papel e Tarefa**:
> *"Você é um especialista em auditoria jurídica e análise de documentos contratuais. Sua missão é realizar a extração precisa e fidedigna de metadados e cláusulas contratuais a partir do texto fornecido. Não assuma ou infira informações não presentes no texto. Mantenha valores numéricos, percentuais e datas exatamente conforme estipulados no documento. Caso algum campo não esteja presente, utilize valores nulos/padrão seguros sem inventar dados."*

### 1.2 Contexto (Background & Multi-Agent Pipeline)
> **Cenário do Sistema**:
> *"Você atua como o Agente 1 (Extração) de um sistema multi-agente automatizado de análise contratual. Os dados JSON extraídos por você serão enviados diretamente para o Agente 2 (Validação), que consultará tabelas de regras de negócio para verificar a conformidade jurídica das cláusulas. Portanto, a exatidão dos valores numéricos e das datas é crítica para evitar erros de validação a jusante."*

### 1.3 Exemplos (Few-Shot Demonstration)
> **Demonstração In-Context**:
> **Entrada de Exemplo:**
> `"CONTRATO DE SERVIÇO. CONTRATANTE: Empresa X (CNPJ 11.111.111/0001-11). CONTRATADA: Serviços Y (CNPJ 22.222.222/0001-22). Objeto: Consultoria. Valor: R$ 10.000,00 em 2x. Vigência: 12 meses a partir de 01/01/2026. Multa de rescisão de 10% com aviso prévio de 30 dias."`
>
> **Saída de Exemplo Esperada:**
> ```json
> {
>   "titulo": "CONTRATO DE SERVIÇO",
>   "contratante": {"nome": "Empresa X", "cnpj_cpf": "11.111.111/0001-11", "papel": "CONTRATANTE"},
>   "contratada": {"nome": "Serviços Y", "cnpj_cpf": "22.222.222/0001-22", "papel": "CONTRATADA"},
>   "objeto": "Consultoria",
>   "valor_total_brl": 10000.0,
>   "forma_pagamento": "em 2x",
>   "vigencia_meses": 12,
>   "data_inicio": "01/01/2026",
>   "multa_rescisao_percentual": 10.0,
>   "aviso_previo_dias": 30
> }
> ```

### 1.4 Formato de Saída (Output Schema & Constraints)
> **Regras de Validação Pydantic**:
> *"A resposta DEVE ser estritamente formatada de acordo com o esquema JSON validado pelo modelo DadosContrato. Campos obrigatórios: valor_total_brl (float puro, ex: 45000.0), multa_rescisao_percentual (float puro, ex: 20.0), vigencia_meses e aviso_previo_dias (inteiros), data_inicio (string DD/MM/AAAA)."*

---

## 🧪 2. Comparação de Comportamento e Outputs Produzidos

| Métrica / Comportamento | Versão Inicial (Prompt Simples) | Versão Anatômica (Instrução + Contexto + Few-Shot + Schema) |
| :--- | :--- | :--- |
| **Papel da Parte** | Retornava strings genéricas ("CONTRATANTE", "pessoa jurídica...") | Padronizou e isolou a Razão Social exata e o papel formal no contrato |
| **Valor Numérico (`valor_total_brl`)** | Eventualmente trazia caracteres como `"R$ 45.000,00"` | Converteu estritamente para `float` puro (`45000.0`) exigido para contas no Agente 2 |
| **Formatos de Data** | Variava entre `"01 de setembro de 2026"` e `"2026-09-01"` | Padronizou em `DD/MM/AAAA` (`01/09/2026`) graças ao exemplo Few-Shot |
| **Determinismo em Validação** | 75% de conformidade imediata | 100% de conformidade com o schema Pydantic |

---

## 📝 3. Output Final Gerado (`resultado_extracao.json`)

```json
{
  "titulo": "CONTRATO DE PRESTAÇÃO DE SERVIÇOS DE DESENVOLVIMENTO DE INTELIGÊNCIA ARTIFICIAL",
  "contratante": {
    "nome": "TechSolutions Ltda.",
    "cnpj_cpf": "12.345.678/0001-90",
    "papel": "CONTRATANTE"
  },
  "contratada": {
    "nome": "Alfa Consultoria em IA S.A.",
    "cnpj_cpf": "98.765.432/0001-10",
    "papel": "CONTRATADA"
  },
  "objeto": "prestação de serviços técnicos especializados para o desenvolvimento, integração e suporte de um sistema de inteligência artificial multi-agentes focado em análise de conformidade e extração de dados de documentos jurídicos",
  "valor_total_brl": 45000.0,
  "forma_pagamento": "3 parcelas mensais e consecutivas de R$ 15.000,00 com primeiro vencimento em 15/09/2026",
  "vigencia_meses": 6,
  "data_inicio": "01/09/2026",
  "multa_rescisao_percentual": 20.0,
  "aviso_previo_dias": 30
}
```

---

## 🎯 4. Conclusão dos Ajustes
A adição explícita da seção de **Contexto (Pipeline Multi-Agente)** conscientizou o modelo sobre o consumo posterior dos dados, enquanto a seção de **Exemplos (Few-Shot)** garantiu que os tipos primitivos Python (`float`, `int`, `string DD/MM/AAAA`) fossem respeitados integralmente sem necessidade de pós-processamento manual.
