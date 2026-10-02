# Documentação de Saídas Estruturadas em JSON com Schema Explícito

Esta documentação especifica o uso de **Saídas Estruturadas (Structured Outputs)** no **Agente 1 (Extrator Enriquecido)** via **OpenAI Agents SDK** e **Pydantic v2**. O objetivo é garantir respostas tipadas, fortemente validadas e auditáveis, eliminando respostas em texto livre ou desalinhadas do schema.

---

## 🎯 1. Definição do Schema Pydantic e Campos Obrigatórios

O modelo de dados do contrato extraído é estruturado nas classes Pydantic v2 definidas em [`agent/models.py`](../agent/models.py):

### 1.1 Modelo `ParteContratante` (Sub-objeto)
| Campo | Tipo Python | Obrigatório? | Descrição | Exemplo de Valor |
| :--- | :--- | :--- | :--- | :--- |
| `nome` | `str` | Sim | Razão Social ou Nome completo da parte | `"Empresa Contratante S.A."` |
| `cnpj_cpf` | `str` | Sim | Número formatado do CNPJ/CPF com validação de dígitos | `"98.765.432/0001-10"` |
| `papel` | `str` | Sim | Papel no documento (`CONTRATANTE` ou `CONTRATADA`) | `"CONTRATANTE"` |

### 1.2 Modelo `CronogramaFinanceiro` (Validado via Tool Financeira)
| Campo | Tipo Python | Descrição | Exemplo de Valor |
| :--- | :--- | :--- | :--- |
| `valor_total_brl` | `float` | Valor global do contrato em Reais | `120000.0` |
| `parcelas_quantidade` | `int` | Quantidade total de parcelas | `12` |
| `valor_parcela_brl` | `float` | Valor unitário de cada parcela | `10000.0` |
| `soma_consistente` | `bool` | Ateste algorítmico de consistência matemática | `true` |
| `cronograma_resumo` | `str` | Resumo descritivo das condições | `"12 parcelas de R$ 10,000.00 (mensal)"` |

### 1.3 Modelo `PeriodoVigencia` (Normalizado via Tool de Prazos)
| Campo | Tipo Python | Descrição | Exemplo de Valor |
| :--- | :--- | :--- | :--- |
| `data_inicio_iso` | `str` | Data de início em padrão ISO-8601 | `"2026-01-15"` |
| `data_fim_calculada_iso` | `str` | Data final calculada no calendário internacional | `"2027-01-15"` |
| `vigencia_meses` | `int` | Prazo formal em meses | `12` |
| `dias_corridos_totais` | `int` | Cômputo exato de dias de vigência | `365` |
| `aviso_previo_dias` | `int` | Prazo formal de aviso prévio de rescisão | `30` |

### 1.4 Modelo `DadosContratoExtraido` (Schema Principal de Saída do Agente 1)
Reúne as entidades `contratante`, `contratada`, `financeiro`, `vigencia` e `penalidades`, constituindo a interface de dados sanitizada a ser consumida pelo futuro Agente 2.

---

## ⚙️ 2. Configuração de `output_type` no Agent e Verificação via `result.final_output`

No **OpenAI Agents SDK**, a estruturação do retorno é configurada diretamente no parâmetro `output_type` da classe `Agent`. O `Runner` aplica as diretivas de *Structured Outputs* do modelo LLM para garantir que a resposta chegue já convertida no objeto Pydantic correspondente.

### Fluxo de Configuração e Captura no Script ([`agent/demo_saida_tipada.py`](../agent/demo_saida_tipada.py)):

1. **Configuração da Classe:** A classe Pydantic `DadosContratoExtraido` é passada diretamente ao argumento `output_type=DadosContratoExtraido` do `Agent`.
2. **Execução pelo Runner:** O framework despacha o prompt ao modelo exigindo conformidade com o JSON Schema da classe.
3. **Captura Tipada:** O objeto retornado em `resultado.final_output` é nativamente uma instância validada de `DadosContratoExtraido`.
4. **Serialização:** A conversão para payload JSON consumível por outros sistemas é realizada com `.model_dump()`.

---

## 📊 3. Exemplo do Payload JSON Validado Produzido pelo Agente

Abaixo está a saída real produzida pelo agente e registrada no repositório em [`agent/resultado_saida_tipada.json`](../agent/resultado_saida_tipada.json):

```json
{
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
  },
  "secoes_analisadas": [
    "PREAMBULO",
    "OBJETO",
    "PRECO_E_CONDICOES",
    "VIGENCIA",
    "RESCISAO_E_PENALIDADES"
  ]
}
```
