# CLAUDE.md — Agente 1: Extrator Enriquecido de Contratos

Este arquivo define o contrato de contexto, regras operacionais e especificações técnicas exclusivas do **Agente 1 (Extrator Enriquecido de Contratos)**.

---

## 1. Responsabilidade e Fronteiras de Atuação (Role & Boundary)

O **Agente 1** é um microsserviço especializado em **Processamento e Extração Estruturada de Linguagem Natural Jurídica**.

### O que o Agente 1 FAZ:
- Recebe minutas contratuais em texto bruto via HTTP.
- Decompõe seções documentais (preâmbulo, objeto, valores, prazos, rescisão).
- Executa ferramentas determinísticas em Python para normalização temporal e consistência financeira.
- Valida estruturalmente todas as saídas utilizando modelos **Pydantic v2**.
- Expõe endpoints assíncronos (`/run` e `/status/{task_id}`) para orquestração externa determinística via **n8n**.

### O que o Agente 1 NÃO FAZ (Fronteira Estrita):
- **NÃO** realiza auditoria de conformidade legal, análise de risco ou verificação de regras de negócio corporativas. Essa responsabilidade pertence estritamente ao **Agente 2**.
- **NÃO** chama o Agente 2 diretamente via código interno. A comunicação entre os agentes é desacoplada e realizada unicamente pelo **n8n**.

---

## 2. Hierarquia e Estrutura de Arquivos

```text
agent1/
├── CLAUDE.md                      # Este arquivo: fonte de verdade e especificações do Agente 1
├── AGENTS.md                      # Espelho canônico de especificações do Agente 1
├── main.py                        # Serviço REST FastAPI com BackgroundTasks (/run e /status)
├── agente_extracao.py             # Agente de extração com OpenAI Agents SDK e Runner.run
├── subagente_cadastral.py         # Subagente com isolamento de contexto para homologação de fornecedores
├── tools.py                       # Ferramentas determinísticas Python (@function_tool)
├── models.py                      # Schemas de dados e validações estruturais Pydantic v2
├── memoria_rag.py                 # Persistência relacional (fornecedores) e vetorial (rag_documentos)
├── contrato_exemplo.txt           # Minuta de contrato 1 para testes
├── contrato_exemplo_2.txt         # Minuta de contrato 2 para validação de extração dinâmica
├── test_api.py                    # Suíte de testes automatizados dos endpoints REST
├── requirements.txt               # Dependências Python específicas do microsserviço
├── .claude/                       # Governança formal: settings.json, hooks, skills e agents
│   ├── settings.json              # Permissões allow, deny e ask (schema oficial Claude Code)
│   ├── hooks/                     # Scripts de PreToolUse e PostToolUse (exit code 2 em bloqueio)
│   ├── skills/                    # Skills descobertas pelo Claude Code (.claude/skills/)
│   │   └── validacao-financeira-contratual/
│   │       └── SKILL.md
│   └── agents/                    # Subagentes descobertos pelo Claude Code (.claude/agents/)
│       └── validador-cadastral-fornecedor.md
├── skills/                        # Espelho estruturado de skills do agente
│   └── validacao-financeira-contratual/
│       └── SKILL.md               # Diretrizes de cálculo financeiro e consistência matemática
└── subagents/                     # Documentação e especificação de subagentes isolados
    ├── README.md                  # Justificativa do isolamento de contexto
    └── validador_cadastral.md     # Definição YAML do subagente validador cadastral
```

---

## 3. Ferramentas Python Integradas (`tools.py`)

O Agente 1 possui três ferramentas determinísticas decoradas com `@function_tool` e tipagem estrita (PEP 484):

1. **`normalizar_prazos_e_datas`**:
   - *Finalidade:* Converte datas para padrão ISO-8601 (`YYYY-MM-DD`), calcula prazo final de vigência somando meses contratados e calcula dias corridos e prazo de aviso prévio.
   - *Assinatura:* `(data_inicio_str: str, meses_vigencia: int, dias_aviso_previo: int = 30) -> str (JSON)`

2. **`extrair_e_validar_tabela_financeira`**:
   - *Finalidade:* Realiza auditoria matemática estrita: multiplica quantidade de parcelas pelo valor unitário, confronta com o valor total e calcula discrepâncias centésimais.
   - *Assinatura:* `(valor_total: float, parcelas_qtd: int, valor_parcela: float, periodicidade: str = "mensal") -> str (JSON)`

3. **`consultar_cadastro_fornecedor`**:
   - *Finalidade:* Consulta a fonte de dados estruturada corporativa em banco relacional (`cadastro_fornecedores`) para recuperar situação cadastral, score de compliance e limite de alçada homologado.
   - *Assinatura:* `(cnpj_cpf: str) -> str (JSON)`

---

## 4. Contratos de API REST (Endpoints)

O serviço é exposto via **FastAPI** rodando por padrão na porta **`8001`**.

### 4.1. `POST /run`
Inicia a extração de forma assíncrona.
- **Status HTTP:** `202 Accepted`
- **Request Body (JSON):**
  ```json
  {
    "texto_contrato": "Texto integral da minuta contratual..."
  }
  ```
- **Response Body (JSON):**
  ```json
  {
    "task_id": "13f30f50-268c-4c2c-bcde-caeafda925e1",
    "status": "pending",
    "message": "Processamento de extração iniciado com sucesso em segundo plano."
  }
  ```

### 4.2. `GET /status/{task_id}`
Consulta o progresso e o resultado da extração.
- **Status HTTP:** `200 OK` (ou `404 Not Found` se `task_id` inexistente)
- **Response Body — Em Processamento (`pending`):**
  ```json
  {
    "task_id": "...",
    "status": "pending",
    "created_at": 1792433716.57,
    "completed_at": null,
    "data": null,
    "error": null
  }
  ```
- **Response Body — Concluído com Sucesso (`done`):**
  ```json
  {
    "task_id": "...",
    "status": "done",
    "created_at": 1792433716.57,
    "completed_at": 1792433716.58,
    "data": {
      "titulo": "Contrato de Prestação de Serviços...",
      "contratante": { "nome": "...", "cnpj_cpf": "...", "papel": "CONTRATANTE" },
      "contratada": { "nome": "...", "cnpj_cpf": "...", "papel": "CONTRATADA" },
      "objeto": "...",
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
      "secoes_analisadas": ["PREAMBULO", "OBJETO", "PRECO_E_CONDICOES", "VIGENCIA", "RESCISAO_E_PENALIDADES"]
    },
    "error": null
  }
  ```
- **Response Body — Erro (`error`):**
  ```json
  {
    "task_id": "...",
    "status": "error",
    "data": null,
    "error": "Descrição detalhada da falha durante a extração"
  }
  ```

---

## 5. Estratégia de Context Engineering Adotada

1. **Separação Rígida de Conhecimento:** Este arquivo restringe o contexto do Claude Code à camada de extração e API do Agente 1, evitando alucinações sobre regras de negócio que pertencem ao Agente 2.
2. **Contratos Tipados como Especificação:** As entradas e saídas utilizam a especificação de tipos Pydantic v2 (`DadosContratoExtraido`), assegurando serialização determinística para o n8n.
3. **Padrão Assíncrono Desacoplado:** O uso do padrão `202 Accepted` com `task_id` e polling `/status` protege o sistema contra timeouts HTTP em contratos extensos.

---

## 6. Comandos Operacionais

- **Instalar Dependências:**
  ```bash
  pip install -r requirements.txt
  ```
- **Executar o Serviço FastAPI:**
  ```bash
  uvicorn main:app --host 0.0.0.0 --port 8001 --reload
  ```
- **Executar a Suíte de Testes dos Endpoints:**
  ```bash
  python test_api.py
  ```
- **Acessar Documentação Interativa:**
  Swagger UI em `http://localhost:8001/docs` e Redoc em `http://localhost:8001/redoc`.

---

## 7. Governança Formal do Claude Code: Permissões e Hooks (`.claude/settings.json`)

A especificação formal do Claude Code dentro do diretório `agent1/` é regida pelo arquivo `.claude/settings.json` e pelos scripts automatizados em `.claude/hooks/`.

### 7.1. Decisões de Permissão (Permissions Engine)
- **`allow` (Execução Autônoma):**
  - Leitura e busca de arquivos (`Read(*)`, `Glob(*)`, `Grep(*)`), inspeção de versionamento (`Bash(git status*)`, `Bash(git diff*)`) e execução de testes internos (`Bash(python test_api.py*)`, `Bash(python agente_extracao.py*)`, `Bash(python demo_memoria_rag.py*)`, `Bash(python pipeline_raciocinio.py*)`, `Bash(python subagente_cadastral.py*)`).
  - *Justificativa:* Viabiliza diagnóstico e validação autônoma rápida sem atrito operacional desnecessário.
- **`deny` (Bloqueio Irrevogável):**
  - Leitura, escrita ou edição de arquivos de credenciais e segredos (`Read(.env*)`, `Edit(.env*)`, `Write(.env*)`).
  - Tentativas de escrita ou edição no diretório do Agente 2 (`Edit(../agent2/**)`, `Write(../agent2/**)`, `Edit(**/agent2/**)`, `Write(**/agent2/**)`, `Bash(*agent2*)`).
  - Comandos destrutivos de terminal (`Bash(rm -rf *)`, `Bash(del /f /q *)`, `Bash(git push --force*)`, `Bash(*DROP TABLE*)`).
  - *Justificativa:* Proteção estrita do isolamento entre microsserviços e salvaguarda contra perda de dados ou vazamento de credenciais.
- **`ask` (Exigência de Confirmação Humana):**
  - Alterações no schema central de saída (`Edit(models.py)`, `Write(models.py)`), persistência vetorial/relacional (`Edit(memoria_rag.py)`, `Write(memoria_rag.py)`), camada HTTP (`Edit(main.py)`, `Write(main.py)`), instalação de novos pacotes (`Bash(pip install*)`) e push remoto (`Bash(git push*)`).
  - *Justificativa:* Evita breaking changes em contratos de integração consumidos pelo n8n.

### 7.2. Hooks Automatizados e Verificáveis
1. **Hook `PreToolUse` (`.claude/hooks/pre_tool_use.py`):**
   - Configurado segundo o schema oficial (`hooks: [{type: "command", command: "python .claude/hooks/pre_tool_use.py"}]`), intercepta ferramentas de escrita (`Edit|Write|MultiEdit`) e comandos de shell (`Bash`) lendo `tool_input` via `stdin`.
   - Bloqueia em tempo real qualquer tentativa de cruzar a fronteira para o `agent2/`, editar arquivos `.env` ou executar comandos destrutivos, retornando **código de saída oficial `2`** (`sys.exit(2)`) com mensagem explicativa em `stderr`.
   - Registra cada tentativa (aprovada ou rejeitada) no arquivo estruturado `.claude/hooks/logs/hook_audit.log`.
2. **Hook `PostToolUse` (`.claude/hooks/post_tool_use.py`):**
   - Disparado imediatamente após a execução bem-sucedida de ferramentas de escrita (`Edit|Write|MultiEdit`).
   - Executa automaticamente a compilação sintática de arquivos Python modificados (`py_compile.compile`) e valida a integridade estrutural de arquivos JSON, retornando `sys.exit(2)` caso detecte sintaxe corrompida.
   - Garante que nenhum arquivo corrompido ou com erro de sintaxe permaneça despercebido no microsserviço.

---

## 8. Evolução do Agente no TP4: Novas Capacidades e Decisões Técnicas

Neste ciclo (TP4), o Agente 1 consolidou as seguintes decisões técnicas fundamentais:

1. **Substituição de Extração Mockada por Agent Real:**
   - O Agente 1 opera com uma instância real da classe `Agent` do **OpenAI Agents SDK**, integrada ao modelo de inferência via OpenRouter (`nvidia/nemotron-3.5-lightning:free` / compatíveis OpenAI API).
   - Saída tipada com `AgentOutputSchema(DadosContratoExtraido, strict_json_schema=False)`.
   - Limite estrito de conversação configurado com `max_turns=3` para respostas ágeis e sem travamento na esteira do n8n.
2. **Integração com Fonte de Dados Estruturada de Fornecedores:**
   - Adicionado módulo de conexão e tabela SQLite `cadastro_fornecedores` contendo situação cadastral, score de compliance, limite de alçada e apontamentos jurídicos.
   - Exposta a ferramenta `@function_tool consultar_cadastro_fornecedor(cnpj_cpf: str)` para enriquecimento autônomo do modelo extraído.
3. **Skill Reutilizável de Validação Financeira:**
   - Criada a skill `validacao-financeira-contratual` ([`.claude/skills/validacao-financeira-contratual/SKILL.md`](./.claude/skills/validacao-financeira-contratual/SKILL.md) e espelho em [`skills/validacao-financeira-contratual/SKILL.md`](./skills/validacao-financeira-contratual/SKILL.md)), que encapsula as regras de verificação matemática de parcelamento e discrepâncias centesimais.
4. **Subagente Cadastral com Isolamento de Contexto:**
   - Implementado o subagente `validador-cadastral-fornecedor` ([`.claude/agents/validador-cadastral-fornecedor.md`](./.claude/agents/validador-cadastral-fornecedor.md), [`subagents/validador_cadastral.md`](./subagents/validador_cadastral.md) e [`subagente_cadastral.py`](./subagente_cadastral.py)), isolando a diligência de antecedentes empresariais do processamento do texto integral da minuta.
5. **Orquestração Assíncrona Integrada ao n8n:**
   - O Agente 1 não conhece nem chama o Agente 2. Ele atua como produtor assíncrono consumido pelo orquestrador n8n através do padrão `POST /run` (202 Accepted) e polling `GET /status/{task_id}`.

---

## 9. Mapeamento de Requisitos do Projeto vs. Funcionalidades Implementadas

A tabela abaixo estabelece a matriz de rastreabilidade entre os requisitos de projeto e a arquitetura concreta do Agente 1:

| Requisito do Projeto | Componente / Arquivo no Agente 1 | Descrição da Implementação | Status |
| :--- | :--- | :--- | :---: |
| **Ingestão Documental Flexível** | `main.py` (`POST /run`) | Endpoint REST que recebe texto bruto de contratos via payload JSON. | Concluído |
| **Extração Tipada e Dinâmica** | `agente_extracao.py`, `models.py` | Extração via `Agent` com Pydantic v2 (`DadosContratoExtraido`), variando conforme a minuta analisada. | Concluído |
| **Normalização Temporal** | `tools.py` (`normalizar_prazos_e_datas`) | Conversão de datas para ISO-8601, cálculo de vigência em meses e dias corridos. | Concluído |
| **Validação Financeira Estrita** | `tools.py` (`extrair_e_validar_tabela_financeira`) | Auditoria matemática de parcelas vs. valor total com cálculo de discrepância centesimal. | Concluído |
| **Fonte Estruturada de Negócio** | `memoria_rag.py` (`cadastro_fornecedores`) | Tabela relacional SQLite com CNPJs, scores de compliance e limites de alçada homologados. | Concluído |
| **Memória de Sessão e RAG** | `memoria_rag.py`, `demo_memoria_rag.py` | Persistência multi-turno de histórico em banco e busca semântica em precedentes (`rag_documentos`). | Concluído |
| **Raciocínio Encadeado** | `pipeline_raciocinio.py` | Execução encadeada *Least-to-Most* e *Chain-of-Thought* para síntese jurídica. | Concluído |
| **Subagente Especializado** | `subagente_cadastral.py`, `subagents/` | Subagente com contexto isolado para diligência cadastral e emissão de `FornecedorHomologadoInfo`. | Concluído |
| **Skill Reutilizável** | `skills/validacao-financeira-contratual/` | Especificação formal YAML de procedimentos para auditoria de cronogramas econômicos. | Concluído |
| **Governança Claude Code** | `.claude/settings.json`, `.claude/hooks/` | Permissões estritas (`allow`, `deny`, `ask`) e hooks `PreToolUse` (fronteira) e `PostToolUse` (sintaxe). | Concluído |
| **Orquestração n8n** | `workflows/workflow_tp4_orquestrador_completo.json` | Ciclo assíncrono de submissão, polling e merge em pipeline desacoplado no n8n. | Concluído |

