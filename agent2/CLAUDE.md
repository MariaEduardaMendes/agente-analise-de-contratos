# CLAUDE.md — Agente 2: Avaliador de Conformidade e Risco Contratual

Este arquivo define o contrato de contexto, regras operacionais e especificações técnicas exclusivas do **Agente 2 (Avaliador de Conformidade e Risco)**.

---

## 1. Responsabilidade e Fronteiras de Atuação (Role & Boundary)

O **Agente 2** é um microsserviço especializado em **Auditoria de Governança, Compliance e Análise de Risco Contratual**.

### O que o Agente 2 FAZ:
- Recebe os dados já estruturados do contrato via HTTP (payload JSON entregue pelo orquestrador **n8n**).
- Confronta valores, prazos, penalidades e alçadas contra a base corporativa de regras de negócio.
- Executa ferramentas determinísticas em Python para cálculo de score de conformidade e detecção de violações normativas.
- Emite parecer executivo estruturado e fortemente tipado com **Pydantic v2** (`RelatorioConformidade`).
- Expõe endpoints assíncronos (`POST /run` com `202 Accepted` e `GET /status/{task_id}`) para orquestração externa determinística via **n8n**.

### O que o Agente 2 NÃO FAZ (Fronteira Estrita):
- **NÃO** processa texto bruto de minutas contratuais e **NÃO** faz extração de entidades (essa é a atribuição exclusiva do **Agente 1**).
- **NÃO** chama o Agente 1 diretamente nem depende de acoplamento em código com ele. Toda orquestração é realizada externamente pelo **n8n**.

---

## 2. Hierarquia e Estrutura de Arquivos

```text
agent2/
├── CLAUDE.md              # Este arquivo: fonte de verdade e especificações do Agente 2
├── AGENTS.md              # Espelho canônico de especificações do Agente 2
├── main.py                # Serviço REST FastAPI com BackgroundTasks (/run e /status)
├── agente_auditoria.py     # Agente de auditoria com OpenAI Agents SDK e Runner.run
├── subagente_penalidades.py # Subagente com isolamento de contexto para auditoria de cláusulas penais
├── tools.py               # Ferramentas determinísticas Python de conformidade e alçada
├── models.py              # Schemas e validações estruturais tipadas com Pydantic v2
├── test_api.py            # Suíte de testes automatizados dos endpoints REST
├── requirements.txt       # Dependências Python específicas do microsserviço
├── .claude/               # Governança formal: settings.json, hooks, skills e agents
│   ├── settings.json      # Permissões allow, deny e ask (schema oficial Claude Code)
│   ├── hooks/             # Scripts de PreToolUse e PostToolUse (exit code 2 em bloqueio)
│   ├── skills/            # Skills descobertas pelo Claude Code (.claude/skills/)
│   │   └── auditoria-alcada-e-multa/
│   │       └── SKILL.md
│   └── agents/            # Subagentes descobertos pelo Claude Code (.claude/agents/)
│       └── auditor-clausulas-penais.md
├── skills/                # Espelho estruturado de skills do agente
│   └── auditoria-alcada-e-multa/
│       └── SKILL.md       # Regras de governança de alçadas, multas e mitigações
└── subagents/             # Documentação e especificação de subagentes isolados
    ├── README.md          # Justificativa do isolamento de contexto
    └── especialista_clausulas_penais.md # Definição YAML do subagente de penalidades
```

---

## 3. Ferramentas Python Integradas (`tools.py`)

1. **`auditar_parametros_contratuais` (`@function_tool`)**:
   - *Finalidade:* Realiza a auditoria determinística de parâmetros contratuais contra as diretrizes corporativas, acionada diretamente pelo Agent via OpenAI Agents SDK:
     - Teto de multa rescisória (alerta caso supere 10.0%).
     - Limite de alçada para aprovação financeira (exige ratificação da Diretoria Executiva acima de R$ 100.000,00).
     - Prazo mínimo de aviso prévio (mínimo de 30 dias).
     - Verificação da regularidade cadastral e score de compliance na fonte estruturada de fornecedores.
   - *Assinatura:* `(valor_total_brl: float, vigencia_meses: int, aviso_previo_dias: int, percentual_multa: float, situacao_fornecedor: str = "ATIVA", score_compliance_fornecedor: float = 90.0) -> str (JSON)`

2. **`consultar_base_regras_negocio_fn`**:
   - *Finalidade:* Fornece os parâmetros vigentes da política interna de riscos e compliance.

3. **Arquitetura do Agente 2:**
   - Instanciado como `Agent(name="AgenteAuditoriaRisco", tools=[auditar_parametros_contratuais], output_type=RelatorioConformidade)`.
   - Executa via `Runner.run` para interpretar o diagnóstico da tool, classificar o risco e redigir o parecer executivo em Markdown.

---

## 4. Contratos de API REST (Endpoints)

O serviço é exposto via **FastAPI** rodando por padrão na porta **`8002`** (diferenciada do Agente 1 para viabilizar execução simultânea).

### 4.1. `POST /run`
Dispara a auditoria de risco de forma assíncrona.
- **Status HTTP:** `202 Accepted`
- **Request Body (JSON):**
  ```json
  {
    "dados_contrato": {
      "titulo": "Contrato de Prestação de Serviços...",
      "financeiro": { "valor_total_brl": 120000.0 },
      "vigencia": { "vigencia_meses": 12, "aviso_previo_dias": 30 },
      "penalidades": { "percentual_multa_rescisoria": 20.0 }
    }
  }
  ```
- **Response Body (JSON):**
  ```json
  {
    "task_id": "a3344d60-8ba6-41ab-9b1a-285ada4c22b9",
    "status": "pending",
    "message": "Auditoria de conformidade iniciada com sucesso em segundo plano."
  }
  ```

### 4.2. `GET /status/{task_id}`
Consulta o progresso e o parecer tipado da auditoria.
- **Status HTTP:** `200 OK` (ou `404 Not Found` se `task_id` inexistente)
- **Response Body — Concluído (`done`):**
  ```json
  {
    "task_id": "a3344d60-8ba6-41ab-9b1a-285ada4c22b9",
    "status": "done",
    "created_at": 1792437581.50,
    "completed_at": 1792437581.51,
    "data": {
      "contrato_titulo": "Contrato de Prestação de Serviços...",
      "score_conformidade": 73.33,
      "nivel_risco_geral": "MEDIO",
      "total_regras_auditadas": 3,
      "itens_conformes": 1,
      "itens_alerta": 2,
      "itens_nao_conformes": 0,
      "itens_auditados": [
        {
          "regra": "Teto de Multa Rescisória",
          "status": "ALERTA",
          "nivel_risco": "MEDIO",
          "descricao_analise": "Multa rescisória fixada em 20.0%, superando a diretriz de governança recomendada de até 10.0%...",
          "fundamentacao": "Política Interna de Riscos Contratuais (Cap. IV, Art. 12)..."
        }
      ],
      "recomendacoes_mitigacao": [
        "Negociar redução da cláusula penal para o patamar padrão de até 10%.",
        "Submeter o contrato à assinatura conjunta da Diretoria Executiva."
      ],
      "parecer_executivo_markdown": "# Parecer de Conformidade e Risco Contratual..."
    },
    "error": null
  }
  ```

---

## 5. Estratégia de Context Engineering Adotada

1. **Separação Rígida de Conhecimento:** Este arquivo delimita expressamente que o Agente 2 opera somente sobre dados estruturados de contratos, mantendo foco na auditoria de conformidade e mitigação de risco.
2. **Contrato de Saída Tipado (`RelatorioConformidade`):** Garante invariantes de modelo via Pydantic v2 (ex: validação de que a soma dos itens auditados coincide com o total).
3. **Desacoplamento Determinístico para o n8n:** O design assíncrono via `POST /run` e polling `GET /status/{task_id}` viabiliza a orquestração limpa por nós HTTP do n8n sem dependência direta de código entre agentes.

---

## 6. Comandos Operacionais

- **Instalar Dependências:**
  ```bash
  pip install -r requirements.txt
  ```
- **Executar o Serviço FastAPI:**
  ```bash
  uvicorn main:app --host 0.0.0.0 --port 8002 --reload
  ```
- **Executar a Suíte de Testes dos Endpoints:**
  ```bash
  python test_api.py
  ```
- **Acessar Documentação Interativa:**
  Swagger UI em `http://localhost:8002/docs` e Redoc em `http://localhost:8002/redoc`.

---

## 7. Governança Formal do Claude Code: Permissões e Hooks (`.claude/settings.json`)

A especificação formal do Claude Code dentro do diretório `agent2/` é regida pelo arquivo `.claude/settings.json` e pelos scripts automatizados em `.claude/hooks/`.

### 7.1. Decisões de Permissão (Permissions Engine)
- **`allow` (Execução Autônoma):**
  - Leitura e busca de arquivos (`Read(*)`, `Glob(*)`, `Grep(*)`), comandos de inspeção (`Bash(git status*)`, `Bash(git diff*)`) e execução dos testes e motor de auditoria (`Bash(python test_api.py*)`, `Bash(python agente_auditoria.py*)`, `Bash(python subagente_penalidades.py*)`).
  - *Justificativa:* Permite depuração contínua e verificação de regras de compliance sem interrupções manuais.
- **`deny` (Bloqueio Irrevogável):**
  - Leitura, modificação ou deleção em arquivos de segredos (`Read(.env*)`, `Edit(.env*)`, `Write(.env*)`).
  - Tentativas de escrita ou modificação no diretório do Agente 1 (`Edit(../agent1/**)`, `Write(../agent1/**)`, `Edit(**/agent1/**)`, `Write(**/agent1/**)`, `Bash(*agent1*)`).
  - Comandos de terminal de alto risco (`Bash(rm -rf *)`, `Bash(del /f /q *)`, `Bash(git push --force*)`, `Bash(*DROP TABLE*)`).
  - *Justificativa:* Garante a soberania arquitetural do microsserviço de conformidade e impede acoplamento ou contaminação com o pipeline de extração.
- **`ask` (Exigência de Confirmação Humana):**
  - Edição das ferramentas de compliance (`Edit(tools.py)`, `Write(tools.py)`), alteração dos schemas de parecer (`Edit(models.py)`, `Write(models.py)`), camada HTTP (`Edit(main.py)`, `Write(main.py)`), instalação de dependências (`Bash(pip install*)`) e publicação remota (`Bash(git push*)`).
  - *Justificativa:* Políticas e parâmetros regulatórios (ex: tetos de multa de 10% e alçadas de R$ 100.000,00) representam governança corporativa e exigem aprovação explícita para alteração.

### 7.2. Hooks Automatizados e Verificáveis
1. **Hook `PreToolUse` (`.claude/hooks/pre_tool_use.py`):**
   - Configurado segundo o schema oficial (`hooks: [{type: "command", command: "python .claude/hooks/pre_tool_use.py"}]`), intercepta ferramentas de escrita (`Edit|Write|MultiEdit`) e comandos de terminal (`Bash`) lendo `tool_input` via `stdin`.
   - Bloqueia imediatamente qualquer ação direcionada ao `agent1/`, a arquivos sensíveis (`.env`) ou comandos destrutivos, retornando **código de saída oficial `2`** (`sys.exit(2)`) com registro de auditoria em `.claude/hooks/logs/hook_audit.log`.
2. **Hook `PostToolUse` (`.claude/hooks/post_tool_use.py`):**
   - Disparado imediatamente após a execução bem-sucedida de ferramentas de escrita (`Edit|Write|MultiEdit`).
   - Executa validação sintática automática em Python (`py_compile`) e checagem estrutural de arquivos JSON, retornando `sys.exit(2)` em caso de falha.
   - Garante a integridade imediata dos schemas Pydantic e da lógica de cálculo de risco.

---

## 8. Evolução do Agente no TP4: Novas Capacidades e Decisões Técnicas

Neste ciclo (TP4), o Agente 2 consolidou as seguintes decisões técnicas fundamentais:

1. **Transformação Completa em Agent com OpenAI Agents SDK:**
   - O Agente 2 agora é instanciado como `Agent(name="AgenteAuditoriaRisco", tools=[auditar_parametros_contratuais], output_type=AgentOutputSchema(RelatorioConformidade, strict_json_schema=False))`.
   - Executa a auditoria via inferência real de LLM conectada ao OpenRouter (`Runner.run_sync(..., max_turns=3)`).
2. **Auditoria de Conformidade como `@function_tool`:**
   - A lógica analítica de governança foi encapsulada na ferramenta determinística `@function_tool auditar_parametros_contratuais`, acionada dinamicamente pelo modelo durante o raciocínio de auditoria.
3. **Skill Reutilizável de Alçadas e Penalidades:**
   - Criada a skill `auditoria-alcada-e-multa` ([`.claude/skills/auditoria-alcada-e-multa/SKILL.md`](./.claude/skills/auditoria-alcada-e-multa/SKILL.md) e espelho em [`skills/auditoria-alcada-e-multa/SKILL.md`](./skills/auditoria-alcada-e-multa/SKILL.md)), que padroniza os critérios regulatórios de teto de multa (10%), alçada executiva (R$ 100.000,00) e ações de mitigação.
4. **Subagente Especialista em Penalidades Rescisórias:**
   - Implementado o subagente isolado `auditor-clausulas-penais` ([`.claude/agents/auditor-clausulas-penais.md`](./.claude/agents/auditor-clausulas-penais.md), [`subagents/especialista_clausulas_penais.md`](./subagents/especialista_clausulas_penais.md) e [`subagente_penalidades.py`](./subagente_penalidades.py)), isolando a dogmática jurídica de multas rescisórias para evitar viés de compensação por outros termos comerciais.
5. **Orquestração Assíncrona via n8n:**
   - O Agente 2 consome estritamente o payload validado pelo Agente 1 e despachado pelo n8n via `POST /run` (202 Accepted) e `GET /status/{task_id}`, compondo o dossiê executivo final.

---

## 9. Mapeamento de Requisitos do Projeto vs. Funcionalidades Implementadas

A tabela abaixo estabelece a matriz de rastreabilidade entre os requisitos de projeto e a arquitetura concreta do Agente 2:

| Requisito do Projeto | Componente / Arquivo no Agente 2 | Descrição da Implementação | Status |
| :--- | :--- | :--- | :---: |
| **Ingestão de Dados Estruturados** | `main.py` (`POST /run`) | Endpoint REST que recebe payload tipado via n8n sem processar texto bruto. | Concluído |
| **Agente de Conformidade Real** | `agente_auditoria.py` | Instância real de `Agent` com OpenAI Agents SDK e execução via `Runner.run`. | Concluído |
| **Regras de Negócio como Tool** | `tools.py` (`auditar_parametros_contratuais`) | Ferramenta Python tipada decorada com `@function_tool` para auditoria determinística. | Concluído |
| **Auditoria de Alçada Financeira** | `tools.py` | Confronto automático do valor global contra o teto gerencial de R$ 100.000,00. | Concluído |
| **Auditoria de Teto de Multa** | `tools.py` | Avaliação do percentual de penalidade rescisória contra a diretriz de 10% e Código Civil. | Concluído |
| **Verificação de Regularidade do Fornecedor**| `tools.py` | Auditoria do score de compliance e situação cadastral recuperados da fonte estruturada. | Concluído |
| **Parecer Executivo Tipado** | `models.py` (`RelatorioConformidade`) | Schema Pydantic v2 contendo score, matriz de risco, itens auditados e parecer em Markdown. | Concluído |
| **Subagente Especializado** | `subagente_penalidades.py`, `subagents/` | Subagente com contexto isolado para auditoria especializada de cláusulas penais. | Concluído |
| **Skill Reutilizável** | `skills/auditoria-alcada-e-multa/` | Especificação formal YAML de governança corporativa e mitigações recomendadas. | Concluído |
| **Governança Claude Code** | `.claude/settings.json`, `.claude/hooks/` | Permissões estritas (`allow`, `deny`, `ask`) e hooks `PreToolUse` (fronteira) e `PostToolUse` (sintaxe). | Concluído |
| **Orquestração n8n** | `workflows/workflow_tp4_orquestrador_completo.json` | Pipeline assíncrono completo com polling, roteamento condicional e merge final. | Concluído |

