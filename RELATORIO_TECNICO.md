# Relatório Técnico de Evolução do Sistema Multi-Agente de Análise de Contratos

**Projeto de Bloco — Desenvolvimento de Agentes Inteligentes**  
**Repositório Oficial:** [github.com/MariaEduardaMendes/agente-analise-de-contratos](https://github.com/MariaEduardaMendes/agente-analise-de-contratos)  
**Data:** 01/10/2026  
**Status:** Protótipo Funcional Validado em Produção  

---

## 🧭 1. Visão Geral das Evoluções Implementadas

Na primeira fase deste projeto, construímos um componente inicial: um script Python simples que recebia o texto bruto de um contrato e emitia uma extração básica em JSON. Embora funcional, o componente operava isolado, sem acesso à realidade factual fora do prompt, sem capacidade de decompor problemas complexos e sem memória entre sessões.

Nesta etapa, o sistema evoluiu para um **Agente Inteligente e Funcional**, atuando em quatro frentes estruturantes:

1. **Acesso a Tools Python de Resolução e Cálculo:** Implementação de ferramentas decoradas com `@function_tool` e tipagem estrita (PEP 484) que calculam datas de encerramento em padrão ISO-8601 e verificam a integridade matemática do cronograma financeiro.
2. **Pipelines de Raciocínio Encadeado (Prompt Chaining & CoT):** Decomposição de tarefas complexas através de *Least-to-Most Prompting* e raciocínio deliberativo passo a passo (*Chain-of-Thought*).
3. **Memória Persistente em Duas Camadas:**
   - *Camada de Sessão:* `SQLiteSession` vinculada ao **OpenAI Agents SDK** para preservar o histórico conversacional entre runs distintos.
   - *Camada Semântica Corporativa:* Pipeline de **RAG vetorial** com embeddings (`text-embedding-3-small` de 1536 dimensões) e similaridade de cosseno em SQLite.
4. **Saídas Fortemente Tipadas com Pydantic v2:** Validação estrutural de ponta a ponta com `@field_validator` e `@model_validator`, combinando `tools` e `output_type` no mesmo agente.

### 📐 1.1 Entregáveis de Arquitetura do TP2 (Os 9 Componentes)

O sistema orquestrado no **n8n** e executado via **OpenAI Agents SDK** foi estruturado em conformidade estrita com os requisitos da entrega, documentados integralmente em [`diagrama.md`](diagrama.md) e [`diagrama.png`](diagrama.png):

> [!NOTE]
> **Delimitação de Escopo do TP2:** A orquestração via **n8n** e o **Agente 2 (Avaliador de Risco)** constituem a **especificação arquitetural** planejada para implementação nas próximas entregas do Projeto de Bloco. A **implementação funcional e código executável deste TP2** concentra-se integralmente na evolução do **Agente 1 (Extrator Enriquecido)** em Python, dotando-o de ferramentas externas (`@function_tool`), raciocínio em etapas (*Least-to-Most* e *CoT*), persistência de memória (`SQLiteSession` + RAG) e saídas tipadas via Pydantic v2.

| # | Entregável do TP2 | Implementação na Solução |
| :-: | :--- | :--- |
| **1** | **Gatilho n8n** | **Webhook HTTP** (`POST /webhook/auditar-contrato`) com suporte a Chatbot Web e Telegram. |
| **2** | **Fonte de Informações** | • **Não Estruturada:** Minuta Contratual em texto bruto ([`agent/contrato_exemplo.txt`](agent/contrato_exemplo.txt)).<br/>• **Estruturada:** Prazos e Calendário ISO, Tabela Financeira e Precedentes Vetoriais RAG. |
| **3** | **Diagrama de Arquitetura** | Imagem contendo os **9 componentes** interconectados ([`diagrama.png`](diagrama.png)). |
| **4** | **Descrição dos 9 Componentes** | 1. Gatilho (Trigger); 2. Nó de Entrada n8n; 3. Terceiro Agente n8n (Router & Merger); 4. Módulo Assíncrono (Polling /status); 5. API REST dos Agentes (/run e /status); 6. Agente 1 (Extrator Enriquecido com Tools, CoT, RAG e Pydantic); 7. Memória (SQLiteSession + RAG do Agente 1); 8. Agente 2 (Avaliador de Risco — Desenvolvimento Futuro); 9. Nó de Saída (Relatório Consolidado). |
| **5** | **Exemplo de Fluxo de Dados** | Jornada de processamento: envio do contrato ➔ processamento no Agente 1 (decomposição estrutural, CoT, invocação de Tools de Prazos/Finanças, memória e validação Pydantic) ➔ entrega do relatório e dados estruturados ao usuário. |
| **6** | **Dado Estruturado** | Tabelas SQLite `sessoes_historico` e `precedentes_contratuais`, APIs REST e modelos Pydantic v2 (`DadosContratoExtraido`). |
| **7** | **Demais Itens do TP2** | Tools decoradas com `@function_tool`, raciocínio CoT/Least-to-Most, memória persistente, saídas tipadas e avaliação quantitativa A/B (PRRR) aplicados integralmente ao Agente 1. |

### 🏛️ 1.2 Descrição Detalhada dos 9 Componentes da Arquitetura

Conforme ilustrado em [`diagrama.png`](diagrama.png) e detalhado em [`diagrama.md`](diagrama.md):

1. **Componente 1 — Gatilho de Entrada (Trigger):** Ponto de entrada externo (Webhook HTTP, Chatbot Web ou Telegram) que captura a minuta do contrato e os parâmetros da auditoria submetidos pelo usuário.
2. **Componente 2 — Nó de Entrada do n8n (Recebimento e Parsing):** Recebe o payload HTTP inicial, efetua a sanitização do texto, valida a presença dos campos essenciais e encaminha os dados ao roteador.
3. **Componente 3 — Terceiro Agente n8n (Router & Merger):** Orquestrador central no n8n planejado para a arquitetura multi-agente, responsável por rotear jobs para os microsserviços e consolidar retornos.
4. **Componente 4 — Módulo de Chamadas Assíncronas (Background Tasks & Polling):** Gerencia requisições de longa duração via `POST /run` e polling cíclico em `GET /status`, garantindo resiliência operacional sem bloqueio da fila HTTP.
5. **Componente 5 — API REST dos Agentes (Endpoints `/run` e `/status`):** Camada padronizada de microsserviços HTTP que isola e expõe os motores de agentes Python de forma desacoplada do orquestrador.
6. **Componente 6 — Agente 1: Extrator Enriquecido (Motor Python + LLM) [Desenvolvido neste TP2]:** O agente central desenvolvido e evoluído neste TP2 via **OpenAI Agents SDK**. Ele é responsável por ler a minuta contratual, decompor a estrutura documental (*Least-to-Most* e *Chain-of-Thought*), acionar ferramentas externas (`@function_tool` de normalização temporal de datas e validação matemática de parcelas), acessar a memória de sessão e RAG, e produzir saídas estruturadas validadas com Pydantic v2 (`DadosContratoExtraido`).
7. **Componente 7 — Memória Persistente & RAG do Agente 1 (SQLiteSession & Vector DB):** Dupla camada de persistência vinculada diretamente ao **Agente 1**:
   - *Histórico:* `SQLiteSession` para reter diretrizes de sessão entre runs distintos.
   - *Semântica:* Vector DB com embeddings de 1536 dimensões (`text-embedding-3-small`) para recuperação contextual de precedentes contratuais.
8. **Componente 8 — Agente 2: Avaliador de Risco (Desenvolvimento Futuro):** Componente previsto na arquitetura global multi-agente que será implementado na próxima entrega do projeto, atuando como auditor desacoplado a partir dos dados do Agente 1.
9. **Componente 9 — Nó de Saída / Relatório Consolidado ao Usuário:** Camada de entrega que compila os metadados validados e o parecer executivo em formato Markdown e JSON estruturado, despachando o resultado ao usuário no canal de origem.

---

## 🛠️ 2. Documentação das Ferramentas Python (`@function_tool`)

O Agente 1 foi integrado a ferramentas determinísticas de extração, resolução temporal e consistência matemática ([`agent/tools.py`](agent/tools.py)) e busca de precedentes ([`agent/memoria_rag.py`](agent/memoria_rag.py)):

### 2.1 `normalizar_prazos_e_datas`
- **Finalidade:** Normalização temporal da vigência contratual e cálculo de data de término no padrão internacional ISO-8601 (`YYYY-MM-DD`).
- **Parâmetros de Entrada:** `data_inicio_str: str`, `meses_vigencia: int`, `dias_aviso_previo: int`.
- **Retorno JSON de Exemplo:**
```json
{
  "data_inicio_iso": "2026-01-15",
  "data_fim_calculada_iso": "2027-01-15",
  "vigencia_meses": 12,
  "dias_corridos_totais": 365,
  "aviso_previo_dias": 30,
  "vigencia_formatada": "De 2026-01-15 a 2027-01-15 (12 meses / 365 dias)"
}
```

### 2.2 `extrair_e_validar_tabela_financeira`
- **Finalidade:** Decomposição do cronograma financeiro e verificação algorítmica de integridade matemática entre valor global e parcelas.
- **Parâmetros de Entrada:** `valor_total: float`, `parcelas_qtd: int`, `valor_parcela: float`, `periodicidade: str`.
- **Retorno JSON de Exemplo:**
```json
{
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
```

### 2.3 `buscar_precedentes_contratuais_rag`
- **Finalidade:** Executa busca vetorial semântica sobre precedentes históricos, aditivos anteriores e cláusulas-padrão corporativas.
- **Parâmetro de Entrada:** `query: str` (texto de consulta comparado contra vetores de 1536 dimensões via similaridade de cosseno).
- **Retorno:** Trecho do precedente contratual mais similar com score de relevância e contexto normativo.

---

## ⛓️ 3. Pipeline de Raciocínio Encadeado e Outputs Intermediários

Para processar a minuta com fidelidade factual sem cometer alucinações matemáticas ou temporais, decompusemos a extração do Agente 1 em **três etapas de prompt encadeadas** ([`prompts/prompts_encadeados.md`](prompts/prompts_encadeados.md) e [`agent/pipeline_raciocinio.py`](agent/pipeline_raciocinio.py)):

### 🔹 Etapa 1: *Least-to-Most Prompting* (Decomposição Estrutural)
- **Técnica:** Decompõe o documento em 5 seções atômicas isoladas (**Preâmbulo**, **Objeto**, **Condições Financeiras**, **Prazos/Vigência** e **Penalidades**), sem emissão de juízos de risco prematuros.
- **Output Intermediário 1 ([`agent/output_etapa1_decomposicao.json`](agent/output_etapa1_decomposicao.json)):**
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

### 🔹 Etapa 2: *Chain-of-Thought (CoT)* (Resolução Factual e Invocação de Tools)
- **Técnica:** O modelo segue o encadeamento: `Constatação Fática ➔ Raciocínio Passo a Passo ➔ Invocação de Tool Algorítmica ➔ Parâmetro Normalizado`.
- **Output Intermediário 2 ([`agent/output_etapa2_cot.json`](agent/output_etapa2_cot.json)):**
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

### 🔹 Etapa 3: Síntese e Emissão Tipada (Payload para o Agente 2)
- **Output Consolidado ([`agent/resultado_pipeline_raciocinio.json`](agent/resultado_pipeline_raciocinio.json) e [`agent/parecer_auditoria_raciocinio.md`](agent/parecer_auditoria_raciocinio.md)):**
  - Objeto `DadosContratoExtraido` sanitizado, gerando o relatório técnico de extração e fornecendo a base de dados estruturada que o **Agente 2 (Avaliador de Risco)** consumirá no futuro.

---

## 🧠 4. Memória Persistente e Busca Semântica

Implementada no módulo [`agent/memoria_rag.py`](agent/memoria_rag.py) e comprovada em [`agent/demo_memoria_rag.py`](agent/demo_memoria_rag.py):

### 4.1 Continuidade de Sessão (`SQLiteSession`)
- **Protocolo:** Herda de `SessionABC` do OpenAI Agents SDK.
- **Banco:** [`agent/banco_memoria_contratos.db`](agent/banco_memoria_contratos.db), tabela `sessoes_historico`.
- **Comprovação:** Na Run 1, o Diretor Jurídico instrui: *"O teto de multa deve ser 10% e o foro deve ser São Paulo/SP"*. Na Run 2 (processo independente), o agente recupera o histórico e responde perfeitamente sem reintrodução das diretrizes.

### 4.2 Recuperação Semântica em Sessão Nova (Cross-Session RAG)
- Em uma **sessão virgem** sem histórico prévio, o usuário questiona se a TechSolutions já negociou multa rescisória com a Alfa Consultoria no passado.
- O agente dispara a tool `buscar_precedentes_contratuais_rag`, localiza o documento **`PRECEDENTE-ALFA-2025-01`** (Aditivo de 2025 que reduziu a multa de 20% para 10%) com **similaridade de cosseno de 0.6525** e formula uma resposta contextualizada.

---

## 🛡️ 5. Saídas Tipadas e Validadas com Pydantic v2 e Tools

No módulo [`agent/demo_saida_tipada.py`](agent/demo_saida_tipada.py), combinamos `tools` e `output_type=DadosContratoExtraido`. A validação estrutural é assegurada pelo modelo Pydantic v2 com validações granulares:

- **`titulo: str`**: Título oficial do contrato extraído.
- **`contratante` / `contratada: ParteContratante`**: Razão Social e CNPJ validados via `@field_validator` (14 dígitos).
- **`financeiro: CronogramaFinanceiro`**: Preenchido via tool `extrair_e_validar_tabela_financeira`, com ateste de `soma_consistente: true`.
- **`vigencia: PeriodoVigencia`**: Preenchido via tool `normalizar_prazos_e_datas`, com datas `data_inicio_iso` e `data_fim_calculada_iso`.
- **`penalidades: ClausulaPenal`**: Dados da multa rescisória e gatilho de aplicação preservados fielmente para análise posterior.

- **Verificação via `result.final_output`:**
```text
[OK] Tipo do objeto final: <class 'DadosContratoExtraido'>
[OK] É instância de DadosContratoExtraido: True
[OK] Cronograma financeiro consistente: True (12 parcelas de R$ 10,000.00)
[OK] Vigência normalizada: De 2026-01-15 a 2027-01-15 (365 dias corridos)
```
- **Output JSON Validado:** [`agent/resultado_saida_tipada.json`](agent/resultado_saida_tipada.json).

---

## 📊 6. Avaliação A/B e Ciclo Prompt-Response-Reflect-Revise (evaluation/)

Implementado em [`evaluation/avaliacao_metricas_prompt.py`](evaluation/avaliacao_metricas_prompt.py) e [`evaluation/comparativo_variantes_prrr.md`](evaluation/comparativo_variantes_prrr.md):

### 6.1 Benchmark Comparativo
- **Variante A (Prompt Monolítico):** Texto livre, sem tools e sem schema estrito.
- **Variante B (Prompt Estruturado + CoT + Tools + Pydantic v2):** Prompt anatômico com tools forçadas e tipagem estrita.

| Métrica | Variante A (Prompt Básico) | Variante B (Estruturado + Tools) | Diferencial |
| :--- | :---: | :---: | :---: |
| **Taxa de Conformidade de Schema (TCS)** | `0.00` | `1.00` | **+1.00** |
| **Taxa de Invocação de Tools (TIT)** | `0.00` | `1.00` | **+1.00** |
| **Acurácia Factual dos Campos (AFC)** | `0.50` | `1.00` | **+0.50** |
| **Acurácia na Detecção de Risco (ARA)** | `0.50` | `1.00` | **+0.50** |
| **Índice Geral de Qualidade (IGQ)** | **`0.200`** | **`1.000`** | **+0.800 (+400%)** |

> **Decisão Justificada:** Adoção mandatória da **Variante B**. A Variante A gerou texto livre sem validação de schema (TCS=0.00), não acionou tools (TIT=0.00) e não calculou prazos no calendário ISO nem conferiu consistência financeira (ASC=0.00). A Variante B alcançou pontuação máxima (IGQ=1.00).

### 6.2 Ciclo Prompt-Response-Reflect-Revise (PRRR)
1. **Prompt (V1):** Solicitação genérica em texto livre.
2. **Response (V1):** Retornou texto corrido sem converter datas nem verificar as parcelas.
3. **Reflect:** Constatada a incapacidade do modelo isolado de calcular a data de término no calendário internacional e atestar a consistência matemática das parcelas.
4. **Revise (V2):** Aplicação de anatomia completa, imposição das tools de cálculo e validação via `DadosContratoExtraido` (Pydantic v2), elevando o IGQ para 1.000.

---

## 📂 7. Estrutura Organizada do Repositório GitHub

O repositório está organizado segundo as diretrizes exigidas:

```
agente-analise-de-contratos/
├── agent/                                  # Código-fonte principal do agente
│   ├── agente_extracao.py                  # Agente com tools e Runner SDK
│   ├── tools.py                            # Ferramentas Python com @function_tool
│   ├── memoria_rag.py                      # SQLiteSession + Pipeline RAG vetorial
│   ├── pipeline_raciocinio.py              # Prompt Chaining + CoT + Least-to-Most
│   ├── demo_memoria_rag.py                 # Script de demonstração da memória e RAG
│   ├── demo_saida_tipada.py                # Script com tools + output_type Pydantic
│   ├── contrato_exemplo.txt                # Minuta contratual para testes
│   ├── banco_memoria_contratos.db          # Banco SQLite de sessões e vetores
│   ├── resultado_extracao.json             # Saída estruturada do agente
│   └── resultado_saida_tipada.json         # Saída tipada e validada pelo Pydantic
│
├── prompts/                                # Prompts encadeados e outputs intermediários
│   ├── prompts_encadeados.md               # Sequência completa documentada
│   ├── prompts_anatomia.md                 # Decomposição anatômica do prompt
│   ├── saidas_estruturadas.md              # Documentação das saídas estruturadas
│   ├── output_etapa1_decomposicao.json     # Output da Etapa 1 (Least-to-Most)
│   ├── output_etapa2_cot.json              # Output da Etapa 2 (Chain-of-Thought)
│   └── resultado_pipeline_raciocinio.json  # Output final consolidado do pipeline
│
├── evaluation/                             # Avaliação A/B e ciclo PRRR
│   ├── comparativo_variantes_prrr.md       # Relatório de benchmark A/B e ciclo PRRR
│   ├── avaliacao_metricas_prompt.py        # Script de medição de métricas (TCS, TIT, AFC, ARA)
│   └── resultado_avaliacao_metricas.json   # Dados quantitativos medidos no benchmark
│
├── spec/                                   # Especificações técnicas de engenharia
│   ├── especificacao_projeto.md            # Especificação arquitetural do projeto
│   ├── implementacao_ferramentas.md        # Documentação de implementação das tools
│   ├── memoria_persistente_rag.md          # Documentação de SQLiteSession e RAG
│   ├── pipeline_raciocinio_etapas.md       # Documentação de Prompt Chaining e CoT
│   └── saidas_tipadas_pydantic.md          # Documentação de saídas tipadas Pydantic v2
│
├── diagrama.md                             # Diagrama da arquitetura atualizada
├── diagrama.png                            # Imagem renderizada da arquitetura
└── RELATORIO_TECNICO.md                    # Este relatório técnico consolidado
```
