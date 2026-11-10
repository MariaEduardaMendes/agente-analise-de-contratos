# Relatório Técnico Unificado de Evolução do Sistema Multi-Agente de Análise de Contratos

**Projeto de Bloco — Desenvolvimento de Agentes Inteligentes**  
**Autora:** Maria Eduarda Mendes  
**Repositório Oficial no GitHub:** [https://github.com/MariaEduardaMendes/agente-analise-de-contratos](https://github.com/MariaEduardaMendes/agente-analise-de-contratos)  
**Versão:** TP3 Consolidado com Atendimento Integral aos Feedbacks de TP2 e TP3 (Rubrica 12, Agentes Reais via Runner.run, Fonte Estruturada de Negócio e Avaliação A/B Real)  
**Data:** 10/11/2026  
**Status:** Implementado, Testado com Modelo Real e Homologado  

---

## 🧭 1. Visão Geral da Arquitetura e Evolução Histórica (TP1 ➔ TP2 ➔ TP3)

O projeto de análise e auditoria inteligente de contratos foi estruturado em um ciclo evolutivo rigoroso:

```
┌─────────────────────────┐     ┌─────────────────────────┐     ┌─────────────────────────┐
│           TP1           │ ──> │           TP2           │ ──> │           TP3           │
│   Script Python Básico  │     │  Agente com Ferramentas,│     │  Dois Microsserviços    │
│   e Extração Inicial    │     │  CoT, RAG e Pydantic v2 │     │  FastAPI, CLAUDE.md e   │
│   em Texto Livre        │     │  (OpenAI Agents SDK)    │     │  Workflow Inicial n8n   │
└─────────────────────────┘     └─────────────────────────┘     └─────────────────────────┘
```

1. **Fase TP1 (Componente Inicial):** Script Python elementar que consumia minutas contratuais e produzia JSONs simples, sujeito a alucinações de cálculo e vigência temporal relativa.
2. **Fase TP2 (Agente Inteligente e Funcional com Execução Real):**
   - Implementação de ferramentas Python determinísticas decoradas com `@function_tool` (cálculo de datas ISO-8601, integridade de parcelas e consulta a cadastro de fornecedores).
   - Decomposição de tarefas complexas através de *Least-to-Most Prompting* e raciocínio deliberativo (*Chain-of-Thought*) enviados de verdade ao modelo LLM via `Runner.run`.
   - Dupla camada de memória persistente: `SQLiteSession` para retenção de histórico conversacional entre runs distintos e RAG vetorial com embeddings (`text-embedding-3-small`) sobre a tabela `rag_documentos` para recuperação de precedentes.
   - Saídas fortemente tipadas com validação estrutural via **Pydantic v2** (`DadosContratoExtraido`).
   - Benchmark A/B real comparando variantes executadas via API.
3. **Fase TP3 (Arquitetura Multi-Agente Desacoplada e Orquestração):**
   - **Agente 1 em Microsserviço REST:** Transformação do extrator em serviço HTTP com **FastAPI** e **`BackgroundTasks`**, respondendo `POST /run` com `202 Accepted` imediato e polling em `GET /status/{task_id}`, lendo dinamicamente minutas reais através do `Runner.run`.
   - **Segundo Agente Independente (Agente 2):** Implementação de um microsserviço isolado (`agent2/`) especializado em **Auditoria de Conformidade e Risco**, transformado em um **Agent inteligente real** com `@function_tool auditar_parametros_contratuais`, Pydantic v2 (`output_type=RelatorioConformidade`) e API FastAPI na porta `8002`.
   - **Context Engineering Descentralizado:** Arquivos `CLAUDE.md` exclusivos em cada pasta de agente (`agent1/CLAUDE.md` e `agent2/CLAUDE.md`), sem arquivos globais acoplados na raiz.
   - **Primeiro Workflow n8n:** Demonstração operacional de disparo assíncrono e captura de resposta via nó HTTP no n8n (`workflows/workflow_tp3_agente_extracao.json`).
   - **Consolidação Final do Pipeline de Prompts:** Avaliação quantitativa com 4 métricas (TCS, TIT, AFC, ASC, IGQ) sobre execuções reais do modelo.

---

## 📌 2. Atendimento aos Feedbacks de TP2 e TP3 (Rubrica 12 e Agentes Reais)

Em resposta aos apontamentos da banca avaliadora, todas as deficiências foram integralmente sanadas com implementações e execuções reais:

### 2.1 Correção dos Agentes: Fim das Simulações e Execução Real com `Runner.run`
- **Problema Apontado:** Memória, raciocínio encadeado, saídas tipadas e avaliação haviam sido demonstrados com valores fixos em código, sem chamar o modelo LLM no runtime.
- **Solução Implementada:**
  - O Agente 1 ([`agent1/agente_extracao.py`](agent1/agente_extracao.py)) agora executa o LLM real via `Runner.run_sync(agente, ...)` utilizando o `OpenAIChatCompletionsModel` conectado ao OpenRouter (`nvidia/nemotron-3.5-lightning:free`). Ele lê e extrai os dados diretamente da minuta fornecida (e não de valores estáticos). Testes com duas minutas distintas (`contrato_exemplo.txt` e `contrato_exemplo_2.txt`) comprovam que o agente extrai valores e partes diferentes dinamicamente.
  - O Agente 2 ([`agent2/agente_auditoria.py`](agent2/agente_auditoria.py)) foi transformado de uma função estática em um **Agent completo** (`AgenteAuditoriaRisco`) que executa via `Runner.run`, aciona a tool `@function_tool auditar_parametros_contratuais` e gera a saída tipada `RelatorioConformidade`.
  - O módulo de memória persistente ([`agent1/demo_memoria_rag.py`](agent1/demo_memoria_rag.py)) passa a sessão `SQLiteSession` no `Runner.run(agent, ..., session=session)` tanto no Run 1 quanto no Run 2, comprovando que o modelo recupera as diretrizes prévias diretamente do banco SQLite.
  - O pipeline de raciocínio encadeado ([`agent1/pipeline_raciocinio.py`](agent1/pipeline_raciocinio.py)) envia os prompts das etapas *Least-to-Most* e *Chain-of-Thought* diretamente ao modelo LLM.

### 2.2 Atendimento da Rubrica 12: Os 3 Entregáveis Adicionais

#### A) Fonte Estruturada de Negócio
- **Exigência da Rubrica 12:** Uma fonte de dados de negócio em banco relacional ou API (como cadastro de fornecedores ou de contratos), visto que tools de cálculo e banco vetorial não cumprem esse papel.
- **Implementação:** Criada a tabela corporativa **`cadastro_fornecedores`** no banco SQLite (`agent1/banco_memoria_contratos.db`), armazenando dados cadastrais, situação fiscal, limite de alçada homologado e histórico de compliance.
- **Integração:** Disponibilizada a ferramenta `@function_tool consultar_cadastro_fornecedor(cnpj_cpf: str) -> str` no Agente 1, permitindo confrontar a Contratada extraída da minuta contra o cadastro corporativo.

#### B) Dado Estruturado com Documentação Alinhada ao Banco Real
- **Exigência da Rubrica 12:** Documentar os campos da fonte de negócio e alinhar as tabelas com o banco de dados real (`rag_documentos`, e não `precedentes_contratuais`).
- **Implementação:** O banco `banco_memoria_contratos.db` possui 3 tabelas reais documentadas com precisão na Seção 6 deste relatório:
  1. `cadastro_fornecedores`: Fonte estruturada relacional de negócio.
  2. `rag_documentos`: Vector store com embeddings e metadados (corrigindo a nomenclatura antiga).
  3. `sessoes_historico`: Histórico de conversação da `SQLiteSession`.

#### C) Fluxo de Dados com Pergunta de Dupla Intenção
- **Exigência da Rubrica 12:** Um exemplo concreto com pergunta de dupla intenção que acione os dois agentes e apresente dados reais em cada etapa.
- **Implementação:** Detalhado na Seção 5 deste relatório, demonstrando a pergunta de dupla intenção ("extrair dados da minuta E verificar cadastro corporativo e conformidade de multa"), com os payloads JSON concretos produzidos em cada estágio.

---

## 🏛️ 3. Mapeamento da Estrutura de Pastas do Repositório

```text
agente-analise-de-contratos/
├── RELATORIO_TECNICO.md            # Este Relatório Técnico Unificado Oficial
├── README.md                       # Documentação e guia de inicialização
├── diagrama.md                     # Especificação arquitetural e diagrama Mermaid
├── diagrama.png                    # Diagrama formal da arquitetura multi-agente
│
├── agent1/                         # PRIMEIRO AGENTE (Extrator Enriquecido de Contratos)
│   ├── CLAUDE.md                   # Contexto e regras exclusivas do Agente 1
│   ├── main.py                     # Microsserviço FastAPI (Porta 8001) com BackgroundTasks
│   ├── agente_extracao.py          # Pipeline de extração estruturada via LLM Real + Runner.run
│   ├── tools.py                    # Ferramentas Python (@function_tool) de prazos, finanças e cadastro
│   ├── models.py                   # Schemas Pydantic v2 (DadosContratoExtraido)
│   ├── memoria_rag.py              # Memória de sessão SQLite, banco relacional e RAG vetorial
│   ├── banco_memoria_contratos.db  # Banco SQLite (cadastro_fornecedores, rag_documentos, sessoes)
│   ├── contrato_exemplo.txt        # Minuta jurídica 1 (TechSolutions e Alfa Consultoria, R$ 45k)
│   ├── contrato_exemplo_2.txt      # Minuta jurídica 2 (TechSolutions e CloudCorp, R$ 180k)
│   ├── pipeline_raciocinio.py      # Pipeline CoT e Least-to-Most com chamadas reais ao LLM
│   ├── demo_memoria_rag.py         # Validação de SQLiteSession e RAG com chamadas reais
│   ├── test_api.py                 # Testes automatizados dos endpoints REST (:8001)
│   └── requirements.txt            # Dependências específicas do Agente 1
│
├── agent2/                         # SEGUNDO AGENTE (Avaliador de Conformidade e Risco)
│   ├── CLAUDE.md                   # Contexto e regras exclusivas do Agente 2
│   ├── main.py                     # Microsserviço FastAPI (Porta 8002) com BackgroundTasks
│   ├── agente_auditoria.py         # Motor inteligente de auditoria com Agent e Runner.run
│   ├── tools.py                    # Ferramenta @function_tool auditar_parametros_contratuais
│   ├── models.py                   # Schemas Pydantic v2 (RelatorioConformidade)
│   ├── test_api.py                 # Testes automatizados dos endpoints REST (:8002)
│   └── requirements.txt            # Dependências específicas do Agente 2
│
├── workflows/                      # WORKFLOWS DO N8N
│   └── workflow_tp3_agente_extracao.json # Workflow oficial homologado no n8n
│
├── evaluation/                     # PIPELINE DE PROMPTS E AVALIAÇÃO
│   ├── avaliacao_metricas_prompt.py # Benchmark A/B real com modelo LLM
│   ├── comparativo_variantes_prrr.md # Documentação do ciclo PRRR e métricas
│   ├── PIPELINE_PROMPTS_CONSOLIDADO.md # Diagnóstico técnico e decisão de prompts
│   └── resultado_avaliacao_metricas.json # Resultados quantitativos gravados
│
└── integration/                    # CONTRATOS DE INTERFACE E APIS
    └── contrato_api_agentes.md     # Especificação técnica dos endpoints e payloads
```

---

## 🔌 4. Documentação das APIs REST dos Dois Agentes

Ambos os agentes operam como microsserviços HTTP padronizados usando **FastAPI** e **`BackgroundTasks`**, garantindo execução não-bloqueante com o padrão **`202 Accepted`** e polling em `/status/{task_id}`.

### 4.1 Agente 1: Extrator Enriquecido de Contratos (Porta `8001`)

- **Endpoints:**
  - `POST /run`: Dispara a extração assíncrona recebendo `{"texto_contrato": "..."}`. Retorna `202 Accepted` com `task_id`.
  - `GET /status/{task_id}`: Retorna status (`pending`, `done`, `error`) e o payload validado `DadosContratoExtraido`.
  - `GET /health`: Healthcheck do serviço.

- **Payload Real de Saída (`GET /status/{task_id}`) gerado pelo Agente 1:**
```json
{
  "task_id": "853f61da-d864-4b62-8579-b77130c85501",
  "status": "done",
  "created_at": 1794338422.51,
  "completed_at": 1794338436.51,
  "data": {
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
    "objeto": "Prestação de serviços técnicos especializados para o desenvolvimento, integração e suporte de um sistema de inteligência artificial multi-agentes focado em análise de conformidade e extração de dados de documentos jurídicos.",
    "financeiro": {
      "moeda": "BRL",
      "valor_total_brl": 45000.0,
      "parcelas_quantidade": 3,
      "valor_parcela_brl": 15000.0,
      "periodicidade": "mensal",
      "soma_consistente": true,
      "discrepancia_centavos": 0.0,
      "cronograma_resumo": "3 parcelas de R$ 15.000,00, primeira em 15/09/2026"
    },
    "vigencia": {
      "data_inicio_iso": "2026-09-01",
      "data_fim_calculada_iso": "2027-03-01",
      "vigencia_meses": 6,
      "dias_corridos_totais": 181,
      "aviso_previo_dias": 30,
      "vigencia_formatada": "01/09/2026 a 01/03/2027"
    },
    "penalidades": {
      "percentual_multa_rescisoria": 20.0,
      "base_calculo": "valor remanescente do contrato",
      "gatilho_aplicacao": "rescisão imotivada"
    },
    "fornecedor_homologado": {
      "cnpj": "98.765.432/0001-10",
      "razao_social": "Alfa Consultoria em IA S.A.",
      "situacao_cadastral": "ATIVA",
      "score_compliance": 88.5,
      "limite_alcada_brl": 150000.0,
      "categoria_risco": "MEDIO",
      "restricoes_juridicas": "Histórico de renegociação de multa rescisória em aditivo prévio (2025). Homologada com ressalva contratual."
    },
    "secoes_analisadas": ["PREAMBULO", "OBJETO", "CONDICOES_FINANCEIRAS", "PRAZOS_E_VIGENCIA", "PENALIDADES"]
  },
  "error": null
}
```

---

### 4.2 Agente 2: Avaliador de Conformidade e Risco (Porta `8002`)

- **Endpoints:**
  - `POST /run`: Dispara a auditoria assíncrona recebendo `{"dados_contrato": {...}}`. Retorna `202 Accepted` com `task_id`.
  - `GET /status/{task_id}`: Retorna status e o modelo tipado `RelatorioConformidade`.
  - `GET /health`: Healthcheck do serviço.

- **Payload Real de Saída (`GET /status/{task_id}`) gerado pelo Agente 2:**
```json
{
  "task_id": "0a9ff2c9-a1f8-4cf9-a982-334839496eac",
  "status": "done",
  "created_at": 1794338663.58,
  "completed_at": 1794338686.55,
  "data": {
    "contrato_titulo": "CONTRATO DE PRESTAÇÃO DE SERVIÇOS DE DESENVOLVIMENTO DE INTELIGÊNCIA ARTIFICIAL",
    "score_conformidade": 85.0,
    "nivel_risco_geral": "MEDIO",
    "total_regras_auditadas": 4,
    "itens_conformes": 3,
    "itens_alerta": 1,
    "itens_nao_conformes": 0,
    "itens_auditados": [
      {
        "regra": "Teto de Multa Rescisória",
        "status": "ALERTA",
        "nivel_risco": "MEDIO",
        "descricao_analise": "Multa rescisória fixada em 20.0%, superando a diretriz de governança recomendada de até 10.0% sobre o saldo remanescente.",
        "fundamentacao": "Política Interna de Riscos Contratuais e Jurisprudência Cível (Art. 413 CC)."
      },
      {
        "regra": "Alçada de Aprovação Financeira",
        "status": "CONFORME",
        "nivel_risco": "BAIXO",
        "descricao_analise": "Valor de R$ 45.000,00 dentro da alçada operacional regular (abaixo de R$ 100.000,00).",
        "fundamentacao": "Manual de Alçadas e Governança Financeira."
      },
      {
        "regra": "Prazo Mínimo de Aviso Prévio",
        "status": "CONFORME",
        "nivel_risco": "BAIXO",
        "descricao_analise": "Aviso prévio pactuado (30 dias) atende integralmente ao requisito de segurança.",
        "fundamentacao": "Diretriz Operacional de Continuidade de Negócios."
      },
      {
        "regra": "Regularidade Cadastral do Fornecedor",
        "status": "CONFORME",
        "nivel_risco": "BAIXO",
        "descricao_analise": "Fornecedor homologado ativo com score de compliance de 88.5/100.",
        "fundamentacao": "Cadastro Corporativo de Fornecedores Homologados."
      }
    ],
    "recomendacoes_mitigacao": [
      "Negociar a redução da multa rescisória de 20% para 10%, alinhando ao precedente histórico (Aditivo nº 1 de 2025 da Alfa Consultoria).",
      "Manter o acompanhamento do fornecedor haja vista a categoria de risco MÉDIO registrada na fonte estruturada."
    ],
    "parecer_executivo_markdown": "# Parecer de Conformidade e Risco Contratual\n**Instrumento:** CONTRATO DE PRESTAÇÃO DE SERVIÇOS DE DESENVOLVIMENTO DE INTELIGÊNCIA ARTIFICIAL\n**Score de Compliance:** 85.0 / 100.0\n**Classificação de Risco:** MEDIO\n..."
  },
  "error": null
}
```

---

## 🔄 5. Fluxo de Dados com Pergunta de Dupla Intenção (Rubrica 12)

Para cumprir integralmente a Rubrica 12, demonstramos o fluxo de dados disparado por uma **pergunta de dupla intenção** que mobiliza ambos os agentes de forma encadeada e orquestrada.

### 5.1 Pergunta de Dupla Intenção
> **Pergunta:**  
> *"Por favor, extraia os dados essenciais da minuta contratual em anexo com a Alfa Consultoria em IA S.A. (valores, número de parcelas, vigência e penalidades) **E** verifique se o fornecedor possui situação cadastral regular na nossa base interna e se a multa rescisória de 20% atende às diretrizes corporativas da TechSolutions."*

### 5.2 Decomposição das Intenções e Execução dos Agentes
1. **Intenção 1 (Extração, Normalização e Consulta Cadastral):**
   - **Agente Acionado:** Agente 1 (Extrator Enriquecido).
   - **Execução Real:** O Agente 1 lê o texto da minuta, invoca a tool `normalizar_prazos_e_datas` (início `2026-09-01`, fim `2027-03-01`), invoca a tool `extrair_e_validar_tabela_financeira` (3 parcelas de R$ 15.000,00 = R$ 45.000,00) e consulta a tabela `cadastro_fornecedores` via `consultar_cadastro_fornecedor` para o CNPJ `98.765.432/0001-10`.
   - **Dado Produzido:** Payload estruturado `DadosContratoExtraido` (apresentado na subseção 4.1).
2. **Intenção 2 (Auditoria de Risco e Análise de Conformidade):**
   - **Agente Acionado:** Agente 2 (Avaliador de Risco).
   - **Execução Real:** O orquestrador repassa o JSON do Agente 1 ao Agente 2. O Agente 2 executa a tool `@function_tool auditar_parametros_contratuais`, identifica que a multa de 20% ultrapassa o teto de 10% corporativo (gerando ALERTA), confirma que o valor de R$ 45.000,00 está dentro da alçada e valida que o fornecedor está ATIVO com score 88.5/100.
   - **Dado Produzido:** Relatório executivo tipado `RelatorioConformidade` (apresentado na subseção 4.2).

### 5.3 Resposta Final Consolidada Entregue ao Usuário
```markdown
### Síntese da Análise Contratual (Dupla Intenção Atendida)

**1. Dados Extraídos do Contrato:**
- **Partes:** TechSolutions Ltda. (Contratante) e Alfa Consultoria em IA S.A. (Contratada - CNPJ 98.765.432/0001-10).
- **Objeto:** Desenvolvimento, integração e suporte de sistema de inteligência artificial multi-agentes.
- **Condições Financeiras:** R$ 45.000,00 em 3 parcelas mensais de R$ 15.000,00 (100% íntegro matematicamente).
- **Vigência:** 6 meses, de 01/09/2026 a 01/03/2027 (181 dias corridos), aviso prévio de 30 dias.
- **Penalidade Contratual:** Multa de 20% sobre o saldo remanescente em caso de rescisão imotivada.

**2. Diagnóstico de Governança e Cadastro Corporativo:**
- **Situação do Fornecedor:** O fornecedor Alfa Consultoria em IA S.A. está **ATIVO** na base estruturada corporativa com Score de Compliance de **88.5/100** e limite de alçada homologado de R$ 150.000,00.
- **Auditoria de Multa Rescisória:** **ALERTA (Risco Médio)**. A multa proposta de 20% excede o teto corporativo tolerado de 10%.
- **Recomendação:** Negociar a redução da multa para 10%, aplicando o precedente corporativo registrado no Aditivo nº 1 de 2025 já firmado com a própria Alfa Consultoria.
```

---

## 💾 6. Dados Estruturados (Tabelas Reais no SQLite)

O banco relacional do sistema está localizado em:  
📂 **`agent1/banco_memoria_contratos.db`**

### 6.1 Tabela `cadastro_fornecedores` (Fonte Estruturada de Negócio)
Armazena a base cadastral corporativa homologada:

```sql
CREATE TABLE IF NOT EXISTS cadastro_fornecedores (
    cnpj TEXT PRIMARY KEY,
    razao_social TEXT NOT NULL,
    nome_fantasia TEXT,
    situacao_cadastral TEXT NOT NULL,
    score_compliance REAL NOT NULL,
    limite_alcada_brl REAL NOT NULL,
    categoria_risco TEXT NOT NULL,
    data_homologacao TEXT NOT NULL,
    restricoes_juridicas TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

- **Registros Homologados:**
  1. `98.765.432/0001-10` — *Alfa Consultoria em IA S.A.* (Ativa, Score 88.5, Alçada R$ 150k, Risco Médio).
  2. `12.345.678/0001-90` — *TechSolutions Ltda.* (Ativa, Score 96.0, Alçada R$ 500k, Risco Baixo).
  3. `23.456.789/0001-01` — *CloudCorp Soluções Digitais Ltda.* (Ativa, Score 91.0, Alçada R$ 300k, Risco Baixo).
  4. `99.888.777/0001-66` — *FraudeTech Serviços Suspensos ME* (Suspensa no CEIS, Score 25.0, Alçada R$ 0, Risco Alto).

### 6.2 Tabela `rag_documentos` (Vector Store com Embeddings)
> [!NOTE]
> A tabela do banco SQLite responsável pela busca semântica é denominada **`rag_documentos`** (e não `precedentes_contratuais`, alinhando a documentação rigorosamente com o código).

```sql
CREATE TABLE IF NOT EXISTS rag_documentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    documento_id TEXT UNIQUE NOT NULL,
    titulo TEXT NOT NULL,
    conteudo TEXT NOT NULL,
    categoria TEXT NOT NULL,
    metadados TEXT NOT NULL,
    vetor_embedding TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 6.3 Tabela `sessoes_historico` (Memória Persistente SQLiteSession)
Mantém o histórico conversacional da `SQLiteSession`:

```sql
CREATE TABLE IF NOT EXISTS sessoes_historico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    item_data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔬 7. Consolidação Definitiva do Pipeline de Prompts e Avaliação A/B Real

O benchmark comparativo foi refeito com **execuções 100% REAIS** através do script [`evaluation/avaliacao_metricas_prompt.py`](evaluation/avaliacao_metricas_prompt.py) sobre a minuta real [`agent1/contrato_exemplo.txt`](agent1/contrato_exemplo.txt):

### 7.1 Métricas Utilizadas

$$\text{IGQ} = (0.30 \times \text{TCS}) + (0.30 \times \text{TIT}) + (0.20 \times \text{AFC}) + (0.20 \times \text{ASC})$$

### 7.2 Tabela de Resultados Reais Gravados

| Métrica | Variante A (Prompt Monolítico / LLM Real) | Variante B (Agente Estruturado + Tools / Runner.run) | Ganho |
| :--- | :---: | :---: | :---: |
| **TCS** (Conformidade de Schema) | `0.00` | `1.00` | **+1.00** |
| **TIT** (Invocação de Ferramentas) | `0.00` | `1.00` | **+1.00** |
| **AFC** (Acurácia Factual) | `1.00` | `1.00` | **0.00** |
| **ASC** (Sanitização e Cálculo) | `0.00` | `1.00` | **+1.00** |
| **Índice Geral de Qualidade (IGQ)** | **`0.200`** | **`1.000`** | **+0.800 (+400%)** |

- **Decisão Técnica Justificada:** Adoção mandatória da Variante B. Enquanto a Variante A produz prosa livre que não aciona ferramentas nem gera chaves consumíveis por APIs, a Variante B atinge conformidade total (IGQ = 1.000) e alimenta deterministicamente o Agente 2.

---

## 🔄 8. Workflow n8n Homologado ([`workflows/workflow_tp3_agente_extracao.json`](workflows/workflow_tp3_agente_extracao.json))

1. **Trigger:** `When clicking ‘Execute workflow’`.
2. **Nó `HTTP Request` (`POST /run`):** Envia a minuta para o Agente 1 e recebe `202 Accepted` imediato com `task_id`.
3. **Nó `Wait`:** Aguarda 2 segundos para processamento em background.
4. **Nó `HTTP Request1` (`GET /status/{task_id}`):** Consulta o status e captura o payload `DadosContratoExtraido`.

---

## 🏆 9. Checklist Consolidado de Entregáveis

| Entregável | Localização no Repositório | Status |
| :--- | :--- | :---: |
| **Agente 1 Real (Runner.run + Tools + Pydantic v2)** | [`agent1/agente_extracao.py`](agent1/agente_extracao.py) | ✅ Validado com Modelo Real |
| **Agente 2 Real (Runner.run + @function_tool + RelatorioConformidade)** | [`agent2/agente_auditoria.py`](agent2/agente_auditoria.py) | ✅ Validado com Modelo Real |
| **Fonte Estruturada de Negócio (`cadastro_fornecedores`)** | [`agent1/memoria_rag.py`](agent1/memoria_rag.py) | ✅ Banco SQLite Populado |
| **Fluxo com Pergunta de Dupla Intenção e Dados Concretos** | [`diagrama.md`](diagrama.md) e [`RELATORIO_TECNICO.md`](RELATORIO_TECNICO.md) | ✅ Documentado |
| **Dado Estruturado com Documentação Alinhada (`rag_documentos`)** | [`diagrama.md`](diagrama.md) e [`RELATORIO_TECNICO.md`](RELATORIO_TECNICO.md) | ✅ Alinhado ao Banco Real |
| **Memória Persistente SQLiteSession (Runner.run com session)** | [`agent1/demo_memoria_rag.py`](agent1/demo_memoria_rag.py) | ✅ Validado com Modelo Real |
| **Raciocínio Encadeado Least-to-Most + CoT com LLM Real** | [`agent1/pipeline_raciocinio.py`](agent1/pipeline_raciocinio.py) | ✅ Validado com Modelo Real |
| **Benchmark A/B Real com Métricas e JSON** | [`evaluation/avaliacao_metricas_prompt.py`](evaluation/avaliacao_metricas_prompt.py) | ✅ Executado e Salvo |
| **APIs REST FastAPI com BackgroundTasks e Testes** | [`agent1/test_api.py`](agent1/test_api.py), [`agent2/test_api.py`](agent2/test_api.py) | ✅ 100% Aprovados |
| **CLAUDE.md por Agente (Context Engineering)** | [`agent1/CLAUDE.md`](agent1/CLAUDE.md), [`agent2/CLAUDE.md`](agent2/CLAUDE.md) | ✅ Concluído |
| **Workflow n8n Exportado** | [`workflows/workflow_tp3_agente_extracao.json`](workflows/workflow_tp3_agente_extracao.json) | ✅ Exportado |
| **Contrato de API e Interfaces** | [`integration/contrato_api_agentes.md`](integration/contrato_api_agentes.md) | ✅ Concluído |
