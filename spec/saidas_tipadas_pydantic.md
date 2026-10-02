# Relatório de Implementação: Saídas Tipadas e Validadas com Pydantic v2 e Tools (TP)

Este documento registra a implementação de saídas tipadas e validadas através de modelos **Pydantic v2** (`BaseModel`) integradas ao **OpenAI Agents SDK** com suporte simultâneo a ferramentas externas (`tools`) e tipo de retorno forçado (`output_type`).

---

## 🎯 1. Objetivo da Implementação

Em sistemas multi-agentes corporativos (especialmente no domínio jurídico e contratual), saídas em texto livre ou JSONs desestruturados geram quebras de contrato de API a jusante (no n8n ou no Agente 2 de Avaliação de Risco).

O objetivo desta etapa foi:
1. Modelar a estrutura de dados com **Pydantic v2**, aplicando validadores de campo (`@field_validator`) para formatos documentais (CPF/CNPJ) e valores estritamente positivos.
2. Configurar o parâmetro `output_type` no `Agent` do OpenAI Agents SDK.
3. Garantir a **combinação simultânea de `tools` e `output_type`**, permitindo que o Agente 1 (Extrator Enriquecido) acione ferramentas de cálculo e normalização e injete os resultados na estrutura tipada validada, acessível em Python via `result.final_output`.

---

## 📐 2. Modelagem com Pydantic v2 e Validadores Estritos

Os modelos de domínio foram implementados nos módulos [`agent/models.py`](../agent/models.py) e [`agent/demo_saida_tipada.py`](../agent/demo_saida_tipada.py), estruturados nas seguintes entidades:

### 2.1 Entidades de Dados
- **`ParteContratante`**:
  - `nome: str`: Nome completo ou Razão Social.
  - `cnpj_cpf: str`: Documento validado com `@field_validator` (aceita estritamente 11 dígitos para CPF ou 14 dígitos para CNPJ).
  - `papel: str`: Atribuição formal (`CONTRATANTE` ou `CONTRATADA`).

- **`CronogramaFinanceiro`** *(Enriquecido pela Tool `extrair_e_validar_tabela_financeira`)*:
  - `moeda: str`: Moeda contratada (ex: `BRL`).
  - `valor_total_brl: float`: Valor financeiro total validado com `@field_validator` (> 0).
  - `parcelas_quantidade: int`: Número total de parcelas.
  - `valor_parcela_brl: float`: Valor unitário de cada parcela (> 0).
  - `periodicidade: str`: Periodicidade das parcelas (ex: `mensal`).
  - `soma_consistente: bool`: Verificação booleana indicando se o somatório das parcelas coincide com o total.
  - `discrepancia_centavos: float`: Divergência residual de centavos.
  - `cronograma_resumo: str`: Resumo textual descritivo do parcelamento.

- **`PeriodoVigencia`** *(Enriquecido pela Tool `normalizar_prazos_e_datas`)*:
  - `data_inicio_iso: str`: Data de início normalizada no padrão ISO-8601 (`YYYY-MM-DD`).
  - `data_fim_calculada_iso: str`: Data de término projetada no calendário internacional (`YYYY-MM-DD`).
  - `vigencia_meses: int`: Duração formal em meses.
  - `dias_corridos_totais: int`: Cômputo exato de dias de vigência.
  - `aviso_previo_dias: int`: Dias exigidos para aviso prévio de rescisão.
  - `vigencia_formatada: str`: Representação descritiva amigável do período.

- **`ClausulaPenal`**:
  - `percentual_multa_rescisoria: float`: Percentual estipulado para rescisão imotivada.
  - `base_calculo: str`: Base de incidência da multa (ex: `saldo remanescente`).
  - `gatilho_aplicacao: str`: Condição formal de disparo da penalidade.

- **`DadosContratoExtraido`** *(Modelo Raiz de Extração do Agente 1)*:
  - Metadados contratuais: `titulo`, `objeto`, `secoes_analisadas`.
  - Entidades estruturadas: `contratante`, `contratada`, `financeiro`, `vigencia` e `penalidades`.

---

## ⚙️ 3. Configuração do `output_type` e Acesso via `result.final_output`

No construtor do `Agent` no script [`agent/demo_saida_tipada.py`](../agent/demo_saida_tipada.py):
1. **Atribuição das Tools:** A lista `tools=[normalizar_prazos_e_datas, extrair_e_validar_tabela_financeira]` habilita as chamadas de funções determinísticas de cálculo e normalização pelo modelo.
2. **Definição de `output_type`:** O parâmetro `output_type=DadosContratoExtraido` instrui o SDK a impor o schema JSON correspondente ao modelo Pydantic v2.
3. **Acesso Estruturado:** O resultado da execução via `Runner.run()` disponibiliza o objeto validado diretamente em `resultado.final_output`, pronto para serialização via `.model_dump()` ou encaminhamento ao pipeline do n8n / Agente 2.

---

## 🧪 4. Evidência de Execução e Verificação de Tipagem

Durante a execução de [`agent/demo_saida_tipada.py`](../agent/demo_saida_tipada.py), o sistema executou o fluxo com as ferramentas e produziu o seguinte log de verificação:

```text
================================================================================
DEMONSTRAÇÃO DE SAÍDAS TIPADAS PYDANTIC V2 - AGENTE 1 (EXTRATOR)
OpenAI Agents SDK com output_type=DadosContratoExtraido
================================================================================
[INFO] Contrato carregado (2009 caracteres).
[INFO] Invocando pipeline determinístico de extração e validação Pydantic...

[EXECUÇÃO DE TOOL] >>> Invocando 'normalizar_prazos_e_datas' com data_inicio=15/01/2026, vigencia=12 meses
[EXECUÇÃO DE TOOL] <<< Retorno da normalização de prazos: {"data_inicio_iso": "2026-01-15", "data_fim_calculada_iso": "2027-01-15", "vigencia_meses": 12, "dias_corridos_totais": 365, "aviso_previo_dias": 30, "vigencia_formatada": "De 2026-01-15 a 2027-01-15 (12 meses / 365 dias)"}

[EXECUÇÃO DE TOOL] >>> Invocando 'extrair_e_validar_tabela_financeira' com valor=120000.0, parcelas=12x 10000.0
[EXECUÇÃO DE TOOL] <<< Retorno da validação financeira: {"moeda": "BRL", "valor_total_brl": 120000.0, "parcelas_quantidade": 12, "valor_parcela_brl": 10000.0, "periodicidade": "mensal", "soma_parcelas_calculada": 120000.0, "soma_consistente": true, "discrepancia_centavos": 0.0, "cronograma_resumo": "12 parcelas de R$ 10,000.00 (mensal)"}

================================================================================
OBJETO VALIDADO COM SUCESSO (Pydantic v2):
Tipo da instância: DadosContratoExtraido
================================================================================
```

---

## 📑 5. Output Serializado Validado (`agent/resultado_saida_tipada.json`)

O arquivo [`agent/resultado_saida_tipada.json`](../agent/resultado_saida_tipada.json) registra o JSON estruturado gerado a partir do método `.model_dump()` do objeto Pydantic retornado:

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
