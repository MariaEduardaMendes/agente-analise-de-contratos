# Documentação de Saídas Estruturadas em JSON com Schema Explícito

Esta documentação especifica o uso de **Saídas Estruturadas (Structured Outputs)** no **Agente 1 (Extração de Contratos)** via **OpenAI Agents SDK** e **Pydantic v2**. O objetivo é garantir respostas tipadas, fortemente validadas e auditáveis, eliminando respostas em texto livre ou desalinhadas do schema.

---

## 🎯 1. Definição do Schema Pydantic e Campos Obrigatórios

O modelo de dados do contrato é estruturado em duas classes Pydantic principais: `ParteContratante` e `DadosContrato`.

### 1.1 Modelo `ParteContratante` (Sub-objeto)
| Campo | Tipo Python | Obrigatório? | Descrição | Exemplo de Valor |
| :--- | :--- | :--- | :--- | :--- |
| `nome` | `str` | Sim | Razão Social ou Nome completo da parte | `"TechSolutions Ltda."` |
| `cnpj_cpf` | `str` | Sim | Número formatado ou numérico do CNPJ/CPF | `"12.345.678/0001-90"` |
| `papel` | `str` | Sim | Papel no documento (`CONTRATANTE` ou `CONTRATADA`) | `"CONTRATANTE"` |

### 1.2 Modelo `DadosContrato` (Schema Principal de Saída)
| Campo | Tipo Python | Restrição / Formato | Descrição | Exemplo de Valor |
| :--- | :--- | :--- | :--- | :--- |
| `titulo` | `str` | String não vazia | Título ou tipo identificador do contrato | `"CONTRATO DE PRESTAÇÃO DE SERVIÇOS..."` |
| `contratante` | `ParteContratante` | Objeto validado | Dados identificadores do Contratante | `{"nome": "TechSolutions Ltda.", ...}` |
| `contratada` | `ParteContratante` | Objeto validado | Dados identificadores da Contratada | `{"nome": "Alfa Consultoria em IA S.A.", ...}` |
| `objeto` | `str` | Texto sucinto | Resumo claro e objetivo da finalidade contratual | `"Desenvolvimento e suporte de IA multi-agentes..."` |
| `valor_total_brl` | `float` | Número real puro | Valor total do contrato em reais (BRL) | `45000.0` |
| `forma_pagamento` | `str` | Texto descritivo | Condição e parcelamento do pagamento | `"3 parcelas mensais consecutivas..."` |
| `vigencia_meses` | `int` | Número inteiro | Prazo total de vigência em meses | `6` |
| `data_inicio` | `str` | Formato `DD/MM/AAAA` | Data oficial de início de vigência | `"01/09/2026"` |
| `multa_rescisao_percentual` | `float` | Porcentagem pura | Multa estipulada para rescisão imotivada | `20.0` |
| `aviso_previo_dias` | `int` | Número de dias | Dias exigidos para notificação prévia | `30` |

---

## ⚙️ 2. Configuração de `output_type` no Agent e Verificação via `result.final_output`

No **OpenAI Agents SDK**, a estruturação do retorno é configurada diretamente no parâmetro `output_type` da classe `Agent`. O `Runner` aplica as ferramentas de *JSON Schema / Structured Outputs* do modelo LLM para garantir que a resposta chegue já convertida no objeto Pydantic correspondente.

### Trecho de Código de Configuração e Captura:

```python
from agents import Agent, Runner
from pydantic import BaseModel, Field

# 1. Passa a classe Pydantic como output_type
agente = Agent(
    name="Agente_Extracao_Contratos",
    model=modelo_custom,
    instructions=system_instructions,
    output_type=DadosContrato,  # <--- Configuração da Saída Estruturada
)

# 2. Executa a extração via Runner
resultado = Runner.run_sync(agente, prompt_usuario)

# 3. O output retornado em result.final_output já é uma instância de DadosContrato!
dados_extraidos = resultado.final_output

# Validação do tipo no runtime:
assert isinstance(dados_extraidos, DadosContrato)
print(f"Tipo retornado: {type(dados_extraidos)}")  # <class 'DadosContrato'>

# 4. Serialização limpa para JSON
payload_json = dados_extraidos.model_dump_json(indent=2)
```

---

## 📊 3. Exemplo do Payload JSON Validado Produzido pelo Agente

Abaixo está a saída real produzida pelo agente e registrada no repositório em [`resultado_extracao.json`](file:///c:/Users/dudap/OneDrive/Área%20de%20Trabalho/Agentes%20IA/PB/resultado_extracao.json):

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
  "objeto": "Desenvolvimento, integração e suporte de um sistema de inteligência artificial multi-agentes focado em análise de conformidade e extração de dados de documentos jurídicos.",
  "valor_total_brl": 45000.0,
  "forma_pagamento": "3 parcelas mensais e consecutivas de R$ 15.000,00 com primeiro vencimento em 15/09/2026",
  "vigencia_meses": 6,
  "data_inicio": "01/09/2026",
  "multa_rescisao_percentual": 20.0,
  "aviso_previo_dias": 30
}
```

---

## ✅ 4. Garantias e Vantagens da Saída Estruturada

1. **Ausência de Texto Livre**: O agente não inclui introduções como *"Aqui está o JSON extraído:"* ou marcadores markdown adicionais. A resposta é parseada e validada diretamente na camada SDK/Pydantic.
2. **Tipagem Garantida**: Campos como `valor_total_brl` chegam como `float` (ex: `45000.0`) e não como `string` (`"R$ 45.000,00"`), permitindo operações aritméticas diretas no Agente 2.
3. **Consumo no Pipeline Multi-Agente**: O payload JSON gerado pode ser serializado diretamente para webhooks (ex: n8n) ou inserido em tabelas de banco de dados SQLite/DuckDB sem necessidade de expressões regulares ou tratamentos complexos.
